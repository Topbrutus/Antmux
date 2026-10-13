from __future__ import annotations

import os
import tempfile
from pathlib import Path

for name in (
    "BROTO_T8_ENABLED","BROTO_T9_ENABLED","BROTO_T10_ENABLED","BROTO_T11_ENABLED",
    "BROTO_T12_ENABLED","BROTO_L1_ENABLED","BROTO_L2_ENABLED","BROTO_L3_ENABLED",
    "BROTO_L4_ENABLED","BROTO_L5_ENABLED","BROTO_S1_ENABLED","BROTO_S2_ENABLED",
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
from brotoculateur.s2_lineage_index import S2LineageIndexTelemetry


def make_result(formula_id: str, value: int):
    registry = build_default_registry()
    formula = registry.get(formula_id)
    source = z_stamp_root(TracePacket(value))
    assert formula.is_applicable(source), (formula_id, value)
    out = z_stamp_child(formula.apply(source), source)
    return source, out


def test_repeated_direct_edge_multiplicity() -> None:
    source, out = make_result("DOUBLE", 11)
    t = S2LineageIndexTelemetry()
    for _ in range(3):
        assert t.observe("DOUBLE", source, out, "AGGREGATED_Z_AT_OR_ABOVE_REFERENCE") == "LINEAGE_INDEXED_PARENT_AT_OR_ABOVE_REFERENCE"
    s = t.status()
    assert s["indexed"] == 3
    assert s["direct_parent_edges"] == 1
    assert s["repeated_parent_edges"] == 1
    assert s["max_parent_edge_multiplicity"] == 3
    assert s["unique_child_z"] == 1 and s["unique_parent_z"] == 1 and s["unique_origin_z"] == 1
    assert s["multi_parent_child_z"] == 0 and s["multi_origin_child_z"] == 0
    print("S2_EDGE_MULTIPLICITY=PASS", out.z_parent_id, out.z_id, 3)


def test_same_child_can_have_observed_multiple_parents_without_merge() -> None:
    source_a, out_a = make_result("PLUS1", 10)       # 10 -> 11
    source_b, out_b = make_result("HALF_EVEN", 22)  # 22 -> 11
    assert out_a.z_id == out_b.z_id
    assert out_a.z_parent_id != out_b.z_parent_id
    assert out_a.z_origin_id != out_b.z_origin_id

    t = S2LineageIndexTelemetry()
    t.observe("PLUS1", source_a, out_a, "AGGREGATED_Z_BELOW_REFERENCE")
    t.observe("HALF_EVEN", source_b, out_b, "AGGREGATED_Z_AT_OR_ABOVE_REFERENCE")
    s = t.status()
    child = out_a.z_id
    assert t.parents_by_child[child] == {out_a.z_parent_id, out_b.z_parent_id}
    assert t.origins_by_child[child] == {out_a.z_origin_id, out_b.z_origin_id}
    assert s["unique_child_z"] == 1
    assert s["unique_parent_z"] == 2
    assert s["direct_parent_edges"] == 2
    assert s["multi_parent_child_z"] == 1
    assert s["multi_origin_child_z"] == 1
    print("S2_MULTI_PARENT_OBSERVED=PASS", child, sorted(t.parents_by_child[child]))


def test_root_is_indexed_without_invented_parent() -> None:
    root = z_stamp_root(TracePacket(343))
    t = S2LineageIndexTelemetry()
    outcome = t.observe("SEED", root, root, "AGGREGATED_Z_AT_OR_ABOVE_REFERENCE")
    s = t.status()
    assert outcome == "LINEAGE_INDEXED_ROOT_AT_OR_ABOVE_REFERENCE"
    assert s["indexed"] == 1 and s["root_observations"] == 1 and s["root_child_z"] == 1
    assert s["direct_parent_edges"] == 0 and s["unique_parent_z"] == 0
    assert s["origin_present_observations"] == 1 and s["unique_origin_z"] == 1
    assert t.parents_by_child[root.z_id] == set()
    print("S2_ROOT_NO_PARENT_INVENTION=PASS", root.z_id)


def test_s1_gate_and_missing_z() -> None:
    source, out = make_result("PLUS1", 10)
    t = S2LineageIndexTelemetry()
    assert t.observe("PLUS1", source, out, "BLOCKED_L5_OTHER") == "BLOCKED_S1_OTHER"
    raw = TracePacket(11)
    assert t.observe("PLUS1", source, raw, "AGGREGATED_Z_AT_OR_ABOVE_REFERENCE") == "BLOCKED_MISSING_Z_ID"
    s = t.status()
    assert s["indexed"] == 0 and s["blocked_s1_other"] == 1 and s["blocked_missing_z"] == 1
    print("S2_INPUT_GATES=PASS")


def test_no_transitive_inference_or_cross_index_authority() -> None:
    source_a, mid = make_result("PLUS1", 10)  # 10 -> 11
    registry = build_default_registry()
    f = registry.get("PLUS1")
    end = z_stamp_child(f.apply(mid), mid)     # 11 -> 12

    t = S2LineageIndexTelemetry()
    t.observe("PLUS1", source_a, mid, "AGGREGATED_Z_AT_OR_ABOVE_REFERENCE")
    t.observe("PLUS1", mid, end, "AGGREGATED_Z_AT_OR_ABOVE_REFERENCE")
    assert t.parents_by_child[end.z_id] == {mid.z_id}
    assert source_a.z_id not in t.parents_by_child[end.z_id]
    s = t.status()
    assert s["infers_transitive_ancestry"] is False
    assert s["route_index_authority"] is False and s["formula_index_authority"] is False
    assert s["creates_new_identity"] is False and s["proof_promotion"] is False
    print("S2_DIRECT_ONLY=PASS")


def test_dashboard_lockstep() -> None:
    with tempfile.TemporaryDirectory(prefix="brotos2-") as td:
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
            service.l2_threshold, service.l3_press, service.l4_canon,
            service.l5_placement, service.s1_aggregator, service.s2_lineage_index,
        ]
        before = [m.status()["observations"] for m in modules]
        for _ in range(17):
            source, out = make_result("DOUBLE", 11)
            service._observe_formula_result("DOUBLE", source, out)
        after = [m.status()["observations"] for m in modules]
        assert [a-b for a,b in zip(after,before)] == [17] * 12
        s = service.s2_lineage_index.status()
        assert s["indexed"] == 17 and s["blocked_s1_other"] == 0 and s["blocked_missing_z"] == 0
        assert s["direct_parent_observations"] == 17 and s["root_observations"] == 0
        assert s["direct_parent_edges"] == 1 and s["max_parent_edge_multiplicity"] == 17
        assert s["unique_child_z"] == 1 and s["unique_parent_z"] == 1 and s["unique_origin_z"] == 1
        assert s["reference_sides"] == {"AT_OR_ABOVE_REFERENCE": 16, "BELOW_REFERENCE": 1}
        print("S2_CALLBACK_LOCKSTEP=PASS", *after, s["direct_parent_edges"], s["max_parent_edge_multiplicity"])


if __name__ == "__main__":
    test_repeated_direct_edge_multiplicity()
    test_same_child_can_have_observed_multiple_parents_without_merge()
    test_root_is_indexed_without_invented_parent()
    test_s1_gate_and_missing_z()
    test_no_transitive_inference_or_cross_index_authority()
    test_dashboard_lockstep()
    print("S2_LINEAGE_INDEX=PASS")
