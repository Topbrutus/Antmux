from __future__ import annotations

import os, tempfile
from pathlib import Path

for name in (
    "BROTO_T8_ENABLED","BROTO_T9_ENABLED","BROTO_T10_ENABLED","BROTO_T11_ENABLED",
    "BROTO_T12_ENABLED","BROTO_L1_ENABLED","BROTO_L2_ENABLED","BROTO_L3_ENABLED",
    "BROTO_L4_ENABLED","BROTO_L5_ENABLED","BROTO_S1_ENABLED",
):
    os.environ[name] = "1"
os.environ["BROTO_L2_THRESHOLD"] = "75"
os.environ["BROTO_T11_CPU_SLOTS"] = "8"
os.environ["BROTO_T11_MEMORY_SLOTS"] = "8"
os.environ["BROTO_T11_STORAGE_SLOTS"] = "8"
os.environ["BROTO_T11_TIME_SLOTS"] = "8"

from brotoculateur.dashboard import DashboardService, build_default_registry
from brotoculateur.engine import TracePacket, z_stamp_child, z_stamp_root
from brotoculateur.orchestrator import ExperimentSpec
from brotoculateur.s1_aggregator import S1AggregatorTelemetry


def make_result(formula_id: str, value: int):
    registry = build_default_registry()
    formula = registry.get(formula_id)
    source = z_stamp_root(TracePacket(value))
    assert formula.is_applicable(source)
    out = z_stamp_child(formula.apply(source), source)
    return source, out


def test_repeated_same_z_aggregates_multiplicity() -> None:
    source, out = make_result("DOUBLE", 11)
    t = S1AggregatorTelemetry()
    outcomes = [
        t.observe("DOUBLE", source, out, "PLACED_HOT_BELOW_REFERENCE"),
        t.observe("DOUBLE", source, out, "PLACED_HOT_AT_OR_ABOVE_REFERENCE"),
        t.observe("DOUBLE", source, out, "PLACED_HOT_AT_OR_ABOVE_REFERENCE"),
    ]
    s = t.status()
    assert outcomes == [
        "AGGREGATED_Z_BELOW_REFERENCE",
        "AGGREGATED_Z_AT_OR_ABOVE_REFERENCE",
        "AGGREGATED_Z_AT_OR_ABOVE_REFERENCE",
    ]
    assert s["aggregated"] == 3
    assert s["unique_aggregate_z"] == 1
    assert s["repeated_aggregate_z"] == 1
    assert s["max_aggregate_count"] == 3
    assert s["aggregate_multiplicity_distribution"] == {"3": 1}
    assert s["recent"][-1]["aggregate_z"] == out.z_id
    assert s["recent"][-1]["aggregate_count"] == 3
    print("S1_REPEAT_MULTIPLICITY=PASS", out.z_id, 3)


def test_distinct_z_are_not_merged() -> None:
    s1, o1 = make_result("PLUS1", 10)
    s2, o2 = make_result("DOUBLE", 11)
    assert o1.z_id != o2.z_id
    t = S1AggregatorTelemetry()
    t.observe("PLUS1", s1, o1, "PLACED_HOT_AT_OR_ABOVE_REFERENCE")
    t.observe("DOUBLE", s2, o2, "PLACED_HOT_AT_OR_ABOVE_REFERENCE")
    s = t.status()
    assert s["aggregated"] == 2 and s["unique_aggregate_z"] == 2
    assert s["repeated_aggregate_z"] == 0 and s["max_aggregate_count"] == 1
    assert s["merges_distinct_z"] is False and s["creates_new_identity"] is False
    print("S1_NO_DISTINCT_Z_MERGE=PASS")


def test_invalid_l5_blocks() -> None:
    source, out = make_result("PLUS1", 10)
    t = S1AggregatorTelemetry()
    assert t.observe("PLUS1", source, out, "BLOCKED_L4_OTHER") == "BLOCKED_L5_OTHER"
    s = t.status()
    assert s["aggregated"] == 0 and s["blocked_l5_other"] == 1
    print("S1_L5_GATE=PASS")


def test_missing_z_blocks() -> None:
    t = S1AggregatorTelemetry()
    source = TracePacket(10); out = TracePacket(11)
    assert t.observe("PLUS1", source, out, "PLACED_HOT_AT_OR_ABOVE_REFERENCE") == "BLOCKED_MISSING_Z_ID"
    s = t.status()
    assert s["aggregated"] == 0 and s["blocked_missing_z"] == 1
    print("S1_MISSING_Z_GATE=PASS")


def test_no_false_authority() -> None:
    source, out = make_result("PLUS1", 10)
    t = S1AggregatorTelemetry(); t.observe("PLUS1", source, out, "PLACED_HOT_AT_OR_ABOVE_REFERENCE")
    s = t.status()
    assert s["aggregate_z_is_output_z_id"] is True
    assert s["aggregate_z_is_l5_canonical_z"] is True
    assert s["counts_multiplicity_only"] is True
    assert s["s2_lineage_index_input"] is True
    assert s["scientific_proof_claim"] is False
    assert s["validation_state_mutated"] is False and s["proof_promotion"] is False
    assert s["controls_routing"] is False and s["controls_scheduling"] is False and s["controls_calculation"] is False
    print("S1_NO_FALSE_AUTHORITY=PASS")


def test_dashboard_lockstep() -> None:
    with tempfile.TemporaryDirectory(prefix="brotos1-") as td:
        service = DashboardService(
            Path(td) / "instance",
            spec=ExperimentSpec(duration_seconds=60, checkpoint_seconds=60, max_depth=4, max_active_branches=16, max_packets=100),
            checkpoint_seconds=60,
            tick_seconds=0.01,
            sleeping_pool_enabled=False,
        )
        modules = [
            service.t8_countertest, service.t9_stability, service.t10_replay,
            service.t11_budget, service.t12_candidate, service.l1_crystal_score,
            service.l2_threshold, service.l3_press, service.l4_canon, service.l5_placement,
            service.s1_aggregator,
        ]
        before = [m.status()["observations"] for m in modules]
        for _ in range(17):
            source, out = make_result("DOUBLE", 11)
            service._observe_formula_result("DOUBLE", source, out)
        after = [m.status()["observations"] for m in modules]
        assert [a-b for a,b in zip(after,before)] == [17] * 11
        s = service.s1_aggregator.status()
        assert s["aggregated"] == 17 and s["blocked_l5_other"] == 0 and s["blocked_missing_z"] == 0
        assert s["unique_aggregate_z"] == 1 and s["repeated_aggregate_z"] == 1 and s["max_aggregate_count"] == 17
        assert s["aggregate_multiplicity_distribution"] == {"17": 1}
        assert s["reference_sides"] == {"AT_OR_ABOVE_REFERENCE": 16, "BELOW_REFERENCE": 1}
        print("S1_CALLBACK_LOCKSTEP=PASS", *after, s["reference_sides"], s["unique_aggregate_z"], s["max_aggregate_count"])


if __name__ == "__main__":
    test_repeated_same_z_aggregates_multiplicity()
    test_distinct_z_are_not_merged()
    test_invalid_l5_blocks()
    test_missing_z_blocks()
    test_no_false_authority()
    test_dashboard_lockstep()
    print("S1_AGGREGATOR=PASS")
