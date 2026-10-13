from __future__ import annotations

import os
from collections import deque
from hashlib import blake2b
from typing import Any

SCHEMA = "BRUTUS_T5_OPERATIONAL_INDEPENDENCE_V1"
RECENT_LIMIT = 37
DEFAULT_MAX_TARGETS = 16_384

TIERS = (
    "NOT_CONVERGENT",
    "CONVERGENT_SAME_LINEAGE",
    "DIVERSE_1_AXIS",
    "DIVERSE_2_AXES_REVIEW",
    "INDEPENDENCE_CANDIDATE",
)


def _env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)).strip())
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))


def _target_sig(z_id: str) -> bytes:
    return blake2b(z_id.encode("utf-8"), digest_size=12).digest()


class T5OperationalIndependence:
    """Shadow-only operational independence candidate classifier.

    T5 never proves scientific independence. It consumes the read-only T4 target
    summary after T4 has observed a packet. A target must already have at least
    two distinct C2 structures (real T4 convergence). Diversity is then measured
    on three operational axes: T1 family, Z origin, and Z parent.

    Only a convergent target with diversity on all three axes is labelled
    INDEPENDENCE_CANDIDATE. Two axes are kept as REVIEW, not promoted.
    """

    def __init__(self, max_targets: int | None = None) -> None:
        self.max_targets = max_targets if max_targets is not None else _env_int(
            "BROTO_T5_MAX_TARGETS", DEFAULT_MAX_TARGETS, 37, 131_072
        )
        self._tiers: dict[bytes, int] = {}
        self.observations = 0
        self.retained_observations = 0
        self.missing_z = 0
        self.untracked_capacity = 0
        self.t4_consistency_conflicts = 0
        self.convergent_observations = 0
        self.nonconvergent_observations = 0
        self.exact_repeat_observations = 0
        self.tier_target_counts = {name: 0 for name in TIERS}
        self.tier_observation_counts = {name: 0 for name in TIERS}
        self.tier_upgrade_events = 0
        self.independence_candidate_targets = 0
        self.independence_candidate_observations = 0
        self.two_axis_review_targets = 0
        self.max_axes_seen = 0
        self.last_tier: str | None = None
        self._recent: deque[dict[str, Any]] = deque(maxlen=RECENT_LIMIT)

    @staticmethod
    def classify_summary(summary: dict[str, Any]) -> tuple[str, int]:
        distinct_c2 = int(summary.get("distinct_c2") or 0)
        if distinct_c2 < 2 or not bool(summary.get("convergent")):
            return "NOT_CONVERGENT", 0
        axes = sum(
            int(summary.get(key) or 0) >= 2
            for key in ("families", "origins", "parents")
        )
        if axes >= 3:
            return "INDEPENDENCE_CANDIDATE", 3
        if axes == 2:
            return "DIVERSE_2_AXES_REVIEW", 2
        if axes == 1:
            return "DIVERSE_1_AXIS", 1
        return "CONVERGENT_SAME_LINEAGE", 0

    def observe(
        self,
        packet: Any,
        fingerprint: str,
        *,
        t4_event: str,
        t4_summary: dict[str, Any] | None,
    ) -> str:
        if not isinstance(fingerprint, str) or not fingerprint.startswith("C2-"):
            raise ValueError("T5 requires a C2- fingerprint")
        self.observations += 1
        z_id = getattr(packet, "z_id", None)
        if not isinstance(z_id, str) or not z_id.startswith("Z-"):
            self.missing_z += 1
            self.last_tier = "NOT_CONVERGENT"
            return self.last_tier
        summary = dict(t4_summary or {})
        tier, axes = self.classify_summary(summary)
        self.max_axes_seen = max(self.max_axes_seen, axes)
        if tier == "NOT_CONVERGENT":
            self.nonconvergent_observations += 1
        else:
            self.convergent_observations += 1
        if str(t4_event or "") == "EXACT_REPEAT_NOT_CONVERGENCE":
            self.exact_repeat_observations += 1
        if str(t4_event or "").startswith("STRUCTURAL_CONVERGENCE") and tier == "NOT_CONVERGENT":
            self.t4_consistency_conflicts += 1

        sig = _target_sig(z_id)
        previous = self._tiers.get(sig)
        tier_index = TIERS.index(tier)
        if previous is None:
            if len(self._tiers) >= self.max_targets:
                self.untracked_capacity += 1
                self.last_tier = tier
                self.tier_observation_counts[tier] += 1
                return tier
            self._tiers[sig] = tier_index
            self.tier_target_counts[tier] += 1
            if tier == "INDEPENDENCE_CANDIDATE":
                self.independence_candidate_targets += 1
            if tier == "DIVERSE_2_AXES_REVIEW":
                self.two_axis_review_targets += 1
        elif tier_index > previous:
            old_tier = TIERS[previous]
            self.tier_target_counts[old_tier] -= 1
            self.tier_target_counts[tier] += 1
            self._tiers[sig] = tier_index
            self.tier_upgrade_events += 1
            if tier == "INDEPENDENCE_CANDIDATE":
                self.independence_candidate_targets += 1
            if tier == "DIVERSE_2_AXES_REVIEW":
                self.two_axis_review_targets += 1
        elif tier_index < previous:
            # T4 summaries are monotone for a retained target. A downgrade means
            # the consumer saw an inconsistent summary and must not rewrite history.
            self.t4_consistency_conflicts += 1
            tier = TIERS[previous]
            tier_index = previous

        self.retained_observations += 1
        self.tier_observation_counts[tier] += 1
        if tier == "INDEPENDENCE_CANDIDATE":
            self.independence_candidate_observations += 1
        self.last_tier = tier
        self._recent.append({
            "z_id": z_id,
            "fingerprint": fingerprint,
            "t4_event": t4_event,
            "tier": tier,
            "diversity_axes": axes,
            "distinct_c2": int(summary.get("distinct_c2") or 0),
            "families": int(summary.get("families") or 0),
            "origins": int(summary.get("origins") or 0),
            "parents": int(summary.get("parents") or 0),
        })
        return tier

    def status(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "mode": SCHEMA,
            "authority": "SHADOW_ONLY",
            "source_of_truth": "T4_READ_ONLY_TARGET_SUMMARY",
            "observations": self.observations,
            "retained_observations": self.retained_observations,
            "tracked_targets": len(self._tiers),
            "max_targets": self.max_targets,
            "missing_z": self.missing_z,
            "untracked_capacity": self.untracked_capacity,
            "t4_consistency_conflicts": self.t4_consistency_conflicts,
            "convergent_observations": self.convergent_observations,
            "nonconvergent_observations": self.nonconvergent_observations,
            "exact_repeat_observations": self.exact_repeat_observations,
            "tier_target_counts": dict(self.tier_target_counts),
            "tier_observation_counts": dict(self.tier_observation_counts),
            "tier_upgrade_events": self.tier_upgrade_events,
            "independence_candidate_targets": self.independence_candidate_targets,
            "independence_candidate_observations": self.independence_candidate_observations,
            "two_axis_review_targets": self.two_axis_review_targets,
            "max_axes_seen": self.max_axes_seen,
            "candidate_rule": "T4 convergence + >=2 families + >=2 Z origins + >=2 Z parents",
            "last_tier": self.last_tier,
            "recent_limit": RECENT_LIMIT,
            "recent": list(self._recent),
            "scientific_independence_claim": False,
            "operational_candidate_only": True,
            "deduplication_applied": False,
            "packets_collapsed": 0,
            "controls_routing": False,
            "controls_scheduling": False,
            "compute_skips": 0,
            "value_mutated": False,
            "proof_promotion": False,
            "persistent": False,
        }
