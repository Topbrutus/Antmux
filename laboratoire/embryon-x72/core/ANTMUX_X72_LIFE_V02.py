"""
ANTMUX-X72 / MYRMIX-X72-D13-G7
HORLOGE DE LA VIE — CORE V0.2

But
---
Remplacer la réparation de démonstration de V0.1 par un chemin de réparation
réellement vérifiable :

    QueenCore -> EventBus -> RepairEngine -> Telemetry -> VisualState -> Visual

Règles verrouillées
-------------------
- Le visuel n'invente jamais l'état du CORE.
- SHA-256 est une empreinte, pas un mécanisme d'inversion.
- Base36_50 est une représentation réversible du digest complet.
- La réparation restaure uniquement des champs autorisés depuis une référence
  déterministe et doit fermer sur le hash protégé de référence.
- PASS / FAIL / INVALID sont des verdicts explicites.

Cette version reste un noyau expérimental minimal. Elle ne prétend pas démontrer
une intelligence générale, une auto-guérison universelle, ni une loi physique.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import random
import time
import tkinter as tk
from dataclasses import asdict, dataclass, field
from pathlib import Path
from tkinter import filedialog
from typing import Dict, List, Optional, Tuple


# =============================================================================
# 0 — THÈME PROVISOIRE (remplaçable sans toucher au CORE)
# =============================================================================
THEME = {
    "bg": "#05070C",
    "panel": "#0A0F18",
    "panel2": "#0D1420",
    "grid": "#172333",
    "text": "#F2F5F8",
    "muted": "#8795A8",
    "gold": "#F6B94A",
    "gold2": "#FFDF8A",
    "cyan": "#39D8FF",
    "blue": "#4B7CFF",
    "magenta": "#E65BFF",
    "violet": "#8B5CFF",
    "green": "#5CFFB1",
    "warning": "#FFB84C",
    "error": "#FF557A",
    "white": "#FFFFFF",
}

BASE36_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
CANON_SCHEMA = "ANTMUX-X72-CANON-v1"
CORE_SCHEMA = "ANTMUX-X72-QUEEN-CORE-v0.2"
PROTECTED_SCHEMA = "ANTMUX-X72-PROTECTED-STATE-v1"


# =============================================================================
# 1 — CANON / H256 / BASE36_50
# =============================================================================
def canonical_bytes(obj: dict) -> bytes:
    """Sérialisation canonique minimale et versionnée pour V0.2.

    Le CORE évite NaN/Infinity et passe par des valeurs déjà quantifiées dans
    ses projections protégées. Même objet logique -> mêmes octets.
    """
    envelope = {"canon_schema": CANON_SCHEMA, "payload": obj}
    return json.dumps(
        envelope,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256_digest(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def base36_50(digest: bytes) -> str:
    if len(digest) != 32:
        raise ValueError("H256 doit contenir exactement 32 octets.")
    n = int.from_bytes(digest, "big", signed=False)
    if n == 0:
        raw = "0"
    else:
        chars = []
        while n:
            n, r = divmod(n, 36)
            chars.append(BASE36_ALPHABET[r])
        raw = "".join(reversed(chars))
    if len(raw) > 50:
        raise ValueError("Digest 256 bits impossible à représenter en Base36_50.")
    return raw.rjust(50, "0")


def base36_50_inverse(text: str) -> bytes:
    text = text.strip().upper()
    if len(text) != 50:
        raise ValueError("B36 canonique doit contenir exactement 50 caractères.")
    n = 0
    for ch in text:
        if ch not in BASE36_ALPHABET:
            raise ValueError(f"Caractère Base36 invalide: {ch}")
        n = n * 36 + BASE36_ALPHABET.index(ch)
    if n >= (1 << 256):
        raise ValueError("Valeur Base36 hors domaine 256 bits.")
    return n.to_bytes(32, "big", signed=False)


# =============================================================================
# 2 — MODÈLES D'ÉTAT
# =============================================================================
@dataclass
class SynapseState:
    synapse_id: str
    role: str
    integrity: int = 1000          # 0..1000, champ protégé
    enabled: bool = True           # champ protégé
    generation: int = 0            # champ protégé
    activity: float = 0.0          # dynamique
    memory: float = 0.0            # dynamique expérimentale
    crystal: float = 0.0           # dynamique expérimentale
    repair_progress: float = 0.0   # dynamique réparation


@dataclass
class CoreEvent:
    event_id: int
    tick: int
    event_type: str
    entity_id: str
    payload: dict


@dataclass
class RepairReport:
    verdict: str                   # PASS | FAIL | INVALID
    reason: str
    changed_synapses: List[str]
    before_protected_h256: str
    after_protected_h256: str
    reference_protected_h256: str
    whole_state_h256: str


@dataclass
class VisualState:
    source: str
    tick_count: int
    sim_time: float
    dt_sim: float
    r_exec: float
    f_rt: float
    event_count: int
    queen_mode: str
    generation: int
    active_synapses: int
    repair_level: float
    crystallization_level: float
    memory_level: float
    error_level: float
    activity_level: float
    whole_h256: str
    b36_view: str
    protected_h256: str
    reference_h256: str
    integrity_match: bool
    repair_verdict: str
    repair_reason: str
    synapses: List[SynapseState]
    relations: List[Tuple[int, int]]
    recent_events: List[str] = field(default_factory=list)


# =============================================================================
# 3 — EVENT BUS
# =============================================================================
class EventBus:
    def __init__(self, entity_id: str):
        self.entity_id = entity_id
        self._next_id = 1
        self._events: List[CoreEvent] = []

    def emit(self, tick: int, event_type: str, **payload) -> CoreEvent:
        evt = CoreEvent(
            event_id=self._next_id,
            tick=tick,
            event_type=event_type,
            entity_id=self.entity_id,
            payload=payload,
        )
        self._next_id += 1
        self._events.append(evt)
        self._events = self._events[-512:]
        return evt

    @property
    def count(self) -> int:
        return len(self._events)

    def recent_labels(self, n: int = 10) -> List[str]:
        out = []
        for e in self._events[-n:]:
            suffix = ""
            if e.payload:
                key = next(iter(e.payload))
                suffix = f":{e.payload[key]}"
            out.append(f"{e.event_type}{suffix}")
        return out

    def serializable(self) -> List[dict]:
        return [asdict(e) for e in self._events]


# =============================================================================
# 4 — QUEEN CORE EXPÉRIMENTAL
# =============================================================================
class QueenCore:
    """Noyau minimal déterministe avec état protégé + dynamique observable."""

    def __init__(self, seed: int = 72):
        self.seed = int(seed)
        self.entity_id = f"QUEEN-X72-{self.seed:04d}"
        self.queen_epoch = 0
        self.generation = 0
        self.mode = "SLEEP"
        self.tick = 0
        self.sim_time = 0.0
        self.dt_sim = 1.0 / 240.0
        self.rng = random.Random(self.seed)

        self.relations: List[Tuple[int, int]] = [
            (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 0),
            (0, 3), (2, 5), (1, 4),
        ]
        roles = [
            "INPUT", "MEMORY", "RELATION", "CHOICE", "TEMPORAL", "REPAIR", "AUDIT"
        ]
        self.synapses: List[SynapseState] = []
        for i in range(7):
            self.synapses.append(
                SynapseState(
                    synapse_id=f"S{i+1}",
                    role=roles[i],
                    integrity=1000,
                    enabled=True,
                    generation=0,
                    activity=0.08 + 0.03 * i,
                    memory=0.07 + 0.02 * i,
                    crystal=0.04 + 0.015 * i,
                )
            )

        self.bus = EventBus(self.entity_id)
        self.bus.emit(self.tick, "SEED_LOADED", seed=self.seed)
        self.bus.emit(self.tick, "QUEEN_BORN", entity_id=self.entity_id)

        # Référence autorisée : projection structurelle protégée à la naissance.
        self._protected_reference = copy.deepcopy(self.protected_projection())
        self.reference_protected_h256 = self.hash_protected(self._protected_reference)

        self.last_repair_report = RepairReport(
            verdict="INVALID",
            reason="Aucune réparation exécutée.",
            changed_synapses=[],
            before_protected_h256=self.reference_protected_h256,
            after_protected_h256=self.reference_protected_h256,
            reference_protected_h256=self.reference_protected_h256,
            whole_state_h256=self.whole_state_h256(),
        )

    # ---------------------------------------------------------------------
    # PROJECTIONS / HASHES
    # ---------------------------------------------------------------------
    def protected_projection(self) -> dict:
        """État explicitement couvert par la réparation V0.2.

        Les métriques dynamiques (activité, mémoire, cristal, tick) sont exclues
        du hash protégé : une réparation doit restaurer l'intégrité structurelle,
        pas remonter le temps.
        """
        return {
            "schema": PROTECTED_SCHEMA,
            "entity_id": self.entity_id,
            "queen_epoch": self.queen_epoch,
            "relations": [list(x) for x in self.relations],
            "synapses": [
                {
                    "synapse_id": s.synapse_id,
                    "role": s.role,
                    "integrity": int(s.integrity),
                    "enabled": bool(s.enabled),
                    "generation": int(s.generation),
                }
                for s in self.synapses
            ],
        }

    @staticmethod
    def hash_protected(projection: dict) -> str:
        return sha256_hex(canonical_bytes(projection))

    def current_protected_h256(self) -> str:
        return self.hash_protected(self.protected_projection())

    def integrity_matches_reference(self) -> bool:
        return self.current_protected_h256() == self.reference_protected_h256

    def whole_state_projection(self) -> dict:
        return {
            "schema": CORE_SCHEMA,
            "seed": self.seed,
            "entity_id": self.entity_id,
            "queen_epoch": self.queen_epoch,
            "generation": self.generation,
            "mode": self.mode,
            "tick": self.tick,
            "sim_time_us": int(round(self.sim_time * 1_000_000)),
            "relations": [list(x) for x in self.relations],
            "synapses": [
                {
                    "synapse_id": s.synapse_id,
                    "role": s.role,
                    "integrity": s.integrity,
                    "enabled": s.enabled,
                    "generation": s.generation,
                    "activity_u": int(round(s.activity * 1_000_000)),
                    "memory_u": int(round(s.memory * 1_000_000)),
                    "crystal_u": int(round(s.crystal * 1_000_000)),
                    "repair_u": int(round(s.repair_progress * 1_000_000)),
                }
                for s in self.synapses
            ],
        }

    def whole_state_digest(self) -> bytes:
        return sha256_digest(canonical_bytes(self.whole_state_projection()))

    def whole_state_h256(self) -> str:
        return self.whole_state_digest().hex()

    def whole_state_b36(self) -> str:
        digest = self.whole_state_digest()
        encoded = base36_50(digest)
        if base36_50_inverse(encoded) != digest:
            raise RuntimeError("Round-trip H256 <-> Base36_50 invalide.")
        return encoded

    # ---------------------------------------------------------------------
    # DYNAMIQUE OBSERVABLE
    # ---------------------------------------------------------------------
    def _mode_for_tick(self) -> str:
        if not self.integrity_matches_reference():
            return "AUTO_REPAIR" if any(s.repair_progress > 0 for s in self.synapses) else "FAULT"
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

        for i, s in enumerate(self.synapses):
            phase = self.sim_time * (1.5 + i * 0.11) + i * 0.9
            oscillation = 0.5 + 0.5 * math.sin(phase)
            target = mode_gain * (0.55 + 0.45 * oscillation)
            if not s.enabled or s.integrity <= 0:
                target = 0.0
            s.activity += (target - s.activity) * 0.055
            s.activity = max(0.0, min(1.0, s.activity))

            # Dynamique expérimentale bornée avec légère décroissance : évite
            # la saturation permanente de V0.1.
            if s.enabled and s.activity > 0.48:
                s.memory += 0.00020 * s.activity
            s.memory -= 0.000015 * max(0.0, s.memory - 0.08)
            s.memory = max(0.0, min(0.92, s.memory))

            if s.memory > 0.18:
                s.crystal += 0.000075 * s.memory
            s.crystal -= 0.000005 * max(0.0, s.crystal - 0.05)
            s.crystal = max(0.0, min(0.90, s.crystal))

        if self.tick % 360 == 0:
            self.bus.emit(self.tick, "MODE", mode=self.mode)
        if self.tick % 7200 == 0:
            self.generation += 1
            # La génération dynamique de la Reine ne modifie pas ici la
            # référence protégée ; ce sera une opération versionnée plus tard.
            self.bus.emit(self.tick, "GENERATION_ADVANCED", generation=self.generation)

    # ---------------------------------------------------------------------
    # PANNE CONTRÔLÉE
    # ---------------------------------------------------------------------
    def inject_fault(self, synapse_id: Optional[str] = None) -> str:
        if not self.integrity_matches_reference():
            raise RuntimeError("Une panne protégée existe déjà ; réparer avant d'en injecter une autre.")

        if synapse_id is None:
            idx = (self.tick // 17 + 3) % len(self.synapses)
        else:
            matches = [i for i, s in enumerate(self.synapses) if s.synapse_id == synapse_id]
            if not matches:
                raise ValueError(f"Synapse inconnue: {synapse_id}")
            idx = matches[0]

        s = self.synapses[idx]
        before = self.current_protected_h256()
        s.enabled = False
        s.integrity = 0
        s.repair_progress = 0.0
        after = self.current_protected_h256()
        self.mode = "FAULT"
        self.bus.emit(
            self.tick,
            "FAULT_DETECTED",
            synapse_id=s.synapse_id,
            before_h256=before,
            fault_h256=after,
        )
        if before == after:
            raise RuntimeError("Injection invalide : le hash protégé n'a pas changé.")
        return s.synapse_id

    def reset_to_reference(self) -> None:
        ref = self._protected_reference
        by_id = {x["synapse_id"]: x for x in ref["synapses"]}
        for s in self.synapses:
            rs = by_id[s.synapse_id]
            s.role = rs["role"]
            s.integrity = rs["integrity"]
            s.enabled = rs["enabled"]
            s.generation = rs["generation"]
            s.repair_progress = 0.0
        self.relations = [tuple(x) for x in ref["relations"]]
        self.queen_epoch = ref["queen_epoch"]
        # La génération courante reste dynamique : ne pas remonter le temps.
        self.mode = "STABLE"
        self.bus.emit(self.tick, "CORE_RESET_TO_REFERENCE")


# =============================================================================
# 5 — REPAIR ENGINE : RESTAURATION + PREUVE PAR HASH PROTÉGÉ
# =============================================================================
class RepairEngine:
    ALLOWED_FIELDS = ("role", "integrity", "enabled", "generation")

    def __init__(self, core: QueenCore):
        self.core = core
        self.active = False
        self.progress = 0.0
        self.targets: List[str] = []
        self.before_h256 = core.current_protected_h256()

    def diagnose(self) -> List[str]:
        ref_by_id = {x["synapse_id"]: x for x in self.core._protected_reference["synapses"]}
        damaged: List[str] = []
        for s in self.core.synapses:
            r = ref_by_id.get(s.synapse_id)
            if r is None:
                damaged.append(s.synapse_id)
                continue
            if any(getattr(s, f) != r[f] for f in self.ALLOWED_FIELDS):
                damaged.append(s.synapse_id)
        return damaged

    def begin(self) -> RepairReport:
        current = self.core.current_protected_h256()
        ref = self.core.reference_protected_h256
        if current == ref:
            report = RepairReport(
                verdict="INVALID",
                reason="Aucune divergence protégée à réparer.",
                changed_synapses=[],
                before_protected_h256=current,
                after_protected_h256=current,
                reference_protected_h256=ref,
                whole_state_h256=self.core.whole_state_h256(),
            )
            self.core.last_repair_report = report
            self.core.bus.emit(self.core.tick, "REPAIR_INVALID", reason=report.reason)
            return report

        self.targets = self.diagnose()
        if not self.targets:
            report = RepairReport(
                verdict="FAIL",
                reason="Hash protégé divergent mais aucune synapse réparable identifiée.",
                changed_synapses=[],
                before_protected_h256=current,
                after_protected_h256=current,
                reference_protected_h256=ref,
                whole_state_h256=self.core.whole_state_h256(),
            )
            self.core.last_repair_report = report
            self.core.bus.emit(self.core.tick, "REPAIR_FAILED", reason=report.reason)
            return report

        self.before_h256 = current
        self.active = True
        self.progress = 0.0
        self.core.mode = "AUTO_REPAIR"
        self.core.bus.emit(self.core.tick, "REPAIR_STARTED", targets=",".join(self.targets))
        for s in self.core.synapses:
            if s.synapse_id in self.targets:
                s.repair_progress = 0.001
        return RepairReport(
            verdict="INVALID",
            reason="Réparation en cours.",
            changed_synapses=list(self.targets),
            before_protected_h256=current,
            after_protected_h256=current,
            reference_protected_h256=ref,
            whole_state_h256=self.core.whole_state_h256(),
        )

    def step(self) -> Optional[RepairReport]:
        if not self.active:
            return None
        self.progress = min(1.0, self.progress + 0.0075)
        for s in self.core.synapses:
            if s.synapse_id in self.targets:
                s.repair_progress = self.progress

        if self.progress < 1.0:
            return None

        # Restauration atomique des champs autorisés depuis la référence.
        ref_by_id = {x["synapse_id"]: x for x in self.core._protected_reference["synapses"]}
        changed = []
        for s in self.core.synapses:
            if s.synapse_id not in self.targets:
                continue
            r = ref_by_id[s.synapse_id]
            for field_name in self.ALLOWED_FIELDS:
                setattr(s, field_name, r[field_name])
            s.repair_progress = 0.0
            changed.append(s.synapse_id)

        after = self.core.current_protected_h256()
        ref = self.core.reference_protected_h256
        verdict = "PASS" if after == ref else "FAIL"
        reason = (
            "Hash protégé restauré exactement sur la référence autorisée."
            if verdict == "PASS"
            else "Le hash protégé ne ferme pas sur la référence après restauration."
        )
        self.active = False
        self.core.mode = "STABLE" if verdict == "PASS" else "FAULT"
        self.core.bus.emit(
            self.core.tick,
            "REPAIR_COMPLETED" if verdict == "PASS" else "REPAIR_FAILED",
            verdict=verdict,
            targets=",".join(changed),
            protected_h256=after,
        )
        self.core.bus.emit(self.core.tick, "STATE_CANONICALIZED")
        self.core.bus.emit(self.core.tick, "STATE_HASHED", whole_h256=self.core.whole_state_h256())

        report = RepairReport(
            verdict=verdict,
            reason=reason,
            changed_synapses=changed,
            before_protected_h256=self.before_h256,
            after_protected_h256=after,
            reference_protected_h256=ref,
            whole_state_h256=self.core.whole_state_h256(),
        )
        self.core.last_repair_report = report
        self.targets = []
        self.progress = 0.0
        return report


# =============================================================================
# 6 — TELEMETRY ADAPTER
# =============================================================================
class CoreTelemetryAdapter:
    def __init__(self, core: QueenCore, repair: RepairEngine):
        self.core = core
        self.repair = repair

    def visual_state(self, r_exec: float, f_rt: float) -> VisualState:
        h = self.core.whole_state_digest()
        b = base36_50(h)
        if base36_50_inverse(b) != h:
            raise RuntimeError("B36_50 n'est pas réversible.")

        activity = sum(s.activity for s in self.core.synapses) / len(self.core.synapses)
        memory = sum(s.memory for s in self.core.synapses) / len(self.core.synapses)
        crystal = sum(s.crystal for s in self.core.synapses) / len(self.core.synapses)
        current_protected = self.core.current_protected_h256()
        match = current_protected == self.core.reference_protected_h256
        error = 0.0 if match else 1.0

        return VisualState(
            source="QUEEN_CORE_V0.2_VERIFIED_REPAIR",
            tick_count=self.core.tick,
            sim_time=self.core.sim_time,
            dt_sim=self.core.dt_sim,
            r_exec=r_exec,
            f_rt=f_rt,
            event_count=self.core.bus.count,
            queen_mode=self.core.mode,
            generation=self.core.generation,
            active_synapses=sum(1 for s in self.core.synapses if s.enabled),
            repair_level=self.repair.progress,
            crystallization_level=crystal,
            memory_level=memory,
            error_level=error,
            activity_level=activity,
            whole_h256=h.hex(),
            b36_view=b,
            protected_h256=current_protected,
            reference_h256=self.core.reference_protected_h256,
            integrity_match=match,
            repair_verdict=self.core.last_repair_report.verdict,
            repair_reason=self.core.last_repair_report.reason,
            synapses=[SynapseState(**asdict(s)) for s in self.core.synapses],
            relations=list(self.core.relations),
            recent_events=self.core.bus.recent_labels(10),
        )


# =============================================================================
# 7 — VISUALISATION : AQUARIUM / HORLOGE DE LA VIE
# =============================================================================
class LifeClockCanvas(tk.Canvas):
    def __init__(self, master, **kwargs):
        super().__init__(master, bg=THEME["bg"], highlightthickness=0, **kwargs)
        self.state: Optional[VisualState] = None
        self.phase = 0.0
        self.stars: List[Tuple[float, float, int]] = []
        self.bind("<Configure>", lambda _e: self.stars.clear())

    def set_state(self, state: VisualState):
        self.state = state
        self.phase += 0.012 + 0.045 * state.activity_level
        self.redraw()

    @staticmethod
    def node_pos(idx, cx, cy, r):
        a = -math.pi / 2 + idx * math.tau / 7
        return cx + math.cos(a) * r * 0.76, cy + math.sin(a) * r * 0.76

    def gear(self, cx, cy, radius, teeth, angle, color, width=2):
        pts = []
        for i in range(teeth * 2):
            a = angle + i * math.pi / teeth
            rr = radius * (1.0 if i % 2 == 0 else 0.90)
            pts += [cx + math.cos(a) * rr, cy + math.sin(a) * rr]
        self.create_polygon(pts, outline=color, fill="", width=width)

    def meter(self, cx, cy, radius, value, color):
        value = max(0.0, min(1.0, value))
        self.create_oval(cx-radius, cy-radius, cx+radius, cy+radius,
                         outline=THEME["grid"], width=2)
        self.create_arc(cx-radius, cy-radius, cx+radius, cy+radius,
                        start=90, extent=-359.5*value, style="arc",
                        outline=color, width=5)

    def redraw(self):
        self.delete("all")
        s = self.state
        if not s:
            return

        w = max(320, self.winfo_width())
        h = max(320, self.winfo_height())
        cx, cy = w * 0.5, h * 0.5
        r = min(w, h) * 0.34

        for x in range(0, int(w) + 40, 40):
            self.create_line(x, 0, x, h, fill=THEME["grid"])
        for y in range(0, int(h) + 40, 40):
            self.create_line(0, y, w, y, fill=THEME["grid"])

        if not self.stars:
            rng = random.Random(int(w) * 100003 + int(h))
            self.stars = [
                (rng.uniform(0, w), rng.uniform(0, h), rng.choice((1, 1, 1, 2)))
                for _ in range(max(40, int(w*h/18000)))
            ]
        for x, y, rr in self.stars:
            self.create_oval(x-rr, y-rr, x+rr, y+rr,
                             fill=THEME["muted"], outline="")

        # Relations réelles + particules calculées à partir de l'activité.
        for a, b in s.relations:
            x1, y1 = self.node_pos(a, cx, cy, r)
            x2, y2 = self.node_pos(b, cx, cy, r)
            intensity = (s.synapses[a].activity + s.synapses[b].activity) / 2
            color = THEME["cyan"] if intensity > 0.45 else THEME["blue"]
            if not (s.synapses[a].enabled and s.synapses[b].enabled):
                color = THEME["error"]
            self.create_line(x1, y1, x2, y2, fill=color, width=1+3*intensity)
            if intensity > 0.25 and s.synapses[a].enabled and s.synapses[b].enabled:
                q = ((s.tick_count * 0.011) + a*0.19 + b*0.07) % 1.0
                px, py = x1 + (x2-x1)*q, y1 + (y2-y1)*q
                pr = 2 + 3*intensity
                self.create_oval(px-pr, py-pr, px+pr, py+pr,
                                 fill=THEME["gold2"], outline="")

        speed = 0.15 + 0.85*s.activity_level
        self.gear(cx, cy, r*1.02, 36, self.phase*speed, THEME["gold"], 2)
        self.gear(cx, cy, r*0.84, 28, -self.phase*1.25*speed, THEME["cyan"], 2)
        self.gear(cx, cy, r*0.60, 20, self.phase*1.8*speed, THEME["violet"], 2)

        self.meter(cx, cy, r*1.12, s.crystallization_level, THEME["gold"])
        self.meter(cx, cy, r*0.72, s.memory_level, THEME["cyan"])
        self.meter(cx, cy, r*0.48, s.activity_level, THEME["magenta"])

        # Mémoire cristallisée : nombre/forme dérivés uniquement de la métrique.
        count = int(8 + s.crystallization_level * 64)
        rng = random.Random(1307)
        for i in range(count):
            a = rng.random() * math.tau
            rr = r * (0.28 + rng.random()*0.58)
            x = cx + math.cos(a)*rr
            y = cy + math.sin(a)*rr
            size = 2 + 9*s.crystallization_level*(0.35+rng.random()*0.65)
            rot = a + self.phase*0.08
            pts = []
            for k in range(4):
                aa = rot + k*math.pi/2
                mul = 1.0 if k % 2 == 0 else 0.45
                pts += [x + math.cos(aa)*size*mul, y + math.sin(aa)*size*mul]
            self.create_polygon(
                pts, fill="",
                outline=THEME["gold2"] if i % 3 else THEME["cyan"]
            )

        # Synapses.
        for i, syn in enumerate(s.synapses):
            x, y = self.node_pos(i, cx, cy, r)
            pulse = 1 + 0.18*math.sin(self.phase*8+i)
            rr = (12 + 16*syn.activity) * pulse
            if not syn.enabled or syn.integrity <= 0:
                color = THEME["error"]
            elif syn.repair_progress > 0:
                color = THEME["warning"]
            elif syn.crystal > 0.20:
                color = THEME["gold2"]
            else:
                color = THEME["cyan"]

            self.create_oval(x-rr*1.7, y-rr*1.7, x+rr*1.7, y+rr*1.7,
                             outline=THEME["grid"], width=2)
            self.create_oval(x-rr, y-rr, x+rr, y+rr,
                             fill=THEME["panel2"], outline=color, width=3)
            inn = max(3, rr*syn.activity*0.65)
            self.create_oval(x-inn, y-inn, x+inn, y+inn, fill=color, outline="")
            self.create_text(
                x, y+rr+14,
                text=f"{syn.synapse_id}  A:{syn.activity:.2f}  I:{syn.integrity/1000:.2f}",
                fill=THEME["text"], font=("Consolas", 8, "bold")
            )

        mode_color = {
            "SLEEP": THEME["blue"],
            "EVENT": THEME["gold"],
            "BURST": THEME["magenta"],
            "STABLE": THEME["green"],
            "FAULT": THEME["error"],
            "AUTO_REPAIR": THEME["warning"],
        }.get(s.queen_mode, THEME["white"])
        core_r = r*(0.17 + 0.035*math.sin(self.phase*4))
        self.create_oval(cx-core_r*1.5, cy-core_r*1.5, cx+core_r*1.5, cy+core_r*1.5,
                         outline=THEME["grid"], width=3)
        self.create_oval(cx-core_r, cy-core_r, cx+core_r, cy+core_r,
                         fill=THEME["panel"], outline=mode_color, width=4)
        self.create_text(cx, cy-8, text="∞", fill=THEME["gold2"],
                         font=("Georgia", max(20, int(core_r*0.72)), "bold"))
        self.create_text(cx, cy+core_r*0.52, text=s.queen_mode,
                         fill=mode_color, font=("Consolas", 10, "bold"))

        self.create_text(cx, cy-r*1.23, text="HORLOGE DE LA VIE — REINE",
                         fill=THEME["gold2"], font=("Georgia", 15, "bold"))
        self.create_text(
            cx, cy+r*1.24,
            text=f"TICK {s.tick_count:,}  •  GEN {s.generation}  •  SYNAPSES {s.active_synapses}/7  •  REPAIR {s.repair_verdict}",
            fill=THEME["text"], font=("Consolas", 10, "bold")
        )
        self.create_text(
            16, h-14, anchor="sw",
            text=f"WHOLE H256 {s.whole_h256[:18]}…   PROTECTED {'MATCH' if s.integrity_match else 'MISMATCH'}",
            fill=THEME["green"] if s.integrity_match else THEME["error"],
            font=("Consolas", 8, "bold")
        )


# =============================================================================
# 8 — APP
# =============================================================================
class AntmuxLifeClockApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ANTMUX-X72 — MYRMIX LIFE CLOCK — CORE V0.2")
        self.root.configure(bg=THEME["bg"])
        self.root.minsize(1100, 720)
        try:
            self.root.state("zoomed")
        except tk.TclError:
            self.root.geometry("1400x900")

        self.core = QueenCore(seed=72)
        self.repair = RepairEngine(self.core)
        self.telemetry = CoreTelemetryAdapter(self.core, self.repair)

        self.running = True
        self.last_frame = time.perf_counter()
        self.accumulator = 0.0
        self.window_start = self.last_frame
        self.window_ticks = 0
        self.r_exec = 0.0
        self.f_rt = 0.0
        self.metric_labels: Dict[str, tk.Label] = {}
        self.status_var = tk.StringVar(value="CORE prêt — hash protégé conforme à la référence.")

        self.build_ui()
        self.update_ui()

    def build_ui(self):
        header = tk.Frame(self.root, bg=THEME["panel"], height=58)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header, text="ANTMUX-X72  /  MYRMIX-X72-D13-G7",
            bg=THEME["panel"], fg=THEME["gold2"], font=("Georgia", 18, "bold")
        ).pack(side="left", padx=18)
        tk.Label(
            header, text="SOURCE: QUEEN CORE V0.2 — VERIFIED REPAIR PATH",
            bg=THEME["panel"], fg=THEME["green"], font=("Consolas", 9, "bold")
        ).pack(side="right", padx=18)

        body = tk.Frame(self.root, bg=THEME["bg"])
        body.pack(fill="both", expand=True)
        left = tk.Frame(body, bg=THEME["panel"], width=285)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        center = tk.Frame(body, bg=THEME["bg"])
        center.pack(side="left", fill="both", expand=True)
        right = tk.Frame(body, bg=THEME["panel"], width=345)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        self.canvas = LifeClockCanvas(center)
        self.canvas.pack(fill="both", expand=True)

        self.section(left, "TÉLÉMÉTRIE CORE")
        for key, title in [
            ("mode", "QUEEN MODE"), ("tick", "TICK"), ("dt", "dt_sim"),
            ("rexec", "R_exec"), ("frt", "F_rt"), ("activity", "ACTIVITÉ"),
            ("memory", "MÉMOIRE"), ("crystal", "CRISTAL"),
            ("repair", "RÉPARATION"), ("integrity", "INTÉGRITÉ"),
            ("events", "ÉVÉNEMENTS"), ("generation", "GÉNÉRATION"),
        ]:
            self.metric(left, key, title)

        self.section(left, "CONTRÔLES")
        self.pause_button = self.button(left, "PAUSE", self.toggle_run, THEME["cyan"])
        self.button(left, "INJECTER PANNE PROTÉGÉE", self.inject_fault, THEME["error"])
        self.button(left, "RÉPARER + VÉRIFIER", self.request_repair, THEME["warning"])
        self.button(left, "RESET RÉFÉRENCE", self.reset_core, THEME["gold2"])
        self.button(left, "SNAPSHOT JSON", self.save_snapshot, THEME["green"])

        tk.Label(
            left,
            textvariable=self.status_var,
            bg=THEME["panel"], fg=THEME["text"], justify="left",
            wraplength=255, font=("Consolas", 8)
        ).pack(anchor="w", padx=14, pady=14)

        self.section(right, "EVENT BUS")
        self.event_box = tk.Text(
            right, bg=THEME["panel2"], fg=THEME["cyan"], relief="flat",
            height=12, wrap="word", font=("Consolas", 9), state="disabled"
        )
        self.event_box.pack(fill="x", padx=10)

        self.section(right, "SYNAPSES / PREUVE")
        self.synapse_box = tk.Text(
            right, bg=THEME["panel2"], fg=THEME["text"], relief="flat",
            wrap="none", font=("Consolas", 9), state="disabled"
        )
        self.synapse_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    @staticmethod
    def section(parent, title):
        tk.Label(
            parent, text=title, bg=THEME["panel"], fg=THEME["gold"],
            font=("Consolas", 10, "bold")
        ).pack(anchor="w", padx=14, pady=(14, 7))

    def metric(self, parent, key, title):
        row = tk.Frame(parent, bg=THEME["panel2"])
        row.pack(fill="x", padx=10, pady=2)
        tk.Label(row, text=title, bg=THEME["panel2"], fg=THEME["muted"],
                 font=("Consolas", 9)).pack(side="left", padx=8, pady=6)
        val = tk.Label(row, text="—", bg=THEME["panel2"], fg=THEME["text"],
                       font=("Consolas", 9, "bold"))
        val.pack(side="right", padx=8)
        self.metric_labels[key] = val

    @staticmethod
    def button(parent, text, command, fg):
        b = tk.Button(
            parent, text=text, command=command,
            bg=THEME["panel2"], fg=fg,
            activebackground=THEME["grid"], activeforeground=THEME["white"],
            relief="flat", bd=0, font=("Consolas", 10, "bold"),
            cursor="hand2", padx=10, pady=9
        )
        b.pack(fill="x", padx=10, pady=4)
        return b

    def toggle_run(self):
        self.running = not self.running
        self.pause_button.configure(text="PAUSE" if self.running else "REPRENDRE")

    def inject_fault(self):
        try:
            sid = self.core.inject_fault()
            self.status_var.set(
                f"PANNE injectée dans {sid}. Le hash protégé diverge maintenant de la référence."
            )
        except Exception as exc:
            self.status_var.set(f"Injection refusée : {exc}")

    def request_repair(self):
        report = self.repair.begin()
        if self.repair.active:
            self.status_var.set(
                "Réparation réelle démarrée : restauration depuis référence autorisée + fermeture H256."
            )
        else:
            self.status_var.set(f"{report.verdict}: {report.reason}")

    def reset_core(self):
        self.core = QueenCore(seed=72)
        self.repair = RepairEngine(self.core)
        self.telemetry = CoreTelemetryAdapter(self.core, self.repair)
        self.status_var.set("CORE réinitialisé depuis la graine déterministe.")

    def save_snapshot(self):
        state = self.telemetry.visual_state(self.r_exec, self.f_rt)
        path = filedialog.asksaveasfilename(
            title="Sauvegarder snapshot ANTMUX-X72",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialfile=f"antmux_core_tick_{state.tick_count}.json",
        )
        if not path:
            return
        payload = {
            "visual_state": asdict(state),
            "protected_projection": self.core.protected_projection(),
            "reference_protected_h256": self.core.reference_protected_h256,
            "events": self.core.bus.serializable(),
            "last_repair_report": asdict(self.core.last_repair_report),
        }
        Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self.core.bus.emit(self.core.tick, "SNAPSHOT_SAVED", path=Path(path).name)
        self.status_var.set(f"Snapshot sauvegardé : {Path(path).name}")

    def refresh_panels(self, s: VisualState):
        vals = {
            "mode": s.queen_mode,
            "tick": f"{s.tick_count:,}",            "dt": f"{s.dt_sim:.6f}s",
            "rexec": f"{s.r_exec:,.1f}/s",
            "frt": f"{s.f_rt:.3f}×",
            "activity": f"{s.activity_level:.3f}",
            "memory": f"{s.memory_level:.3f}",
            "crystal": f"{s.crystallization_level:.3f}",
            "repair": f"{s.repair_level:.3f}",
            "integrity": "MATCH" if s.integrity_match else "MISMATCH",
            "events": f"{s.event_count:,}",
            "generation": str(s.generation),
        }
        for key, val in vals.items():
            self.metric_labels[key].configure(text=val)
        self.metric_labels["integrity"].configure(
            fg=THEME["green"] if s.integrity_match else THEME["error"]
        )

        self.event_box.configure(state="normal")
        self.event_box.delete("1.0", "end")
        for e in reversed(s.recent_events):
            self.event_box.insert("end", f"• {e}\n")
        self.event_box.configure(state="disabled")

        self.synapse_box.configure(state="normal")
        self.synapse_box.delete("1.0", "end")
        self.synapse_box.insert("end", "ID  ROLE      ACT   MEM   CRYS  INTEG  STATE\n")
        self.synapse_box.insert("end", "─" * 48 + "\n")
        for syn in s.synapses:
            st = "ON" if syn.enabled else "FAULT"
            self.synapse_box.insert(
                "end",
                f"{syn.synapse_id:<3} {syn.role:<9} {syn.activity:.3f} "
                f"{syn.memory:.3f} {syn.crystal:.3f} {syn.integrity:4d}  {st}\n"
            )
        self.synapse_box.insert("end", "\nWHOLE H256\n")
        self.synapse_box.insert("end", s.whole_h256 + "\n\n")
        self.synapse_box.insert("end", "B36_50\n" + s.b36_view + "\n\n")
        self.synapse_box.insert("end", "PROTECTED CURRENT\n" + s.protected_h256 + "\n\n")
        self.synapse_box.insert("end", "PROTECTED REFERENCE\n" + s.reference_h256 + "\n\n")
        self.synapse_box.insert("end", f"VERDICT: {s.repair_verdict}\n{s.repair_reason}\n")
        self.synapse_box.configure(state="disabled")

    def update_ui(self):
        now = time.perf_counter()
        elapsed = min(0.1, max(0.0, now - self.last_frame))
        self.last_frame = now

        if self.running:
            self.accumulator += elapsed
            steps = 0
            while self.accumulator >= self.core.dt_sim and steps < 64:
                self.core.step()
                report = self.repair.step()
                if report is not None:
                    self.status_var.set(f"{report.verdict}: {report.reason}")
                self.accumulator -= self.core.dt_sim
                steps += 1
                self.window_ticks += 1

        window_elapsed = now - self.window_start
        if window_elapsed >= 0.5:
            self.r_exec = self.window_ticks / window_elapsed
            sim_advanced = self.window_ticks * self.core.dt_sim
            self.f_rt = sim_advanced / window_elapsed if window_elapsed > 0 else 0.0
            self.window_ticks = 0
            self.window_start = now

        state = self.telemetry.visual_state(self.r_exec, self.f_rt)
        self.canvas.set_state(state)
        self.refresh_panels(state)
        self.root.after(16, self.update_ui)

    def run(self):
        self.root.mainloop()


# =============================================================================
# 9 — SELF-TESTS NON-GRAPHIQUES
# =============================================================================
def run_self_tests(verbose: bool = True) -> dict:
    results = {}

    # Base36 : zéros initiaux inclus.
    digest = bytes.fromhex("0000" + "AB" * 30)
    b = base36_50(digest)
    results["base36_roundtrip"] = (len(b) == 50 and base36_50_inverse(b) == digest)

    # Déterminisme naissance.
    q1 = QueenCore(seed=72)
    q2 = QueenCore(seed=72)
    results["deterministic_reference"] = (
        q1.reference_protected_h256 == q2.reference_protected_h256
    )

    # Hash protégé stable pendant activité normale.
    ref = q1.current_protected_h256()
    for _ in range(1000):
        q1.step()
    results["protected_stable_during_ticks"] = (q1.current_protected_h256() == ref)

    # Panne détectée par divergence.
    sid = q1.inject_fault("S4")
    fault_hash = q1.current_protected_h256()
    results["fault_changes_protected_hash"] = (
        sid == "S4" and fault_hash != q1.reference_protected_h256
    )

    # Réparation réelle + fermeture hash.
    engine = RepairEngine(q1)
    begin = engine.begin()
    guard = 0
    report = None
    while engine.active and guard < 10000:
        q1.step()
        report = engine.step() or report
        guard += 1
    results["repair_completed"] = report is not None
    results["repair_pass"] = bool(report and report.verdict == "PASS")
    results["repair_closes_reference_hash"] = (
        q1.current_protected_h256() == q1.reference_protected_h256
    )
    results["repaired_synapse_enabled"] = q1.synapses[3].enabled and q1.synapses[3].integrity == 1000

    # Aucun faux succès sans panne.
    invalid = RepairEngine(q1).begin()
    results["no_fault_is_invalid"] = invalid.verdict == "INVALID"

    ok = all(results.values())
    if verbose:
        print("ANTMUX-X72 CORE V0.2 SELF-TEST")
        for name, value in results.items():
            print(f"{'PASS' if value else 'FAIL':4}  {name}")
        print("VERDICT:", "PASS" if ok else "FAIL")
    return {"ok": ok, "tests": results}


def main():
    # Self-test au démarrage : si le noyau de réparation est cassé, ne pas
    # ouvrir une vitrine donnant une impression de succès.
    result = run_self_tests(verbose=True)
    if not result["ok"]:
        raise SystemExit("SELF-TEST CORE V0.2 = FAIL — interface non lancée.")
    AntmuxLifeClockApp().run()


if __name__ == "__main__":
    main()