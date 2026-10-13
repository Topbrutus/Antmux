from __future__ import annotations

import os, tempfile
from pathlib import Path

for name in ("BROTO_T8_ENABLED","BROTO_T9_ENABLED","BROTO_T10_ENABLED","BROTO_T11_ENABLED","BROTO_T12_ENABLED","BROTO_L1_ENABLED","BROTO_L2_ENABLED"):
    os.environ[name]="1"
os.environ["BROTO_L2_THRESHOLD"]="75"
os.environ["BROTO_T11_CPU_SLOTS"]="8"; os.environ["BROTO_T11_MEMORY_SLOTS"]="8"; os.environ["BROTO_T11_STORAGE_SLOTS"]="8"; os.environ["BROTO_T11_TIME_SLOTS"]="8"

from brotoculateur.dashboard import DashboardService, build_default_registry
from brotoculateur.engine import TracePacket, z_stamp_child, z_stamp_root
from brotoculateur.orchestrator import ExperimentSpec
from brotoculateur.l2_threshold import L2ThresholdTelemetry


def make_result(formula_id: str, value: int):
    registry=build_default_registry(); formula=registry.get(formula_id); source=z_stamp_root(TracePacket(value)); assert formula.is_applicable(source); out=z_stamp_child(formula.apply(source),source); return source,out


def test_threshold_boundary() -> None:
    t=L2ThresholdTelemetry(threshold=75); source,out=make_result("PLUS1",10)
    assert t.observe("PLUS1",source,out,"PASS","STABLE_REPEAT","REPLAY_8","BUDGET_FULL_8","CANDIDATE_RECORDED_FULL_BUDGET","CRYSTAL_SCORE_RECORDED")=="AT_OR_ABOVE_ENGINEERING_REFERENCE"
    assert t.status()["recent"][-1]["score"]==75.0
    assert t.status()["recent"][-1]["margin"]==0.0
    print("L2_BOUNDARY=PASS")


def test_below_and_above() -> None:
    t=L2ThresholdTelemetry(threshold=75); source,out=make_result("PLUS1",10)
    assert t.observe("PLUS1",source,out,"PASS","BASELINE","REPLAY_8","BUDGET_FULL_8","CANDIDATE_RECORDED_FULL_BUDGET","CRYSTAL_SCORE_RECORDED")=="BELOW_ENGINEERING_REFERENCE"
    assert t.observe("PLUS1",source,out,"PASS","STABLE_REPEAT","REPLAY_1","BUDGET_FULL_1","CANDIDATE_RECORDED_FULL_BUDGET","CRYSTAL_SCORE_RECORDED")=="AT_OR_ABOVE_ENGINEERING_REFERENCE"
    s=t.status(); assert s["below_reference"]==1 and s["at_or_above_reference"]==1
    print("L2_ABOVE_BELOW=PASS")


def test_guardrails() -> None:
    t=L2ThresholdTelemetry(threshold=75); source,out=make_result("PLUS1",10)
    assert t.observe("PLUS1",source,out,"PASS","STABLE_REPEAT","REPLAY_1","BUDGET_FULL_1","CANDIDATE_RECORDED_FULL_BUDGET","BLOCKED") == "BLOCKED_L1_OTHER"
    s=t.status(); assert s["threshold_scientifically_calibrated"] is False and s["scientific_threshold_claim"] is False
    assert s["accepts_candidate"] is False and s["rejects_candidate"] is False and s["proof_promotion"] is False
    assert s["l3_press_input"] is True and s["authority"]=="SHADOW_ONLY"
    print("L2_GUARDS=PASS")


def test_config_bounds() -> None:
    assert L2ThresholdTelemetry(threshold=-1).status()["threshold"]==0.0
    assert L2ThresholdTelemetry(threshold=101).status()["threshold"]==100.0
    print("L2_BOUNDS=PASS")


def test_dashboard_lockstep() -> None:
    with tempfile.TemporaryDirectory(prefix="brotol2-") as td:
        service=DashboardService(Path(td)/"instance",spec=ExperimentSpec(duration_seconds=60,checkpoint_seconds=60,max_depth=4,max_active_branches=16,max_packets=100),checkpoint_seconds=60,tick_seconds=0.01,sleeping_pool_enabled=False)
        before=[service.t8_countertest.status()["observations"],service.t9_stability.status()["observations"],service.t10_replay.status()["observations"],service.t11_budget.status()["observations"],service.t12_candidate.status()["observations"],service.l1_crystal_score.status()["observations"],service.l2_threshold.status()["observations"]]
        for _ in range(17):
            source,out=make_result("DOUBLE",11); service._observe_formula_result("DOUBLE",source,out)
        after=[service.t8_countertest.status()["observations"],service.t9_stability.status()["observations"],service.t10_replay.status()["observations"],service.t11_budget.status()["observations"],service.t12_candidate.status()["observations"],service.l1_crystal_score.status()["observations"],service.l2_threshold.status()["observations"]]
        assert [a-b for a,b in zip(after,before)] == [17]*7
        s=service.l2_threshold.status(); assert s["compared"]==17 and s["blocked_l1_other"]==0 and s["blocked_score_invalid"]==0
        print("L2_CALLBACK_LOCKSTEP=PASS",*after,s["at_or_above_reference"],s["below_reference"])

if __name__=="__main__":
    test_threshold_boundary(); test_below_and_above(); test_guardrails(); test_config_bounds(); test_dashboard_lockstep(); print("L2_THRESHOLD=PASS")
