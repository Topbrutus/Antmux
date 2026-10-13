from __future__ import annotations

import os
import tempfile
from dataclasses import replace
from pathlib import Path

os.environ["BROTO_T8_ENABLED"] = "1"
os.environ["BROTO_T9_ENABLED"] = "1"

from brotoculateur.dashboard import DashboardService, build_default_registry
from brotoculateur.engine import TracePacket, z_identity_for_value, z_stamp_child, z_stamp_root
from brotoculateur.orchestrator import ExperimentSpec
from brotoculateur.t9_stability import T9StabilityTelemetry


def make_result(formula_id: str, value: int):
    registry = build_default_registry()
    formula = registry.get(formula_id)
    source = z_stamp_root(TracePacket(value))
    assert formula.is_applicable(source), (formula_id, value)
    out = formula.apply(source)
    out = z_stamp_child(out, source)
    return source, out


def test_repeat_is_stable() -> None:
    t9 = T9StabilityTelemetry()
    outcomes = []
    for _ in range(5):
        source, out = make_result("PLUS1", 10)
        outcomes.append(t9.observe("PLUS1", source, out, "PASS"))
    s = t9.status()
    assert outcomes == ["BASELINE"] + ["STABLE_REPEAT"] * 4
    assert s["observations"] == 5
    assert s["eligible_pass_observations"] == 5
    assert s["baselines_created"] == 1
    assert s["repeat_observations"] == 4
    assert s["stable_repeats"] == 4
    assert s["drifts"] == 0
    assert s["stability_rate"] == 1.0
    print("T9_REPEAT_STABILITY=PASS", s["stability_rate"])


def test_semantic_drift_detected() -> None:
    t9 = T9StabilityTelemetry()
    source, out = make_result("PLUS1", 10)
    assert t9.observe("PLUS1", source, out, "PASS") == "BASELINE"
    bad_value = out.value + 1
    drift = replace(out, value=bad_value, z_id=z_identity_for_value(bad_value))
    outcome = t9.observe("PLUS1", source, drift, "PASS")
    s = t9.status()
    assert outcome == "DRIFT"
    assert s["repeat_observations"] == 1
    assert s["drifts"] == 1
    assert s["stable_repeats"] == 0
    assert s["recent"][-1]["drift_fields"] == ["OUTPUT_VALUE"]
    print("T9_DRIFT_DETECTED=PASS", s["recent"][-1])


def test_upstream_nonpass_is_ineligible() -> None:
    t9 = T9StabilityTelemetry()
    source, out = make_result("DOUBLE", 11)
    assert t9.observe("DOUBLE", source, out, "FAIL") == "UPSTREAM_FAIL"
    assert t9.observe("DOUBLE", source, out, "LIMITED") == "UPSTREAM_LIMITED"
    s = t9.status()
    assert s["eligible_pass_observations"] == 0
    assert s["distinct_baselines"] == 0
    assert s["upstream_fail"] == 1
    assert s["upstream_limited"] == 1
    print("T9_UPSTREAM_GATE=PASS")


def test_baselines_are_bounded() -> None:
    t9 = T9StabilityTelemetry(max_baselines=2)
    for value in (1, 2, 3):
        source, out = make_result("PLUS1", value)
        assert t9.observe("PLUS1", source, out, "PASS") == "BASELINE"
    s = t9.status()
    assert s["distinct_baselines"] == 2
    assert s["evictions"] == 1
    assert s["baseline_capacity"] == 2
    assert s["eviction_policy"] == "LRU"
    print("T9_BOUNDED_BASELINES=PASS", s["distinct_baselines"], s["evictions"], s["eviction_policy"])


def test_dashboard_callback_lockstep() -> None:
    with tempfile.TemporaryDirectory(prefix="brotot9-") as td:
        service = DashboardService(
            Path(td) / "instance",
            spec=ExperimentSpec(
                duration_seconds=60,
                checkpoint_seconds=60,
                max_depth=4,
                max_active_branches=16,
                max_packets=100,
            ),
            checkpoint_seconds=60,
            tick_seconds=0.01,
            sleeping_pool_enabled=False,
        )
        before_t8 = service.t8_countertest.status()["observations"]
        before_t9 = service.t9_stability.status()["observations"]

        source, out = make_result("DOUBLE", 11)
        service._observe_formula_result("DOUBLE", source, out)

        after_t8 = service.t8_countertest.status()["observations"]
        after_t9 = service.t9_stability.status()["observations"]
        assert after_t8 - before_t8 == 1
        assert after_t9 - before_t9 == 1
        assert service.t9_stability.status()["baselines_created"] >= 1

        source2, out2 = make_result("DOUBLE", 11)
        service._observe_formula_result("DOUBLE", source2, out2)
        s9 = service.t9_stability.status()
        assert s9["stable_repeats"] >= 1
        assert s9["drifts"] == 0
        print("T9_CALLBACK_LOCKSTEP=PASS", after_t8, after_t9, s9["stable_repeats"])


if __name__ == "__main__":
    test_repeat_is_stable()
    test_semantic_drift_detected()
    test_upstream_nonpass_is_ineligible()
    test_baselines_are_bounded()
    test_dashboard_callback_lockstep()
    print("T9_STABILITY=PASS")
