from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ["BROTO_T8_ENABLED"] = "1"
os.environ["BROTO_T9_ENABLED"] = "1"
os.environ["BROTO_T10_ENABLED"] = "1"
os.environ["BROTO_T11_ENABLED"] = "1"
os.environ["BROTO_T11_CPU_SLOTS"] = "8"
os.environ["BROTO_T11_MEMORY_SLOTS"] = "8"
os.environ["BROTO_T11_STORAGE_SLOTS"] = "8"
os.environ["BROTO_T11_TIME_SLOTS"] = "8"

from brotoculateur.dashboard import DashboardService, build_default_registry
from brotoculateur.engine import TracePacket, z_stamp_child, z_stamp_root
from brotoculateur.orchestrator import ExperimentSpec
from brotoculateur.t11_budget import T11BudgetTelemetry


def make_result(formula_id: str, value: int):
    registry = build_default_registry()
    formula = registry.get(formula_id)
    source = z_stamp_root(TracePacket(value))
    assert formula.is_applicable(source), (formula_id, value)
    out = formula.apply(source)
    out = z_stamp_child(out, source)
    return source, out


def test_neutral_profile_preserves_t10_merit() -> None:
    t11 = T11BudgetTelemetry(cpu_slots=8, memory_slots=8, storage_slots=8, time_slots=8)
    expected = {
        "REPLAY_8": "BUDGET_FULL_8",
        "REPLAY_6": "BUDGET_FULL_6",
        "REPLAY_4": "BUDGET_FULL_4",
        "REPLAY_2": "BUDGET_FULL_2",
        "REPLAY_1": "BUDGET_FULL_1",
    }
    source, out = make_result("PLUS1", 10)
    for t10_outcome, budget_outcome in expected.items():
        assert t11.observe("PLUS1", source, out, t10_outcome) == budget_outcome
    s = t11.status()
    assert s["normalized_capacity"] == 8
    assert s["demand_total"] == 21
    assert s["advised_total"] == 21
    assert s["clipped_total"] == 0
    assert s["full_admissions"] == 5
    print("T11_NEUTRAL_PROFILE=PASS", s["slot_caps"])


def test_bottleneck_clips_without_execution() -> None:
    t11 = T11BudgetTelemetry(cpu_slots=6, memory_slots=4, storage_slots=2, time_slots=1)
    source, out = make_result("DOUBLE", 11)
    outcome = t11.observe("DOUBLE", source, out, "REPLAY_8")
    s = t11.status()
    assert outcome == "BUDGET_PARTIAL_1_OF_8"
    assert s["normalized_capacity"] == 1
    assert s["demand_total"] == 8
    assert s["advised_total"] == 1
    assert s["clipped_total"] == 7
    assert s["recent"][-1]["bottlenecks"] == ["time"]
    assert s["execution_eligible"] is False
    assert s["reserves_resources"] is False
    assert s["executes_replay"] is False
    assert s["schedules_replay"] is False
    print("T11_BOTTLENECK_CLIP=PASS", s["recent"][-1])


def test_zero_budget_blocks_advisory_count() -> None:
    t11 = T11BudgetTelemetry(cpu_slots=8, memory_slots=8, storage_slots=0, time_slots=8)
    source, out = make_result("PLUS1", 10)
    outcome = t11.observe("PLUS1", source, out, "REPLAY_4")
    s = t11.status()
    assert outcome == "BUDGET_ZERO_OF_4"
    assert s["normalized_capacity"] == 0
    assert s["advised_total"] == 0
    assert s["clipped_total"] == 4
    assert s["zero_admissions"] == 1
    assert s["recent"][-1]["bottlenecks"] == ["storage"]
    print("T11_ZERO_BUDGET=PASS")


def test_non_replay_t10_outcome_is_ineligible() -> None:
    t11 = T11BudgetTelemetry()
    source, out = make_result("PLUS1", 10)
    assert t11.observe("PLUS1", source, out, "BLOCKED_T9_DRIFT") == "BLOCKED_T10_OTHER"
    s = t11.status()
    assert s["eligible_observations"] == 0
    assert s["blocked_t10_other"] == 1
    assert s["demand_total"] == 0
    assert s["advised_total"] == 0
    print("T11_T10_GATE=PASS")


def test_slot_caps_are_bounded() -> None:
    t11 = T11BudgetTelemetry(cpu_slots=999, memory_slots=-1, storage_slots=9, time_slots=3)
    s = t11.status()
    assert s["slot_caps"] == {"cpu": 8, "memory": 0, "storage": 8, "time": 3}
    assert s["normalized_capacity"] == 0
    assert s["physical_calibration"] is False
    assert s["physical_units_claimed"] is False
    print("T11_SLOT_BOUNDS=PASS", s["slot_caps"])


def test_dashboard_callback_lockstep() -> None:
    with tempfile.TemporaryDirectory(prefix="brotot11-") as td:
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
        before_t10 = service.t10_replay.status()["observations"]
        before_t11 = service.t11_budget.status()["observations"]

        for _ in range(17):
            source, out = make_result("DOUBLE", 11)
            service._observe_formula_result("DOUBLE", source, out)

        s8 = service.t8_countertest.status()
        s9 = service.t9_stability.status()
        s10 = service.t10_replay.status()
        s11 = service.t11_budget.status()
        assert s8["observations"] - before_t8 == 17
        assert s9["observations"] - before_t9 == 17
        assert s10["observations"] - before_t10 == 17
        assert s11["observations"] - before_t11 == 17
        assert s8["failed"] == 0 and s8["limited"] == 0
        assert s9["drifts"] == 0
        assert s10["blocked_t8_fail"] == 0
        assert s10["blocked_t8_limited"] == 0
        assert s10["blocked_t9_drift"] == 0
        assert s11["blocked_t10_other"] == 0
        assert s11["demand_total"] == s11["advised_total"]
        assert s11["clipped_total"] == 0
        assert s11["physical_calibration"] is False
        assert s11["execution_eligible"] is False
        assert s11["candidate_advisory_only"] is True
        assert s11["t12_candidate_input"] is True
        assert s11["proof_promotion"] is False
        print(
            "T11_CALLBACK_LOCKSTEP=PASS",
            s8["observations"],
            s9["observations"],
            s10["observations"],
            s11["observations"],
            s11["demand_total"],
        )


if __name__ == "__main__":
    test_neutral_profile_preserves_t10_merit()
    test_bottleneck_clips_without_execution()
    test_zero_budget_blocks_advisory_count()
    test_non_replay_t10_outcome_is_ineligible()
    test_slot_caps_are_bounded()
    test_dashboard_callback_lockstep()
    print("T11_BUDGET=PASS")
