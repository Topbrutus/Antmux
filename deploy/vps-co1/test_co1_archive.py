from __future__ import annotations

import json
import os
import tempfile
from dataclasses import replace
from pathlib import Path

for name in (
    "BROTO_T8_ENABLED","BROTO_T9_ENABLED","BROTO_T10_ENABLED","BROTO_T11_ENABLED",
    "BROTO_T12_ENABLED","BROTO_L1_ENABLED","BROTO_L2_ENABLED","BROTO_L3_ENABLED",
    "BROTO_L4_ENABLED","BROTO_L5_ENABLED","BROTO_S1_ENABLED","BROTO_S2_ENABLED",
    "BROTO_S3_ENABLED","BROTO_S4_ENABLED","BROTO_S5_ENABLED","BROTO_CO1_ENABLED",
):
    os.environ[name] = "1"
os.environ["BROTO_L2_THRESHOLD"] = "75"
os.environ["BROTO_T11_CPU_SLOTS"] = "8"
os.environ["BROTO_T11_MEMORY_SLOTS"] = "8"
os.environ["BROTO_T11_STORAGE_SLOTS"] = "8"
os.environ["BROTO_T11_TIME_SLOTS"] = "8"

from brotoculateur.c3_library import C3Library37
from brotoculateur.co1_archive import Co1ArchiveTelemetry, RECORD_SCHEMA
from brotoculateur.dashboard import DashboardService, build_default_registry
from brotoculateur.engine import TracePacket, c2_fingerprint, z_stamp_child, z_stamp_root
from brotoculateur.orchestrator import ExperimentSpec


def make_result(formula_id: str, value: int, branch_path: str = "ROOT"):
    registry = build_default_registry()
    formula = registry.get(formula_id)
    source = z_stamp_root(TracePacket(value, branch_path=branch_path))
    assert formula.is_applicable(source), (formula_id, value)
    out = z_stamp_child(formula.apply(source), source)
    return source, out


def read_lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_append_only_dedup_and_restart() -> None:
    with tempfile.TemporaryDirectory(prefix="brotoco1-") as td:
        path = Path(td) / "archive.jsonl"
        source, out = make_result("DOUBLE", 11, "ROOT/A")
        co1 = Co1ArchiveTelemetry(path)
        got = [co1.observe("DOUBLE", source, out, "FAST_INDEXED_AT_OR_ABOVE_REFERENCE") for _ in range(3)]
        assert got[0] == "ARCHIVED_NEW_AT_OR_ABOVE_REFERENCE"
        assert got[1:] == ["ARCHIVE_ALREADY_PRESENT_AT_OR_ABOVE_REFERENCE"] * 2
        rows = read_lines(path)
        assert len(rows) == 1
        s = co1.status()
        assert s["appended_records"] == 1 and s["already_present"] == 2
        assert s["unique_archive_records"] == 1 and s["archive_bytes"] > 0

        again = Co1ArchiveTelemetry(path)
        s0 = again.status()
        assert s0["loaded_records"] == 1 and s0["unique_archive_records"] == 1
        assert again.observe("DOUBLE", source, out, "FAST_INDEXED_AT_OR_ABOVE_REFERENCE") == "ARCHIVE_ALREADY_PRESENT_AT_OR_ABOVE_REFERENCE"
        assert len(read_lines(path)) == 1
        print("CO1_APPEND_ONLY_RESTART=PASS", s["archive_bytes"], rows[0]["archive_id"])


def test_record_preserves_structural_state_and_bucket() -> None:
    with tempfile.TemporaryDirectory(prefix="brotoco1-") as td:
        path = Path(td) / "archive.jsonl"
        source, out = make_result("PLUS1", 10, "ROOT/B")
        co1 = Co1ArchiveTelemetry(path)
        assert co1.observe("PLUS1", source, out, "FAST_INDEXED_BELOW_REFERENCE") == "ARCHIVED_NEW_BELOW_REFERENCE"
        row = read_lines(path)[0]
        fp = c2_fingerprint(out)
        assert row["schema"] == RECORD_SCHEMA
        assert row["c2_fingerprint"] == fp
        assert row["bucket37"] == C3Library37.bucket_for(fp)
        assert row["formula_id"] == "PLUS1" and row["z_id"] == out.z_id
        st = row["structural_state"]
        assert st["value"] == str(out.value)
        assert st["depth"] == out.depth
        assert st["formula_chain"] == list(out.formula_chain)
        assert st["state"] == out.state.value
        assert st["z_id"] == out.z_id and st["z_parent_id"] == out.z_parent_id and st["z_origin_id"] == out.z_origin_id
        print("CO1_STRUCTURAL_PAYLOAD=PASS", row["bucket37"], fp, out.z_id)


def test_same_z_distinct_structures_are_not_collapsed() -> None:
    with tempfile.TemporaryDirectory(prefix="brotoco1-") as td:
        path = Path(td) / "archive.jsonl"
        a, ao = make_result("PLUS1", 10)
        b, bo = make_result("HALF_EVEN", 22)
        assert ao.z_id == bo.z_id
        assert c2_fingerprint(ao) != c2_fingerprint(bo)
        co1 = Co1ArchiveTelemetry(path)
        co1.observe("PLUS1", a, ao, "FAST_INDEXED_BELOW_REFERENCE")
        co1.observe("HALF_EVEN", b, bo, "FAST_INDEXED_AT_OR_ABOVE_REFERENCE")
        s = co1.status()
        assert s["unique_archive_records"] == 2
        assert s["unique_z_archived"] == 1
        assert len(read_lines(path)) == 2
        print("CO1_MULTI_STRUCTURE_Z_PRESERVED=PASS", ao.z_id, s["occupied_buckets_archived"])


def test_input_guards() -> None:
    with tempfile.TemporaryDirectory(prefix="brotoco1-") as td:
        path = Path(td) / "archive.jsonl"
        source, out = make_result("PLUS1", 10)
        co1 = Co1ArchiveTelemetry(path)
        assert co1.observe("PLUS1", source, out, "BLOCKED_S4_OTHER") == "BLOCKED_S5_OTHER"
        assert co1.observe("", source, out, "FAST_INDEXED_AT_OR_ABOVE_REFERENCE") == "BLOCKED_MISSING_FORMULA_ID"
        assert co1.observe("PLUS1", source, replace(out, z_id=None), "FAST_INDEXED_AT_OR_ABOVE_REFERENCE") == "BLOCKED_MISSING_Z_ID"
        assert co1.observe("DOUBLE", source, out, "FAST_INDEXED_AT_OR_ABOVE_REFERENCE") == "BLOCKED_FORMULA_CHAIN_MISMATCH"
        s = co1.status()
        assert s["appended_records"] == 0 and s["unique_archive_records"] == 0
        assert s["blocked_s5_other"] == 1 and s["blocked_missing_formula"] == 1
        assert s["blocked_missing_z"] == 1 and s["blocked_formula_mismatch"] == 1
        print("CO1_INPUT_GATES=PASS")


def test_corrupt_archive_fails_closed_without_rewrite() -> None:
    with tempfile.TemporaryDirectory(prefix="brotoco1-") as td:
        path = Path(td) / "archive.jsonl"
        original = "{not-json}\n"
        path.write_text(original, encoding="utf-8")
        co1 = Co1ArchiveTelemetry(path)
        s0 = co1.status()
        assert s0["available"] is False and s0["load_errors"] == 1
        source, out = make_result("DOUBLE", 11)
        assert co1.observe("DOUBLE", source, out, "FAST_INDEXED_AT_OR_ABOVE_REFERENCE") == "BLOCKED_ARCHIVE_UNAVAILABLE"
        assert path.read_text(encoding="utf-8") == original
        print("CO1_CORRUPTION_FAIL_CLOSED=PASS")


def test_persistence_only_authority() -> None:
    with tempfile.TemporaryDirectory(prefix="brotoco1-") as td:
        path = Path(td) / "archive.jsonl"
        source, out = make_result("DOUBLE", 11)
        co1 = Co1ArchiveTelemetry(path)
        co1.observe("DOUBLE", source, out, "FAST_INDEXED_AT_OR_ABOVE_REFERENCE")
        s = co1.status()
        assert s["authority"] == "PERSISTENCE_ONLY"
        assert s["persistent"] is True and s["append_only"] is True and s["fsync_on_new_record"] is True
        assert s["rewrites_existing_records"] is False and s["archive_copy_only"] is True
        assert s["age_policy_defined"] is False and s["hot_removal_enabled"] is False and s["hot_evictions"] == 0
        assert s["hash_chain_enabled"] is False and s["co2_owns_hash_chain"] is True
        assert s["s5_fast_index_mutated"] is False and s["validation_state_mutated"] is False
        assert s["controls_routing"] is False and s["controls_scheduling"] is False and s["controls_calculation"] is False
        assert s["scientific_proof_claim"] is False and s["proof_promotion"] is False
        assert s["co2_proof_chain_input"] is True
        print("CO1_PERSISTENCE_ONLY_AUTHORITY=PASS")


def test_dashboard_lockstep() -> None:
    with tempfile.TemporaryDirectory(prefix="brotoco1dash-") as td:
        archive = Path(td) / "co1.jsonl"
        os.environ["BROTO_CO1_ARCHIVE_PATH"] = str(archive)
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
            service.co1_archive,
        ]
        before = [m.status()["observations"] for m in modules]
        for _ in range(17):
            source, out = make_result("DOUBLE", 11, "ROOT/A")
            service._observe_formula_result("DOUBLE", source, out)
        after = [m.status()["observations"] for m in modules]
        assert [a-b for a,b in zip(after,before)] == [17] * 16
        s5 = service.s5_fast_index.status()
        co1 = service.co1_archive.status()
        assert co1["observations"] == s5["observations"] == 17
        assert co1["eligible_s5"] == s5["indexed"] == 17
        assert co1["blocked_s5_other"] == 0 and co1["write_errors"] == 0 and co1["load_errors"] == 0
        assert co1["appended_records"] == 1 and co1["already_present"] == 16
        assert co1["unique_archive_records"] == 1 and co1["unique_z_archived"] == 1
        assert len(read_lines(archive)) == 1
        print("CO1_CALLBACK_LOCKSTEP=PASS", *after, co1["appended_records"], co1["already_present"])


if __name__ == "__main__":
    test_append_only_dedup_and_restart()
    test_record_preserves_structural_state_and_bucket()
    test_same_z_distinct_structures_are_not_collapsed()
    test_input_guards()
    test_corrupt_archive_fails_closed_without_rewrite()
    test_persistence_only_authority()
    test_dashboard_lockstep()
    print("CO1_ARCHIVE=PASS")
