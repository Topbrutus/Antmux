from __future__ import annotations

import os
import tempfile
from dataclasses import replace
from pathlib import Path

for name in (
    "BROTO_T8_ENABLED","BROTO_T9_ENABLED","BROTO_T10_ENABLED","BROTO_T11_ENABLED",
    "BROTO_T12_ENABLED","BROTO_L1_ENABLED","BROTO_L2_ENABLED","BROTO_L3_ENABLED",
    "BROTO_L4_ENABLED","BROTO_L5_ENABLED","BROTO_S1_ENABLED","BROTO_S2_ENABLED",
    "BROTO_S3_ENABLED","BROTO_S4_ENABLED",
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
from brotoculateur.s4_formula_index import S4FormulaIndexTelemetry


def make_result(formula_id: str, value: int, branch_path: str = "ROOT"):
    registry = build_default_registry()
    formula = registry.get(formula_id)
    source = z_stamp_root(TracePacket(value, branch_path=branch_path))
    assert formula.is_applicable(source), (formula_id, value)
    out = z_stamp_child(formula.apply(source), source)
    return source, out


def test_exact_formula_result_repeat() -> None:
    source, out = make_result("PLUS1", 10, "ROOT/A")
    t = S4FormulaIndexTelemetry()
    for _ in range(3):
        got = t.observe("PLUS1", source, out, "ROUTE_INDEXED_AT_OR_ABOVE_REFERENCE")
        assert got == "FORMULA_INDEXED_AT_OR_ABOVE_REFERENCE"
    s = t.status()
    assert s["indexed"] == 3
    assert s["unique_formulas"] == 1 and s["unique_result_z"] == 1
    assert s["unique_formula_result_pairs"] == 1
    assert s["repeated_formula_result_pairs"] == 1
    assert s["max_formula_result_multiplicity"] == 3
    assert s["recent"][-1]["formula_id"] == "PLUS1"
    assert s["recent"][-1]["z_id"] == out.z_id
    print("S4_EXACT_FORMULA_RESULT=PASS", out.z_id, s["max_formula_result_multiplicity"])


def test_one_formula_multiple_results() -> None:
    a, ao = make_result("PLUS1", 10)
    b, bo = make_result("PLUS1", 11)
    assert ao.z_id != bo.z_id
    t = S4FormulaIndexTelemetry()
    t.observe("PLUS1", a, ao, "ROUTE_INDEXED_BELOW_REFERENCE")
    t.observe("PLUS1", b, bo, "ROUTE_INDEXED_BELOW_REFERENCE")
    s = t.status()
    assert s["unique_formulas"] == 1
    assert s["unique_result_z"] == 2
    assert s["multi_result_formulas"] == 1
    assert s["max_results_per_formula"] == 2
    print("S4_MULTI_RESULT_FORMULA=PASS", sorted(t.results_by_formula["PLUS1"]))


def test_same_z_multiple_formulas() -> None:
    a, ao = make_result("PLUS1", 10)       # 10 -> 11
    b, bo = make_result("HALF_EVEN", 22)  # 22 -> 11
    assert ao.z_id == bo.z_id
    t = S4FormulaIndexTelemetry()
    t.observe("PLUS1", a, ao, "ROUTE_INDEXED_BELOW_REFERENCE")
    t.observe("HALF_EVEN", b, bo, "ROUTE_INDEXED_AT_OR_ABOVE_REFERENCE")
    s = t.status()
    assert s["unique_formulas"] == 2
    assert s["unique_result_z"] == 1
    assert s["multi_formula_z"] == 1
    assert s["max_formulas_per_z"] == 2
    assert t.formulas_by_z[ao.z_id] == {"PLUS1", "HALF_EVEN"}
    print("S4_MULTI_FORMULA_Z=PASS", ao.z_id, sorted(t.formulas_by_z[ao.z_id]))


def test_input_guards() -> None:
    source, out = make_result("PLUS1", 10)
    t = S4FormulaIndexTelemetry()
    assert t.observe("PLUS1", source, out, "BLOCKED_S2_OTHER") == "BLOCKED_S3_OTHER"
    assert t.observe("", source, out, "ROUTE_INDEXED_AT_OR_ABOVE_REFERENCE") == "BLOCKED_MISSING_FORMULA_ID"
    assert t.observe("PLUS1", source, replace(out, z_id=None), "ROUTE_INDEXED_AT_OR_ABOVE_REFERENCE") == "BLOCKED_MISSING_Z_ID"
    assert t.observe("DOUBLE", source, out, "ROUTE_INDEXED_AT_OR_ABOVE_REFERENCE") == "BLOCKED_FORMULA_CHAIN_MISMATCH"
    s = t.status()
    assert s["indexed"] == 0
    assert s["blocked_s3_other"] == 1
    assert s["blocked_missing_formula"] == 1
    assert s["blocked_missing_z"] == 1
    assert s["blocked_formula_mismatch"] == 1
    print("S4_INPUT_GATES=PASS")


def test_no_formula_authority() -> None:
    source, out = make_result("DOUBLE", 11)
    t = S4FormulaIndexTelemetry()
    t.observe("DOUBLE", source, out, "ROUTE_INDEXED_AT_OR_ABOVE_REFERENCE")
    s = t.status()
    assert s["creates_formula"] is False and s["executes_formula"] is False
    assert s["selects_formula"] is False and s["ranks_formula"] is False
    assert s["assigns_formula_score"] is False and s["merges_distinct_formulas"] is False
    assert s["formula_registry_mutated"] is False and s["route_index_mutated"] is False
    assert s["z_identity_preserved"] is True and s["s5_fast_index_input"] is True
    assert s["scientific_proof_claim"] is False and s["proof_promotion"] is False
    assert s["controls_routing"] is False and s["controls_scheduling"] is False and s["controls_calculation"] is False
    print("S4_READ_ONLY_AUTHORITY=PASS")


def test_dashboard_lockstep() -> None:
    with tempfile.TemporaryDirectory(prefix="brotos4-") as td:
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
            service.s3_route_index, service.s4_formula_index,
        ]
        before = [m.status()["observations"] for m in modules]
        for _ in range(17):
            source, out = make_result("DOUBLE", 11, "ROOT/A")
            service._observe_formula_result("DOUBLE", source, out)
        after = [m.status()["observations"] for m in modules]
        assert [a-b for a,b in zip(after,before)] == [17] * 14
        s3 = service.s3_route_index.status()
        s4 = service.s4_formula_index.status()
        assert s4["observations"] == s3["observations"] == 17
        assert s4["indexed"] == s3["indexed"] == 17
        assert s4["blocked_s3_other"] == 0
        assert s4["blocked_missing_formula"] == 0 and s4["blocked_missing_z"] == 0 and s4["blocked_formula_mismatch"] == 0
        assert s4["unique_formulas"] == 1 and s4["unique_result_z"] == 1
        assert s4["unique_formula_result_pairs"] == 1 and s4["max_formula_result_multiplicity"] == 17
        assert sum(s4["reference_sides"].values()) == 17
        print("S4_CALLBACK_LOCKSTEP=PASS", *after, s4["unique_formulas"], s4["unique_result_z"], s4["max_formula_result_multiplicity"])


if __name__ == "__main__":
    test_exact_formula_result_repeat()
    test_one_formula_multiple_results()
    test_same_z_multiple_formulas()
    test_input_guards()
    test_no_formula_authority()
    test_dashboard_lockstep()
    print("S4_FORMULA_INDEX=PASS")
