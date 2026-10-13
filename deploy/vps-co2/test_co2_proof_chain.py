from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

for name in (
    "BROTO_T8_ENABLED","BROTO_T9_ENABLED","BROTO_T10_ENABLED","BROTO_T11_ENABLED",
    "BROTO_T12_ENABLED","BROTO_L1_ENABLED","BROTO_L2_ENABLED","BROTO_L3_ENABLED",
    "BROTO_L4_ENABLED","BROTO_L5_ENABLED","BROTO_S1_ENABLED","BROTO_S2_ENABLED",
    "BROTO_S3_ENABLED","BROTO_S4_ENABLED","BROTO_S5_ENABLED","BROTO_CO1_ENABLED",
    "BROTO_CO2_ENABLED",
):
    os.environ[name] = "1"
os.environ["BROTO_L2_THRESHOLD"] = "75"
os.environ["BROTO_T11_CPU_SLOTS"] = "8"
os.environ["BROTO_T11_MEMORY_SLOTS"] = "8"
os.environ["BROTO_T11_STORAGE_SLOTS"] = "8"
os.environ["BROTO_T11_TIME_SLOTS"] = "8"

from brotoculateur.co1_archive import Co1ArchiveTelemetry
from brotoculateur.co2_proof_chain import (
    Co2ProofChainTelemetry,
    GENESIS_HASH,
    verify_chain_files,
)
from brotoculateur.dashboard import DashboardService, build_default_registry
from brotoculateur.engine import TracePacket, z_stamp_child, z_stamp_root
from brotoculateur.orchestrator import ExperimentSpec


def make_result(formula_id: str, value: int, branch_path: str = "ROOT"):
    registry = build_default_registry()
    formula = registry.get(formula_id)
    source = z_stamp_root(TracePacket(value, branch_path=branch_path))
    assert formula.is_applicable(source), (formula_id, value)
    out = z_stamp_child(formula.apply(source), source)
    return source, out


def read_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_rows(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(r, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n" for r in rows),
        encoding="utf-8",
    )


def seed_archive(path: Path, count: int = 3) -> None:
    co1 = Co1ArchiveTelemetry(path)
    for i in range(count):
        source, out = make_result("DOUBLE", 11 + i, f"ROOT/{i}")
        outcome = co1.observe("DOUBLE", source, out, "FAST_INDEXED_AT_OR_ABOVE_REFERENCE")
        assert outcome.startswith("ARCHIVED_NEW_"), outcome


def test_bootstrap_binds_existing_archive_and_restarts() -> None:
    with tempfile.TemporaryDirectory(prefix="brotoco2-") as td:
        archive = Path(td) / "co1.jsonl"
        chain = Path(td) / "co2.jsonl"
        seed_archive(archive, 3)

        co2 = Co2ProofChainTelemetry(archive, chain)
        s = co2.status()
        assert s["available"] is True
        assert s["backfilled_links"] == 3
        assert s["loaded_chain_links"] == 0
        assert s["chain_links"] == 3 == s["archive_records_seen"]
        assert s["head_chain_hash"] != GENESIS_HASH
        assert len(read_rows(chain)) == 3

        again = Co2ProofChainTelemetry(archive, chain)
        s2 = again.status()
        assert s2["available"] is True
        assert s2["loaded_chain_links"] == 3
        assert s2["backfilled_links"] == 0
        assert s2["chain_links"] == 3
        assert s2["head_chain_hash"] == s["head_chain_hash"]
        print("CO2_BOOTSTRAP_RESTART=PASS", s["head_chain_hash"])


def test_runtime_tail_advances_in_physical_order() -> None:
    with tempfile.TemporaryDirectory(prefix="brotoco2-") as td:
        archive = Path(td) / "co1.jsonl"
        chain = Path(td) / "co2.jsonl"
        co1 = Co1ArchiveTelemetry(archive)
        co2 = Co2ProofChainTelemetry(archive, chain)

        source1, out1 = make_result("DOUBLE", 11, "ROOT/A")
        o1 = co1.observe("DOUBLE", source1, out1, "FAST_INDEXED_AT_OR_ABOVE_REFERENCE")
        assert co2.observe("DOUBLE", source1, out1, o1) == "CHAIN_ADVANCED_1"

        source2, out2 = make_result("PLUS1", 20, "ROOT/B")
        o2 = co1.observe("PLUS1", source2, out2, "FAST_INDEXED_BELOW_REFERENCE")
        assert co2.observe("PLUS1", source2, out2, o2) == "CHAIN_ADVANCED_1"

        s = co2.status()
        assert s["runtime_appended_links"] == 2
        assert s["chain_links"] == 2 == s["archive_records_seen"]
        rows = read_rows(chain)
        assert rows[0]["sequence"] == 1 and rows[0]["previous_chain_hash"] == GENESIS_HASH
        assert rows[1]["sequence"] == 2 and rows[1]["previous_chain_hash"] == rows[0]["chain_hash"]
        assert verify_chain_files(archive, chain)["missing_links"] == 0
        print("CO2_RUNTIME_ORDER=PASS", rows[-1]["chain_hash"])


def test_physical_duplicate_lines_are_chained_not_deleted() -> None:
    with tempfile.TemporaryDirectory(prefix="brotoco2-") as td:
        archive = Path(td) / "co1.jsonl"
        chain = Path(td) / "co2.jsonl"
        seed_archive(archive, 1)
        raw = archive.read_text(encoding="utf-8")
        archive.write_text(raw + raw, encoding="utf-8")

        co2 = Co2ProofChainTelemetry(archive, chain)
        s = co2.status()
        assert s["available"] is True
        assert s["chain_links"] == 2
        links = read_rows(chain)
        assert links[0]["archive_id"] == links[1]["archive_id"]
        assert links[0]["chain_hash"] != links[1]["chain_hash"]
        assert len(read_rows(archive)) == 2
        print("CO2_PHYSICAL_DUPLICATE_PRESERVED=PASS", links[0]["archive_id"])


def test_archive_tamper_fails_closed() -> None:
    with tempfile.TemporaryDirectory(prefix="brotoco2-") as td:
        archive = Path(td) / "co1.jsonl"
        chain = Path(td) / "co2.jsonl"
        seed_archive(archive, 2)
        first = Co2ProofChainTelemetry(archive, chain)
        assert first.status()["available"] is True

        rows = read_rows(archive)
        rows[0]["structural_state"]["value"] = "999999"
        write_rows(archive, rows)

        check = Co2ProofChainTelemetry(archive, chain)
        s = check.status()
        assert s["available"] is False
        assert s["integrity_failures"] == 1
        assert "proof-chain mismatch at line 1" in (s["error_summary"] or "")
        print("CO2_ARCHIVE_TAMPER=PASS")


def test_chain_tamper_or_omission_fails_closed() -> None:
    with tempfile.TemporaryDirectory(prefix="brotoco2-") as td:
        archive = Path(td) / "co1.jsonl"
        chain = Path(td) / "co2.jsonl"
        seed_archive(archive, 3)
        first = Co2ProofChainTelemetry(archive, chain)
        assert first.status()["available"] is True

        links = read_rows(chain)
        links[1]["previous_chain_hash"] = GENESIS_HASH
        write_rows(chain, links)
        bad = Co2ProofChainTelemetry(archive, chain)
        assert bad.status()["available"] is False

    with tempfile.TemporaryDirectory(prefix="brotoco2-") as td:
        archive = Path(td) / "co1.jsonl"
        chain = Path(td) / "co2.jsonl"
        seed_archive(archive, 3)
        Co2ProofChainTelemetry(archive, chain)
        links = read_rows(chain)
        write_rows(chain, [links[0], links[2]])
        missing = Co2ProofChainTelemetry(archive, chain)
        assert missing.status()["available"] is False
        print("CO2_CHAIN_TAMPER_OMISSION=PASS")


def test_trace_integrity_only_authority() -> None:
    with tempfile.TemporaryDirectory(prefix="brotoco2-") as td:
        archive = Path(td) / "co1.jsonl"
        chain = Path(td) / "co2.jsonl"
        seed_archive(archive, 1)
        co2 = Co2ProofChainTelemetry(archive, chain)
        s = co2.status()
        assert s["authority"] == "TRACE_INTEGRITY_ONLY"
        assert s["hash_algorithm"] == "SHA-256"
        assert s["chain_definition"] == "PHYSICAL_CO1_ARCHIVE_RECORD_ORDER"
        assert s["append_only"] is True and s["rewrites_existing_links"] is False
        assert s["co1_archive_mutated"] is False
        assert s["trace_integrity_claim"] is True
        assert s["scientific_proof_claim"] is False
        assert s["truth_of_claim_established"] is False
        assert s["historical_attestation_claim"] is False
        assert s["external_trust_anchor"] is False
        assert s["digital_signature_enabled"] is False
        assert s["validation_state_mutated"] is False and s["proof_promotion"] is False
        assert s["controls_routing"] is False and s["controls_scheduling"] is False and s["controls_calculation"] is False
        assert s["co3_checkpoint_input"] is True
        print("CO2_TRACE_INTEGRITY_ONLY=PASS")


def test_dashboard_lockstep() -> None:
    with tempfile.TemporaryDirectory(prefix="brotoco2dash-") as td:
        archive = Path(td) / "co1.jsonl"
        chain = Path(td) / "co2.jsonl"
        os.environ["BROTO_CO1_ARCHIVE_PATH"] = str(archive)
        os.environ["BROTO_CO2_CHAIN_PATH"] = str(chain)

        service = DashboardService(
            Path(td) / "instance",
            spec=ExperimentSpec(duration_seconds=60, checkpoint_seconds=60, max_depth=4, max_active_branches=16, max_packets=100),
            checkpoint_seconds=60,
            tick_seconds=0.01,
            sleeping_pool_enabled=False,
        )
        modules = [
            service.t8_countertest, service.t9_stability, service.t10_replay,
            service.t11_budget, service.t12_candidate, service.l1_crystal_score,
            service.l2_threshold, service.l3_press, service.l4_canon,
            service.l5_placement, service.s1_aggregator, service.s2_lineage_index,
            service.s3_route_index, service.s4_formula_index, service.s5_fast_index,
            service.co1_archive, service.co2_proof_chain,
        ]
        before = [m.status()["observations"] for m in modules]
        for _ in range(17):
            source, out = make_result("DOUBLE", 11, "ROOT/A")
            service._observe_formula_result("DOUBLE", source, out)
        after = [m.status()["observations"] for m in modules]
        assert [a-b for a,b in zip(after,before)] == [17] * 17

        co1 = service.co1_archive.status()
        co2 = service.co2_proof_chain.status()
        assert co2["observations"] == co1["observations"] == 17
        assert co2["eligible_co1"] == co1["eligible_s5"] == 17
        assert co2["co1_new_signals"] == 1 and co2["co1_present_signals"] == 16
        assert co2["blocked_co1_other"] == 0 and co2["blocked_chain_unavailable"] == 0
        assert co2["runtime_appended_links"] == 1
        assert co2["chain_links"] == co2["archive_records_seen"] == 1
        assert co2["integrity_failures"] == 0 and co2["write_errors"] == 0
        assert verify_chain_files(archive, chain)["missing_links"] == 0
        print("CO2_CALLBACK_LOCKSTEP=PASS", *after, co2["chain_links"])


if __name__ == "__main__":
    test_bootstrap_binds_existing_archive_and_restarts()
    test_runtime_tail_advances_in_physical_order()
    test_physical_duplicate_lines_are_chained_not_deleted()
    test_archive_tamper_fails_closed()
    test_chain_tamper_or_omission_fails_closed()
    test_trace_integrity_only_authority()
    test_dashboard_lockstep()
    print("CO2_PROOF_CHAIN=PASS")
