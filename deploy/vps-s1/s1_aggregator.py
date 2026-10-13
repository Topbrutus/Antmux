from __future__ import annotations

import os
from collections import Counter, deque
from typing import Any

SCHEMA = "BRUTUS_S1_AGGREGATOR_V1"
RECENT_LIMIT = 37
VALID_L5 = frozenset({
    "PLACED_HOT_AT_OR_ABOVE_REFERENCE",
    "PLACED_HOT_BELOW_REFERENCE",
})


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "1" if default else "0").strip().lower()
    return raw in {"1", "true", "yes", "on"}


class S1AggregatorTelemetry:
    """Shadow-only Z-identity aggregator downstream of L5 Placement.

    The Colonne 37 prototype represented S1_AGGREGATOR as
    ``aggregate_z = z_stamp.z_id``. S1 v1 therefore groups repeated successful
    L5 HOT placements by the already-existing output Z identity. Different Z
    identities are never merged together.

    Aggregation here means counting multiplicity for one stable Z identity. It
    does not create a new identity, change value, score, threshold, placement,
    validation state, or scientific proof status.
    """

    def __init__(self) -> None:
        self.enabled = _env_flag("BROTO_S1_ENABLED", False)
        self.observations = 0
        self.aggregated = 0
        self.blocked_l5_other = 0
        self.blocked_missing_z = 0
        self.aggregate_counts: Counter[str] = Counter()
        self.reference_sides: Counter[str] = Counter()
        self.by_formula: dict[str, Counter[str]] = {}
        self._recent: deque[dict[str, Any]] = deque(maxlen=RECENT_LIMIT)

    def _record(self, formula_id: str, outcome: str) -> None:
        self.by_formula.setdefault(formula_id, Counter())[outcome] += 1

    def observe(self, formula_id: str, source: Any, out: Any, l5_outcome: str) -> str:
        if not self.enabled:
            return "DISABLED"

        self.observations += 1
        l5 = str(l5_outcome).upper()
        if l5 not in VALID_L5:
            self.blocked_l5_other += 1
            outcome = "BLOCKED_L5_OTHER"
            self._record(formula_id, outcome)
            self._recent.append({
                "formula_id": formula_id,
                "outcome": outcome,
                "l5_outcome": l5,
                "aggregate_z": None,
                "aggregate_count": 0,
                "aggregated": False,
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
                "l5_outcome": l5,
                "aggregate_z": None,
                "aggregate_count": 0,
                "aggregated": False,
            })
            return outcome

        aggregate_z = str(z_id)
        self.aggregate_counts[aggregate_z] += 1
        aggregate_count = self.aggregate_counts[aggregate_z]
        self.aggregated += 1

        if l5 == "PLACED_HOT_AT_OR_ABOVE_REFERENCE":
            side = "AT_OR_ABOVE_REFERENCE"
            outcome = "AGGREGATED_Z_AT_OR_ABOVE_REFERENCE"
        else:
            side = "BELOW_REFERENCE"
            outcome = "AGGREGATED_Z_BELOW_REFERENCE"
        self.reference_sides[side] += 1
        self._record(formula_id, outcome)
        self._recent.append({
            "formula_id": formula_id,
            "outcome": outcome,
            "l5_outcome": l5,
            "reference_side": side,
            "placement": "HOT",
            "aggregate_z": aggregate_z,
            "aggregate_count": aggregate_count,
            "source_z_id": getattr(source, "z_id", None),
            "output_z_id": z_id,
            "aggregated": True,
        })
        return outcome

    def status(self) -> dict[str, Any]:
        multiplicities = Counter(self.aggregate_counts.values())
        max_count = max(self.aggregate_counts.values(), default=0)
        repeated_z = sum(1 for count in self.aggregate_counts.values() if count > 1)
        return {
            "schema": SCHEMA,
            "mode": SCHEMA,
            "enabled": self.enabled,
            "authority": "SHADOW_ONLY",
            "source_of_truth": "L5_HOT_PLACEMENT_OUTCOME_PLUS_EXISTING_OUTPUT_Z_ID",
            "observations": self.observations,
            "aggregated": self.aggregated,
            "unique_aggregate_z": len(self.aggregate_counts),
            "repeated_aggregate_z": repeated_z,
            "max_aggregate_count": max_count,
            "aggregate_multiplicity_distribution": {
                str(k): v for k, v in sorted(multiplicities.items())
            },
            "blocked_l5_other": self.blocked_l5_other,
            "blocked_missing_z": self.blocked_missing_z,
            "reference_sides": dict(sorted(self.reference_sides.items())),
            "by_formula": {k: dict(v) for k, v in sorted(self.by_formula.items())},
            "recent_limit": RECENT_LIMIT,
            "recent": list(self._recent),
            "aggregation_definition": "GROUP_REPEATED_L5_HOT_PLACEMENTS_BY_EXISTING_OUTPUT_Z_ID",
            "aggregate_z_is_output_z_id": True,
            "aggregate_z_is_l5_canonical_z": True,
            "merges_distinct_z": False,
            "creates_new_identity": False,
            "counts_multiplicity_only": True,
            "preserves_hot_placement": True,
            "preserves_both_reference_sides": True,
            "s2_lineage_index_input": True,
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
