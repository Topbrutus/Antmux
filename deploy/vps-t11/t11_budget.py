from __future__ import annotations

import hashlib
import os
from collections import Counter, deque
from typing import Any

SCHEMA = "BRUTUS_T11_BUDGET_V1"
RECENT_LIMIT = 37
MAX_REPLAY_SLOTS = 8
VALID_T10_REPLAY_OUTCOMES = frozenset({"REPLAY_1", "REPLAY_2", "REPLAY_4", "REPLAY_6", "REPLAY_8"})


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


def _parse_t10_request(t10_outcome: str) -> int | None:
    outcome = str(t10_outcome).upper()
    if outcome not in VALID_T10_REPLAY_OUTCOMES:
        return None
    return int(outcome.rsplit("_", 1)[1])


class T11BudgetTelemetry:
    """Shadow-only normalized budget arbitration downstream of T10.

    T11 consumes T10 replay-merit outcomes and intersects the requested replay
    count with four operator-configured *normalized policy slot* caps:
    CPU, memory, storage, and time.

    Version 1 deliberately does not pretend those slot counts are physical CPU
    cores, bytes, disk blocks, milliseconds, or measured replay costs. The
    default profile is neutral (8 slots on every axis), matching the maximum
    T10 request, so wiring T11 cannot silently reduce T10 by default.

    T11 never reserves resources, executes replay, schedules replay, mutates
    packets or validation state, or promotes proof. Its result is advisory input
    for T12 Candidate only. Physical calibration is explicitly false in v1.
    """

    def __init__(
        self,
        *,
        cpu_slots: int | None = None,
        memory_slots: int | None = None,
        storage_slots: int | None = None,
        time_slots: int | None = None,
    ) -> None:
        self.enabled = _env_flag("BROTO_T11_ENABLED", False)
        self.slots = {
            "cpu": _env_int("BROTO_T11_CPU_SLOTS", MAX_REPLAY_SLOTS, minimum=0, maximum=MAX_REPLAY_SLOTS)
            if cpu_slots is None
            else max(0, min(MAX_REPLAY_SLOTS, int(cpu_slots))),
            "memory": _env_int("BROTO_T11_MEMORY_SLOTS", MAX_REPLAY_SLOTS, minimum=0, maximum=MAX_REPLAY_SLOTS)
            if memory_slots is None
            else max(0, min(MAX_REPLAY_SLOTS, int(memory_slots))),
            "storage": _env_int("BROTO_T11_STORAGE_SLOTS", MAX_REPLAY_SLOTS, minimum=0, maximum=MAX_REPLAY_SLOTS)
            if storage_slots is None
            else max(0, min(MAX_REPLAY_SLOTS, int(storage_slots))),
            "time": _env_int("BROTO_T11_TIME_SLOTS", MAX_REPLAY_SLOTS, minimum=0, maximum=MAX_REPLAY_SLOTS)
            if time_slots is None
            else max(0, min(MAX_REPLAY_SLOTS, int(time_slots))),
        }

        self.observations = 0
        self.eligible_observations = 0
        self.blocked_t10_other = 0
        self.full_admissions = 0
        self.partial_admissions = 0
        self.zero_admissions = 0
        self.demand_total = 0
        self.advised_total = 0
        self.clipped_total = 0

        self.by_formula: dict[str, Counter[str]] = {}
        self.bottleneck_counts: Counter[str] = Counter()
        self.request_distribution: Counter[str] = Counter()
        self.advised_distribution: Counter[str] = Counter()
        self._recent: deque[dict[str, Any]] = deque(maxlen=RECENT_LIMIT)

    @property
    def normalized_capacity(self) -> int:
        return min(self.slots.values())

    def _record_formula(self, formula_id: str, outcome: str) -> None:
        self.by_formula.setdefault(formula_id, Counter())[outcome] += 1

    def observe(
        self,
        formula_id: str,
        source: Any,
        out: Any,
        t10_outcome: str,
    ) -> str:
        if not self.enabled:
            return "DISABLED"

        self.observations += 1
        requested = _parse_t10_request(t10_outcome)
        if requested is None:
            self.blocked_t10_other += 1
            outcome = "BLOCKED_T10_OTHER"
            self._record_formula(formula_id, outcome)
            self._recent.append({
                "formula_id": formula_id,
                "source_key": _source_key(formula_id, source.value),
                "t10_outcome": str(t10_outcome).upper(),
                "outcome": outcome,
                "requested_replays": 0,
                "advised_replays": 0,
                "bottlenecks": [],
            })
            return outcome

        self.eligible_observations += 1
        self.demand_total += requested
        self.request_distribution[str(requested)] += 1

        capacity = self.normalized_capacity
        advised = min(requested, capacity)
        clipped = requested - advised
        self.advised_total += advised
        self.clipped_total += clipped
        self.advised_distribution[str(advised)] += 1

        bottlenecks = sorted(axis for axis, slots in self.slots.items() if slots == capacity)
        self.bottleneck_counts.update(bottlenecks)

        if advised == requested:
            self.full_admissions += 1
            outcome = f"BUDGET_FULL_{advised}"
        elif advised == 0:
            self.zero_admissions += 1
            outcome = f"BUDGET_ZERO_OF_{requested}"
        else:
            self.partial_admissions += 1
            outcome = f"BUDGET_PARTIAL_{advised}_OF_{requested}"

        self._record_formula(formula_id, outcome)
        self._recent.append({
            "formula_id": formula_id,
            "source_key": _source_key(formula_id, source.value),
            "t10_outcome": str(t10_outcome).upper(),
            "outcome": outcome,
            "requested_replays": requested,
            "advised_replays": advised,
            "clipped_replays": clipped,
            "normalized_capacity": capacity,
            "bottlenecks": bottlenecks,
        })
        return outcome

    def status(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "mode": SCHEMA,
            "enabled": self.enabled,
            "authority": "SHADOW_ONLY",
            "source_of_truth": "T10_REPLAY_OUTCOME_CALLBACK",
            "observations": self.observations,
            "eligible_observations": self.eligible_observations,
            "blocked_t10_other": self.blocked_t10_other,
            "full_admissions": self.full_admissions,
            "partial_admissions": self.partial_admissions,
            "zero_admissions": self.zero_admissions,
            "demand_total": self.demand_total,
            "advised_total": self.advised_total,
            "clipped_total": self.clipped_total,
            "slot_caps": dict(self.slots),
            "normalized_capacity": self.normalized_capacity,
            "slot_cap_maximum": MAX_REPLAY_SLOTS,
            "slot_units": "NORMALIZED_REPLAY_POLICY_SLOTS",
            "physical_calibration": False,
            "physical_units_claimed": False,
            "neutral_default_profile": {
                "cpu": MAX_REPLAY_SLOTS,
                "memory": MAX_REPLAY_SLOTS,
                "storage": MAX_REPLAY_SLOTS,
                "time": MAX_REPLAY_SLOTS,
            },
            "bottleneck_counts": dict(sorted(self.bottleneck_counts.items())),
            "request_distribution": dict(sorted(self.request_distribution.items())),
            "advised_distribution": dict(sorted(self.advised_distribution.items())),
            "by_formula": {k: dict(v) for k, v in sorted(self.by_formula.items())},
            "recent_limit": RECENT_LIMIT,
            "recent": list(self._recent),
            "requires_t10_replay_merit": True,
            "candidate_advisory_only": True,
            "t12_candidate_input": True,
            "execution_eligible": False,
            "reserves_resources": False,
            "executes_replay": False,
            "schedules_replay": False,
            "scientific_proof_claim": False,
            "validation_state_mutated": False,
            "controls_routing": False,
            "controls_scheduling": False,
            "controls_calculation": False,
            "compute_skips": 0,
            "value_mutated": False,
            "proof_promotion": False,
        }
