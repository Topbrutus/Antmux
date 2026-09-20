from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any

from .daat_gate import CHANNELS
from .daat_link import DaatLinkFrame

HOPSCOTCH_SCHEMA = "ANTMUX-X72-HOPSCOTCH-v0.1"
HOPSCOTCH_STATUS = "CANDIDATE"
HOPSCOTCH_AUTHORITY = "OBSERVATION_ONLY"

ROUTES: dict[str, tuple[int, ...]] = {
    "FORWARD": tuple(range(CHANNELS)),
    "REVERSE": tuple(reversed(range(CHANNELS))),
    "EVEN_THEN_ODD": tuple(range(0, CHANNELS, 2)) + tuple(range(1, CHANNELS, 2)),
    "ODD_THEN_EVEN": tuple(range(1, CHANNELS, 2)) + tuple(range(0, CHANNELS, 2)),
}

THRESHOLDS = (0.50, 0.75, 0.90)


def _canonical_hash(payload: Any) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _is_permutation(route: tuple[int, ...]) -> bool:
    return len(route) == CHANNELS and set(route) == set(range(CHANNELS))
@dataclass(frozen=True)
class HopscotchRouteTrace:
    name: str
    route: tuple[int, ...]
    cumulative_link: tuple[float, ...]
    final_link: float
    prefix_mean: float
    threshold_steps: tuple[tuple[str, int | None], ...]
    trace_h256: str

    @classmethod
    def from_link(
        cls,
        *,
        name: str,
        route: tuple[int, ...],
        link: DaatLinkFrame,
    ) -> "HopscotchRouteTrace":
        if not _is_permutation(route):
            raise ValueError("route must be a complete permutation of 12 channels")

        remaining = 1.0
        cumulative: list[float] = []
        for channel in route:
            contribution = float(link.contributions[channel])
            if not 0.0 <= contribution <= 1.0:
                raise ValueError("route contribution must stay in [0,1]")
            remaining *= 1.0 - contribution
            cumulative.append(1.0 - remaining)

        final_link = cumulative[-1] if cumulative else 0.0
        prefix_mean = math.fsum(cumulative) / len(cumulative)
        threshold_steps: list[tuple[str, int | None]] = []
        for threshold in THRESHOLDS:
            reached = next(
                (
                    step
                    for step, value in enumerate(cumulative, start=1)
                    if value >= threshold
                ),
                None,
            )
            threshold_steps.append((f"{threshold:.2f}", reached))

        payload = {
            "schema": HOPSCOTCH_SCHEMA,
            "name": name,
            "route": route,
            "cumulative_link": cumulative,
            "final_link": final_link,
            "prefix_mean": prefix_mean,
            "threshold_steps": threshold_steps,
        }

        return cls(
            name=name,
            route=route,
            cumulative_link=tuple(cumulative),
            final_link=final_link,
            prefix_mean=prefix_mean,
            threshold_steps=tuple(threshold_steps),
            trace_h256=_canonical_hash(payload),
        )
    def verify(self, *, tolerance: float = 1e-12) -> bool:
        if not _is_permutation(self.route):
            return False
        if len(self.cumulative_link) != CHANNELS:
            return False
        if any(
            not math.isfinite(value) or not 0.0 <= value <= 1.0
            for value in self.cumulative_link
        ):
            return False
        if any(
            self.cumulative_link[index] + tolerance
            < self.cumulative_link[index - 1]
            for index in range(1, CHANNELS)
        ):
            return False
        if abs(self.final_link - self.cumulative_link[-1]) > tolerance:
            return False
        if not 0.0 <= self.prefix_mean <= 1.0:
            return False

        payload = {
            "schema": HOPSCOTCH_SCHEMA,
            "name": self.name,
            "route": self.route,
            "cumulative_link": list(self.cumulative_link),
            "final_link": self.final_link,
            "prefix_mean": self.prefix_mean,
            "threshold_steps": list(self.threshold_steps),
        }
        return self.trace_h256 == _canonical_hash(payload)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "route": list(self.route),
            "cumulative_link": list(self.cumulative_link),
            "final_link": self.final_link,
            "prefix_mean": self.prefix_mean,
            "threshold_steps": dict(self.threshold_steps),
            "verified": self.verify(),
            "trace_h256": self.trace_h256,
        }
@dataclass(frozen=True)
class HopscotchEnsembleFrame:
    tick: int
    generation: int
    source_h256: str
    target_link_score: float
    routes: tuple[HopscotchRouteTrace, ...]
    ensemble_h256: str

    @classmethod
    def from_link(cls, link: DaatLinkFrame) -> "HopscotchEnsembleFrame":
        if type(link) is not DaatLinkFrame:
            raise TypeError("link must be exactly DaatLinkFrame")
        if not link.verify():
            raise ValueError("Da'at link frame must verify")

        traces = tuple(
            HopscotchRouteTrace.from_link(
                name=name,
                route=route,
                link=link,
            )
            for name, route in ROUTES.items()
        )
        payload = {
            "schema": HOPSCOTCH_SCHEMA,
            "tick": link.tick,
            "generation": link.generation,
            "source_h256": link.source_h256,
            "target_link_score": link.link_score,
            "routes": [trace.to_dict() for trace in traces],
        }
        return cls(
            tick=link.tick,
            generation=link.generation,
            source_h256=link.source_h256,
            target_link_score=link.link_score,
            routes=traces,
            ensemble_h256=_canonical_hash(payload),
        )
    def verify(self, *, tolerance: float = 1e-12) -> bool:
        if len(self.routes) != len(ROUTES):
            return False
        if any(not route.verify(tolerance=tolerance) for route in self.routes):
            return False
        if any(
            abs(route.final_link - self.target_link_score) > tolerance
            for route in self.routes
        ):
            return False
        if len({route.name for route in self.routes}) != len(self.routes):
            return False

        payload = {
            "schema": HOPSCOTCH_SCHEMA,
            "tick": self.tick,
            "generation": self.generation,
            "source_h256": self.source_h256,
            "target_link_score": self.target_link_score,
            "routes": [route.to_dict() for route in self.routes],
        }
        return self.ensemble_h256 == _canonical_hash(payload)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": HOPSCOTCH_SCHEMA,
            "status": HOPSCOTCH_STATUS,
            "authority": HOPSCOTCH_AUTHORITY,
            "mutates_queen": False,
            "physical_claim": False,
            "tick": self.tick,
            "generation": self.generation,
            "source_h256": self.source_h256,
            "route_semantics": "CHANNEL_ORDER_ONLY_NO_SPATIAL_MEANING",
            "target_link_score": self.target_link_score,
            "route_invariant_final_link": all(
                math.isclose(
                    route.final_link,
                    self.target_link_score,
                    rel_tol=0.0,
                    abs_tol=1e-12,
                )
                for route in self.routes
            ),
            "routes": [route.to_dict() for route in self.routes],
            "unmapped": [
                "VERTICAL_AXIS",
                "DEPTH_AXIS",
                "TREE_NODE_GEOMETRY",
                "SEFIROT_SEMANTICS",
            ],
            "verified": self.verify(),
            "ensemble_h256": self.ensemble_h256,
        }
