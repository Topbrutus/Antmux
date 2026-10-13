from __future__ import annotations

import os
from collections import deque
from dataclasses import dataclass
from hashlib import blake2b
from typing import Any

SCHEMA = "BRUTUS_T2_EXACT_DUPLICATE_V1"
RECENT_LIMIT = 37
DEFAULT_MAX_KEYS = 131_072


def _env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)).strip())
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))


def _path_sig(packet: Any) -> bytes:
    path = str(getattr(packet, "branch_path", "ROOT"))
    return blake2b(path.encode("utf-8"), digest_size=8).digest()


@dataclass
class DuplicateRecord:
    family: str
    first_path_sig: bytes
    observations: int = 1


class T2ExactDuplicate:
    """Bounded shadow exact-duplicate detector keyed by canonical C2 fingerprint.

    C2 is the exact structural identity. T2 never collapses packets or changes
    scheduling. It only counts recurrence, checks T1-family consistency, and
    notes whether an exact C2 reappears through a different physical path.
    """

    def __init__(self, max_keys: int | None = None) -> None:
        self.max_keys = max_keys if max_keys is not None else _env_int(
            "BROTO_T2_MAX_KEYS", DEFAULT_MAX_KEYS, 37, 1_048_576
        )
        self._records: dict[str, DuplicateRecord] = {}
        self.observations = 0
        self.retained_observations = 0
        self.unique_fingerprints = 0
        self.exact_duplicates = 0
        self.same_family_duplicates = 0
        self.same_path_duplicates = 0
        self.alternate_path_duplicates = 0
        self.cross_family_conflicts = 0
        self.untracked_capacity = 0
        self.max_duplicate_count = 1
        self.last_event: str | None = None
        self._recent: deque[dict[str, Any]] = deque(maxlen=RECENT_LIMIT)

    def observe(self, packet: Any, fingerprint: str, *, family: str) -> str:
        if not isinstance(fingerprint, str) or not fingerprint.startswith("C2-"):
            raise ValueError("T2 requires a C2- fingerprint")
        family = str(family or "OTHER")
        self.observations += 1
        sig = _path_sig(packet)

        rec = self._records.get(fingerprint)
        if rec is None:
            if len(self._records) >= self.max_keys:
                self.untracked_capacity += 1
                event = "UNTRACKED_CAPACITY"
                self.last_event = event
                self._recent.append({
                    "fingerprint": fingerprint,
                    "event": event,
                    "family": family,
                    "duplicate_count": None,
                    "alternate_path": None,
                })
                return event
            rec = DuplicateRecord(family=family, first_path_sig=sig)
            self._records[fingerprint] = rec
            self.retained_observations += 1
            self.unique_fingerprints += 1
            event = "UNIQUE"
        else:
            self.retained_observations += 1
            self.exact_duplicates += 1
            rec.observations += 1
            self.max_duplicate_count = max(self.max_duplicate_count, rec.observations)
            if family == rec.family:
                self.same_family_duplicates += 1
                if sig == rec.first_path_sig:
                    self.same_path_duplicates += 1
                    event = "EXACT_DUPLICATE_SAME_PATH"
                else:
                    self.alternate_path_duplicates += 1
                    event = "EXACT_DUPLICATE_ALT_PATH"
            else:
                self.cross_family_conflicts += 1
                event = "EXACT_DUPLICATE_FAMILY_CONFLICT"

        self.last_event = event
        self._recent.append({
            "fingerprint": fingerprint,
            "event": event,
            "family": family,
            "first_family": rec.family,
            "duplicate_count": rec.observations,
            "alternate_path": sig != rec.first_path_sig,
            "z_id": getattr(packet, "z_id", None),
        })
        return event

    def status(self) -> dict[str, Any]:
        duplicate_rate = 0.0 if self.retained_observations == 0 else self.exact_duplicates / self.retained_observations
        return {
            "schema": SCHEMA,
            "mode": SCHEMA,
            "authority": "SHADOW_ONLY",
            "identity_key": "C2_FINGERPRINT_EXACT",
            "observations": self.observations,
            "retained_observations": self.retained_observations,
            "tracked_fingerprints": len(self._records),
            "max_keys": self.max_keys,
            "unique_fingerprints": self.unique_fingerprints,
            "exact_duplicates": self.exact_duplicates,
            "duplicate_rate": duplicate_rate,
            "same_family_duplicates": self.same_family_duplicates,
            "same_path_duplicates": self.same_path_duplicates,
            "alternate_path_duplicates": self.alternate_path_duplicates,
            "cross_family_conflicts": self.cross_family_conflicts,
            "untracked_capacity": self.untracked_capacity,
            "max_duplicate_count": self.max_duplicate_count,
            "last_event": self.last_event,
            "recent_limit": RECENT_LIMIT,
            "recent": list(self._recent),
            "family_consistency_rule": "same C2 should retain the same T1 family",
            "physical_path_is_identity": False,
            "deduplication_applied": False,
            "packets_collapsed": 0,
            "controls_routing": False,
            "controls_scheduling": False,
            "compute_skips": 0,
            "value_mutated": False,
            "proof_promotion": False,
            "scientific_claim": False,
            "persistent": False,
        }
