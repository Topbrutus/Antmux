from __future__ import annotations

import json
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

os.environ["BROTO_CO1_ENABLED"] = "1"

from brotoculateur.co1_archive import Co1ArchiveTelemetry
from brotoculateur.dashboard import build_default_registry
from brotoculateur.engine import TracePacket, z_stamp_child, z_stamp_root


def make_result(formula_id: str, value: int, branch_path: str = "ROOT"):
    registry = build_default_registry()
    formula = registry.get(formula_id)
    source = z_stamp_root(TracePacket(value, branch_path=branch_path))
    assert formula.is_applicable(source), (formula_id, value)
    out = z_stamp_child(formula.apply(source), source)
    return source, out


def physical_lines(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def test_parallel_duplicate_is_single_append() -> None:
    with tempfile.TemporaryDirectory(prefix="brotoco1race-") as td:
        path = Path(td) / "archive.jsonl"
        source, out = make_result("DOUBLE", 11, "ROOT/RACE")
        co1 = Co1ArchiveTelemetry(path)

        def one(_: int) -> str:
            return co1.observe("DOUBLE", source, out, "FAST_INDEXED_AT_OR_ABOVE_REFERENCE")

        with ThreadPoolExecutor(max_workers=16) as pool:
            outcomes = list(pool.map(one, range(128)))

        assert outcomes.count("ARCHIVED_NEW_AT_OR_ABOVE_REFERENCE") == 1
        assert outcomes.count("ARCHIVE_ALREADY_PRESENT_AT_OR_ABOVE_REFERENCE") == 127
        status = co1.status()
        assert status["thread_safe_deduplication"] is True
        assert status["appended_records"] == 1
        assert status["already_present"] == 127
        assert status["unique_archive_records"] == 1
        assert status["physical_records_seen"] == 1
        assert physical_lines(path) == 1
        print("CO1_PARALLEL_DEDUP=PASS", status["appended_records"], status["already_present"])


def test_preexisting_duplicate_lines_are_preserved_and_counted() -> None:
    with tempfile.TemporaryDirectory(prefix="brotoco1legacy-") as td:
        path = Path(td) / "archive.jsonl"
        source, out = make_result("PLUS1", 10)
        first = Co1ArchiveTelemetry(path)
        assert first.observe("PLUS1", source, out, "FAST_INDEXED_BELOW_REFERENCE") == "ARCHIVED_NEW_BELOW_REFERENCE"
        row = path.read_text(encoding="utf-8")
        path.write_text(row * 3, encoding="utf-8", newline="\n")

        loaded = Co1ArchiveTelemetry(path)
        status = loaded.status()
        assert status["available"] is True
        assert status["loaded_records"] == 3
        assert status["loaded_duplicate_ids"] == 2
        assert status["physical_records_seen"] == 3
        assert status["unique_archive_records"] == 1
        assert status["preexisting_duplicate_lines_preserved"] is True
        assert physical_lines(path) == 3
        assert loaded.observe("PLUS1", source, out, "FAST_INDEXED_BELOW_REFERENCE") == "ARCHIVE_ALREADY_PRESENT_BELOW_REFERENCE"
        assert physical_lines(path) == 3
        print("CO1_LEGACY_DUPLICATES_PRESERVED=PASS", status["loaded_records"], status["loaded_duplicate_ids"])


if __name__ == "__main__":
    test_parallel_duplicate_is_single_append()
    test_preexisting_duplicate_lines_are_preserved_and_counted()
    print("CO1_CONCURRENCY=PASS")
