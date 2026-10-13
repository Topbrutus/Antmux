from __future__ import annotations

from collections import deque
from typing import Any


SCHEMA = "BRUTUS_C4_NOVELTY_V1"
RECENT_NOVEL_LIMIT = 37


class C4Novelty:
    """Shadow novelty classifier driven strictly by C3 hit/miss outcomes.

    C4 labels an exact C2 fingerprint as KNOWN when C3 reports a hit and as
    NOVEL_CANDIDATE when C3 reports a miss. NOVEL_CANDIDATE is an engineering
    novelty label only; it is not a scientific discovery claim or proof.
    """

    def __init__(self) -> None:
        self.observations = 0
        self.known = 0
        self.novel_candidates = 0
        self.tracked_novel = 0
        self.untracked_capacity = 0
        self.first_novel_fingerprint: str | None = None
        self.last_novel_fingerprint: str | None = None
        self.last_classification: str | None = None
        self._recent_novel: deque[str] = deque(maxlen=RECENT_NOVEL_LIMIT)

    def observe(self, fingerprint: str, *, c3_hit: bool, c3_retained: bool) -> str:
        if not isinstance(fingerprint, str) or not fingerprint.startswith("C2-"):
            raise ValueError("C4 requires a C2- fingerprint")

        self.observations += 1
        if c3_hit:
            self.known += 1
            self.last_classification = "KNOWN"
            return "KNOWN"

        self.novel_candidates += 1
        if c3_retained:
            self.tracked_novel += 1
        else:
            self.untracked_capacity += 1
        if self.first_novel_fingerprint is None:
            self.first_novel_fingerprint = fingerprint
        self.last_novel_fingerprint = fingerprint
        self.last_classification = "NOVEL_CANDIDATE"
        self._recent_novel.append(fingerprint)
        return "NOVEL_CANDIDATE"

    def status(self) -> dict[str, Any]:
        novelty_rate = (self.novel_candidates / self.observations) if self.observations else 0.0
        known_rate = (self.known / self.observations) if self.observations else 0.0
        return {
            "schema": SCHEMA,
            "mode": SCHEMA,
            "authority": "SHADOW_ONLY",
            "source_of_truth": "C3_EXACT_HIT_MISS",
            "classification_known": "KNOWN",
            "classification_novel": "NOVEL_CANDIDATE",
            "observations": self.observations,
            "known": self.known,
            "novel_candidates": self.novel_candidates,
            "known_rate": known_rate,
            "novelty_rate": novelty_rate,
            "tracked_novel": self.tracked_novel,
            "untracked_capacity": self.untracked_capacity,
            "first_novel_fingerprint": self.first_novel_fingerprint,
            "last_novel_fingerprint": self.last_novel_fingerprint,
            "last_classification": self.last_classification,
            "recent_novel_limit": RECENT_NOVEL_LIMIT,
            "recent_novel_fingerprints": list(self._recent_novel),
            "scientific_discovery_claim": False,
            "persistent": False,
            "query_before_compute": False,
            "compute_skips": 0,
            "scheduling_influence": False,
            "value_mutated": False,
            "proof_promotion": False,
        }
