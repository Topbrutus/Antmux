from __future__ import annotations

import os
import tempfile
from dataclasses import replace
from pathlib import Path

for name in (
    "BROTO_T8_ENABLED","BROTO_T9_ENABLED","BROTO_T10_ENABLED","BROTO_T11_ENABLED",
    "BROTO_T12_ENABLED","BROTO_L1_ENABLED","BROTO_L2_ENABLED","BROTO_L3_ENABLED",
    "BROTO_L4_ENABLED","BROTO_L5_ENABLED","BROTO_S1_ENABLED","BROTO_S2_ENABLED","BROTO_S3_ENABLED",
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
from brotoculateur.papillon_engine import Papillon144
from brotoculateur.s3_route_index import S3RouteIndexTelemetry


def make_result(formula_id: str, value: int, branch_path: str = "ROOT"):
    registry = build_default_registry()
    formula = registry.get(formula_id)
    source = z_stamp_root(TracePacket(value, branch_path=branch_path))
    assert formula.is_applicable(source), (formula_id, value)
    out = z_stamp_child(formula.apply(source), source)
    return source, out


def test_exact_live_papillon_shard_and_repeat() -> None:
    pap = Papillon144()
    source, out = make_result("DOUBLE", 11, "ROOT/A")
    expected = pap.shard_index("DOUBLE", source.value)
    before = pap.status()
    t = S3RouteIndexTelemetry()
    for _ in range(3):
        got = t.observe("DOUBLE", source, out, "LINEAGE_INDEXED_PARENT_AT_OR_ABOVE_REFERENCE", papillon=pap)
        assert got == "ROUTE_INDEXED_AT_OR_ABOVE_REFERENCE"
    s = t.status()
    assert pap.status() == before
    assert s["indexed"] == 3 and s["unique_routes"] == 1
    assert s["repeated_routes"] == 1 and s["max_route_multiplicity"] == 3
    assert s["papillon_shards_touched"] == 1 and s["unique_branch_paths"] == 1
    assert s["recent"][-1]["papillon_shard"] == expected
    assert s["recent"][-1]["route_ref"] == f"P{expected:03d}|ROOT/A"
    print("S3_EXACT_PAPILLON_ROUTE=PASS", expected, s["recent"][-1]["route_ref"])


def test_same_z_multiple_observed_paths() -> None:
    pap = Papillon144()
    source_a, out_a = make_result("PLUS1", 10, "ROOT/A")
    source_b, out_b = make_result("PLUS1", 10, "ROOT/B")
    assert out_a.z_id == out_b.z_id
    t = S3RouteIndexTelemetry()
    t.observe("PLUS1", source_a, out_a, "LINEAGE_INDEXED_PARENT_BELOW_REFERENCE", papillon=pap)
    t.observe("PLUS1", source_b, out_b, "LINEAGE_INDEXED_PARENT_BELOW_REFERENCE", papillon=pap)
    s = t.status()
    assert s["unique_z_indexed"] == 1
    assert s["unique_routes"] == 2
    assert s["multi_route_z"] == 1
    assert s["max_routes_per_z"] == 2
    assert len(t.paths_by_z[out_a.z_id]) == 2
    print("S3_MULTI_ROUTE_Z=PASS", out_a.z_id, sorted(t.routes_by_z[out_a.z_id]))


def test_s2_gate_missing_papillon_and_path_drift() -> None:
    pap = Papillon144()
    source, out = make_result("PLUS1", 10, "ROOT/A")
    t = S3RouteIndexTelemetry()
    assert t.observe("PLUS1", source, out, "BLOCKED_S1_OTHER", papillon=pap) == "BLOCKED_S2_OTHER"
    assert t.observe("PLUS1", source, out, "LINEAGE_INDEXED_PARENT_AT_OR_ABOVE_REFERENCE", papillon=None) == "BLOCKED_MISSING_PAPILLON_INDEX"
    drift = replace(out, branch_path="ROOT/B")
    assert t.observe("PLUS1", source, drift, "LINEAGE_INDEXED_PARENT_AT_OR_ABOVE_REFERENCE", papillon=pap) == "BLOCKED_BRANCH_PATH_DRIFT"
    s = t.status()
    assert s["indexed"] == 0
    assert s["blocked_s2_other"] == 1 and s["blocked_missing_papillon"] == 1 and s["blocked_path_drift"] == 1
    print("S3_INPUT_GATES=PASS")


def test_no_router_authority() -> None:
    pap = Papillon144()
    source, out = make_result("DOUBLE", 11, "ROOT/A")
    before = pap.status()
    t = S3RouteIndexTelemetry()
    t.observe("DOUBLE", source, out, "LINEAGE_INDEXED_PARENT_AT_OR_ABOVE_REFERENCE", papillon=pap)
    s = t.status()
    assert pap.status() == before
    assert s["creates_parallel_router"] is False
    assert s["chooses_route"] is False and s["applies_route"] is False and s["actual_routes_applied"] == 0
    assert s["controls_routing"] is False and s["controls_scheduling"] is False and s["controls_calculation"] is False
    assert s["lineage_mutated"] is False and s["formula_index_authority"] is False
    assert s["scientific_proof_claim"] is False and s["proof_promotion"] is False
    print("S3_READ_ONLY_AUTHORITY=PASS")


def test_dashboard_lockstep() -> None:
    with tempfile.TemporaryDirectory(prefix="brotos3-") as td:
        service = DashboardService(
            Path(td) / "instance",
            spec=ExperimentSpec(duration_seconds=60, checkpoint_seconds=60, max_depth=4, max_active_branches=16, max_packets=100),
            checkpoint_seconds=60,
            tick_seconds=0.01,
            sleeping_pool_enabled=False,
        )
        assert getattr(service._runner, "papillon", None) is not None
        modules = [
            service.t8_countertest, service.t9_stability, service.t10_replay,
            service.t11_budget, service.t12_candidate, service.l1_crystal_score,
            service.l2_threshold, service.l3_press, service.l4_canon,
            service.l5_placement, service.s1_aggregator, service.s2_lineage_index,
            service.s3_route_index,
        ]
        before = [m.status()["observations"] for m in modules]
        for _ in range(17):
            source, out = make_result("DOUBLE", 11, "ROOT/A")
            service._observe_formula_result("DOUBLE", source, out)
        after = [m.status()["observations"] for m in modules]
        assert [a-b for a,b in zip(after,before)] == [17] * 13
        s = service.s3_route_index.status()
        assert s["indexed"] == 17
        assert s["blocked_s2_other"] == 0 and s["blocked_missing_z"] == 0
        assert s["blocked_missing_path"] == 0 and s["blocked_missing_papillon"] == 0 and s["blocked_path_drift"] == 0
        assert s["unique_routes"] == 1 and s["max_route_multiplicity"] == 17
        assert s["unique_z_indexed"] == 1 and s["papillon_shards_touched"] == 1
        assert s["reference_sides"] == {"AT_OR_ABOVE_REFERENCE": 16, "BELOW_REFERENCE": 1}
        print("S3_CALLBACK_LOCKSTEP=PASS", *after, s["unique_routes"], s["max_route_multiplicity"])


if __name__ == "__main__":
    test_exact_live_papillon_shard_and_repeat()
    test_same_z_multiple_observed_paths()
    test_s2_gate_missing_papillon_and_path_drift()
    test_no_router_authority()
    test_dashboard_lockstep()
    print("S3_ROUTE_INDEX=PASS")
