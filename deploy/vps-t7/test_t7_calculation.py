import os

from brotoculateur.c3_library import C3Library37
from brotoculateur.c4_novelty import C4Novelty
from brotoculateur.c5_rarity import C5StructuralRarity
from brotoculateur.c6_provenance import C6Provenance
from brotoculateur.c7_router import C7ShadowRouter
from brotoculateur.dashboard import build_default_registry
from brotoculateur.engine import TracePacket
from brotoculateur.orchestrator import ExperimentRunner, ExperimentSpec
from brotoculateur.papillon_engine import Papillon144
from brotoculateur.t1_family import T1FamilyClassifier
from brotoculateur.t2_exact_duplicate import T2ExactDuplicate
from brotoculateur.t3_neighborhood import T3SemanticNeighborhood
from brotoculateur.t4_convergence import T4Convergence
from brotoculateur.t5_independence import T5OperationalIndependence
from brotoculateur.t6_papillon import T6PapillonAffinity
from brotoculateur.t7_calculation import T7CalculationTelemetry


def set_env(master_percent: int = 10) -> None:
    for name in (
        "BROTO_C2_ENABLED", "BROTO_C3_ENABLED", "BROTO_C4_ENABLED", "BROTO_C5_ENABLED",
        "BROTO_C6_ENABLED", "BROTO_C7_ENABLED", "BROTO_T1_ENABLED", "BROTO_T2_ENABLED",
        "BROTO_T3_ENABLED", "BROTO_T4_ENABLED", "BROTO_T5_ENABLED", "BROTO_T6_ENABLED",
        "BROTO_T7_ENABLED",
    ):
        os.environ[name] = "1"
    os.environ["BROTO_ZSTAMP_ENABLED"] = "1"
    os.environ["BROTO_ZSTAMP_PERCENT"] = "100"
    os.environ["BROTO_PAPILLON_MASTER_ENABLED"] = "1"
    os.environ["BROTO_PAPILLON_MASTER_PERCENT"] = str(master_percent)


def test_papillon_telemetry_is_pure() -> None:
    pap = Papillon144()
    before = pap.status()
    a = pap.telemetry_counters()
    b = pap.telemetry_counters()
    after = pap.status()
    assert a == b
    assert before == after
    assert set(a) == {
        "evaluations", "direct_evaluations", "cacheable_evaluations", "cache_hits",
        "cache_misses", "predicate_calls", "formula_calls",
    }
    print("T7_PAPILLON_TELEMETRY_PURE=PASS", a)


def make_shared():
    return {
        "c3": C3Library37(), "c4": C4Novelty(), "c5": C5StructuralRarity(),
        "c6": C6Provenance(), "c7": C7ShadowRouter(), "t1": T1FamilyClassifier(),
        "t2": T2ExactDuplicate(max_keys=4096), "t3": T3SemanticNeighborhood(per_family_limit=64),
        "t4": T4Convergence(max_targets=4096, sigs_per_target=16),
        "t5": T5OperationalIndependence(max_targets=4096), "t6": T6PapillonAffinity(),
        "t7": T7CalculationTelemetry(),
    }


def make_runner(shared):
    return ExperimentRunner(
        build_default_registry(),
        ExperimentSpec(duration_seconds=60, checkpoint_seconds=60, max_depth=8, max_active_branches=64, max_packets=6000),
        papillon_enabled=True, sleeping_pool_enabled=False,
        c3_library=shared["c3"], c4_novelty=shared["c4"], c5_rarity=shared["c5"],
        c6_provenance=shared["c6"], c7_router=shared["c7"], t1_family=shared["t1"],
        t2_duplicate=shared["t2"], t3_neighborhood=shared["t3"], t4_convergence=shared["t4"],
        t5_independence=shared["t5"], t6_papillon=shared["t6"], t7_calculation=shared["t7"],
    )


def assert_accounting(runner: ExperimentRunner) -> None:
    s = runner.t7_status()
    assert s["enabled"] is True
    assert s["packet_observations"] == runner.processed_packets
    assert s["logical_formula_attempts"] == s["packet_observations"] * len(runner.registry.ids())
    assert s["logical_formula_attempts"] == s["native_attempts"] + s["papillon_evaluations"]
    assert s["accounting_conflicts"] == 0
    assert s["negative_delta_conflicts"] == 0
    assert s["controls_formula_selection"] is False
    assert s["controls_papillon"] is False
    assert s["compute_skips"] == 0
    assert s["proof_promotion"] is False


def test_chain_accounting() -> None:
    set_env(10)
    shared = make_shared()
    r = make_runner(shared)
    r.seed(TracePacket(v) for v in (343, 703, 2701, 6337, 11611))
    r.run_steps(120)
    assert_accounting(r)
    s = r.t7_status()
    assert s["packet_observations"] > 0
    assert s["physical_formula_calls"] > 0
    assert s["papillon_evaluations"] > 0
    print("T7_CHAIN=PASS", s["packet_observations"], s["logical_formula_attempts"], s["physical_formula_calls"], s["memo_hits_observed"])


def test_master_all_and_rollover() -> None:
    set_env(100)
    shared = make_shared()
    r1 = make_runner(shared)
    r1.seed(TracePacket(v) for v in (343, 703, 2701, 6337, 11611))
    r1.run_steps(40)
    assert_accounting(r1)
    s1 = r1.t7_status()
    assert s1["native_attempts"] == 0
    assert s1["papillon_evaluations"] == s1["logical_formula_attempts"]
    before = s1["packet_observations"]

    r2 = make_runner(shared)
    r2.seed(TracePacket(v) for v in (343, 703, 2701, 6337, 11611))
    r2.run_steps(20)
    s2 = r2.t7_status()
    assert s2["packet_observations"] > before
    assert s2["accounting_conflicts"] == 0 and s2["negative_delta_conflicts"] == 0
    print("T7_ROLLOVER=PASS", before, s2["packet_observations"])


if __name__ == "__main__":
    test_papillon_telemetry_is_pure()
    test_chain_accounting()
    test_master_all_and_rollover()
    print("T7_CALCULATION=PASS")
