from __future__ import annotations

import os, tempfile
from pathlib import Path

for name in (
    "BROTO_T8_ENABLED","BROTO_T9_ENABLED","BROTO_T10_ENABLED","BROTO_T11_ENABLED",
    "BROTO_T12_ENABLED","BROTO_L1_ENABLED","BROTO_L2_ENABLED","BROTO_L3_ENABLED",
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
from brotoculateur.l3_press import L3PressTelemetry


def make_result(formula_id: str, value: int):
    registry = build_default_registry()
    formula = registry.get(formula_id)
    source = z_stamp_root(TracePacket(value))
    assert formula.is_applicable(source)
    out = z_stamp_child(formula.apply(source), source)
    return source, out


def test_dust_key_equals_existing_output_z() -> None:
    source, out = make_result("DOUBLE", 11)
    t = L3PressTelemetry()
    a = t.observe("DOUBLE", source, out, "BELOW_ENGINEERING_REFERENCE")
    b = t.observe("DOUBLE", source, out, "AT_OR_ABOVE_ENGINEERING_REFERENCE")
    s = t.status()
    assert a == "PRESSED_BELOW_REFERENCE"
    assert b == "PRESSED_AT_OR_ABOVE_REFERENCE"
    assert s["pressed"] == 2
    assert s["unique_dust_keys"] == 1
    assert s["recent"][0]["dust_key"] == out.z_id
    assert s["recent"][1]["dust_key"] == out.z_id
    assert s["dust_key_is_output_z_id"] is True
    assert s["creates_new_identity"] is False
    print("L3_DUST_KEY_Z_ID=PASS", out.z_id)


def test_missing_z_blocks_instead_of_inventing() -> None:
    t = L3PressTelemetry()
    source = TracePacket(10)
    out = TracePacket(11)
    assert t.observe("PLUS1", source, out, "AT_OR_ABOVE_ENGINEERING_REFERENCE") == "BLOCKED_MISSING_Z_ID"
    s = t.status()
    assert s["pressed"] == 0
    assert s["blocked_missing_z"] == 1
    assert s["unique_dust_keys"] == 0
    print("L3_MISSING_Z_GATE=PASS")


def test_invalid_l2_blocks() -> None:
    source, out = make_result("PLUS1", 10)
    t = L3PressTelemetry()
    assert t.observe("PLUS1", source, out, "BLOCKED_SCORE_INVALID") == "BLOCKED_L2_OTHER"
    s = t.status()
    assert s["blocked_l2_other"] == 1 and s["pressed"] == 0
    print("L3_L2_GATE=PASS")


def test_no_canon_or_promotion() -> None:
    source, out = make_result("PLUS1", 10)
    t = L3PressTelemetry()
    t.observe("PLUS1", source, out, "AT_OR_ABOVE_ENGINEERING_REFERENCE")
    s = t.status()
    assert s["l4_canon_input"] is True
    assert s["canonizes"] is False
    assert s["assigns_score"] is False
    assert s["applies_threshold"] is False
    assert s["accepts_candidate"] is False and s["rejects_candidate"] is False
    assert s["validation_state_mutated"] is False
    assert s["proof_promotion"] is False
    print("L3_NO_CANON_PROMOTION=PASS")


def test_dashboard_lockstep() -> None:
    with tempfile.TemporaryDirectory(prefix="brotol3-") as td:
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
        ]
        before = [m.status()["observations"] for m in modules]
        for _ in range(17):
            source, out = make_result("DOUBLE", 11)
            service._observe_formula_result("DOUBLE", source, out)
        after = [m.status()["observations"] for m in modules]
        assert [a - b for a, b in zip(after, before)] == [17] * 8
        s = service.l3_press.status()
        assert s["pressed"] == 17
        assert s["blocked_l2_other"] == 0
        assert s["blocked_missing_z"] == 0
        assert s["unique_dust_keys"] == 1
        assert s["reference_sides"] == {"AT_OR_ABOVE_REFERENCE": 16, "BELOW_REFERENCE": 1}
        assert all(r["dust_key"] == r["output_z_id"] for r in s["recent"])
        print("L3_CALLBACK_LOCKSTEP=PASS", *after, s["reference_sides"], s["unique_dust_keys"])


if __name__ == "__main__":
    test_dust_key_equals_existing_output_z()
    test_missing_z_blocks_instead_of_inventing()
    test_invalid_l2_blocks()
    test_no_canon_or_promotion()
    test_dashboard_lockstep()
    print("L3_PRESS=PASS")
