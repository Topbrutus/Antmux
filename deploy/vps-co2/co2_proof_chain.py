from __future__ import annotations

import hashlib
import json
import os
import tempfile
import threading
from collections import Counter, deque
from pathlib import Path
from typing import Any

SCHEMA = "BRUTUS_CO2_PROOF_CHAIN_V1"
LINK_SCHEMA = "BRUTUS_CO2_PROOF_LINK_V1"
LINK_PAYLOAD_SCHEMA = "BRUTUS_CO2_PROOF_LINK_PAYLOAD_V1"
CO1_RECORD_SCHEMA = "BRUTUS_CO1_ARCHIVE_RECORD_V1"
RECENT_LIMIT = 37
GENESIS_HASH = "0" * 64

VALID_CO1_PREFIXES = (
    "ARCHIVED_NEW_",
    "ARCHIVE_ALREADY_PRESENT_",
)


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "1" if default else "0").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _default_archive_path() -> Path:
    raw = os.getenv("BROTO_CO1_ARCHIVE_PATH", "").strip()
    if raw:
        return Path(raw).expanduser()
    return Path.home() / "brotoculateur" / "data" / "co1" / "archive-v1.jsonl"


def _default_chain_path() -> Path:
    raw = os.getenv("BROTO_CO2_CHAIN_PATH", "").strip()
    if raw:
        return Path(raw).expanduser()
    return Path.home() / "brotoculateur" / "data" / "co2" / "proof-chain-v1.jsonl"


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _parse_json_line(raw: bytes, *, kind: str, line_no: int) -> dict[str, Any]:
    if not raw.endswith(b"\n"):
        raise RuntimeError(f"{kind} incomplete final line at {line_no}")
    try:
        obj = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{kind} invalid JSON at line {line_no}: {exc}") from exc
    if not isinstance(obj, dict):
        raise RuntimeError(f"{kind} non-object record at line {line_no}")
    return obj


def _archive_digest(record: dict[str, Any]) -> str:
    return _sha256_text(_canonical(record))


def _link_payload(
    *,
    sequence: int,
    archive_id: str,
    archive_record_sha256: str,
    previous_chain_hash: str,
) -> dict[str, Any]:
    return {
        "payload_schema": LINK_PAYLOAD_SCHEMA,
        "sequence": int(sequence),
        "archive_line": int(sequence),
        "archive_id": str(archive_id),
        "archive_record_sha256": str(archive_record_sha256),
        "previous_chain_hash": str(previous_chain_hash),
    }


def build_link(record: dict[str, Any], *, sequence: int, previous_chain_hash: str) -> dict[str, Any]:
    if record.get("schema") != CO1_RECORD_SCHEMA:
        raise RuntimeError(f"unexpected Co1 schema at archive line {sequence}")
    archive_id = str(record.get("archive_id") or "")
    if not archive_id:
        raise RuntimeError(f"missing archive_id at archive line {sequence}")
    digest = _archive_digest(record)
    payload = _link_payload(
        sequence=sequence,
        archive_id=archive_id,
        archive_record_sha256=digest,
        previous_chain_hash=previous_chain_hash,
    )
    return {
        "schema": LINK_SCHEMA,
        **payload,
        "chain_hash": _sha256_text(_canonical(payload)),
    }


def verify_chain_files(archive_path: Path, chain_path: Path) -> dict[str, Any]:
    archive: list[dict[str, Any]] = []
    if archive_path.exists():
        with archive_path.open("rb") as handle:
            for line_no, raw in enumerate(handle, start=1):
                if not raw.strip():
                    continue
                archive.append(_parse_json_line(raw, kind="archive", line_no=line_no))

    links: list[dict[str, Any]] = []
    if chain_path.exists():
        with chain_path.open("rb") as handle:
            for line_no, raw in enumerate(handle, start=1):
                if not raw.strip():
                    continue
                links.append(_parse_json_line(raw, kind="chain", line_no=line_no))

    if len(links) > len(archive):
        raise RuntimeError("proof chain is longer than Co1 archive")

    previous = GENESIS_HASH
    for i, link in enumerate(links, start=1):
        expected = build_link(archive[i - 1], sequence=i, previous_chain_hash=previous)
        if link != expected:
            raise RuntimeError(f"proof-chain mismatch at line {i}")
        previous = expected["chain_hash"]

    return {
        "archive_records": len(archive),
        "chain_links": len(links),
        "verified_links": len(links),
        "missing_links": len(archive) - len(links),
        "head_chain_hash": previous,
    }


class Co2ProofChainTelemetry:
    """Hash-linked continuity ledger over the physical Co1 archive order.

    Co2 binds each physical Co1 JSONL record to the previous Co2 link with SHA-256.
    It detects content changes, proof-link changes, omission, insertion and reordering
    relative to the ledger prefix it has already bound.

    This is trace-integrity evidence only. It does NOT establish truth of a scientific
    claim, independent validation, historical timestamping or external attestation.
    """

    def __init__(
        self,
        archive_path: str | Path | None = None,
        chain_path: str | Path | None = None,
    ) -> None:
        self.enabled = _env_flag("BROTO_CO2_ENABLED", False)
        self.archive_path = Path(archive_path).expanduser() if archive_path is not None else _default_archive_path()
        self.chain_path = Path(chain_path).expanduser() if chain_path is not None else _default_chain_path()
        self._lock = threading.RLock()

        self.observations = 0
        self.eligible_co1 = 0
        self.co1_new_signals = 0
        self.co1_present_signals = 0
        self.blocked_co1_other = 0
        self.blocked_chain_unavailable = 0

        self.sync_runs = 0
        self.runtime_appended_links = 0
        self.backfilled_links = 0
        self.loaded_chain_links = 0
        self.archive_records_seen = 0
        self.verified_links = 0

        self.archive_load_errors = 0
        self.chain_load_errors = 0
        self.write_errors = 0
        self.integrity_failures = 0
        self.available = True
        self.error_summary: str | None = None

        self._archive_offset = 0
        self._head_chain_hash = GENESIS_HASH
        self._recent: deque[dict[str, Any]] = deque(maxlen=RECENT_LIMIT)
        self.by_outcome: Counter[str] = Counter()

        if self.enabled:
            self._bootstrap()

    def _prepare_chain_dir(self) -> None:
        self.chain_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.chain_path.parent, 0o700)
        except OSError:
            pass

    def _read_archive_all(self) -> tuple[list[dict[str, Any]], int]:
        rows: list[dict[str, Any]] = []
        if not self.archive_path.exists():
            return rows, 0
        try:
            with self.archive_path.open("rb") as handle:
                for line_no, raw in enumerate(handle, start=1):
                    if not raw.strip():
                        continue
                    row = _parse_json_line(raw, kind="archive", line_no=line_no)
                    if row.get("schema") != CO1_RECORD_SCHEMA:
                        raise RuntimeError(f"unexpected Co1 schema at archive line {line_no}")
                    if not row.get("archive_id"):
                        raise RuntimeError(f"missing archive_id at archive line {line_no}")
                    rows.append(row)
                end = handle.tell()
            return rows, end
        except (OSError, RuntimeError) as exc:
            self.archive_load_errors += 1
            raise RuntimeError(f"archive load failed: {exc}") from exc

    def _read_chain_all(self) -> list[dict[str, Any]]:
        if not self.chain_path.exists():
            return []
        rows: list[dict[str, Any]] = []
        try:
            with self.chain_path.open("rb") as handle:
                for line_no, raw in enumerate(handle, start=1):
                    if not raw.strip():
                        continue
                    row = _parse_json_line(raw, kind="chain", line_no=line_no)
                    if row.get("schema") != LINK_SCHEMA:
                        raise RuntimeError(f"unexpected Co2 schema at chain line {line_no}")
                    rows.append(row)
            return rows
        except (OSError, RuntimeError) as exc:
            self.chain_load_errors += 1
            raise RuntimeError(f"chain load failed: {exc}") from exc

    def _verify_prefix(
        self,
        archive_rows: list[dict[str, Any]],
        links: list[dict[str, Any]],
    ) -> str:
        if len(links) > len(archive_rows):
            raise RuntimeError("proof chain is longer than Co1 archive")
        previous = GENESIS_HASH
        for i, link in enumerate(links, start=1):
            expected = build_link(archive_rows[i - 1], sequence=i, previous_chain_hash=previous)
            if link != expected:
                raise RuntimeError(f"proof-chain mismatch at line {i}")
            previous = expected["chain_hash"]
        return previous

    def _write_initial_chain_atomic(self, links: list[dict[str, Any]]) -> None:
        self._prepare_chain_dir()
        fd, tmp_name = tempfile.mkstemp(prefix=".proof-chain-v1.", suffix=".tmp", dir=self.chain_path.parent)
        tmp = Path(tmp_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                for link in links:
                    handle.write(_canonical(link) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.chmod(tmp, 0o600)
            except OSError:
                pass
            os.replace(tmp, self.chain_path)
            try:
                dfd = os.open(self.chain_path.parent, os.O_RDONLY)
                try:
                    os.fsync(dfd)
                finally:
                    os.close(dfd)
            except OSError:
                pass
        finally:
            if tmp.exists():
                try:
                    tmp.unlink()
                except OSError:
                    pass

    def _append_link(self, link: dict[str, Any]) -> None:
        self._prepare_chain_dir()
        with self.chain_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(_canonical(link) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.chmod(self.chain_path, 0o600)
        except OSError:
            pass

    def _bootstrap(self) -> None:
        with self._lock:
            try:
                archive_rows, archive_end = self._read_archive_all()
                links = self._read_chain_all()
                self.loaded_chain_links = len(links)
                previous = self._verify_prefix(archive_rows, links)
                self.verified_links = len(links)

                missing = archive_rows[len(links):]
                if not links and missing:
                    built: list[dict[str, Any]] = []
                    for idx, row in enumerate(missing, start=1):
                        link = build_link(row, sequence=idx, previous_chain_hash=previous)
                        built.append(link)
                        previous = link["chain_hash"]
                    self._write_initial_chain_atomic(built)
                    self.backfilled_links = len(built)
                    self.verified_links = len(built)
                elif missing:
                    sequence = len(links)
                    for row in missing:
                        sequence += 1
                        link = build_link(row, sequence=sequence, previous_chain_hash=previous)
                        self._append_link(link)
                        previous = link["chain_hash"]
                        self.backfilled_links += 1
                        self.verified_links += 1
                elif not self.chain_path.exists():
                    self._write_initial_chain_atomic([])

                self.archive_records_seen = len(archive_rows)
                self._archive_offset = archive_end
                self._head_chain_hash = previous
            except (OSError, RuntimeError) as exc:
                self.available = False
                self.integrity_failures += 1
                self.error_summary = f"{type(exc).__name__}: {exc}"

    def _sync_tail(self) -> int:
        if not self.available:
            return 0
        self.sync_runs += 1
        appended = 0
        try:
            if not self.archive_path.exists():
                if self.archive_records_seen != 0:
                    raise RuntimeError("Co1 archive disappeared after chain bootstrap")
                return 0

            with self.archive_path.open("rb") as handle:
                handle.seek(self._archive_offset)
                line_no = self.archive_records_seen
                while True:
                    raw = handle.readline()
                    if not raw:
                        break
                    if not raw.strip():
                        self._archive_offset = handle.tell()
                        continue
                    line_no += 1
                    row = _parse_json_line(raw, kind="archive", line_no=line_no)
                    link = build_link(row, sequence=line_no, previous_chain_hash=self._head_chain_hash)
                    self._append_link(link)
                    self._head_chain_hash = link["chain_hash"]
                    self.archive_records_seen += 1
                    self.verified_links += 1
                    self.runtime_appended_links += 1
                    appended += 1
                    self._archive_offset = handle.tell()
            return appended
        except (OSError, RuntimeError) as exc:
            self.available = False
            self.integrity_failures += 1
            if isinstance(exc, OSError):
                self.write_errors += 1
            self.error_summary = f"{type(exc).__name__}: {exc}"
            return appended

    def observe(self, formula_id: str, source: Any, out: Any, co1_outcome: str) -> str:
        if not self.enabled:
            return "DISABLED"
        with self._lock:
            self.observations += 1
            outcome_text = str(co1_outcome or "").upper()

            if not self.available:
                self.blocked_chain_unavailable += 1
                outcome = "BLOCKED_CHAIN_UNAVAILABLE"
                self.by_outcome[outcome] += 1
                self._recent.append({"co1_outcome": outcome_text, "outcome": outcome, "advanced": 0})
                return outcome

            if not outcome_text.startswith(VALID_CO1_PREFIXES):
                self.blocked_co1_other += 1
                outcome = "BLOCKED_CO1_OTHER"
                self.by_outcome[outcome] += 1
                self._recent.append({"co1_outcome": outcome_text, "outcome": outcome, "advanced": 0})
                return outcome

            self.eligible_co1 += 1
            if outcome_text.startswith("ARCHIVED_NEW_"):
                self.co1_new_signals += 1
                advanced = self._sync_tail()
            else:
                self.co1_present_signals += 1
                advanced = 0

            if not self.available:
                self.blocked_chain_unavailable += 1
                outcome = "BLOCKED_CHAIN_UNAVAILABLE"
            elif advanced:
                outcome = f"CHAIN_ADVANCED_{advanced}"
            else:
                outcome = "CHAIN_ALREADY_CURRENT"

            self.by_outcome[outcome] += 1
            self._recent.append({
                "formula_id": str(formula_id or "") or None,
                "co1_outcome": outcome_text,
                "outcome": outcome,
                "advanced": advanced,
                "archive_records_seen": self.archive_records_seen,
                "head_chain_hash": self._head_chain_hash,
            })
            return outcome

    def status(self) -> dict[str, Any]:
        with self._lock:
            chain_bytes = 0
            try:
                if self.chain_path.exists():
                    chain_bytes = int(self.chain_path.stat().st_size)
            except OSError:
                chain_bytes = -1
            return {
                "schema": SCHEMA,
                "mode": SCHEMA,
                "enabled": self.enabled,
                "authority": "TRACE_INTEGRITY_ONLY",
                "source_of_truth": "CO1_ARCHIVE_PHYSICAL_ORDER",
                "observations": self.observations,
                "eligible_co1": self.eligible_co1,
                "co1_new_signals": self.co1_new_signals,
                "co1_present_signals": self.co1_present_signals,
                "blocked_co1_other": self.blocked_co1_other,
                "blocked_chain_unavailable": self.blocked_chain_unavailable,
                "sync_runs": self.sync_runs,
                "runtime_appended_links": self.runtime_appended_links,
                "backfilled_links": self.backfilled_links,
                "loaded_chain_links": self.loaded_chain_links,
                "archive_records_seen": self.archive_records_seen,
                "chain_links": self.verified_links,
                "verified_links": self.verified_links,
                "head_chain_hash": self._head_chain_hash,
                "genesis_hash": GENESIS_HASH,
                "archive_path": str(self.archive_path),
                "chain_path": str(self.chain_path),
                "chain_bytes": chain_bytes,
                "available": self.available,
                "archive_load_errors": self.archive_load_errors,
                "chain_load_errors": self.chain_load_errors,
                "write_errors": self.write_errors,
                "integrity_failures": self.integrity_failures,
                "error_summary": self.error_summary,
                "by_outcome": dict(sorted(self.by_outcome.items())),
                "recent_limit": RECENT_LIMIT,
                "recent": list(self._recent),
                "hash_algorithm": "SHA-256",
                "chain_definition": "PHYSICAL_CO1_ARCHIVE_RECORD_ORDER",
                "link_schema": LINK_SCHEMA,
                "detects_archive_record_change": True,
                "detects_proof_link_change": True,
                "detects_omission_in_bound_prefix": True,
                "detects_reordering_in_bound_prefix": True,
                "detects_insertion_in_bound_prefix": True,
                "append_only": True,
                "fsync_on_runtime_link": True,
                "atomic_initial_backfill": True,
                "rewrites_existing_links": False,
                "co1_archive_mutated": False,
                "backfill_is_retrospective_integrity_binding": True,
                "historical_attestation_claim": False,
                "external_trust_anchor": False,
                "digital_signature_enabled": False,
                "trace_integrity_claim": True,
                "scientific_proof_claim": False,
                "truth_of_claim_established": False,
                "validation_state_mutated": False,
                "proof_promotion": False,
                "controls_routing": False,
                "controls_scheduling": False,
                "controls_calculation": False,
                "reserves_resources": False,
                "executes_replay": False,
                "schedules_replay": False,
                "compute_skips": 0,
                "value_mutated": False,
                "co3_checkpoint_input": True,
            }
