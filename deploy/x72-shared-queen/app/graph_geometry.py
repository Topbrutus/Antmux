from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any

from .daat_gate import CHANNELS
from .hopscotch_paths import HopscotchEnsembleFrame

GRAPH_GEOMETRY_SCHEMA = "ANTMUX-X72-GRAPH-GEOMETRY-v0.1"
GRAPH_GEOMETRY_STATUS = "CANDIDATE"
GRAPH_GEOMETRY_AUTHORITY = "OBSERVATION_ONLY"


def _canonical_hash(payload: Any) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def ring_distance(left: int, right: int, *, size: int = CHANNELS) -> int:
    if not 0 <= left < size or not 0 <= right < size:
        raise ValueError("ring node out of range")
    delta = abs(left - right)
    return min(delta, size - delta)


def ring_edges(*, size: int = CHANNELS) -> tuple[tuple[int, int], ...]:
    return tuple((index, (index + 1) % size) for index in range(size))


def rotate_label(node: int, shift: int, *, size: int = CHANNELS) -> int:
    if not 0 <= node < size:
        raise ValueError("ring node out of range")
    return (node + shift) % size


def reflect_label(node: int, shift: int = 0, *, size: int = CHANNELS) -> int:
    if not 0 <= node < size:
        raise ValueError("ring node out of range")
    return (shift - node) % size
@dataclass(frozen=True)
class RouteGeometry:
    name: str
    route: tuple[int, ...]
    hop_distances: tuple[int, ...]
    walk_length: int
    endpoint_distance: int
    mean_hop_distance: float
    max_hop_distance: int
    endpoint_efficiency: float

    @classmethod
    def from_route(
        cls,
        *,
        name: str,
        route: tuple[int, ...],
    ) -> "RouteGeometry":
        if len(route) != CHANNELS or set(route) != set(range(CHANNELS)):
            raise ValueError("route must be a complete 12-channel permutation")

        hops = tuple(
            ring_distance(route[index], route[index + 1])
            for index in range(len(route) - 1)
        )
        walk_length = sum(hops)
        endpoint_distance = ring_distance(route[0], route[-1])
        mean_hop_distance = (
            math.fsum(hops) / len(hops)
            if hops
            else 0.0
        )
        max_hop_distance = max(hops, default=0)
        endpoint_efficiency = (
            endpoint_distance / walk_length
            if walk_length > 0
            else 1.0
        )

        return cls(
            name=name,
            route=route,
            hop_distances=hops,
            walk_length=walk_length,
            endpoint_distance=endpoint_distance,
            mean_hop_distance=mean_hop_distance,
            max_hop_distance=max_hop_distance,
            endpoint_efficiency=endpoint_efficiency,
        )

    def rotated(self, shift: int) -> "RouteGeometry":
        return RouteGeometry.from_route(
            name=self.name,
            route=tuple(rotate_label(node, shift) for node in self.route),
        )

    def reflected(self, shift: int = 0) -> "RouteGeometry":
        return RouteGeometry.from_route(
            name=self.name,
            route=tuple(reflect_label(node, shift) for node in self.route),
        )

    def verify(self) -> bool:
        if len(self.hop_distances) != CHANNELS - 1:
            return False
        if self.walk_length != sum(self.hop_distances):
            return False
        if self.endpoint_distance != ring_distance(
            self.route[0],
            self.route[-1],
        ):
            return False
        if any(distance < 1 or distance > CHANNELS // 2 for distance in self.hop_distances):
            return False
        if not 0.0 <= self.endpoint_efficiency <= 1.0:
            return False
        rotated = self.rotated(3)
        reflected = self.reflected(5)
        return (
            rotated.hop_distances == self.hop_distances
            and rotated.walk_length == self.walk_length
            and rotated.endpoint_distance == self.endpoint_distance
            and reflected.hop_distances == self.hop_distances
            and reflected.walk_length == self.walk_length
            and reflected.endpoint_distance == self.endpoint_distance
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "route": list(self.route),
            "hop_distances": list(self.hop_distances),
            "walk_length": self.walk_length,
            "endpoint_distance": self.endpoint_distance,
            "mean_hop_distance": self.mean_hop_distance,
            "max_hop_distance": self.max_hop_distance,
            "endpoint_efficiency": self.endpoint_efficiency,
            "verified": self.verify(),
        }
@dataclass(frozen=True)
class GraphGeometryFrame:
    tick: int
    generation: int
    source_h256: str
    routes: tuple[RouteGeometry, ...]
    mean_pair_distance: float
    diameter: int
    edge_count: int
    degree_sequence: tuple[int, ...]
    forman_edge_curvature: tuple[int, ...]
    geometry_h256: str

    @classmethod
    def from_hopscotch(
        cls,
        hopscotch: HopscotchEnsembleFrame,
    ) -> "GraphGeometryFrame":
        if type(hopscotch) is not HopscotchEnsembleFrame:
            raise TypeError("hopscotch must be exactly HopscotchEnsembleFrame")
        if not hopscotch.verify():
            raise ValueError("hopscotch frame must verify")

        routes = tuple(
            RouteGeometry.from_route(
                name=trace.name,
                route=trace.route,
            )
            for trace in hopscotch.routes
        )

        pair_distances = [
            ring_distance(left, right)
            for left in range(CHANNELS)
            for right in range(left + 1, CHANNELS)
        ]
        mean_pair_distance = math.fsum(pair_distances) / len(pair_distances)
        diameter = max(pair_distances)
        edges = ring_edges()
        degree_sequence = tuple(2 for _ in range(CHANNELS))
        # Unweighted Forman-Ricci edge curvature: 4 - deg(u) - deg(v).
        forman_edge_curvature = tuple(
            4 - degree_sequence[left] - degree_sequence[right]
            for left, right in edges
        )

        payload = {
            "schema": GRAPH_GEOMETRY_SCHEMA,
            "tick": hopscotch.tick,
            "generation": hopscotch.generation,
            "source_h256": hopscotch.source_h256,
            "routes": [route.to_dict() for route in routes],
            "mean_pair_distance": mean_pair_distance,
            "diameter": diameter,
            "edge_count": len(edges),
            "degree_sequence": degree_sequence,
            "forman_edge_curvature": forman_edge_curvature,
        }

        return cls(
            tick=hopscotch.tick,
            generation=hopscotch.generation,
            source_h256=hopscotch.source_h256,
            routes=routes,
            mean_pair_distance=mean_pair_distance,
            diameter=diameter,
            edge_count=len(edges),
            degree_sequence=degree_sequence,
            forman_edge_curvature=forman_edge_curvature,
            geometry_h256=_canonical_hash(payload),
        )
    def verify(self, *, tolerance: float = 1e-12) -> bool:
        if self.edge_count != CHANNELS:
            return False
        if self.degree_sequence != tuple(2 for _ in range(CHANNELS)):
            return False
        if self.diameter != CHANNELS // 2:
            return False
        if self.forman_edge_curvature != tuple(0 for _ in range(CHANNELS)):
            return False
        if any(not route.verify() for route in self.routes):
            return False

        pair_distances = [
            ring_distance(left, right)
            for left in range(CHANNELS)
            for right in range(left + 1, CHANNELS)
        ]
        expected_mean = math.fsum(pair_distances) / len(pair_distances)
        if abs(self.mean_pair_distance - expected_mean) > tolerance:
            return False

        # Exhaustive metric triangle inequality on the candidate ring graph.
        for a in range(CHANNELS):
            for b in range(CHANNELS):
                for c in range(CHANNELS):
                    if ring_distance(a, c) > ring_distance(a, b) + ring_distance(b, c):
                        return False

        payload = {
            "schema": GRAPH_GEOMETRY_SCHEMA,
            "tick": self.tick,
            "generation": self.generation,
            "source_h256": self.source_h256,
            "routes": [route.to_dict() for route in self.routes],
            "mean_pair_distance": self.mean_pair_distance,
            "diameter": self.diameter,
            "edge_count": self.edge_count,
            "degree_sequence": self.degree_sequence,
            "forman_edge_curvature": self.forman_edge_curvature,
        }
        return self.geometry_h256 == _canonical_hash(payload)

    def to_dict(self) -> dict[str, Any]:
        route_lengths = {
            route.name: route.walk_length
            for route in self.routes
        }
        return {
            "schema": GRAPH_GEOMETRY_SCHEMA,
            "status": GRAPH_GEOMETRY_STATUS,
            "authority": GRAPH_GEOMETRY_AUTHORITY,
            "mutates_queen": False,
            "physical_claim": False,
            "riemannian_claim": False,
            "tick": self.tick,
            "generation": self.generation,
            "source_h256": self.source_h256,
            "topology": "CYCLE_C12_OPERATIONAL_ONLY",
            "metric": "UNWEIGHTED_SHORTEST_PATH_DISTANCE",
            "edge_count": self.edge_count,
            "degree_sequence": list(self.degree_sequence),
            "diameter": self.diameter,
            "mean_pair_distance": self.mean_pair_distance,
            "forman_edge_curvature": list(self.forman_edge_curvature),
            "curvature_note": "UNWEIGHTED_FORMAN_DIAGNOSTIC_ONLY",
            "route_lengths": route_lengths,
            "routes": [route.to_dict() for route in self.routes],
            "route_lengths_distinguish_some_paths": len(set(route_lengths.values())) > 1,
            "relabeling_invariance": "VERIFIED_FOR_CYCLE_ROTATIONS_AND_REFLECTIONS",
            "unmapped": [
                "CONTINUOUS_MANIFOLD",
                "RIEMANN_METRIC_TENSOR",
                "PHYSICAL_CURVATURE",
                "TREE_NODE_GEOMETRY",
                "VERTICAL_AXIS",
                "DEPTH_AXIS",
            ],
            "verified": self.verify(),
            "geometry_h256": self.geometry_h256,
        }
