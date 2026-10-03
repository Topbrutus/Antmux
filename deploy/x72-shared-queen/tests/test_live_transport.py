from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.live_transport import (
    LiveTransportStore,
    create_live_transport_router,
)


ANT_ID = "ANT-000000000001"
MATERIAL_ID = "MAT-MATH-AAAAAAAAAAAAAAAAAAAAAAAA"
MATERIAL_H256 = "a" * 64
TOKEN = "transport-test-token"


def canonical_h256(payload: dict) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def test_store_atomic_move_and_replay() -> None:
    with tempfile.TemporaryDirectory(prefix="antmux-live-transport-store-") as tmp:
        store = LiveTransportStore(Path(tmp))

        attached = store.attach(
            ant_id=ANT_ID,
            material_id=MATERIAL_ID,
            material_h256=MATERIAL_H256,
            position="W:START",
            tick=100,
        )
        assert attached["position"] == "W:START"
        assert attached["binding_state"] == "ATTACHED"
        assert attached["state_version"] == 1

        # Exact re-attach is idempotent.
        again = store.attach(
            ant_id=ANT_ID,
            material_id=MATERIAL_ID,
            material_h256=MATERIAL_H256,
            position="W:START",
            tick=101,
        )
        assert again["state_version"] == 1
        assert again["position"] == "W:START"

        moved = store.move(
            command_id="LTC-T110-AAAAAAAAAAAAAAAAAAAA",
            authorization_id="LTA-T105-BBBBBBBBBBBBBBBBBBBB",
            authorization_h256="b" * 64,
            ant_id=ANT_ID,
            material_id=MATERIAL_ID,
            material_h256=MATERIAL_H256,
            from_position="W:START",
            to_position="W:GENESIS-A",
            requested_at_tick=110,
            executed_at_tick=111,
        )
        assert moved["position"] == "W:GENESIS-A"
        assert moved["state_version"] == 2
        assert moved["last_move_tick"] == 111

        try:
            store.move(
                command_id="LTC-T110-AAAAAAAAAAAAAAAAAAAA",
                authorization_id="LTA-T105-BBBBBBBBBBBBBBBBBBBB",
                authorization_h256="b" * 64,
                ant_id=ANT_ID,
                material_id=MATERIAL_ID,
                material_h256=MATERIAL_H256,
                from_position="W:GENESIS-A",
                to_position="W:GENESIS-B",
                requested_at_tick=112,
                executed_at_tick=113,
            )
        except Exception as exc:
            assert "already consumed" in str(exc)
        else:
            raise AssertionError("replayed command must fail")


def test_private_api_attach_state_move() -> None:
    with tempfile.TemporaryDirectory(prefix="antmux-live-transport-api-") as tmp:
        tick = {"value": 200}
        app = FastAPI()
        app.include_router(
            create_live_transport_router(
                Path(tmp),
                lambda: {
                    "entity_id": "QUEEN-X72-0072",
                    "tick_count": tick["value"],
                    "generation": 3,
                    "queen_mode": "STABLE",
                    "integrity_match": True,
                    "reference_h256": "c" * 64,
                },
                transport_token=TOKEN,
            )
        )
        client = TestClient(app)

        attach_payload = {
            "ANT_ID": ANT_ID,
            "MATERIAL_ID": MATERIAL_ID,
            "MATERIAL_H256": MATERIAL_H256,
            "POSITION": "W:START",
            "TRACE_ID": "TRACE-LIVE-TRANSPORT-ATTACH",
        }

        unauthorized = client.post("/api/live-transport/attach", json=attach_payload)
        assert unauthorized.status_code == 401

        headers = {"Authorization": f"Bearer {TOKEN}"}
        attached = client.post(
            "/api/live-transport/attach",
            json=attach_payload,
            headers=headers,
        )
        assert attached.status_code == 200
        body = attached.json()
        assert body["schema"] == "ANTMUX-LIVE-FOURMI-TRANSPORT-v0.1"
        assert body["authority"] == "QUEEN_SERVER_V0_2"
        assert body["tick"] == 200
        assert body["queen"] == {
            "entity_id": "QUEEN-X72-0072",
            "tick_count": 200,
            "generation": 3,
            "queen_mode": "STABLE",
            "integrity_match": True,
            "reference_h256": "c" * 64,
        }
        assert body["position"] == "W:START"
        assert body["material"]["binding_state"] == "ATTACHED"
        assert body["integrity_match"] is True

        hash_payload = {
            key: value
            for key, value in body.items()
            if key not in {"state_h256", "integrity_match"}
        }
        assert body["state_h256"] == canonical_h256(hash_payload)

        tick["value"] = 201
        before = client.get(
            f"/api/live-transport/state/{ANT_ID}/{MATERIAL_ID}",
            headers=headers,
        )
        assert before.status_code == 200
        assert before.json()["tick"] == 201
        assert before.json()["position"] == "W:START"

        move_payload = {
            "COMMAND_ID": "LTC-T201-CCCCCCCCCCCCCCCCCCCC",
            "AUTHORIZATION_ID": "LTA-T200-DDDDDDDDDDDDDDDDDDDD",
            "AUTHORIZATION_H256": "d" * 64,
            "ANT_ID": ANT_ID,
            "MATERIAL_ID": MATERIAL_ID,
            "MATERIAL_H256": MATERIAL_H256,
            "REQUESTED_AT_TICK": 201,
            "CLOCK_AUTHORITY": "QUEEN_SERVER_V0_2",
            "FROM": "W:START",
            "TO": "W:GENESIS-A",
            "MAX_MOVES": 1,
            "SINGLE_USE": True,
            "PROOF_REF": None,
            "EXECUTABLE": False,
            "GATE_AUTHORITY": False,
            "ROUTING_AUTHORIZATION": "AUTHORIZED",
        }

        tick["value"] = 202
        moved = client.post(
            "/api/live-transport/move",
            json=move_payload,
            headers=headers,
        )
        assert moved.status_code == 200
        assert moved.json() == {
            "STATUS": "ACCEPTED",
            "COMMAND_ID": move_payload["COMMAND_ID"],
            "AUTHORIZATION_ID": move_payload["AUTHORIZATION_ID"],
            "ANT_ID": ANT_ID,
            "MATERIAL_ID": MATERIAL_ID,
            "FROM": "W:START",
            "TO": "W:GENESIS-A",
        }

        tick["value"] = 203
        after = client.get(
            f"/api/live-transport/state/{ANT_ID}/{MATERIAL_ID}",
            headers=headers,
        )
        assert after.status_code == 200
        after_body = after.json()
        assert after_body["tick"] == 203
        assert after_body["position"] == "W:GENESIS-A"
        assert after_body["last_move_tick"] == 202
        assert after_body["last_command_id"] == move_payload["COMMAND_ID"]
        assert after_body["last_authorization_id"] == move_payload["AUTHORIZATION_ID"]
        assert after_body["state_version"] == 2

        replay = client.post(
            "/api/live-transport/move",
            json=move_payload,
            headers=headers,
        )
        assert replay.status_code == 409
        assert "already consumed" in replay.json()["detail"]


def test_move_rejects_wrong_from_and_unsafe_flags() -> None:
    with tempfile.TemporaryDirectory(prefix="antmux-live-transport-deny-") as tmp:
        tick = {"value": 300}
        app = FastAPI()
        app.include_router(
            create_live_transport_router(
                Path(tmp),
                lambda: {
                    "entity_id": "QUEEN-X72-0072",
                    "tick_count": tick["value"],
                    "generation": 4,
                    "queen_mode": "STABLE",
                    "integrity_match": True,
                    "reference_h256": "d" * 64,
                },
                transport_token=TOKEN,
            )
        )
        client = TestClient(app)
        headers = {"Authorization": f"Bearer {TOKEN}"}

        client.post(
            "/api/live-transport/attach",
            json={
                "ANT_ID": ANT_ID,
                "MATERIAL_ID": MATERIAL_ID,
                "MATERIAL_H256": MATERIAL_H256,
                "POSITION": "W:START",
                "TRACE_ID": "TRACE-LIVE-TRANSPORT-ATTACH",
            },
            headers=headers,
        )

        base = {
            "COMMAND_ID": "LTC-T300-EEEEEEEEEEEEEEEEEEEE",
            "AUTHORIZATION_ID": "LTA-T299-FFFFFFFFFFFFFFFFFFFF",
            "AUTHORIZATION_H256": "f" * 64,
            "ANT_ID": ANT_ID,
            "MATERIAL_ID": MATERIAL_ID,
            "MATERIAL_H256": MATERIAL_H256,
            "REQUESTED_AT_TICK": 300,
            "CLOCK_AUTHORITY": "QUEEN_SERVER_V0_2",
            "FROM": "W:OTHER",
            "TO": "W:GENESIS-A",
            "MAX_MOVES": 1,
            "SINGLE_USE": True,
            "PROOF_REF": None,
            "EXECUTABLE": False,
            "GATE_AUTHORITY": False,
            "ROUTING_AUTHORIZATION": "AUTHORIZED",
        }

        tick["value"] = 301
        wrong_from = client.post(
            "/api/live-transport/move",
            json=base,
            headers=headers,
        )
        assert wrong_from.status_code == 409
        assert "FROM position mismatch" in wrong_from.json()["detail"]

        unsafe = dict(base)
        unsafe["FROM"] = "W:START"
        unsafe["COMMAND_ID"] = "LTC-T300-GGGGGGGGGGGGGGGGGGGG"
        unsafe["EXECUTABLE"] = True
        unsafe_result = client.post(
            "/api/live-transport/move",
            json=unsafe,
            headers=headers,
        )
        assert unsafe_result.status_code == 422
        assert "EXECUTABLE must be false" in unsafe_result.json()["detail"]


if __name__ == "__main__":
    test_store_atomic_move_and_replay()
    test_private_api_attach_state_move()
    test_move_rejects_wrong_from_and_unsafe_flags()
    print("LIVE_TRANSPORT_STORE=PASS")
    print("LIVE_TRANSPORT_AUTH=PASS")
    print("LIVE_TRANSPORT_STATE_HASH=PASS")
    print("LIVE_TRANSPORT_SINGLE_USE=PASS")
    print("LIVE_TRANSPORT_FAIL_CLOSED=PASS")
