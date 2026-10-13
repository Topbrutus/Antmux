from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ["BROTO_T8_ENABLED"] = "1"
os.environ["BROTO_T9_ENABLED"] = "1"
os.environ["BROTO_T10_ENABLED"] = "1"

from brotoculateur.dashboard import DashboardService, build_default_registry
from brotoculateur.engine import TracePacket, z_stamp_child, z_stamp_root
from brotoculateur.orchestrator import ExperimentSpec
from brotoculateur.t10_replay import T10ReplayTelemetry, replay_merit


def make_result(formula_id: str, value: int):
    registry = build_default_registry()
    formula = registry.get(formula_id)
    source = z_stamp_root(TracePacket(value))
    assert formula.is_applicable(source), (formula_id, value)
    out = formula.apply(source)
    out = z_stamp_child(out, source)
    return source, out


def test_reference_policy_thresholds() -> None:
    expected = {
        1: 8,
        2: 8,
        3: 6,
        4: 6,
        5: 4,
        8: 4,
        9: 2,
        16: 2,
        17: 1,
        37: 1,
    }
    for count, merit in expected.items():
        assert replay_merit(count) == merit, (count, replay_merit(count), merit)

    t10 = T10ReplayTelemetry()
    outcomes = []
    for index in range(1, 18):
        source, out = make_result("PLUS1", 10)
        t9 = "BASELINE" if index == 1 else "STABLE_REPEAT"
        outcomes.append(t10.observe("PLUS1", source, out, "PASS", t9))

    assert outcomes[0:2] == ["REPLAY_8", "REPLAY_8"]
    assert outcomes[2:4] == ["REPLAY_6", "REPLAY_6"]
    assert outcomes[4:8] == ["REPLAY_4"] * 4
    assert outcomes[8:16] == ["REPLAY_2"] * 8
    assert outcomes[16] == "REPLAY_1"
    s = t10.status()
    assert s["eligible_observations"] == 17
    assert s["distinct_keys"] == 1
    assert s["current_replay_merit_distribution"] == {"1": 1}
    assert s["current_replay_merit_total"] == 1
    print("T10_REFERENCE_POLICY=PASS", s["policy"])


def test_t8_gate_blocks_replay_merit() -> None:
    t10 = T10ReplayTelemetry()
    source, out = make_result("DOUBLE", 11)
    assert t10.observe("DOUBLE", source, out, "FAIL", "UPSTREAM_FAIL") == "BLOCKED_T8_FAIL"
    assert t10.observe("DOUBLE", source, out, "LIMITED", "UPSTREAM_LIMITED") == "BLOCKED_T8_LIMITED"
    s = t10.status()
    assert s["eligible_observations"] == 0
    assert s["distinct_keys"] == 0
    assert s["blocked_t8_fail"] == 1
    assert s["blocked_t8_limited"] == 1
    print("T10_T8_GATE=PASS")


def test_t9_drift_blocks_replay_merit() -> None:
    t10 = T10ReplayTelemetry()
    source, out = make_result("PLUS1", 10)
    assert t10.observe("PLUS1", source, out, "PASS", "BASELINE") == "REPLAY_8"
    assert t10.observe("PLUS1", source, out, "PASS", "DRIFT") == "BLOCKED_T9_DRIFT"
    s = t10.status()
    assert s["eligible_observations"] == 1
    assert s["blocked_t9_drift"] == 1
    assert s["distinct_keys"] == 1
    assert s["current_replay_merit_total"] == 8
    print("T10_T9_DRIFT_GATE=PASS")


def test_keys_are_bounded_lru() -> None:
    t10 = T10ReplayTelemetry(max_keys=2)
    for value in (1, 2, 3):
        source, out = make_result("PLUS1", value)
        assert t10.observe("PLUS1", source, out, "PASS", "BASELINE") == "REPLAY_8"
    s = t10.status()
    assert s["distinct_keys"] == 2
    assert s["evictions"] == 1
    assert s["key_capacity"] == 2
    assert s["eviction_policy"] == "LRU"
    assert s["current_replay_merit_total"] == 16
    print("T10_BOUNDED_KEYS=PASS", s["distinct_keys"], s["evictions"], s["eviction_policy"])


def test_dashboard_callback_lockstep_and_no_execution() -> None:
    with tempfile.TemporaryDirectory(prefix="brotot10-") as td:
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

        for _ in range(17):
            source, out = make_result("DOUBLE", 11)
            service._observe_formula_result("DOUBLE", source, out)

        s8 = service.t8_countertest.status()
        s9 = service.t9_stability.status()
        s10 = service.t10_replay.status()
        assert s8["observations"] - before_t8 == 17
        assert s9["observations"] - before_t9 == 17
        assert s10["observations"] - before_t10 == 17
        assert s8["failed"] == 0
        assert s8["limited"] == 0
        assert s9["drifts"] == 0
        assert s9["stable_repeats"] >= 16
        assert s10["recent"][-1]["recommended_replays"] == 1
        assert s10["executes_replay"] is False
        assert s10["schedules_replay"] is False
        assert s10["controls_budget"] is False
        assert s10["t11_budget_required"] is True
        assert s10["proof_promotion"] is False
        print(
            "T10_CALLBACK_LOCKSTEP=PASS",
            s8["observations"],
            s9["observations"],
            s10["observations"],
            s10["recent"][-1]["recommended_replays"],
        )


if __name__ == "__main__":
    test_reference_policy_thresholds()
    test_t8_gate_blocks_replay_merit()
    test_t9_drift_blocks_replay_merit()
    test_keys_are_bounded_lru()
    test_dashboard_callback_lockstep_and_no_execution()
    print("T10_REPLAY=PASS")
