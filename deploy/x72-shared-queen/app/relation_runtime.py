from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any

RELATION_RUNTIME_SCHEMA = "ANTMUX-X72-RELATION-RUNTIME-v0.1"
RELATION_RUNTIME_STATUS = "CANDIDATE"
RELATION_RUNTIME_AUTHORITY = "OBSERVATION_ONLY"
RELATION_SAMPLE_INTERVAL_TICKS = 60
RELATION_SIGNAL_THRESHOLD = 0.25
RELATION_BALANCE_EPSILON = 1e-12


def _canonical_hash(payload: Any) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _finite(value: Any, field: str) -> float:
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"{field} must be finite")
    return out


def _edge_id(left: int, right: int) -> str:
    a, b = sorted((left, right))
    return f"S{a + 1}-S{b + 1}"


@dataclass
class RelationPulseStat:
    pulse_count: int = 0
    last_pulse_tick: int | None = None
    last_pulse_generation: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "pulse_count": self.pulse_count,
            "last_pulse_tick": self.last_pulse_tick,
            "last_pulse_generation": self.last_pulse_generation,
        }


class RelationRuntime:
    """Observation-only sampled telemetry for Queen relation edges.

    A sampled pulse is counted every RELATION_SAMPLE_INTERVAL_TICKS while both
    endpoints are healthy and their mean activity is above the historical
    frontend marker threshold. Direction is a software visualization
    convention based on the current activity gradient; it is not a physical
    transport claim and does not mutate Queen synapses.
    """

    def __init__(
        self,
        *,
        sample_interval_ticks: int = RELATION_SAMPLE_INTERVAL_TICKS,
        signal_threshold: float = RELATION_SIGNAL_THRESHOLD,
    ) -> None:
        if type(sample_interval_ticks) is not int or sample_interval_ticks <= 0:
            raise ValueError("sample_interval_ticks must be a positive integer")
        threshold = _finite(signal_threshold, "signal_threshold")
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("signal_threshold must be between 0 and 1")
        self.sample_interval_ticks = sample_interval_ticks
        self.signal_threshold = threshold
        self.last_sample_tick = -1
        self.stats: dict[str, RelationPulseStat] = {}

    def _stat_for(self, relation_id: str) -> RelationPulseStat:
        stat = self.stats.get(relation_id)
        if stat is None:
            stat = RelationPulseStat()
            self.stats[relation_id] = stat
        return stat

    def _metric(
        self,
        *,
        left: int,
        right: int,
        synapses: list[Any],
        tick: int,
        generation: int,
    ) -> dict[str, Any]:
        if not (0 <= left < len(synapses) and 0 <= right < len(synapses)):
            raise ValueError("relation endpoint index out of range")
        if left == right:
            raise ValueError("relation endpoints must differ")

        a_index, b_index = sorted((left, right))
        a = synapses[a_index]
        b = synapses[b_index]
        relation_id = _edge_id(a_index, b_index)

        a_activity = _finite(a.activity, f"{relation_id}.a_activity")
        b_activity = _finite(b.activity, f"{relation_id}.b_activity")
        a_memory = _finite(a.memory, f"{relation_id}.a_memory")
        b_memory = _finite(b.memory, f"{relation_id}.b_memory")
        a_crystal = _finite(a.crystal, f"{relation_id}.a_crystal")
        b_crystal = _finite(b.crystal, f"{relation_id}.b_crystal")

        mean_activity = (a_activity + b_activity) / 2.0
        activity_delta = b_activity - a_activity
        activity_gap = abs(activity_delta)
        memory_gap = abs(b_memory - a_memory)
        crystal_gap = abs(b_crystal - a_crystal)

        endpoints_healthy = bool(
            a.enabled
            and b.enabled
            and int(a.integrity) > 0
            and int(b.integrity) > 0
        )
        pulse_active = endpoints_healthy and mean_activity > self.signal_threshold

        a_id = str(a.synapse_id)
        b_id = str(b.synapse_id)
        if abs(activity_delta) <= RELATION_BALANCE_EPSILON:
            gradient_direction = "BALANCED"
        elif activity_delta > 0.0:
            gradient_direction = f"{b_id}_TO_{a_id}"
        else:
            gradient_direction = f"{a_id}_TO_{b_id}"

        stat = self._stat_for(relation_id)
        payload = {
            "relation_id": relation_id,
            "left_index": a_index,
            "right_index": b_index,
            "left_synapse": a_id,
            "right_synapse": b_id,
            "tick": tick,
            "generation": generation,
            "pulse_active": pulse_active,
            "signal_level": mean_activity if endpoints_healthy else 0.0,
            "activity_delta": activity_delta,
            "activity_gap": activity_gap,
            "memory_gap": memory_gap,
            "crystal_gap": crystal_gap,
            "activity_gradient_direction": gradient_direction,
            "pulse_count": stat.pulse_count,
            "last_pulse_tick": stat.last_pulse_tick,
            "last_pulse_generation": stat.last_pulse_generation,
        }
        payload["relation_h256"] = _canonical_hash(payload)
        return payload

    def observe(
        self,
        *,
        tick: int,
        generation: int,
        synapses: list[Any],
        relations: list[list[int]],
    ) -> bool:
        if tick == self.last_sample_tick or tick % self.sample_interval_ticks != 0:
            return False

        metrics = [
            self._metric(
                left=int(left),
                right=int(right),
                synapses=synapses,
                tick=tick,
                generation=generation,
            )
            for left, right in relations
        ]
        for metric in metrics:
            if metric["pulse_active"]:
                stat = self._stat_for(metric["relation_id"])
                stat.pulse_count += 1
                stat.last_pulse_tick = tick
                stat.last_pulse_generation = generation
        self.last_sample_tick = tick
        return True

    def visual_state(
        self,
        *,
        tick: int,
        generation: int,
        synapses: list[Any],
        relations: list[list[int]],
    ) -> dict[str, Any]:
        metrics = [
            self._metric(
                left=int(left),
                right=int(right),
                synapses=synapses,
                tick=tick,
                generation=generation,
            )
            for left, right in relations
        ]
        pulse_total = sum(self._stat_for(item["relation_id"]).pulse_count for item in metrics)
        active_count = sum(1 for item in metrics if item["pulse_active"])
        runtime_h256 = _canonical_hash(
            {
                "schema": RELATION_RUNTIME_SCHEMA,
                "last_sample_tick": self.last_sample_tick,
                "stats": {
                    key: value.to_dict()
                    for key, value in sorted(self.stats.items())
                },
            }
        )
        return {
            "schema": RELATION_RUNTIME_SCHEMA,
            "status": RELATION_RUNTIME_STATUS,
            "authority": RELATION_RUNTIME_AUTHORITY,
            "mutates_queen": False,
            "physical_claim": False,
            "sample_interval_ticks": self.sample_interval_ticks,
            "sample_hz_at_240hz": 240.0 / self.sample_interval_ticks,
            "signal_threshold": self.signal_threshold,
            "direction_semantics": "HIGHER_ACTIVITY_TO_LOWER_ACTIVITY_VISUAL_CANDIDATE",
            "relation_count": len(metrics),
            "active_relation_count": active_count,
            "pulse_total": pulse_total,
            "last_sample_tick": self.last_sample_tick,
            "runtime_h256": runtime_h256,
            "relations": metrics,
        }

    def to_checkpoint(self) -> dict[str, Any]:
        return {
            "schema": RELATION_RUNTIME_SCHEMA,
            "sample_interval_ticks": self.sample_interval_ticks,
            "signal_threshold": self.signal_threshold,
            "last_sample_tick": self.last_sample_tick,
            "stats": {
                key: value.to_dict()
                for key, value in sorted(self.stats.items())
            },
        }

    @classmethod
    def from_checkpoint(cls, payload: Any) -> "RelationRuntime":
        if not isinstance(payload, dict) or payload.get("schema") != RELATION_RUNTIME_SCHEMA:
            return cls()
        runtime = cls(
            sample_interval_ticks=int(
                payload.get("sample_interval_ticks", RELATION_SAMPLE_INTERVAL_TICKS)
            ),
            signal_threshold=float(
                payload.get("signal_threshold", RELATION_SIGNAL_THRESHOLD)
            ),
        )
        runtime.last_sample_tick = int(payload.get("last_sample_tick", -1))
        raw_stats = payload.get("stats") or {}
        if not isinstance(raw_stats, dict):
            raise ValueError("relation runtime stats must be an object")
        for relation_id, raw in raw_stats.items():
            if not isinstance(raw, dict):
                raise ValueError("relation runtime stat must be an object")
            pulse_count = int(raw.get("pulse_count", 0))
            if pulse_count < 0:
                raise ValueError("pulse_count cannot be negative")
            last_tick = raw.get("last_pulse_tick")
            last_generation = raw.get("last_pulse_generation")
            runtime.stats[str(relation_id)] = RelationPulseStat(
                pulse_count=pulse_count,
                last_pulse_tick=None if last_tick is None else int(last_tick),
                last_pulse_generation=(
                    None if last_generation is None else int(last_generation)
                ),
            )
        return runtime
