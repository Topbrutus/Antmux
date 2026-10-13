from __future__ import annotations

import os

from brotoculateur.c3_library import C3Library37
from brotoculateur.c4_novelty import C4Novelty
from brotoculateur.c5_rarity import C5StructuralRarity
from brotoculateur.c6_provenance import C6Provenance
from brotoculateur.c7_router import C7ShadowRouter
from brotoculateur.dashboard import build_default_registry
from brotoculateur.engine import TracePacket, c2_fingerprint, z_stamp_root
from brotoculateur.orchestrator import ExperimentRunner, ExperimentSpec
from brotoculateur.t1_family import T1FamilyClassifier
from brotoculateur.t2_exact_duplicate import T2ExactDuplicate
from brotoculateur.t3_neighborhood import SemanticRep, T3SemanticNeighborhood


def set_env() -> None:
    for name in ("BROTO_C2_ENABLED", "BROTO_C3_ENABLED", "BROTO_C4_ENABLED", "BROTO_C5_ENABLED", "BROTO_C6_ENABLED", "BROTO_C7_ENABLED", "BROTO_T1_ENABLED", "BROTO_T2_ENABLED", "BROTO_T3_ENABLED"):
        os.environ[name] = "1"
    os.environ["BROTO_ZSTAMP_ENABLED"] = "1"
    os.environ["BROTO_ZSTAMP_PERCENT"] = "100"


def test_metric() -> None:
    a = SemanticRep("C2-a", "PELL", 1000, 4, ("PLUS1", "PELL_N"), "EXACT")
    b = SemanticRep("C2-b", "PELL", 1001, 4, ("DOUBLE", "PELL_N"), "EXACT")
    c = SemanticRep("C2-c", "REDUCTION", 1001, 4, ("DOUBLE", "PELL_N"), "EXACT")
    assert T3SemanticNeighborhood.similarity(a, b) >= 80
    assert T3SemanticNeighborhood.similarity(a, c) == 0
    assert T3SemanticNeighborhood.classify_score(80) == "NEAR"
    assert T3SemanticNeighborhood.classify_score(60) == "ADJACENT"
    assert T3SemanticNeighborhood.classify_score(59) == "DISTANT"
    print("T3_METRIC=PASS")


def test_same_value_distinct_c2() -> None:
    t3 = T3SemanticNeighborhood(per_family_limit=8)
    p1 = z_stamp_root(TracePacket(10, depth=1, formula_chain=("PLUS1",)))
    p2 = z_stamp_root(TracePacket(10, depth=1, formula_chain=("DOUBLE",)))
    f1, f2 = c2_fingerprint(p1), c2_fingerprint(p2)
    assert f1 != f2
    t3.observe(p1, f1, family="ARITHMETIC_EXPANSION", t2_event="UNIQUE")
    t3.observe(p2, f2, family="ARITHMETIC_EXPANSION", t2_event="UNIQUE")
    s = t3.status()
    assert s["same_value_distinct_c2"] == 1
    assert s["hash_distance_used"] is False
    print("T3_SAME_VALUE_DISTINCT_C2=PASS")


def make_shared():
    return {
        "c3": C3Library37(),
        "c4": C4Novelty(),
        "c5": C5StructuralRarity(),
        "c6": C6Provenance(),
        "c7": C7ShadowRouter(),
        "t1": T1FamilyClassifier(),
        "t2": T2ExactDuplicate(max_keys=4096),
        "t3": T3SemanticNeighborhood(per_family_limit=64),
    }


def make_runner(shared):
    return ExperimentRunner(
        build_default_registry(),
        ExperimentSpec(duration_seconds=60, checkpoint_seconds=60, max_depth=8, max_active_branches=64, max_packets=4000),
        papillon_enabled=False,
        sleeping_pool_enabled=False,
        c3_library=shared["c3"], c4_novelty=shared["c4"], c5_rarity=shared["c5"],
        c6_provenance=shared["c6"], c7_router=shared["c7"], t1_family=shared["t1"],
        t2_duplicate=shared["t2"], t3_neighborhood=shared["t3"],
    )


def test_chain_and_rollover() -> None:
    set_env()
    shared = make_shared()
    r1 = make_runner(shared)
    r1.seed(TracePacket(v) for v in (343, 703, 2701, 6337, 11611))
    r1.run_steps(80)
    n = r1.c2_status()["fingerprints"]
    assert n > 0
    assert n == r1.c3_status()["observations"] == r1.c4_status()["observations"]
    assert n == r1.c5_status()["observations"] == r1.c6_status()["observations"]
    assert n == r1.c7_status()["observations"] == r1.t1_status()["observations"]
    assert n == r1.t2_status()["observations"] == r1.t3_status()["observations"]
    assert r1.t2_status()["exact_duplicates"] == r1.t3_status()["exact_references"]
    assert r1.t2_status()["cross_family_conflicts"] == 0
    assert sum(r1.t3_status()["class_counts"].values()) == n
    assert r1.t3_status()["hash_distance_used"] is False
    assert r1.t3_status()["compute_skips"] == 0
    before = r1.t3_status()["exact_references"]
    print("T3_CHAIN=PASS", n, r1.t3_status()["class_counts"])

    r2 = make_runner(shared)
    r2.seed(TracePacket(v) for v in (343, 703, 2701, 6337, 11611))
    r2.run_steps(20)
    after = r2.t3_status()["exact_references"]
    assert after > before
    assert r2.t2_status()["cross_family_conflicts"] == 0
    print("T3_ROLLOVER=PASS", before, after)


if __name__ == "__main__":
    test_metric()
    test_same_value_distinct_c2()
    test_chain_and_rollover()
    print("T3_NEIGHBORHOOD=PASS")
