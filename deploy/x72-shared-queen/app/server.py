from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import math
import os
import random
import sqlite3
import time
from collections import deque
from contextlib import closing
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from .relation_runtime import RelationRuntime
from .noyau_runtime import NoyauConfig, NoyauEngine, NoyauServerAdapter
from .z3_runtime import Z3RuntimeBridge


BASE36_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
CANON_SCHEMA = "ANTMUX-X72-CANON-v1"
PROTECTED_SCHEMA = "ANTMUX-X72-PROTECTED-STATE-v1"
ALLOWED_FAULTS = {"S1", "S2", "S3", "S4", "S5", "S6", "S7", "RANDOM"}
RELATION_TOPOLOGY_VERSION = "K7-COMPLETE-v1"
COMPLETE_RELATIONS_K7: tuple[tuple[int, int], ...] = tuple(
    (left, right)
    for left in range(7)
    for right in range(left + 1, 7)
)
RELATION_COUNT_K7 = len(COMPLETE_RELATIONS_K7)


def relations_are_complete_k7(relations: Any) -> bool:
    if not isinstance(relations, list) or len(relations) != RELATION_COUNT_K7:
        return False
    normalized: set[tuple[int, int]] = set()
    for edge in relations:
        if not isinstance(edge, (list, tuple)) or len(edge) != 2:
            return False
        left, right = edge
        if type(left) is not int or type(right) is not int:
            return False
        if left == right or not (0 <= left < 7 and 0 <= right < 7):
            return False
        normalized.add(tuple(sorted((left, right))))
    return normalized == set(COMPLETE_RELATIONS_K7)


def canonical_bytes(obj: dict[str, Any]) -> bytes:
    return json.dumps(
        {"canon_schema": CANON_SCHEMA, "payload": obj},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256_hex(obj: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(obj)).hexdigest()


def base36_50_from_hex(hex_digest: str) -> str:
    n = int(hex_digest, 16)
    if n == 0:
        raw = "0"
    else:
        chars: list[str] = []
        while n:
            n, r = divmod(n, 36)
            chars.append(BASE36_ALPHABET[r])
        raw = "".join(reversed(chars))
    return raw.rjust(50, "0")


@dataclass
class SynapseState:
    synapse_id: str
    role: str
    integrity: int = 1000
    enabled: bool = True
    generation: int = 0
    activity: float = 0.0
    memory: float = 0.0
    crystal: float = 0.0
    repair_progress: float = 0.0


@dataclass
class RepairReport:
    verdict: str = "INVALID"
    reason: str = "Aucune reparation executee."
    changed_synapses: list[str] = field(default_factory=list)
    before_protected_h256: str = ""
    after_protected_h256: str = ""
    reference_protected_h256: str = ""
    whole_state_h256: str = ""


class EventBus:
    def __init__(self, entity_id: str):
        self.entity_id = entity_id
        self.next_id = 1
        self.events: list[dict[str, Any]] = []

    def emit(self, tick: int, event_type: str, **payload: Any) -> None:
        self.events.append(
            {
                "event_id": self.next_id,
                "tick": tick,
                "event_type": event_type,
                "entity_id": self.entity_id,
                "payload": payload,
            }
        )
        self.next_id += 1
        self.events = self.events[-512:]

    def labels(self, n: int = 10) -> list[str]:
        labels = []
        for event in self.events[-n:]:
            payload = event.get("payload") or {}
            suffix = ""
            if payload:
                first_key = sorted(payload.keys())[0]
                suffix = f":{payload[first_key]}"
            labels.append(f"{event['event_type']}{suffix}")
        return labels


class QueenCore:
    def __init__(self, seed: int = 72):
        self.seed = seed
        self.entity_id = f"QUEEN-X72-{seed:04d}"
        self.queen_epoch = 0
        self.generation = 0
        self.mode = "SLEEP"
        self.tick = 0
        self.sim_time = 0.0
        self.dt_sim = 1 / 240
        self.started_at = time.monotonic()
        self.runtime_start_tick = self.tick
        self.repair_active = False
        self.relations = [list(edge) for edge in COMPLETE_RELATIONS_K7]
        roles = ["INPUT", "MEMORY", "RELATION", "CHOICE", "TEMPORAL", "REPAIR", "AUDIT"]
        self.synapses = [
            SynapseState(
                synapse_id=f"S{i + 1}",
                role=role,
                activity=0.0,
                memory=0.0,
                crystal=0.0,
            )
            for i, role in enumerate(roles)
        ]
        self.bus = EventBus(self.entity_id)
        self.bus.emit(self.tick, "SEED_LOADED", seed=self.seed)
        self.bus.emit(self.tick, "QUEEN_BORN", entity_id=self.entity_id)
        self.protected_reference = self.protected_projection()
        self.last_repair_report = RepairReport(reference_protected_h256=self.reference_h256())
        self.z3_runtime = Z3RuntimeBridge()
        self.relation_runtime = RelationRuntime()
        self.noyau_runtime = NoyauServerAdapter(
            engine=NoyauEngine(NoyauConfig(dt=self.dt_sim))
        )

    def protected_projection(self) -> dict[str, Any]:
        return {
            "schema": PROTECTED_SCHEMA,
            "entity_id": self.entity_id,
            "queen_epoch": self.queen_epoch,
            "relation_topology": RELATION_TOPOLOGY_VERSION,
            "relations": self.relations,
            "synapses": [
                {
                    "synapse_id": s.synapse_id,
                    "role": s.role,
                    "integrity": s.integrity,
                    "enabled": s.enabled,
                    "generation": s.generation,
                }
                for s in self.synapses
            ],
        }

    def whole_projection(self) -> dict[str, Any]:
        return {
            "seed": self.seed,
            "entity_id": self.entity_id,
            "queen_epoch": self.queen_epoch,
            "generation": self.generation,
            "mode": self.mode,
            "tick": self.tick,
            "sim_time": round(self.sim_time, 6),
            "dt_sim": self.dt_sim,
            "relation_topology": RELATION_TOPOLOGY_VERSION,
            "relations": self.relations,
            "synapses": [asdict(s) for s in self.synapses],
            "events_tail": self.bus.events[-32:],
            "z3_runtime": self.z3_runtime.whole_projection(),
        }

    def protected_h256(self) -> str:
        return sha256_hex(self.protected_projection())

    def reference_h256(self) -> str:
        return sha256_hex(self.protected_reference)

    def whole_h256(self) -> str:
        return sha256_hex(self.whole_projection())

    def integrity_match(self) -> bool:
        return self.protected_h256() == self.reference_h256()

    def _mode_for_tick(self) -> str:
        if not self.integrity_match():
            return "AUTO_REPAIR" if self.repair_active else "FAULT"
        phase = self.tick % 1800
        if phase < 260:
            return "SLEEP"
        if phase < 420:
            return "EVENT"
        if phase < 760:
            return "BURST"
        return "STABLE"

    def step(self) -> None:
        self.tick += 1
        self.sim_time += self.dt_sim
        self.mode = self._mode_for_tick()

        mode_gain = {
            "SLEEP": 0.16,
            "EVENT": 0.56,
            "BURST": 0.88,
            "STABLE": 0.38,
            "FAULT": 0.22,
            "AUTO_REPAIR": 0.70,
        }[self.mode]

        for index, synapse in enumerate(self.synapses):
            phase = self.sim_time * (1.5 + index * 0.11) + index * 0.9
            oscillation = 0.5 + 0.5 * math.sin(phase)
            target = mode_gain * (0.55 + 0.45 * oscillation)
            if not synapse.enabled or synapse.integrity <= 0:
                target = 0.0
            synapse.activity += (target - synapse.activity) * 0.055
            synapse.activity = max(0.0, min(1.0, synapse.activity))

            if synapse.enabled and synapse.activity > 0.48:
                synapse.memory += 0.00020 * synapse.activity
            synapse.memory -= 0.000015 * max(0.0, synapse.memory - 0.08)
            synapse.memory = max(0.0, min(0.92, synapse.memory))

            if synapse.memory > 0.18:
                synapse.crystal += 0.000075 * synapse.memory
            synapse.crystal -= 0.000005 * max(0.0, synapse.crystal - 0.05)
            synapse.crystal = max(0.0, min(0.90, synapse.crystal))

        if self.tick % 360 == 0:
            self.bus.emit(self.tick, "MODE", mode=self.mode)

        if self.tick % 7200 == 0:
            self.generation += 1
            self.bus.emit(self.tick, "GENERATION_ADVANCED", generation=self.generation)

        z3_updated = self.z3_runtime.observe(
            tick=self.tick,
            generation=self.generation,
            synapses=self.synapses,
        )
        self.relation_runtime.observe(
            tick=self.tick,
            generation=self.generation,
            synapses=self.synapses,
            relations=self.relations,
        )
        if z3_updated and self.tick % 240 == 0:
            latest = self.z3_runtime.latest
            if latest is not None:
                self.bus.emit(
                    self.tick,
                    "Z3_RUNTIME_FRAME",
                    center_h256=latest.center_provenance_h256,
                    verified=latest.fast_verified,
                )

        self.noyau_runtime.tick()

    def inject_fault(self, synapse_id: str) -> str:
        if synapse_id == "RANDOM":
            synapse_id = random.Random(self.tick + self.seed).choice([f"S{i}" for i in range(1, 8)])
        target = next((s for s in self.synapses if s.synapse_id == synapse_id), None)
        if target is None:
            raise ValueError("invalid synapse")
        target.enabled = False
        target.integrity = 0
        self.mode = "FAULT"
        self.bus.emit(self.tick, "FAULT_INJECTED", synapse_id=synapse_id)
        self.last_repair_report = RepairReport(
            verdict="INVALID",
            reason="Panne protegee active.",
            changed_synapses=[synapse_id],
            before_protected_h256=self.protected_h256(),
            after_protected_h256=self.protected_h256(),
            reference_protected_h256=self.reference_h256(),
            whole_state_h256=self.whole_h256(),
        )
        return synapse_id

    async def repair(self) -> RepairReport:
        before = self.protected_h256()
        if before == self.reference_h256():
            self.last_repair_report = RepairReport(
                verdict="INVALID",
                reason="Aucune panne protegee active.",
                before_protected_h256=before,
                after_protected_h256=before,
                reference_protected_h256=self.reference_h256(),
                whole_state_h256=self.whole_h256(),
            )
            self.bus.emit(self.tick, "REPAIR_INVALID", reason="NO_FAULT")
            return self.last_repair_report
        self.repair_active = True
        self.mode = "AUTO_REPAIR"
        self.bus.emit(self.tick, "REPAIR_STARTED", before_h256=before)
        changed: list[str] = []
        reference_by_id = {s["synapse_id"]: s for s in self.protected_reference["synapses"]}
        for progress in (0.2, 0.45, 0.7, 1.0):
            for synapse in self.synapses:
                synapse.repair_progress = progress
            await asyncio.sleep(0.08)
        for synapse in self.synapses:
            ref = reference_by_id[synapse.synapse_id]
            if synapse.integrity != ref["integrity"] or synapse.enabled != ref["enabled"] or synapse.generation != ref["generation"]:
                changed.append(synapse.synapse_id)
            synapse.integrity = int(ref["integrity"])
            synapse.enabled = bool(ref["enabled"])
            synapse.generation = int(ref["generation"])
            synapse.repair_progress = 0.0
        after = self.protected_h256()
        verdict = "PASS" if after == self.reference_h256() else "FAIL"
        self.mode = "STABLE" if verdict == "PASS" else "FAULT"
        self.repair_active = False
        self.last_repair_report = RepairReport(
            verdict=verdict,
            reason="Protected state restored to reference." if verdict == "PASS" else "Protected state still differs from reference.",
            changed_synapses=changed,
            before_protected_h256=before,
            after_protected_h256=after,
            reference_protected_h256=self.reference_h256(),
            whole_state_h256=self.whole_h256(),
        )
        self.bus.emit(self.tick, "REPAIR_COMPLETED", verdict=verdict, after_h256=after)
        return self.last_repair_report

    def visual_state(self) -> dict[str, Any]:
        elapsed = max(0.001, time.monotonic() - self.started_at)
        runtime_ticks = max(0, self.tick - self.runtime_start_tick)
        active = sum(1 for s in self.synapses if s.enabled)
        activity = sum(s.activity for s in self.synapses) / len(self.synapses)
        memory = sum(s.memory for s in self.synapses) / len(self.synapses)
        crystal = sum(s.crystal for s in self.synapses) / len(self.synapses)
        repair = sum(s.repair_progress for s in self.synapses) / len(self.synapses)
        error = 1.0 - active / 7
        whole = self.whole_h256()
        protected = self.protected_h256()
        return {
            "source": "QUEEN_SERVER_V0_2",
            "entity_id": self.entity_id,
            "seed": self.seed,
            "tick_count": self.tick,
            "sim_time": round(self.sim_time, 6),
            "dt_sim": self.dt_sim,
            "r_exec": round(runtime_ticks / elapsed, 3),
            "f_rt": round((runtime_ticks * self.dt_sim) / elapsed, 6),
            "event_count": len(self.bus.events),
            "queen_mode": self.mode,
            "generation": self.generation,
            "active_synapses": active,
            "relation_topology": RELATION_TOPOLOGY_VERSION,
            "relation_count": len(self.relations),
            "relation_possible": RELATION_COUNT_K7,
            "relation_complete": relations_are_complete_k7(self.relations),
            "repair_level": round(repair, 6),
            "crystallization_level": round(crystal, 6),
            "memory_level": round(memory, 6),
            "error_level": round(error, 6),
            "activity_level": round(activity, 6),
            "whole_h256": whole,
            "b36_view": base36_50_from_hex(whole),
            "protected_h256": protected,
            "reference_h256": self.reference_h256(),
            "integrity_match": protected == self.reference_h256(),
            "repair_verdict": self.last_repair_report.verdict,
            "repair_reason": self.last_repair_report.reason,
            "repair_changed_synapses": list(self.last_repair_report.changed_synapses),
            "z3_runtime": self.z3_runtime.visual_state(),
            "relation_runtime": self.relation_runtime.visual_state(
                tick=self.tick,
                generation=self.generation,
                synapses=self.synapses,
                relations=self.relations,
            ),
            "noyau_runtime": self.noyau_runtime.visual_payload(),
            "synapses": [asdict(s) for s in self.synapses],
            "relations": self.relations,
            "recent_events": self.bus.labels(),
        }

    def to_checkpoint(self) -> dict[str, Any]:
        return {
            "schema": "ANTMUX-X72-SERVER-CHECKPOINT-v1",
            "seed": self.seed,
            "entity_id": self.entity_id,
            "queen_epoch": self.queen_epoch,
            "generation": self.generation,
            "mode": self.mode,
            "tick": self.tick,
            "sim_time": self.sim_time,
            "relation_topology": RELATION_TOPOLOGY_VERSION,
            "relations": self.relations,
            "synapses": [asdict(s) for s in self.synapses],
            "protected_reference": self.protected_reference,
            "events": self.bus.events[-512:],
            "next_event_id": self.bus.next_id,
            "last_repair_report": asdict(self.last_repair_report),
            "z3_runtime": self.z3_runtime.to_checkpoint(),
            "relation_runtime": self.relation_runtime.to_checkpoint(),
            "noyau_runtime": self.noyau_runtime.to_checkpoint(),
        }

    @classmethod
    def from_checkpoint(cls, checkpoint: dict[str, Any]) -> "QueenCore":
        if checkpoint.get("relation_topology") != RELATION_TOPOLOGY_VERSION:
            raise ValueError("checkpoint relation topology is not K7-COMPLETE-v1")
        if not relations_are_complete_k7(checkpoint.get("relations")):
            raise ValueError("checkpoint relation graph is incomplete or malformed")
        queen = cls(int(checkpoint["seed"]))
        queen.entity_id = checkpoint["entity_id"]
        queen.queen_epoch = int(checkpoint["queen_epoch"])
        queen.generation = int(checkpoint["generation"])
        queen.mode = checkpoint["mode"]
        queen.tick = int(checkpoint["tick"])
        queen.sim_time = float(checkpoint["sim_time"])
        queen.started_at = time.monotonic()
        queen.runtime_start_tick = queen.tick
        queen.relations = checkpoint["relations"]
        queen.synapses = [SynapseState(**item) for item in checkpoint["synapses"]]
        queen.protected_reference = checkpoint["protected_reference"]
        queen.bus = EventBus(queen.entity_id)
        queen.bus.events = checkpoint.get("events", [])[-512:]
        queen.bus.next_id = int(checkpoint.get("next_event_id", len(queen.bus.events) + 1))
        queen.last_repair_report = RepairReport(**checkpoint.get("last_repair_report", {}))
        queen.z3_runtime = Z3RuntimeBridge.from_checkpoint(
            checkpoint.get("z3_runtime"),
            tick=queen.tick,
            generation=queen.generation,
        )
        queen.relation_runtime = RelationRuntime.from_checkpoint(
            checkpoint.get("relation_runtime")
        )
        noyau_checkpoint = checkpoint.get("noyau_runtime")
        if noyau_checkpoint is None:
            queen.noyau_runtime = NoyauServerAdapter(
                engine=NoyauEngine(NoyauConfig(dt=queen.dt_sim))
            )
        else:
            queen.noyau_runtime = NoyauServerAdapter.from_checkpoint(noyau_checkpoint)
            if abs(queen.noyau_runtime.engine.config.dt - queen.dt_sim) > 1e-12:
                raise ValueError("checkpoint noyau cadence differs from Queen dt_sim")
        return queen


class Persistence:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.db_path)) as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS checkpoints ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "created_at REAL NOT NULL,"
                "state_json TEXT NOT NULL,"
                "protected_h256 TEXT NOT NULL,"
                "whole_h256 TEXT NOT NULL)"
            )
            db.commit()

    def save(self, queen: QueenCore) -> None:
        state_json = json.dumps(queen.to_checkpoint(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        with closing(sqlite3.connect(self.db_path)) as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                "INSERT INTO checkpoints(created_at, state_json, protected_h256, whole_h256) VALUES (?, ?, ?, ?)",
                (time.time(), state_json, queen.protected_h256(), queen.whole_h256()),
            )
            db.commit()

    def load_latest(self) -> QueenCore | None:
        with closing(sqlite3.connect(self.db_path)) as db:
            rows = db.execute(
                "SELECT state_json, protected_h256, whole_h256 "
                "FROM checkpoints ORDER BY id DESC LIMIT 20"
            ).fetchall()
        for state_json, stored_protected_h256, stored_whole_h256 in rows:
            try:
                checkpoint = json.loads(state_json)
                if checkpoint.get("schema") != "ANTMUX-X72-SERVER-CHECKPOINT-v1":
                    continue
                queen = QueenCore.from_checkpoint(checkpoint)
                if queen.protected_h256() != stored_protected_h256:
                    continue
                if queen.whole_h256() != stored_whole_h256:
                    continue
                return queen
            except Exception:
                continue
        return None


class FaultRequest(BaseModel):
    synapse_id: str = "RANDOM"


DATA_DIR = Path(os.environ.get("ANTMUX_X72_DATA_DIR", "/home/rob/antmux-x72-queen/data"))
ZEL_INGEST_TOKEN = os.environ.get("ANTMUX_ZEL_INGEST_TOKEN", "").strip()
ZEL_MAX_BODY_BYTES = 65536
zel_state: dict[str, Any] | None = None
zel_state_version = 0
zel_state_condition = asyncio.Condition()
zel_state_history: deque[tuple[int, dict[str, Any]]] = deque(maxlen=256)


def normalize_zel_public_state(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise HTTPException(status_code=400, detail="invalid payload")
    if raw.get("mode") != "PUBLIC_SAFE" or raw.get("read_only") is not True:
        raise HTTPException(status_code=400, detail="PUBLIC_SAFE read-only payload required")
    stage_index = raw.get("stage_index")
    if type(stage_index) is not int or not 0 <= stage_index <= 6:
        raise HTTPException(status_code=400, detail="invalid stage_index")
    channels = raw.get("channels")
    trace_points = raw.get("trace_points")
    trace_total = raw.get("trace_total")
    public_values_total = raw.get("public_values_total", 0)
    for name, value, lo, hi in (
        ("channels", channels, 0, 36),
        ("trace_points", trace_points, 0, 10000),
        ("trace_total", trace_total, 1, 10000),
        ("public_values_total", public_values_total, 0, 10000),
    ):
        if type(value) is not int or not lo <= value <= hi:
            raise HTTPException(status_code=400, detail=f"invalid {name}")
    stage = str(raw.get("stage", ""))[:64]
    if not stage:
        raise HTTPException(status_code=400, detail="invalid stage")
    stage_exec_us = raw.get("stage_exec_us", 0.0)
    stage_work_ratio = raw.get("stage_work_ratio", 0.0)
    for name, value, lo, hi in (
        ("stage_exec_us", stage_exec_us, 0.0, 1000000.0),
        ("stage_work_ratio", stage_work_ratio, 0.0, 1.0),
    ):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or not lo <= float(value) <= hi:
            raise HTTPException(status_code=400, detail=f"invalid {name}")
    ge = raw.get("global_error") if isinstance(raw.get("global_error"), dict) else {}
    f1 = raw.get("f1") if isinstance(raw.get("f1"), dict) else {}
    vals = raw.get("public_values") if isinstance(raw.get("public_values"), list) else []
    safe_vals: list[dict[str, Any]] = []
    for v in vals[:36]:
        if isinstance(v, dict):
            safe_vals.append({"exact": str(v.get("exact", ""))[:128], "decimal": v.get("decimal", 0)})
    return {
        "mode": "PUBLIC_SAFE",
        "read_only": True,
        "status": "LIVE",
        "stage_index": stage_index,
        "stage": stage,
        "channels": channels,
        "trace_points": trace_points,
        "trace_total": trace_total,
        "stage_exec_us": round(float(stage_exec_us), 3),
        "stage_work_ratio": round(float(stage_work_ratio), 6),
        "public_values": safe_vals,
        "public_values_total": public_values_total,
        "global_error": {"exact": str(ge.get("exact", ""))[:128], "decimal": ge.get("decimal", 0)},
        "f1": {
            "formula_id": str(f1.get("formula_id", ""))[:32],
            "k": f1.get("k", 0),
            "value": str(f1.get("value", ""))[:128],
            "formula": str(f1.get("formula", ""))[:256],
            "source_commit_short": str(f1.get("source_commit_short", ""))[:16],
        },
        "events": [],
        "event_seq": raw.get("event_seq", 0) if type(raw.get("event_seq", 0)) is int else 0,
        "timestamp": time.time(),
    }

DB_PATH = DATA_DIR / "queen.db"
REPORT_PATH = DATA_DIR / "ANTMUX_X72_SERVER_SHARED_QUEEN_TEST_REPORT.json"

app = FastAPI(title="ANTMUX X72 Shared Queen Server", version="0.2")
persistence = Persistence(DB_PATH)
queen = persistence.load_latest() or QueenCore(seed=72)
state_lock = asyncio.Lock()
last_mutation_by_ip: dict[str, float] = {}
tick_task: asyncio.Task[None] | None = None
checkpoint_task: asyncio.Task[None] | None = None
server_started_monotonic = time.monotonic()
active_websocket_clients = 0
websocket_messages_sent = 0


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def enforce_rate_limit(ip: str) -> None:
    now = time.monotonic()
    last = last_mutation_by_ip.get(ip, 0)
    if now - last < 3:
        raise HTTPException(status_code=429, detail="rate limit: one public mutation per IP per 3 seconds")
    last_mutation_by_ip[ip] = now


def observability_snapshot() -> dict[str, Any]:
    state = queen.visual_state()
    return {
        "schema": "ANTMUX-X72-OBSERVABILITY-v1",
        "scope": "operational_read_only",
        "authority": "QUEEN_SERVER_V0_2",
        "entity_id": state["entity_id"],
        "uptime_seconds": round(max(0.0, time.monotonic() - server_started_monotonic), 3),
        "tick_count": state["tick_count"],
        "queen_mode": state["queen_mode"],
        "generation": state["generation"],
        "active_synapses": state["active_synapses"],
        "integrity_match": state["integrity_match"],
        "repair_active": queen.repair_active,
        "event_count": state["event_count"],
        "websocket_clients": active_websocket_clients,
        "websocket_messages_sent": websocket_messages_sent,
        "cadence_seconds": {"tick": 1.0 / 240.0, "scheduler": 0.005, "checkpoint": 2.0, "websocket": 0.25},
    }


async def tick_loop() -> None:
    target_hz = 240.0
    scheduler_sleep = 0.005
    max_catchup_steps = 96
    started = time.monotonic()
    base_tick = queen.tick

    while True:
        elapsed = max(0.0, time.monotonic() - started)
        target_tick = base_tick + int(elapsed * target_hz)

        async with state_lock:
            due_steps = max(0, target_tick - queen.tick)
            for _ in range(min(due_steps, max_catchup_steps)):
                queen.step()

        await asyncio.sleep(scheduler_sleep)


async def checkpoint_loop() -> None:
    while True:
        await asyncio.sleep(2.0)
        async with state_lock:
            persistence.save(queen)


@app.on_event("startup")
async def on_startup() -> None:
    global tick_task, checkpoint_task
    tick_task = asyncio.create_task(tick_loop())
    checkpoint_task = asyncio.create_task(checkpoint_loop())


@app.on_event("shutdown")
async def on_shutdown() -> None:
    for task in (tick_task, checkpoint_task):
        if task:
            task.cancel()
    async with state_lock:
        persistence.save(queen)


@app.get("/api/health")
async def health() -> dict[str, Any]:
    async with state_lock:
        return {
            "ok": True,
            "source": "QUEEN_SERVER_V0_2",
            "entity_id": queen.entity_id,
            "tick_count": queen.tick,
            "db_path": str(DB_PATH),
            "integrity_match": queen.integrity_match(),
        }


@app.get("/api/state")
async def state() -> dict[str, Any]:
    async with state_lock:
        return queen.visual_state()


@app.get("/api/telemetry")
async def telemetry() -> dict[str, Any]:
    async with state_lock:
        return observability_snapshot()


@app.get("/api/events")
async def events() -> dict[str, Any]:
    async with state_lock:
        return {"events": queen.bus.events[-64:], "event_count": len(queen.bus.events)}


@app.get("/api/report")
async def report() -> dict[str, Any]:
    async with state_lock:
        return asdict(queen.last_repair_report)


@app.post("/api/fault")
async def fault(body: FaultRequest, request: Request) -> dict[str, Any]:
    synapse_id = body.synapse_id.upper().strip()
    if synapse_id not in ALLOWED_FAULTS:
        raise HTTPException(status_code=422, detail="fault must be S1..S7 or RANDOM")
    enforce_rate_limit(client_ip(request))
    async with state_lock:
        if not queen.integrity_match():
            raise HTTPException(status_code=409, detail="protected fault already active")
        actual = queen.inject_fault(synapse_id)
        persistence.save(queen)
        return {"ok": True, "fault": actual, "state": queen.visual_state()}


@app.post("/api/repair")
async def repair(request: Request) -> dict[str, Any]:
    enforce_rate_limit(client_ip(request))
    async with state_lock:
        if queen.repair_active:
            raise HTTPException(status_code=409, detail="repair already active")
        before = queen.protected_h256()
        if before == queen.reference_h256():
            report_obj = RepairReport(
                verdict="INVALID",
                reason="Aucune panne protegee active.",
                before_protected_h256=before,
                after_protected_h256=before,
                reference_protected_h256=queen.reference_h256(),
                whole_state_h256=queen.whole_h256(),
            )
            queen.last_repair_report = report_obj
            queen.bus.emit(queen.tick, "REPAIR_INVALID", reason="NO_FAULT")
            persistence.save(queen)
            return {"ok": False, "report": asdict(report_obj), "state": queen.visual_state()}
        queen.repair_active = True
        queen.mode = "AUTO_REPAIR"
        queen.bus.emit(queen.tick, "REPAIR_STARTED", before_h256=before)

    for progress in (0.2, 0.45, 0.7, 1.0):
        async with state_lock:
            for synapse in queen.synapses:
                synapse.repair_progress = progress
        await asyncio.sleep(0.08)

    async with state_lock:
        reference_by_id = {s["synapse_id"]: s for s in queen.protected_reference["synapses"]}
        changed: list[str] = []
        for synapse in queen.synapses:
            ref = reference_by_id[synapse.synapse_id]
            if synapse.integrity != ref["integrity"] or synapse.enabled != ref["enabled"] or synapse.generation != ref["generation"]:
                changed.append(synapse.synapse_id)
            synapse.integrity = int(ref["integrity"])
            synapse.enabled = bool(ref["enabled"])
            synapse.generation = int(ref["generation"])
            synapse.repair_progress = 0.0
        after = queen.protected_h256()
        verdict = "PASS" if after == queen.reference_h256() else "FAIL"
        queen.mode = "STABLE" if verdict == "PASS" else "FAULT"
        queen.repair_active = False
        report_obj = RepairReport(
            verdict=verdict,
            reason="Protected state restored to reference." if verdict == "PASS" else "Protected state still differs from reference.",
            changed_synapses=changed,
            before_protected_h256=before,
            after_protected_h256=after,
            reference_protected_h256=queen.reference_h256(),
            whole_state_h256=queen.whole_h256(),
        )
        queen.last_repair_report = report_obj
        queen.bus.emit(queen.tick, "REPAIR_COMPLETED", verdict=verdict, after_h256=after)
        persistence.save(queen)
        return {"ok": report_obj.verdict == "PASS", "report": asdict(report_obj), "state": queen.visual_state()}


@app.post("/api/zelstereos/ingest")
async def ingest_zelstereos(request: Request) -> dict[str, Any]:
    global zel_state, zel_state_version
    if not ZEL_INGEST_TOKEN:
        raise HTTPException(status_code=503, detail="ZEL ingest disabled")
    supplied = request.headers.get("authorization", "")
    expected = f"Bearer {ZEL_INGEST_TOKEN}"
    if not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="unauthorized")
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > ZEL_MAX_BODY_BYTES:
        raise HTTPException(status_code=413, detail="payload too large")
    body = await request.body()
    if len(body) > ZEL_MAX_BODY_BYTES:
        raise HTTPException(status_code=413, detail="payload too large")
    try:
        raw = json.loads(body)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="invalid json") from exc
    normalized = normalize_zel_public_state(raw)
    async with zel_state_condition:
        zel_state = normalized
        zel_state_version += 1
        version = zel_state_version
        zel_state_history.append((version, dict(normalized)))
        zel_state_condition.notify_all()
    return {"ok": True, "version": version}


async def stream_zelstereos(websocket: WebSocket) -> None:
    await websocket.accept()
    async with zel_state_condition:
        initial_replay_version = zel_state_version if zel_state is not None else None
        last_version = max(0, zel_state_version - 1) if zel_state is not None else 0
    try:
        while True:
            async with zel_state_condition:
                await zel_state_condition.wait_for(lambda: zel_state_version > last_version)
                pending = [
                    (version, dict(payload))
                    for version, payload in zel_state_history
                    if version > last_version
                ]
                if not pending and zel_state is not None and zel_state_version > last_version:
                    pending = [(zel_state_version, dict(zel_state))]
            for version, payload in pending:
                stream_payload = dict(payload)
                stream_payload["transport_event_version"] = version
                stream_payload["transport_replay"] = bool(
                    initial_replay_version is not None and version == initial_replay_version
                )
                await websocket.send_json(stream_payload)
                if initial_replay_version == version:
                    initial_replay_version = None
                last_version = version
    except WebSocketDisconnect:
        return


@app.websocket("/ws/zelstereos")
async def websocket_zelstereos(websocket: WebSocket) -> None:
    await stream_zelstereos(websocket)


@app.websocket("/ws")
async def websocket_state(websocket: WebSocket) -> None:
    global active_websocket_clients, websocket_messages_sent

    if websocket.query_params.get("channel") == "zelstereos":
        await stream_zelstereos(websocket)
        return

    await websocket.accept()
    active_websocket_clients += 1
    try:
        while True:
            async with state_lock:
                payload = queen.visual_state()
            await websocket.send_json(payload)
            websocket_messages_sent += 1
            await asyncio.sleep(0.25)
    except WebSocketDisconnect:
        return
    finally:
        active_websocket_clients = max(0, active_websocket_clients - 1)
