from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any

from .stereo_source import StereoZSourceFrame

DAAT_GATE_SCHEMA = "ANTMUX-X72-DAAT-GATE-v0.1"
DAAT_GATE_STATUS = "CANDIDATE"
DAAT_GATE_AUTHORITY = "OBSERVATION_ONLY"
CHANNELS = 12


def _canonical_hash(payload: Any) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _finite_tuple(values: tuple[float, ...], field: str) -> tuple[float, ...]:
    if len(values) != CHANNELS:
        raise ValueError(f"{field} must contain exactly {CHANNELS} channels")
    out = tuple(float(value) for value in values)
    if any(not math.isfinite(value) for value in out):
        raise ValueError(f"{field} must stay finite")
    return out


def _energy(values: tuple[float, ...]) -> float:
    return math.fsum(value * value for value in values)
@dataclass(frozen=True)
class DaatGateFrame:
    tick: int
    generation: int
    source_h256: str
    left: tuple[float, ...]
    right: tuple[float, ...]
    center: tuple[float, ...]
    residual: tuple[float, ...]
    left_reconstructed: tuple[float, ...]
    right_reconstructed: tuple[float, ...]
    pair_energy: float
    decomposed_energy: float
    daat_h256: str

    @classmethod
    def from_stereo_source(
        cls,
        stereo: StereoZSourceFrame,
        *,
        tick: int,
        generation: int,
    ) -> "DaatGateFrame":
        if type(stereo) is not StereoZSourceFrame:
            raise TypeError("stereo must be exactly StereoZSourceFrame")
        if not stereo.verify():
            raise ValueError("stereo source must verify")
        if type(tick) is not int or tick < 0:
            raise ValueError("tick must be a non-negative integer")
        if type(generation) is not int or generation < 0:
            raise ValueError("generation must be a non-negative integer")

        left = _finite_tuple(stereo.left_channels, "left")
        right = _finite_tuple(stereo.right_channels, "right")
        center = tuple((left[i] + right[i]) / 2.0 for i in range(CHANNELS))
        residual = tuple((left[i] - right[i]) / 2.0 for i in range(CHANNELS))
        left_reconstructed = tuple(center[i] + residual[i] for i in range(CHANNELS))
        right_reconstructed = tuple(center[i] - residual[i] for i in range(CHANNELS))
        pair_energy = _energy(left) + _energy(right)
        decomposed_energy = 2.0 * (_energy(center) + _energy(residual))
        payload = {
            "schema": DAAT_GATE_SCHEMA,
            "tick": tick,
            "generation": generation,
            "source_h256": stereo.source_h256,
            "left": left,
            "right": right,
            "center": center,
            "residual": residual,
        }

        return cls(
            tick=tick,
            generation=generation,
            source_h256=stereo.source_h256,
            left=left,
            right=right,
            center=center,
            residual=residual,
            left_reconstructed=left_reconstructed,
            right_reconstructed=right_reconstructed,
            pair_energy=pair_energy,
            decomposed_energy=decomposed_energy,
            daat_h256=_canonical_hash(payload),
        )
    def verify(self, *, tolerance: float = 1e-12) -> bool:
        def close_tuple(
            observed: tuple[float, ...],
            expected: tuple[float, ...],
        ) -> bool:
            return all(
                abs(observed[i] - expected[i])
                <= tolerance * max(1.0, abs(observed[i]), abs(expected[i]))
                for i in range(CHANNELS)
            )

        if not close_tuple(self.left_reconstructed, self.left):
            return False
        if not close_tuple(self.right_reconstructed, self.right):
            return False

        expected_center = tuple(
            (self.left[i] + self.right[i]) / 2.0 for i in range(CHANNELS)
        )
        expected_residual = tuple(
            (self.left[i] - self.right[i]) / 2.0 for i in range(CHANNELS)
        )
        if self.center != expected_center or self.residual != expected_residual:
            return False

        scale = max(1.0, abs(self.pair_energy), abs(self.decomposed_energy))
        if abs(self.pair_energy - self.decomposed_energy) > tolerance * scale:
            return False

        payload = {
            "schema": DAAT_GATE_SCHEMA,
            "tick": self.tick,
            "generation": self.generation,
            "source_h256": self.source_h256,
            "left": self.left,
            "right": self.right,
            "center": self.center,
            "residual": self.residual,
        }
        return self.daat_h256 == _canonical_hash(payload)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": DAAT_GATE_SCHEMA,
            "status": DAAT_GATE_STATUS,
            "authority": DAAT_GATE_AUTHORITY,
            "mutates_queen": False,
            "physical_claim": False,
            "tick": self.tick,
            "generation": self.generation,
            "source_h256": self.source_h256,
            "route": ["Z_INPUT", "STEREO_G_D", "DAAT"],
            "mapped_now": {
                "axis": "LEFT_RIGHT_ONLY",
                "left": "G",
                "right": "D",
                "meeting_point": "DAAT",
            },
            "deliberately_unmapped": [
                "VERTICAL_AXIS",
                "DEPTH_AXIS",
                "FULL_TREE_PATHS",
                "SEFIROT_SEMANTICS",
            ],
            "left": list(self.left),
            "right": list(self.right),
            "daat": {
                "center": list(self.center),
                "residual": list(self.residual),
                "transform": {
                    "center": "(G + D) / 2",
                    "residual": "(G - D) / 2",
                    "reconstruct_G": "center + residual",
                    "reconstruct_D": "center - residual",
                },
            },
            "invariants": {
                "lossless_left_right_reconstruction": all(
                    abs(self.left_reconstructed[i] - self.left[i])
                    <= 1e-12 * max(
                        1.0,
                        abs(self.left_reconstructed[i]),
                        abs(self.left[i]),
                    )
                    and abs(self.right_reconstructed[i] - self.right[i])
                    <= 1e-12 * max(
                        1.0,
                        abs(self.right_reconstructed[i]),
                        abs(self.right[i]),
                    )
                    for i in range(CHANNELS)
                ),
                "pair_energy": self.pair_energy,
                "decomposed_energy": self.decomposed_energy,
                "energy_identity_error": abs(
                    self.pair_energy - self.decomposed_energy
                ),
            },
            "hopscotch_model": {
                "ordered_route": True,
                "same_tick_pair_required": True,
                "side_identity_preserved": True,
                "completion_condition": "G_AND_D_PRESENT_AT_DAAT",
            },
            "daat_h256": self.daat_h256,
            "verified": self.verify(),
        }
