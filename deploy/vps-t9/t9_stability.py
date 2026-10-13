from __future__ import annotations

import hashlib
import os
from collections import Counter, OrderedDict, deque
from typing import Any

SCHEMA = "BRUTUS_T9_STABILITY_V1"
RECENT_LIMIT = 37
DEFAULT_MAX_BASELINES = 32768
HARD_MAX_BASELINES = 131072


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "1" if default else "0").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int, *, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)).strip())
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))


def _state_name(value: Any) -> str:
    return str(getattr(value, "value", value))


def _source_key(formula_id: str, source_value: Any) -> str:
    raw = f"{formula_id}\0{source_value}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:32]


def _semantic_signature(out: Any) -> tuple[str, str]:
    return (str(out.value), _state_name(out.state))


class T9StabilityTelemetry:
    """Shadow-only repetition stability telemetry downstream of T8.

    T9 does not recalculate formulas. It accepts only T8 PASS observations as
    eligible stability samples, establishes one semantic baseline per
    (formula_id, source_value), and checks later repetitions for deterministic
    drift in output value or validation state.

    It never mutates packets, routing, scheduling, calculation, or proof state.
    """

    def __init__(self, max_baselines: int | None = None) -> None:
        self.enabled = _env_flag("BROTO_T9_ENABLED", False)
        configured = (
            _env_int(
                "BROTO_T9_MAX_BASELINES",
                DEFAULT_MAX_BASELINES,
                minimum=1,
                maximum=HARD_MAX_BASELINES,
            )
            if max_baselines is None
            else int(max_baselines)
        )
        self.max_baselines = max(1, min(HARD_MAX_BASELINES, configured))

        self.observations = 0
        self.eligible_pass_observations = 0
        self.upstream_fail = 0
        self.upstream_limited = 0
        self.upstream_other = 0

        self.baselines_created = 0
        self.repeat_observations = 0
        self.stable_repeats = 0
        self.drifts = 0
        self.evictions = 0

        self.by_formula: dict[str, Counter[str]] = {}
        self._baselines: OrderedDict[str, tuple[str, str]] = OrderedDict()
        self._recent: deque[dict[str, Any]] = deque(maxlen=RECENT_LIMIT)

    def _record_formula(self, formula_id: str, outcome: str) -> None:
        self.by_formula.setdefault(formula_id, Counter())[outcome] += 1

    def observe(self, formula_id: str, source: Any, out: Any, t8_outcome: str) -> str:
        if not self.enabled:
            return "DISABLED"

        self.observations += 1
        t8 = str(t8_outcome).upper()

        if t8 != "PASS":
            if t8 == "FAIL":
                self.upstream_fail += 1
                outcome = "UPSTREAM_FAIL"
            elif t8 == "LIMITED":
                self.upstream_limited += 1
                outcome = "UPSTREAM_LIMITED"
            else:
                self.upstream_other += 1
                outcome = "UPSTREAM_OTHER"

            self._record_formula(formula_id, outcome)
            self._recent.append({
                "formula_id": formula_id,
                "source_key": _source_key(formula_id, source.value),
                "outcome": outcome,
                "t8_outcome": t8,
                "drift_fields": [],
            })
            return outcome

        self.eligible_pass_observations += 1
        key = _source_key(formula_id, source.value)
        signature = _semantic_signature(out)
        previous = self._baselines.get(key)

        if previous is None:
            if len(self._baselines) >= self.max_baselines:
                self._baselines.popitem(last=False)
                self.evictions += 1
            self._baselines[key] = signature
            self.baselines_created += 1
            outcome = "BASELINE"
            drift_fields: list[str] = []
        else:
            self.repeat_observations += 1
            self._baselines.move_to_end(key)
            drift_fields = []
            if previous[0] != signature[0]:
                drift_fields.append("OUTPUT_VALUE")
            if previous[1] != signature[1]:
                drift_fields.append("VALIDATION_STATE")

            if drift_fields:
                self.drifts += 1
                outcome = "DRIFT"
            else:
                self.stable_repeats += 1
                outcome = "STABLE_REPEAT"

        self._record_formula(formula_id, outcome)
        self._recent.append({
            "formula_id": formula_id,
            "source_key": key,
            "outcome": outcome,
            "t8_outcome": t8,
            "drift_fields": drift_fields,
        })
        return outcome

    def status(self) -> dict[str, Any]:
        stability_rate = (
            self.stable_repeats / self.repeat_observations
            if self.repeat_observations
            else 0.0
        )
        return {
            "schema": SCHEMA,
            "mode": SCHEMA,
            "enabled": self.enabled,
            "authority": "SHADOW_ONLY",
            "source_of_truth": "T8_PASS_CALLBACK",
            "observations": self.observations,
            "eligible_pass_observations": self.eligible_pass_observations,
            "upstream_fail": self.upstream_fail,
            "upstream_limited": self.upstream_limited,
            "upstream_other": self.upstream_other,
            "baselines_created": self.baselines_created,
            "repeat_observations": self.repeat_observations,
            "stable_repeats": self.stable_repeats,
            "drifts": self.drifts,
            "stability_rate": round(stability_rate, 6),
            "distinct_baselines": len(self._baselines),
            "baseline_capacity": self.max_baselines,
            "evictions": self.evictions,
            "by_formula": {k: dict(v) for k, v in sorted(self.by_formula.items())},
            "recent_limit": RECENT_LIMIT,
            "recent": list(self._recent),
            "requires_t8_pass": True,
            "repeat_key": "formula_id+source_value",
            "semantic_signature": "output_value+validation_state",
            "scientific_proof_claim": False,
            "validation_state_mutated": False,
            "controls_routing": False,
            "controls_scheduling": False,
            "controls_calculation": False,
            "compute_skips": 0,
            "value_mutated": False,
            "proof_promotion": False,
        }
