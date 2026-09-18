from __future__ import annotations

import asyncio
import http.server
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any

import websockets

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from observation_adapter import X72ObservationAdapter, deterministic_report

EXPECTED_ENTITY = "QUEEN-X72-0072"
EXPECTED_REFERENCE = "49e75d92d8fde33f402c3b60482bc5dcf13c12f09bd8c07c7937961d42ceaff9"


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def get_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


class InvalidUtf8Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"\xff\xfe")

    def log_message(self, format: str, *args: Any) -> None:
        return


class InvalidUtf8HttpHarness:
    def __init__(self) -> None:
        self.server = http.server.ThreadingHTTPServer(
            ("127.0.0.1", 0),
            InvalidUtf8Handler,
        )
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.thread = threading.Thread(
            target=self.server.serve_forever,
            daemon=True,
        )

    def __enter__(self) -> "InvalidUtf8HttpHarness":
        self.thread.start()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)


class ServerHarness:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.port = free_port()
        self.base = f"http://127.0.0.1:{self.port}"
        self.proc: subprocess.Popen[str] | None = None

    def start(self) -> None:
        env = os.environ.copy()
        env["ANTMUX_X72_DATA_DIR"] = str(self.data_dir)
        self.proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.server:app",
                "--app-dir",
                str(ROOT),
                "--host",
                "127.0.0.1",
                "--port",
                str(self.port),
                "--log-level",
                "warning",
            ],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        deadline = time.time() + 15
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError(f"server exited early: {self.proc.returncode}")
            try:
                health = get_json(f"{self.base}/api/health")
                if health.get("ok") is True:
                    return
            except Exception:
                pass
            time.sleep(0.1)
        raise RuntimeError("server did not become ready")

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
        time.sleep(0.25)

    def restart(self) -> None:
        self.stop()
        self.start()


def require(condition: bool, name: str, detail: str = "") -> dict[str, Any]:
    if not condition:
        raise AssertionError(f"{name}: {detail}")
    print(f"PASS | {name} | {detail}")
    return {"name": name, "ok": True, "detail": detail}


async def next_with_timeout(iterator: Any, timeout: float = 8.0) -> Any:
    return await asyncio.wait_for(anext(iterator), timeout=timeout)


async def websocket_acceptance(
    harness: ServerHarness,
    adapter: X72ObservationAdapter,
    checks: list[dict[str, Any]],
) -> None:
    stream = adapter.stream_state()
    try:
        first = await next_with_timeout(stream)
        checks.append(
            require(
                first.status == "FRESH"
                and first.condition == "STREAM_STATE"
                and first.entity_id == EXPECTED_ENTITY
                and first.payload is not None
                and first.payload["reference_h256"] == EXPECTED_REFERENCE,
                "WebSocket initial VisualState",
                f"tick={first.payload['tick_count'] if first.payload else None}",
            )
        )
        frozen_payload = json.loads(json.dumps(first.payload, sort_keys=True))

        harness.stop()
        stale = await next_with_timeout(stream)
        checks.append(
            require(
                stale.status == "STALE"
                and stale.condition == "WEBSOCKET_DISCONNECT"
                and stale.payload == frozen_payload,
                "disconnect freezes last authoritative state",
                f"freshness_ms={stale.freshness_ms}",
            )
        )

        harness.start()
        reconnected = await next_with_timeout(stream, timeout=12)
        checks.append(
            require(
                reconnected.status == "FRESH"
                and reconnected.condition == "RECONNECTED"
                and reconnected.entity_id == EXPECTED_ENTITY
                and reconnected.payload is not None
                and reconnected.payload["reference_h256"] == EXPECTED_REFERENCE,
                "WebSocket reconnect restores server authority",
                f"tick={reconnected.payload['tick_count'] if reconnected.payload else None}",
            )
        )
    finally:
        await stream.aclose()


async def two_client_acceptance(
    harness: ServerHarness,
    checks: list[dict[str, Any]],
) -> None:
    adapter_a = X72ObservationAdapter(harness.base)
    adapter_b = X72ObservationAdapter(harness.base)
    stream_a = adapter_a.stream_state()
    stream_b = adapter_b.stream_state()
    try:
        a, b = await asyncio.gather(
            next_with_timeout(stream_a),
            next_with_timeout(stream_b),
        )
        checks.append(
            require(
                a.status == b.status == "FRESH"
                and a.entity_id == b.entity_id == EXPECTED_ENTITY
                and a.payload is not None
                and b.payload is not None
                and a.payload["reference_h256"]
                == b.payload["reference_h256"]
                == EXPECTED_REFERENCE,
                "two adapters observe same Queen",
            )
        )
    finally:
        await stream_a.aclose()
        await stream_b.aclose()


async def invalid_utf8_websocket_acceptance(
    checks: list[dict[str, Any]],
) -> None:
    async def handler(websocket: Any) -> None:
        await websocket.send(b"\xff\xfe")
        await asyncio.sleep(0.2)

    port = free_port()
    async with websockets.serve(handler, "127.0.0.1", port):
        adapter = X72ObservationAdapter(
            f"http://127.0.0.1:{port}",
            timeout_seconds=2.0,
            reconnect_delay_seconds=0.1,
        )
        stream = adapter.stream_state()
        try:
            observation = await next_with_timeout(stream)
            checks.append(
                require(
                    observation.status == "UNKNOWN"
                    and observation.condition == "WEBSOCKET_INVALID_JSON",
                    "invalid UTF-8 WebSocket frame classified INVALID_JSON",
                    observation.condition,
                )
            )
        finally:
            await stream.aclose()


def run() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(
        prefix="antmux-x72-observation-",
        ignore_cleanup_errors=True,
    ) as temp:
        data_dir = Path(temp)
        harness = ServerHarness(data_dir)
        harness.start()
        try:
            adapter = X72ObservationAdapter(
                harness.base,
                timeout_seconds=2.0,
                reconnect_delay_seconds=0.1,
            )

            before = get_json(f"{harness.base}/api/state")
            health = adapter.read_health()
            telemetry = adapter.read_telemetry()
            state = adapter.read_state()
            events = adapter.read_events()
            repair_report = adapter.read_report()
            after = get_json(f"{harness.base}/api/state")

            checks.append(
                require(
                    health.status == "FRESH"
                    and telemetry.status == "FRESH"
                    and state.status == "FRESH"
                    and events.status == "FRESH"
                    and repair_report.status == "FRESH",
                    "HTTP observation endpoints fresh",
                )
            )
            checks.append(
                require(
                    health.entity_id
                    == telemetry.entity_id
                    == state.entity_id
                    == events.entity_id
                    == repair_report.entity_id
                    == EXPECTED_ENTITY,
                    "entity correlation preserved",
                )
            )
            checks.append(
                require(
                    telemetry.payload is not None
                    and telemetry.payload["schema"] == "ANTMUX-X72-OBSERVABILITY-v1"
                    and telemetry.payload["authority"] == "QUEEN_SERVER_V0_2"
                    and telemetry.payload["scope"] == "operational_read_only",
                    "telemetry authority/schema/scope validated",
                )
            )

            for bad_scope in (None, "mutating"):
                bad_adapter = X72ObservationAdapter(harness.base)
                bad_payload = {
                    "schema": "ANTMUX-X72-OBSERVABILITY-v1",
                    "authority": "QUEEN_SERVER_V0_2",
                    "entity_id": EXPECTED_ENTITY,
                }
                if bad_scope is not None:
                    bad_payload["scope"] = bad_scope
                bad_adapter._request_json = lambda path, payload=bad_payload: (
                    "OK",
                    dict(payload),
                    None,
                )
                rejected = bad_adapter.read_telemetry()
                checks.append(
                    require(
                        rejected.status == "UNKNOWN"
                        and rejected.condition == "SCHEMA_MISMATCH",
                        f"telemetry scope rejected: {bad_scope!r}",
                        rejected.condition,
                    )
                )
            checks.append(
                require(
                    state.payload is not None
                    and state.payload["source"] == "QUEEN_SERVER_V0_2"
                    and state.payload["reference_h256"] == EXPECTED_REFERENCE,
                    "state authority/reference validated",
                )
            )
            checks.append(
                require(
                    before["protected_h256"]
                    == after["protected_h256"]
                    == EXPECTED_REFERENCE
                    and before["integrity_match"] is True
                    and after["integrity_match"] is True,
                    "adapter reads do not mutate protected Queen state",
                )
            )

            source = (
                ROOT / "observation_adapter" / "adapter.py"
            ).read_text(encoding="utf-8")
            checks.append(
                require(
                    'method="POST"' not in source
                    and "/api/fault" not in source
                    and "/api/repair" not in source,
                    "adapter exposes no mutation transport",
                )
            )

            records = [health, telemetry, state, events, repair_report]
            report_a = deterministic_report(records)
            report_b = deterministic_report(list(reversed(list(reversed(records)))))
            checks.append(
                require(
                    report_a == report_b
                    and report_a["record_count"] == 5
                    and report_a["entity_ids"] == [EXPECTED_ENTITY],
                    "deterministic observation report",
                    report_a["report_h256"],
                )
            )

            unavailable = X72ObservationAdapter(
                f"http://127.0.0.1:{free_port()}",
                timeout_seconds=0.2,
            ).read_health()
            checks.append(
                require(
                    unavailable.status == "UNKNOWN"
                    and unavailable.condition
                    in {"HTTP_CONNECT_ERROR", "HTTP_TIMEOUT", "HTTP_IO_ERROR"},
                    "HTTP failure remains UNKNOWN",
                    unavailable.condition,
                )
            )

            with InvalidUtf8HttpHarness() as invalid_http:
                invalid_utf8_http = X72ObservationAdapter(
                    invalid_http.base,
                    timeout_seconds=1.0,
                ).read_health()
            checks.append(
                require(
                    invalid_utf8_http.status == "UNKNOWN"
                    and invalid_utf8_http.condition == "INVALID_JSON",
                    "invalid UTF-8 HTTP body classified INVALID_JSON",
                    invalid_utf8_http.condition,
                )
            )

            asyncio.run(invalid_utf8_websocket_acceptance(checks))
            asyncio.run(websocket_acceptance(harness, adapter, checks))
            asyncio.run(two_client_acceptance(harness, checks))

            final_state = get_json(f"{harness.base}/api/state")
            checks.append(
                require(
                    final_state["entity_id"] == EXPECTED_ENTITY
                    and final_state["reference_h256"] == EXPECTED_REFERENCE
                    and final_state["protected_h256"] == EXPECTED_REFERENCE
                    and final_state["integrity_match"] is True,
                    "final Queen integrity unchanged",
                )
            )

            report = {
                "schema": "ANTMUX-X72-OBSERVATION-ADAPTER-ACCEPTANCE-v1",
                "queen_entity_id": EXPECTED_ENTITY,
                "reference_h256": EXPECTED_REFERENCE,
                "checks_total": len(checks),
                "checks_passed": sum(1 for item in checks if item["ok"]),
                "checks_failed": sum(1 for item in checks if not item["ok"]),
                "deterministic_report_h256": report_a["report_h256"],
                "verdict": "PASS" if all(item["ok"] for item in checks) else "FAIL",
                "checks": checks,
            }
            print(json.dumps(report, sort_keys=True))
            return report
        finally:
            harness.stop()


if __name__ == "__main__":
    result = run()
    if result["verdict"] != "PASS":
        raise SystemExit(1)
