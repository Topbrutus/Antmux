from __future__ import annotations

from typing import Any

from .engine import NoyauEngine, NoyauState

ADAPTER_SCHEMA = "ANTMUX-X72-NOYAU-SERVER-ADAPTER-v0.1"


class NoyauServerAdapter:
    """Read-only contract for the existing X72 Shared Queen runtime."""

    def __init__(self, engine: NoyauEngine | None = None):
        self.engine = engine or NoyauEngine()

    def tick(self, steps: int = 1) -> NoyauState:
        return self.engine.step(steps)

    def visual_payload(self) -> dict[str, Any]:
        state = self.engine.snapshot()
        return {
            "schema": ADAPTER_SCHEMA,
            "authority": "NOYAU_ENGINE_HEADLESS",
            "control": {
                "held_input": self.engine.held_input,
                "held_percent": round(self.engine.held_input * 100.0, 3),
                "mode": "HELD",
            },
            "noyau": state.to_dict(),
        }

    def set_held_input(self, value: float) -> dict[str, Any]:
        self.engine.set_held_input(value)
        return self.visual_payload()

    def inject(self, strength: float = 1.15) -> dict[str, Any]:
        self.engine.inject(strength)
        return self.visual_payload()

    def intercept(self, strength: float = 0.35) -> dict[str, Any]:
        self.engine.intercept(strength)
        return self.visual_payload()

    def switch_world(self, world_index: int) -> dict[str, Any]:
        self.engine.switch_world(world_index)
        return self.visual_payload()

    def to_checkpoint(self) -> dict[str, Any]:
        return {
            "schema": ADAPTER_SCHEMA,
            "engine": self.engine.to_checkpoint(),
        }

    @classmethod
    def from_checkpoint(cls, checkpoint: dict[str, Any] | None) -> "NoyauServerAdapter":
        if checkpoint is None:
            return cls()
        if checkpoint.get("schema") != ADAPTER_SCHEMA:
            raise ValueError("invalid noyau adapter checkpoint schema")
        return cls(engine=NoyauEngine.from_checkpoint(checkpoint.get("engine")))
