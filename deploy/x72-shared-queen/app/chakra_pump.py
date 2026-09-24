from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any

SCHEMA = "ANTMUX-X72-CHAKRA-PUMP-v0.1"
CHECKPOINT_SCHEMA = "ANTMUX-X72-CHAKRA-PUMP-CHECKPOINT-v0.1"
LEVEL_LABELS = tuple(f"CH{i}" for i in range(1, 8))


def _hash_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class ChakraPumpConfig:
    min_level: int = 1
    max_level: int = 7
    initial_target_level: int = 2
    ticks_per_level: int = 240

    def validate(self) -> None:
        if self.min_level != 1:
            raise ValueError("min_level must be 1")
        if self.max_level < 2:
            raise ValueError("max_level must be >= 2")
        if not self.min_level < self.initial_target_level <= self.max_level:
            raise ValueError("initial_target_level must be within pump range")
        if self.ticks_per_level < 1:
            raise ValueError("ticks_per_level must be >= 1")


@dataclass
class ChakraPumpState:
    schema: str
    queen_tick: int
    current_level: int
    target_level: int
    direction: str
    completed_cycles: int
    completed_escalations: int
    retained_boost: float
    phase_ticks: int
    integrity_ready: bool
    stability_ready: bool
    blocked_reason: str | None
    up_route: tuple[str, ...]
    down_route: tuple[str, ...]
    physical_claim: bool = False
    whole_h256: str = ""

    def payload(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "queen_tick": self.queen_tick,
            "current_level": self.current_level,
            "target_level": self.target_level,
            "direction": self.direction,
            "completed_cycles": self.completed_cycles,
            "completed_escalations": self.completed_escalations,
            "retained_boost": self.retained_boost,
            "phase_ticks": self.phase_ticks,
            "integrity_ready": self.integrity_ready,
            "stability_ready": self.stability_ready,
            "blocked_reason": self.blocked_reason,
            "up_route": list(self.up_route),
            "down_route": list(self.down_route),
            "physical_claim": self.physical_claim,
        }

    def to_dict(self) -> dict[str, Any]:
        out = self.payload()
        out["whole_h256"] = self.whole_h256
        return out


class ProgressiveChakraPump:
    """Deterministic software overlay for progressive up/down level traversal.

    The labels CH1..CH7 are software-state labels only. This module makes no
    biological, medical, or physical-energy claim and does not mutate QueenCore
    or NoyauEngine state.
    """

    def __init__(self, config: ChakraPumpConfig | None = None):
        self.config = config or ChakraPumpConfig()
        self.config.validate()
        self.current_level = self.config.min_level
        self.target_level = self.config.initial_target_level
        self.direction = "UP"
        self.completed_cycles = 0
        self.completed_escalations = 0
        self.phase_ticks = 0
        self.queen_tick = 0
        self.integrity_ready = True
        self.stability_ready = False
        self.blocked_reason: str | None = "WAIT_STABILITY"
        self._last_state: ChakraPumpState | None = None

    @property
    def retained_boost(self) -> float:
        span = self.config.max_level - self.config.initial_target_level
        if span <= 0:
            return 1.0
        return round(self.completed_escalations / span, 9)

    def _routes(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
        up = tuple(f"CH{i}" for i in range(self.config.min_level, self.target_level + 1))
        return up, tuple(reversed(up))

    def _blocked_reason(self) -> str | None:
        if not self.integrity_ready:
            return "WAIT_INTEGRITY"
        if not self.stability_ready:
            return "WAIT_STABILITY"
        return None

    def _advance_one_level(self) -> None:
        if self.direction == "UP":
            if self.current_level < self.target_level:
                self.current_level += 1
            if self.current_level >= self.target_level:
                self.current_level = self.target_level
                self.direction = "DOWN"
            return

        if self.direction != "DOWN":
            raise ValueError("invalid pump direction")

        if self.current_level > self.config.min_level:
            self.current_level -= 1
        if self.current_level <= self.config.min_level:
            self.current_level = self.config.min_level
            self.completed_cycles += 1
            if self.target_level < self.config.max_level:
                self.target_level += 1
                self.completed_escalations += 1
            self.direction = "UP"

    def step(
        self,
        *,
        queen_tick: int,
        integrity_ready: bool,
        stability_ready: bool,
    ) -> ChakraPumpState:
        if type(queen_tick) is not int or queen_tick < 0:
            raise ValueError("queen_tick must be a non-negative integer")
        if queen_tick < self.queen_tick:
            raise ValueError("queen_tick cannot move backwards")

        self.queen_tick = queen_tick
        self.integrity_ready = bool(integrity_ready)
        self.stability_ready = bool(stability_ready)
        self.blocked_reason = self._blocked_reason()

        if self.blocked_reason is None:
            self.phase_ticks += 1
            if self.phase_ticks >= self.config.ticks_per_level:
                self.phase_ticks = 0
                self._advance_one_level()

        state = self._compose_state()
        self._last_state = state
        return state

    def snapshot(self) -> ChakraPumpState:
        if self._last_state is None:
            return self._compose_state()
        return self._clone_state(self._last_state)

    def visual_payload(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "status": "CANDIDATE",
            "authority": "OBSERVATION_ONLY",
            "mutates_queen": False,
            "mutates_noyau": False,
            "physical_claim": False,
            "state": self.snapshot().to_dict(),
        }

    def _compose_state(self) -> ChakraPumpState:
        up, down = self._routes()
        state = ChakraPumpState(
            schema=SCHEMA,
            queen_tick=self.queen_tick,
            current_level=self.current_level,
            target_level=self.target_level,
            direction=self.direction,
            completed_cycles=self.completed_cycles,
            completed_escalations=self.completed_escalations,
            retained_boost=self.retained_boost,
            phase_ticks=self.phase_ticks,
            integrity_ready=self.integrity_ready,
            stability_ready=self.stability_ready,
            blocked_reason=self.blocked_reason,
            up_route=up,
            down_route=down,
            physical_claim=False,
        )
        state.whole_h256 = _hash_payload(state.payload())
        return state

    def to_checkpoint(self) -> dict[str, Any]:
        checkpoint = {
            "schema": CHECKPOINT_SCHEMA,
            "config": asdict(self.config),
            "state": self.snapshot().to_dict(),
        }
        checkpoint["checkpoint_h256"] = _hash_payload(checkpoint)
        return checkpoint

    @classmethod
    def from_checkpoint(
        cls,
        checkpoint: dict[str, Any] | None,
        *,
        default_config: ChakraPumpConfig | None = None,
    ) -> "ProgressiveChakraPump":
        if checkpoint is None:
            return cls(default_config)

        if checkpoint.get("schema") != CHECKPOINT_SCHEMA:
            raise ValueError("invalid chakra pump checkpoint schema")

        supplied_hash = checkpoint.get("checkpoint_h256")
        hash_payload = {k: v for k, v in checkpoint.items() if k != "checkpoint_h256"}
        if supplied_hash != _hash_payload(hash_payload):
            raise ValueError("chakra pump checkpoint hash mismatch")

        config = ChakraPumpConfig(**checkpoint["config"])
        engine = cls(config)
        state = checkpoint["state"]

        state_hash = state.get("whole_h256")
        state_payload = {k: v for k, v in state.items() if k != "whole_h256"}
        if state_hash != _hash_payload(state_payload):
            raise ValueError("chakra pump state hash mismatch")

        engine.queen_tick = int(state["queen_tick"])
        engine.current_level = int(state["current_level"])
        engine.target_level = int(state["target_level"])
        engine.direction = str(state["direction"])
        engine.completed_cycles = int(state["completed_cycles"])
        engine.completed_escalations = int(state["completed_escalations"])
        engine.phase_ticks = int(state["phase_ticks"])
        engine.integrity_ready = bool(state["integrity_ready"])
        engine.stability_ready = bool(state["stability_ready"])
        engine.blocked_reason = state.get("blocked_reason")
        engine._validate_runtime_state()
        engine._last_state = engine._compose_state()

        if engine._last_state.whole_h256 != state_hash:
            raise ValueError("chakra pump checkpoint state is inconsistent")
        return engine

    def _validate_runtime_state(self) -> None:
        if not self.config.min_level <= self.current_level <= self.target_level <= self.config.max_level:
            raise ValueError("chakra pump levels are out of range")
        if self.direction not in {"UP", "DOWN"}:
            raise ValueError("invalid chakra pump direction")
        if self.phase_ticks < 0 or self.phase_ticks >= self.config.ticks_per_level:
            raise ValueError("invalid chakra pump phase_ticks")
        max_escalations = self.config.max_level - self.config.initial_target_level
        if not 0 <= self.completed_escalations <= max_escalations:
            raise ValueError("invalid chakra pump completed_escalations")
        if self.completed_cycles < self.completed_escalations:
            raise ValueError("completed_cycles cannot be lower than completed_escalations")

    @staticmethod
    def _clone_state(state: ChakraPumpState) -> ChakraPumpState:
        return ChakraPumpState(
            schema=state.schema,
            queen_tick=state.queen_tick,
            current_level=state.current_level,
            target_level=state.target_level,
            direction=state.direction,
            completed_cycles=state.completed_cycles,
            completed_escalations=state.completed_escalations,
            retained_boost=state.retained_boost,
            phase_ticks=state.phase_ticks,
            integrity_ready=state.integrity_ready,
            stability_ready=state.stability_ready,
            blocked_reason=state.blocked_reason,
            up_route=tuple(state.up_route),
            down_route=tuple(state.down_route),
            physical_claim=state.physical_claim,
            whole_h256=state.whole_h256,
        )
