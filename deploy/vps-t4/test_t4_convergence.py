from __future__ import annotations

import os
from types import SimpleNamespace

from brotoculateur.c3_library import C3Library37
from brotoculateur.c4_novelty import C4Novelty
from brotoculateur.c5_rarity import C5StructuralRarity
from brotoculateur.c6_provenance import C6Provenance
from brotoculateur.c7_router import C7ShadowRouter
from brotoculateur.dashboard import build_default_registry
from brotoculateur.engine import TracePacket
from brotoculateur.orchestrator import ExperimentRunner, ExperimentSpec
from brotoculateur.t1_family import T1FamilyClassifier
from brotoculateur.t2_exact_duplicate import T2ExactDuplicate
from brotoculateur.t3_neighborhood import T3SemanticNeighborhood
from brotoculateur.t4_convergence import T4Convergence


def set_env() -> None:
    for name in (
        "BROTO_C2_ENABLED", "BROTO_C3_ENABLED", "BROTO_C4_ENABLED", "BROTO_C5_ENABLED",
        "BROTO_C6_ENABLED", "BROTO_C7_ENABLED", "BROTO_T1_ENABLED", "BROTO_T2_ENABLED",
        "BROTO_T3_ENABLED", "BROTO_T4_ENABLED",
    ):
        os.environ[name] = "1"
    os.environ["BROTO_ZSTAMP_ENABLED"] = "1"
    os.environ["BROTO_ZSTAMP_PERCENT"] = "100"


def packet(z: str, origin: str, parent: str | None) -> SimpleNamespace:
    return SimpleNamespace(z_id=z, z_origin_id=origin, z_parent_id=parent)


def test_semantics() -> None:
    t4 = T4Convergence(max_targets=37, sigs_per_target=8)
    p1 = packet("Z-target", "Z-origin-a", None)
    p2 = packet("Z-target", "Z-origin-a", "Z-parent-b")
    p3 = packet("Z-target", "Z-origin-c", "Z-parent-c")

    assert t4.observe(p1, "C2-aaa", family="PELL", t2_event="UNIQUE", t3_class="ISOLATED") == "FIRST_STRUCTURE"
    assert t4.observe(p1, "C2-aaa", family="PELL", t2_event="EXACT_DUPLICATE_ALT_PATH", t3_class="EXACT_REFERENCE") == "EXACT_REPEAT_NOT_CONVERGENCE"
    e2 = t4.observe(p2, "C2-bbb", family="PELL", t2_event="UNIQUE", t3_class="NEAR")
    assert e2.startswith("STRUCTURAL_CONVERGENCE")
    e3 = t4.observe(p3, "C2-ccc", family="REDUCTION", t2_event="UNIQUE", t3_class="ADJACENT")
    assert e3.startswith("STRUCTURAL_CONVERGENCE") and "CROSS_FAMILY" in e3 and "MULTI_ORIGIN" in e3

    s = t4.status()
    assert s["observations"] == 4
    assert s["exact_repeat_observations"] == 1
    assert s["distinct_structure_observations"] == 3
    assert s["structural_convergence_events"] == 2
    assert s["convergent_targets"] == 1
    assert s["cross_family_convergence_events"] == 1
    assert s["multi_origin_convergence_events"] == 1
    assert s["multi_parent_convergence_events"] == 2
    assert s["t2_consistency_conflicts"] == 0
    assert s["t3_consistency_conflicts"] == 0
    assert s["exact_duplicate_counts_as_convergence"] is False
    print("T4_SEMANTICS=PASS")


def test_capacity_does_not_fake_conflict() -> None:
    t4 = T4Convergence(max_targets=37, sigs_per_target=2)
    p = packet("Z-cap", "Z-o", "Z-p")
    t4.observe(p, "C2-a", family="PELL", t2_event="UNIQUE", t3_class="ISOLATED")
    t4.observe(p, "C2-b", family="PELL", t2_event="UNIQUE", t3_class="NEAR")
    t4.observe(p, "C2-c", family="PELL", t2_event="UNIQUE", t3_class="NEAR")
    t4.observe(p, "C2-c", family="PELL", t2_event="EXACT_DUPLICATE_ALT_PATH", t3_class="EXACT_REFERENCE")
    s = t4.status()
    assert s["signature_capacity_events"] == 2
    assert s["t2_consistency_conflicts"] == 0
    assert s["t3_consistency_conflicts"] == 0
    print("T4_CAPACITY_GUARD=PASS")


def make_shared():
    return {
        "c3": C3Library37(), "c4": C4Novelty(), "c5": C5StructuralRarity(),
        "c6": C6Provenance(), "c7": C7ShadowRouter(), "t1": T1FamilyClassifier(),
        "t2": T2ExactDuplicate(max_keys=4096), "t3": T3SemanticNeighborhood(per_family_limit=64),
        "t4": T4Convergence(max_targets=4096, sigs_per_target=32),
    }


def make_runner(shared):
    return ExperimentRunner(
        build_default_registry(),
        ExperimentSpec(duration_seconds=60, checkpoint_seconds=60, max_depth=8, max_active_branches=64, max_packets=4000),
        papillon_enabled=False, sleeping_pool_enabled=False,
        c3_library=shared["c3"], c4_novelty=shared["c4"], c5_rarity=shared["c5"],
        c6_provenance=shared["c6"], c7_router=shared["c7"], t1_family=shared["t1"],
        t2_duplicate=shared["t2"], t3_neighborhood=shared["t3"], t4_convergence=shared["t4"],
    )


def test_chain_and_rollover() -> None:
    set_env()
    shared = make_shared()
    r1 = make_runner(shared)
    r1.seed(TracePacket(v) for v in (343, 703, 2701, 6337, 11611))
    r1.run_steps(100)
    n = r1.c2_status()["fingerprints"]
    assert n > 0
    assert n == r1.c3_status()["observations"] == r1.c4_status()["observations"]
    assert n == r1.c5_status()["observations"] == r1.c6_status()["observations"]
    assert n == r1.c7_status()["observations"] == r1.t1_status()["observations"]
    assert n == r1.t2_status()["observations"] == r1.t3_status()["observations"] == r1.t4_status()["observations"]
    s1 = r1.t4_status()
    assert s1["t2_consistency_conflicts"] == 0 and s1["t3_consistency_conflicts"] == 0
    assert s1["structural_convergence_events"] > 0
    assert s1["exact_duplicate_counts_as_convergence"] is False
    assert s1["compute_skips"] == 0 and s1["proof_promotion"] is False
    before = s1["structural_convergence_events"]
    print("T4_CHAIN=PASS", n, s1["tracked_targets"], before, s1["convergence_by_t3_class"])

    r2 = make_runner(shared)
    r2.seed(TracePacket(v) for v in (343, 703, 2701, 6337, 11611))
    r2.run_steps(30)
    s2 = r2.t4_status()
    assert s2["observations"] > n
    assert s2["structural_convergence_events"] >= before
    assert s2["t2_consistency_conflicts"] == 0 and s2["t3_consistency_conflicts"] == 0
    print("T4_ROLLOVER=PASS", before, s2["structural_convergence_events"])


if __name__ == "__main__":
    test_semantics()
    test_capacity_does_not_fake_conflict()
    test_chain_and_rollover()
    print("T4_CONVERGENCE=PASS")
