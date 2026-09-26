from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import websockets


def request_json(
    method: str,
    url: str,
    body: dict[str, Any] | None = None,
    ip: str = "127.0.0.1",
    extra_headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, Any]]:
    data = None
    headers = {"X-Forwarded-For": ip}
    if extra_headers:
        headers.update(extra_headers)
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
        except Exception:
            payload = {"detail": str(exc)}
        return exc.code, payload


def assert_test(results: list[dict[str, Any]], name: str, ok: bool, detail: str = "") -> None:
    results.append({"name": name, "ok": bool(ok), "detail": detail})
    if not ok:
        raise AssertionError(f"{name}: {detail}")


async def websocket_snapshot(ws_url: str) -> dict[str, Any]:
    async with websockets.connect(ws_url, open_timeout=10) as ws:
        return json.loads(await asyncio.wait_for(ws.recv(), timeout=10))


def zel_test_token() -> str:
    direct = os.environ.get("ANTMUX_ZEL_INGEST_TOKEN", "").strip()
    if direct:
        return direct
    path = os.environ.get("ANTMUX_ZEL_INGEST_TOKEN_FILE", "").strip()
    if not path:
        return ""
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def zel_payload(stage_index: int) -> dict[str, Any]:
    stage_names = ["ENTREE", "Z1 1->3", "F 3->9", "Z MIROIR 9->36", "CHECK 36->9", "RECOMB 9->3", "SORTIE 3->1"]
    channels = [1, 3, 9, 36, 9, 3, 1]
    traces = [1, 4, 13, 49, 58, 61, 62]
    return {
        "mode": "PUBLIC_SAFE",
        "read_only": True,
        "status": "RUN",
        "stage_index": stage_index,
        "stage": stage_names[stage_index],
        "channels": channels[stage_index],
        "trace_points": traces[stage_index],
        "trace_total": 62,
        "stage_exec_us": float(stage_index + 1),
        "stage_work_ratio": min(1.0, (stage_index + 1) / 7.0),
        "public_values": [{"exact": "17/5", "decimal": 3.4}],
        "public_values_total": channels[stage_index],
        "global_error": {"exact": "0", "decimal": 0.0},
        "f1": {
            "formula_id": "F1",
            "k": 3,
            "value": 1764,
            "formula": "z_P(21^k)=4*21^(k-1)",
            "source_commit_short": "aa08bd336662",
        },
        "event_seq": stage_index + 1,
    }


async def zel_relay_sequence(base: str, ws_url: str, token: str) -> tuple[list[int], list[dict[str, Any]]]:
    received: list[dict[str, Any]] = []
    codes: list[int] = []
    async with websockets.connect(ws_url + "?channel=zelstereos", open_timeout=10) as ws:
        for stage_index in (0, 1):
            code, _ = await asyncio.to_thread(
                request_json,
                "POST",
                f"{base}/api/zelstereos/ingest",
                zel_payload(stage_index),
                "127.0.0.1",
                {"Authorization": f"Bearer {token}"},
            )
            codes.append(code)
            received.append(json.loads(await asyncio.wait_for(ws.recv(), timeout=10)))
    return codes, received


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8720")
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    base = args.base.rstrip("/")
    ws_url = base.replace("http://", "ws://").replace("https://", "wss://") + "/ws"
    results: list[dict[str, Any]] = []

    code, health = request_json("GET", f"{base}/api/health")
    assert_test(results, "A health JSON", code == 200 and health.get("ok") is True, str(health))

    code, telemetry0 = request_json("GET", f"{base}/api/telemetry")
    assert_test(results, "A1 telemetry schema", code == 200 and telemetry0.get("schema") == "ANTMUX-X72-OBSERVABILITY-v1", str(telemetry0))
    assert_test(results, "A2 telemetry authority", telemetry0.get("authority") == "QUEEN_SERVER_V0_2" and telemetry0.get("scope") == "operational_read_only", str(telemetry0))
    ws_clients = telemetry0.get("websocket_clients")
    assert_test(results, "A3 telemetry exposes WS client count", isinstance(ws_clients, int) and ws_clients >= 0, str(telemetry0))

    code, state1 = request_json("GET", f"{base}/api/state")
    time.sleep(0.3)
    _, state2 = request_json("GET", f"{base}/api/state")
    assert_test(results, "B state JSON", code == 200 and state2["tick_count"] > state1["tick_count"], "tick did not advance")
    entity_id = state2["entity_id"]
    reference_h256 = state2["reference_h256"]

    ws_a, ws_b = await asyncio.gather(websocket_snapshot(ws_url), websocket_snapshot(ws_url))
    assert_test(results, "C plusieurs WebSockets", ws_a["tick_count"] >= 0 and ws_b["tick_count"] >= 0, "no ws state")
    assert_test(results, "D same Queen entity_id", ws_a["entity_id"] == ws_b["entity_id"] == entity_id, "entity mismatch")
    assert_test(results, "E same reference H256", ws_a["reference_h256"] == ws_b["reference_h256"] == reference_h256, "reference mismatch")
    _, telemetry_ws = request_json("GET", f"{base}/api/telemetry")
    assert_test(results, "E1 telemetry counts WS messages", telemetry_ws.get("websocket_messages_sent", 0) >= 2, str(telemetry_ws))

    token = zel_test_token()
    if token:
        unauthorized_code, _ = request_json(
            "POST",
            f"{base}/api/zelstereos/ingest",
            zel_payload(0),
            ip="127.0.0.1",
        )
        assert_test(results, "E2 ZEL ingest rejects missing bearer", unauthorized_code == 401, str(unauthorized_code))
        zel_codes, zel_states = await zel_relay_sequence(base, ws_url, token)
        assert_test(results, "E3 ZEL ingest accepts authenticated PUBLIC_SAFE", zel_codes == [200, 200], str(zel_codes))
        assert_test(
            results,
            "E4 ZEL WebSocket preserves ordered stages",
            [state.get("stage_index") for state in zel_states] == [0, 1],
            str([state.get("stage_index") for state in zel_states]),
        )
        assert_test(
            results,
            "E5 ZEL relay stays PUBLIC_SAFE",
            all(state.get("mode") == "PUBLIC_SAFE" and state.get("read_only") is True for state in zel_states),
            str(zel_states),
        )
    else:
        results.append({"name": "E2-E5 ZEL relay", "ok": True, "detail": "SKIP: no ingest token configured"})

    for index in range(1, 8):
        synapse = f"S{index}"
        _, before = request_json("GET", f"{base}/api/state")
        before_hash = before["protected_h256"]
        code, fault = request_json("POST", f"{base}/api/fault", {"synapse_id": synapse}, ip=f"10.72.0.{index}")
        assert_test(results, f"F fault {synapse}", code == 200, str(fault))
        fault_hash = fault["state"]["protected_h256"]
        assert_test(results, f"G {synapse} changes protected H256", fault_hash != before_hash, f"{fault_hash} == {before_hash}")
        code, repair = request_json("POST", f"{base}/api/repair", ip=f"10.72.1.{index}")
        assert_test(results, f"H repair {synapse} restores reference H256", code == 200 and repair["report"]["verdict"] == "PASS" and repair["state"]["protected_h256"] == reference_h256, str(repair))

    code, invalid = request_json("POST", f"{base}/api/repair", ip="10.72.2.1")
    assert_test(results, "I repair sans fault = INVALID", code == 200 and invalid["report"]["verdict"] == "INVALID", str(invalid))

    code, _ = request_json("POST", f"{base}/api/fault", {"synapse_id": "S1"}, ip="10.72.3.1")
    assert_test(results, "J double fault setup", code == 200, "first fault failed")
    code, double_fault = request_json("POST", f"{base}/api/fault", {"synapse_id": "S2"}, ip="10.72.3.2")
    assert_test(results, "J double fault refused", code == 409, str(double_fault))
    request_json("POST", f"{base}/api/repair", ip="10.72.3.3")

    request_json("POST", f"{base}/api/fault", {"synapse_id": "S3"}, ip="10.72.4.1")
    second_repair = await asyncio.gather(
        asyncio.to_thread(request_json, "POST", f"{base}/api/repair", None, "10.72.4.2"),
        asyncio.to_thread(request_json, "POST", f"{base}/api/repair", None, "10.72.4.3"),
    )
    repair_codes = sorted(code for code, _ in second_repair)
    assert_test(results, "K double repair refused", repair_codes == [200, 409], str(repair_codes))

    code, _ = request_json("POST", f"{base}/api/fault", {"synapse_id": "S4"}, ip="10.72.5.1")
    request_json("POST", f"{base}/api/repair", ip="10.72.5.2")
    code, limited = request_json("POST", f"{base}/api/fault", {"synapse_id": "S5"}, ip="10.72.5.1")
    assert_test(results, "L rate limit", code == 429, str(limited))

    time.sleep(2.5)
    _, checkpoint_state = request_json("GET", f"{base}/api/state")
    assert_test(results, "M checkpoint tick available", checkpoint_state["tick_count"] > 0, str(checkpoint_state))

    ws_fault_a, ws_fault_b = await asyncio.gather(websocket_snapshot(ws_url), websocket_snapshot(ws_url))
    assert_test(results, "P WebSocket reconnect", ws_fault_a["entity_id"] == entity_id and ws_fault_b["entity_id"] == entity_id, "reconnect mismatch")

    request_json("POST", f"{base}/api/fault", {"synapse_id": "S6"}, ip="10.72.6.1")
    q_state_a, q_state_b = await asyncio.gather(websocket_snapshot(ws_url), websocket_snapshot(ws_url))
    assert_test(results, "Q clients see same panne", q_state_a["integrity_match"] is False and q_state_b["protected_h256"] == q_state_a["protected_h256"], "fault not shared")
    code, q_repair = request_json("POST", f"{base}/api/repair", ip="10.72.6.2")
    assert_test(results, "R other client launches repair", code == 200 and q_repair["report"]["verdict"] == "PASS", str(q_repair))
    s_state_a, s_state_b = await asyncio.gather(websocket_snapshot(ws_url), websocket_snapshot(ws_url))
    assert_test(results, "S all see same PASS", s_state_a["integrity_match"] is True and s_state_b["protected_h256"] == reference_h256, "pass not shared")

    final_state = s_state_a
    report = {
        "version": "ANTMUX_X72_SERVER_SHARED_QUEEN_V0_2",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "queen_entity_id": entity_id,
        "seed": 72,
        "tests_total": len(results),
        "tests_passed": sum(1 for item in results if item["ok"]),
        "tests_failed": sum(1 for item in results if not item["ok"]),
        "reference_h256": reference_h256,
        "final_protected_h256": final_state["protected_h256"],
        "persistent_state_restored": None,
        "multi_client_shared": True,
        "websocket_reconnect": True,
        "systemd_restart": None,
        "rate_limit": True,
        "verdict": "PASS" if all(item["ok"] for item in results) else "FAIL",
        "tests": results,
        "final_state": {
            "tick_count": final_state["tick_count"],
            "whole_h256": final_state["whole_h256"],
            "protected_h256": final_state["protected_h256"],
            "reference_h256": final_state["reference_h256"],
        },
    }
    Path(args.report).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"verdict": report["verdict"], "tests_total": report["tests_total"]}, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())

