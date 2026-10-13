from __future__ import annotations

import os
import re
from collections import Counter, deque
from typing import Any

SCHEMA = "BRUTUS_L1_CRYSTAL_SCORE_V1"
RECENT_LIMIT = 37
REPLAY_MAX = 8

_BUDGET_FULL_RE = re.compile(r"^BUDGET_FULL_(\d+)$")
_BUDGET_PARTIAL_RE = re.compile(r"^BUDGET_PARTIAL_(\d+)_OF_(\d+)$")
_BUDGET_ZERO_RE = re.compile(r"^BUDGET_ZERO_OF_(\d+)$")


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "1" if default else "0").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _replay_request(t10_outcome: str) -> int | None:
    outcome = str(t10_outcome).upper()
    if not outcome.startswith("REPLAY_"):
        return None
    try:
        value = int(outcome.rsplit("_", 1)[1])
    except ValueError:
        return None
    return value if value in {1, 2, 4, 6, 8} else None


def _budget_fraction(t11_outcome: str) -> float | None:
    outcome = str(t11_outcome).upper()
    m = _BUDGET_FULL_RE.match(outcome)
    if m:
        return 1.0
    m = _BUDGET_PARTIAL_RE.match(outcome)
    if m:
        advised, requested = map(int, m.groups())
        if requested <= 0 or advised < 0 or advised > requested:
            return None
        return advised / requested
    m = _BUDGET_ZERO_RE.match(outcome)
    if m:
        requested = int(m.group(1))
        return 0.0 if requested > 0 else None
    return None


def score_components(
    *,
    t8_outcome: str,
    t9_outcome: str,
    t10_outcome: str,
    t11_outcome: str,
) -> dict[str, float] | None:
    """Return the transparent L1 engineering-score components.

    This is deliberately an operational score, not a scientific score. It is
    only computed for a T8 PASS and recognized downstream outcomes.

    Components:
      countertest          PASS -> 1.0
      stability            BASELINE -> 0.5, STABLE_REPEAT -> 1.0
      replay_maturity      (8 - requested_replays) / 7
      budget_fulfillment   advised / requested

    The final score is 100 * the equal-weight mean of the four components.
    L2, not L1, owns any future threshold decision.
    """
    t8 = str(t8_outcome).upper()
    t9 = str(t9_outcome).upper()
    if t8 != "PASS":
        return None

    if t9 == "BASELINE":
        stability = 0.5
    elif t9 == "STABLE_REPEAT":
        stability = 1.0
    else:
        return None

    requested = _replay_request(t10_outcome)
    if requested is None:
        return None
    replay_maturity = (REPLAY_MAX - requested) / (REPLAY_MAX - 1)

    budget = _budget_fraction(t11_outcome)
    if budget is None:
        return None

    return {
        "countertest": 1.0,
        "stability": stability,
        "replay_maturity": replay_maturity,
        "budget_fulfillment": budget,
    }


def engineering_score(components: dict[str, float]) -> float:
    values = [
        float(components["countertest"]),
        float(components["stability"]),
        float(components["replay_maturity"]),
        float(components["budget_fulfillment"]),
    ]
    return round(100.0 * sum(values) / len(values), 6)


class L1CrystalScoreTelemetry:
    """Shadow-only, explainable engineering score downstream of T12.

    L1 does not decide acceptance. It assigns a transparent operational score
    to a technical T12 candidate and exposes every component. L2 Threshold is
    the next and only layer allowed to interpret that score against a threshold.
    """

    def __init__(self) -> None:
        self.enabled = _env_flag("BROTO_L1_ENABLED", False)
        self.observations = 0
        self.scored = 0
        self.blocked_t12_other = 0
        self.blocked_component_invalid = 0
        self.score_sum = 0.0
        self.score_min: float | None = None
        self.score_max: float | None = None
        self.component_sums: Counter[str] = Counter()
        self.by_formula: dict[str, Counter[str]] = {}
        self._recent: deque[dict[str, Any]] = deque(maxlen=RECENT_LIMIT)

    @staticmethod
    def _is_candidate(t12_outcome: str) -> bool:
        return str(t12_outcome).upper().startswith("CANDIDATE_RECORDED_")

    def _record_formula(self, formula_id: str, outcome: str) -> None:
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
    ) -> str:
        if not self.enabled:
            return "DISABLED"

        self.observations += 1
        if not self._is_candidate(t12_outcome):
            self.blocked_t12_other += 1
            outcome = "BLOCKED_T12_OTHER"
            self._record_formula(formula_id, outcome)
            self._recent.append({
                "formula_id": formula_id,
                "outcome": outcome,
                "score": None,
                "components": None,
                "t12_outcome": str(t12_outcome).upper(),
            })
            return outcome

        components = score_components(
            t8_outcome=t8_outcome,
            t9_outcome=t9_outcome,
            t10_outcome=t10_outcome,
            t11_outcome=t11_outcome,
        )
        if components is None:
            self.blocked_component_invalid += 1
            outcome = "BLOCKED_COMPONENT_INVALID"
            self._record_formula(formula_id, outcome)
            self._recent.append({
                "formula_id": formula_id,
                "outcome": outcome,
                "score": None,
                "components": None,
                "t12_outcome": str(t12_outcome).upper(),
            })
            return outcome

        score = engineering_score(components)
        self.scored += 1
        self.score_sum += score
        self.score_min = score if self.score_min is None else min(self.score_min, score)
        self.score_max = score if self.score_max is None else max(self.score_max, score)
        for key, value in components.items():
            self.component_sums[key] += value

        outcome = "CRYSTAL_SCORE_RECORDED"
        self._record_formula(formula_id, outcome)
        self._recent.append({
            "formula_id": formula_id,
            "outcome": outcome,
            "score": score,
            "components": components,
            "t8_outcome": str(t8_outcome).upper(),
            "t9_outcome": str(t9_outcome).upper(),
            "t10_outcome": str(t10_outcome).upper(),
            "t11_outcome": str(t11_outcome).upper(),
            "t12_outcome": str(t12_outcome).upper(),
        })
        return outcome

    def status(self) -> dict[str, Any]:
        average = None if self.scored == 0 else round(self.score_sum / self.scored, 6)
        component_averages = {
            key: round(value / self.scored, 6)
            for key, value in sorted(self.component_sums.items())
        } if self.scored else {}
        return {
            "schema": SCHEMA,
            "mode": SCHEMA,
            "enabled": self.enabled,
            "authority": "SHADOW_ONLY",
            "source_of_truth": "T12_CANDIDATE_CALLBACK_PLUS_UPSTREAM_OUTCOMES",
            "observations": self.observations,
            "scored": self.scored,
            "blocked_t12_other": self.blocked_t12_other,
            "blocked_component_invalid": self.blocked_component_invalid,
            "score_sum": round(self.score_sum, 6),
            "score_average": average,
            "score_min": self.score_min,
            "score_max": self.score_max,
            "score_range": [0.0, 100.0],
            "score_formula": "100 * mean(countertest, stability, replay_maturity, budget_fulfillment)",
            "score_weights": {
                "countertest": 0.25,
                "stability": 0.25,
                "replay_maturity": 0.25,
                "budget_fulfillment": 0.25,
            },
            "component_definitions": {
                "countertest": "T8 PASS -> 1.0",
                "stability": "T9 BASELINE -> 0.5; STABLE_REPEAT -> 1.0",
                "replay_maturity": "(8 - T10_requested_replays) / 7",
                "budget_fulfillment": "T11_advised_replays / T11_requested_replays",
            },
            "component_averages": component_averages,
            "by_formula": {k: dict(v) for k, v in sorted(self.by_formula.items())},
            "recent_limit": RECENT_LIMIT,
            "recent": list(self._recent),
            "engineering_score_only": True,
            "scientific_score_claim": False,
            "l2_threshold_input": True,
            "assigns_score": True,
            "applies_threshold": False,
            "threshold_value": None,
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
