from __future__ import annotations

import os

from brotoculateur.c3_library import C3Library37
from brotoculateur.c4_novelty import C4Novelty
from brotoculateur.c5_rarity import C5StructuralRarity
from brotoculateur.c6_provenance import C6Provenance
from brotoculateur.c7_router import C7ShadowRouter
from brotoculateur.dashboard import build_default_registry
from brotoculateur.engine import TracePacket, z_stamp_root
from brotoculateur.orchestrator import ExperimentRunner, ExperimentSpec


def configure() -> None:
    os.environ["BROTO_ZSTAMP_ENABLED"] = "1"
    os.environ["BROTO_ZSTAMP_PERCENT"] = "100"
    os.environ["BROTO_C2_ENABLED"] = "1"
    os.environ["BROTO_C3_ENABLED"] = "1"
    os.environ["BROTO_C4_ENABLED"] = "1"
    os.environ["BROTO_C5_ENABLED"] = "1"
    os.environ["BROTO_C6_ENABLED"] = "1"
    os.environ["BROTO_C7_ENABLED"] = "1"


def make_runner(shared: tuple[C3Library37, C4Novelty, C5StructuralRarity, C6Provenance, C7ShadowRouter]) -> ExperimentRunner:
    c3, c4, c5, c6, c7 = shared
    return ExperimentRunner(
        build_default_registry(),
        ExperimentSpec(duration_seconds=60, checkpoint_seconds=10, max_depth=4, max_active_branches=64, max_packets=1000),
        papillon_enabled=False,
        c3_library=c3,
        c4_novelty=c4,
        c5_rarity=c5,
        c6_provenance=c6,
        c7_router=c7,
    )


def test_decisions() -> None:
    r = C7ShadowRouter
    assert r.recommend(c3_hit=False, c3_retained=False, c5_class=None, c6=None)[0] == "CAPACITY_REVIEW"
    assert r.recommend(c3_hit=True, c3_retained=True, c5_class="RARE_8", c6={"operational_independence_candidate": True})[0] == "PROVENANCE_REVIEW"
    assert r.recommend(c3_hit=False, c3_retained=True, c5_class="RARE_8", c6={})[0] == "NOVELTY_REVIEW"
    assert r.recommend(c3_hit=True, c3_retained=True, c5_class="SCARCE_4", c6={})[0] == "RARE_REPLAY"
    assert r.recommend(c3_hit=True, c3_retained=True, c5_class="CONVERGENT_2", c6={})[0] == "CONVERGENCE_REVIEW"
    assert r.recommend(c3_hit=True, c3_retained=True, c5_class="COMMON_1_CONTROL", c6={})[0] == "KNOWN_CONTROL"
    print("C7_DECISIONS=PASS")


def test_c6_public_summary() -> None:
    c6 = C6Provenance(max_targets=100, signature_cap=16)
    p = z_stamp_root(TracePacket(777))
    c6.observe(p, "C2-" + "a" * 64, c3_retained=True, c5_class="RARE_8")
    s = c6.target_summary(p.z_id)
    assert s and s["z_id"] == p.z_id and s["observations"] == 1
    assert s["distinct_c2"] == 1 and s["operational_independence_candidate"] is False
    print("C7_C6_PUBLIC_SUMMARY=PASS")


def test_chain_and_rollover() -> None:
    configure()
    shared = (C3Library37(), C4Novelty(), C5StructuralRarity(), C6Provenance(max_targets=1000, signature_cap=16), C7ShadowRouter())
    r1 = make_runner(shared)
    r1.seed([TracePacket(343), TracePacket(703)])
    for _ in range(6):
        if not r1.step():
            break
    c2 = r1.c2_status(); c3 = r1.c3_status(); c4 = r1.c4_status(); c5 = r1.c5_status(); c6 = r1.c6_status(); c7 = r1.c7_status()
    n = int(c2["fingerprints"])
    assert n > 0
    assert n == int(c3["observations"]) == int(c4["observations"]) == int(c5["observations"]) == int(c6["observations"]) == int(c7["observations"])
    assert int(c7["actual_routes_applied"]) == 0
    assert c7["controls_scheduling"] is False and c7["proof_promotion"] is False
    before = int(c7["observations"])

    r2 = make_runner(shared)
    r2.seed([TracePacket(343)])
    after = int(r2.c7_status()["observations"])
    assert after == before + 1
    assert sum(r2.c7_status()["route_counts"].values()) == after
    print("C7_CHAIN=PASS", n, r2.c7_status()["route_counts"])
    print("C7_ROLLOVER=PASS", before, after)


if __name__ == "__main__":
    test_decisions()
    test_c6_public_summary()
    test_chain_and_rollover()
    print("C7_SHADOW_ROUTER=PASS")

