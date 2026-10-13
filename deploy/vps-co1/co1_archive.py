from __future__ import annotations

import hashlib
import json
import os
import threading
from collections import Counter, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .c3_library import C3Library37
from .engine import c2_fingerprint

SCHEMA = "BRUTUS_CO1_ARCHIVE_V1"
RECORD_SCHEMA = "BRUTUS_CO1_ARCHIVE_RECORD_V1"
RECENT_LIMIT = 37
VALID_S5 = frozenset({
    "FAST_INDEXED_AT_OR_ABOVE_REFERENCE",
    "FAST_INDEXED_BELOW_REFERENCE",
})


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "1" if default else "0").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _default_archive_path() -> Path:
    raw = os.getenv("BROTO_CO1_ARCHIVE_PATH", "").strip()
    if raw:
        return Path(raw).expanduser()
    return Path.home() / "brotoculateur" / "data" / "co1" / "archive-v1.jsonl"


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _state_value(packet: Any) -> str:
    state = getattr(packet, "state", None)
    value = getattr(state, "value", state)
    return str(value) if value is not None else ""


def _terminal_formula(packet: Any) -> str | None:
    chain = tuple(str(x) for x in (getattr(packet, "formula_chain", ()) or ()))
    return chain[-1] if chain else None


def _identity_payload(*, fingerprint: str, formula_id: str, z_id: str) -> dict[str, str]:
    return {
        "c2_fingerprint": str(fingerprint),
        "formula_id": str(formula_id),
        "z_id": str(z_id),
    }


def _archive_id(*, fingerprint: str, formula_id: str, z_id: str) -> str:
    return "A1-" + _sha256_text(_canonical(_identity_payload(
        fingerprint=fingerprint,
        formula_id=formula_id,
        z_id=z_id,
    )))


def _record_identity_ok(record: dict[str, Any]) -> bool:
    try:
        expected = _archive_id(
            fingerprint=str(record["c2_fingerprint"]),
            formula_id=str(record["formula_id"]),
            z_id=str(record["z_id"]),
        )
    except (KeyError, TypeError, ValueError):
        return False
    return str(record.get("archive_id") or "") == expected


class Co1ArchiveTelemetry:
    """Persistent append-only archive boundary downstream of S5 Fast Index.

    Source contract:
    - the prototype names Co1 ``Archive`` and exposes ``archive: false``;
    - the prototype UI says Co1 takes old objects out of the hot circuit without
      losing them;
    - no source-defined age threshold or HOT eviction rule currently exists.

    Co1 v1 therefore implements the non-destructive half first: every *new exact
    S5 fast entry* gets one durable JSONL archive record. Repeated observations
    are recognized by a deterministic archive id and do not rewrite or append a
    duplicate record. The archived payload preserves the canonical structural
    fields used by C2 plus the exact S5 formula/Z/bucket context.

    The check+append+in-memory registration sequence is serialized with an
    RLock so concurrent callbacks cannot append the same archive id twice.

    Co1 v1 deliberately does NOT evict from S5, invent an age policy, change
    ValidationState, or claim scientific proof. Co2 owns proof-chain continuity.
    """

    def __init__(self, archive_path: str | Path | None = None) -> None:
        self.enabled = _env_flag("BROTO_CO1_ENABLED", False)
        self.archive_path = Path(archive_path).expanduser() if archive_path is not None else _default_archive_path()
        self._lock = threading.RLock()

        self.observations = 0
        self.eligible_s5 = 0
        self.appended_records = 0
        self.already_present = 0
        self.blocked_s5_other = 0
        self.blocked_missing_formula = 0
        self.blocked_missing_z = 0
        self.blocked_formula_mismatch = 0
        self.blocked_archive_unavailable = 0
        self.write_errors = 0

        self.loaded_records = 0
        self.loaded_duplicate_ids = 0
        self.load_errors = 0
        self.available = True
        self.load_error_summary: str | None = None

        self.reference_sides: Counter[str] = Counter()
        self.by_formula: dict[str, Counter[str]] = {}
        self._archive_ids: set[str] = set()
        self._z_ids: set[str] = set()
        self._formula_ids: set[str] = set()
        self._buckets: set[int] = set()
        self._recent: deque[dict[str, Any]] = deque(maxlen=RECENT_LIMIT)

        if self.enabled:
            self._load_existing_archive()

    def _record_outcome(self, formula_id: str, outcome: str) -> None:
        self.by_formula.setdefault(str(formula_id), Counter())[outcome] += 1

    def _prepare_path(self) -> None:
        self.archive_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.archive_path.parent, 0o700)
        except OSError:
            pass
        if not self.archive_path.exists():
            self.archive_path.touch(mode=0o600, exist_ok=True)
        try:
            os.chmod(self.archive_path, 0o600)
        except OSError:
            pass

    def _load_existing_archive(self) -> None:
        try:
            self._prepare_path()
            with self.archive_path.open("r", encoding="utf-8") as handle:
                for line_no, raw in enumerate(handle, start=1):
                    if not raw.strip():
                        continue
                    try:
                        record = json.loads(raw)
                    except json.JSONDecodeError as exc:
                        raise RuntimeError(f"invalid JSON at line {line_no}: {exc.msg}") from exc
                    if not isinstance(record, dict):
                        raise RuntimeError(f"non-object record at line {line_no}")
                    if record.get("schema") != RECORD_SCHEMA:
                        raise RuntimeError(f"unexpected schema at line {line_no}")
                    if not _record_identity_ok(record):
                        raise RuntimeError(f"archive identity mismatch at line {line_no}")
                    archive_id = str(record["archive_id"])
                    if archive_id in self._archive_ids:
                        self.loaded_duplicate_ids += 1
                    else:
                        self._archive_ids.add(archive_id)
                    self._z_ids.add(str(record.get("z_id") or ""))
                    self._formula_ids.add(str(record.get("formula_id") or ""))
                    try:
                        self._buckets.add(int(record.get("bucket37")))
                    except (TypeError, ValueError):
                        raise RuntimeError(f"invalid bucket37 at line {line_no}")
                    self.loaded_records += 1
        except (OSError, RuntimeError) as exc:
            self.available = False
            self.load_errors += 1
            self.load_error_summary = f"{type(exc).__name__}: {exc}"

    def _append_record(self, record: dict[str, Any]) -> None:
        self._prepare_path()
        line = _canonical(record) + "\n"
        with self.archive_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(line)
            handle.flush()
            os.fsync(handle.fileno())

    def observe(self, formula_id: str, source: Any, out: Any, s5_outcome: str) -> str:
        if not self.enabled:
            return "DISABLED"
        with self._lock:
            return self._observe_locked(formula_id, source, out, s5_outcome)

    def _observe_locked(self, formula_id: str, source: Any, out: Any, s5_outcome: str) -> str:
        self.observations += 1
        s5 = str(s5_outcome).upper()
        formula = str(formula_id or "").strip()

        if s5 not in VALID_S5:
            self.blocked_s5_other += 1
            outcome = "BLOCKED_S5_OTHER"
            self._record_outcome(formula or "<MISSING>", outcome)
            self._recent.append({
                "formula_id": formula or None,
                "outcome": outcome,
                "s5_outcome": s5,
                "archived": False,
            })
            return outcome

        self.eligible_s5 += 1

        if not self.available:
            self.blocked_archive_unavailable += 1
            outcome = "BLOCKED_ARCHIVE_UNAVAILABLE"
            self._record_outcome(formula or "<MISSING>", outcome)
            self._recent.append({
                "formula_id": formula or None,
                "outcome": outcome,
                "s5_outcome": s5,
                "archived": False,
            })
            return outcome

        if not formula:
            self.blocked_missing_formula += 1
            outcome = "BLOCKED_MISSING_FORMULA_ID"
            self._record_outcome("<MISSING>", outcome)
            self._recent.append({"formula_id": None, "outcome": outcome, "s5_outcome": s5, "archived": False})
            return outcome

        z_raw = getattr(out, "z_id", None)
        if not z_raw:
            self.blocked_missing_z += 1
            outcome = "BLOCKED_MISSING_Z_ID"
            self._record_outcome(formula, outcome)
            self._recent.append({"formula_id": formula, "outcome": outcome, "s5_outcome": s5, "archived": False})
            return outcome

        terminal = _terminal_formula(out)
        if terminal != formula:
            self.blocked_formula_mismatch += 1
            outcome = "BLOCKED_FORMULA_CHAIN_MISMATCH"
            self._record_outcome(formula, outcome)
            self._recent.append({
                "formula_id": formula,
                "terminal_formula": terminal,
                "outcome": outcome,
                "s5_outcome": s5,
                "archived": False,
            })
            return outcome

        fingerprint = c2_fingerprint(out)
        bucket37 = C3Library37.bucket_for(fingerprint)
        z_id = str(z_raw)
        archive_id = _archive_id(fingerprint=fingerprint, formula_id=formula, z_id=z_id)
        side = "AT_OR_ABOVE_REFERENCE" if s5.endswith("AT_OR_ABOVE_REFERENCE") else "BELOW_REFERENCE"
        self.reference_sides[side] += 1

        if archive_id in self._archive_ids:
            self.already_present += 1
            outcome = f"ARCHIVE_ALREADY_PRESENT_{side}"
            self._record_outcome(formula, outcome)
            self._recent.append({
                "archive_id": archive_id,
                "formula_id": formula,
                "z_id": z_id,
                "c2_fingerprint": fingerprint,
                "bucket37": bucket37,
                "outcome": outcome,
                "s5_outcome": s5,
                "archived": True,
                "new_record": False,
            })
            return outcome

        chain = [str(x) for x in (getattr(out, "formula_chain", ()) or ())]
        record = {
            "schema": RECORD_SCHEMA,
            "archive_id": archive_id,
            "archived_at": datetime.now(timezone.utc).isoformat(),
            "c2_fingerprint": fingerprint,
            "bucket37": bucket37,
            "formula_id": formula,
            "z_id": z_id,
            "reference_side": side,
            "structural_state": {
                "value": str(int(getattr(out, "value"))),
                "depth": int(getattr(out, "depth")),
                "formula_chain": chain,
                "state": _state_value(out),
                "z_id": z_id,
                "z_parent_id": getattr(out, "z_parent_id", None),
                "z_origin_id": getattr(out, "z_origin_id", None),
            },
            "source_z_id_first_observed": getattr(source, "z_id", None),
        }

        try:
            self._append_record(record)
        except OSError as exc:
            self.write_errors += 1
            self.available = False
            self.load_error_summary = f"{type(exc).__name__}: {exc}"
            outcome = "BLOCKED_ARCHIVE_WRITE_ERROR"
            self._record_outcome(formula, outcome)
            self._recent.append({
                "archive_id": archive_id,
                "formula_id": formula,
                "z_id": z_id,
                "bucket37": bucket37,
                "outcome": outcome,
                "s5_outcome": s5,
                "archived": False,
            })
            return outcome

        self._archive_ids.add(archive_id)
        self._z_ids.add(z_id)
        self._formula_ids.add(formula)
        self._buckets.add(bucket37)
        self.appended_records += 1
        outcome = f"ARCHIVED_NEW_{side}"
        self._record_outcome(formula, outcome)
        self._recent.append({
            "archive_id": archive_id,
            "formula_id": formula,
            "z_id": z_id,
            "c2_fingerprint": fingerprint,
            "bucket37": bucket37,
            "outcome": outcome,
            "s5_outcome": s5,
            "archived": True,
            "new_record": True,
        })
        return outcome

    def status(self) -> dict[str, Any]:
        with self._lock:
            return self._status_locked()

    def _status_locked(self) -> dict[str, Any]:
        archive_bytes = 0
        try:
            if self.archive_path.exists():
                archive_bytes = int(self.archive_path.stat().st_size)
        except OSError:
            archive_bytes = -1
        return {
            "schema": SCHEMA,
            "mode": SCHEMA,
            "enabled": self.enabled,
            "authority": "PERSISTENCE_ONLY",
            "source_of_truth": "S5_FAST_INDEX_OUTCOME_PLUS_EXISTING_C2_STRUCTURAL_STATE",
            "observations": self.observations,
            "eligible_s5": self.eligible_s5,
            "appended_records": self.appended_records,
            "already_present": self.already_present,
            "blocked_s5_other": self.blocked_s5_other,
            "blocked_missing_formula": self.blocked_missing_formula,
            "blocked_missing_z": self.blocked_missing_z,
            "blocked_formula_mismatch": self.blocked_formula_mismatch,
            "blocked_archive_unavailable": self.blocked_archive_unavailable,
            "write_errors": self.write_errors,
            "available": self.available,
            "load_errors": self.load_errors,
            "load_error_summary": self.load_error_summary,
            "loaded_records": self.loaded_records,
            "loaded_duplicate_ids": self.loaded_duplicate_ids,
            "physical_records_seen": self.loaded_records + self.appended_records,
            "unique_archive_records": len(self._archive_ids),
            "unique_z_archived": len({z for z in self._z_ids if z}),
            "unique_formulas_archived": len({f for f in self._formula_ids if f}),
            "occupied_buckets_archived": len(self._buckets),
            "archive_bytes": archive_bytes,
            "archive_path": str(self.archive_path),
            "reference_sides": dict(sorted(self.reference_sides.items())),
            "by_formula": {k: dict(v) for k, v in sorted(self.by_formula.items())},
            "recent_limit": RECENT_LIMIT,
            "recent": list(self._recent),
            "archive_definition": "ONE_APPEND_ONLY_RECORD_PER_UNIQUE_S5_C2_FORMULA_Z_ENTRY",
            "record_schema": RECORD_SCHEMA,
            "record_content_scope": "C2_CANONICAL_STRUCTURAL_STATE_PLUS_S5_FORMULA_Z_BUCKET_CONTEXT",
            "persistent": True,
            "append_only": True,
            "fsync_on_new_record": True,
            "deduplicates_by_archive_id": True,
            "thread_safe_deduplication": True,
            "preexisting_duplicate_lines_preserved": True,
            "rewrites_existing_records": False,
            "archive_id_is_scientific_identity": False,
            "archive_id_is_c2_fingerprint": False,
            "full_c2_fingerprint_preserved": True,
            "uses_exact_c3_bucket_function": True,
            "complete_path_provenance_claim": False,
            "s2_lineage_replaced": False,
            "co2_proof_chain_input": True,
            "hash_chain_enabled": False,
            "co2_owns_hash_chain": True,
            "archive_copy_only": True,
            "age_policy_defined": False,
            "hot_removal_enabled": False,
            "hot_evictions": 0,
            "s5_fast_index_mutated": False,
            "scientific_proof_claim": False,
            "validation_state_mutated": False,
            "controls_routing": False,
            "controls_scheduling": False,
            "controls_calculation": False,
            "reserves_resources": False,
            "executes_replay": False,
            "schedules_replay": False,
            "compute_skips": 0,
            "value_mutated": False,
            "proof_promotion": False,
        }
