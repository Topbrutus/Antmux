from __future__ import annotations

import os
from collections import Counter, deque
from typing import Any

SCHEMA = "BRUTUS_L5_PLACEMENT_V1"
RECENT_LIMIT = 37
PLACEMENT = "HOT"
VALID_L4 = frozenset({
    "CANONICAL_Z_RECORDED_AT_OR_ABOVE_REFERENCE",
    "CANONICAL_Z_RECORDED_BELOW_REFERENCE",
})


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "1" if default else "0").strip().lower()
    return raw in {"1", "true", "yes", "on"}


class L5PlacementTelemetry:
    """Shadow-only logical placement downstream of L4 Canon.

    The Colonne 37 prototype represented L5_PLACEMENT literally as ``HOT``.
    L5 v1 preserves that source contract without inventing WARM/COLD classes or
    physical meanings. A successful L4 technical canon is placed in the logical
    HOT class; blocked L4 observations remain blocked.
    """

    def __init__(self) -> None:
        self.enabled = _env_flag("BROTO_L5_ENABLED", False)
        self.observations = 0
        self.placed = 0
        self.blocked_l4_other = 0
        self.blocked_missing_z = 0
        self.unique_placed_z: set[str] = set()
        self.placement_classes: Counter[str] = Counter()
        self.reference_sides: Counter[str] = Counter()
        self.by_formula: dict[str, Counter[str]] = {}
        self._recent: deque[dict[str, Any]] = deque(maxlen=RECENT_LIMIT)

    def _record(self, formula_id: str, outcome: str) -> None:
        self.by_formula.setdefault(formula_id, Counter())[outcome] += 1

    def observe(self, formula_id: str, source: Any, out: Any, l4_outcome: str) -> str:
        if not self.enabled:
            return "DISABLED"

        self.observations += 1
        l4 = str(l4_outcome).upper()
        if l4 not in VALID_L4:
            self.blocked_l4_other += 1
            outcome = "BLOCKED_L4_OTHER"
            self._record(formula_id, outcome)
            self._recent.append({
                "formula_id": formula_id,
                "outcome": outcome,
                "l4_outcome": l4,
                "placement": None,
                "canonical_z": None,
                "placed": False,
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
                "l4_outcome": l4,
                "placement": None,
                "canonical_z": None,
                "placed": False,
            })
            return outcome

        canonical_z = str(z_id)
        is_new = canonical_z not in self.unique_placed_z
        self.unique_placed_z.add(canonical_z)
        self.placed += 1
        self.placement_classes[PLACEMENT] += 1

        if l4 == "CANONICAL_Z_RECORDED_AT_OR_ABOVE_REFERENCE":
            side = "AT_OR_ABOVE_REFERENCE"
            outcome = "PLACED_HOT_AT_OR_ABOVE_REFERENCE"
        else:
            side = "BELOW_REFERENCE"
            outcome = "PLACED_HOT_BELOW_REFERENCE"
        self.reference_sides[side] += 1
        self._record(formula_id, outcome)
        self._recent.append({
            "formula_id": formula_id,
            "outcome": outcome,
            "l4_outcome": l4,
            "reference_side": side,
            "placement": PLACEMENT,
            "canonical_z": canonical_z,
            "canonical_z_new_for_l5": is_new,
            "source_z_id": getattr(source, "z_id", None),
            "output_z_id": z_id,
            "placed": True,
        })
        return outcome

    def status(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "mode": SCHEMA,
            "enabled": self.enabled,
            "authority": "SHADOW_ONLY",
            "source_of_truth": "L4_TECHNICAL_CANON_OUTCOME_PLUS_EXISTING_OUTPUT_Z_ID",
            "observations": self.observations,
            "placed": self.placed,
            "unique_placed_z": len(self.unique_placed_z),
            "blocked_l4_other": self.blocked_l4_other,
            "blocked_missing_z": self.blocked_missing_z,
            "placement_classes": dict(sorted(self.placement_classes.items())),
            "reference_sides": dict(sorted(self.reference_sides.items())),
            "by_formula": {k: dict(v) for k, v in sorted(self.by_formula.items())},
            "recent_limit": RECENT_LIMIT,
            "recent": list(self._recent),
            "placement_definition": "PROTOTYPE_LITERAL_HOT_AFTER_SUCCESSFUL_L4_TECHNICAL_CANON",
            "prototype_placement_literal": PLACEMENT,
            "hot_is_logical_class": True,
            "physical_temperature_claim": False,
            "priority_claim": False,
            "storage_tier_claim": False,
            "canonical_z_is_output_z_id": True,
            "creates_new_identity": False,
            "places_both_l4_reference_sides": True,
            "s1_aggregator_input": True,
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
