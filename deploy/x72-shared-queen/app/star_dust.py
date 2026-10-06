from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from typing import Any, Callable

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from .live_transport import AUTHORITY, DB_FILE_NAME, LiveTransportStore, _canonical_h256, _ant_id, _world_ref


DUST_SCHEMA = "ANTMUX-STAR-DUST-RESOURCE-v1"
DUST_RESOURCE_KIND = "BROTOCULATEUR_STAR_DUST"
DUST_UNIT = "DUST"
DUST_MATERIAL_ID = "MAT-MATH-6452A5149069851BE888F6A3"
DUST_MATERIAL_H256 = "6452a5149069851be888f6a3dc8717ca36301b5fd035e216aa5eab0a4a93d4ca"
DUST_DEFAULT_POSITION = "W:BROTOCULATEUR-OUT"
DUST_SOURCE = "BROTOCULATEUR_PUBLIC_CRYSTAL_BRIDGE"
DUST_TOKEN_SHA256 = "0f007385b6f9d4b7eeb2748605afe1a984a0a3bfa3f014d09e2a784ce9e5cd1a"


class DustSyncRequest(BaseModel):
    SOURCE_TOTAL: int = Field(ge=0)
    DUST_PER_TRANSIT: int = Field(default=39, ge=1, le=1_000_000_000)
    SOURCE: str = Field(default=DUST_SOURCE, min_length=4, max_length=96)
    TRACE_ID: str = Field(min_length=4, max_length=96)


class DustConsumeRequest(BaseModel):
    CONSUME_ID: str = Field(min_length=8, max_length=128)
    ANT_ID: str
    AMOUNT: int = Field(gt=0, le=1_000_000_000)
    POSITION: str
    TRACE_ID: str = Field(min_length=4, max_length=96)


def _require_dust_token(request: Request) -> None:
    header = request.headers.get("authorization", "")
    if not header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing star dust ingest token")
    token = header[7:].strip()
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    if not hmac.compare_digest(digest, DUST_TOKEN_SHA256):
        raise HTTPException(status_code=401, detail="invalid star dust ingest token")


def _state_hash(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        **payload,
        "state_h256": _canonical_h256(payload),
        "integrity_match": True,
    }


class StarDustStore:
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / DB_FILE_NAME
        self.transport = LiveTransportStore(self.data_dir)
        self._init_db()

    def _init_db(self) -> None:
        with closing(sqlite3.connect(self.db_path)) as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS star_dust_inventory (
                    material_id TEXT PRIMARY KEY,
                    material_h256 TEXT NOT NULL,
                    resource_kind TEXT NOT NULL,
                    unit TEXT NOT NULL,
                    quantity INTEGER NOT NULL CHECK(quantity >= 0),
                    produced_total INTEGER NOT NULL CHECK(produced_total >= 0),
                    consumed_total INTEGER NOT NULL CHECK(consumed_total >= 0),
                    source_total INTEGER NOT NULL CHECK(source_total >= 0),
                    source_name TEXT NOT NULL,
                    dust_per_transit INTEGER NOT NULL CHECK(dust_per_transit > 0),
                    updated_tick INTEGER NOT NULL,
                    state_version INTEGER NOT NULL,
                    latest_trace_id TEXT NOT NULL
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS star_dust_consumptions (
                    consume_id TEXT PRIMARY KEY,
                    ant_id TEXT NOT NULL,
                    amount INTEGER NOT NULL CHECK(amount > 0),
                    position TEXT NOT NULL,
                    tick INTEGER NOT NULL,
                    trace_id TEXT NOT NULL,
                    receipt_json TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS star_dust_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    ant_id TEXT,
                    delta INTEGER NOT NULL,
                    quantity_after INTEGER NOT NULL CHECK(quantity_after >= 0),
                    source_total INTEGER NOT NULL CHECK(source_total >= 0),
                    tick INTEGER NOT NULL,
                    trace_id TEXT NOT NULL,
                    event_h256 TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )
            db.commit()

    def _ensure_carrier(self, tick: int) -> dict[str, Any]:
        receipt = self.transport.bootstrap_system_ant()
        ant_id = receipt["ant_id"]
        try:
            state = self.transport.read(ant_id=ant_id, material_id=DUST_MATERIAL_ID)
        except HTTPException as exc:
            if exc.status_code != 404:
                raise
            state = self.transport.attach(
                ant_id=ant_id,
                material_id=DUST_MATERIAL_ID,
                material_h256=DUST_MATERIAL_H256,
                position=DUST_DEFAULT_POSITION,
                tick=tick,
            )
        if state["material_h256"] != DUST_MATERIAL_H256:
            raise HTTPException(status_code=409, detail="star dust material identity mismatch")
        return state

    def _read_inventory_row(self, db: sqlite3.Connection) -> tuple[Any, ...] | None:
        return db.execute(
            """
            SELECT quantity, produced_total, consumed_total, source_total,
                   source_name, dust_per_transit, updated_tick, state_version,
                   latest_trace_id
            FROM star_dust_inventory
            WHERE material_id=?
            """,
            (DUST_MATERIAL_ID,),
        ).fetchone()

    def public_state(self) -> dict[str, Any] | None:
        try:
            with closing(sqlite3.connect(self.db_path)) as db:
                row = self._read_inventory_row(db)
                transport_row = db.execute(
                    """
                    SELECT ant_id, position, binding_state, attached_tick,
                           updated_tick, last_move_tick, state_version
                    FROM transport_state
                    WHERE material_id=?
                    """,
                    (DUST_MATERIAL_ID,),
                ).fetchone()
        except sqlite3.Error as exc:
            raise HTTPException(status_code=503, detail="star dust ledger unavailable") from exc

        if row is None:
            return None

        carrier_ant_id = None
        position = DUST_DEFAULT_POSITION
        transport_version = 0
        binding_state = "UNATTACHED"
        attached_tick = None
        last_move_tick = None
        if transport_row is not None:
            carrier_ant_id = transport_row[0]
            position = transport_row[1]
            binding_state = transport_row[2]
            attached_tick = int(transport_row[3])
            last_move_tick = None if transport_row[5] is None else int(transport_row[5])
            transport_version = int(transport_row[6])

        payload = {
            "schema": DUST_SCHEMA,
            "authority": AUTHORITY,
            "material": {
                "material_id": DUST_MATERIAL_ID,
                "material_h256": DUST_MATERIAL_H256,
                "resource_kind": DUST_RESOURCE_KIND,
                "unit": DUST_UNIT,
            },
            "carrier_ant_id": carrier_ant_id,
            "position": position,
            "binding_state": binding_state,
            "quantity": int(row[0]),
            "produced_total": int(row[1]),
            "consumed_total": int(row[2]),
            "source_total": int(row[3]),
            "source": row[4],
            "dust_per_transit": int(row[5]),
            "updated_tick": int(row[6]),
            "state_version": int(row[7]),
            "latest_trace_id": row[8],
            "transport_state_version": transport_version,
            "attached_tick": attached_tick,
            "last_move_tick": last_move_tick,
        }
        return _state_hash(payload)

    def sync(
        self,
        *,
        source_total: int,
        dust_per_transit: int,
        source_name: str,
        trace_id: str,
        tick: int,
    ) -> dict[str, Any]:
        self._ensure_carrier(tick)
        source_name = str(source_name).strip().upper()
        if source_name != DUST_SOURCE:
            raise HTTPException(status_code=422, detail="unsupported star dust source")

        with closing(sqlite3.connect(self.db_path)) as db:
            db.execute("BEGIN IMMEDIATE")
            row = self._read_inventory_row(db)

            if row is None:
                quantity = int(source_total)
                produced_total = int(source_total)
                consumed_total = 0
                state_version = 1
                delta = int(source_total)
                db.execute(
                    """
                    INSERT INTO star_dust_inventory(
                        material_id, material_h256, resource_kind, unit,
                        quantity, produced_total, consumed_total, source_total,
                        source_name, dust_per_transit, updated_tick, state_version,
                        latest_trace_id
                    ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        DUST_MATERIAL_ID,
                        DUST_MATERIAL_H256,
                        DUST_RESOURCE_KIND,
                        DUST_UNIT,
                        quantity,
                        produced_total,
                        int(source_total),
                        source_name,
                        int(dust_per_transit),
                        int(tick),
                        state_version,
                        trace_id,
                    ),
                )
            else:
                previous_source_total = int(row[3])
                if source_total < previous_source_total:
                    db.rollback()
                    raise HTTPException(
                        status_code=409,
                        detail="star dust source counter moved backwards",
                    )
                delta = int(source_total) - previous_source_total
                if delta == 0:
                    db.commit()
                    state = self.public_state()
                    if state is None:
                        raise HTTPException(status_code=503, detail="star dust state unavailable")
                    return {**state, "delta_produced": 0}

                quantity = int(row[0]) + delta
                produced_total = int(row[1]) + delta
                consumed_total = int(row[2])
                state_version = int(row[7]) + 1
                db.execute(
                    """
                    UPDATE star_dust_inventory
                    SET quantity=?, produced_total=?, source_total=?,
                        source_name=?, dust_per_transit=?, updated_tick=?,
                        state_version=?, latest_trace_id=?
                    WHERE material_id=?
                    """,
                    (
                        quantity,
                        produced_total,
                        int(source_total),
                        source_name,
                        int(dust_per_transit),
                        int(tick),
                        state_version,
                        trace_id,
                        DUST_MATERIAL_ID,
                    ),
                )

            event_payload = {
                "event_type": "DUST_PRODUCED",
                "material_id": DUST_MATERIAL_ID,
                "delta": delta,
                "quantity_after": quantity,
                "source_total": int(source_total),
                "tick": int(tick),
                "trace_id": trace_id,
            }
            db.execute(
                """
                INSERT INTO star_dust_events(
                    event_type, ant_id, delta, quantity_after, source_total,
                    tick, trace_id, event_h256, created_at
                ) VALUES ('DUST_PRODUCED', NULL, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    delta,
                    quantity,
                    int(source_total),
                    int(tick),
                    trace_id,
                    _canonical_h256(event_payload),
                    time.time(),
                ),
            )
            db.commit()

        state = self.public_state()
        if state is None:
            raise HTTPException(status_code=503, detail="star dust state unavailable")
        return {**state, "delta_produced": delta}

    def consume(
        self,
        *,
        consume_id: str,
        ant_id: str,
        amount: int,
        position: str,
        trace_id: str,
        tick: int,
    ) -> dict[str, Any]:
        self.transport.read_ant_receipt(ant_id)

        with closing(sqlite3.connect(self.db_path)) as db:
            db.execute("BEGIN IMMEDIATE")
            replay = db.execute(
                """
                SELECT ant_id, amount, position, trace_id, receipt_json
                FROM star_dust_consumptions
                WHERE consume_id=?
                """,
                (consume_id,),
            ).fetchone()
            if replay is not None:
                if (
                    replay[0] != ant_id
                    or int(replay[1]) != int(amount)
                    or replay[2] != position
                    or replay[3] != trace_id
                ):
                    db.rollback()
                    raise HTTPException(status_code=409, detail="consume id replay mismatch")
                db.commit()
                return json.loads(replay[4])

            transport_row = db.execute(
                """
                SELECT ant_id, position, binding_state
                FROM transport_state
                WHERE material_id=?
                """,
                (DUST_MATERIAL_ID,),
            ).fetchone()
            if transport_row is None or transport_row[2] != "ATTACHED":
                db.rollback()
                raise HTTPException(status_code=409, detail="star dust material is not attached")
            dust_carrier = transport_row[0]
            dust_position = transport_row[1]
            if dust_position != position:
                db.rollback()
                raise HTTPException(status_code=409, detail="star dust position mismatch")

            if ant_id != dust_carrier:
                colocated = db.execute(
                    """
                    SELECT 1
                    FROM transport_state
                    WHERE ant_id=? AND binding_state='ATTACHED' AND position=?
                    LIMIT 1
                    """,
                    (ant_id, position),
                ).fetchone()
                if colocated is None:
                    db.rollback()
                    raise HTTPException(status_code=409, detail="consumer ANT is not colocated with star dust")

            row = self._read_inventory_row(db)
            if row is None:
                db.rollback()
                raise HTTPException(status_code=404, detail="star dust inventory not initialized")
            quantity = int(row[0])
            if amount > quantity:
                db.rollback()
                raise HTTPException(status_code=409, detail="insufficient star dust quantity")

            quantity_after = quantity - int(amount)
            consumed_total = int(row[2]) + int(amount)
            state_version = int(row[7]) + 1
            db.execute(
                """
                UPDATE star_dust_inventory
                SET quantity=?, consumed_total=?, updated_tick=?,
                    state_version=?, latest_trace_id=?
                WHERE material_id=?
                """,
                (
                    quantity_after,
                    consumed_total,
                    int(tick),
                    state_version,
                    trace_id,
                    DUST_MATERIAL_ID,
                ),
            )

            receipt_payload = {
                "schema": DUST_SCHEMA,
                "event_type": "DUST_CONSUMED",
                "authority": AUTHORITY,
                "consume_id": consume_id,
                "ant_id": ant_id,
                "material_id": DUST_MATERIAL_ID,
                "amount": int(amount),
                "position": position,
                "tick": int(tick),
                "trace_id": trace_id,
                "quantity_after": quantity_after,
                "state_version": state_version,
            }
            receipt = _state_hash(receipt_payload)
            db.execute(
                """
                INSERT INTO star_dust_consumptions(
                    consume_id, ant_id, amount, position, tick, trace_id,
                    receipt_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    consume_id,
                    ant_id,
                    int(amount),
                    position,
                    int(tick),
                    trace_id,
                    json.dumps(receipt, ensure_ascii=False, separators=(",", ":")),
                    time.time(),
                ),
            )
            event_payload = {
                "event_type": "DUST_CONSUMED",
                "material_id": DUST_MATERIAL_ID,
                "ant_id": ant_id,
                "delta": -int(amount),
                "quantity_after": quantity_after,
                "source_total": int(row[3]),
                "tick": int(tick),
                "trace_id": trace_id,
            }
            db.execute(
                """
                INSERT INTO star_dust_events(
                    event_type, ant_id, delta, quantity_after, source_total,
                    tick, trace_id, event_h256, created_at
                ) VALUES ('DUST_CONSUMED', ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ant_id,
                    -int(amount),
                    quantity_after,
                    int(row[3]),
                    int(tick),
                    trace_id,
                    _canonical_h256(event_payload),
                    time.time(),
                ),
            )
            db.commit()
            return receipt


def read_public_star_dust_state(data_dir: Path) -> dict[str, Any] | None:
    db_path = Path(data_dir) / DB_FILE_NAME
    if not db_path.exists():
        return None
    try:
        return StarDustStore(Path(data_dir)).public_state()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="star dust state unavailable") from exc


def create_star_dust_router(
    data_dir: Path,
    get_queen_snapshot: Callable[[], dict[str, Any]],
) -> APIRouter:
    store = StarDustStore(Path(data_dir))
    router = APIRouter(tags=["brutobac-star-dust"])

    def current_tick() -> int:
        snapshot = get_queen_snapshot()
        if not isinstance(snapshot, dict) or type(snapshot.get("tick_count")) is not int:
            raise HTTPException(status_code=503, detail="Queen tick unavailable")
        tick = int(snapshot["tick_count"])
        if tick < 0:
            raise HTTPException(status_code=503, detail="Queen tick unavailable")
        return tick

    @router.get("/dust/state")
    async def dust_state() -> dict[str, Any]:
        state = store.public_state()
        if state is None:
            payload = {
                "schema": DUST_SCHEMA,
                "authority": AUTHORITY,
                "material": {
                    "material_id": DUST_MATERIAL_ID,
                    "material_h256": DUST_MATERIAL_H256,
                    "resource_kind": DUST_RESOURCE_KIND,
                    "unit": DUST_UNIT,
                },
                "carrier_ant_id": None,
                "position": DUST_DEFAULT_POSITION,
                "binding_state": "UNINITIALIZED",
                "quantity": 0,
                "produced_total": 0,
                "consumed_total": 0,
                "source_total": 0,
                "source": DUST_SOURCE,
                "dust_per_transit": 39,
                "updated_tick": current_tick(),
                "state_version": 0,
                "latest_trace_id": None,
                "transport_state_version": 0,
                "attached_tick": None,
                "last_move_tick": None,
            }
            return _state_hash(payload)
        return state

    @router.post("/internal/dust/sync")
    async def sync_dust(body: DustSyncRequest, request: Request) -> dict[str, Any]:
        _require_dust_token(request)
        return store.sync(
            source_total=int(body.SOURCE_TOTAL),
            dust_per_transit=int(body.DUST_PER_TRANSIT),
            source_name=body.SOURCE,
            trace_id=body.TRACE_ID,
            tick=current_tick(),
        )

    @router.post("/internal/dust/consume")
    async def consume_dust(body: DustConsumeRequest, request: Request) -> dict[str, Any]:
        _require_dust_token(request)
        return store.consume(
            consume_id=str(body.CONSUME_ID).strip().upper(),
            ant_id=_ant_id(body.ANT_ID),
            amount=int(body.AMOUNT),
            position=_world_ref(body.POSITION, "POSITION"),
            trace_id=body.TRACE_ID,
            tick=current_tick(),
        )

    return router


__all__ = [
    "DUST_SCHEMA",
    "DUST_RESOURCE_KIND",
    "DUST_UNIT",
    "DUST_MATERIAL_ID",
    "DUST_MATERIAL_H256",
    "DUST_DEFAULT_POSITION",
    "DUST_SOURCE",
    "StarDustStore",
    "read_public_star_dust_state",
    "create_star_dust_router",
]
