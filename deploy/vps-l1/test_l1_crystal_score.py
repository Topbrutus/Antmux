from __future__ import annotations

import os, tempfile
from pathlib import Path

for name in ("BROTO_T8_ENABLED","BROTO_T9_ENABLED","BROTO_T10_ENABLED","BROTO_T11_ENABLED","BROTO_T12_ENABLED","BROTO_L1_ENABLED"):
    os.environ[name]="1"
os.environ["BROTO_T11_CPU_SLOTS"]="8"; os.environ["BROTO_T11_MEMORY_SLOTS"]="8"; os.environ["BROTO_T11_STORAGE_SLOTS"]="8"; os.environ["BROTO_T11_TIME_SLOTS"]="8"

from brotoculateur.dashboard import DashboardService, build_default_registry
from brotoculateur.engine import TracePacket, z_stamp_child, z_stamp_root
from brotoculateur.orchestrator import ExperimentSpec
from brotoculateur.l1_crystal_score import L1CrystalScoreTelemetry, score_components, engineering_score


def make_result(formula_id: str, value: int):
    registry=build_default_registry(); formula=registry.get(formula_id); source=z_stamp_root(TracePacket(value)); assert formula.is_applicable(source); out=z_stamp_child(formula.apply(source),source); return source,out


def test_formula_extremes() -> None:
    c=score_components(t8_outcome="PASS",t9_outcome="BASELINE",t10_outcome="REPLAY_8",t11_outcome="BUDGET_FULL_8")
    assert c is not None and engineering_score(c)==62.5
    c=score_components(t8_outcome="PASS",t9_outcome="STABLE_REPEAT",t10_outcome="REPLAY_1",t11_outcome="BUDGET_FULL_1")
    assert c is not None and engineering_score(c)==100.0
    c=score_components(t8_outcome="PASS",t9_outcome="STABLE_REPEAT",t10_outcome="REPLAY_4",t11_outcome="BUDGET_PARTIAL_2_OF_4")
    assert c is not None and engineering_score(c)==76.785714
    print("L1_FORMULA_EXTREMES=PASS")


def test_invalid_upstream_blocks() -> None:
    t=L1CrystalScoreTelemetry(); source,out=make_result("PLUS1",10)
    assert t.observe("PLUS1",source,out,"FAIL","UPSTREAM_FAIL","BLOCKED","BLOCKED","CANDIDATE_RECORDED_FULL_BUDGET")=="BLOCKED_COMPONENT_INVALID"
    assert t.observe("PLUS1",source,out,"PASS","STABLE_REPEAT","REPLAY_1","BUDGET_FULL_1","BLOCKED_T11_OTHER")=="BLOCKED_T12_OTHER"
    s=t.status(); assert s["scored"]==0 and s["blocked_component_invalid"]==1 and s["blocked_t12_other"]==1
    print("L1_UPSTREAM_GATES=PASS")


def test_no_threshold_or_promotion() -> None:
    t=L1CrystalScoreTelemetry(); source,out=make_result("PLUS1",10)
    assert t.observe("PLUS1",source,out,"PASS","STABLE_REPEAT","REPLAY_2","BUDGET_FULL_2","CANDIDATE_RECORDED_FULL_BUDGET")=="CRYSTAL_SCORE_RECORDED"
    s=t.status(); assert s["applies_threshold"] is False and s["threshold_value"] is None
    assert s["accepts_candidate"] is False and s["rejects_candidate"] is False
    assert s["scientific_score_claim"] is False and s["proof_promotion"] is False
    assert 0 <= s["score_min"] <= s["score_max"] <= 100
    print("L1_NO_THRESHOLD_PROMOTION=PASS",s["score_average"])


def test_dashboard_lockstep() -> None:
    with tempfile.TemporaryDirectory(prefix="brotol1-") as td:
        service=DashboardService(Path(td)/"instance",spec=ExperimentSpec(duration_seconds=60,checkpoint_seconds=60,max_depth=4,max_active_branches=16,max_packets=100),checkpoint_seconds=60,tick_seconds=0.01,sleeping_pool_enabled=False)
        before=[service.t8_countertest.status()["observations"],service.t9_stability.status()["observations"],service.t10_replay.status()["observations"],service.t11_budget.status()["observations"],service.t12_candidate.status()["observations"],service.l1_crystal_score.status()["observations"]]
        for _ in range(17):
            source,out=make_result("DOUBLE",11); service._observe_formula_result("DOUBLE",source,out)
        after=[service.t8_countertest.status()["observations"],service.t9_stability.status()["observations"],service.t10_replay.status()["observations"],service.t11_budget.status()["observations"],service.t12_candidate.status()["observations"],service.l1_crystal_score.status()["observations"]]
        assert [a-b for a,b in zip(after,before)] == [17]*6
        s=service.l1_crystal_score.status(); assert s["scored"]==17 and s["blocked_t12_other"]==0 and s["blocked_component_invalid"]==0
        assert s["l2_threshold_input"] is True and s["applies_threshold"] is False
        print("L1_CALLBACK_LOCKSTEP=PASS",*after,s["score_average"])

if __name__=="__main__":
    test_formula_extremes(); test_invalid_upstream_blocks(); test_no_threshold_or_promotion(); test_dashboard_lockstep(); print("L1_CRYSTAL_SCORE=PASS")
