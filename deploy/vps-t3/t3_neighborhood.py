from __future__ import annotations

import os
from collections import deque
from dataclasses import dataclass
from typing import Any

SCHEMA = "BRUTUS_T3_SEMANTIC_NEIGHBORHOOD_V1"
RECENT_LIMIT = 37
DEFAULT_PER_FAMILY = 128


def _env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)).strip())
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))


def _state_value(packet: Any) -> str:
    state = getattr(packet, "state", None)
    return str(getattr(state, "value", state or "UNKNOWN"))


@dataclass(frozen=True)
class SemanticRep:
    fingerprint: str
    family: str
    value: int
    depth: int
    chain: tuple[str, ...]
    state: str

    @property
    def terminal_formula(self) -> str | None:
        return self.chain[-1] if self.chain else None

    @property
    def bit_length(self) -> int:
        return abs(int(self.value)).bit_length()


class T3SemanticNeighborhood:
    """Bounded, observation-only semantic neighborhood estimator.

    C2 remains exact identity. T3 deliberately does NOT compare SHA256 bit distance;
    it compares packet semantics inside the same T1 family. Exact C2 recurrence is
    delegated to T2 and reported as EXACT_REFERENCE.
    """

    CLASSES = ("EXACT_REFERENCE", "NEAR", "ADJACENT", "DISTANT", "ISOLATED")

    def __init__(self, per_family_limit: int | None = None) -> None:
        self.per_family_limit = per_family_limit if per_family_limit is not None else _env_int(
            "BROTO_T3_PER_FAMILY", DEFAULT_PER_FAMILY, 8, 2048
        )
        self._pools: dict[str, deque[SemanticRep]] = {}
        self.observations = 0
        self.unique_observations = 0
        self.exact_references = 0
        self.class_counts = {name: 0 for name in self.CLASSES}
        self.same_value_distinct_c2 = 0
        self.comparisons = 0
        self.best_score_sum = 0
        self.best_score_count = 0
        self.last_class: str | None = None
        self._recent: deque[dict[str, Any]] = deque(maxlen=RECENT_LIMIT)

    @staticmethod
    def _rep(packet: Any, fingerprint: str, family: str) -> SemanticRep:
        return SemanticRep(
            fingerprint=str(fingerprint),
            family=str(family or "OTHER"),
            value=int(getattr(packet, "value")),
            depth=int(getattr(packet, "depth", 0)),
            chain=tuple(str(x) for x in (getattr(packet, "formula_chain", ()) or ())),
            state=_state_value(packet),
        )

    @staticmethod
    def similarity(a: SemanticRep, b: SemanticRep) -> int:
        if a.family != b.family:
            return 0
        score = 10  # family agreement; candidates are family-bounded
        if a.terminal_formula == b.terminal_formula:
            score += 25
        if a.state == b.state:
            score += 10

        dd = abs(a.depth - b.depth)
        score += 15 if dd == 0 else 8 if dd == 1 else 0

        dl = abs(len(a.chain) - len(b.chain))
        score += 10 if dl == 0 else 5 if dl == 1 else 0

        db = abs(a.bit_length - b.bit_length)
        score += 15 if db == 0 else 8 if db == 1 else 0

        # Reward a common formula suffix without requiring identical full ancestry.
        common_suffix = 0
        for x, y in zip(reversed(a.chain), reversed(b.chain)):
            if x != y:
                break
            common_suffix += 1
        if common_suffix >= 3:
            score += 10
        elif common_suffix == 2:
            score += 7
        elif common_suffix == 1:
            score += 4

        # Numeric locality is measured by order of magnitude of the absolute gap,
        # never by distance between cryptographic fingerprints.
        gap = abs(a.value - b.value)
        if gap == 0:
            score += 15
        else:
            span_bits = max(a.bit_length, b.bit_length, 1)
            gap_bits = gap.bit_length()
            if gap_bits <= max(1, span_bits - 4):
                score += 10
            elif gap_bits <= max(1, span_bits - 2):
                score += 5
        return min(100, score)

    @staticmethod
    def classify_score(score: int) -> str:
        if score >= 80:
            return "NEAR"
        if score >= 60:
            return "ADJACENT"
        return "DISTANT"

    def observe(
        self,
        packet: Any,
        fingerprint: str,
        *,
        family: str,
        t2_event: str,
    ) -> str:
        if not isinstance(fingerprint, str) or not fingerprint.startswith("C2-"):
            raise ValueError("T3 requires a C2- fingerprint")
        self.observations += 1
        family = str(family or "OTHER")
        event = str(t2_event or "")

        if event.startswith("EXACT_DUPLICATE"):
            cls = "EXACT_REFERENCE"
            self.exact_references += 1
            self.class_counts[cls] += 1
            self.last_class = cls
            self._recent.append({"fingerprint": fingerprint, "family": family, "class": cls, "score": 100})
            return cls

        rep = self._rep(packet, fingerprint, family)
        pool = self._pools.setdefault(family, deque(maxlen=self.per_family_limit))
        self.unique_observations += 1

        best: SemanticRep | None = None
        best_score = -1
        for candidate in pool:
            self.comparisons += 1
            score = self.similarity(rep, candidate)
            if score > best_score:
                best_score = score
                best = candidate

        if best is None:
            cls = "ISOLATED"
            score_out: int | None = None
        else:
            cls = self.classify_score(best_score)
            score_out = best_score
            self.best_score_sum += best_score
            self.best_score_count += 1
            if rep.value == best.value and rep.fingerprint != best.fingerprint:
                self.same_value_distinct_c2 += 1

        pool.append(rep)
        self.class_counts[cls] += 1
        self.last_class = cls
        self._recent.append({
            "fingerprint": fingerprint,
            "family": family,
            "class": cls,
            "score": score_out,
            "neighbor_fingerprint": None if best is None else best.fingerprint,
            "same_value_distinct_c2": bool(best is not None and rep.value == best.value and rep.fingerprint != best.fingerprint),
        })
        return cls

    def status(self) -> dict[str, Any]:
        retained = sum(len(pool) for pool in self._pools.values())
        mean_best = None if self.best_score_count == 0 else self.best_score_sum / self.best_score_count
        return {
            "schema": SCHEMA,
            "mode": SCHEMA,
            "authority": "SHADOW_ONLY",
            "metric": "PACKET_SEMANTICS_NOT_HASH_DISTANCE",
            "observations": self.observations,
            "unique_observations": self.unique_observations,
            "exact_references": self.exact_references,
            "class_counts": dict(self.class_counts),
            "same_value_distinct_c2": self.same_value_distinct_c2,
            "comparisons": self.comparisons,
            "mean_best_score": mean_best,
            "families_with_pool": len(self._pools),
            "retained_representatives": retained,
            "per_family_limit": self.per_family_limit,
            "recent_limit": RECENT_LIMIT,
            "recent": list(self._recent),
            "hash_distance_used": False,
            "scientific_similarity_claim": False,
            "deduplication_applied": False,
            "packets_collapsed": 0,
            "controls_routing": False,
            "controls_scheduling": False,
            "compute_skips": 0,
            "value_mutated": False,
            "proof_promotion": False,
            "persistent": False,
        }
