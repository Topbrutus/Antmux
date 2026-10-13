from __future__ import annotations

import os
import tempfile
from dataclasses import replace
from pathlib import Path

from brotoculateur.c3_library import C3Library37
from brotoculateur.c4_novelty import C4Novelty
from brotoculateur.c5_rarity import C5StructuralRarity
from brotoculateur.c6_provenance import C6Provenance
from brotoculateur.dashboard import DashboardService
from brotoculateur.engine import Formula, FormulaRegistry, TracePacket, c2_fingerprint, z_identity_for_value, z_stamp_root
from brotoculateur.orchestrator import ExperimentRunner, ExperimentSpec


def registry() -> FormulaRegistry:
    reg = FormulaRegistry()
    reg.register(Formula("PLUS1", "x+1", "plus", lambda x: x + 1))
    reg.register(Formula("DOUBLE", "2x", "double", lambda x: x * 2))
    return reg


def test_multi_origin_convergence() -> None:
    c6 = C6Provenance(max_targets=100, signature_cap=16)
    z = z_identity_for_value(777)
    a = TracePacket(777, branch_path="ROOT/A/Y:T", formula_chain=("PLUS1",), z_id=z, z_parent_id="Z-parent-a", z_origin_id="Z-origin-a")
    b = TracePacket(777, branch_path="ROOT/B/Y:E", formula_chain=("DOUBLE",), z_id=z, z_parent_id="Z-parent-b", z_origin_id="Z-origin-b")
    fa, fb = c2_fingerprint(a), c2_fingerprint(b)
    assert fa != fb
    c6.observe(a, fa, c3_retained=True, c5_class="RARE_8")
    s1 = c6.status()
    assert s1["tracked_targets"] == 1
    assert s1["operational_independence_candidate_targets"] == 0
    c6.observe(b, fb, c3_retained=True, c5_class="RARE_8")
    s2 = c6.status()
    assert s2["tracked_targets"] == 1
    assert s2["multi_path_targets"] == 1
    assert s2["multi_formula_targets"] == 1
    assert s2["multi_parent_targets"] == 1
    assert s2["multi_origin_targets"] == 1
    assert s2["operational_independence_candidate_targets"] == 1
    assert s2["scientific_independence_claim"] is False
    print("C6_MULTI_ORIGIN=PASS", s2["tracked_targets"], s2["operational_independence_candidate_targets"])


def test_parent_formula_candidate_without_multi_origin() -> None:
    c6 = C6Provenance(max_targets=100, signature_cap=16)
    z = z_identity_for_value(888)
    a = TracePacket(888, branch_path="ROOT/A", formula_chain=("PLUS1",), z_id=z, z_parent_id="Z-pa", z_origin_id="Z-origin")
    b = TracePacket(888, branch_path="ROOT/B", formula_chain=("DOUBLE",), z_id=z, z_parent_id="Z-pb", z_origin_id="Z-origin")
    c6.observe(a, c2_fingerprint(a), c3_retained=True, c5_class="RARE_8")
    c6.observe(b, c2_fingerprint(b), c3_retained=True, c5_class="RARE_8")
    s = c6.status()
    assert s["multi_origin_targets"] == 0
    assert s["multi_parent_targets"] == 1
    assert s["multi_formula_targets"] == 1
    assert s["operational_independence_candidate_targets"] == 1
    print("C6_PARENT_FORMULA=PASS")


def test_capacity_bound() -> None:
    c6 = C6Provenance(max_targets=37, signature_cap=2)
    for value in range(100):
        p = z_stamp_root(TracePacket(value))
        c6.observe(p, c2_fingerprint(p), c3_retained=True, c5_class="RARE_8")
    s = c6.status()
    assert s["tracked_targets"] == 37
    assert s["untracked_capacity"] == 63
    assert s["compute_skips"] == 0
    assert s["controls_scheduling"] is False
    assert s["proof_promotion"] is False
    print("C6_CAPACITY=PASS", s["tracked_targets"], s["untracked_capacity"])


def test_full_chain_canary() -> None:
    os.environ["BROTO_ZSTAMP_ENABLED"] = "1"
    os.environ["BROTO_ZSTAMP_PERCENT"] = "10"
    os.environ["BROTO_C2_ENABLED"] = "1"
    os.environ["BROTO_C3_ENABLED"] = "1"
    os.environ["BROTO_C4_ENABLED"] = "1"
    os.environ["BROTO_C5_ENABLED"] = "1"
    os.environ["BROTO_C6_ENABLED"] = "1"
    lib=C3Library37(max_entries=1000); c4=C4Novelty(); c5=C5StructuralRarity(); c6=C6Provenance(max_targets=1000)
    runner=ExperimentRunner(registry(), ExperimentSpec(max_depth=2,max_active_branches=64,max_packets=500), c3_library=lib,c4_novelty=c4,c5_rarity=c5,c6_provenance=c6)
    runner.seed(TracePacket(v, packet_id=f"p{v}") for v in (343,703,2701,6337,11611))
    runner.run_steps(8)
    c2=runner.c2_status(); s3=runner.c3_status(); s4=runner.c4_status(); s5=runner.c5_status(); s6=runner.c6_status()
    n=int(c2["fingerprints"])
    assert n > 1
    assert int(s3["observations"]) == n
    assert int(s4["observations"]) == n
    assert int(s5["observations"]) == n
    assert int(s6["observations"]) == n
    assert s6["authority"] == "SHADOW_ONLY"
    assert s6["scientific_independence_claim"] is False
    assert int(s6["compute_skips"]) == 0
    print("C6_CHAIN=PASS", n, s6["tracked_targets"], s6["operational_independence_candidate_targets"])


def test_survives_runner_rollover() -> None:
    os.environ["BROTO_ZSTAMP_ENABLED"]="1"; os.environ["BROTO_ZSTAMP_PERCENT"]="10"
    os.environ["BROTO_C2_ENABLED"]="1"; os.environ["BROTO_C3_ENABLED"]="1"; os.environ["BROTO_C4_ENABLED"]="1"; os.environ["BROTO_C5_ENABLED"]="1"; os.environ["BROTO_C6_ENABLED"]="1"
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        service=DashboardService(Path(tmp)/"store", spec=ExperimentSpec(duration_seconds=60,max_depth=1,max_active_branches=32,max_packets=200), tick_seconds=0.01, sleeping_pool_enabled=True)
        try:
            service.reset((343,703,2701,6337,11611))
            first=service.status()["c6_provenance"]
            c6_id=id(service.c6_provenance)
            with service._lock:
                service._zstamp_rollup_unlocked(); service._c2_rollup_unlocked(); service._runner=service._new_runner((343,))
            second=service.status()["c6_provenance"]
            assert id(service.c6_provenance) == c6_id
            assert int(second["observations"]) > int(first["observations"])
            print("C6_ROLLOVER=PASS", first["observations"], second["observations"])
        finally:
            service.close()


def main() -> None:
    test_multi_origin_convergence()
    test_parent_formula_candidate_without_multi_origin()
    test_capacity_bound()
    test_full_chain_canary()
    test_survives_runner_rollover()
    print("C6_PROVENANCE=PASS")


if __name__ == "__main__":
    main()
