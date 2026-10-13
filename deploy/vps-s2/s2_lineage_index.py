from __future__ import annotations

import os
from collections import Counter, defaultdict, deque
from typing import Any

SCHEMA = "BRUTUS_S2_LINEAGE_INDEX_V1"
RECENT_LIMIT = 37
VALID_S1 = frozenset({
    "AGGREGATED_Z_AT_OR_ABOVE_REFERENCE",
    "AGGREGATED_Z_BELOW_REFERENCE",
})


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "1" if default else "0").strip().lower()
    return raw in {"1", "true", "yes", "on"}


class S2LineageIndexTelemetry:
    """Shadow-only direct Z-lineage index downstream of S1 Aggregator.

    The Colonne 37 prototype represents S2_LINEAGE_INDEX by the observed
    ``parent_z`` field. The live Z-stamp also exposes ``z_origin_id``. S2 v1
    indexes only these already-emitted lineage references:

      child Z -> observed direct parent Z(s)
      parent Z -> observed direct child Z(s)
      child Z -> observed origin Z(s)

    It never invents transitive ancestry, rewrites identity, or treats lineage
    multiplicity as scientific proof.
    """

    def __init__(self) -> None:
        self.enabled = _env_flag("BROTO_S2_ENABLED", False)
        self.observations = 0
        self.indexed = 0
        self.blocked_s1_other = 0
        self.blocked_missing_z = 0
        self.direct_parent_observations = 0
        self.root_observations = 0
        self.origin_present_observations = 0
        self.origin_missing_observations = 0

        self.parents_by_child: dict[str, set[str]] = defaultdict(set)
        self.children_by_parent: dict[str, set[str]] = defaultdict(set)
        self.origins_by_child: dict[str, set[str]] = defaultdict(set)
        self.children_by_origin: dict[str, set[str]] = defaultdict(set)
        self.parent_edge_counts: Counter[tuple[str, str]] = Counter()
        self.root_counts: Counter[str] = Counter()
        self.reference_sides: Counter[str] = Counter()
        self.by_formula: dict[str, Counter[str]] = {}
        self._recent: deque[dict[str, Any]] = deque(maxlen=RECENT_LIMIT)

    def _record(self, formula_id: str, outcome: str) -> None:
        self.by_formula.setdefault(formula_id, Counter())[outcome] += 1

    def observe(self, formula_id: str, source: Any, out: Any, s1_outcome: str) -> str:
        if not self.enabled:
            return "DISABLED"

        self.observations += 1
        s1 = str(s1_outcome).upper()
        if s1 not in VALID_S1:
            self.blocked_s1_other += 1
            outcome = "BLOCKED_S1_OTHER"
            self._record(formula_id, outcome)
            self._recent.append({
                "formula_id": formula_id,
                "outcome": outcome,
                "s1_outcome": s1,
                "child_z": None,
                "parent_z": None,
                "origin_z": None,
                "indexed": False,
            })
            return outcome

        child_raw = getattr(out, "z_id", None)
        if not child_raw:
            self.blocked_missing_z += 1
            outcome = "BLOCKED_MISSING_Z_ID"
            self._record(formula_id, outcome)
            self._recent.append({
                "formula_id": formula_id,
                "outcome": outcome,
                "s1_outcome": s1,
                "child_z": None,
                "parent_z": None,
                "origin_z": None,
                "indexed": False,
            })
            return outcome

        child_z = str(child_raw)
        parent_raw = getattr(out, "z_parent_id", None)
        origin_raw = getattr(out, "z_origin_id", None)
        parent_z = str(parent_raw) if parent_raw else None
        origin_z = str(origin_raw) if origin_raw else None

        edge_multiplicity = 0
        parent_count_for_child = len(self.parents_by_child[child_z])
        child_count_for_parent = 0
        if parent_z is None:
            self.root_observations += 1
            self.root_counts[child_z] += 1
        else:
            self.direct_parent_observations += 1
            self.parents_by_child[child_z].add(parent_z)
            self.children_by_parent[parent_z].add(child_z)
            edge = (parent_z, child_z)
            self.parent_edge_counts[edge] += 1
            edge_multiplicity = self.parent_edge_counts[edge]
            parent_count_for_child = len(self.parents_by_child[child_z])
            child_count_for_parent = len(self.children_by_parent[parent_z])

        if origin_z is None:
            self.origin_missing_observations += 1
        else:
            self.origin_present_observations += 1
            self.origins_by_child[child_z].add(origin_z)
            self.children_by_origin[origin_z].add(child_z)

        self.indexed += 1
        if s1 == "AGGREGATED_Z_AT_OR_ABOVE_REFERENCE":
            side = "AT_OR_ABOVE_REFERENCE"
        else:
            side = "BELOW_REFERENCE"
        self.reference_sides[side] += 1

        if parent_z is None:
            outcome = f"LINEAGE_INDEXED_ROOT_{side}"
        else:
            outcome = f"LINEAGE_INDEXED_PARENT_{side}"
        self._record(formula_id, outcome)
        self._recent.append({
            "formula_id": formula_id,
            "outcome": outcome,
            "s1_outcome": s1,
            "reference_side": side,
            "aggregate_z": child_z,
            "child_z": child_z,
            "parent_z": parent_z,
            "origin_z": origin_z,
            "edge_multiplicity": edge_multiplicity,
            "parent_count_for_child": parent_count_for_child,
            "child_count_for_parent": child_count_for_parent,
            "origin_count_for_child": len(self.origins_by_child[child_z]),
            "indexed": True,
        })
        return outcome

    def status(self) -> dict[str, Any]:
        repeated_edges = sum(1 for count in self.parent_edge_counts.values() if count > 1)
        max_edge_multiplicity = max(self.parent_edge_counts.values(), default=0)
        multi_parent_children = sum(1 for parents in self.parents_by_child.values() if len(parents) > 1)
        multi_origin_children = sum(1 for origins in self.origins_by_child.values() if len(origins) > 1)
        all_children = set(self.parents_by_child) | set(self.origins_by_child) | set(self.root_counts)
        return {
            "schema": SCHEMA,
            "mode": SCHEMA,
            "enabled": self.enabled,
            "authority": "SHADOW_ONLY",
            "source_of_truth": "S1_AGGREGATED_Z_PLUS_EMITTED_Z_PARENT_AND_Z_ORIGIN_FIELDS",
            "observations": self.observations,
            "indexed": self.indexed,
            "blocked_s1_other": self.blocked_s1_other,
            "blocked_missing_z": self.blocked_missing_z,
            "direct_parent_observations": self.direct_parent_observations,
            "root_observations": self.root_observations,
            "origin_present_observations": self.origin_present_observations,
            "origin_missing_observations": self.origin_missing_observations,
            "unique_child_z": len(all_children),
            "unique_parent_z": len(self.children_by_parent),
            "unique_origin_z": len(self.children_by_origin),
            "direct_parent_edges": len(self.parent_edge_counts),
            "repeated_parent_edges": repeated_edges,
            "max_parent_edge_multiplicity": max_edge_multiplicity,
            "multi_parent_child_z": multi_parent_children,
            "multi_origin_child_z": multi_origin_children,
            "root_child_z": len(self.root_counts),
            "reference_sides": dict(sorted(self.reference_sides.items())),
            "by_formula": {k: dict(v) for k, v in sorted(self.by_formula.items())},
            "recent_limit": RECENT_LIMIT,
            "recent": list(self._recent),
            "lineage_definition": "DIRECT_OBSERVED_Z_PARENT_AND_ORIGIN_INDEX_ONLY",
            "prototype_measurement_parent_z": True,
            "indexes_direct_parent_only": True,
            "indexes_reverse_observed_children": True,
            "indexes_observed_origin": True,
            "infers_transitive_ancestry": False,
            "infers_missing_parent": False,
            "infers_missing_origin": False,
            "aggregate_z_identity_preserved": True,
            "creates_new_identity": False,
            "merges_distinct_z": False,
            "route_index_authority": False,
            "formula_index_authority": False,
            "s3_route_index_input": True,
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
