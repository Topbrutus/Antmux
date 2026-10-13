from __future__ import annotations

import os
from collections import Counter, defaultdict, deque
from typing import Any

from .c3_library import BUCKET_COUNT, C3Library37
from .engine import c2_fingerprint

SCHEMA = "BRUTUS_S5_FAST_INDEX_V1"
RECENT_LIMIT = 37
DEFAULT_MAX_ENTRIES = 131_072
VALID_S4 = frozenset({
    "FORMULA_INDEXED_AT_OR_ABOVE_REFERENCE",
    "FORMULA_INDEXED_BELOW_REFERENCE",
})


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "1" if default else "0").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _env_max_entries() -> int:
    raw = os.getenv("BROTO_S5_MAX_ENTRIES", str(DEFAULT_MAX_ENTRIES)).strip()
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = DEFAULT_MAX_ENTRIES
    return max(BUCKET_COUNT, min(value, 2_000_000))


class S5FastIndexTelemetry:
    """Shadow-only 37-way fast index downstream of S4 Formula Index.

    The Colonne 37 prototype represents S5 with ``bucket37``. Rather than
    inventing a new partition, S5 v1 reuses the already-validated C2 structural
    fingerprint and the exact C3 Library37 bucket function:

        fp = c2_fingerprint(out)
        bucket37 = C3Library37.bucket_for(fp)

    The full C2 fingerprint remains the lookup identity. The 37-way bucket is
    only an access accelerator. S5 neither skips computation nor changes S4,
    C3, formulas, Z identity, scheduling, validation, or proof state.
    """

    def __init__(self, max_entries: int | None = None) -> None:
        self.enabled = _env_flag("BROTO_S5_ENABLED", False)
        limit = _env_max_entries() if max_entries is None else int(max_entries)
        self.max_entries = max(BUCKET_COUNT, min(limit, 2_000_000))

        self.observations = 0
        self.indexed = 0
        self.blocked_s4_other = 0
        self.blocked_missing_formula = 0
        self.blocked_missing_z = 0
        self.blocked_formula_mismatch = 0
        self.capacity_rejections = 0

        self._buckets: list[dict[str, set[tuple[str, str]]]] = [dict() for _ in range(BUCKET_COUNT)]
        self.entry_counts: Counter[tuple[str, str, str]] = Counter()
        self.fingerprint_counts: Counter[str] = Counter()
        self.bucket_observations: Counter[int] = Counter()
        self.buckets_by_z: dict[str, set[int]] = defaultdict(set)
        self.fingerprints_by_z: dict[str, set[str]] = defaultdict(set)
        self.formulas_by_bucket: dict[int, set[str]] = defaultdict(set)
        self.reference_sides: Counter[str] = Counter()
        self.by_formula: dict[str, Counter[str]] = {}
        self._recent: deque[dict[str, Any]] = deque(maxlen=RECENT_LIMIT)

    def _record(self, formula_id: str, outcome: str) -> None:
        self.by_formula.setdefault(str(formula_id), Counter())[outcome] += 1

    @staticmethod
    def _terminal_formula(out: Any) -> str | None:
        chain = tuple(str(x) for x in (getattr(out, "formula_chain", ()) or ()))
        return chain[-1] if chain else None

    def lookup(self, fingerprint: str) -> set[tuple[str, str]]:
        """Return observed (formula_id, z_id) pairs for one exact C2 fingerprint."""
        bucket = C3Library37.bucket_for(fingerprint)
        return set(self._buckets[bucket].get(str(fingerprint), set()))

    def observe(self, formula_id: str, source: Any, out: Any, s4_outcome: str) -> str:
        if not self.enabled:
            return "DISABLED"

        self.observations += 1
        s4 = str(s4_outcome).upper()
        formula = str(formula_id or "").strip()

        if s4 not in VALID_S4:
            self.blocked_s4_other += 1
            outcome = "BLOCKED_S4_OTHER"
            self._record(formula or "<MISSING>", outcome)
            self._recent.append({"formula_id": formula or None, "outcome": outcome, "s4_outcome": s4, "indexed": False})
            return outcome

        if not formula:
            self.blocked_missing_formula += 1
            outcome = "BLOCKED_MISSING_FORMULA_ID"
            self._record("<MISSING>", outcome)
            self._recent.append({"formula_id": None, "outcome": outcome, "s4_outcome": s4, "indexed": False})
            return outcome

        z_raw = getattr(out, "z_id", None)
        if not z_raw:
            self.blocked_missing_z += 1
            outcome = "BLOCKED_MISSING_Z_ID"
            self._record(formula, outcome)
            self._recent.append({"formula_id": formula, "outcome": outcome, "s4_outcome": s4, "indexed": False})
            return outcome

        terminal = self._terminal_formula(out)
        if terminal != formula:
            self.blocked_formula_mismatch += 1
            outcome = "BLOCKED_FORMULA_CHAIN_MISMATCH"
            self._record(formula, outcome)
            self._recent.append({
                "formula_id": formula,
                "terminal_formula": terminal,
                "outcome": outcome,
                "s4_outcome": s4,
                "indexed": False,
            })
            return outcome

        fingerprint = c2_fingerprint(out)
        bucket37 = C3Library37.bucket_for(fingerprint)
        z_id = str(z_raw)
        pair = (formula, z_id)
        entry = (fingerprint, formula, z_id)
        bucket = self._buckets[bucket37]

        is_new_fingerprint = fingerprint not in bucket
        is_new_entry = entry not in self.entry_counts
        if is_new_entry and len(self.entry_counts) >= self.max_entries:
            self.capacity_rejections += 1
            outcome = "BLOCKED_CAPACITY"
            self._record(formula, outcome)
            self._recent.append({
                "formula_id": formula,
                "z_id": z_id,
                "c2_fingerprint": fingerprint,
                "bucket37": bucket37,
                "outcome": outcome,
                "s4_outcome": s4,
                "indexed": False,
            })
            return outcome

        bucket.setdefault(fingerprint, set()).add(pair)
        self.entry_counts[entry] += 1
        self.fingerprint_counts[fingerprint] += 1
        self.bucket_observations[bucket37] += 1
        self.buckets_by_z[z_id].add(bucket37)
        self.fingerprints_by_z[z_id].add(fingerprint)
        self.formulas_by_bucket[bucket37].add(formula)
        self.indexed += 1

        side = "AT_OR_ABOVE_REFERENCE" if s4.endswith("AT_OR_ABOVE_REFERENCE") else "BELOW_REFERENCE"
        self.reference_sides[side] += 1
        outcome = f"FAST_INDEXED_{side}"
        self._record(formula, outcome)
        self._recent.append({
            "formula_id": formula,
            "terminal_formula": terminal,
            "outcome": outcome,
            "s4_outcome": s4,
            "z_id": z_id,
            "c2_fingerprint": fingerprint,
            "bucket37": bucket37,
            "new_fingerprint_in_bucket": is_new_fingerprint,
            "new_fast_entry": is_new_entry,
            "entry_multiplicity": self.entry_counts[entry],
            "fingerprint_multiplicity": self.fingerprint_counts[fingerprint],
            "pairs_for_fingerprint": len(bucket[fingerprint]),
            "buckets_for_z": len(self.buckets_by_z[z_id]),
            "indexed": True,
        })
        return outcome

    def status(self) -> dict[str, Any]:
        occupancy = [len(bucket) for bucket in self._buckets]
        repeated_entries = sum(1 for count in self.entry_counts.values() if count > 1)
        multi_pair_fingerprints = sum(
            1 for bucket in self._buckets for pairs in bucket.values() if len(pairs) > 1
        )
        multi_bucket_z = sum(1 for buckets in self.buckets_by_z.values() if len(buckets) > 1)
        hottest_buckets = sorted(self.bucket_observations.items(), key=lambda row: (-row[1], row[0]))[:10]
        return {
            "schema": SCHEMA,
            "mode": SCHEMA,
            "enabled": self.enabled,
            "authority": "SHADOW_ONLY",
            "source_of_truth": "S4_INDEXED_RESULT_PLUS_EXISTING_C2_FINGERPRINT_AND_C3_LIBRARY37_BUCKET_FUNCTION",
            "observations": self.observations,
            "indexed": self.indexed,
            "blocked_s4_other": self.blocked_s4_other,
            "blocked_missing_formula": self.blocked_missing_formula,
            "blocked_missing_z": self.blocked_missing_z,
            "blocked_formula_mismatch": self.blocked_formula_mismatch,
            "capacity_rejections": self.capacity_rejections,
            "bucket_count": BUCKET_COUNT,
            "occupied_buckets": sum(1 for n in occupancy if n > 0),
            "bucket_occupancy": occupancy,
            "max_bucket_fingerprints": max(occupancy, default=0),
            "unique_fingerprints": len(self.fingerprint_counts),
            "unique_fast_entries": len(self.entry_counts),
            "repeated_fast_entries": repeated_entries,
            "max_fast_entry_multiplicity": max(self.entry_counts.values(), default=0),
            "max_fingerprint_multiplicity": max(self.fingerprint_counts.values(), default=0),
            "multi_pair_fingerprints": multi_pair_fingerprints,
            "unique_z_indexed": len(self.buckets_by_z),
            "multi_bucket_z": multi_bucket_z,
            "max_buckets_per_z": max((len(v) for v in self.buckets_by_z.values()), default=0),
            "unique_formulas_in_buckets": len({f for formulas in self.formulas_by_bucket.values() for f in formulas}),
            "hottest_buckets": [{"bucket37": b, "observations": n} for b, n in hottest_buckets],
            "max_entries": self.max_entries,
            "reference_sides": dict(sorted(self.reference_sides.items())),
            "by_formula": {k: dict(v) for k, v in sorted(self.by_formula.items())},
            "recent_limit": RECENT_LIMIT,
            "recent": list(self._recent),
            "fast_index_definition": "FULL_C2_FINGERPRINT_ROUTED_BY_EXACT_C3_LIBRARY37_BUCKET_TO_S4_FORMULA_Z_PAIR",
            "prototype_measurement_bucket37": True,
            "uses_existing_c2_fingerprint": True,
            "uses_exact_c3_bucket_function": True,
            "full_c2_fingerprint_is_identity": True,
            "bucket37_is_routing_only": True,
            "query_before_compute": False,
            "compute_skips": 0,
            "persistent": False,
            "creates_formula": False,
            "executes_formula": False,
            "selects_formula": False,
            "ranks_formula": False,
            "formula_registry_mutated": False,
            "z_identity_preserved": True,
            "s4_formula_index_mutated": False,
            "co1_archive_input": True,
            "scientific_proof_claim": False,
            "validation_state_mutated": False,
            "controls_routing": False,
            "controls_scheduling": False,
            "controls_calculation": False,
            "reserves_resources": False,
            "executes_replay": False,
            "schedules_replay": False,
            "value_mutated": False,
            "proof_promotion": False,
        }
