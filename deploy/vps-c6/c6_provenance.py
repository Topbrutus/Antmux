from __future__ import annotations

import os
from collections import deque
from dataclasses import dataclass, field
from hashlib import blake2b
from typing import Any


SCHEMA = "BRUTUS_C6_PROVENANCE_V1"
DEFAULT_MAX_TARGETS = 16_384
DEFAULT_SIGNATURE_CAP = 16
RECENT_LIMIT = 37


def _env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)).strip())
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))


def _sig(value: str) -> bytes:
    return blake2b(value.encode("utf-8"), digest_size=8).digest()


def _chain_text(chain: tuple[str, ...]) -> str:
    return "|".join(chain) if chain else "ROOT"


@dataclass
class ProvenanceRecord:
    observations: int = 0
    fingerprints: set[bytes] = field(default_factory=set)
    paths: set[bytes] = field(default_factory=set)
    formulas: set[bytes] = field(default_factory=set)
    parents: set[bytes] = field(default_factory=set)
    origins: set[bytes] = field(default_factory=set)
    signature_overflow: int = 0
    independence_candidate: bool = False


class C6Provenance:
    """Bounded shadow provenance aggregator keyed by canonical Z target.

    Exact structural identity remains C2. C6 groups multiple exact C2 traces that
    converge on the same Z-ID and measures route diversity using compact digests.
    It never claims scientific independence or proof.
    """

    def __init__(self, max_targets: int | None = None, signature_cap: int | None = None) -> None:
        self.max_targets = max_targets if max_targets is not None else _env_int(
            "BROTO_C6_MAX_TARGETS", DEFAULT_MAX_TARGETS, 37, 262_144
        )
        self.signature_cap = signature_cap if signature_cap is not None else _env_int(
            "BROTO_C6_SIGNATURE_CAP", DEFAULT_SIGNATURE_CAP, 2, 128
        )
        self._records: dict[str, ProvenanceRecord] = {}
        self.observations = 0
        self.retained_observations = 0
        self.untracked_capacity = 0
        self.missing_z = 0
        self.multi_path_targets = 0
        self.multi_formula_targets = 0
        self.multi_parent_targets = 0
        self.multi_origin_targets = 0
        self.independence_candidate_targets = 0
        self._recent: deque[dict[str, Any]] = deque(maxlen=RECENT_LIMIT)

    def _add(self, bucket: set[bytes], signature: bytes, rec: ProvenanceRecord) -> bool:
        if signature in bucket:
            return False
        if len(bucket) >= self.signature_cap:
            rec.signature_overflow += 1
            return False
        bucket.add(signature)
        return True

    @staticmethod
    def _candidate(rec: ProvenanceRecord) -> bool:
        # Conservative engineering heuristic only. Two distinct origins are the
        # strongest signal available here; otherwise require both parent and formula diversity.
        return len(rec.origins) >= 2 or (len(rec.parents) >= 2 and len(rec.formulas) >= 2)

    def observe(self, packet: Any, fingerprint: str, *, c3_retained: bool, c5_class: str | None) -> None:
        if not isinstance(fingerprint, str) or not fingerprint.startswith("C2-"):
            raise ValueError("C6 requires a C2- fingerprint")
        self.observations += 1
        if not c3_retained:
            self.untracked_capacity += 1
            return
        z_id = getattr(packet, "z_id", None)
        if not z_id:
            self.missing_z += 1
            return

        rec = self._records.get(z_id)
        if rec is None:
            if len(self._records) >= self.max_targets:
                self.untracked_capacity += 1
                return
            rec = ProvenanceRecord()
            self._records[z_id] = rec

        self.retained_observations += 1
        rec.observations += 1

        before_path = len(rec.paths)
        before_formula = len(rec.formulas)
        before_parent = len(rec.parents)
        before_origin = len(rec.origins)

        self._add(rec.fingerprints, _sig(fingerprint), rec)
        self._add(rec.paths, _sig(str(getattr(packet, "branch_path", "ROOT"))), rec)
        self._add(rec.formulas, _sig(_chain_text(tuple(getattr(packet, "formula_chain", ())))), rec)
        self._add(rec.parents, _sig(str(getattr(packet, "z_parent_id", None) or "ROOT")), rec)
        self._add(rec.origins, _sig(str(getattr(packet, "z_origin_id", None) or z_id)), rec)

        if before_path < 2 <= len(rec.paths):
            self.multi_path_targets += 1
        if before_formula < 2 <= len(rec.formulas):
            self.multi_formula_targets += 1
        if before_parent < 2 <= len(rec.parents):
            self.multi_parent_targets += 1
        if before_origin < 2 <= len(rec.origins):
            self.multi_origin_targets += 1

        if not rec.independence_candidate and self._candidate(rec):
            rec.independence_candidate = True
            self.independence_candidate_targets += 1

        self._recent.append({
            "z_id": z_id,
            "c5_class": c5_class,
            "observations": rec.observations,
            "distinct_c2": len(rec.fingerprints),
            "distinct_paths": len(rec.paths),
            "distinct_formula_chains": len(rec.formulas),
            "distinct_parents": len(rec.parents),
            "distinct_origins": len(rec.origins),
            "operational_independence_candidate": rec.independence_candidate,
        })

    def status(self) -> dict[str, Any]:
        max_paths = max((len(r.paths) for r in self._records.values()), default=0)
        max_formulas = max((len(r.formulas) for r in self._records.values()), default=0)
        max_parents = max((len(r.parents) for r in self._records.values()), default=0)
        max_origins = max((len(r.origins) for r in self._records.values()), default=0)
        return {
            "schema": SCHEMA,
            "mode": SCHEMA,
            "authority": "SHADOW_ONLY",
            "grouping_key": "Z_ID_CANONICAL_VALUE_TARGET",
            "exact_trace_identity": "C2_FINGERPRINT",
            "observations": self.observations,
            "retained_observations": self.retained_observations,
            "tracked_targets": len(self._records),
            "max_targets": self.max_targets,
            "signature_cap_per_dimension": self.signature_cap,
            "untracked_capacity": self.untracked_capacity,
            "missing_z": self.missing_z,
            "multi_path_targets": self.multi_path_targets,
            "multi_formula_targets": self.multi_formula_targets,
            "multi_parent_targets": self.multi_parent_targets,
            "multi_origin_targets": self.multi_origin_targets,
            "operational_independence_candidate_targets": self.independence_candidate_targets,
            "max_distinct_paths": max_paths,
            "max_distinct_formula_chains": max_formulas,
            "max_distinct_parents": max_parents,
            "max_distinct_origins": max_origins,
            "recent_limit": RECENT_LIMIT,
            "recent": list(self._recent),
            "independence_rule": "origins>=2 OR (parents>=2 AND formula_chains>=2)",
            "scientific_independence_claim": False,
            "scientific_discovery_claim": False,
            "controls_scheduling": False,
            "compute_skips": 0,
            "value_mutated": False,
            "proof_promotion": False,
            "persistent": False,
        }
