from __future__ import annotations

from collections import deque
from typing import Any


SCHEMA = "BRUTUS_C5_STRUCTURAL_RARITY_V1"
RECENT_LIMIT = 37


class C5StructuralRarity:
    """Shadow rarity classifier driven by the exact C3 observation count.

    C5 does not influence scheduling. It classifies recurrence of a retained
    C2 fingerprint using the same tier boundaries as the Papillon rarity law,
    but the subject is different: exact structural fingerprints, not values.
    """

    TIERS = (
        (2, "RARE_8", 8),
        (4, "RARE_6", 6),
        (8, "SCARCE_4", 4),
        (16, "CONVERGENT_2", 2),
        (None, "COMMON_1_CONTROL", 1),
    )

    def __init__(self) -> None:
        self.observations = 0
        self.retained_observations = 0
        self.untracked_capacity = 0
        self.class_counts = {name: 0 for _, name, _ in self.TIERS}
        self.last_classification: str | None = None
        self.last_observation_count = 0
        self.max_observation_count = 0
        self._recent: deque[dict[str, Any]] = deque(maxlen=RECENT_LIMIT)

    @classmethod
    def classify_count(cls, observation_count: int) -> tuple[str, int]:
        count = int(observation_count)
        if count < 1:
            raise ValueError("C5 observation_count must be >= 1")
        for upper, name, rights in cls.TIERS:
            if upper is None or count <= upper:
                return name, rights
        raise AssertionError("unreachable")

    def observe(
        self,
        fingerprint: str,
        *,
        observation_count: int,
        c3_retained: bool,
    ) -> str:
        if not isinstance(fingerprint, str) or not fingerprint.startswith("C2-"):
            raise ValueError("C5 requires a C2- fingerprint")

        self.observations += 1
        if not c3_retained:
            self.untracked_capacity += 1
            self.last_classification = "UNTRACKED_CAPACITY"
            self.last_observation_count = 0
            return "UNTRACKED_CAPACITY"

        count = int(observation_count)
        name, rights = self.classify_count(count)
        self.retained_observations += 1
        self.class_counts[name] += 1
        self.last_classification = name
        self.last_observation_count = count
        self.max_observation_count = max(self.max_observation_count, count)
        self._recent.append(
            {
                "fingerprint": fingerprint,
                "count": count,
                "class": name,
                "reference_rights": rights,
            }
        )
        return name

    def status(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "mode": SCHEMA,
            "authority": "SHADOW_ONLY",
            "source_of_truth": "C3_EXACT_FINGERPRINT_COUNT",
            "subject": "C2_STRUCTURAL_FINGERPRINT_RECURRENCE",
            "observations": self.observations,
            "retained_observations": self.retained_observations,
            "untracked_capacity": self.untracked_capacity,
            "class_counts": dict(self.class_counts),
            "tiers": [
                {"hits": "1-2", "class": "RARE_8", "reference_rights": 8},
                {"hits": "3-4", "class": "RARE_6", "reference_rights": 6},
                {"hits": "5-8", "class": "SCARCE_4", "reference_rights": 4},
                {"hits": "9-16", "class": "CONVERGENT_2", "reference_rights": 2},
                {"hits": "17+", "class": "COMMON_1_CONTROL", "reference_rights": 1},
            ],
            "last_classification": self.last_classification,
            "last_observation_count": self.last_observation_count,
            "max_observation_count": self.max_observation_count,
            "recent_limit": RECENT_LIMIT,
            "recent": list(self._recent),
            "controls_scheduling": False,
            "reference_rights_applied": False,
            "scientific_rarity_claim": False,
            "persistent": False,
            "query_before_compute": False,
            "compute_skips": 0,
            "value_mutated": False,
            "proof_promotion": False,
        }
