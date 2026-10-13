from __future__ import annotations

from collections import deque
from typing import Any

SCHEMA = "BRUTUS_T7_CALCULATION_TELEMETRY_V1"
RECENT_LIMIT = 37


class T7CalculationTelemetry:
    """Shadow-only accounting of logical versus physically executed calculation work.

    One T7 observation corresponds to one packet that actually enters ExperimentRunner.step().
    T7 never chooses formulas, routes, cache policy, priorities, or proof state.
    """

    def __init__(self) -> None:
        self.packet_observations = 0
        self.logical_formula_attempts = 0
        self.native_attempts = 0
        self.native_predicate_calls = 0
        self.native_formula_calls = 0
        self.papillon_evaluations = 0
        self.papillon_direct_evaluations = 0
        self.papillon_cacheable_evaluations = 0
        self.papillon_cache_hits = 0
        self.papillon_cache_misses = 0
        self.papillon_predicate_calls = 0
        self.papillon_formula_calls = 0
        self.outputs_emitted = 0
        self.accounting_conflicts = 0
        self.negative_delta_conflicts = 0
        self._recent: deque[dict[str, Any]] = deque(maxlen=RECENT_LIMIT)

    @staticmethod
    def _delta(before: dict[str, int], after: dict[str, int], key: str) -> int:
        return int(after.get(key, 0)) - int(before.get(key, 0))

    def observe_packet(
        self,
        *,
        packet_value: int,
        logical_formula_attempts: int,
        native_attempts: int,
        native_predicate_calls: int,
        native_formula_calls: int,
        papillon_before: dict[str, int],
        papillon_after: dict[str, int],
        outputs_emitted: int,
    ) -> None:
        keys = (
            "evaluations",
            "direct_evaluations",
            "cacheable_evaluations",
            "cache_hits",
            "cache_misses",
            "predicate_calls",
            "formula_calls",
        )
        deltas = {key: self._delta(papillon_before, papillon_after, key) for key in keys}
        if any(value < 0 for value in deltas.values()):
            self.negative_delta_conflicts += 1
            return

        logical = int(logical_formula_attempts)
        native_attempts = int(native_attempts)
        pap_eval = deltas["evaluations"]
        if logical != native_attempts + pap_eval:
            self.accounting_conflicts += 1

        self.packet_observations += 1
        self.logical_formula_attempts += logical
        self.native_attempts += native_attempts
        self.native_predicate_calls += int(native_predicate_calls)
        self.native_formula_calls += int(native_formula_calls)
        self.papillon_evaluations += pap_eval
        self.papillon_direct_evaluations += deltas["direct_evaluations"]
        self.papillon_cacheable_evaluations += deltas["cacheable_evaluations"]
        self.papillon_cache_hits += deltas["cache_hits"]
        self.papillon_cache_misses += deltas["cache_misses"]
        self.papillon_predicate_calls += deltas["predicate_calls"]
        self.papillon_formula_calls += deltas["formula_calls"]
        self.outputs_emitted += int(outputs_emitted)

        self._recent.append({
            "packet_value": str(int(packet_value)),
            "logical_formula_attempts": logical,
            "native_attempts": native_attempts,
            "papillon_evaluations": pap_eval,
            "papillon_cache_hits": deltas["cache_hits"],
            "papillon_cache_misses": deltas["cache_misses"],
            "physical_formula_calls": int(native_formula_calls) + deltas["formula_calls"],
            "outputs_emitted": int(outputs_emitted),
        })

    def status(self) -> dict[str, Any]:
        physical_formula_calls = self.native_formula_calls + self.papillon_formula_calls
        physical_predicate_calls = self.native_predicate_calls + self.papillon_predicate_calls
        logical_to_physical = (
            self.logical_formula_attempts / physical_formula_calls
            if physical_formula_calls else 0.0
        )
        cache_hit_rate = (
            self.papillon_cache_hits / self.papillon_cacheable_evaluations
            if self.papillon_cacheable_evaluations else 0.0
        )
        return {
            "schema": SCHEMA,
            "mode": SCHEMA,
            "authority": "SHADOW_ONLY",
            "unit": "PROCESSED_PACKET",
            "packet_observations": self.packet_observations,
            "logical_formula_attempts": self.logical_formula_attempts,
            "native_attempts": self.native_attempts,
            "native_predicate_calls": self.native_predicate_calls,
            "native_formula_calls": self.native_formula_calls,
            "papillon_evaluations": self.papillon_evaluations,
            "papillon_direct_evaluations": self.papillon_direct_evaluations,
            "papillon_cacheable_evaluations": self.papillon_cacheable_evaluations,
            "papillon_cache_hits": self.papillon_cache_hits,
            "papillon_cache_misses": self.papillon_cache_misses,
            "papillon_predicate_calls": self.papillon_predicate_calls,
            "papillon_formula_calls": self.papillon_formula_calls,
            "physical_formula_calls": physical_formula_calls,
            "physical_predicate_calls": physical_predicate_calls,
            "memo_hits_observed": self.papillon_cache_hits,
            "logical_to_physical_formula_ratio": round(logical_to_physical, 6),
            "papillon_cache_hit_rate": round(cache_hit_rate, 6),
            "outputs_emitted": self.outputs_emitted,
            "accounting_conflicts": self.accounting_conflicts,
            "negative_delta_conflicts": self.negative_delta_conflicts,
            "recent_limit": RECENT_LIMIT,
            "recent": list(self._recent),
            "timing_claim": False,
            "performance_speedup_claim": False,
            "controls_formula_selection": False,
            "controls_papillon": False,
            "controls_routing": False,
            "controls_scheduling": False,
            "compute_skips": 0,
            "value_mutated": False,
            "proof_promotion": False,
            "persistent": False,
        }
