from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any

from .daat_gate import CHANNELS
from .daat_link import DaatLinkFrame

OSCILLATOR_SCHEMA = "ANTMUX-X72-BOUNDED-OSCILLATOR-v0.1"
OSCILLATOR_STATUS = "CANDIDATE"
OSCILLATOR_AUTHORITY = "OBSERVATION_ONLY"


def _canonical_hash(payload: Any) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _clamp01(value: float) -> float:
    item = float(value)
    if not math.isfinite(item):
        raise ValueError("oscillator values must stay finite")
    return max(0.0, min(1.0, item))


@dataclass(frozen=True)
class OscillatorMode:
    channel: int
    mode_number: int
    amplitude: float
    phase: float
    x: float
    y: float
    radius_error: float
    @classmethod
    def from_components(
        cls,
        *,
        channel: int,
        common_b: float,
        differential_a: float,
        theta: float,
    ) -> "OscillatorMode":
        if not 0 <= channel < CHANNELS:
            raise ValueError("channel out of range")
        if not all(
            math.isfinite(float(value))
            for value in (common_b, differential_a, theta)
        ):
            raise ValueError("oscillator inputs must stay finite")

        mode_number = channel + 1
        amplitude = _clamp01(
            math.hypot(float(common_b), float(differential_a))
        )
        phase = math.remainder(
            mode_number * float(theta),
            math.tau,
        )
        x = amplitude * math.cos(phase)
        y = amplitude * math.sin(phase)
        radius_error = abs(
            (x * x + y * y) - (amplitude * amplitude)
        )

        return cls(
            channel=channel,
            mode_number=mode_number,
            amplitude=amplitude,
            phase=phase,
            x=x,
            y=y,
            radius_error=radius_error,
        )

    def verify(self, *, tolerance: float = 1e-12) -> bool:
        if self.mode_number != self.channel + 1:
            return False
        if not 0.0 <= self.amplitude <= 1.0:
            return False
        if not -math.pi <= self.phase <= math.pi:
            return False
        if abs(self.x) > self.amplitude + tolerance:
            return False
        if abs(self.y) > self.amplitude + tolerance:
            return False
        if self.radius_error > tolerance:
            return False
        return True
    def to_dict(self) -> dict[str, Any]:
        return {
            "channel": self.channel,
            "mode_number": self.mode_number,
            "amplitude": self.amplitude,
            "phase": self.phase,
            "x": self.x,
            "y": self.y,
            "radius_error": self.radius_error,
            "verified": self.verify(),
        }


@dataclass(frozen=True)
class BoundedOscillatorFrame:
    tick: int
    generation: int
    source_h256: str
    theta: float
    modes: tuple[OscillatorMode, ...]
    oscillator_h256: str

    @classmethod
    def from_link(
        cls,
        link: DaatLinkFrame,
        *,
        theta: float,
    ) -> "BoundedOscillatorFrame":
        if type(link) is not DaatLinkFrame:
            raise TypeError("link must be exactly DaatLinkFrame")
        if not link.verify():
            raise ValueError("Da'at link frame must verify")
        if not math.isfinite(float(theta)):
            raise ValueError("theta must be finite")

        modes = tuple(
            OscillatorMode.from_components(
                channel=index,
                common_b=link.common_b[index],
                differential_a=link.differential_a[index],
                theta=float(theta),
            )
            for index in range(CHANNELS)
        )

        payload = {
            "schema": OSCILLATOR_SCHEMA,
            "tick": link.tick,
            "generation": link.generation,
            "source_h256": link.source_h256,
            "theta": float(theta),
            "modes": [mode.to_dict() for mode in modes],
        }
        return cls(
            tick=link.tick,
            generation=link.generation,
            source_h256=link.source_h256,
            theta=float(theta),
            modes=modes,
            oscillator_h256=_canonical_hash(payload),
        )
    def verify(self, *, tolerance: float = 1e-12) -> bool:
        if len(self.modes) != CHANNELS:
            return False
        if not math.isfinite(self.theta):
            return False
        if any(not mode.verify(tolerance=tolerance) for mode in self.modes):
            return False
        if [mode.channel for mode in self.modes] != list(range(CHANNELS)):
            return False
        if [mode.mode_number for mode in self.modes] != list(range(1, CHANNELS + 1)):
            return False

        payload = {
            "schema": OSCILLATOR_SCHEMA,
            "tick": self.tick,
            "generation": self.generation,
            "source_h256": self.source_h256,
            "theta": self.theta,
            "modes": [mode.to_dict() for mode in self.modes],
        }
        return self.oscillator_h256 == _canonical_hash(payload)

    def to_dict(self) -> dict[str, Any]:
        max_radius_error = max(
            (mode.radius_error for mode in self.modes),
            default=0.0,
        )
        return {
            "schema": OSCILLATOR_SCHEMA,
            "status": OSCILLATOR_STATUS,
            "authority": OSCILLATOR_AUTHORITY,
            "mutates_queen": False,
            "physical_claim": False,
            "quantum_claim": False,
            "tick": self.tick,
            "generation": self.generation,
            "source_h256": self.source_h256,
            "theta": self.theta,
            "mode_rule": "mode_number = channel + 1",
            "amplitude_rule": "clamp(hypot(B_i,A_i),0,1)",
            "phase_rule": "remainder(mode_number*theta,2*pi)",
            "state_rule": "x=a*cos(phi), y=a*sin(phi)",
            "bounded": all(
                abs(mode.x) <= mode.amplitude + 1e-12
                and abs(mode.y) <= mode.amplitude + 1e-12
                for mode in self.modes
            ),
            "max_radius_error": max_radius_error,
            "modes": [mode.to_dict() for mode in self.modes],
            "unmapped": [
                "QUANTUM_ENERGY_LEVELS",
                "PLANCK_CONSTANT",
                "PHYSICAL_FREQUENCY",
                "VERTICAL_AXIS",
                "DEPTH_AXIS",
            ],
            "verified": self.verify(),
            "oscillator_h256": self.oscillator_h256,
        }
