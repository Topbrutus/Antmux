from __future__ import annotations

import os
import tempfile
from dataclasses import replace
from pathlib import Path

os.environ["BROTO_T8_ENABLED"] = "1"

from brotoculateur.dashboard import DashboardService, build_default_registry
from brotoculateur.engine import TracePacket, ValidationState, z_identity_for_value, z_stamp_child, z_stamp_root
from brotoculateur.orchestrator import ExperimentSpec
from brotoculateur.t8_countertest import T8CountertestTelemetry

SAMPLES = {
    "PLUS1": 10,
    "DOUBLE": 11,
    "SQUARE": -7,
    "HALF_EVEN": 20,
    "DIGIT_SUM": 1234,
    "BIT_LENGTH": 17,
    "PELL_N": 8,
    "PELL_Q": 5,
    "FACTOR_GAP_LOW_666": 3355,
    "FACTOR_GAP_HIGH_666": 3355,
}


def make_result(formula_id: str, value: int):
    registry = build_default_registry()
    formula = registry.get(formula_id)
    source = z_stamp_root(TracePacket(value))
    assert formula.is_applicable(source), (formula_id, value)
    out = formula.apply(source)
    out = z_stamp_child(out, source)
    return source, out


def test_all_current_formulas() -> None:
    t8 = T8CountertestTelemetry()
    for formula_id, value in SAMPLES.items():
        source, out = make_result(formula_id, value)
        outcome = t8.observe(formula_id, source, out)
        assert outcome == "PASS", (formula_id, t8.status()["recent"][-1])
    s = t8.status()
    assert s["observations"] == 10
    assert s["passed"] == 10 and s["failed"] == 0 and s["limited"] == 0
    assert s["relation_passes"] == 10 and s["countertest_coverage"] == 1.0
    assert s["known_formula_count"] == 10
    assert s["sets_countertested_state"] is False
    print("T8_ALL_FORMULAS=PASS", s["by_formula"])


def test_corruption_fails() -> None:
    t8 = T8CountertestTelemetry()
    source, out = make_result("PLUS1", 10)
    bad_value = out.value + 2
    bad = replace(out, value=bad_value, z_id=z_identity_for_value(bad_value))
    outcome = t8.observe("PLUS1", source, bad)
    s = t8.status()
    assert outcome == "FAIL"
    assert s["failed"] == 1 and s["relation_failures"] == 1
    assert s["failure_checks"].get("RELATION") == 1
    print("T8_CORRUPTION_DETECTED=PASS", s["failure_checks"])


def test_unknown_is_limited() -> None:
    t8 = T8CountertestTelemetry()
    source = z_stamp_root(TracePacket(7))
    value = 123
    out = TracePacket(
        value=value,
        parent_id=source.packet_id,
        branch_path=source.branch_path,
        depth=source.depth + 1,
        formula_chain=source.formula_chain + ("UNKNOWN_X",),
        state=ValidationState.EXACT,
        z_id=z_identity_for_value(value),
        z_parent_id=source.z_id,
        z_origin_id=source.z_origin_id,
    )
    outcome = t8.observe("UNKNOWN_X", source, out)
    s = t8.status()
    assert outcome == "LIMITED" and s["limited"] == 1 and s["failed"] == 0
    print("T8_UNKNOWN_LIMITED=PASS")


def test_dashboard_callback_lockstep() -> None:
    with tempfile.TemporaryDirectory(prefix="brotot8-") as td:
        service = DashboardService(
            Path(td) / "instance",
            spec=ExperimentSpec(duration_seconds=60, checkpoint_seconds=60, max_depth=4, max_active_branches=16, max_packets=100),
            checkpoint_seconds=60,
            tick_seconds=0.01,
            sleeping_pool_enabled=False,
        )
        before_b = service.brutomagique.status()["total_observations"]
        before_t = service.t8_countertest.status()["observations"]
        source, out = make_result("DOUBLE", 11)
        service._observe_formula_result("DOUBLE", source, out)
        after_b = service.brutomagique.status()["total_observations"]
        after_t = service.t8_countertest.status()["observations"]
        assert after_b - before_b == 1
        assert after_t - before_t == 1
        assert service.t8_countertest.status()["passed"] >= 1
        print("T8_CALLBACK_LOCKSTEP=PASS", after_b, after_t)


if __name__ == "__main__":
    test_all_current_formulas()
    test_corruption_fails()
    test_unknown_is_limited()
    test_dashboard_callback_lockstep()
    print("T8_COUNTERTEST=PASS")