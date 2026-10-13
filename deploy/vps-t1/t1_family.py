from __future__ import annotations

from collections import deque
from typing import Any

SCHEMA = "BRUTUS_T1_FAMILY_V1"
RECENT_LIMIT = 37

FORMULA_FAMILY = {
    "PLUS1": "ARITHMETIC_EXPANSION",
    "DOUBLE": "ARITHMETIC_EXPANSION",
    "SQUARE": "ARITHMETIC_EXPANSION",
    "HALF_EVEN": "REDUCTION",
    "DIGIT_SUM": "REDUCTION",
    "BIT_LENGTH": "REDUCTION",
    "PELL_N": "PELL",
    "PELL_Q": "PELL",
    "FACTOR_GAP_LOW_666": "FACTOR_GAP",
    "FACTOR_GAP_HIGH_666": "FACTOR_GAP",
    "CRYSTAL_SEPARATOR_RELEASE": "CRYSTAL_REINJECTION",
}

FAMILIES = (
    "ROOT",
    "ARITHMETIC_EXPANSION",
    "REDUCTION",
    "PELL",
    "FACTOR_GAP",
    "CRYSTAL_REINJECTION",
    "OTHER",
)


def operation_family(formula_id: str) -> str:
    fid = str(formula_id)
    if fid.startswith("CRYSTAL_REINJECT:"):
        return "CRYSTAL_REINJECTION"
    return FORMULA_FAMILY.get(fid, "OTHER")


class T1FamilyClassifier:
    """Shadow family classifier for the Brutus T1 stage.

    T1 classifies the current/terminal operation and preserves the set of
    operational families seen in the lineage. It never changes routing,
    scheduling, values, proof status, or compute behavior.
    """

    def __init__(self) -> None:
        self.observations = 0
        self.family_counts = {family: 0 for family in FAMILIES}
        self.mixed_lineage_observations = 0
        self.unknown_formula_events = 0
        self.route_family_counts: dict[str, dict[str, int]] = {}
        self.last_family: str | None = None
        self._recent: deque[dict[str, Any]] = deque(maxlen=RECENT_LIMIT)

    @staticmethod
    def classify(packet: Any) -> dict[str, Any]:
        chain = tuple(str(x) for x in getattr(packet, "formula_chain", ()) or ())
        if not chain:
            return {
                "family": "ROOT",
                "terminal_formula": None,
                "lineage_families": ["ROOT"],
                "mixed_lineage": False,
                "unknown_formula_count": 0,
            }

        families = [operation_family(fid) for fid in chain]
        unique: list[str] = []
        for family in families:
            if family not in unique:
                unique.append(family)
        unknowns = sum(1 for family in families if family == "OTHER")
        return {
            "family": families[-1],
            "terminal_formula": chain[-1],
            "lineage_families": unique,
            "mixed_lineage": len(unique) > 1,
            "unknown_formula_count": unknowns,
        }

    def observe(self, packet: Any, fingerprint: str, *, c7_route: str) -> str:
        if not isinstance(fingerprint, str) or not fingerprint.startswith("C2-"):
            raise ValueError("T1 requires a C2- fingerprint")
        info = self.classify(packet)
        family = str(info["family"])
        if family not in self.family_counts:
            family = "OTHER"

        self.observations += 1
        self.family_counts[family] += 1
        self.last_family = family
        if bool(info["mixed_lineage"]):
            self.mixed_lineage_observations += 1
        self.unknown_formula_events += int(info["unknown_formula_count"])

        route = str(c7_route or "OBSERVE_ONLY")
        by_family = self.route_family_counts.setdefault(route, {f: 0 for f in FAMILIES})
        by_family[family] += 1

        self._recent.append({
            "fingerprint": fingerprint,
            "family": family,
            "terminal_formula": info["terminal_formula"],
            "lineage_families": info["lineage_families"],
            "mixed_lineage": bool(info["mixed_lineage"]),
            "c7_route": route,
            "z_id": getattr(packet, "z_id", None),
        })
        return family

    def status(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "mode": SCHEMA,
            "authority": "SHADOW_ONLY",
            "observations": self.observations,
            "families": list(FAMILIES),
            "family_counts": dict(self.family_counts),
            "mixed_lineage_observations": self.mixed_lineage_observations,
            "unknown_formula_events": self.unknown_formula_events,
            "route_family_counts": {k: dict(v) for k, v in self.route_family_counts.items()},
            "last_family": self.last_family,
            "recent_limit": RECENT_LIMIT,
            "recent": list(self._recent),
            "classification_rule": "terminal known operation family + complete lineage family set",
            "scientific_taxonomy_claim": False,
            "controls_routing": False,
            "controls_scheduling": False,
            "actual_routes_applied": 0,
            "compute_skips": 0,
            "value_mutated": False,
            "proof_promotion": False,
            "persistent": False,
        }
