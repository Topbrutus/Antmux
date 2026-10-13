from __future__ import annotations

import os
import tempfile
from pathlib import Path

for name in (
    "BROTO_T8_ENABLED","BROTO_T9_ENABLED","BROTO_T10_ENABLED","BROTO_T11_ENABLED",
    "BROTO_T12_ENABLED","BROTO_L1_ENABLED","BROTO_L2_ENABLED","BROTO_L3_ENABLED","BROTO_L4_ENABLED",
):
    os.environ[name] = "1"
os.environ["BROTO_L2_THRESHOLD"] = "75"
os.environ["BROTO_T11_CPU_SLOTS"] = "8"
os.environ["BROTO_T11_MEMORY_SLOTS"] = "8"
os.environ["BROTO_T11_STORAGE_SLOTS"] = "8"
os.environ["BROTO_T11_TIME_SLOTS"] = "8"

from brotoculateur.dashboard import DashboardService, build_default_registry
from brotoculateur.engine import TracePacket, z_stamp_child, z_stamp_root
from brotoculateur.l4_canon import L4CanonTelemetry
from brotoculateur.orchestrator import ExperimentSpec


def make_result(formula_id: str, value: int):
    registry = build_default_registry()
    formula = registry.get(formula_id)
    source = z_stamp_root(TracePacket(value))
    assert formula.is_applicable(source)
    out = z_stamp_child(formula.apply(source), source)
    return source, out


def test_canonical_z_equals_existing_output_z() -> None:
    source, out = make_result("DOUBLE", 11)
    t = L4CanonTelemetry()
    a = t.observe("DOUBLE", source, out, "PRESSED_BELOW_REFERENCE")
    b = t.observe("DOUBLE", source, out, "PRESSED_AT_OR_ABOVE_REFERENCE")
    s = t.status()
    assert a == "CANONICAL_Z_RECORDED_BELOW_REFERENCE"
    assert b == "CANONICAL_Z_RECORDED_AT_OR_ABOVE_REFERENCE"
    assert s["canonical_records"] == 2
    assert s["unique_canonical_z"] == 1
    assert s["recent"][0]["canonical_z"] == out.z_id
    assert s["recent"][1]["canonical_z"] == out.z_id
    assert s["canonical_z_is_output_z_id"] is True
    assert s["creates_new_identity"] is False
    print("L4_CANONICAL_Z_ID=PASS", out.z_id)


def test_missing_z_blocks_instead_of_inventing() -> None:
    t = L4CanonTelemetry()
    source = TracePacket(10)
    out = TracePacket(11)
    assert t.observe("PLUS1", source, out, "PRESSED_AT_OR_ABOVE_REFERENCE") == "BLOCKED_MISSING_Z_ID"
    s = t.status()
    assert s["canonical_records"] == 0
    assert s["blocked_missing_z"] == 1
    assert s["unique_canonical_z"] == 0
    print("L4_MISSING_Z_GATE=PASS")


def test_invalid_l3_blocks() -> None:
    source, out = make_result("PLUS1", 10)
    t = L4CanonTelemetry()
    assert t.observe("PLUS1", source, out, "BLOCKED_MISSING_Z_ID") == "BLOCKED_L3_OTHER"
    s = t.status()
    assert s["blocked_l3_other"] == 1
    assert s["canonical_records"] == 0
    print("L4_L3_GATE=PASS")


def test_technical_canon_is_not_scientific_proof() -> None:
    source, out = make_result("PLUS1", 10)
    t = L4CanonTelemetry()
    t.observe("PLUS1", source, out, "PRESSED_AT_OR_ABOVE_REFERENCE")
    s = t.status()
    assert s["technical_identity_canon"] is True
    assert s["scientific_canon_claim"] is False
    assert s["canonicalizes_scientific_proof"] is False
    assert s["l5_placement_input"] is True
    assert s["assigns_score"] is False
    assert s["applies_threshold"] is False
    assert s["accepts_candidate"] is False and s["rejects_candidate"] is False
    assert s["validation_state_mutated"] is False
    assert s["proof_promotion"] is False
    print("L4_NO_SCIENTIFIC_CANON_PROMOTION=PASS")


def test_dashboard_lockstep() -> None:
    with tempfile.TemporaryDirectory(prefix="brotol4-") as td:
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
        modules = [
            service.t8_countertest,
            service.t9_stability,
            service.t10_replay,
            service.t11_budget,
            service.t12_candidate,
            service.l1_crystal_score,
            service.l2_threshold,
            service.l3_press,
            service.l4_canon,
        ]
        before = [m.status()["observations"] for m in modules]
        for _ in range(17):
            source, out = make_result("DOUBLE", 11)
            service._observe_formula_result("DOUBLE", source, out)
        after = [m.status()["observations"] for m in modules]
        assert [a - b for a, b in zip(after, before)] == [17] * 9
        l3 = service.l3_press.status()
        l4 = service.l4_canon.status()
        assert l3["pressed"] == 17
        assert l4["canonical_records"] == 17
        assert l4["blocked_l3_other"] == 0
        assert l4["blocked_missing_z"] == 0
        assert l4["unique_canonical_z"] == 1
        assert l4["reference_sides"] == {"AT_OR_ABOVE_REFERENCE": 16, "BELOW_REFERENCE": 1}
        assert all(r["canonical_z"] == r["output_z_id"] for r in l4["recent"])
        print("L4_CALLBACK_LOCKSTEP=PASS", *after, l4["reference_sides"], l4["unique_canonical_z"])


if __name__ == "__main__":
    test_canonical_z_equals_existing_output_z()
    test_missing_z_blocks_instead_of_inventing()
    test_invalid_l3_blocks()
    test_technical_canon_is_not_scientific_proof()
    test_dashboard_lockstep()
    print("L4_CANON=PASS")
