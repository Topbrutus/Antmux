from __future__ import annotations

import os
from collections import Counter, defaultdict, deque
from typing import Any

SCHEMA = "BRUTUS_S3_ROUTE_INDEX_V1"
RECENT_LIMIT = 37
VALID_S2_PREFIXES = (
    "LINEAGE_INDEXED_ROOT_",
    "LINEAGE_INDEXED_PARENT_",
)


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "1" if default else "0").strip().lower()
    return raw in {"1", "true", "yes", "on"}


class S3RouteIndexTelemetry:
    """Shadow-only index of observed Papillon routes downstream of S2.

    The Colonne 37 prototype stores a route signature at S3 and the prototype
    UI describes S3 as indexing Papillon paths. The live runtime already owns
    one exact Papillon144 shard function, exposed read-only by
    ``Papillon144.shard_index(formula_id, input_value)``. S3 v1 reuses that
    source of truth and combines it with the emitted branch_path:

        route_ref = P{papillon_shard:03d}|{branch_path}

    This is an index key only. S3 never chooses, applies, or changes a route.
    It does not infer hidden paths, rewrite Z identity, or absorb formula-index
    authority reserved for S4.
    """

    def __init__(self) -> None:
        self.enabled = _env_flag("BROTO_S3_ENABLED", False)
        self.observations = 0
        self.indexed = 0
        self.blocked_s2_other = 0
        self.blocked_missing_z = 0
        self.blocked_missing_path = 0
        self.blocked_missing_papillon = 0
        self.blocked_path_drift = 0

        self.route_counts: Counter[str] = Counter()
        self.shard_counts: Counter[int] = Counter()
        self.path_counts: Counter[str] = Counter()
        self.routes_by_z: dict[str, set[str]] = defaultdict(set)
        self.z_by_route: dict[str, set[str]] = defaultdict(set)
        self.shards_by_z: dict[str, set[int]] = defaultdict(set)
        self.paths_by_z: dict[str, set[str]] = defaultdict(set)
        self.reference_sides: Counter[str] = Counter()
        self.by_formula: dict[str, Counter[str]] = {}
        self._recent: deque[dict[str, Any]] = deque(maxlen=RECENT_LIMIT)

    def _record(self, formula_id: str, outcome: str) -> None:
        self.by_formula.setdefault(str(formula_id), Counter())[outcome] += 1

    @staticmethod
    def _valid_s2(outcome: str) -> bool:
        return any(outcome.startswith(prefix) for prefix in VALID_S2_PREFIXES)

    def observe(
        self,
        formula_id: str,
        source: Any,
        out: Any,
        s2_outcome: str,
        *,
        papillon: Any,
    ) -> str:
        if not self.enabled:
            return "DISABLED"

        self.observations += 1
        s2 = str(s2_outcome).upper()
        if not self._valid_s2(s2):
            self.blocked_s2_other += 1
            outcome = "BLOCKED_S2_OTHER"
            self._record(formula_id, outcome)
            self._recent.append({"formula_id": formula_id, "outcome": outcome, "s2_outcome": s2, "indexed": False})
            return outcome

        z_raw = getattr(out, "z_id", None)
        if not z_raw:
            self.blocked_missing_z += 1
            outcome = "BLOCKED_MISSING_Z_ID"
            self._record(formula_id, outcome)
            self._recent.append({"formula_id": formula_id, "outcome": outcome, "s2_outcome": s2, "indexed": False})
            return outcome

        source_path_raw = getattr(source, "branch_path", None)
        out_path_raw = getattr(out, "branch_path", None)
        if source_path_raw is None or out_path_raw is None or str(out_path_raw) == "":
            self.blocked_missing_path += 1
            outcome = "BLOCKED_MISSING_BRANCH_PATH"
            self._record(formula_id, outcome)
            self._recent.append({"formula_id": formula_id, "outcome": outcome, "s2_outcome": s2, "indexed": False})
            return outcome
        source_path = str(source_path_raw)
        branch_path = str(out_path_raw)
        if source_path != branch_path:
            self.blocked_path_drift += 1
            outcome = "BLOCKED_BRANCH_PATH_DRIFT"
            self._record(formula_id, outcome)
            self._recent.append({
                "formula_id": formula_id,
                "outcome": outcome,
                "s2_outcome": s2,
                "source_path": source_path,
                "output_path": branch_path,
                "indexed": False,
            })
            return outcome

        if papillon is None or not hasattr(papillon, "shard_index"):
            self.blocked_missing_papillon += 1
            outcome = "BLOCKED_MISSING_PAPILLON_INDEX"
            self._record(formula_id, outcome)
            self._recent.append({"formula_id": formula_id, "outcome": outcome, "s2_outcome": s2, "indexed": False})
            return outcome

        shard = int(papillon.shard_index(str(formula_id), int(getattr(source, "value"))))
        if not 0 <= shard < 144:
            raise ValueError("Papillon shard index out of bounds")

        z_id = str(z_raw)
        route_ref = f"P{shard:03d}|{branch_path}"
        self.route_counts[route_ref] += 1
        self.shard_counts[shard] += 1
        self.path_counts[branch_path] += 1
        self.routes_by_z[z_id].add(route_ref)
        self.z_by_route[route_ref].add(z_id)
        self.shards_by_z[z_id].add(shard)
        self.paths_by_z[z_id].add(branch_path)
        self.indexed += 1

        side = "AT_OR_ABOVE_REFERENCE" if s2.endswith("AT_OR_ABOVE_REFERENCE") else "BELOW_REFERENCE"
        self.reference_sides[side] += 1
        outcome = f"ROUTE_INDEXED_{side}"
        self._record(formula_id, outcome)
        self._recent.append({
            "formula_id": formula_id,
            "outcome": outcome,
            "s2_outcome": s2,
            "z_id": z_id,
            "branch_path": branch_path,
            "papillon_shard": shard,
            "route_ref": route_ref,
            "route_multiplicity": self.route_counts[route_ref],
            "routes_for_z": len(self.routes_by_z[z_id]),
            "indexed": True,
        })
        return outcome

    def status(self) -> dict[str, Any]:
        multi_route_z = sum(1 for routes in self.routes_by_z.values() if len(routes) > 1)
        multi_z_routes = sum(1 for zs in self.z_by_route.values() if len(zs) > 1)
        repeated_routes = sum(1 for n in self.route_counts.values() if n > 1)
        hottest = sorted(self.route_counts.items(), key=lambda row: (-row[1], row[0]))[:10]
        return {
            "schema": SCHEMA,
            "mode": SCHEMA,
            "enabled": self.enabled,
            "authority": "SHADOW_ONLY",
            "source_of_truth": "S2_INDEXED_Z_PLUS_EXACT_LIVE_PAPILLON144_SHARD_INDEX_PLUS_EMITTED_BRANCH_PATH",
            "observations": self.observations,
            "indexed": self.indexed,
            "blocked_s2_other": self.blocked_s2_other,
            "blocked_missing_z": self.blocked_missing_z,
            "blocked_missing_path": self.blocked_missing_path,
            "blocked_missing_papillon": self.blocked_missing_papillon,
            "blocked_path_drift": self.blocked_path_drift,
            "unique_routes": len(self.route_counts),
            "repeated_routes": repeated_routes,
            "max_route_multiplicity": max(self.route_counts.values(), default=0),
            "papillon_shards_touched": len(self.shard_counts),
            "unique_branch_paths": len(self.path_counts),
            "unique_z_indexed": len(self.routes_by_z),
            "multi_route_z": multi_route_z,
            "multi_z_routes": multi_z_routes,
            "max_routes_per_z": max((len(v) for v in self.routes_by_z.values()), default=0),
            "max_z_per_route": max((len(v) for v in self.z_by_route.values()), default=0),
            "hottest_routes": [{"route_ref": r, "observations": n} for r, n in hottest],
            "reference_sides": dict(sorted(self.reference_sides.items())),
            "by_formula": {k: dict(v) for k, v in sorted(self.by_formula.items())},
            "recent_limit": RECENT_LIMIT,
            "recent": list(self._recent),
            "route_definition": "EXACT_PAPILLON144_SHARD_PLUS_EXISTING_BRANCH_PATH",
            "prototype_measurement_route_signature": True,
            "indexes_papillon_paths": True,
            "uses_existing_papillon_shard_function": True,
            "creates_parallel_router": False,
            "chooses_route": False,
            "applies_route": False,
            "actual_routes_applied": 0,
            "infers_hidden_path": False,
            "z_identity_preserved": True,
            "lineage_mutated": False,
            "formula_index_authority": False,
            "s4_formula_index_input": True,
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
