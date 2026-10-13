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
from brotoculateur.papillon_engine import Papillon144
from brotoculateur.t1_family import T1FamilyClassifier
from brotoculateur.t2_exact_duplicate import T2ExactDuplicate
from brotoculateur.t3_neighborhood import T3SemanticNeighborhood
from brotoculateur.t4_convergence import T4Convergence
from brotoculateur.t5_independence import T5OperationalIndependence
from brotoculateur.t6_papillon import AFFINITY_BY_T5, T6PapillonAffinity


def set_env() -> None:
    for name in ("BROTO_C2_ENABLED", "BROTO_C3_ENABLED", "BROTO_C4_ENABLED", "BROTO_C5_ENABLED", "BROTO_C6_ENABLED", "BROTO_C7_ENABLED", "BROTO_T1_ENABLED", "BROTO_T2_ENABLED", "BROTO_T3_ENABLED", "BROTO_T4_ENABLED", "BROTO_T5_ENABLED", "BROTO_T6_ENABLED"):
        os.environ[name] = "1"
    os.environ["BROTO_ZSTAMP_ENABLED"] = "1"
    os.environ["BROTO_ZSTAMP_PERCENT"] = "100"


def test_public_index_is_pure() -> None:
    pap = Papillon144()
    before = pap.status()
    rows = [("ROOT", 343), ("PELL_Q", 73), ("PLUS1", 6337), ("DOUBLE", -47)]
    indexes = [pap.shard_index(fid, value) for fid, value in rows]
    assert all(0 <= idx < 144 for idx in indexes)
    assert indexes == [pap.shard_index(fid, value) for fid, value in rows]
    after = pap.status()
    assert after == before
    print("T6_PUBLIC_INDEX_PURE=PASS", indexes)


def test_affinity_is_read_only() -> None:
    pap = Papillon144()
    t6 = T6PapillonAffinity()
    tiers = list(AFFINITY_BY_T5)
    for i, tier in enumerate(tiers, 1):
        packet = z_stamp_root(TracePacket(100 + i, formula_chain=("PLUS1",)))
        fingerprint = c2_fingerprint(packet)
        before = pap.status()
        affinity = t6.observe(packet, fingerprint, t5_tier=tier, papillon=pap)
        assert affinity == AFFINITY_BY_T5[tier]
        assert pap.status() == before
    s = t6.status()
    assert s["observations"] == len(tiers)
    assert s["candidate_observations"] == 1
    assert s["shard_count"] == 144
    assert s["actual_papillon_routes_applied"] == 0
    assert s["papillon_cache_mutated"] is False
    assert s["controls_papillon"] is False
    print("T6_READ_ONLY=PASS", s["shards_touched"], s["candidate_shards"])


def make_shared():
    return {
        "c3": C3Library37(), "c4": C4Novelty(), "c5": C5StructuralRarity(),
        "c6": C6Provenance(), "c7": C7ShadowRouter(), "t1": T1FamilyClassifier(),
        "t2": T2ExactDuplicate(max_keys=4096), "t3": T3SemanticNeighborhood(per_family_limit=64),
        "t4": T4Convergence(max_targets=4096, sigs_per_target=16),
        "t5": T5OperationalIndependence(max_targets=4096), "t6": T6PapillonAffinity(),
    }


def make_runner(shared):
    return ExperimentRunner(
        build_default_registry(),
        ExperimentSpec(duration_seconds=60, checkpoint_seconds=60, max_depth=8, max_active_branches=64, max_packets=6000),
        papillon_enabled=True, sleeping_pool_enabled=False,
        c3_library=shared["c3"], c4_novelty=shared["c4"], c5_rarity=shared["c5"],
        c6_provenance=shared["c6"], c7_router=shared["c7"], t1_family=shared["t1"],
        t2_duplicate=shared["t2"], t3_neighborhood=shared["t3"], t4_convergence=shared["t4"],
        t5_independence=shared["t5"], t6_papillon=shared["t6"],
    )


def test_chain_and_rollover() -> None:
    set_env()
    shared = make_shared()
    r1 = make_runner(shared)
    r1.seed(TracePacket(v) for v in (343, 703, 2701, 6337, 11611))
    r1.run_steps(100)
    n = r1.c2_status()["fingerprints"]
    assert n > 0
    assert n == r1.t4_status()["observations"] == r1.t5_status()["observations"] == r1.t6_status()["observations"]
    t5 = r1.t5_status(); t6 = r1.t6_status()
    assert t6["t5_tier_counts"] == t5["tier_observation_counts"]
    assert t6["shard_count"] == 144 and 0 < t6["shards_touched"] <= 144
    assert t6["actual_papillon_routes_applied"] == 0
    assert t6["compute_skips"] == 0 and t6["proof_promotion"] is False
    before = t6["observations"]
    print("T6_CHAIN=PASS", n, t6["shards_touched"], t6["affinity_counts"])

    r2 = make_runner(shared)
    r2.seed(TracePacket(v) for v in (343, 703, 2701, 6337, 11611))
    r2.run_steps(20)
    after = r2.t6_status()["observations"]
    assert after > before
    assert r2.t6_status()["t5_tier_counts"] == r2.t5_status()["tier_observation_counts"]
    print("T6_ROLLOVER=PASS", before, after)


if __name__ == "__main__":
    test_public_index_is_pure()
    test_affinity_is_read_only()
    test_chain_and_rollover()
    print("T6_PAPILLON=PASS")