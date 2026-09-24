from __future__ import annotations

import copy
from typing import Any, Callable

from .resonance_structure import ResonanceStructure

SCHEMA = "ANTMUX-X72-RESONANCE-BRIDGE-v0.1"


class ResonanceWheelBridge:
    """Read-only interface between the independent resonance structure and wheel.

    The bridge can observe a wheel state through an injected reader. It exposes
    no command sink and no mutation surface. Returned wheel states are deep
    copies so consumers cannot mutate the source object through the bridge.
    """

    def __init__(
        self,
        structure: ResonanceStructure,
        *,
        wheel_state_reader: Callable[[], dict[str, Any]] | None = None,
    ):
        self.structure = structure
        self.wheel_state_reader = wheel_state_reader
        self.read_count = 0

    def read_wheel(self) -> dict[str, Any] | None:
        if self.wheel_state_reader is None:
            return None
        state = self.wheel_state_reader()
        if not isinstance(state, dict):
            raise TypeError("wheel_state_reader must return a dict")
        self.read_count += 1
        return copy.deepcopy(state)

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "status": "CANDIDATE",
            "standalone_structure": True,
            "wheel_optional": True,
            "read_only": True,
            "mutates_wheel": False,
            "wheel_reader_attached": self.wheel_state_reader is not None,
            "read_count": self.read_count,
            "structure": self.structure.snapshot(),
        }
