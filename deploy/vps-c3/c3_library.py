from __future__ import annotations

import os
from typing import Any


SCHEMA = "BRUTUS_C3_LIBRARY37_V1"
BUCKET_COUNT = 37
DEFAULT_MAX_ENTRIES = 131_072


def _env_max_entries() -> int:
    raw = os.getenv("BROTO_C3_MAX_ENTRIES", str(DEFAULT_MAX_ENTRIES)).strip()
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = DEFAULT_MAX_ENTRIES
    return max(BUCKET_COUNT, min(value, 2_000_000))


def _fingerprint_bytes(fingerprint: str) -> bytes:
    if not isinstance(fingerprint, str) or not fingerprint.startswith("C2-"):
        raise ValueError("C3 requires a C2- fingerprint")
    raw = fingerprint[3:]
    if len(raw) != 64:
        raise ValueError("C2 fingerprint must contain 64 hex characters")
    try:
        return bytes.fromhex(raw)
    except ValueError as exc:
        raise ValueError("C2 fingerprint is not valid hex") from exc


class C3Library37:
    """Bounded in-memory shadow library keyed by exact C2 fingerprints.

    C3 only records whether a canonical C2 structural fingerprint has been seen.
    It does not skip computation, mutate packets, influence scheduling, or promote proof.
    Full 256-bit C2 keys define identity; the 37-way bucket is routing only.
    """

    def __init__(self, max_entries: int | None = None) -> None:
        limit = _env_max_entries() if max_entries is None else int(max_entries)
        self.max_entries = max(BUCKET_COUNT, min(limit, 2_000_000))
        self._buckets: list[dict[bytes, int]] = [dict() for _ in range(BUCKET_COUNT)]
        self.observations = 0
        self.hits = 0
        self.misses = 0
        self.unique_entries = 0
        self.capacity_rejections = 0
        self.first_fingerprint: str | None = None
        self.last_fingerprint: str | None = None

    @staticmethod
    def bucket_for(fingerprint: str) -> int:
        key = _fingerprint_bytes(fingerprint)
        return int.from_bytes(key[:8], "big") % BUCKET_COUNT

    def observe(self, fingerprint: str) -> bool:
        key = _fingerprint_bytes(fingerprint)
        bucket_id = int.from_bytes(key[:8], "big") % BUCKET_COUNT
        bucket = self._buckets[bucket_id]
        self.observations += 1
        if self.first_fingerprint is None:
            self.first_fingerprint = fingerprint
        self.last_fingerprint = fingerprint

        previous = bucket.get(key)
        if previous is not None:
            bucket[key] = previous + 1
            self.hits += 1
            return True

        self.misses += 1
        if self.unique_entries >= self.max_entries:
            self.capacity_rejections += 1
            return False

        bucket[key] = 1
        self.unique_entries += 1
        return False

    def contains(self, fingerprint: str) -> bool:
        key = _fingerprint_bytes(fingerprint)
        bucket_id = int.from_bytes(key[:8], "big") % BUCKET_COUNT
        return key in self._buckets[bucket_id]

    def count(self, fingerprint: str) -> int:
        key = _fingerprint_bytes(fingerprint)
        bucket_id = int.from_bytes(key[:8], "big") % BUCKET_COUNT
        return int(self._buckets[bucket_id].get(key, 0))

    def status(self) -> dict[str, Any]:
        occupancy = [len(bucket) for bucket in self._buckets]
        hit_rate = (self.hits / self.observations) if self.observations else 0.0
        return {
            "schema": SCHEMA,
            "mode": SCHEMA,
            "authority": "SHADOW_ONLY",
            "bucket_count": BUCKET_COUNT,
            "bucket_routing": "first_64_bits_of_full_C2_sha256_mod_37",
            "identity_key": "full_256_bit_C2_fingerprint",
            "observations": self.observations,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "unique_entries": self.unique_entries,
            "max_entries": self.max_entries,
            "capacity_rejections": self.capacity_rejections,
            "bucket_occupancy": occupancy,
            "occupied_buckets": sum(1 for value in occupancy if value > 0),
            "max_bucket_entries": max(occupancy, default=0),
            "first_fingerprint": self.first_fingerprint,
            "last_fingerprint": self.last_fingerprint,
            "persistent": False,
            "query_before_compute": False,
            "compute_skips": 0,
            "scheduling_influence": False,
            "value_mutated": False,
            "proof_promotion": False,
        }
