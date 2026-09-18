from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

import websockets

from consumer.observation_adapter import (
    AUTHORITY,
    OBSERVABILITY_SCHEMA,
    X72ObservationAdapter,
    deterministic_report,
)


def run_http_acceptance(base: str, ws: str) -> tuple[X72ObservationAdapter, list[Any]]:
    adapter = X72ObservationAdapter(base, ws_url=ws, timeout=5.0)
    health = adapter.read_health()
    telemetry = adapter.read_telemetry()
    state = adapter.read_state()
    events = adapter.read_events()
    report = adapter.read_report()

    observations = [health, telemetry, state, events, report]
    entity_ids = {item.entity_id for item in observations}
    assert entity_ids == {"QUEEN-X72-0072"}, entity_ids
    assert all(item.status == "FRESH" for item in observations)
    assert telemetry.source_schema == OBSERVABILITY_SCHEMA
    assert telemetry.payload["authority"] == AUTHORITY
    assert telemetry.payload["scope"] == "operational_read_only"
    assert state.payload["source"] == AUTHORITY

    first = deterministic_report(observations)
    second = deterministic_report(observations)
    assert first == second
    assert first["entity_id"] == "QUEEN-X72-0072"
    assert len(first["records"]) == 5
    assert len(first["report_h256"]) == 64

    print("ADAPTER_HTTP_READS=PASS")
    print("ADAPTER_ENTITY_CONTINUITY=PASS")
    print("ADAPTER_DETERMINISTIC_REPORT=PASS")
    return adapter, observations


async def run_reconnect_acceptance(entity_id: str, base: str) -> None:
    connections = 0

    async def handler(websocket: Any) -> None:
        nonlocal connections
        connections += 1
        payload = {
            "source": AUTHORITY,
            "entity_id": entity_id,
            "tick_count": 1000 + connections,
            "integrity_match": True,
        }
        await websocket.send(json.dumps(payload, sort_keys=True))
        await websocket.close()

    server = await websockets.serve(handler, "127.0.0.1", 0)
    try:
        port = server.sockets[0].getsockname()[1]
        adapter = X72ObservationAdapter(
            base,
            ws_url=f"ws://127.0.0.1:{port}",
            timeout=2.0,
            reconnect_delay=0.02,
        )
        adapter.read_health()
        received = [
            item
            async for item in adapter.stream_state(
                max_messages=2,
                reconnect=True,
                max_reconnects=3,
            )
        ]
        assert len(received) == 2
        assert connections >= 2
        assert all(item.entity_id == entity_id for item in received)
        assert received[1].payload["tick_count"] > received[0].payload["tick_count"]
        print("ADAPTER_WS_DISCONNECT_RECONNECT=PASS")
    finally:
        server.close()
        await server.wait_closed()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8720")
    parser.add_argument("--ws", default="ws://127.0.0.1:8720/ws")
    args = parser.parse_args()

    adapter, observations = run_http_acceptance(args.base, args.ws)
    asyncio.run(run_reconnect_acceptance(adapter.read_health().entity_id, args.base))

    summary = {
        "schema": "ANTMUX-X72-OBSERVATION-ADAPTER-ACCEPTANCE-v1",
        "verdict": "PASS",
        "entity_id": observations[0].entity_id,
        "http_observations": len(observations),
        "authority": AUTHORITY,
    }
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
