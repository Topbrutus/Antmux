from __future__ import annotations

import os
from dataclasses import replace

from brotoculateur.c3_library import C3Library37
from brotoculateur.c4_novelty import C4Novelty
from brotoculateur.engine import Formula, FormulaRegistry, TracePacket, c2_fingerprint, z_stamp_root
from brotoculateur.orchestrator import ExperimentRunner, ExperimentSpec


def registry() -> FormulaRegistry:
    reg = FormulaRegistry()
    reg.register(Formula("PLUS1", "x+1", "plus", lambda x: x + 1))
    return reg


def classify(lib: C3Library37, c4: C4Novelty, fingerprint: str) -> str:
    hit = lib.observe(fingerprint)
    return c4.observe(fingerprint, c3_hit=hit, c3_retained=lib.contains(fingerprint))


def test_direct_classification() -> None:
    lib = C3Library37(max_entries=100)
    c4 = C4Novelty()
    base = z_stamp_root(TracePacket(343, packet_id="a", parent_id="p1", branch_path="ROOT/A"))
    same = replace(base, packet_id="b", parent_id="p2", branch_path="ROOT/B")
    other = z_stamp_root(TracePacket(344))
    fp1 = c2_fingerprint(base)
    fp_same = c2_fingerprint(same)
    fp2 = c2_fingerprint(other)

    assert classify(lib, c4, fp1) == "NOVEL_CANDIDATE"
    assert classify(lib, c4, fp_same) == "KNOWN"
    assert classify(lib, c4, fp2) == "NOVEL_CANDIDATE"

    status = c4.status()
    assert status["observations"] == 3
    assert status["known"] == 1
    assert status["novel_candidates"] == 2
    assert status["tracked_novel"] == 2
    assert status["untracked_capacity"] == 0
    assert status["scientific_discovery_claim"] is False
    assert status["compute_skips"] == 0
    assert status["proof_promotion"] is False


def test_capacity_is_explicit_not_silently_known() -> None:
    lib = C3Library37(max_entries=37)
    c4 = C4Novelty()
    for value in range(100):
        fp = c2_fingerprint(z_stamp_root(TracePacket(value)))
        classify(lib, c4, fp)
    status = c4.status()
    assert status["observations"] == 100
    assert status["known"] == 0
    assert status["novel_candidates"] == 100
    assert status["tracked_novel"] == 37
    assert status["untracked_capacity"] == 63
    assert len(status["recent_novel_fingerprints"]) == 37


def test_runner_c2_c3_c4_chain() -> None:
    os.environ["BROTO_ZSTAMP_ENABLED"] = "1"
    os.environ["BROTO_ZSTAMP_PERCENT"] = "100"
    os.environ["BROTO_C2_ENABLED"] = "1"
    os.environ["BROTO_C3_ENABLED"] = "1"
    os.environ["BROTO_C4_ENABLED"] = "1"
    lib = C3Library37(max_entries=1000)
    c4 = C4Novelty()
    runner = ExperimentRunner(
        registry(),
        ExperimentSpec(max_depth=1, max_active_branches=32, max_packets=100),
        c3_library=lib,
        c4_novelty=c4,
    )
    runner.seed([TracePacket(343), TracePacket(343), TracePacket(703)])
    runner.run_steps(1)
    c2 = runner.c2_status()
    c3 = runner.c3_status()
    s4 = runner.c4_status()
    assert c2["fingerprints"] == c3["observations"] == s4["observations"]
    assert s4["known"] == c3["hits"]
    assert s4["novel_candidates"] == c3["misses"]
    assert s4["known"] + s4["novel_candidates"] == s4["observations"]
    assert s4["enabled"] is True
    assert s4["authority"] == "SHADOW_ONLY"
    assert s4["compute_skips"] == 0
    print("C4_CHAIN=PASS", s4["observations"], s4["known"], s4["novel_candidates"])


def test_shared_memory_across_runner_rollover() -> None:
    os.environ["BROTO_ZSTAMP_ENABLED"] = "1"
    os.environ["BROTO_ZSTAMP_PERCENT"] = "100"
    os.environ["BROTO_C2_ENABLED"] = "1"
    os.environ["BROTO_C3_ENABLED"] = "1"
    os.environ["BROTO_C4_ENABLED"] = "1"
    lib = C3Library37(max_entries=1000)
    c4 = C4Novelty()
    spec = ExperimentSpec(max_depth=1, max_active_branches=32, max_packets=100)

    r1 = ExperimentRunner(registry(), spec, c3_library=lib, c4_novelty=c4)
    r1.seed([TracePacket(343)])
    s1 = r1.c4_status()
    assert s1["novel_candidates"] == 1 and s1["known"] == 0

    r2 = ExperimentRunner(registry(), spec, c3_library=lib, c4_novelty=c4)
    r2.seed([TracePacket(343)])
    s2 = r2.c4_status()
    assert s2["observations"] == 2
    assert s2["novel_candidates"] == 1
    assert s2["known"] == 1
    assert lib.status()["unique_entries"] == 1
    print("C4_ROLLOVER=PASS", s2["observations"], s2["known"], s2["novel_candidates"])


def main() -> None:
    test_direct_classification()
    test_capacity_is_explicit_not_silently_known()
    test_runner_c2_c3_c4_chain()
    test_shared_memory_across_runner_rollover()
    print("C4_NOVELTY=PASS")


if __name__ == "__main__":
    main()
