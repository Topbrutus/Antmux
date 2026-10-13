from __future__ import annotations

import os
import tempfile
from pathlib import Path

from brotoculateur.c3_library import C3Library37
from brotoculateur.c4_novelty import C4Novelty
from brotoculateur.c5_rarity import C5StructuralRarity
from brotoculateur.dashboard import DashboardService
from brotoculateur.engine import Formula, FormulaRegistry, TracePacket
from brotoculateur.orchestrator import ExperimentRunner, ExperimentSpec


def registry() -> FormulaRegistry:
    reg = FormulaRegistry()
    reg.register(Formula("PLUS1", "x+1", "plus", lambda x: x + 1))
    return reg


def enable_chain() -> None:
    os.environ["BROTO_ZSTAMP_ENABLED"] = "1"
    os.environ["BROTO_ZSTAMP_PERCENT"] = "10"
    os.environ["BROTO_C2_ENABLED"] = "1"
    os.environ["BROTO_C3_ENABLED"] = "1"
    os.environ["BROTO_C4_ENABLED"] = "1"
    os.environ["BROTO_C5_ENABLED"] = "1"


def test_tier_boundaries() -> None:
    c5 = C5StructuralRarity()
    fp = "C2-" + "ab" * 32
    expected = {
        1: "RARE_8", 2: "RARE_8",
        3: "RARE_6", 4: "RARE_6",
        5: "SCARCE_4", 8: "SCARCE_4",
        9: "CONVERGENT_2", 16: "CONVERGENT_2",
        17: "COMMON_1_CONTROL", 33: "COMMON_1_CONTROL",
    }
    for count, label in expected.items():
        got = c5.observe(fp, observation_count=count, c3_retained=True)
        assert got == label, (count, got, label)
    s = c5.status()
    assert s["controls_scheduling"] is False
    assert s["reference_rights_applied"] is False
    assert s["compute_skips"] == 0
    assert s["proof_promotion"] is False


def test_untracked_capacity() -> None:
    c5 = C5StructuralRarity()
    fp = "C2-" + "cd" * 32
    assert c5.observe(fp, observation_count=0, c3_retained=False) == "UNTRACKED_CAPACITY"
    s = c5.status()
    assert s["observations"] == 1
    assert s["retained_observations"] == 0
    assert s["untracked_capacity"] == 1


def test_chain_c2_c3_c4_c5() -> None:
    enable_chain()
    c3 = C3Library37(max_entries=1000)
    c4 = C4Novelty()
    c5 = C5StructuralRarity()
    runner = ExperimentRunner(
        registry(),
        ExperimentSpec(max_depth=2, max_active_branches=64, max_packets=500),
        c3_library=c3,
        c4_novelty=c4,
        c5_rarity=c5,
    )
    values = [343, 703, 2701, 6337, 11611]
    runner.seed(TracePacket(value, packet_id=f"p{value}") for value in values)
    runner.run_steps(20)
    c2s = runner.c2_status()
    c3s = runner.c3_status()
    c4s = runner.c4_status()
    c5s = runner.c5_status()
    n = int(c2s["fingerprints"])
    assert n > 1
    assert c3s["observations"] == n
    assert c4s["observations"] == n
    assert c5s["observations"] == n
    assert c4s["known"] == c3s["hits"]
    assert c4s["novel_candidates"] == c3s["misses"]
    assert sum(c5s["class_counts"].values()) + c5s["untracked_capacity"] == n
    assert c5s["controls_scheduling"] is False
    assert c5s["reference_rights_applied"] is False
    print("C5_CHAIN=PASS", n, c3s["hits"], c3s["misses"], c5s["class_counts"])


def test_survives_runner_rollover() -> None:
    enable_chain()
    os.environ["BROTO_C3_MAX_ENTRIES"] = "1000"
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        service = DashboardService(
            Path(tmp) / "store",
            spec=ExperimentSpec(duration_seconds=60, max_depth=1, max_active_branches=32, max_packets=200),
            tick_seconds=0.01,
            sleeping_pool_enabled=True,
        )
        try:
            service.reset((343, 703, 2701, 6337, 11611))
            first = service.status()
            assert first["c3_library"]["observations"] == 1
            assert first["c4_novelty"]["novel_candidates"] == 1
            assert first["c5_rarity"]["class_counts"]["RARE_8"] == 1
            ids = (id(service.c3_library), id(service.c4_novelty), id(service.c5_rarity))
            with service._lock:
                service._zstamp_rollup_unlocked()
                service._c2_rollup_unlocked()
                service._runner = service._new_runner((343,))
            second = service.status()
            assert (id(service.c3_library), id(service.c4_novelty), id(service.c5_rarity)) == ids
            assert second["c3_library"]["observations"] == 2
            assert second["c3_library"]["hits"] == 1
            assert second["c4_novelty"]["known"] == 1
            assert second["c5_rarity"]["observations"] == 2
            assert second["c5_rarity"]["class_counts"]["RARE_8"] == 2
            assert second["c5_rarity"]["max_observation_count"] == 2
            print("C5_ROLLOVER=PASS", second["c5_rarity"]["observations"], second["c5_rarity"]["max_observation_count"])
        finally:
            service.close()


def main() -> None:
    test_tier_boundaries()
    test_untracked_capacity()
    test_chain_c2_c3_c4_c5()
    test_survives_runner_rollover()
    print("C5_STRUCTURAL_RARITY=PASS")


if __name__ == "__main__":
    main()
