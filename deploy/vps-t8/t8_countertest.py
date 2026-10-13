from __future__ import annotations

import os
from collections import Counter, deque
from math import isqrt
from typing import Any

from .engine import TracePacket, ValidationState, z_identity_for_value

SCHEMA = "BRUTUS_T8_COUNTERTEST_V1"
RECENT_LIMIT = 37
KNOWN_FORMULAS = frozenset({
    "PLUS1", "DOUBLE", "SQUARE", "HALF_EVEN", "DIGIT_SUM", "BIT_LENGTH",
    "PELL_N", "PELL_Q", "FACTOR_GAP_LOW_666", "FACTOR_GAP_HIGH_666",
})


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "1" if default else "0").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _mat_mul(a: tuple[tuple[int, int], tuple[int, int]], b: tuple[tuple[int, int], tuple[int, int]]) -> tuple[tuple[int, int], tuple[int, int]]:
    return (
        (a[0][0] * b[0][0] + a[0][1] * b[1][0], a[0][0] * b[0][1] + a[0][1] * b[1][1]),
        (a[1][0] * b[0][0] + a[1][1] * b[1][0], a[1][0] * b[0][1] + a[1][1] * b[1][1]),
    )


def _pell_independent(n: int) -> int:
    if n < 0:
        raise ValueError("Pell index must be nonnegative")
    if n == 0:
        return 0
    result = ((1, 0), (0, 1))
    base = ((2, 1), (1, 0))
    power = n - 1
    while power:
        if power & 1:
            result = _mat_mul(result, base)
        base = _mat_mul(base, base)
        power >>= 1
    return result[0][0]


def _relation_check(formula_id: str, x: int, y: int) -> tuple[bool, bool, str]:
    if formula_id == "PLUS1":
        return True, y - x == 1, "y-x=1"
    if formula_id == "DOUBLE":
        return True, y % 2 == 0 and y // 2 == x, "y even and y/2=x"
    if formula_id == "SQUARE":
        r = isqrt(y) if y >= 0 else -1
        return True, y >= 0 and r * r == y and r == abs(x), "sqrt(y)=abs(x)"
    if formula_id == "HALF_EVEN":
        return True, x != 0 and x % 2 == 0 and y * 2 == x, "2y=x with x even"
    if formula_id == "DIGIT_SUM":
        expected = sum(int(ch) for ch in str(abs(x)))
        return True, y == expected, "decimal digit relation"
    if formula_id == "BIT_LENGTH":
        ax = abs(x)
        ok = y >= 1 and (1 << (y - 1)) <= ax < (1 << y)
        return True, ok, "2^(y-1)<=abs(x)<2^y"
    if formula_id == "PELL_N":
        return True, y == _pell_independent(x), "independent Pell matrix recurrence"
    if formula_id == "PELL_Q":
        p = _pell_independent(x)
        p2 = _pell_independent(x * x)
        ok = p != 0 and p2 % p == 0 and y == p2 // p
        return True, ok, "P(x^2)=y*P(x) via independent matrix recurrence"
    if formula_id == "FACTOR_GAP_LOW_666":
        return True, y * (y + 666) == x, "y(y+666)=x"
    if formula_id == "FACTOR_GAP_HIGH_666":
        return True, y * (y - 666) == x, "y(y-666)=x"
    return False, False, "no independent relation registered"


class T8CountertestTelemetry:
    """Shadow-only counter-test telemetry for emitted formula results.

    It never mutates TracePacket, ValidationState, routing, scheduling, or proof state.
    Current known formulas use an independently expressed algebraic/recurrent relation.
    Unknown formulas are LIMITED rather than silently passed.
    """

    def __init__(self) -> None:
        self.enabled = _env_flag("BROTO_T8_ENABLED", False)
        self.observations = 0
        self.passed = 0
        self.failed = 0
        self.limited = 0
        self.lineage_failures = 0
        self.z_failures = 0
        self.state_failures = 0
        self.relation_failures = 0
        self.relation_passes = 0
        self.by_formula: dict[str, Counter[str]] = {}
        self.failure_checks: Counter[str] = Counter()
        self._recent: deque[dict[str, Any]] = deque(maxlen=RECENT_LIMIT)

    def observe(self, formula_id: str, source: TracePacket, out: TracePacket) -> str:
        if not self.enabled:
            return "DISABLED"
        self.observations += 1
        failures: list[str] = []

        lineage_ok = (
            out.parent_id == source.packet_id
            and out.depth == source.depth + 1
            and out.branch_path == source.branch_path
            and out.formula_chain == source.formula_chain + (formula_id,)
        )
        if not lineage_ok:
            self.lineage_failures += 1
            failures.append("LINEAGE")

        if source.z_id is None:
            z_ok = out.z_id is None and out.z_parent_id is None and out.z_origin_id is None
        else:
            z_ok = (
                out.z_id == z_identity_for_value(out.value)
                and out.z_parent_id == source.z_id
                and out.z_origin_id == (source.z_origin_id or source.z_id)
            )
        if not z_ok:
            self.z_failures += 1
            failures.append("Z_LINEAGE")

        known = formula_id in KNOWN_FORMULAS
        state_ok = (not known) or out.state == ValidationState.EXACT
        if not state_ok:
            self.state_failures += 1
            failures.append("VALIDATION_STATE")

        available, relation_ok, relation = _relation_check(formula_id, int(source.value), int(out.value))
        if available:
            if relation_ok:
                self.relation_passes += 1
            else:
                self.relation_failures += 1
                failures.append("RELATION")

        if failures:
            outcome = "FAIL"
            self.failed += 1
            self.failure_checks.update(failures)
        elif not available:
            outcome = "LIMITED"
            self.limited += 1
        else:
            outcome = "PASS"
            self.passed += 1

        bucket = self.by_formula.setdefault(formula_id, Counter())
        bucket[outcome] += 1
        self._recent.append({
            "formula_id": formula_id,
            "source_value": str(source.value),
            "output_value": str(out.value),
            "outcome": outcome,
            "relation": relation,
            "failures": list(failures),
        })
        return outcome

    def status(self) -> dict[str, Any]:
        covered = self.passed + self.failed
        coverage = covered / self.observations if self.observations else 0.0
        return {
            "schema": SCHEMA,
            "mode": SCHEMA,
            "enabled": self.enabled,
            "authority": "SHADOW_ONLY",
            "source_of_truth": "FORMULA_RESULT_CALLBACK",
            "observations": self.observations,
            "passed": self.passed,
            "failed": self.failed,
            "limited": self.limited,
            "countertest_coverage": round(coverage, 6),
            "lineage_failures": self.lineage_failures,
            "z_failures": self.z_failures,
            "state_failures": self.state_failures,
            "relation_failures": self.relation_failures,
            "relation_passes": self.relation_passes,
            "known_formula_count": len(KNOWN_FORMULAS),
            "by_formula": {k: dict(v) for k, v in sorted(self.by_formula.items())},
            "failure_checks": dict(self.failure_checks),
            "recent_limit": RECENT_LIMIT,
            "recent": list(self._recent),
            "independent_relation_where_available": True,
            "sets_countertested_state": False,
            "validation_state_mutated": False,
            "scientific_proof_claim": False,
            "controls_routing": False,
            "controls_scheduling": False,
            "controls_calculation": False,
            "compute_skips": 0,
            "value_mutated": False,
            "proof_promotion": False,
        }