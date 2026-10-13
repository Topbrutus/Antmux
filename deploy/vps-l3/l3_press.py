from __future__ import annotations

import os
from collections import Counter, deque
from typing import Any

SCHEMA = "BRUTUS_L3_PRESS_V1"
RECENT_LIMIT = 37
VALID_L2 = frozenset({
    "AT_OR_ABOVE_ENGINEERING_REFERENCE",
    "BELOW_ENGINEERING_REFERENCE",
})


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "1" if default else "0").strip().lower()
    return raw in {"1", "true", "yes", "on"}


class L3PressTelemetry:
    """Shadow-only identity press downstream of L2.

    The Colonne 37 prototype represented L3_PRESS as ``dust_key = z_stamp.z_id``
    and L4_CANON as ``canonical_z = z_stamp.z_id``. L3 v1 therefore does not
    rescore or decide scientific validity. It records the already-stamped output
    Z identity as a deterministic dust key, preserving the L2 reference side.

    Both L2 sides remain pressable because L2 is an engineering comparison, not
    an acceptance/rejection rule. Missing Z identity is blocked rather than
    replaced by an invented identity. L4 alone owns any future canon step.
    """

    def __init__(self) -> None:
        self.enabled = _env_flag("BROTO_L3_ENABLED", False)
        self.observations = 0
        self.pressed = 0
        self.blocked_l2_other = 0
        self.blocked_missing_z = 0
        self.unique_dust_keys: set[str] = set()
        self.reference_sides: Counter[str] = Counter()
        self.by_formula: dict[str, Counter[str]] = {}
        self._recent: deque[dict[str, Any]] = deque(maxlen=RECENT_LIMIT)

    def _record(self, formula_id: str, outcome: str) -> None:
        self.by_formula.setdefault(formula_id, Counter())[outcome] += 1

    def observe(self, formula_id: str, source: Any, out: Any, l2_outcome: str) -> str:
        if not self.enabled:
            return "DISABLED"

        self.observations += 1
        l2 = str(l2_outcome).upper()
        if l2 not in VALID_L2:
            self.blocked_l2_other += 1
            outcome = "BLOCKED_L2_OTHER"
            self._record(formula_id, outcome)
            self._recent.append({"formula_id": formula_id, "outcome": outcome, "l2_outcome": l2, "dust_key": None, "pressed": False})
            return outcome

        z_id = getattr(out, "z_id", None)
        if not z_id:
            self.blocked_missing_z += 1
            outcome = "BLOCKED_MISSING_Z_ID"
            self._record(formula_id, outcome)
            self._recent.append({"formula_id": formula_id, "outcome": outcome, "l2_outcome": l2, "dust_key": None, "pressed": False})
            return outcome

        dust_key = str(z_id)
        is_new = dust_key not in self.unique_dust_keys
        self.unique_dust_keys.add(dust_key)
        self.pressed += 1

        if l2 == "AT_OR_ABOVE_ENGINEERING_REFERENCE":
            side = "AT_OR_ABOVE_REFERENCE"
            outcome = "PRESSED_AT_OR_ABOVE_REFERENCE"
        else:
            side = "BELOW_REFERENCE"
            outcome = "PRESSED_BELOW_REFERENCE"
        self.reference_sides[side] += 1
        self._record(formula_id, outcome)
        self._recent.append({
            "formula_id": formula_id,
            "outcome": outcome,
            "l2_outcome": l2,
            "reference_side": side,
            "dust_key": dust_key,
            "dust_key_new": is_new,
            "source_z_id": getattr(source, "z_id", None),
            "output_z_id": z_id,
            "pressed": True,
        })
        return outcome

    def status(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "mode": SCHEMA,
            "enabled": self.enabled,
            "authority": "SHADOW_ONLY",
            "source_of_truth": "L2_REFERENCE_OUTCOME_PLUS_OUTPUT_Z_ID",
            "observations": self.observations,
            "pressed": self.pressed,
            "unique_dust_keys": len(self.unique_dust_keys),
            "blocked_l2_other": self.blocked_l2_other,
            "blocked_missing_z": self.blocked_missing_z,
            "reference_sides": dict(sorted(self.reference_sides.items())),
            "by_formula": {k: dict(v) for k, v in sorted(self.by_formula.items())},
            "recent_limit": RECENT_LIMIT,
            "recent": list(self._recent),
            "press_definition": "DUST_KEY_EQUALS_EXISTING_OUTPUT_Z_ID",
            "dust_key_is_output_z_id": True,
            "creates_new_identity": False,
            "presses_both_l2_reference_sides": True,
            "l4_canon_input": True,
            "canonizes": False,
            "assigns_score": False,
            "applies_threshold": False,
            "accepts_candidate": False,
            "rejects_candidate": False,
            "scientific_proof_claim": False,
            "validation_state_mutated": False,
            "controls_routing": False,
            "controls_scheduling": False,
            "controls_calculation": False,
            "reserves_resources": False,
            "executes_replay": False,
            "schedules_replay": False,
            "compute_skips": 0,
            "value_mutated": False,
            "proof_promotion": False,
        }
