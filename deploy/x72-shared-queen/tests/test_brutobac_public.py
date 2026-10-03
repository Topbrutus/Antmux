from __future__ import annotations

import json
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

from app.ant_birth import build_ant_birth
from app.brutobac_public import PUBLIC_SCHEMA, build_public_events
from app.live_transport import LiveTransportStore


def queen_snapshot(tick: int = 1234) -> dict:
    return {
        "entity_id": "QUEEN-X72-0072",
        "tick_count": tick,
        "generation": 7,
        "queen_mode": "STABLE",
        "integrity_match": True,
        "reference_h256": "a" * 64,
    }


def test_public_projection_contains_queen_and_valid_ant_only() -> None:
    with tempfile.TemporaryDirectory(prefix="antmux-brutobac-public-") as tmp:
        data_dir = Path(tmp)
        store = LiveTransportStore(data_dir)

        ant_id = "ANT-123456789ABC"
        material_id = "MAT-MATH-1234567890ABCDEF12345678"
        material_h256 = "b" * 64
        receipt = build_ant_birth(
            ant_id,
            "BrutoBac public test carrier",
            "Read-only projection test.",
            1_790_000_000.0,
        )

        with closing(sqlite3.connect(data_dir / "live-transport.db")) as db:
            db.execute(
                "INSERT INTO carrier_ants(ant_id, receipt_json, created_at) VALUES (?, ?, ?)",
                (ant_id, json.dumps(receipt), 1_790_000_000.0),
            )
            db.commit()

        store.attach(
            ant_id=ant_id,
            material_id=material_id,
            material_h256=material_h256,
            position="W:GENESIS-A",
            tick=1200,
        )

        events = build_public_events(data_dir, lambda: queen_snapshot(1234))
        assert len(events) == 3

        status, queen, ant = events
        assert status["schema"] == PUBLIC_SCHEMA
        assert status["event_type"] == "SYSTEM_STATUS"
        assert status["tick"] == 1234
        assert status["metadata"]["bridge_mode"] == "READ_ONLY"

        assert queen["ant_id"] == "QUEEN-X72-0072"
        assert queen["role"] == "QUEEN"
        assert queen["position"] == "CENTER"

        assert ant["ant_id"] == ant_id
        assert ant["role"] == "SYNAPSE"
        assert ant["state"] == "SINGING_TO_MEET"
        assert ant["position"] == "W:GENESIS-A"
        assert ant["material"]["material_id"] == material_id
        assert ant["material"]["material_h256"] == material_h256
        assert "authorization" not in json.dumps(events).lower()
        assert "token" not in json.dumps(events).lower()


def test_public_projection_fails_closed_without_birth_receipt() -> None:
    with tempfile.TemporaryDirectory(prefix="antmux-brutobac-public-missing-ant-") as tmp:
        data_dir = Path(tmp)
        store = LiveTransportStore(data_dir)

        with closing(sqlite3.connect(data_dir / "live-transport.db")) as db:
            db.execute(
                """
                INSERT INTO transport_state(
                    material_id, material_h256, ant_id, position, binding_state,
                    attached_tick, updated_tick, last_move_tick,
                    last_command_id, last_authorization_id, state_version
                ) VALUES (?, ?, ?, ?, 'ATTACHED', ?, ?, NULL, NULL, NULL, 1)
                """,
                (
                    "MAT-MATH-ABCDEFABCDEFABCDEFABCDEF",
                    "c" * 64,
                    "ANT-ABCDEFABCDEF",
                    "W:START",
                    10,
                    10,
                ),
            )
            db.commit()

        events = build_public_events(data_dir, lambda: queen_snapshot(20))
        assert len(events) == 2
        assert all(event.get("ant_id") != "ANT-ABCDEFABCDEF" for event in events)


if __name__ == "__main__":
    test_public_projection_contains_queen_and_valid_ant_only()
    test_public_projection_fails_closed_without_birth_receipt()
    print("BRUTOBAC_PUBLIC_PROJECTION=PASS")
    print("BRUTOBAC_PUBLIC_FAIL_CLOSED=PASS")
