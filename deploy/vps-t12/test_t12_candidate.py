from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ["BROTO_T8_ENABLED"] = "1"
os.environ["BROTO_T9_ENABLED"] = "1"
os.environ["BROTO_T10_ENABLED"] = "1"
os.environ["BROTO_T11_ENABLED"] = "1"
os.environ["BROTO_T12_ENABLED"] = "1"
os.environ["BROTO_T11_CPU_SLOTS"] = "8"
os.environ["BROTO_T11_MEMORY_SLOTS"] = "8"
os.environ["BROTO_T11_STORAGE_SLOTS"] = "8"
os.environ["BROTO_T11_TIME_SLOTS"] = "8"

from brotoculateur.dashboard import DashboardService, build_default_registry
from brotoculateur.engine import TracePacket, z_stamp_child, z_stamp_root
from brotoculateur.orchestrator import ExperimentSpec
from brotoculateur.t12_candidate import T12CandidateTelemetry


def make_result(formula_id: str, value: int):
    registry = build_default_registry()
    formula = registry.get(formula_id)
    source = z_stamp_root(TracePacket(value))
    assert formula.is_applicable(source), (formula_id, value)
    out = formula.apply(source)
    out = z_stamp_child(out, source)
    return source, out


def test_recognized_budget_classes_become_candidates() -> None:
    t12 = T12CandidateTelemetry()
    source, out = make_result("PLUS1", 10)
    cases = {
        "BUDGET_FULL_8": "CANDIDATE_RECORDED_FULL_BUDGET",
        "BUDGET_PARTIAL_2_OF_8": "CANDIDATE_RECORDED_PARTIAL_BUDGET",
        "BUDGET_ZERO_OF_8": "CANDIDATE_RECORDED_ZERO_BUDGET",
    }
    for t11_outcome, expected in cases.items():
        assert t12.observe("PLUS1", source, out, t11_outcome) == expected
    s = t12.status()
    assert s["candidate_records"] == 3
    assert s["unique_candidate_ids"] == 1
    assert s["budget_classes"] == {"FULL": 1, "PARTIAL": 1, "ZERO": 1}
    assert s["records_zero_budget_candidates"] is True
    print("T12_BUDGET_CLASSES=PASS", s["budget_classes"])


def test_candidate_identity_does_not_depend_on_budget() -> None:
    t12 = T12CandidateTelemetry()
    source, out = make_result("DOUBLE", 11)
    t12.observe("DOUBLE", source, out, "BUDGET_FULL_8")
    first = t12.status()["recent"][-1]["candidate_id"]
    t12.observe("DOUBLE", source, out, "BUDGET_PARTIAL_1_OF_8")
    second = t12.status()["recent"][-1]["candidate_id"]
    assert first == second
    assert t12.status()["unique_candidate_ids"] == 1
    print("T12_ID_STABILITY=PASS", first)


def test_unknown_t11_is_blocked_not_materialized() -> None:
    t12 = T12CandidateTelemetry()
    source, out = make_result("PLUS1", 10)
    assert t12.observe("PLUS1", source, out, "BLOCKED_T10_OTHER") == "BLOCKED_T11_OTHER"
    s = t12.status()
    assert s["candidate_records"] == 0
    assert s["unique_candidate_ids"] == 0
    assert s["blocked_t11_other"] == 1
    print("T12_T11_GATE=PASS")


def test_no_score_threshold_or_scientific_claim() -> None:
    t12 = T12CandidateTelemetry()
    source, out = make_result("PLUS1", 10)
    t12.observe("PLUS1", source, out, "BUDGET_FULL_8")
    s = t12.status()
    assert s["candidate_definition"] == "TECHNICAL_PRE_SCORE_RECORD"
    assert s["l1_crystal_score_input"] is True
    assert s["assigns_score"] is False
    assert s["applies_threshold"] is False
    assert s["scientific_candidate_claim"] is False
    assert s["scientific_proof_claim"] is False
    assert s["candidate_key_is_c2_fingerprint"] is False
    assert s["candidate_key_is_scientific_identity"] is False
    assert s["canonizes"] is False
    assert s["promotes_proof"] is False
    assert s["validation_state_mutated"] is False
    assert s["controls_routing"] is False
    assert s["controls_scheduling"] is False
    assert s["controls_calculation"] is False
    assert s["reserves_resources"] is False
    assert s["executes_replay"] is False
    assert s["schedules_replay"] is False
    assert s["proof_promotion"] is False
    print("T12_NO_PROMOTION=PASS")


def test_dashboard_callback_lockstep() -> None:
    with tempfile.TemporaryDirectory(prefix="brotot12-") as td:
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
        before = [
            service.t8_countertest.status()["observations"],
            service.t9_stability.status()["observations"],
            service.t10_replay.status()["observations"],
            service.t11_budget.status()["observations"],
            service.t12_candidate.status()["observations"],
        ]

        for _ in range(17):
            source, out = make_result("DOUBLE", 11)
            service._observe_formula_result("DOUBLE", source, out)

        after = [
            service.t8_countertest.status()["observations"],
            service.t9_stability.status()["observations"],
            service.t10_replay.status()["observations"],
            service.t11_budget.status()["observations"],
            service.t12_candidate.status()["observations"],
        ]
        deltas = [a - b for a, b in zip(after, before)]
        assert deltas == [17, 17, 17, 17, 17]
        s8 = service.t8_countertest.status()
        s9 = service.t9_stability.status()
        s10 = service.t10_replay.status()
        s11 = service.t11_budget.status()
        s12 = service.t12_candidate.status()
        assert s8["failed"] == 0 and s8["limited"] == 0
        assert s9["drifts"] == 0
        assert s10["blocked_t8_fail"] == 0
        assert s10["blocked_t8_limited"] == 0
        assert s10["blocked_t9_drift"] == 0
        assert s11["blocked_t10_other"] == 0
        assert s12["blocked_t11_other"] == 0
        assert s12["candidate_records"] == 17
        assert s12["l1_crystal_score_input"] is True
        assert s12["assigns_score"] is False
        assert s12["proof_promotion"] is False
        print("T12_CALLBACK_LOCKSTEP=PASS", *deltas, s12["candidate_records"])


if __name__ == "__main__":
    test_recognized_budget_classes_become_candidates()
    test_candidate_identity_does_not_depend_on_budget()
    test_unknown_t11_is_blocked_not_materialized()
    test_no_score_threshold_or_scientific_claim()
    test_dashboard_callback_lockstep()
    print("T12_CANDIDATE=PASS")
