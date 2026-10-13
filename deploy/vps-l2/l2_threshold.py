from __future__ import annotations

import os
from collections import Counter, deque
from typing import Any

from .l1_crystal_score import engineering_score, score_components

SCHEMA = "BRUTUS_L2_THRESHOLD_V1"
RECENT_LIMIT = 37
DEFAULT_THRESHOLD = 75.0


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "1" if default else "0").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float, minimum: float, maximum: float) -> float:
    try:
        value = float(os.getenv(name, str(default)).strip())
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))


class L2ThresholdTelemetry:
    """Shadow-only engineering reference threshold downstream of L1.

    No official scientific threshold exists in the source. The default 75/100
    is a transparent engineering reference: three quarters of the normalized
    L1 scale. It is configurable, uncalibrated scientifically, and never means
    accepted/rejected/proven/canonical.
    """

    def __init__(self, threshold: float | None = None) -> None:
        self.enabled = _env_flag("BROTO_L2_ENABLED", False)
        self.threshold = (
            _env_float("BROTO_L2_THRESHOLD", DEFAULT_THRESHOLD, 0.0, 100.0)
            if threshold is None
            else max(0.0, min(100.0, float(threshold)))
        )
        self.observations = 0
        self.compared = 0
        self.at_or_above = 0
        self.below = 0
        self.blocked_l1_other = 0
        self.blocked_score_invalid = 0
        self.margin_sum = 0.0
        self.by_formula: dict[str, Counter[str]] = {}
        self._recent: deque[dict[str, Any]] = deque(maxlen=RECENT_LIMIT)

    def _record(self, formula_id: str, outcome: str) -> None:
        self.by_formula.setdefault(formula_id, Counter())[outcome] += 1

    def observe(
        self,
        formula_id: str,
        source: Any,
        out: Any,
        t8_outcome: str,
        t9_outcome: str,
        t10_outcome: str,
        t11_outcome: str,
        t12_outcome: str,
        l1_outcome: str,
    ) -> str:
        if not self.enabled:
            return "DISABLED"
        self.observations += 1
        if str(l1_outcome).upper() != "CRYSTAL_SCORE_RECORDED":
            self.blocked_l1_other += 1
            outcome = "BLOCKED_L1_OTHER"
            self._record(formula_id, outcome)
            self._recent.append({"formula_id": formula_id, "outcome": outcome, "score": None, "threshold": self.threshold})
            return outcome

        components = score_components(
            t8_outcome=t8_outcome,
            t9_outcome=t9_outcome,
            t10_outcome=t10_outcome,
            t11_outcome=t11_outcome,
        )
        if components is None:
            self.blocked_score_invalid += 1
            outcome = "BLOCKED_SCORE_INVALID"
            self._record(formula_id, outcome)
            self._recent.append({"formula_id": formula_id, "outcome": outcome, "score": None, "threshold": self.threshold})
            return outcome

        score = engineering_score(components)
        margin = round(score - self.threshold, 6)
        self.compared += 1
        self.margin_sum += margin
        if score >= self.threshold:
            self.at_or_above += 1
            outcome = "AT_OR_ABOVE_ENGINEERING_REFERENCE"
        else:
            self.below += 1
            outcome = "BELOW_ENGINEERING_REFERENCE"
        self._record(formula_id, outcome)
        self._recent.append({
            "formula_id": formula_id,
            "outcome": outcome,
            "score": score,
            "threshold": self.threshold,
            "margin": margin,
            "t12_outcome": str(t12_outcome).upper(),
        })
        return outcome

    def status(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "mode": SCHEMA,
            "enabled": self.enabled,
            "authority": "SHADOW_ONLY",
            "source_of_truth": "L1_ENGINEERING_SCORE_RECOMPUTED_FROM_SAME_COMPONENTS",
            "observations": self.observations,
            "compared": self.compared,
            "at_or_above_reference": self.at_or_above,
            "below_reference": self.below,
            "blocked_l1_other": self.blocked_l1_other,
            "blocked_score_invalid": self.blocked_score_invalid,
            "threshold": self.threshold,
            "threshold_range": [0.0, 100.0],
            "default_threshold": DEFAULT_THRESHOLD,
            "threshold_basis": "ENGINEERING_REFERENCE_THREE_QUARTERS_OF_NORMALIZED_L1_SCALE",
            "threshold_configurable": True,
            "threshold_scientifically_calibrated": False,
            "scientific_threshold_claim": False,
            "margin_average": None if self.compared == 0 else round(self.margin_sum / self.compared, 6),
            "by_formula": {k: dict(v) for k, v in sorted(self.by_formula.items())},
            "recent_limit": RECENT_LIMIT,
            "recent": list(self._recent),
            "l3_press_input": True,
            "accepts_candidate": False,
            "rejects_candidate": False,
            "scientific_proof_claim": False,
            "validation_state_mutated": False,
            "canonizes": False,
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
