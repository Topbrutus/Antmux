from __future__ import annotations

import os
import tempfile
from dataclasses import replace
from pathlib import Path

for name in (
    "BROTO_T8_ENABLED","BROTO_T9_ENABLED","BROTO_T10_ENABLED","BROTO_T11_ENABLED",
    "BROTO_T12_ENABLED","BROTO_L1_ENABLED","BROTO_L2_ENABLED","BROTO_L3_ENABLED",
    "BROTO_L4_ENABLED","BROTO_L5_ENABLED","BROTO_S1_ENABLED","BROTO_S2_ENABLED",
    "BROTO_S3_ENABLED","BROTO_S4_ENABLED","BROTO_S5_ENABLED",
):
    os.environ[name] = "1"
os.environ["BROTO_L2_THRESHOLD"] = "75"
os.environ["BROTO_T11_CPU_SLOTS"] = "8"
os.environ["BROTO_T11_MEMORY_SLOTS"] = "8"
os.environ["BROTO_T11_STORAGE_SLOTS"] = "8"
os.environ["BROTO_T11_TIME_SLOTS"] = "8"

from brotoculateur.c3_library import C3Library37
from brotoculateur.dashboard import DashboardService, build_default_registry
from brotoculateur.engine import TracePacket, c2_fingerprint, z_stamp_child, z_stamp_root
from brotoculateur.orchestrator import ExperimentSpec
from brotoculateur.s5_fast_index import S5FastIndexTelemetry


def make_result(formula_id: str, value: int, branch_path: str = "ROOT"):
    registry = build_default_registry()
    formula = registry.get(formula_id)
    source = z_stamp_root(TracePacket(value, branch_path=branch_path))
    assert formula.is_applicable(source), (formula_id, value)
    out = z_stamp_child(formula.apply(source), source)
    return source, out


def test_exact_c2_c3_bucket_and_lookup() -> None:
    source, out = make_result("DOUBLE", 11, "ROOT/A")
    fp = c2_fingerprint(out)
    expected_bucket = C3Library37.bucket_for(fp)
    t = S5FastIndexTelemetry()
    for _ in range(3):
        got = t.observe("DOUBLE", source, out, "FORMULA_INDEXED_AT_OR_ABOVE_REFERENCE")
        assert got == "FAST_INDEXED_AT_OR_ABOVE_REFERENCE"
    s = t.status()
    assert s["indexed"] == 3
    assert s["unique_fingerprints"] == 1 and s["unique_fast_entries"] == 1
    assert s["repeated_fast_entries"] == 1 and s["max_fast_entry_multiplicity"] == 3
    assert s["recent"][-1]["bucket37"] == expected_bucket
    assert t.lookup(fp) == {("DOUBLE", out.z_id)}
    print("S5_EXACT_C2_C3_BUCKET=PASS", expected_bucket, fp, out.z_id)


def test_same_z_multiple_formulas_preserved() -> None:
    a, ao = make_result("PLUS1", 10)       # 10 -> 11
    b, bo = make_result("HALF_EVEN", 22)  # 22 -> 11
    assert ao.z_id == bo.z_id
    fpa, fpb = c2_fingerprint(ao), c2_fingerprint(bo)
    assert fpa != fpb
    t = S5FastIndexTelemetry()
    t.observe("PLUS1", a, ao, "FORMULA_INDEXED_BELOW_REFERENCE")
    t.observe("HALF_EVEN", b, bo, "FORMULA_INDEXED_AT_OR_ABOVE_REFERENCE")
    s = t.status()
    assert s["unique_z_indexed"] == 1
    assert s["unique_fingerprints"] == 2
    assert s["unique_fast_entries"] == 2
    assert t.lookup(fpa) == {("PLUS1", ao.z_id)}
    assert t.lookup(fpb) == {("HALF_EVEN", bo.z_id)}
    print("S5_MULTI_FORMULA_Z_PRESERVED=PASS", ao.z_id, C3Library37.bucket_for(fpa), C3Library37.bucket_for(fpb))


def test_input_guards() -> None:
    source, out = make_result("PLUS1", 10)
    t = S5FastIndexTelemetry()
    assert t.observe("PLUS1", source, out, "BLOCKED_S3_OTHER") == "BLOCKED_S4_OTHER"
    assert t.observe("", source, out, "FORMULA_INDEXED_AT_OR_ABOVE_REFERENCE") == "BLOCKED_MISSING_FORMULA_ID"
    assert t.observe("PLUS1", source, replace(out, z_id=None), "FORMULA_INDEXED_AT_OR_ABOVE_REFERENCE") == "BLOCKED_MISSING_Z_ID"
    assert t.observe("DOUBLE", source, out, "FORMULA_INDEXED_AT_OR_ABOVE_REFERENCE") == "BLOCKED_FORMULA_CHAIN_MISMATCH"
    s = t.status()
    assert s["indexed"] == 0
    assert s["blocked_s4_other"] == 1 and s["blocked_missing_formula"] == 1
    assert s["blocked_missing_z"] == 1 and s["blocked_formula_mismatch"] == 1
    print("S5_INPUT_GATES=PASS")


def test_capacity_is_bounded_without_eviction() -> None:
    t = S5FastIndexTelemetry(max_entries=37)
    accepted = 0
    rejected = 0
    for value in range(1, 50):
        source, out = make_result("PLUS1", value)
        outcome = t.observe("PLUS1", source, out, "FORMULA_INDEXED_AT_OR_ABOVE_REFERENCE")
        if outcome.startswith("FAST_INDEXED_"):
            accepted += 1
        elif outcome == "BLOCKED_CAPACITY":
            rejected += 1
    s = t.status()
    assert accepted == 37 and rejected == 12
    assert s["unique_fast_entries"] == 37 and s["capacity_rejections"] == 12
    assert s["indexed"] == 37 and s["observations"] == 49
    print("S5_CAPACITY_BOUND=PASS", accepted, rejected)


def test_no_execution_authority() -> None:
    source, out = make_result("DOUBLE", 11)
    t = S5FastIndexTelemetry()
    t.observe("DOUBLE", source, out, "FORMULA_INDEXED_AT_OR_ABOVE_REFERENCE")
    s = t.status()
    assert s["uses_existing_c2_fingerprint"] is True and s["uses_exact_c3_bucket_function"] is True
    assert s["full_c2_fingerprint_is_identity"] is True and s["bucket37_is_routing_only"] is True
    assert s["query_before_compute"] is False and s["compute_skips"] == 0
    assert s["persistent"] is False and s["s4_formula_index_mutated"] is False
    assert s["creates_formula"] is False and s["executes_formula"] is False and s["selects_formula"] is False
    assert s["controls_routing"] is False and s["controls_scheduling"] is False and s["controls_calculation"] is False
    assert s["scientific_proof_claim"] is False and s["proof_promotion"] is False
    assert s["co1_archive_input"] is True
    print("S5_READ_ONLY_AUTHORITY=PASS")


def test_dashboard_lockstep() -> None:
    with tempfile.TemporaryDirectory(prefix="brotos5-") as td:
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
            service.s3_route_index, service.s4_formula_index, service.s5_fast_index,
        ]
        before = [m.status()["observations"] for m in modules]
        for _ in range(17):
            source, out = make_result("DOUBLE", 11, "ROOT/A")
            service._observe_formula_result("DOUBLE", source, out)
        after = [m.status()["observations"] for m in modules]
        assert [a-b for a,b in zip(after,before)] == [17] * 15
        s4 = service.s4_formula_index.status()
        s5 = service.s5_fast_index.status()
        assert s5["observations"] == s4["observations"] == 17
        assert s5["indexed"] == s4["indexed"] == 17
        assert s5["blocked_s4_other"] == 0 and s5["capacity_rejections"] == 0
        assert s5["unique_fingerprints"] == 1 and s5["unique_fast_entries"] == 1
        assert s5["unique_z_indexed"] == 1 and s5["max_fast_entry_multiplicity"] == 17
        assert s5["occupied_buckets"] == 1 and sum(s5["reference_sides"].values()) == 17
        print("S5_CALLBACK_LOCKSTEP=PASS", *after, s5["occupied_buckets"], s5["max_fast_entry_multiplicity"])


if __name__ == "__main__":
    test_exact_c2_c3_bucket_and_lookup()
    test_same_z_multiple_formulas_preserved()
    test_input_guards()
    test_capacity_is_bounded_without_eviction()
    test_no_execution_authority()
    test_dashboard_lockstep()
    print("S5_FAST_INDEX=PASS")
