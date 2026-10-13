from __future__ import annotations

import os, tempfile
from pathlib import Path

for name in (
    "BROTO_T8_ENABLED","BROTO_T9_ENABLED","BROTO_T10_ENABLED","BROTO_T11_ENABLED",
    "BROTO_T12_ENABLED","BROTO_L1_ENABLED","BROTO_L2_ENABLED","BROTO_L3_ENABLED",
    "BROTO_L4_ENABLED","BROTO_L5_ENABLED",
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
from brotoculateur.l5_placement import L5PlacementTelemetry


def make_result(formula_id: str, value: int):
    registry = build_default_registry()
    formula = registry.get(formula_id)
    source = z_stamp_root(TracePacket(value))
    assert formula.is_applicable(source)
    out = z_stamp_child(formula.apply(source), source)
    return source, out


def test_hot_literal_and_identity() -> None:
    source, out = make_result("DOUBLE", 11)
    t = L5PlacementTelemetry()
    a = t.observe("DOUBLE", source, out, "CANONICAL_Z_RECORDED_BELOW_REFERENCE")
    b = t.observe("DOUBLE", source, out, "CANONICAL_Z_RECORDED_AT_OR_ABOVE_REFERENCE")
    s = t.status()
    assert a == "PLACED_HOT_BELOW_REFERENCE"
    assert b == "PLACED_HOT_AT_OR_ABOVE_REFERENCE"
    assert s["placed"] == 2 and s["unique_placed_z"] == 1
    assert s["placement_classes"] == {"HOT": 2}
    assert all(r["placement"] == "HOT" and r["canonical_z"] == out.z_id for r in s["recent"])
    assert s["hot_is_logical_class"] is True
    print("L5_HOT_IDENTITY=PASS", out.z_id)


def test_invalid_l4_blocks() -> None:
    source, out = make_result("PLUS1", 10)
    t = L5PlacementTelemetry()
    assert t.observe("PLUS1", source, out, "BLOCKED_L3_OTHER") == "BLOCKED_L4_OTHER"
    s = t.status()
    assert s["placed"] == 0 and s["blocked_l4_other"] == 1
    print("L5_L4_GATE=PASS")


def test_missing_z_blocks() -> None:
    t = L5PlacementTelemetry()
    source = TracePacket(10); out = TracePacket(11)
    assert t.observe("PLUS1", source, out, "CANONICAL_Z_RECORDED_AT_OR_ABOVE_REFERENCE") == "BLOCKED_MISSING_Z_ID"
    s = t.status()
    assert s["placed"] == 0 and s["blocked_missing_z"] == 1
    print("L5_MISSING_Z_GATE=PASS")


def test_no_physical_or_scientific_claims() -> None:
    source, out = make_result("PLUS1", 10)
    t = L5PlacementTelemetry(); t.observe("PLUS1", source, out, "CANONICAL_Z_RECORDED_AT_OR_ABOVE_REFERENCE")
    s = t.status()
    assert s["prototype_placement_literal"] == "HOT"
    assert s["physical_temperature_claim"] is False
    assert s["priority_claim"] is False and s["storage_tier_claim"] is False
    assert s["creates_new_identity"] is False and s["s1_aggregator_input"] is True
    assert s["validation_state_mutated"] is False and s["proof_promotion"] is False
    print("L5_NO_FALSE_PLACEMENT_CLAIMS=PASS")


def test_dashboard_lockstep() -> None:
    with tempfile.TemporaryDirectory(prefix="brotol5-") as td:
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
        ]
        before = [m.status()["observations"] for m in modules]
        for _ in range(17):
            source, out = make_result("DOUBLE", 11)
            service._observe_formula_result("DOUBLE", source, out)
        after = [m.status()["observations"] for m in modules]
        assert [a-b for a,b in zip(after,before)] == [17] * 10
        s = service.l5_placement.status()
        assert s["placed"] == 17 and s["blocked_l4_other"] == 0 and s["blocked_missing_z"] == 0
        assert s["unique_placed_z"] == 1 and s["placement_classes"] == {"HOT": 17}
        assert s["reference_sides"] == {"AT_OR_ABOVE_REFERENCE": 16, "BELOW_REFERENCE": 1}
        print("L5_CALLBACK_LOCKSTEP=PASS", *after, s["reference_sides"], s["unique_placed_z"])


if __name__ == "__main__":
    test_hot_literal_and_identity()
    test_invalid_l4_blocks()
    test_missing_z_blocks()
    test_no_physical_or_scientific_claims()
    test_dashboard_lockstep()
    print("L5_PLACEMENT=PASS")
