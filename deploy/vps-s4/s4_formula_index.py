from __future__ import annotations

import os
from collections import Counter, defaultdict, deque
from typing import Any

SCHEMA = "BRUTUS_S4_FORMULA_INDEX_V1"
RECENT_LIMIT = 37
VALID_S3 = frozenset({
    "ROUTE_INDEXED_AT_OR_ABOVE_REFERENCE",
    "ROUTE_INDEXED_BELOW_REFERENCE",
})


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "1" if default else "0").strip().lower()
    return raw in {"1", "true", "yes", "on"}


class S4FormulaIndexTelemetry:
    """Shadow-only index of existing results by exact formula id.

    The Colonne 37 prototype stores ``formula_id`` at S4 and the prototype UI
    describes S4 as indexing results by formula. S4 v1 therefore maps the
    callback's exact formula id to the already-existing output Z identity.

    It does not create, execute, select, rank, score, rewrite, or merge formulas.
    A single Z reached by different formulas remains one Z with several observed
    formula references. A single formula reaching several Z identities remains
    one formula key with several observed results.
    """

    def __init__(self) -> None:
        self.enabled = _env_flag("BROTO_S4_ENABLED", False)
        self.observations = 0
        self.indexed = 0
        self.blocked_s3_other = 0
        self.blocked_missing_formula = 0
        self.blocked_missing_z = 0
        self.blocked_formula_mismatch = 0

        self.formula_counts: Counter[str] = Counter()
        self.formula_result_counts: Counter[tuple[str, str]] = Counter()
        self.results_by_formula: dict[str, set[str]] = defaultdict(set)
        self.formulas_by_z: dict[str, set[str]] = defaultdict(set)
        self.reference_sides: Counter[str] = Counter()
        self.by_formula: dict[str, Counter[str]] = {}
        self._recent: deque[dict[str, Any]] = deque(maxlen=RECENT_LIMIT)

    def _record(self, formula_id: str, outcome: str) -> None:
        self.by_formula.setdefault(str(formula_id), Counter())[outcome] += 1

    @staticmethod
    def _terminal_formula(out: Any) -> str | None:
        chain = tuple(str(x) for x in (getattr(out, "formula_chain", ()) or ()))
        return chain[-1] if chain else None

    def observe(self, formula_id: str, source: Any, out: Any, s3_outcome: str) -> str:
        if not self.enabled:
            return "DISABLED"

        self.observations += 1
        s3 = str(s3_outcome).upper()
        formula = str(formula_id or "").strip()

        if s3 not in VALID_S3:
            self.blocked_s3_other += 1
            outcome = "BLOCKED_S3_OTHER"
            self._record(formula or "<MISSING>", outcome)
            self._recent.append({
                "formula_id": formula or None,
                "outcome": outcome,
                "s3_outcome": s3,
                "indexed": False,
            })
            return outcome

        if not formula:
            self.blocked_missing_formula += 1
            outcome = "BLOCKED_MISSING_FORMULA_ID"
            self._record("<MISSING>", outcome)
            self._recent.append({
                "formula_id": None,
                "outcome": outcome,
                "s3_outcome": s3,
                "indexed": False,
            })
            return outcome

        z_raw = getattr(out, "z_id", None)
        if not z_raw:
            self.blocked_missing_z += 1
            outcome = "BLOCKED_MISSING_Z_ID"
            self._record(formula, outcome)
            self._recent.append({
                "formula_id": formula,
                "outcome": outcome,
                "s3_outcome": s3,
                "indexed": False,
            })
            return outcome

        terminal = self._terminal_formula(out)
        if terminal != formula:
            self.blocked_formula_mismatch += 1
            outcome = "BLOCKED_FORMULA_CHAIN_MISMATCH"
            self._record(formula, outcome)
            self._recent.append({
                "formula_id": formula,
                "terminal_formula": terminal,
                "outcome": outcome,
                "s3_outcome": s3,
                "indexed": False,
            })
            return outcome

        z_id = str(z_raw)
        key = (formula, z_id)
        self.formula_counts[formula] += 1
        self.formula_result_counts[key] += 1
        self.results_by_formula[formula].add(z_id)
        self.formulas_by_z[z_id].add(formula)
        self.indexed += 1

        side = "AT_OR_ABOVE_REFERENCE" if s3.endswith("AT_OR_ABOVE_REFERENCE") else "BELOW_REFERENCE"
        self.reference_sides[side] += 1
        outcome = f"FORMULA_INDEXED_{side}"
        self._record(formula, outcome)
        self._recent.append({
            "formula_id": formula,
            "terminal_formula": terminal,
            "outcome": outcome,
            "s3_outcome": s3,
            "source_value": str(getattr(source, "value", "")),
            "output_value": str(getattr(out, "value", "")),
            "z_id": z_id,
            "formula_observations": self.formula_counts[formula],
            "formula_result_multiplicity": self.formula_result_counts[key],
            "results_for_formula": len(self.results_by_formula[formula]),
            "formulas_for_z": len(self.formulas_by_z[z_id]),
            "indexed": True,
        })
        return outcome

    def status(self) -> dict[str, Any]:
        repeated_pairs = sum(1 for n in self.formula_result_counts.values() if n > 1)
        multi_result_formulas = sum(1 for zs in self.results_by_formula.values() if len(zs) > 1)
        multi_formula_z = sum(1 for formulas in self.formulas_by_z.values() if len(formulas) > 1)
        hottest_formulas = sorted(self.formula_counts.items(), key=lambda row: (-row[1], row[0]))[:10]
        hottest_pairs = sorted(self.formula_result_counts.items(), key=lambda row: (-row[1], row[0]))[:10]
        return {
            "schema": SCHEMA,
            "mode": SCHEMA,
            "enabled": self.enabled,
            "authority": "SHADOW_ONLY",
            "source_of_truth": "S3_INDEXED_RESULT_PLUS_EXACT_CALLBACK_FORMULA_ID_PLUS_EXISTING_OUTPUT_Z_ID",
            "observations": self.observations,
            "indexed": self.indexed,
            "blocked_s3_other": self.blocked_s3_other,
            "blocked_missing_formula": self.blocked_missing_formula,
            "blocked_missing_z": self.blocked_missing_z,
            "blocked_formula_mismatch": self.blocked_formula_mismatch,
            "unique_formulas": len(self.results_by_formula),
            "unique_result_z": len(self.formulas_by_z),
            "unique_formula_result_pairs": len(self.formula_result_counts),
            "repeated_formula_result_pairs": repeated_pairs,
            "max_formula_observations": max(self.formula_counts.values(), default=0),
            "max_formula_result_multiplicity": max(self.formula_result_counts.values(), default=0),
            "multi_result_formulas": multi_result_formulas,
            "multi_formula_z": multi_formula_z,
            "max_results_per_formula": max((len(v) for v in self.results_by_formula.values()), default=0),
            "max_formulas_per_z": max((len(v) for v in self.formulas_by_z.values()), default=0),
            "hottest_formulas": [{"formula_id": f, "observations": n} for f, n in hottest_formulas],
            "hottest_formula_result_pairs": [
                {"formula_id": key[0], "z_id": key[1], "observations": n}
                for key, n in hottest_pairs
            ],
            "reference_sides": dict(sorted(self.reference_sides.items())),
            "by_formula": {k: dict(v) for k, v in sorted(self.by_formula.items())},
            "recent_limit": RECENT_LIMIT,
            "recent": list(self._recent),
            "index_definition": "EXACT_FORMULA_ID_TO_EXISTING_OUTPUT_Z_ID",
            "prototype_measurement_formula_id": True,
            "indexes_results_by_formula": True,
            "uses_callback_formula_id": True,
            "requires_formula_chain_terminal_match": True,
            "creates_formula": False,
            "executes_formula": False,
            "selects_formula": False,
            "ranks_formula": False,
            "assigns_formula_score": False,
            "merges_distinct_formulas": False,
            "formula_registry_mutated": False,
            "route_index_mutated": False,
            "z_identity_preserved": True,
            "s5_fast_index_input": True,
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
