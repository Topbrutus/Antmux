from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from typing import Any

SCHEMA = "ANTMUX-X72-NOYAU-DYNAMIC-v0.2"
CHECKPOINT_SCHEMA = "ANTMUX-X72-NOYAU-CHECKPOINT-v0.2"
CENTER_GATES = ("C1", "C2", "C3")
UP_ROUTE = ("SOURCE", "C1", "C2", "C3", "SORTIE")
DOWN_ROUTE = ("SORTIE", "C3", "C2", "C1", "SOURCE")
WORLD_NAMES = ("HELIX", "TORUS", "GRID", "OBSIDIAN")


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


@dataclass(frozen=True)
class NoyauConfig:
    dt: float = 0.035
    base_frequency_hz: float = 1.0
    crystal_spawn_threshold: float = 1.35
    crystal_stability_epsilon: float = 0.015
    crystal_stability_cycles: int = 24
    max_crystals: int = 128


@dataclass
class CrystalState:
    crystal_id: int
    born_tick: int
    world_index: int
    strength: float
    age: int = 0
    ttl: int = 100

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BasinState:
    inflow: float = 0.0
    outflow: float = 0.0
    crystal_index: float = 0.0
    injection_pending: float = 0.0
    interception_pending: float = 0.0
    stable_cycles: int = 0
    crystallized: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NoyauState:
    schema: str
    tick: int
    sim_time: float
    dt: float
    world_index: int
    world_name: str
    speed: float
    coherence: float
    feedback: float
    phase_left: float
    phase_right: float
    center_gates: tuple[str, ...]
    up_route: tuple[str, ...]
    down_route: tuple[str, ...]
    node_signals: dict[str, float]
    basin1: BasinState
    active_crystals: list[CrystalState]
    whole_h256: str = ""

    def payload(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "tick": self.tick,
            "sim_time": self.sim_time,
            "dt": self.dt,
            "world_index": self.world_index,
            "world_name": self.world_name,
            "speed": self.speed,
            "coherence": self.coherence,
            "feedback": self.feedback,
            "phase_left": self.phase_left,
            "phase_right": self.phase_right,
            "center_gates": list(self.center_gates),
            "up_route": list(self.up_route),
            "down_route": list(self.down_route),
            "node_signals": dict(self.node_signals),
            "basin1": self.basin1.to_dict(),
            "active_crystals": [c.to_dict() for c in self.active_crystals],
        }

    def to_dict(self) -> dict[str, Any]:
        out = self.payload()
        out["whole_h256"] = self.whole_h256
        return out


class NoyauEngine:
    """Headless dynamic nucleus. No UI dependency is allowed here."""

    def __init__(self, config: NoyauConfig | None = None):
        self.config = config or NoyauConfig()
        self.tick = 0
        self.sim_time = 0.0
        self.speed = 1.0
        self.coherence = 0.55
        self.feedback = 0.25
        self.world_index = 0
        self._injection_pending = 0.0
        self._interception_pending = 0.0
        self._next_crystal_id = 1
        self._crystals: list[CrystalState] = []
        self._last_crystal_index: float | None = None
        self._stable_cycles = 0
        self._last_state: NoyauState | None = None

    @property
    def world_name(self) -> str:
        return WORLD_NAMES[self.world_index]

    def set_speed(self, value: float) -> None:
        self.speed = clamp(float(value), 0.1, 4.0)

    def set_coherence(self, value: float) -> None:
        self.coherence = clamp(float(value), 0.0, 1.0)

    def set_feedback(self, value: float) -> None:
        self.feedback = clamp(float(value), 0.0, 1.2)

    def switch_world(self, index: int) -> None:
        if type(index) is not int:
            raise TypeError("world index must be int")
        if not 0 <= index < len(WORLD_NAMES):
            raise ValueError("world index must be 0..3")
        self.world_index = index

    def inject(self, strength: float = 1.15) -> None:
        if not math.isfinite(strength) or strength < 0:
            raise ValueError("injection strength must be finite and >= 0")
        self._injection_pending += strength

    def intercept(self, strength: float = 0.35) -> None:
        if not math.isfinite(strength) or strength < 0:
            raise ValueError("interception strength must be finite and >= 0")
        self._interception_pending += strength

    def _node_signal(self, name: str) -> float:
        names = ("SOURCE", "B1", "B2", "B3", "SORTIE")
        idx = names.index(name)
        phase = 0.55 * idx
        base = 0.45 + 0.30 * math.sin(2.0 * self.sim_time + phase)
        mod = 0.18 * math.sin(5.0 * self.sim_time - 0.7 * phase)
        sync = 0.20 * self.coherence
        return max(0.0, base + mod + sync)

    def _basin1(self, update_stability: bool = True) -> BasinState:
        inflow = (
            0.95
            + 0.55 * math.sin(2.3 * self.sim_time)
            + 0.28 * math.sin(6.2 * self.sim_time + 1.2)
            + self._injection_pending
        )
        inflow *= 0.80 + 0.40 * self.coherence
        inflow = max(0.0, inflow)
        crystal_index = inflow * (0.45 + self.coherence) * (1.0 + 0.5 * self.feedback)
        raw_out = 0.62 * inflow + 0.26 * crystal_index + 0.18 * math.sin(2.3 * self.sim_time - 0.9)
        interception = clamp(self._interception_pending, 0.0, 0.95)
        outflow = max(0.0, raw_out * (1.0 - interception))

        if update_stability:
            if self._last_crystal_index is not None:
                if abs(crystal_index - self._last_crystal_index) <= self.config.crystal_stability_epsilon:
                    self._stable_cycles += 1
                else:
                    self._stable_cycles = 0
            self._last_crystal_index = crystal_index

        return BasinState(
            inflow=round(inflow, 9),
            outflow=round(outflow, 9),
            crystal_index=round(crystal_index, 9),
            injection_pending=round(self._injection_pending, 9),
            interception_pending=round(self._interception_pending, 9),
            stable_cycles=self._stable_cycles,
            crystallized=self._stable_cycles >= self.config.crystal_stability_cycles,
        )

    def _advance_crystals(self, basin: BasinState) -> None:
        for crystal in self._crystals:
            crystal.age += 1
        self._crystals = [c for c in self._crystals if c.age < c.ttl]
        spawn = basin.crystal_index > self.config.crystal_spawn_threshold and self.tick % 4 == 0
        if spawn and len(self._crystals) < self.config.max_crystals:
            self._crystals.append(
                CrystalState(
                    crystal_id=self._next_crystal_id,
                    born_tick=self.tick,
                    world_index=self.world_index,
                    strength=round(clamp(basin.crystal_index / 2.8, 0.0, 1.0), 9),
                    ttl=85 + 25 * self.world_index,
                )
            )
            self._next_crystal_id += 1

    def _decay_controls(self) -> None:
        self._injection_pending *= 0.92
        self._interception_pending *= 0.90
        if self._injection_pending < 1e-12:
            self._injection_pending = 0.0
        if self._interception_pending < 1e-12:
            self._interception_pending = 0.0

    def _compose_state(self, basin: BasinState) -> NoyauState:
        omega = 2.0 * math.pi * self.config.base_frequency_hz
        state = NoyauState(
            schema=SCHEMA,
            tick=self.tick,
            sim_time=round(self.sim_time, 9),
            dt=self.config.dt,
            world_index=self.world_index,
            world_name=self.world_name,
            speed=round(self.speed, 9),
            coherence=round(self.coherence, 9),
            feedback=round(self.feedback, 9),
            phase_left=round((omega * self.sim_time) % (2.0 * math.pi), 9),
            phase_right=round((-omega * self.sim_time) % (2.0 * math.pi), 9),
            center_gates=CENTER_GATES,
            up_route=UP_ROUTE,
            down_route=DOWN_ROUTE,
            node_signals={name: round(self._node_signal(name), 9) for name in ("SOURCE", "B1", "B2", "B3", "SORTIE")},
            basin1=basin,
            active_crystals=[CrystalState(**asdict(c)) for c in self._crystals],
        )
        state.whole_h256 = self._hash_state(state)
        return state

    def step(self, steps: int = 1) -> NoyauState:
        if type(steps) is not int or steps < 1:
            raise ValueError("steps must be a positive integer")
        state: NoyauState | None = None
        for _ in range(steps):
            self.tick += 1
            self.sim_time += self.config.dt * self.speed
            basin = self._basin1(update_stability=True)
            self._advance_crystals(basin)
            state = self._compose_state(basin)
            self._last_state = state
            self._decay_controls()
        assert state is not None
        return state

    def snapshot(self) -> NoyauState:
        if self._last_state is None:
            return self._compose_state(self._basin1(update_stability=False))
        return self._clone_state(self._last_state)

    def reset(self) -> NoyauState:
        config = self.config
        self.__init__(config=config)
        return self.step()

    def to_checkpoint(self) -> dict[str, Any]:
        checkpoint = {
            "schema": CHECKPOINT_SCHEMA,
            "config": asdict(self.config),
            "tick": self.tick,
            "sim_time": self.sim_time,
            "speed": self.speed,
            "coherence": self.coherence,
            "feedback": self.feedback,
            "world_index": self.world_index,
            "injection_pending": self._injection_pending,
            "interception_pending": self._interception_pending,
            "next_crystal_id": self._next_crystal_id,
            "crystals": [c.to_dict() for c in self._crystals],
            "last_crystal_index": self._last_crystal_index,
            "stable_cycles": self._stable_cycles,
            "last_state": self._last_state.to_dict() if self._last_state is not None else None,
        }
        raw = json.dumps(
            checkpoint,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        checkpoint["checkpoint_h256"] = hashlib.sha256(raw).hexdigest()
        return checkpoint

    @classmethod
    def from_checkpoint(cls, checkpoint: dict[str, Any] | None) -> "NoyauEngine":
        if checkpoint is None:
            return cls()
        if checkpoint.get("schema") != CHECKPOINT_SCHEMA:
            raise ValueError("invalid noyau checkpoint schema")
        expected = checkpoint.get("checkpoint_h256")
        canonical = dict(checkpoint)
        canonical.pop("checkpoint_h256", None)
        raw = json.dumps(
            canonical,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        if not isinstance(expected, str) or hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError("invalid noyau checkpoint hash")
        engine = cls(NoyauConfig(**checkpoint["config"]))
        engine.tick = int(checkpoint["tick"])
        engine.sim_time = float(checkpoint["sim_time"])
        engine.speed = clamp(float(checkpoint["speed"]), 0.1, 4.0)
        engine.coherence = clamp(float(checkpoint["coherence"]), 0.0, 1.0)
        engine.feedback = clamp(float(checkpoint["feedback"]), 0.0, 1.2)
        engine.switch_world(int(checkpoint["world_index"]))
        engine._injection_pending = float(checkpoint.get("injection_pending", 0.0))
        engine._interception_pending = float(checkpoint.get("interception_pending", 0.0))
        engine._next_crystal_id = int(checkpoint.get("next_crystal_id", 1))
        engine._crystals = [CrystalState(**item) for item in checkpoint.get("crystals", [])]
        last_index = checkpoint.get("last_crystal_index")
        engine._last_crystal_index = None if last_index is None else float(last_index)
        engine._stable_cycles = int(checkpoint.get("stable_cycles", 0))
        last_state = checkpoint.get("last_state")
        if last_state is not None:
            engine._last_state = cls._state_from_dict(last_state)
            if not cls.verify_state(engine._last_state):
                raise ValueError("invalid noyau checkpoint state hash")
        return engine

    @staticmethod
    def _state_from_dict(data: dict[str, Any]) -> NoyauState:
        return NoyauState(
            schema=str(data["schema"]),
            tick=int(data["tick"]),
            sim_time=float(data["sim_time"]),
            dt=float(data["dt"]),
            world_index=int(data["world_index"]),
            world_name=str(data["world_name"]),
            speed=float(data["speed"]),
            coherence=float(data["coherence"]),
            feedback=float(data["feedback"]),
            phase_left=float(data["phase_left"]),
            phase_right=float(data["phase_right"]),
            center_gates=tuple(data["center_gates"]),
            up_route=tuple(data["up_route"]),
            down_route=tuple(data["down_route"]),
            node_signals={str(k): float(v) for k, v in data["node_signals"].items()},
            basin1=BasinState(**data["basin1"]),
            active_crystals=[CrystalState(**item) for item in data["active_crystals"]],
            whole_h256=str(data["whole_h256"]),
        )

    @staticmethod
    def _hash_state(state: NoyauState) -> str:
        raw = json.dumps(state.payload(), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _clone_state(state: NoyauState) -> NoyauState:
        return NoyauState(
            schema=state.schema,
            tick=state.tick,
            sim_time=state.sim_time,
            dt=state.dt,
            world_index=state.world_index,
            world_name=state.world_name,
            speed=state.speed,
            coherence=state.coherence,
            feedback=state.feedback,
            phase_left=state.phase_left,
            phase_right=state.phase_right,
            center_gates=tuple(state.center_gates),
            up_route=tuple(state.up_route),
            down_route=tuple(state.down_route),
            node_signals=dict(state.node_signals),
            basin1=BasinState(**state.basin1.to_dict()),
            active_crystals=[CrystalState(**c.to_dict()) for c in state.active_crystals],
            whole_h256=state.whole_h256,
        )

    @staticmethod
    def verify_state(state: NoyauState) -> bool:
        return (
            state.schema == SCHEMA
            and tuple(state.center_gates) == CENTER_GATES
            and tuple(state.up_route) == UP_ROUTE
            and tuple(state.down_route) == DOWN_ROUTE
            and 0.0 <= state.coherence <= 1.0
            and 0.0 <= state.feedback <= 1.2
            and 0 <= state.world_index < len(WORLD_NAMES)
            and state.whole_h256 == NoyauEngine._hash_state(state)
        )

[executed on device: Topbrutus (e13fd46c-c560-41e2-9c1c-bd2561c44abb)]