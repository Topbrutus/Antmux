from __future__ import annotations

from collections import deque
from typing import Any

SCHEMA = "BRUTUS_C7_SHADOW_ROUTER_V1"
RECENT_LIMIT = 37


class C7ShadowRouter:
    """Observation-only route recommender driven by C3-C6 signals.

    C7 never mutates packet flow, priority, scheduling, proof status, or values.
    Its output is an auditable recommendation for a later authority gate.
    """

    ROUTES = (
        "PROVENANCE_REVIEW",
        "NOVELTY_REVIEW",
        "RARE_REPLAY",
        "CONVERGENCE_REVIEW",
        "KNOWN_CONTROL",
        "CAPACITY_REVIEW",
        "OBSERVE_ONLY",
    )

    def __init__(self) -> None:
        self.observations = 0
        self.route_counts = {route: 0 for route in self.ROUTES}
        self.last_route: str | None = None
        self._recent: deque[dict[str, Any]] = deque(maxlen=RECENT_LIMIT)

    @staticmethod
    def recommend(*, c3_hit: bool, c3_retained: bool, c5_class: str | None, c6: dict[str, Any] | None) -> tuple[str, list[str]]:
        reasons: list[str] = []
        if not c3_retained:
            return "CAPACITY_REVIEW", ["c3_not_retained"]

        c6 = c6 or {}
        if bool(c6.get("operational_independence_candidate")):
            reasons.append("c6_operational_independence_candidate")
            return "PROVENANCE_REVIEW", reasons

        if not c3_hit:
            reasons.extend(["c3_miss", "c4_novel_candidate"])
            if c5_class:
                reasons.append(f"c5:{c5_class}")
            return "NOVELTY_REVIEW", reasons

        if c5_class in {"RARE_8", "RARE_6", "SCARCE_4"}:
            return "RARE_REPLAY", ["c3_hit", f"c5:{c5_class}"]

        diversity = max(
            int(c6.get("distinct_paths") or 0),
            int(c6.get("distinct_formula_chains") or 0),
            int(c6.get("distinct_parents") or 0),
        )
        if c5_class == "CONVERGENT_2" or diversity >= 2:
            reasons.append(f"c5:{c5_class}" if c5_class else "c6_diversity")
            if diversity >= 2:
                reasons.append("c6_route_diversity>=2")
            return "CONVERGENCE_REVIEW", reasons

        if c5_class == "COMMON_1_CONTROL":
            return "KNOWN_CONTROL", ["c3_hit", "c5:COMMON_1_CONTROL"]

        return "OBSERVE_ONLY", ["no_higher_priority_shadow_route"]

    def observe(
        self,
        fingerprint: str,
        *,
        c3_hit: bool,
        c3_retained: bool,
        c5_class: str | None,
        c6_summary: dict[str, Any] | None,
    ) -> str:
        if not isinstance(fingerprint, str) or not fingerprint.startswith("C2-"):
            raise ValueError("C7 requires a C2- fingerprint")
        route, reasons = self.recommend(
            c3_hit=bool(c3_hit),
            c3_retained=bool(c3_retained),
            c5_class=c5_class,
            c6=c6_summary,
        )
        self.observations += 1
        self.route_counts[route] += 1
        self.last_route = route
        self._recent.append({
            "fingerprint": fingerprint,
            "route": route,
            "reasons": reasons,
            "c3_hit": bool(c3_hit),
            "c5_class": c5_class,
            "z_id": None if not c6_summary else c6_summary.get("z_id"),
        })
        return route

    def status(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "mode": SCHEMA,
            "authority": "SHADOW_ONLY",
            "observations": self.observations,
            "route_counts": dict(self.route_counts),
            "last_route": self.last_route,
            "recent_limit": RECENT_LIMIT,
            "recent": list(self._recent),
            "inputs": ["C3_HIT_MISS", "C5_STRUCTURAL_RARITY", "C6_PROVENANCE_SUMMARY"],
            "controls_scheduling": False,
            "actual_routes_applied": 0,
            "compute_skips": 0,
            "value_mutated": False,
            "proof_promotion": False,
            "scientific_claim": False,
            "persistent": False,
        }
