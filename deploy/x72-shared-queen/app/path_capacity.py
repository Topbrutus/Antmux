from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any

from .daat_gate import CHANNELS
from .daat_link import DaatLinkFrame
from .graph_geometry import ring_distance

PATH_CAPACITY_SCHEMA = "ANTMUX-X72-PATH-CAPACITY-v0.1"
PATH_CAPACITY_STATUS = "CANDIDATE"
PATH_CAPACITY_AUTHORITY = "OBSERVATION_ONLY"
DEFAULT_BEAM_WIDTH = 64


def _canonical_hash(payload: Any) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _rank(source_h256: str, prefix: tuple[int, ...]) -> tuple[str, tuple[int, ...]]:
    raw = f"{source_h256}|{','.join(str(item) for item in prefix)}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest(), prefix


def _route_length(route: tuple[int, ...]) -> int:
    return sum(
        ring_distance(route[index], route[index + 1])
        for index in range(len(route) - 1)
    )
@dataclass(frozen=True)
class CapacityStage:
    depth: int
    theoretical_prefixes: int
    generated_candidates: int
    retained_prefixes: int

    def to_dict(self) -> dict[str, int]:
        return {
            "depth": self.depth,
            "theoretical_prefixes": self.theoretical_prefixes,
            "generated_candidates": self.generated_candidates,
            "retained_prefixes": self.retained_prefixes,
        }


def _beam_search(
    *,
    source_h256: str,
    beam_width: int,
) -> tuple[tuple[CapacityStage, ...], tuple[tuple[int, ...], ...]]:
    if type(beam_width) is not int or not 1 <= beam_width <= 4096:
        raise ValueError("beam_width must be an integer inside [1,4096]")

    beam: list[tuple[int, ...]] = [()]
    stages: list[CapacityStage] = []

    for depth in range(1, CHANNELS + 1):
        candidates: list[tuple[int, ...]] = []
        for prefix in beam:
            used = set(prefix)
            for channel in range(CHANNELS):
                if channel not in used:
                    candidates.append(prefix + (channel,))

        # Candidate prefixes are unique because each child has a unique parent.
        candidates.sort(key=lambda prefix: _rank(source_h256, prefix))
        beam = candidates[:beam_width]
        stages.append(
            CapacityStage(
                depth=depth,
                theoretical_prefixes=math.perm(CHANNELS, depth),
                generated_candidates=len(candidates),
                retained_prefixes=len(beam),
            )
        )

    return tuple(stages), tuple(beam)
@dataclass(frozen=True)
class PathCapacityFrame:
    tick: int
    generation: int
    source_h256: str
    target_link_score: float
    beam_width: int
    stages: tuple[CapacityStage, ...]
    sampled_routes: tuple[tuple[int, ...], ...]
    sampled_route_lengths: tuple[int, ...]
    complete_path_space: int
    max_generated_candidates: int
    max_retained_prefixes: int
    max_stored_channel_slots: int
    capacity_h256: str

    @classmethod
    def from_link(
        cls,
        link: DaatLinkFrame,
        *,
        beam_width: int = DEFAULT_BEAM_WIDTH,
    ) -> "PathCapacityFrame":
        if type(link) is not DaatLinkFrame:
            raise TypeError("link must be exactly DaatLinkFrame")
        if not link.verify():
            raise ValueError("Da'at link frame must verify")

        stages, sampled_routes = _beam_search(
            source_h256=link.source_h256,
            beam_width=beam_width,
        )
        lengths = tuple(_route_length(route) for route in sampled_routes)
        complete_path_space = math.factorial(CHANNELS)
        max_generated = max(
            (stage.generated_candidates for stage in stages),
            default=0,
        )
        max_retained = max(
            (stage.retained_prefixes for stage in stages),
            default=0,
        )
        max_slots = beam_width * CHANNELS

        payload = {
            "schema": PATH_CAPACITY_SCHEMA,
            "tick": link.tick,
            "generation": link.generation,
            "source_h256": link.source_h256,
            "target_link_score": link.link_score,
            "beam_width": beam_width,
            "stages": [stage.to_dict() for stage in stages],
            "sampled_routes": sampled_routes,
            "sampled_route_lengths": lengths,
            "complete_path_space": complete_path_space,
        }

        return cls(
            tick=link.tick,
            generation=link.generation,
            source_h256=link.source_h256,
            target_link_score=link.link_score,
            beam_width=beam_width,
            stages=stages,
            sampled_routes=sampled_routes,
            sampled_route_lengths=lengths,
            complete_path_space=complete_path_space,
            max_generated_candidates=max_generated,
            max_retained_prefixes=max_retained,
            max_stored_channel_slots=max_slots,
            capacity_h256=_canonical_hash(payload),
        )
    def verify(self) -> bool:
        if self.complete_path_space != math.factorial(CHANNELS):
            return False
        if len(self.stages) != CHANNELS:
            return False
        if self.max_retained_prefixes > self.beam_width:
            return False
        if self.max_stored_channel_slots != self.beam_width * CHANNELS:
            return False
        if len(self.sampled_routes) > self.beam_width:
            return False
        if len(set(self.sampled_routes)) != len(self.sampled_routes):
            return False
        if any(
            len(route) != CHANNELS or set(route) != set(range(CHANNELS))
            for route in self.sampled_routes
        ):
            return False

        expected_stages, expected_routes = _beam_search(
            source_h256=self.source_h256,
            beam_width=self.beam_width,
        )
        if self.stages != expected_stages or self.sampled_routes != expected_routes:
            return False

        expected_lengths = tuple(
            _route_length(route)
            for route in expected_routes
        )
        if self.sampled_route_lengths != expected_lengths:
            return False

        if any(
            stage.theoretical_prefixes != math.perm(CHANNELS, stage.depth)
            for stage in self.stages
        ):
            return False
        if any(stage.retained_prefixes > self.beam_width for stage in self.stages):
            return False
        if self.max_generated_candidates != max(
            stage.generated_candidates for stage in self.stages
        ):
            return False

        payload = {
            "schema": PATH_CAPACITY_SCHEMA,
            "tick": self.tick,
            "generation": self.generation,
            "source_h256": self.source_h256,
            "target_link_score": self.target_link_score,
            "beam_width": self.beam_width,
            "stages": [stage.to_dict() for stage in self.stages],
            "sampled_routes": self.sampled_routes,
            "sampled_route_lengths": self.sampled_route_lengths,
            "complete_path_space": self.complete_path_space,
        }
        return self.capacity_h256 == _canonical_hash(payload)
    def to_dict(self) -> dict[str, Any]:
        retained_complete = len(self.sampled_routes)
        compression_ratio = (
            self.complete_path_space / retained_complete
            if retained_complete
            else math.inf
        )
        return {
            "schema": PATH_CAPACITY_SCHEMA,
            "status": PATH_CAPACITY_STATUS,
            "authority": PATH_CAPACITY_AUTHORITY,
            "mutates_queen": False,
            "physical_claim": False,
            "gabriels_horn_claim": False,
            "tick": self.tick,
            "generation": self.generation,
            "source_h256": self.source_h256,
            "target_link_score": self.target_link_score,
            "policy": "DETERMINISTIC_HASH_RANKED_BOUNDED_BEAM",
            "beam_width": self.beam_width,
            "channel_count": CHANNELS,
            "complete_path_space": self.complete_path_space,
            "materializes_all_paths": False,
            "full_coverage_claim": False,
            "stages": [stage.to_dict() for stage in self.stages],
            "sampled_route_count": retained_complete,
            "sampled_routes": [list(route) for route in self.sampled_routes],
            "sampled_route_lengths": list(self.sampled_route_lengths),
            "sampled_route_length_min": min(self.sampled_route_lengths, default=0),
            "sampled_route_length_max": max(self.sampled_route_lengths, default=0),
            "sampled_route_length_mean": (
                math.fsum(self.sampled_route_lengths) / retained_complete
                if retained_complete
                else 0.0
            ),
            "bounds": {
                "max_retained_prefixes": self.max_retained_prefixes,
                "max_generated_candidates_per_stage": self.max_generated_candidates,
                "max_stored_channel_slots": self.max_stored_channel_slots,
                "retained_complete_routes": retained_complete,
                "path_space_per_retained_route": compression_ratio,
            },
            "interpretation": (
                "COUNT_AND_SAMPLE_HUGE_ROUTE_SPACE_WITHOUT_MATERIALIZING_ALL_ROUTES"
            ),
            "unmapped": [
                "INFINITE_PATH_SPACE",
                "GABRIELS_HORN_GEOMETRY",
                "LOSSLESS_STORAGE_OF_ALL_ROUTES",
                "VERTICAL_AXIS",
                "DEPTH_AXIS",
            ],
            "verified": self.verify(),
            "capacity_h256": self.capacity_h256,
        }
