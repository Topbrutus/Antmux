from __future__ import annotations

import hashlib
import os
from collections import Counter, OrderedDict, deque
from typing import Any

SCHEMA = "BRUTUS_T10_REPLAY_V1"
RECENT_LIMIT = 37
DEFAULT_MAX_KEYS = 32768
HARD_MAX_KEYS = 131072


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "1" if default else "0").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int, *, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)).strip())
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))


def _source_key(formula_id: str, source_value: Any) -> str:
    raw = f"{formula_id}\0{source_value}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:32]


def replay_merit(observation_count: int) -> int:
    """Reference replay merit from the Colonne 37 prototype.

    This is an advisory count only. T10 never executes or schedules the replays;
    T11 is responsible for resource-budget arbitration before any future action.
    """
    count = max(1, int(observation_count))
    if count <= 2:
        return 8
    if count <= 4:
        return 6
    if count <= 8:
        return 4
    if count <= 16:
        return 2
    return 1


class T10ReplayTelemetry:
    """Shadow-only replay-merit advisory downstream of T9.

    T10 answers one question: how many recalculations are merited for an
    otherwise admissible key? It does not execute replay, schedule work, or
    consume a T11 resource budget.

    Eligibility requires T8 PASS and a non-drift T9 outcome. The recommendation
    follows the reference Colonne 37 replay-merit ladder:
      observations 1-2 -> 8
      observations 3-4 -> 6
      observations 5-8 -> 4
      observations 9-16 -> 2
      observations >16 -> 1
    """

    def __init__(self, max_keys: int | None = None) -> None:
        self.enabled = _env_flag("BROTO_T10_ENABLED", False)
        configured = (
            _env_int(
                "BROTO_T10_MAX_KEYS",
                DEFAULT_MAX_KEYS,
                minimum=1,
                maximum=HARD_MAX_KEYS,
            )
            if max_keys is None
            else int(max_keys)
        )
        self.max_keys = max(1, min(HARD_MAX_KEYS, configured))

        self.observations = 0
        self.eligible_observations = 0
        self.blocked_t8_fail = 0
        self.blocked_t8_limited = 0
        self.blocked_t8_other = 0
        self.blocked_t9_drift = 0
        self.blocked_t9_other = 0
        self.evictions = 0

        self.by_formula: dict[str, Counter[str]] = {}
        self.recommendation_events: Counter[str] = Counter()
        self._counts: OrderedDict[str, int] = OrderedDict()
        self._recent: deque[dict[str, Any]] = deque(maxlen=RECENT_LIMIT)

    def _record_formula(self, formula_id: str, outcome: str) -> None:
        self.by_formula.setdefault(formula_id, Counter())[outcome] += 1

    def _blocked(
        self,
        formula_id: str,
        source: Any,
        *,
        outcome: str,
        t8_outcome: str,
        t9_outcome: str,
    ) -> str:
        self._record_formula(formula_id, outcome)
        self._recent.append({
            "formula_id": formula_id,
            "source_key": _source_key(formula_id, source.value),
            "outcome": outcome,
            "t8_outcome": str(t8_outcome).upper(),
            "t9_outcome": str(t9_outcome).upper(),
            "observation_count": 0,
            "recommended_replays": 0,
        })
        return outcome

    def observe(
        self,
        formula_id: str,
        source: Any,
        out: Any,
        t8_outcome: str,
        t9_outcome: str,
    ) -> str:
        if not self.enabled:
            return "DISABLED"

        self.observations += 1
        t8 = str(t8_outcome).upper()
        t9 = str(t9_outcome).upper()

        if t8 != "PASS":
            if t8 == "FAIL":
                self.blocked_t8_fail += 1
                outcome = "BLOCKED_T8_FAIL"
            elif t8 == "LIMITED":
                self.blocked_t8_limited += 1
                outcome = "BLOCKED_T8_LIMITED"
            else:
                self.blocked_t8_other += 1
                outcome = "BLOCKED_T8_OTHER"
            return self._blocked(
                formula_id,
                source,
                outcome=outcome,
                t8_outcome=t8,
                t9_outcome=t9,
            )

        if t9 == "DRIFT":
            self.blocked_t9_drift += 1
            return self._blocked(
                formula_id,
                source,
                outcome="BLOCKED_T9_DRIFT",
                t8_outcome=t8,
                t9_outcome=t9,
            )

        if t9 not in {"BASELINE", "STABLE_REPEAT"}:
            self.blocked_t9_other += 1
            return self._blocked(
                formula_id,
                source,
                outcome="BLOCKED_T9_OTHER",
                t8_outcome=t8,
                t9_outcome=t9,
            )

        self.eligible_observations += 1
        key = _source_key(formula_id, source.value)
        previous = self._counts.get(key)
        if previous is None:
            if len(self._counts) >= self.max_keys:
                self._counts.popitem(last=False)
                self.evictions += 1
            count = 1
            self._counts[key] = count
        else:
            count = previous + 1
            self._counts[key] = count
            self._counts.move_to_end(key)

        recommended = replay_merit(count)
        outcome = f"REPLAY_{recommended}"
        self.recommendation_events[str(recommended)] += 1
        self._record_formula(formula_id, outcome)
        self._recent.append({
            "formula_id": formula_id,
            "source_key": key,
            "outcome": outcome,
            "t8_outcome": t8,
            "t9_outcome": t9,
            "observation_count": count,
            "recommended_replays": recommended,
        })
        return outcome

    def status(self) -> dict[str, Any]:
        current_distribution: Counter[str] = Counter()
        current_total = 0
        for count in self._counts.values():
            merit = replay_merit(count)
            current_distribution[str(merit)] += 1
            current_total += merit

        return {
            "schema": SCHEMA,
            "mode": SCHEMA,
            "enabled": self.enabled,
            "authority": "SHADOW_ONLY",
            "source_of_truth": "T9_OUTCOME_CALLBACK",
            "observations": self.observations,
            "eligible_observations": self.eligible_observations,
            "blocked_t8_fail": self.blocked_t8_fail,
            "blocked_t8_limited": self.blocked_t8_limited,
            "blocked_t8_other": self.blocked_t8_other,
            "blocked_t9_drift": self.blocked_t9_drift,
            "blocked_t9_other": self.blocked_t9_other,
            "distinct_keys": len(self._counts),
            "key_capacity": self.max_keys,
            "evictions": self.evictions,
            "eviction_policy": "LRU",
            "recommendation_events": dict(sorted(self.recommendation_events.items())),
            "current_replay_merit_distribution": dict(sorted(current_distribution.items())),
            "current_replay_merit_total": current_total,
            "policy": {
                "1-2": 8,
                "3-4": 6,
                "5-8": 4,
                "9-16": 2,
                "17+": 1,
            },
            "by_formula": {k: dict(v) for k, v in sorted(self.by_formula.items())},
            "recent_limit": RECENT_LIMIT,
            "recent": list(self._recent),
            "requires_t8_pass": True,
            "requires_t9_non_drift": True,
            "executes_replay": False,
            "schedules_replay": False,
            "controls_budget": False,
            "t11_budget_required": True,
            "scientific_proof_claim": False,
            "validation_state_mutated": False,
            "controls_routing": False,
            "controls_scheduling": False,
            "controls_calculation": False,
            "compute_skips": 0,
            "value_mutated": False,
            "proof_promotion": False,
        }
