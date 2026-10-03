from __future__ import annotations

import asyncio
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any, Callable, Iterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse


PUBLIC_SCHEMA = "BRUTUS-AQUARIUM-EVENT-v1"
PUBLIC_SOURCE = "ANTMUX_BRUTOBAC_PUBLIC"
AUTHORITY = "QUEEN_SERVER_V0_2"
ROUTER_PREFIX = "/api/brutobac"
LIVE_DB_FILE = "live-transport.db"
JOURNAL_DB_FILE = "public-journal.db"
UI_ROOT = Path(__file__).resolve().parent / "brutobac_ui"


def _queen_snapshot(get_queen_snapshot: Callable[[], dict[str, Any]]) -> dict[str, Any]:
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


def _transport_rows(data_dir: Path) -> list[dict[str, Any]]:
    db_path = Path(data_dir) / LIVE_DB_FILE
    if not db_path.exists():
        return []

    try:
        with closing(sqlite3.connect(db_path)) as db:
            rows = db.execute(
                """
                SELECT material_id, material_h256, ant_id, position, binding_state,
                       attached_tick, updated_tick, last_move_tick, state_version
                FROM transport_state
                WHERE binding_state='ATTACHED'
                ORDER BY ant_id ASC, material_id ASC
                """
            ).fetchall()
    except sqlite3.Error as exc:
        raise HTTPException(status_code=503, detail="live transport state unavailable") from exc

    return [
        {
            "material_id": row[0],
            "material_h256": row[1],
            "ant_id": row[2],
            "position": row[3],
            "binding_state": row[4],
            "attached_tick": int(row[5]),
            "updated_tick": int(row[6]),
            "last_move_tick": None if row[7] is None else int(row[7]),
            "state_version": int(row[8]),
        }
        for row in rows
    ]


def _receipt_from_db(path: Path, query: str, ant_id: str) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        with closing(sqlite3.connect(path)) as db:
            row = db.execute(query, (ant_id,)).fetchone()
    except sqlite3.Error:
        return None
    if row is None:
        return None
    try:
        value = json.loads(row[0])
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(value, dict):
        return None
    if value.get("schema") != "ANTMUX-ANT-BIRTH-v1":
        return None
    if value.get("ant_id") != ant_id:
        return None
    return value


def _ant_receipt(data_dir: Path, ant_id: str) -> dict[str, Any] | None:
    root = Path(data_dir)
    receipt = _receipt_from_db(
        root / JOURNAL_DB_FILE,
        "SELECT receipt_json FROM ants WHERE id=?",
        ant_id,
    )
    if receipt is not None:
        return receipt

    return _receipt_from_db(
        root / LIVE_DB_FILE,
        "SELECT receipt_json FROM carrier_ants WHERE ant_id=?",
        ant_id,
    )


def _queen_visual_state(mode: str) -> str:
    if mode == "SLEEP":
        return "IDLE"
    if mode in {"FAULT", "AUTO_REPAIR"}:
        return "RETURNING"
    return "RESONATING"


def build_public_events(
    data_dir: Path,
    get_queen_snapshot: Callable[[], dict[str, Any]],
) -> list[dict[str, Any]]:
    queen = _queen_snapshot(get_queen_snapshot)
    tick = queen["tick_count"]

    events: list[dict[str, Any]] = [
        {
            "schema": PUBLIC_SCHEMA,
            "event_type": "SYSTEM_STATUS",
            "tick": tick,
            "metadata": {
                "connection_status": "CONNECTED",
                "connection_source": "SSE",
                "source": PUBLIC_SOURCE,
                "authority": AUTHORITY,
                "bridge_mode": "READ_ONLY",
                "integrity_match": True,
                "queen_entity_id": queen["entity_id"],
                "queen_generation": queen["generation"],
                "queen_mode": queen["queen_mode"],
            },
        },
        {
            "schema": PUBLIC_SCHEMA,
            "event_type": "ANT_STATE",
            "tick": tick,
            "ant_id": queen["entity_id"],
            "role": "QUEEN",
            "state": _queen_visual_state(queen["queen_mode"]),
            "position": "CENTER",
            "state_version": max(1, queen["generation"]),
            "metadata": {
                "source": PUBLIC_SOURCE,
                "authority_mode": "READ_ONLY_MIRROR",
                "queen_mode": queen["queen_mode"],
                "integrity_match": True,
                "reference_h256": queen["reference_h256"],
            },
        },
    ]

    for state in _transport_rows(Path(data_dir)):
        receipt = _ant_receipt(Path(data_dir), state["ant_id"])
        if receipt is None:
            # Public projection is fail-closed: an attached state without a
            # validated persisted birth receipt is not published.
            continue

        role = receipt.get("role")
        ant_state = receipt.get("state")
        if role != "SYNAPSE" or ant_state != "SINGING_TO_MEET":
            continue

        project_soul = receipt.get("project_soul")
        if not isinstance(project_soul, dict):
            project_soul = {}

        events.append(
            {
                "schema": PUBLIC_SCHEMA,
                "event_type": "ANT_STATE",
                "tick": tick,
                "ant_id": state["ant_id"],
                "role": role,
                "state": ant_state,
                "position": state["position"],
                "state_version": state["state_version"],
                "last_move_tick": state["last_move_tick"],
                "material": {
                    "material_id": state["material_id"],
                    "material_h256": state["material_h256"],
                },
                "metadata": {
                    "source": PUBLIC_SOURCE,
                    "authority_mode": "READ_ONLY_MIRROR",
                    "binding_state": state["binding_state"],
                    "attached_tick": state["attached_tick"],
                    "updated_tick": state["updated_tick"],
                    "triad_name": receipt.get("triad_name"),
                    "lineage": project_soul.get("lineage"),
                    "birth_tick_ms": project_soul.get("birth_tick_ms"),
                    "memory_id": project_soul.get("memory_id"),
                },
            }
        )

    return events


def _event_signature(event: dict[str, Any]) -> tuple[Any, ...]:
    return (
        event.get("event_type"),
        event.get("ant_id"),
        event.get("role"),
        event.get("state"),
        event.get("position"),
        event.get("state_version"),
        json.dumps(event.get("material"), sort_keys=True, separators=(",", ":")),
        json.dumps(event.get("metadata"), sort_keys=True, separators=(",", ":")),
    )


def create_brutobac_public_router(
    data_dir: Path,
    get_queen_snapshot: Callable[[], dict[str, Any]],
) -> APIRouter:
    router = APIRouter(prefix=ROUTER_PREFIX, tags=["brutobac-public-readonly"])

    @router.get("/")
    async def ui_index() -> FileResponse:
        index_path = UI_ROOT / "index.html"
        if not index_path.is_file():
            raise HTTPException(status_code=503, detail="BrutoBac UI bundle unavailable")
        return FileResponse(index_path, headers={"Cache-Control": "no-cache, no-transform"})

    @router.get("/assets/{asset_path:path}")
    async def ui_asset(asset_path: str) -> FileResponse:
        assets_root = (UI_ROOT / "assets").resolve()
        candidate = (assets_root / asset_path).resolve()
        if assets_root not in candidate.parents or not candidate.is_file():
            raise HTTPException(status_code=404, detail="BrutoBac asset not found")
        return FileResponse(candidate, headers={"Cache-Control": "public, max-age=31536000, immutable"})

    @router.get("/snapshot")
    async def snapshot() -> list[dict[str, Any]]:
        return build_public_events(Path(data_dir), get_queen_snapshot)

    @router.get("/stream")
    async def stream() -> StreamingResponse:
        async def generate() -> Iterator[str]:
            previous: dict[str, tuple[Any, ...]] = {}
            heartbeat_count = 0

            while True:
                events = build_public_events(Path(data_dir), get_queen_snapshot)

                # SYSTEM_STATUS is the authoritative heartbeat and carries the
                # current Queen tick. Entity states are emitted only on change.
                for event in events:
                    if event.get("event_type") == "SYSTEM_STATUS":
                        yield f"data: {json.dumps(event, ensure_ascii=False, separators=(',', ':'))}\n\n"
                        continue

                    key = str(event.get("ant_id") or "UNKNOWN")
                    signature = _event_signature(event)
                    if previous.get(key) != signature:
                        previous[key] = signature
                        yield f"data: {json.dumps(event, ensure_ascii=False, separators=(',', ':'))}\n\n"

                heartbeat_count += 1
                if heartbeat_count % 15 == 0:
                    yield ": brutobac-heartbeat\n\n"

                await asyncio.sleep(1.0)

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "X-Accel-Buffering": "no",
            },
        )

    return router


__all__ = [
    "PUBLIC_SCHEMA",
    "PUBLIC_SOURCE",
    "ROUTER_PREFIX",
    "UI_ROOT",
    "build_public_events",
    "create_brutobac_public_router",
]
