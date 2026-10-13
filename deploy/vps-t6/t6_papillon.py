from __future__ import annotations

from collections import deque
from typing import Any

from .papillon_engine import Papillon144

SCHEMA = "BRUTUS_T6_PAPILLON_AFFINITY_V1"
RECENT_LIMIT = 37
EXPECTED_SHARDS = 144

AFFINITY_BY_T5 = {
    "NOT_CONVERGENT": "PAPILLON_BASELINE_OBSERVE",
    "CONVERGENT_SAME_LINEAGE": "PAPILLON_CONVERGENT_OBSERVE",
    "DIVERSE_1_AXIS": "PAPILLON_LOW_REVIEW",
    "DIVERSE_2_AXES_REVIEW": "PAPILLON_MEDIUM_REVIEW",
    "INDEPENDENCE_CANDIDATE": "PAPILLON_HIGH_REVIEW",
}


class T6PapillonAffinity:
    """Shadow-only projection of T5 observations onto Papillon144 shards.

    T6 does not evaluate formulas, mutate the cache, choose routes, alter
    scheduling, or skip work. It calls Papillon144.shard_index(), a pure public
    view of the exact shard function already used by the live Papillon cache.
    """

    def __init__(self, shard_count: int = EXPECTED_SHARDS) -> None:
        if int(shard_count) != EXPECTED_SHARDS:
            raise ValueError("T6 requires the live Papillon144 geometry")
        self.shard_count = EXPECTED_SHARDS
        self.observations = 0
        self.shard_counts = [0] * self.shard_count
        self.affinity_counts = {name: 0 for name in AFFINITY_BY_T5.values()}
        self.t5_tier_counts = {name: 0 for name in AFFINITY_BY_T5}
        self.candidate_observations = 0
        self.candidate_shards: set[int] = set()
        self.shards_touched: set[int] = set()
        self.invalid_t5_tier = 0
        self.last_shard: int | None = None
        self.last_affinity: str | None = None
        self._recent: deque[dict[str, Any]] = deque(maxlen=RECENT_LIMIT)

    @staticmethod
    def _terminal_formula(packet: Any) -> str:
        chain = tuple(str(x) for x in (getattr(packet, "formula_chain", ()) or ()))
        return chain[-1] if chain else "ROOT"

    def observe(self, packet: Any, fingerprint: str, *, t5_tier: str, papillon: Papillon144) -> str:
        if not isinstance(fingerprint, str) or not fingerprint.startswith("C2-"):
            raise ValueError("T6 requires a C2- fingerprint")
        if papillon.shard_count != self.shard_count:
            raise ValueError("T6/Papillon shard geometry mismatch")
        tier = str(t5_tier or "")
        affinity = AFFINITY_BY_T5.get(tier)
        if affinity is None:
            self.invalid_t5_tier += 1
            tier = "NOT_CONVERGENT"
            affinity = AFFINITY_BY_T5[tier]
        formula_id = self._terminal_formula(packet)
        shard = int(papillon.shard_index(formula_id, int(getattr(packet, "value"))))
        if not 0 <= shard < self.shard_count:
            raise ValueError("Papillon shard index out of bounds")
        self.observations += 1
        self.shard_counts[shard] += 1
        self.shards_touched.add(shard)
        self.t5_tier_counts[tier] += 1
        self.affinity_counts[affinity] += 1
        if tier == "INDEPENDENCE_CANDIDATE":
            self.candidate_observations += 1
            self.candidate_shards.add(shard)
        self.last_shard = shard
        self.last_affinity = affinity
        self._recent.append({
            "fingerprint": fingerprint,
            "z_id": getattr(packet, "z_id", None),
            "formula_id": formula_id,
            "value": str(getattr(packet, "value")),
            "t5_tier": tier,
            "affinity": affinity,
            "papillon_shard": shard,
        })
        return affinity

    def status(self) -> dict[str, Any]:
        nonzero = [(idx, count) for idx, count in enumerate(self.shard_counts) if count]
        hottest = sorted(nonzero, key=lambda row: (-row[1], row[0]))[:10]
        return {
            "schema": SCHEMA,
            "mode": SCHEMA,
            "authority": "SHADOW_ONLY",
            "source_of_truth": "PAPILLON144_PUBLIC_SHARD_INDEX_PLUS_T5_TIER",
            "observations": self.observations,
            "shard_count": self.shard_count,
            "shards_touched": len(self.shards_touched),
            "candidate_shards": len(self.candidate_shards),
            "candidate_observations": self.candidate_observations,
            "t5_tier_counts": dict(self.t5_tier_counts),
            "affinity_counts": dict(self.affinity_counts),
            "hottest_shards": [{"shard": i, "observations": n} for i, n in hottest],
            "max_shard_load": max(self.shard_counts) if self.shard_counts else 0,
            "invalid_t5_tier": self.invalid_t5_tier,
            "last_shard": self.last_shard,
            "last_affinity": self.last_affinity,
            "recent_limit": RECENT_LIMIT,
            "recent": list(self._recent),
            "papillon_cache_mutated": False,
            "papillon_policy_changed": False,
            "actual_papillon_routes_applied": 0,
            "controls_papillon": False,
            "controls_routing": False,
            "controls_scheduling": False,
            "compute_skips": 0,
            "value_mutated": False,
            "proof_promotion": False,
            "scientific_claim": False,
            "persistent": False,
        }