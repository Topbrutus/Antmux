from __future__ import annotations

import argparse
import asyncio
import concurrent.futures
import json
import os
import socket
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import websockets

EXPECTED_ENTITY = "QUEEN-X72-0072"
EXPECTED_REFERENCE = "49e75d92d8fde33f402c3b60482bc5dcf13c12f09bd8c07c7937961d42ceaff9"
APP_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
SERVER_SOURCE = APP_ROOT / "app" / "server.py"


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def request_json(
    method: str,
    url: str,
    body: dict[str, Any] | None = None,
    ip: str | None = None,
    allowed: tuple[int, ...] = (200,),
) -> tuple[int, dict[str, Any]]:
    data = None
    headers: dict[str, str] = {}
    if ip is not None:
        headers["X-Forwarded-For"] = ip
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            code = response.status
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        code = exc.code
        raw = exc.read().decode("utf-8")
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {"detail": raw}
    if code not in allowed:
        raise AssertionError(f"{method} {url} returned {code}: {payload}")
    return code, payload


class Results:
    def __init__(self) -> None:
        self.items: list[dict[str, Any]] = []

    def check(self, name: str, ok: bool, detail: str = "", category: str = "general") -> None:
        item = {"name": name, "ok": bool(ok), "detail": detail, "category": category}
        self.items.append(item)
        print(f"{'PASS' if ok else 'FAIL'} | {category} | {name} | {detail}")
        if not ok:
            raise AssertionError(f"{name}: {detail}")


class ServerHarness:
    def __init__(self, data_dir: Path, log_path: Path) -> None:
        self.data_dir = data_dir
        self.log_path = log_path
        self.port = free_port()
        self.base = f"http://127.0.0.1:{self.port}"
        self.ws = f"ws://127.0.0.1:{self.port}/ws"
        self.proc: subprocess.Popen[str] | None = None
        self._log = None

    def start(self) -> None:
        if self.proc is not None:
            raise RuntimeError("server already started")
        env = os.environ.copy()
        env["ANTMUX_X72_DATA_DIR"] = str(self.data_dir)
        self._log = self.log_path.open("a", encoding="utf-8")
        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "app.server:app",
            "--app-dir",
            str(APP_ROOT),
            "--host",
            "127.0.0.1",
            "--port",
            str(self.port),
            "--log-level",
            "warning",
        ]
        self.proc = subprocess.Popen(
            cmd,
            env=env,
            stdout=self._log,
            stderr=subprocess.STDOUT,
            text=True,
        )
        deadline = time.time() + 15
        last_error = ""
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError(f"server exited early with {self.proc.returncode}")
            try:
                code, health = request_json("GET", f"{self.base}/api/health")
                if code == 200 and health.get("ok") is True:
                    return
            except Exception as exc:
                last_error = str(exc)
            time.sleep(0.1)
        raise RuntimeError(f"server did not become ready: {last_error}")

    def stop(self) -> None:
        if self.proc is None:
            return
        self.proc.terminate()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=5)
        self.proc = None
        if self._log is not None:
            self._log.close()
            self._log = None

    def restart(self) -> None:
        self.stop()
        self.port = free_port()
        self.base = f"http://127.0.0.1:{self.port}"
        self.ws = f"ws://127.0.0.1:{self.port}/ws"
        self.start()


async def recv_until(ws: Any, predicate: Any, label: str, attempts: int = 80) -> dict[str, Any]:
    for _ in range(attempts):
        state = json.loads(await asyncio.wait_for(ws.recv(), timeout=2))
        if predicate(state):
            return state
    raise AssertionError(f"timeout waiting for {label}")


def synapse_faulted(state: dict[str, Any], synapse_id: str) -> bool:
    for synapse in state.get("synapses", []):
        if synapse.get("synapse_id") == synapse_id:
            return synapse.get("enabled") is False and synapse.get("integrity") == 0
    return False


def clean_if_needed(harness: ServerHarness) -> dict[str, Any]:
    _, state = request_json("GET", f"{harness.base}/api/state")
    if state.get("integrity_match") is True:
        return state
    _, repaired = request_json("POST", f"{harness.base}/api/repair", {}, ip="10.72.250.250")
    if repaired.get("report", {}).get("verdict") != "PASS":
        raise AssertionError(f"cleanup repair failed: {repaired}")
    return repaired["state"]


async def websocket_shared_fault_cycle(harness: ServerHarness, results: Results) -> None:
    async with websockets.connect(harness.ws) as a, websockets.connect(harness.ws) as b:
        a0 = await recv_until(a, lambda s: s.get("entity_id") == EXPECTED_ENTITY, "client A baseline")
        b0 = await recv_until(b, lambda s: s.get("entity_id") == EXPECTED_ENTITY, "client B baseline")
        results.check(
            "two clients share entity/reference",
            a0["entity_id"] == b0["entity_id"] == EXPECTED_ENTITY
            and a0["reference_h256"] == b0["reference_h256"] == EXPECTED_REFERENCE,
            category="multi-client",
        )

        _, fault = request_json(
            "POST",
            f"{harness.base}/api/fault",
            {"synapse_id": "S4"},
            ip="10.72.40.1",
        )
        results.check("S4 mutation accepted", synapse_faulted(fault["state"], "S4"), category="fault")
        fa = await recv_until(a, lambda s: synapse_faulted(s, "S4"), "A sees S4")
        fb = await recv_until(b, lambda s: synapse_faulted(s, "S4"), "B sees S4")
        results.check(
            "S4 fault shared to both WebSockets",
            fa["protected_h256"] == fb["protected_h256"] and fa["integrity_match"] is False,
            category="multi-client",
        )

        _, repaired = request_json("POST", f"{harness.base}/api/repair", {}, ip="10.72.40.2")
        results.check(
            "repair returns PASS",
            repaired["report"]["verdict"] == "PASS",
            str(repaired["report"]),
            category="repair",
        )
        ra = await recv_until(
            a,
            lambda s: s.get("protected_h256") == EXPECTED_REFERENCE and s.get("integrity_match") is True,
            "A sees repair",
        )
        rb = await recv_until(
            b,
            lambda s: s.get("protected_h256") == EXPECTED_REFERENCE and s.get("integrity_match") is True,
            "B sees repair",
        )
        results.check(
            "repair hash closes for both clients",
            ra["protected_h256"] == rb["protected_h256"] == EXPECTED_REFERENCE,
            category="repair",
        )


async def websocket_stress(harness: ServerHarness, results: Results, count: int = 16) -> None:
    async def one() -> dict[str, Any]:
        async with websockets.connect(harness.ws, open_timeout=10) as ws:
            return json.loads(await asyncio.wait_for(ws.recv(), timeout=5))

    states = await asyncio.gather(*(one() for _ in range(count)))
    ok = all(
        state.get("entity_id") == EXPECTED_ENTITY
        and state.get("reference_h256") == EXPECTED_REFERENCE
        for state in states
    )
    results.check(f"{count} simultaneous WebSocket clients", ok, category="websocket")


def static_security_checks(results: Results) -> None:
    source = SERVER_SOURCE.read_text(encoding="utf-8")
    dangerous = ["eval(", "exec(", "os.system(", "subprocess.", "shell=True", "websocket.receive"]
    hits = [token for token in dangerous if token in source]
    results.check("no arbitrary execution/read channel", not hits, ",".join(hits), category="security")

    expose = REPO_ROOT / ".github" / "workflows" / "expose-x72-nginx.yml"
    if expose.exists():
        text = expose.read_text(encoding="utf-8")
        trusted = text.count("proxy_set_header X-Forwarded-For $remote_addr;") >= 2
        legacy = "$proxy_add_x_forwarded_for" in text
        results.check(
            "Nginx X72 overwrites client X-Forwarded-For",
            trusted and not legacy,
            f"trusted={trusted} legacy={legacy}",
            category="security",
        )


def insert_corrupt_checkpoint(db_path: Path) -> None:
    with sqlite3.connect(db_path) as db:
        row = db.execute(
            "SELECT state_json, protected_h256, whole_h256 FROM checkpoints ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row is None:
            raise AssertionError("no checkpoint available to corrupt")
        state_json, protected_h256, whole_h256 = row
        payload = json.loads(state_json)
        payload["entity_id"] = "QUEEN-X72-CORRUPT"
        db.execute(
            "INSERT INTO checkpoints(created_at,state_json,protected_h256,whole_h256) VALUES(?,?,?,?)",
            (time.time(), json.dumps(payload, sort_keys=True, separators=(",", ":")), protected_h256, whole_h256),
        )
        db.commit()


def run_sync_tests(harness: ServerHarness, results: Results) -> None:
    _, health = request_json("GET", f"{harness.base}/api/health")
    results.check(
        "health source/entity",
        health.get("ok") is True and health.get("entity_id") == EXPECTED_ENTITY,
        f"source={health.get('source')} entity={health.get('entity_id')}",
        category="health",
    )
    _, state = request_json("GET", f"{harness.base}/api/state")
    results.check(
        "baseline reference/integrity",
        state["reference_h256"] == EXPECTED_REFERENCE and state["integrity_match"] is True,
        category="integrity",
    )

    def get_state(_: int) -> tuple[int, dict[str, Any]]:
        return request_json("GET", f"{harness.base}/api/state")

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
        samples = list(pool.map(get_state, range(120)))
    results.check(
        "120 concurrent state reads",
        all(code == 200 and item["entity_id"] == EXPECTED_ENTITY for code, item in samples),
        category="stress",
    )

    code, invalid = request_json(
        "POST",
        f"{harness.base}/api/fault",
        {"synapse_id": "S9"},
        ip="10.72.50.1",
        allowed=(422,),
    )
    results.check("invalid synapse rejected", code == 422, str(invalid), category="errors")

    code, _ = request_json("DELETE", f"{harness.base}/api/state", allowed=(405,))
    results.check("unsupported method rejected", code == 405, category="errors")

    for path in ("/api/reset", "/api/reseed", "/api/exec", "/api/shell"):
        code, _ = request_json("GET", f"{harness.base}{path}", allowed=(404,))
        results.check(f"admin surface absent {path}", code == 404, category="security")

    clean_if_needed(harness)
    barrier = threading.Barrier(8)

    def fault_worker(index: int) -> tuple[int, dict[str, Any]]:
        barrier.wait(timeout=5)
        synapse = f"S{(index % 7) + 1}"
        return request_json(
            "POST",
            f"{harness.base}/api/fault",
            {"synapse_id": synapse},
            ip=f"10.72.60.{index + 1}",
            allowed=(200, 409),
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        fault_results = list(pool.map(fault_worker, range(8)))
    codes = [code for code, _ in fault_results]
    results.check(
        "concurrent faults serialize to one winner",
        codes.count(200) == 1 and codes.count(409) == 7,
        str(codes),
        category="concurrency",
    )
    request_json("POST", f"{harness.base}/api/repair", {}, ip="10.72.60.99")

    clean_if_needed(harness)
    request_json(
        "POST",
        f"{harness.base}/api/fault",
        {"synapse_id": "S3"},
        ip="10.72.61.1",
    )
    repair_barrier = threading.Barrier(6)

    def repair_worker(index: int) -> tuple[int, dict[str, Any]]:
        repair_barrier.wait(timeout=5)
        return request_json(
            "POST",
            f"{harness.base}/api/repair",
            {},
            ip=f"10.72.61.{index + 10}",
            allowed=(200, 409),
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        repair_results = list(pool.map(repair_worker, range(6)))
    pass_count = sum(
        1
        for code, payload in repair_results
        if code == 200 and payload.get("report", {}).get("verdict") == "PASS"
    )
    bad = [
        (code, payload.get("report", {}).get("verdict"))
        for code, payload in repair_results
        if code not in (200, 409)
        or (code == 200 and payload.get("report", {}).get("verdict") not in ("PASS", "INVALID"))
    ]
    results.check(
        "concurrent repairs produce one PASS and no corrupt result",
        pass_count == 1 and not bad,
        f"pass_count={pass_count} responses={[(c,p.get('report',{}).get('verdict')) for c,p in repair_results]}",
        category="concurrency",
    )
    _, after_repairs = request_json("GET", f"{harness.base}/api/state")
    results.check(
        "concurrent repair final hash closes",
        after_repairs["integrity_match"] is True
        and after_repairs["protected_h256"] == EXPECTED_REFERENCE,
        category="integrity",
    )

    rate_ip = "10.72.62.1"
    code, first = request_json("POST", f"{harness.base}/api/repair", {}, ip=rate_ip)
    results.check(
        "clean repair command is explicit INVALID",
        code == 200 and first.get("report", {}).get("verdict") == "INVALID",
        category="errors",
    )
    code, limited = request_json(
        "POST",
        f"{harness.base}/api/repair",
        {},
        ip=rate_ip,
        allowed=(429,),
    )
    results.check("same-IP mutation rate-limited", code == 429, str(limited), category="rate-limit")


async def run_async_tests(harness: ServerHarness, results: Results) -> None:
    await websocket_stress(harness, results)
    await websocket_shared_fault_cycle(harness, results)

    async with websockets.connect(harness.ws, open_timeout=10) as ws:
        before = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
    await asyncio.sleep(0.35)
    _, after = await asyncio.to_thread(request_json, "GET", f"{harness.base}/api/state")
    results.check(
        "closing WebSocket client does not stop Queen",
        after["entity_id"] == before["entity_id"] == EXPECTED_ENTITY
        and after["tick_count"] > before["tick_count"],
        f"before={before['tick_count']} after={after['tick_count']}",
        category="websocket",
    )


def build_report(results: Results, final_state: dict[str, Any], elapsed: float) -> dict[str, Any]:
    passed = sum(1 for item in results.items if item["ok"])
    failed = len(results.items) - passed
    categories: dict[str, dict[str, int]] = {}
    for item in results.items:
        bucket = categories.setdefault(item["category"], {"passed": 0, "failed": 0})
        bucket["passed" if item["ok"] else "failed"] += 1
    return {
        "schema": "ANTMUX-X72-ROBUSTNESS-v1",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "branch_role": "worker2/x72-tests-hardening",
        "queen_entity_id": final_state["entity_id"],
        "reference_h256": final_state["reference_h256"],
        "final_protected_h256": final_state["protected_h256"],
        "final_integrity_match": final_state["integrity_match"],
        "tests_total": len(results.items),
        "tests_passed": passed,
        "tests_failed": failed,
        "categories": categories,
        "elapsed_seconds": round(elapsed, 3),
        "verdict": "PASS" if failed == 0 else "FAIL",
        "tests": results.items,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# ANTMUX-X72 — Rapport de robustesse Worker 2",
        "",
        f"- Verdict: **{report['verdict']}**",
        f"- Tests: **{report['tests_passed']}/{report['tests_total']} PASS**",
        f"- Queen: `{report['queen_entity_id']}`",
        f"- Reference H256: `{report['reference_h256']}`",
        f"- Final protected H256: `{report['final_protected_h256']}`",
        f"- Integrity match: `{report['final_integrity_match']}`",
        f"- Durée: `{report['elapsed_seconds']} s`",
        "",
        "## Catégories",
        "",
    ]
    for category, counts in sorted(report["categories"].items()):
        lines.append(f"- **{category}** — PASS {counts['passed']} / FAIL {counts['failed']}")
    lines.extend(["", "## Tests", ""])
    for item in report["tests"]:
        mark = "PASS" if item["ok"] else "FAIL"
        detail = f" — {item['detail']}" if item["detail"] else ""
        lines.append(f"- `{mark}` **{item['name']}** ({item['category']}){detail}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True)
    parser.add_argument("--markdown")
    parser.add_argument("--keep-data")
    args = parser.parse_args()

    started = time.monotonic()
    results = Results()
    temp_ctx = None
    if args.keep_data:
        data_dir = Path(args.keep_data).resolve()
        data_dir.mkdir(parents=True, exist_ok=True)
    else:
        temp_ctx = tempfile.TemporaryDirectory(
            prefix="antmux-x72-robust-",
            ignore_cleanup_errors=True,
        )
        data_dir = Path(temp_ctx.name)

    log_path = data_dir / "server.log"
    harness = ServerHarness(data_dir, log_path)
    try:
        static_security_checks(results)
        harness.start()
        run_sync_tests(harness, results)
        asyncio.run(run_async_tests(harness, results))

        clean_if_needed(harness)
        time.sleep(2.2)
        _, before_restart = request_json("GET", f"{harness.base}/api/state")
        db_path = data_dir / "queen.db"
        with sqlite3.connect(db_path) as db:
            row = db.execute("SELECT state_json FROM checkpoints ORDER BY id DESC LIMIT 1").fetchone()
        if row is None:
            raise AssertionError("restart test requires a persisted checkpoint")
        persisted_tick = int(json.loads(row[0])["tick"])
        harness.restart()
        _, after_restart = request_json("GET", f"{harness.base}/api/state")
        results.check(
            "restart restores latest persisted Queen checkpoint",
            after_restart["entity_id"] == before_restart["entity_id"] == EXPECTED_ENTITY
            and after_restart["reference_h256"] == EXPECTED_REFERENCE
            and after_restart["protected_h256"] == EXPECTED_REFERENCE
            and after_restart["integrity_match"] is True
            and after_restart["tick_count"] >= persisted_tick,
            f"persisted={persisted_tick} before={before_restart['tick_count']} after={after_restart['tick_count']}",
            category="restart",
        )

        async def reconnect_once() -> dict[str, Any]:
            async with websockets.connect(harness.ws, open_timeout=10) as ws:
                return json.loads(await asyncio.wait_for(ws.recv(), timeout=5))

        reconnect_state = asyncio.run(reconnect_once())
        results.check(
            "WebSocket reconnect after restart",
            reconnect_state["entity_id"] == EXPECTED_ENTITY
            and reconnect_state["reference_h256"] == EXPECTED_REFERENCE,
            category="websocket",
        )

        harness.stop()
        db_path = data_dir / "queen.db"
        results.check(
            "SQLite checkpoint database exists",
            db_path.exists(),
            "queen.db present" if db_path.exists() else "queen.db missing",
            category="persistence",
        )
        with sqlite3.connect(db_path) as db:
            count = int(db.execute("SELECT COUNT(*) FROM checkpoints").fetchone()[0])
        results.check("multiple checkpoints persisted", count >= 2, f"rows={count}", category="persistence")

        insert_corrupt_checkpoint(db_path)
        harness.start()
        _, recovered = request_json("GET", f"{harness.base}/api/state")
        results.check(
            "corrupt newest checkpoint is rejected with fallback",
            recovered["entity_id"] == EXPECTED_ENTITY
            and recovered["reference_h256"] == EXPECTED_REFERENCE
            and recovered["integrity_match"] is True,
            f"entity={recovered['entity_id']} integrity={recovered['integrity_match']}",
            category="persistence",
        )

        asyncio.run(websocket_stress(harness, results, count=8))
        _, final_state = request_json("GET", f"{harness.base}/api/state")
        results.check(
            "final protected H256 equals reference",
            final_state["protected_h256"] == final_state["reference_h256"] == EXPECTED_REFERENCE,
            category="integrity",
        )
    finally:
        harness.stop()

    report = build_report(results, final_state, time.monotonic() - started)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    if args.markdown:
        md_path = Path(args.markdown)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        write_markdown(report, md_path)
    print(json.dumps({"verdict": report["verdict"], "tests_total": report["tests_total"]}, sort_keys=True))
    if report["verdict"] != "PASS":
        raise SystemExit(1)
    if temp_ctx is not None:
        temp_ctx.cleanup()


if __name__ == "__main__":
    main()
