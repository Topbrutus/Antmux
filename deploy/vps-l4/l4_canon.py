from __future__ import annotations

import os
from collections import Counter, deque
from typing import Any

SCHEMA = "BRUTUS_L4_CANON_V1"
RECENT_LIMIT = 37
VALID_L3 = frozenset({
    "PRESSED_AT_OR_ABOVE_REFERENCE",
    "PRESSED_BELOW_REFERENCE",
})


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "1" if default else "0").strip().lower()
    return raw in {"1", "true", "yes", "on"}


class L4CanonTelemetry:
    """Shadow-only technical canon record downstream of L3.

    The Colonne 37 prototype represented L4_CANON as
    ``canonical_z = z_stamp.z_id``. L4 v1 therefore records the already-existing
    output Z identity as the technical canonical identity after a successful L3
    press. It does not create a new identity and it does not promote scientific
    proof, validation state, or acceptance/rejection.

    Both L3 reference sides remain canon-recordable because L2 is only an
    engineering reference and L3 intentionally preserves both sides. L5 alone
    owns subsequent placement.
    """

    def __init__(self) -> None:
        self.enabled = _env_flag("BROTO_L4_ENABLED", False)
        self.observations = 0
        self.canonical_records = 0
        self.blocked_l3_other = 0
        self.blocked_missing_z = 0
        self.unique_canonical_z: set[str] = set()
        self.reference_sides: Counter[str] = Counter()
        self.by_formula: dict[str, Counter[str]] = {}
        self._recent: deque[dict[str, Any]] = deque(maxlen=RECENT_LIMIT)

    def _record(self, formula_id: str, outcome: str) -> None:
        self.by_formula.setdefault(formula_id, Counter())[outcome] += 1

    def observe(self, formula_id: str, source: Any, out: Any, l3_outcome: str) -> str:
        if not self.enabled:
            return "DISABLED"

        self.observations += 1
        l3 = str(l3_outcome).upper()
        if l3 not in VALID_L3:
            self.blocked_l3_other += 1
            outcome = "BLOCKED_L3_OTHER"
            self._record(formula_id, outcome)
            self._recent.append({
                "formula_id": formula_id,
                "outcome": outcome,
                "l3_outcome": l3,
                "canonical_z": None,
                "canonical_recorded": False,
            })
            return outcome

        z_id = getattr(out, "z_id", None)
        if not z_id:
            self.blocked_missing_z += 1
            outcome = "BLOCKED_MISSING_Z_ID"
            self._record(formula_id, outcome)
            self._recent.append({
                "formula_id": formula_id,
                "outcome": outcome,
                "l3_outcome": l3,
                "canonical_z": None,
                "canonical_recorded": False,
            })
            return outcome

        canonical_z = str(z_id)
        is_new = canonical_z not in self.unique_canonical_z
        self.unique_canonical_z.add(canonical_z)
        self.canonical_records += 1

        if l3 == "PRESSED_AT_OR_ABOVE_REFERENCE":
            side = "AT_OR_ABOVE_REFERENCE"
            outcome = "CANONICAL_Z_RECORDED_AT_OR_ABOVE_REFERENCE"
        else:
            side = "BELOW_REFERENCE"
            outcome = "CANONICAL_Z_RECORDED_BELOW_REFERENCE"
        self.reference_sides[side] += 1
        self._record(formula_id, outcome)
        self._recent.append({
            "formula_id": formula_id,
            "outcome": outcome,
            "l3_outcome": l3,
            "reference_side": side,
            "canonical_z": canonical_z,
            "canonical_z_new": is_new,
            "source_z_id": getattr(source, "z_id", None),
            "output_z_id": z_id,
            "canonical_recorded": True,
        })
        return outcome

    def status(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "mode": SCHEMA,
            "enabled": self.enabled,
            "authority": "SHADOW_ONLY",
            "source_of_truth": "L3_PRESS_OUTCOME_PLUS_EXISTING_OUTPUT_Z_ID",
            "observations": self.observations,
            "canonical_records": self.canonical_records,
            "unique_canonical_z": len(self.unique_canonical_z),
            "blocked_l3_other": self.blocked_l3_other,
            "blocked_missing_z": self.blocked_missing_z,
            "reference_sides": dict(sorted(self.reference_sides.items())),
            "by_formula": {k: dict(v) for k, v in sorted(self.by_formula.items())},
            "recent_limit": RECENT_LIMIT,
            "recent": list(self._recent),
            "canon_definition": "CANONICAL_Z_EQUALS_EXISTING_OUTPUT_Z_ID_AFTER_SUCCESSFUL_L3_PRESS",
            "canonical_z_is_output_z_id": True,
            "creates_new_identity": False,
            "records_both_l3_reference_sides": True,
            "technical_identity_canon": True,
            "scientific_canon_claim": False,
            "canonicalizes_scientific_proof": False,
            "l5_placement_input": True,
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
