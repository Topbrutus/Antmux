from __future__ import annotations

import os
import tempfile
from dataclasses import replace
from pathlib import Path

from brotoculateur.c3_library import C3Library37
from brotoculateur.dashboard import DashboardService
from brotoculateur.engine import Formula, FormulaRegistry, TracePacket, c2_fingerprint, z_stamp_root
from brotoculateur.orchestrator import ExperimentRunner, ExperimentSpec


def registry() -> FormulaRegistry:
    reg = FormulaRegistry()
    reg.register(Formula("PLUS1", "x+1", "plus", lambda x: x + 1))
    return reg


def test_direct_library() -> None:
    lib = C3Library37(max_entries=100)
    base = z_stamp_root(TracePacket(343, packet_id="a", parent_id="p1", branch_path="ROOT/A"))
    same = replace(base, packet_id="b", parent_id="p2", branch_path="ROOT/B")
    other = replace(base, value=344, z_id="Z-other")
    fp1 = c2_fingerprint(base)
    fp_same = c2_fingerprint(same)
    fp2 = c2_fingerprint(other)
    assert fp1 == fp_same
    assert fp1 != fp2
    assert lib.observe(fp1) is False
    assert lib.observe(fp_same) is True
    assert lib.observe(fp2) is False
    status = lib.status()
    assert status["bucket_count"] == 37
    assert len(status["bucket_occupancy"]) == 37
    assert status["observations"] == 3
    assert status["hits"] == 1
    assert status["misses"] == 2
    assert status["unique_entries"] == 2
    assert status["compute_skips"] == 0
    assert status["authority"] == "SHADOW_ONLY"
    assert lib.contains(fp1)
    assert lib.count(fp1) == 2


def test_capacity_bound() -> None:
    lib = C3Library37(max_entries=37)
    for value in range(100):
        packet = z_stamp_root(TracePacket(value))
        lib.observe(c2_fingerprint(packet))
    status = lib.status()
    assert status["unique_entries"] == 37
    assert status["capacity_rejections"] == 63
    assert status["hits"] + status["misses"] == status["observations"]
    assert status["unique_entries"] <= status["max_entries"]


def test_runner_c2_to_c3_canary() -> None:
    os.environ["BROTO_ZSTAMP_ENABLED"] = "1"
    os.environ["BROTO_ZSTAMP_PERCENT"] = "10"
    os.environ["BROTO_C2_ENABLED"] = "1"
    os.environ["BROTO_C3_ENABLED"] = "1"
    library = C3Library37(max_entries=1000)
    runner = ExperimentRunner(
        registry(),
        ExperimentSpec(max_depth=1, max_active_branches=32, max_packets=100),
        c3_library=library,
    )
    values = [343, 703, 2701, 6337, 11611]
    runner.seed(TracePacket(value, packet_id=f"p{value}") for value in values)
    c2_before = runner.c2_status()
    c3_before = runner.c3_status()
    assert c2_before["roots_fingerprinted"] == 1
    assert c3_before["observations"] == 1
    assert c3_before["misses"] == 1
    runner.run_steps(1)
    c2 = runner.c2_status()
    c3 = runner.c3_status()
    assert c2["fingerprints"] > 1
    assert c3["observations"] == c2["fingerprints"]
    assert c3["hits"] + c3["misses"] == c3["observations"]
    assert c3["query_before_compute"] is False
    assert c3["compute_skips"] == 0
    print("C3_CANARY_10=PASS", c2["fingerprints"], c3["observations"], c3["hits"], c3["unique_entries"])


def test_library_survives_runner_rollover() -> None:
    os.environ["BROTO_ZSTAMP_ENABLED"] = "1"
    os.environ["BROTO_ZSTAMP_PERCENT"] = "10"
    os.environ["BROTO_C2_ENABLED"] = "1"
    os.environ["BROTO_C3_ENABLED"] = "1"
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
            first = service.status()["c3_library"]
            assert first["observations"] == 1, first
            library_id = id(service.c3_library)
            with service._lock:
                service._zstamp_rollup_unlocked()
                service._c2_rollup_unlocked()
                service._runner = service._new_runner((343,))
            second = service.status()["c3_library"]
            assert id(service.c3_library) == library_id
            assert second["observations"] == 2, second
            assert second["hits"] == 1, second
            assert second["unique_entries"] == 1, second
            print("C3_ROLLOVER=PASS", second["observations"], second["hits"], second["unique_entries"])
        finally:
            service.close()


def main() -> None:
    test_direct_library()
    test_capacity_bound()
    test_runner_c2_to_c3_canary()
    test_library_survives_runner_rollover()
    print("C3_LIBRARY37=PASS")


if __name__ == "__main__":
    main()
