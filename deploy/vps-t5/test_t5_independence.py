from __future__ import annotations

import os

from brotoculateur.c3_library import C3Library37
from brotoculateur.c4_novelty import C4Novelty
from brotoculateur.c5_rarity import C5StructuralRarity
from brotoculateur.c6_provenance import C6Provenance
from brotoculateur.c7_router import C7ShadowRouter
from brotoculateur.dashboard import build_default_registry
from brotoculateur.engine import TracePacket, c2_fingerprint
from brotoculateur.orchestrator import ExperimentRunner, ExperimentSpec
from brotoculateur.t1_family import T1FamilyClassifier
from brotoculateur.t2_exact_duplicate import T2ExactDuplicate
from brotoculateur.t3_neighborhood import T3SemanticNeighborhood
from brotoculateur.t4_convergence import T4Convergence
from brotoculateur.t5_independence import T5OperationalIndependence


def set_env() -> None:
    for name in (
        "BROTO_C2_ENABLED", "BROTO_C3_ENABLED", "BROTO_C4_ENABLED", "BROTO_C5_ENABLED",
        "BROTO_C6_ENABLED", "BROTO_C7_ENABLED", "BROTO_T1_ENABLED", "BROTO_T2_ENABLED",
        "BROTO_T3_ENABLED", "BROTO_T4_ENABLED", "BROTO_T5_ENABLED",
    ):
        os.environ[name] = "1"
    os.environ["BROTO_ZSTAMP_ENABLED"] = "1"
    os.environ["BROTO_ZSTAMP_PERCENT"] = "100"


def packet(value: int, *, z: str, origin: str, parent: str, formula: str) -> TracePacket:
    return TracePacket(
        value=value,
        depth=1,
        formula_chain=(formula,),
        z_id=z,
        z_origin_id=origin,
        z_parent_id=parent,
    )


def test_three_axis_candidate_and_exact_repeat() -> None:
    t4 = T4Convergence(max_targets=32, sigs_per_target=8)
    t5 = T5OperationalIndependence(max_targets=32)
    p1 = packet(100, z="Z-target", origin="Z-origin-a", parent="Z-parent-a", formula="PLUS1")
    p2 = packet(100, z="Z-target", origin="Z-origin-b", parent="Z-parent-b", formula="PELL_N")
    f1, f2 = c2_fingerprint(p1), c2_fingerprint(p2)
    assert f1 != f2

    e1 = t4.observe(p1, f1, family="ARITHMETIC_EXPANSION", t2_event="UNIQUE", t3_class="ISOLATED")
    s1 = t4.target_summary("Z-target")
    assert e1 == "FIRST_STRUCTURE"
    assert t5.observe(p1, f1, t4_event=e1, t4_summary=s1) == "NOT_CONVERGENT"

    e2 = t4.observe(p2, f2, family="PELL", t2_event="UNIQUE", t3_class="NEAR")
    s2 = t4.target_summary("Z-target")
    assert e2.startswith("STRUCTURAL_CONVERGENCE")
    assert s2 == {
        "z_id": "Z-target", "distinct_c2": 2, "families": 2,
        "origins": 2, "parents": 2, "observations": 2, "convergent": True,
    }
    assert t5.observe(p2, f2, t4_event=e2, t4_summary=s2) == "INDEPENDENCE_CANDIDATE"
    assert t5.status()["independence_candidate_targets"] == 1

    e3 = t4.observe(p2, f2, family="PELL", t2_event="EXACT_DUPLICATE_SAME_PATH", t3_class="EXACT_REFERENCE")
    assert e3 == "EXACT_REPEAT_NOT_CONVERGENCE"
    assert t5.observe(p2, f2, t4_event=e3, t4_summary=t4.target_summary("Z-target")) == "INDEPENDENCE_CANDIDATE"
    s = t5.status()
    assert s["independence_candidate_targets"] == 1
    assert s["exact_repeat_observations"] == 1
    assert s["t4_consistency_conflicts"] == 0
    print("T5_THREE_AXIS=PASS")


def test_two_axis_is_review_only() -> None:
    t4 = T4Convergence(max_targets=32, sigs_per_target=8)
    t5 = T5OperationalIndependence(max_targets=32)
    p1 = packet(200, z="Z-two", origin="Z-o1", parent="Z-p1", formula="PLUS1")
    p2 = packet(200, z="Z-two", origin="Z-o2", parent="Z-p2", formula="DOUBLE")
    f1, f2 = c2_fingerprint(p1), c2_fingerprint(p2)
    e1 = t4.observe(p1, f1, family="ARITHMETIC_EXPANSION", t2_event="UNIQUE", t3_class="ISOLATED")
    t5.observe(p1, f1, t4_event=e1, t4_summary=t4.target_summary("Z-two"))
    e2 = t4.observe(p2, f2, family="ARITHMETIC_EXPANSION", t2_event="UNIQUE", t3_class="NEAR")
    tier = t5.observe(p2, f2, t4_event=e2, t4_summary=t4.target_summary("Z-two"))
    assert tier == "DIVERSE_2_AXES_REVIEW"
    assert t5.status()["independence_candidate_targets"] == 0
    assert t5.status()["two_axis_review_targets"] == 1
    print("T5_TWO_AXIS_REVIEW=PASS")


def make_shared():
    return {
        "c3": C3Library37(), "c4": C4Novelty(), "c5": C5StructuralRarity(),
        "c6": C6Provenance(), "c7": C7ShadowRouter(), "t1": T1FamilyClassifier(),
        "t2": T2ExactDuplicate(max_keys=8192), "t3": T3SemanticNeighborhood(per_family_limit=64),
        "t4": T4Convergence(max_targets=4096, sigs_per_target=16),
        "t5": T5OperationalIndependence(max_targets=4096),
    }


def make_runner(shared):
    return ExperimentRunner(
        build_default_registry(),
        ExperimentSpec(duration_seconds=60, checkpoint_seconds=60, max_depth=8, max_active_branches=64, max_packets=5000),
        papillon_enabled=False, sleeping_pool_enabled=False,
        c3_library=shared["c3"], c4_novelty=shared["c4"], c5_rarity=shared["c5"],
        c6_provenance=shared["c6"], c7_router=shared["c7"], t1_family=shared["t1"],
        t2_duplicate=shared["t2"], t3_neighborhood=shared["t3"],
        t4_convergence=shared["t4"], t5_independence=shared["t5"],
    )


def test_chain_and_rollover() -> None:
    set_env()
    shared = make_shared()
    r1 = make_runner(shared)
    r1.seed(TracePacket(v) for v in (343, 703, 2701, 6337, 11611))
    r1.run_steps(100)
    n = r1.c2_status()["fingerprints"]
    assert n > 0
    statuses = [
        r1.c3_status(), r1.c4_status(), r1.c5_status(), r1.c6_status(), r1.c7_status(),
        r1.t1_status(), r1.t2_status(), r1.t3_status(), r1.t4_status(), r1.t5_status(),
    ]
    assert all(int(s.get("observations") or 0) == n for s in statuses)
    assert r1.t5_status()["scientific_independence_claim"] is False
    assert r1.t5_status()["operational_candidate_only"] is True
    assert r1.t5_status()["t4_consistency_conflicts"] == 0
    assert r1.t5_status()["controls_scheduling"] is False
    assert r1.t5_status()["compute_skips"] == 0
    before_obs = r1.t5_status()["observations"]
    before_candidates = r1.t5_status()["independence_candidate_targets"]
    print("T5_CHAIN=PASS", n, r1.t5_status()["tier_target_counts"])

    r2 = make_runner(shared)
    r2.seed(TracePacket(v) for v in (343, 703, 2701, 6337, 11611))
    r2.run_steps(25)
    assert r2.t5_status()["observations"] > before_obs
    assert r2.t5_status()["independence_candidate_targets"] >= before_candidates
    assert r2.t5_status()["t4_consistency_conflicts"] == 0
    print("T5_ROLLOVER=PASS", before_obs, r2.t5_status()["observations"])


if __name__ == "__main__":
    test_three_axis_candidate_and_exact_repeat()
    test_two_axis_is_review_only()
    test_chain_and_rollover()
    print("T5_INDEPENDENCE=PASS")
