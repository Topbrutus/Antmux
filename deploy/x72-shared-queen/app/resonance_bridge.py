from __future__ import annotations

import copy
import time
from dataclasses import dataclass
from typing import Any, Callable

from .resonance_structure import ResonanceStructure

SCHEMA = "ANTMUX-X72-RESONANCE-BRIDGE-v0.1"


@dataclass(frozen=True)
class BridgeCommand:
    name: str
    payload: dict[str, Any]
    created_at: float
    delivered: bool
    authority: str = "CONTROLLED_COMMAND"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "payload": copy.deepcopy(self.payload),
            "created_at": self.created_at,
            "delivered": self.delivered,
            "authority": self.authority,
        }


class ResonanceWheelBridge:
    """Minimal explicit interface between the independent structure and wheel.

    Default mode is read-only. No Queen/Noyau import is used here. A caller may
    supply a state reader, and optionally a command sink. Commands are never
    delivered unless allow_commands=True was explicitly selected by the caller.
    """

    ALLOWED_COMMANDS = frozenset({"SET_TEST_SIGNAL", "CLEAR_TEST_SIGNAL", "MARK_TEST"})

    def __init__(
        self,
        structure: ResonanceStructure,
        *,
        wheel_state_reader: Callable[[], dict[str, Any]] | None = None,
        wheel_command_sink: Callable[[str, dict[str, Any]], Any] | None = None,
        allow_commands: bool = False,
    ):
        self.structure = structure
        self.wheel_state_reader = wheel_state_reader
        self.wheel_command_sink = wheel_command_sink
        self.allow_commands = bool(allow_commands)
        self.command_log: list[BridgeCommand] = []
        self.read_count = 0

    def read_wheel(self) -> dict[str, Any] | None:
        if self.wheel_state_reader is None:
            return None
        state = self.wheel_state_reader()
        if not isinstance(state, dict):
            raise TypeError("wheel_state_reader must return a dict")
        self.read_count += 1
        return copy.deepcopy(state)

    def make_command(self, name: str, payload: dict[str, Any] | None = None) -> BridgeCommand:
        if name not in self.ALLOWED_COMMANDS:
            raise ValueError(f"unsupported bridge command: {name}")
        body = copy.deepcopy(payload or {})
        delivered = False
        if self.allow_commands:
            if self.wheel_command_sink is None:
                raise RuntimeError("allow_commands=True requires wheel_command_sink")
            self.wheel_command_sink(name, copy.deepcopy(body))
            delivered = True
        command = BridgeCommand(
            name=name,
            payload=body,
            created_at=time.time(),
            delivered=delivered,
        )
        self.command_log.append(command)
        return command

    def comparison_payload(self, *, legacy_direct_present: bool) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "architecture_direct": {
                "status": "EXPERIENCE_CANDIDATE" if legacy_direct_present else "NOT_AVAILABLE",
                "coupling": "IN_QUEEN_STEP" if legacy_direct_present else "UNKNOWN",
            },
            "architecture_bridge": {
                "status": "CANDIDATE",
                "standalone_structure": True,
                "wheel_reader_attached": self.wheel_state_reader is not None,
                "commands_enabled": self.allow_commands,
                "default_mutation": False,
            },
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "status": "CANDIDATE",
            "standalone_structure": True,
            "wheel_optional": True,
            "read_only_default": True,
            "commands_enabled": self.allow_commands,
            "mutates_wheel_by_default": False,
            "read_count": self.read_count,
            "commands": [item.to_dict() for item in self.command_log[-64:]],
            "structure": self.structure.snapshot(),
        }
