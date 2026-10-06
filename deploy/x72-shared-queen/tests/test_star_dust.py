from __future__ import annotations

import json
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.ant_birth import build_ant_birth
from app.brutobac_public import build_public_events, create_brutobac_public_router
from app.live_transport import LiveTransportStore
from app.star_dust import (
    DUST_DEFAULT_POSITION,
    DUST_MATERIAL_H256,
    DUST_MATERIAL_ID,
    DUST_SCHEMA,
    StarDustStore,
)


def queen_snapshot(tick: int = 500) -> dict:
    return {
        "entity_id": "QUEEN-X72-0072",
        "tick_count": tick,
        "generation": 9,
        "queen_mode": "STABLE",
        "integrity_match": True,
        "reference_h256": "a" * 64,
    }


def seed_ant(data_dir: Path, ant_id: str) -> None:
    receipt = build_ant_birth(
        ant_id,
        "Star dust consumer",
        "Validated SYNAPSE ant for resource consumption tests.",
        1_800_000_000.0,
    )
    store = LiveTransportStore(data_dir)
    with closing(sqlite3.connect(store.db_path)) as db:
        db.execute(
            "INSERT INTO carrier_ants(ant_id, receipt_json, created_at) VALUES (?, ?, ?)",
            (ant_id, json.dumps(receipt), 1_800_000_000.0),
        )
        db.commit()


def test_star_dust_sync_is_monotonic_and_attached_to_real_transport() -> None:
    with tempfile.TemporaryDirectory(prefix="antmux-star-dust-sync-") as tmp:
        data_dir = Path(tmp)
        dust = StarDustStore(data_dir)

        first = dust.sync(
            source_total=78,
            dust_per_transit=39,
            source_name="BROTOCULATEUR_PUBLIC_CRYSTAL_BRIDGE",
            trace_id="TRACE-DUST-0001",
            tick=500,
        )
        assert first["schema"] == DUST_SCHEMA
        assert first["quantity"] == 78
        assert first["produced_total"] == 78
        assert first["consumed_total"] == 0
        assert first["delta_produced"] == 78
        assert first["binding_state"] == "ATTACHED"
        assert first["position"] == DUST_DEFAULT_POSITION
        assert first["material"]["material_id"] == DUST_MATERIAL_ID
        assert first["material"]["material_h256"] == DUST_MATERIAL_H256
        assert first["carrier_ant_id"].startswith("ANT-")

        transport = LiveTransportStore(data_dir)
        attached = transport.read(
            ant_id=first["carrier_ant_id"],
            material_id=DUST_MATERIAL_ID,
        )
        assert attached["position"] == DUST_DEFAULT_POSITION
        assert attached["binding_state"] == "ATTACHED"

        same = dust.sync(
            source_total=78,
            dust_per_transit=39,
            source_name="BROTOCULATEUR_PUBLIC_CRYSTAL_BRIDGE",
            trace_id="TRACE-DUST-0001-RETRY",
            tick=501,
        )
        assert same["delta_produced"] == 0
        assert same["quantity"] == 78

        grown = dust.sync(
            source_total=117,
            dust_per_transit=39,
            source_name="BROTOCULATEUR_PUBLIC_CRYSTAL_BRIDGE",
            trace_id="TRACE-DUST-0002",
            tick=502,
        )
        assert grown["delta_produced"] == 39
        assert grown["quantity"] == 117
        assert grown["produced_total"] == 117

        with pytest.raises(HTTPException) as exc:
            dust.sync(
                source_total=100,
                dust_per_transit=39,
                source_name="BROTOCULATEUR_PUBLIC_CRYSTAL_BRIDGE",
                trace_id="TRACE-DUST-BACKWARD",
                tick=503,
            )
        assert exc.value.status_code == 409
        assert "moved backwards" in str(exc.value.detail)


def test_star_dust_consumption_is_bounded_colocated_and_idempotent() -> None:
    with tempfile.TemporaryDirectory(prefix="antmux-star-dust-consume-") as tmp:
        data_dir = Path(tmp)
        dust = StarDustStore(data_dir)
        initial = dust.sync(
            source_total=117,
            dust_per_transit=39,
            source_name="BROTOCULATEUR_PUBLIC_CRYSTAL_BRIDGE",
            trace_id="TRACE-DUST-CONSUME-SEED",
            tick=600,
        )
        carrier = initial["carrier_ant_id"]

        receipt = dust.consume(
            consume_id="DUST-CONSUME-0001",
            ant_id=carrier,
            amount=39,
            position=DUST_DEFAULT_POSITION,
            trace_id="TRACE-DUST-CONSUME-0001",
            tick=601,
        )
        assert receipt["event_type"] == "DUST_CONSUMED"
        assert receipt["amount"] == 39
        assert receipt["quantity_after"] == 78
        assert receipt["integrity_match"] is True

        replay = dust.consume(
            consume_id="DUST-CONSUME-0001",
            ant_id=carrier,
            amount=39,
            position=DUST_DEFAULT_POSITION,
            trace_id="TRACE-DUST-CONSUME-0001",
            tick=602,
        )
        assert replay == receipt
        assert dust.public_state()["quantity"] == 78

        with pytest.raises(HTTPException) as exc:
            dust.consume(
                consume_id="DUST-CONSUME-TOO-MUCH",
                ant_id=carrier,
                amount=79,
                position=DUST_DEFAULT_POSITION,
                trace_id="TRACE-DUST-CONSUME-TOO-MUCH",
                tick=603,
            )
        assert exc.value.status_code == 409
        assert "insufficient" in str(exc.value.detail)
        assert dust.public_state()["quantity"] == 78

        other_ant = "ANT-111111111111"
        seed_ant(data_dir, other_ant)
        transport = LiveTransportStore(data_dir)
        other_material = "MAT-MATH-111111111111111111111111"
        transport.attach(
            ant_id=other_ant,
            material_id=other_material,
            material_h256="1" * 64,
            position="W:OTHER",
            tick=604,
        )

        with pytest.raises(HTTPException) as exc:
            dust.consume(
                consume_id="DUST-CONSUME-NOT-COLOCATED",
                ant_id=other_ant,
                amount=1,
                position=DUST_DEFAULT_POSITION,
                trace_id="TRACE-DUST-NOT-COLOCATED",
                tick=605,
            )
        assert exc.value.status_code == 409
        assert "not colocated" in str(exc.value.detail)

        transport.move(
            command_id="LTC-T606-11111111111111111111",
            authorization_id="LTA-T605-22222222222222222222",
            authorization_h256="2" * 64,
            ant_id=other_ant,
            material_id=other_material,
            material_h256="1" * 64,
            from_position="W:OTHER",
            to_position=DUST_DEFAULT_POSITION,
            requested_at_tick=606,
            executed_at_tick=607,
        )
        colocated = dust.consume(
            consume_id="DUST-CONSUME-COLOCATED",
            ant_id=other_ant,
            amount=1,
            position=DUST_DEFAULT_POSITION,
            trace_id="TRACE-DUST-COLOCATED",
            tick=608,
        )
        assert colocated["quantity_after"] == 77
        state = dust.public_state()
        assert state["quantity"] == 77
        assert state["consumed_total"] == 40
        assert state["produced_total"] == 117


def test_star_dust_is_published_in_brutobac_and_public_cannot_mutate() -> None:
    with tempfile.TemporaryDirectory(prefix="antmux-star-dust-public-") as tmp:
        data_dir = Path(tmp)
        dust = StarDustStore(data_dir)
        dust.sync(
            source_total=39,
            dust_per_transit=39,
            source_name="BROTOCULATEUR_PUBLIC_CRYSTAL_BRIDGE",
            trace_id="TRACE-DUST-PUBLIC",
            tick=700,
        )

        events = build_public_events(data_dir, lambda: queen_snapshot(701))
        resources = [event for event in events if event.get("event_type") == "RESOURCE_STATE"]
        assert len(resources) == 1
        resource = resources[0]
        assert resource["material"]["material_id"] == DUST_MATERIAL_ID
        assert resource["resource"]["quantity"] == 39
        assert resource["resource"]["produced_total"] == 39
        assert resource["metadata"]["integrity_match"] is True

        app = FastAPI()
        app.include_router(create_brutobac_public_router(data_dir, lambda: queen_snapshot(702)))
        client = TestClient(app)

        public_state = client.get("/api/brutobac/dust/state")
        assert public_state.status_code == 200
        assert public_state.json()["quantity"] == 39
        assert public_state.json()["integrity_match"] is True

        unauthorized = client.post(
            "/api/brutobac/internal/dust/sync",
            json={
                "SOURCE_TOTAL": 78,
                "DUST_PER_TRANSIT": 39,
                "SOURCE": "BROTOCULATEUR_PUBLIC_CRYSTAL_BRIDGE",
                "TRACE_ID": "TRACE-DUST-NO-TOKEN",
            },
        )
        assert unauthorized.status_code == 401
        assert dust.public_state()["quantity"] == 39


if __name__ == "__main__":
    test_star_dust_sync_is_monotonic_and_attached_to_real_transport()
    test_star_dust_consumption_is_bounded_colocated_and_idempotent()
    test_star_dust_is_published_in_brutobac_and_public_cannot_mutate()
    print("STAR_DUST_SYNC_MONOTONIC=PASS")
    print("STAR_DUST_REAL_TRANSPORT=PASS")
    print("STAR_DUST_CONSUME_BOUNDED=PASS")
    print("STAR_DUST_COLOCATION=PASS")
    print("STAR_DUST_PUBLIC_READ_ONLY=PASS")
