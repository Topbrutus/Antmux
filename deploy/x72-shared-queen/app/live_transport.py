from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from typing import Any, Callable

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from .ant_birth import build_ant_birth


SCHEMA = "ANTMUX-LIVE-FOURMI-TRANSPORT-v0.1"
AUTHORITY = "QUEEN_SERVER_V0_2"
ROUTER_PREFIX = "/api/live-transport"
TOKEN_FILE_NAME = "live-transport-token"
DB_FILE_NAME = "live-transport.db"
JOURNAL_DB_FILE_NAME = "public-journal.db"
MAX_COMMAND_AGE_TICKS = 65536


def _utc_iso(now: float | None = None) -> str:
    stamp = time.time() if now is None else float(now)
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(stamp)) + f".{int((stamp % 1) * 1000):03d}Z"


def _canonical_h256(payload: dict[str, Any]) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _world_ref(value: str, label: str) -> str:
    text = str(value).strip().upper()
    if not text.startswith("W:") or len(text) < 3 or len(text) > 34:
        raise HTTPException(status_code=422, detail=f"{label} must be a W: reference")
    suffix = text[2:]
    if not all(ch.isdigit() or ("A" <= ch <= "Z") or ch == "-" for ch in suffix):
        raise HTTPException(status_code=422, detail=f"{label} contains unsupported characters")
    return text


def _ant_id(value: str) -> str:
    text = str(value).strip().upper()
    if len(text) != 16 or not text.startswith("ANT-"):
        raise HTTPException(status_code=422, detail="ANT_ID format invalid")
    suffix = text[4:]
    if len(suffix) != 12 or any(ch not in "0123456789ABCDEF" for ch in suffix):
        raise HTTPException(status_code=422, detail="ANT_ID format invalid")
    return text


def _material_id(value: str) -> str:
    text = str(value).strip().upper()
    prefix = "MAT-MATH-"
    if not text.startswith(prefix) or len(text) != len(prefix) + 24:
        raise HTTPException(status_code=422, detail="MATERIAL_ID format invalid")
    suffix = text[len(prefix):]
    if any(ch not in "0123456789ABCDEF" for ch in suffix):
        raise HTTPException(status_code=422, detail="MATERIAL_ID format invalid")
    return text


def _h256(value: str, label: str) -> str:
    text = str(value).strip().lower()
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise HTTPException(status_code=422, detail=f"{label} must be SHA-256 hex")
    return text


def _bounded_id(value: str, label: str, prefix: str, max_len: int = 128) -> str:
    text = str(value).strip().upper()
    if not text.startswith(prefix) or len(text) < len(prefix) + 4 or len(text) > max_len:
        raise HTTPException(status_code=422, detail=f"{label} format invalid")
    if any(not (ch.isdigit() or ("A" <= ch <= "Z") or ch == "-") for ch in text):
        raise HTTPException(status_code=422, detail=f"{label} contains unsupported characters")
    return text


def _ensure_secret(path: Path, bytes_count: int = 32) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    value = secrets.token_urlsafe(bytes_count)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        fd = os.open(path, flags, 0o600)
    except FileExistsError:
        return
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(value + "\n")


def load_transport_token(data_dir: Path) -> str:
    direct = os.environ.get("ANTMUX_LIVE_TRANSPORT_TOKEN", "").strip()
    if direct:
        return direct

    configured = os.environ.get("ANTMUX_LIVE_TRANSPORT_TOKEN_FILE", "").strip()
    path = Path(configured) if configured else data_dir / TOKEN_FILE_NAME
    _ensure_secret(path)
    token = path.read_text(encoding="utf-8").strip()
    if not token:
        raise RuntimeError("live transport token file is empty")
    return token


class AttachRequest(BaseModel):
    ANT_ID: str
    MATERIAL_ID: str
    MATERIAL_H256: str
    POSITION: str
    TRACE_ID: str = Field(min_length=4, max_length=96)


class MoveRequest(BaseModel):
    COMMAND_ID: str
    AUTHORIZATION_ID: str
    AUTHORIZATION_H256: str
    ANT_ID: str
    MATERIAL_ID: str
    MATERIAL_H256: str
    REQUESTED_AT_TICK: int = Field(ge=0)
    CLOCK_AUTHORITY: str
    FROM: str
    TO: str
    MAX_MOVES: int
    SINGLE_USE: bool
    PROOF_REF: None = None
    EXECUTABLE: bool
    GATE_AUTHORITY: bool
    ROUTING_AUTHORIZATION: str


class LiveTransportStore:
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / DB_FILE_NAME
        self._init_db()

    def _init_db(self) -> None:
        with closing(sqlite3.connect(self.db_path)) as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS transport_state (
                    material_id TEXT PRIMARY KEY,
                    material_h256 TEXT NOT NULL,
                    ant_id TEXT NOT NULL,
                    position TEXT NOT NULL,
                    binding_state TEXT NOT NULL,
                    attached_tick INTEGER NOT NULL,
                    updated_tick INTEGER NOT NULL,
                    last_move_tick INTEGER,
                    last_command_id TEXT,
                    last_authorization_id TEXT,
                    state_version INTEGER NOT NULL
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS move_commands (
                    command_id TEXT PRIMARY KEY,
                    authorization_id TEXT NOT NULL UNIQUE,
                    authorization_h256 TEXT NOT NULL,
                    ant_id TEXT NOT NULL,
                    material_id TEXT NOT NULL,
                    material_h256 TEXT NOT NULL,
                    from_position TEXT NOT NULL,
                    to_position TEXT NOT NULL,
                    requested_at_tick INTEGER NOT NULL,
                    executed_at_tick INTEGER NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS carrier_ants (
                    ant_id TEXT PRIMARY KEY,
                    receipt_json TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )
            db.commit()

    @staticmethod
    def _validated_ant_receipt(receipt_json: str, ant_id: str) -> dict[str, Any]:
        try:
            receipt = json.loads(receipt_json)
        except (TypeError, json.JSONDecodeError) as exc:
            raise HTTPException(status_code=503, detail="ant birth receipt malformed") from exc

        if not isinstance(receipt, dict):
            raise HTTPException(status_code=503, detail="ant birth receipt malformed")
        if receipt.get("schema") != "ANTMUX-ANT-BIRTH-v1":
            raise HTTPException(status_code=503, detail="ant birth schema mismatch")
        if receipt.get("ant_id") != ant_id:
            raise HTTPException(status_code=503, detail="ant birth identity mismatch")
        if receipt.get("role") != "SYNAPSE":
            raise HTTPException(status_code=409, detail="ant role is not SYNAPSE")
        return receipt

    def bootstrap_system_ant(self) -> dict[str, Any]:
        with closing(sqlite3.connect(self.db_path)) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT ant_id, receipt_json FROM carrier_ants ORDER BY created_at ASC LIMIT 1"
            ).fetchone()
            if row is not None:
                db.commit()
                return self._validated_ant_receipt(row[1], row[0])

            now = time.time()
            ant_id = "ANT-" + secrets.token_hex(6).upper()
            receipt = build_ant_birth(
                ant_id,
                "Brutus live transport carrier",
                "Private system carrier for bounded Brutus transport.",
                now,
            )
            db.execute(
                """
                INSERT INTO carrier_ants(ant_id, receipt_json, created_at)
                VALUES (?, ?, ?)
                """,
                (
                    ant_id,
                    json.dumps(receipt, ensure_ascii=False, separators=(",", ":")),
                    now,
                ),
            )
            db.commit()
            return receipt

    def read_ant_receipt(self, ant_id: str) -> dict[str, Any]:
        journal_db = self.data_dir / JOURNAL_DB_FILE_NAME
        row = None

        if journal_db.exists():
            try:
                with closing(sqlite3.connect(journal_db)) as db:
                    row = db.execute(
                        "SELECT receipt_json FROM ants WHERE id=?",
                        (ant_id,),
                    ).fetchone()
            except sqlite3.Error as exc:
                raise HTTPException(status_code=503, detail="ant registry unavailable") from exc

        if row is not None:
            return self._validated_ant_receipt(row[0], ant_id)

        with closing(sqlite3.connect(self.db_path)) as db:
            carrier = db.execute(
                "SELECT receipt_json FROM carrier_ants WHERE ant_id=?",
                (ant_id,),
            ).fetchone()

        if carrier is None:
            raise HTTPException(status_code=404, detail="ant birth receipt not found")

        return self._validated_ant_receipt(carrier[0], ant_id)

    def attach(
        self,
        *,
        ant_id: str,
        material_id: str,
        material_h256: str,
        position: str,
        tick: int,
    ) -> dict[str, Any]:
        with closing(sqlite3.connect(self.db_path)) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                """
                SELECT material_h256, ant_id, position, binding_state,
                       attached_tick, updated_tick, state_version
                FROM transport_state
                WHERE material_id=?
                """,
                (material_id,),
            ).fetchone()

            if row is not None:
                same = (
                    row[0] == material_h256
                    and row[1] == ant_id
                    and row[2] == position
                    and row[3] == "ATTACHED"
                )
                if not same:
                    db.rollback()
                    raise HTTPException(
                        status_code=409,
                        detail="material already attached with different runtime state",
                    )
                db.commit()
                return {
                    "material_id": material_id,
                    "material_h256": row[0],
                    "ant_id": row[1],
                    "position": row[2],
                    "binding_state": row[3],
                    "attached_tick": int(row[4]),
                    "updated_tick": int(row[5]),
                    "last_move_tick": None,
                    "last_command_id": None,
                    "last_authorization_id": None,
                    "state_version": int(row[6]),
                }

            db.execute(
                """
                INSERT INTO transport_state(
                    material_id, material_h256, ant_id, position, binding_state,
                    attached_tick, updated_tick, last_move_tick,
                    last_command_id, last_authorization_id, state_version
                ) VALUES (?, ?, ?, ?, 'ATTACHED', ?, ?, NULL, NULL, NULL, 1)
                """,
                (material_id, material_h256, ant_id, position, tick, tick),
            )
            db.commit()
            return {
                "material_id": material_id,
                "material_h256": material_h256,
                "ant_id": ant_id,
                "position": position,
                "binding_state": "ATTACHED",
                "attached_tick": tick,
                "updated_tick": tick,
                "last_move_tick": None,
                "last_command_id": None,
                "last_authorization_id": None,
                "state_version": 1,
            }

    def read(self, *, ant_id: str, material_id: str) -> dict[str, Any]:
        with closing(sqlite3.connect(self.db_path)) as db:
            row = db.execute(
                """
                SELECT material_h256, ant_id, position, binding_state,
                       attached_tick, updated_tick, last_move_tick,
                       last_command_id, last_authorization_id, state_version
                FROM transport_state
                WHERE material_id=?
                """,
                (material_id,),
            ).fetchone()

        if row is None:
            raise HTTPException(status_code=404, detail="transport material not attached")
        if row[1] != ant_id:
            raise HTTPException(status_code=404, detail="transport ant/material pair not found")

        return {
            "material_id": material_id,
            "material_h256": row[0],
            "ant_id": row[1],
            "position": row[2],
            "binding_state": row[3],
            "attached_tick": int(row[4]),
            "updated_tick": int(row[5]),
            "last_move_tick": None if row[6] is None else int(row[6]),
            "last_command_id": row[7],
            "last_authorization_id": row[8],
            "state_version": int(row[9]),
        }

    def move(
        self,
        *,
        command_id: str,
        authorization_id: str,
        authorization_h256: str,
        ant_id: str,
        material_id: str,
        material_h256: str,
        from_position: str,
        to_position: str,
        requested_at_tick: int,
        executed_at_tick: int,
    ) -> dict[str, Any]:
        if requested_at_tick > executed_at_tick:
            raise HTTPException(status_code=409, detail="requested tick is in the future")
        if executed_at_tick - requested_at_tick > MAX_COMMAND_AGE_TICKS:
            raise HTTPException(status_code=409, detail="transport command is stale")

        with closing(sqlite3.connect(self.db_path)) as db:
            db.execute("BEGIN IMMEDIATE")

            replay = db.execute(
                """
                SELECT command_id, authorization_id
                FROM move_commands
                WHERE command_id=? OR authorization_id=?
                """,
                (command_id, authorization_id),
            ).fetchone()
            if replay is not None:
                db.rollback()
                raise HTTPException(
                    status_code=409,
                    detail="single-use transport command or authorization already consumed",
                )

            row = db.execute(
                """
                SELECT material_h256, ant_id, position, binding_state, state_version
                FROM transport_state
                WHERE material_id=?
                """,
                (material_id,),
            ).fetchone()
            if row is None:
                db.rollback()
                raise HTTPException(status_code=404, detail="transport material not attached")
            if row[0] != material_h256:
                db.rollback()
                raise HTTPException(status_code=409, detail="material hash mismatch")
            if row[1] != ant_id:
                db.rollback()
                raise HTTPException(status_code=409, detail="carrier ANT mismatch")
            if row[3] != "ATTACHED":
                db.rollback()
                raise HTTPException(status_code=409, detail="material is not ATTACHED")
            if row[2] != from_position:
                db.rollback()
                raise HTTPException(status_code=409, detail="runtime FROM position mismatch")

            next_version = int(row[4]) + 1
            db.execute(
                """
                UPDATE transport_state
                SET position=?, updated_tick=?, last_move_tick=?,
                    last_command_id=?, last_authorization_id=?, state_version=?
                WHERE material_id=?
                """,
                (
                    to_position,
                    executed_at_tick,
                    executed_at_tick,
                    command_id,
                    authorization_id,
                    next_version,
                    material_id,
                ),
            )
            db.execute(
                """
                INSERT INTO move_commands(
                    command_id, authorization_id, authorization_h256,
                    ant_id, material_id, material_h256,
                    from_position, to_position,
                    requested_at_tick, executed_at_tick, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    command_id,
                    authorization_id,
                    authorization_h256,
                    ant_id,
                    material_id,
                    material_h256,
                    from_position,
                    to_position,
                    requested_at_tick,
                    executed_at_tick,
                    time.time(),
                ),
            )
            db.commit()

        return {
            "material_id": material_id,
            "material_h256": material_h256,
            "ant_id": ant_id,
            "position": to_position,
            "binding_state": "ATTACHED",
            "updated_tick": executed_at_tick,
            "last_move_tick": executed_at_tick,
            "last_command_id": command_id,
            "last_authorization_id": authorization_id,
            "state_version": next_version,
        }


def create_live_transport_router(
    data_dir: Path,
    get_queen_snapshot: Callable[[], dict[str, Any]],
    *,
    transport_token: str | None = None,
) -> APIRouter:
    store = LiveTransportStore(Path(data_dir))
    token = (transport_token or load_transport_token(Path(data_dir))).strip()
    if not token:
        raise RuntimeError("live transport token is empty")

    router = APIRouter(prefix=ROUTER_PREFIX, tags=["live-fourmi-transport"])

    def require_token(request: Request) -> None:
        supplied = request.headers.get("authorization", "").strip()
        if supplied.startswith("Bearer "):
            supplied = supplied[7:].strip()
        else:
            supplied = ""
        if not hmac.compare_digest(supplied, token):
            raise HTTPException(status_code=401, detail="live transport authorization required")

    def queen_snapshot() -> dict[str, Any]:
        value = get_queen_snapshot()
        if not isinstance(value, dict):
            raise HTTPException(status_code=503, detail="Queen snapshot unavailable")
        required = {
            "entity_id",
            "tick_count",
            "generation",
            "queen_mode",
            "integrity_match",
            "reference_h256",
        }
        if set(value.keys()) != required:
            raise HTTPException(status_code=503, detail="Queen snapshot shape invalid")
        if not isinstance(value["entity_id"], str) or not value["entity_id"]:
            raise HTTPException(status_code=503, detail="Queen entity unavailable")
        if type(value["tick_count"]) is not int or value["tick_count"] < 0:
            raise HTTPException(status_code=503, detail="Queen tick unavailable")
        if type(value["generation"]) is not int or value["generation"] < 0:
            raise HTTPException(status_code=503, detail="Queen generation unavailable")
        if not isinstance(value["queen_mode"], str) or not value["queen_mode"]:
            raise HTTPException(status_code=503, detail="Queen mode unavailable")
        if value["integrity_match"] is not True:
            raise HTTPException(status_code=503, detail="Queen integrity mismatch")
        reference = str(value["reference_h256"]).strip().lower()
        if len(reference) != 64 or any(ch not in "0123456789abcdef" for ch in reference):
            raise HTTPException(status_code=503, detail="Queen reference hash unavailable")
        return {
            "entity_id": value["entity_id"],
            "tick_count": value["tick_count"],
            "generation": value["generation"],
            "queen_mode": value["queen_mode"],
            "integrity_match": True,
            "reference_h256": reference,
        }

    def snapshot(state: dict[str, Any]) -> dict[str, Any]:
        now = time.time()
        queen = queen_snapshot()
        payload = {
            "schema": SCHEMA,
            "authority": AUTHORITY,
            "source_endpoint": f"{ROUTER_PREFIX}/state",
            "observed_at_utc": _utc_iso(now),
            "tick": queen["tick_count"],
            "queen": queen,
            "ant_id": state["ant_id"],
            "position": state["position"],
            "material": {
                "material_id": state["material_id"],
                "material_h256": state["material_h256"],
                "binding_state": state["binding_state"],
            },
            "attached_tick": state.get("attached_tick"),
            "updated_tick": state.get("updated_tick"),
            "last_move_tick": state.get("last_move_tick"),
            "last_command_id": state.get("last_command_id"),
            "last_authorization_id": state.get("last_authorization_id"),
            "state_version": state["state_version"],
        }
        return {
            **payload,
            "state_h256": _canonical_h256(payload),
            "integrity_match": True,
        }

    @router.post("/bootstrap-ant")
    async def bootstrap_ant(request: Request) -> dict[str, Any]:
        require_token(request)
        return store.bootstrap_system_ant()

    @router.get("/ant/{ant_id}")
    async def ant_receipt(ant_id: str, request: Request) -> dict[str, Any]:
        require_token(request)
        return store.read_ant_receipt(_ant_id(ant_id))

    @router.post("/attach")
    async def attach(body: AttachRequest, request: Request) -> dict[str, Any]:
        require_token(request)
        ant_id = _ant_id(body.ANT_ID)
        store.read_ant_receipt(ant_id)
        material_id = _material_id(body.MATERIAL_ID)
        material_h256 = _h256(body.MATERIAL_H256, "MATERIAL_H256")
        position = _world_ref(body.POSITION, "POSITION")
        tick = queen_snapshot()["tick_count"]

        state = store.attach(
            ant_id=ant_id,
            material_id=material_id,
            material_h256=material_h256,
            position=position,
            tick=tick,
        )
        return snapshot(state)

    @router.get("/state/{ant_id}/{material_id}")
    async def state(ant_id: str, material_id: str, request: Request) -> dict[str, Any]:
        require_token(request)
        state_row = store.read(
            ant_id=_ant_id(ant_id),
            material_id=_material_id(material_id),
        )
        return snapshot(state_row)

    @router.post("/move")
    async def move(body: MoveRequest, request: Request) -> dict[str, Any]:
        require_token(request)

        if body.CLOCK_AUTHORITY != AUTHORITY:
            raise HTTPException(status_code=422, detail="CLOCK_AUTHORITY mismatch")
        if body.MAX_MOVES != 1:
            raise HTTPException(status_code=422, detail="MAX_MOVES must be 1")
        if body.SINGLE_USE is not True:
            raise HTTPException(status_code=422, detail="SINGLE_USE must be true")
        if body.PROOF_REF is not None:
            raise HTTPException(status_code=422, detail="PROOF_REF must be null")
        if body.EXECUTABLE is not False:
            raise HTTPException(status_code=422, detail="EXECUTABLE must be false")
        if body.GATE_AUTHORITY is not False:
            raise HTTPException(status_code=422, detail="GATE_AUTHORITY must be false")
        if body.ROUTING_AUTHORIZATION != "AUTHORIZED":
            raise HTTPException(status_code=422, detail="ROUTING_AUTHORIZATION must be AUTHORIZED")

        command_id = _bounded_id(body.COMMAND_ID, "COMMAND_ID", "LTC-T")
        authorization_id = _bounded_id(
            body.AUTHORIZATION_ID,
            "AUTHORIZATION_ID",
            "LTA-T",
        )
        authorization_h256 = _h256(body.AUTHORIZATION_H256, "AUTHORIZATION_H256")
        ant_id = _ant_id(body.ANT_ID)
        material_id = _material_id(body.MATERIAL_ID)
        material_h256 = _h256(body.MATERIAL_H256, "MATERIAL_H256")
        from_position = _world_ref(body.FROM, "FROM")
        to_position = _world_ref(body.TO, "TO")
        if from_position == to_position:
            raise HTTPException(status_code=422, detail="FROM and TO must differ")

        store.move(
            command_id=command_id,
            authorization_id=authorization_id,
            authorization_h256=authorization_h256,
            ant_id=ant_id,
            material_id=material_id,
            material_h256=material_h256,
            from_position=from_position,
            to_position=to_position,
            requested_at_tick=int(body.REQUESTED_AT_TICK),
            executed_at_tick=queen_snapshot()["tick_count"],
        )

        # Keep this acknowledgment shape intentionally minimal and exact:
        # Brutus treats it as acceptance only, never as movement proof.
        return {
            "STATUS": "ACCEPTED",
            "COMMAND_ID": command_id,
            "AUTHORIZATION_ID": authorization_id,
            "ANT_ID": ant_id,
            "MATERIAL_ID": material_id,
            "FROM": from_position,
            "TO": to_position,
        }

    return router


__all__ = [
    "SCHEMA",
    "AUTHORITY",
    "ROUTER_PREFIX",
    "LiveTransportStore",
    "create_live_transport_router",
    "load_transport_token",
]
