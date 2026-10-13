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


def test_module() -> None:
    t2 = T2ExactDuplicate(max_keys=2)
    a = SimpleNamespace(branch_path="ROOT/A", z_id="Z-A")
    b = SimpleNamespace(branch_path="ROOT/B", z_id="Z-A")

    assert t2.observe(a, "C2-A", family="PELL") == "UNIQUE"
    assert t2.observe(a, "C2-A", family="PELL") == "EXACT_DUPLICATE_SAME_PATH"
    assert t2.observe(b, "C2-A", family="PELL") == "EXACT_DUPLICATE_ALT_PATH"
    assert t2.observe(b, "C2-A", family="REDUCTION") == "EXACT_DUPLICATE_FAMILY_CONFLICT"
    assert t2.observe(a, "C2-B", family="PELL") == "UNIQUE"
    assert t2.observe(a, "C2-C", family="PELL") == "UNTRACKED_CAPACITY"

    s = t2.status()
    assert s["observations"] == 6
    assert s["unique_fingerprints"] == 2
    assert s["exact_duplicates"] == 3
    assert s["same_family_duplicates"] == 2
    assert s["same_path_duplicates"] == 1
    assert s["alternate_path_duplicates"] == 1
    assert s["cross_family_conflicts"] == 1
    assert s["untracked_capacity"] == 1
    assert s["deduplication_applied"] is False
    assert s["packets_collapsed"] == 0
    print("T2_MODULE=PASS")


def set_flags() -> None:
    for name in ("BROTO_C2_ENABLED", "BROTO_C3_ENABLED", "BROTO_C4_ENABLED", "BROTO_C5_ENABLED", "BROTO_C6_ENABLED", "BROTO_C7_ENABLED", "BROTO_T1_ENABLED", "BROTO_T2_ENABLED"):
        os.environ[name] = "1"
    os.environ["BROTO_ZSTAMP_ENABLED"] = "1"
    os.environ["BROTO_ZSTAMP_PERCENT"] = "100"


def make_runner(shared: dict[str, object]) -> ExperimentRunner:
    return ExperimentRunner(
        build_default_registry(),
        ExperimentSpec(duration_seconds=60, checkpoint_seconds=10, max_depth=8, max_active_branches=128, max_packets=20_000),
        c3_library=shared["c3"],
        c4_novelty=shared["c4"],
        c5_rarity=shared["c5"],
        c6_provenance=shared["c6"],
        c7_router=shared["c7"],
        t1_family=shared["t1"],
        t2_duplicate=shared["t2"],
    )


def test_chain_and_rollover() -> None:
    set_flags()
    shared = {
        "c3": C3Library37(),
        "c4": C4Novelty(),
        "c5": C5StructuralRarity(),
        "c6": C6Provenance(),
        "c7": C7ShadowRouter(),
        "t1": T1FamilyClassifier(),
        "t2": T2ExactDuplicate(),
    }

    r1 = make_runner(shared)
    seeds = [TracePacket(343), TracePacket(703), TracePacket(73)]
    r1.seed(seeds)
    for _ in range(50):
        if not r1.step():
            break

    n = int(r1.c2_status()["fingerprints"])
    assert n > 0
    assert n == int(r1.c3_status()["observations"])
    assert n == int(r1.c4_status()["observations"])
    assert n == int(r1.c5_status()["observations"])
    assert n == int(r1.c6_status()["observations"])
    assert n == int(r1.c7_status()["observations"])
    assert n == int(r1.t1_status()["observations"])
    assert n == int(r1.t2_status()["observations"])
    assert r1.t2_status()["deduplication_applied"] is False
    assert int(r1.t2_status()["packets_collapsed"]) == 0
    before = int(r1.t2_status()["exact_duplicates"])
    print("T2_CHAIN=PASS", n, r1.t2_status()["exact_duplicates"])

    r2 = make_runner(shared)
    r2.seed([TracePacket(343), TracePacket(703), TracePacket(73)])
    for _ in range(10):
        if not r2.step():
            break
    after = int(r2.t2_status()["exact_duplicates"])
    assert after > before
    assert int(r2.t2_status()["observations"]) == int(r2.t1_status()["observations"])
    print("T2_ROLLOVER=PASS", before, after)


if __name__ == "__main__":
    test_module()
    test_chain_and_rollover()
    print("T2_EXACT_DUPLICATE=PASS")
