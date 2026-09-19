from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Iterable

from z3_echo import (
    CenterCoupling12,
    CenterSummary3WithResidual,
    Channels12,
    FourTriadZState,
    Z3EchoTransfer,
    euler_zyz,
    seal_center_provenance,
    seal_provenance,
    verify_center_provenance,
    verify_provenance,
)

RUNTIME_SCHEMA = "ANTMUX-X72-Z3-RUNTIME-v0.1"
ADAPTER_STATUS = "CANDIDATE"
ADAPTER_AUTHORITY = "OBSERVATION_ONLY"
GROUPS: tuple[tuple[str, tuple[int, ...]], ...] = (
    ("G0_S1_S2", (0, 1)),
    ("G1_S3_S4", (2, 3)),
    ("G2_S5_S6", (4, 5)),
    ("G3_S7", (6,)),
)
CHANNEL_NAMES = ("activity", "memory", "crystal")
SAMPLE_INTERVAL_TICKS = 60
HISTORY_SIZE = 32
GENERATION_TICKS = 7200


def _canonical_hash(payload: Any) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _mean(values: Iterable[float]) -> float:
    data = tuple(float(value) for value in values)
    if not data:
        raise ValueError("cannot average an empty sequence")
    return math.fsum(data) / len(data)


def _finite_float(value: Any, field: str) -> float:
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"{field} must be finite")
    return out


def _triad_groups_from_synapses(synapses: list[Any]) -> Channels12:
    if len(synapses) != 7:
        raise ValueError("Z3 runtime adapter requires exactly seven Queen synapses")

    values: list[float] = []
    for _, indices in GROUPS:
        group = [synapses[index] for index in indices]
        values.extend(
            (
                _mean(_finite_float(item.activity, "activity") for item in group),
                _mean(_finite_float(item.memory, "memory") for item in group),
                _mean(_finite_float(item.crystal, "crystal") for item in group),
            )
        )
    return Channels12.from_values(values)


@dataclass(frozen=True)
class Z3RuntimeSnapshot:
    tick: int
    generation: int
    sample_count: int
    theta: float
    center: tuple[float, float, float]
    center_energy: float
    residual_energy: float
    source_state_h256: str
    coupled_state_h256: str
    center_provenance_h256: str
    echo_provenance_h256: tuple[str, str, str, str]
    fast_verified: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "tick": self.tick,
            "generation": self.generation,
            "sample_count": self.sample_count,
            "theta": self.theta,
            "center": list(self.center),
            "center_energy": self.center_energy,
            "residual_energy": self.residual_energy,
            "source_state_h256": self.source_state_h256,
            "coupled_state_h256": self.coupled_state_h256,
            "center_provenance_h256": self.center_provenance_h256,
            "echo_provenance_h256": list(self.echo_provenance_h256),
            "fast_verified": self.fast_verified,
        }


class Z3RuntimeBridge:
    """Read-only runtime projection from the seven-synapse Queen into Z3 v0.1.

    This adapter does not mutate Queen state and does not claim physical meaning.
    The four triads are deterministic aggregates of activity/memory/crystal:
    (S1,S2), (S3,S4), (S5,S6), (S7).
    """

    def __init__(
        self,
        *,
        sample_interval_ticks: int = SAMPLE_INTERVAL_TICKS,
        history_size: int = HISTORY_SIZE,
    ) -> None:
        if type(sample_interval_ticks) is not int or sample_interval_ticks <= 0:
            raise ValueError("sample_interval_ticks must be a positive integer")
        if type(history_size) is not int or history_size <= 0:
            raise ValueError("history_size must be a positive integer")
        self.sample_interval_ticks = sample_interval_ticks
        self.history_size = history_size
        self.history: list[tuple[float, ...]] = []
        self.last_sample_tick = -1
        self.latest: Z3RuntimeSnapshot | None = None

    def observe(self, *, tick: int, generation: int, synapses: list[Any]) -> bool:
        if tick <= 0 or tick % self.sample_interval_ticks != 0:
            return False
        if tick == self.last_sample_tick:
            return False

        channels = _triad_groups_from_synapses(synapses)
        self.history.append(tuple(value.real for value in channels.values))
        self.history = self.history[-self.history_size :]
        self.last_sample_tick = tick
        self.latest = self._build_snapshot(tick=tick, generation=generation)
        return True

    def _build_snapshot(self, *, tick: int, generation: int) -> Z3RuntimeSnapshot:
        rows = [Channels12.from_values(values) for values in self.history]
        source = FourTriadZState.from_channel_series(rows)

        # First live integration keeps the Echo transfer neutral. This proves
        # the whole path without inventing a gain/rotation law.
        transfer = Z3EchoTransfer(
            gain=1.0,
            delay=0,
            rotation=euler_zyz(0.0, 0.0, 0.0),
        )

        echoed_triads = []
        echo_hashes: list[str] = []
        echo_verified = True
        for triad in source.triads:
            echoed = transfer.apply(triad)
            frame = seal_provenance(
                source=triad,
                transfer=transfer,
                echoed=echoed,
                euler_zyz_angles=(0.0, 0.0, 0.0),
            )
            echo_verified = echo_verified and verify_provenance(
                frame,
                source=triad,
                echoed=echoed,
            )
            echoed_triads.append(echoed)
            echo_hashes.append(frame.provenance_h256)

        echoed_state = FourTriadZState(tuple(echoed_triads))

        # Candidate runtime phase: one full center-coupling turn per Queen
        # generation period. This is an internal design mapping, not physics.
        theta = math.tau * ((tick % GENERATION_TICKS) / GENERATION_TICKS)
        coupling = CenterCoupling12.from_theta(theta)
        coupled = coupling.apply(echoed_state)
        summary = CenterSummary3WithResidual.decompose(coupled)
        center_frame = seal_center_provenance(
            source=echoed_state,
            coupling=coupling,
            coupled=coupled,
            summary=summary,
        )
        center_verified = verify_center_provenance(
            center_frame,
            source=echoed_state,
            coupled=coupled,
            summary=summary,
        )

        center_now = summary.center.samples[-1]
        center_values = tuple(float(value.real) for value in center_now.as_tuple())
        residual_energy = math.fsum(
            abs(value) ** 2
            for residual in summary.residuals
            for value in residual.samples[-1].as_tuple()
        )
        center_energy = math.fsum(abs(value) ** 2 for value in center_now.as_tuple())

        return Z3RuntimeSnapshot(
            tick=tick,
            generation=generation,
            sample_count=len(self.history),
            theta=theta,
            center=center_values,
            center_energy=float(center_energy),
            residual_energy=float(residual_energy),
            source_state_h256=center_frame.source_state_h256,
            coupled_state_h256=center_frame.coupled_state_h256,
            center_provenance_h256=center_frame.provenance_h256,
            echo_provenance_h256=tuple(echo_hashes),  # type: ignore[arg-type]
            fast_verified=bool(echo_verified and center_verified),
        )

    def visual_state(self) -> dict[str, Any]:
        latest = self.latest
        return {
            "schema": RUNTIME_SCHEMA,
            "status": ADAPTER_STATUS,
            "authority": ADAPTER_AUTHORITY,
            "mutates_queen": False,
            "physical_claim": False,
            "topology": {
                "total_nodes": 13,
                "peripheral_channels": 12,
                "center_channels": 3,
                "groups": [
                    {"name": name, "synapse_indices": list(indices)}
                    for name, indices in GROUPS
                ],
                "triad_channels": list(CHANNEL_NAMES),
            },
            "sample_interval_ticks": self.sample_interval_ticks,
            "history_size": self.history_size,
            "history_count": len(self.history),
            "latest": latest.to_dict() if latest is not None else None,
        }

    def whole_projection(self) -> dict[str, Any]:
        payload = self.visual_state()
        payload["history_h256"] = _canonical_hash(self.history)
        return payload

    def to_checkpoint(self) -> dict[str, Any]:
        return {
            "schema": RUNTIME_SCHEMA,
            "sample_interval_ticks": self.sample_interval_ticks,
            "history_size": self.history_size,
            "history": [list(row) for row in self.history],
            "last_sample_tick": self.last_sample_tick,
            "latest_generation": (
                self.latest.generation if self.latest is not None else None
            ),
        }

    @classmethod
    def from_checkpoint(cls, payload: Any, *, tick: int, generation: int) -> "Z3RuntimeBridge":
        if not isinstance(payload, dict) or payload.get("schema") != RUNTIME_SCHEMA:
            return cls()
        bridge = cls(
            sample_interval_ticks=int(payload.get("sample_interval_ticks", SAMPLE_INTERVAL_TICKS)),
            history_size=int(payload.get("history_size", HISTORY_SIZE)),
        )
        raw_history = payload.get("history") or []
        for row in raw_history[-bridge.history_size :]:
            channels = Channels12.from_values(row)
            bridge.history.append(tuple(float(value.real) for value in channels.values))
        bridge.last_sample_tick = int(payload.get("last_sample_tick", -1))
        if bridge.history:
            latest_tick = (
                bridge.last_sample_tick
                if bridge.last_sample_tick >= 0
                else tick
            )
            raw_latest_generation = payload.get("latest_generation")
            latest_generation = (
                int(raw_latest_generation)
                if raw_latest_generation is not None
                else generation
            )
            bridge.latest = bridge._build_snapshot(
                tick=latest_tick,
                generation=latest_generation,
            )
        return bridge
