from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any

from z3_echo import FourTriadZState, Triad3

HEMISPHERE_SCHEMA = "ANTMUX-X72-HEMISPHERE4-v0.1"
HEMISPHERE_STATUS = "CANDIDATE"
HEMISPHERE_AUTHORITY = "OBSERVATION_ONLY"
SIDE_CHANNELS = 12
CENTER_CHANNELS = 3


def _canonical_hash(payload: Any) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _real(value: complex | float | int, field: str) -> float:
    item = complex(value)
    if not math.isfinite(item.real) or not math.isfinite(item.imag):
        raise ValueError(f"{field} must be finite")
    if abs(item.imag) > 1e-12:
        raise ValueError(f"{field} must remain on the current real-valued live path")
    return float(item.real)
def _mirror(values: tuple[float, ...]) -> tuple[float, ...]:
    return tuple(-value for value in reversed(values))


@dataclass(frozen=True)
class Hemisphere4Frame:
    left_positive: tuple[float, ...]
    left_negative: tuple[float, ...]
    right_positive: tuple[float, ...]
    right_negative: tuple[float, ...]
    center: tuple[float, float, float]
    bilateral_mean: tuple[float, ...]
    quadrants_h256: str
    bilateral_h256: str

    @classmethod
    def from_z3(
        cls,
        *,
        source: FourTriadZState,
        coupled: FourTriadZState,
        center: Triad3,
    ) -> "Hemisphere4Frame":
        if type(source) is not FourTriadZState:
            raise TypeError("source must be exactly FourTriadZState")
        if type(coupled) is not FourTriadZState:
            raise TypeError("coupled must be exactly FourTriadZState")
        if type(center) is not Triad3:
            raise TypeError("center must be exactly Triad3")
        if source.coefficient_count != coupled.coefficient_count:
            raise ValueError("source and coupled coefficient counts must match")
        index = source.coefficient_count - 1
        left_positive = tuple(
            _real(value, f"left_positive[{i}]")
            for i, value in enumerate(source.channels_at(index).values)
        )
        right_positive = tuple(
            _real(value, f"right_positive[{i}]")
            for i, value in enumerate(coupled.channels_at(index).values)
        )
        if len(left_positive) != SIDE_CHANNELS or len(right_positive) != SIDE_CHANNELS:
            raise ValueError("hemisphere4 requires 12 channels on each live side")

        left_negative = _mirror(left_positive)
        right_negative = _mirror(right_positive)
        center_values = tuple(
            _real(value, f"center[{i}]")
            for i, value in enumerate(center.as_tuple())
        )
        if len(center_values) != CENTER_CHANNELS:
            raise ValueError("hemisphere4 requires exactly 3 center channels")

        bilateral_mean = tuple(
            (left_positive[i] + right_positive[i]) / 2.0
            for i in range(SIDE_CHANNELS)
        )
        quadrants_payload = {
            "left_positive": left_positive,
            "left_negative": left_negative,
            "right_positive": right_positive,
            "right_negative": right_negative,
            "center": center_values,
        }
        return cls(
            left_positive=left_positive,
            left_negative=left_negative,
            right_positive=right_positive,
            right_negative=right_negative,
            center=center_values,  # type: ignore[arg-type]
            bilateral_mean=bilateral_mean,
            quadrants_h256=_canonical_hash(quadrants_payload),
            bilateral_h256=_canonical_hash(bilateral_mean),
        )

    def verify(self) -> bool:
        if len(self.left_positive) != SIDE_CHANNELS:
            return False
        if len(self.right_positive) != SIDE_CHANNELS:
            return False
        if self.left_negative != _mirror(self.left_positive):
            return False
        if self.right_negative != _mirror(self.right_positive):
            return False
        expected_mean = tuple(
            (self.left_positive[i] + self.right_positive[i]) / 2.0
            for i in range(SIDE_CHANNELS)
        )
        if self.bilateral_mean != expected_mean:
            return False
        payload = {
            "left_positive": self.left_positive,
            "left_negative": self.left_negative,
            "right_positive": self.right_positive,
            "right_negative": self.right_negative,
            "center": self.center,
        }
        return (
            self.quadrants_h256 == _canonical_hash(payload)
            and self.bilateral_h256 == _canonical_hash(self.bilateral_mean)
        )
    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": HEMISPHERE_SCHEMA,
            "status": HEMISPHERE_STATUS,
            "authority": HEMISPHERE_AUTHORITY,
            "mutates_queen": False,
            "physical_claim": False,
            "synchronized_frame": True,
            "quadrants": {
                "left_positive": list(self.left_positive),
                "left_negative": list(self.left_negative),
                "right_positive": list(self.right_positive),
                "right_negative": list(self.right_negative),
            },
            "center": list(self.center),
            "bilateral_mean": list(self.bilateral_mean),
            "layout": {
                "left_positive": "source12",
                "right_positive": "coupled12",
                "left_negative": "reversed sign-mirror of source12",
                "right_negative": "reversed sign-mirror of coupled12",
                "center": "center3 / BOTH",
                "eye_color_basis": "bilateral mean of left/right positive lanes",
            },
            "eye_render_contract": {
                "color_sync": "SAME_TONE_BOTH_EYES_FROM_BILATERAL_MEAN",
                "left_eye": {
                    "data_side": "G",
                    "motif_rotation": "COUNTERCLOCKWISE",
                    "mirror_x": False,
                },
                "right_eye": {
                    "data_side": "D",
                    "motif_rotation": "CLOCKWISE",
                    "mirror_x": True,
                },
                "rotation_relation": "OPPOSITE_DIRECTIONS",
                "visual_goal": "INWARD_OR_OUTWARD_PAIR_NOT_SAME_DIRECTION",
            },
            "figure8_route_candidate": [
                "LEFT_POSITIVE", "CENTER", "RIGHT_POSITIVE", "CENTER",
                "LEFT_NEGATIVE", "CENTER", "RIGHT_NEGATIVE", "CENTER",
            ],
            "signal_side_tags": {
                "left": "G",
                "right": "D",
                "center": "BOTH",
            },
            "carrier_routes": {
                "G_POS": {"side": "G", "polarity": "POS", "lane": "left_positive"},
                "G_NEG": {"side": "G", "polarity": "NEG", "lane": "left_negative"},
                "D_POS": {"side": "D", "polarity": "POS", "lane": "right_positive"},
                "D_NEG": {"side": "D", "polarity": "NEG", "lane": "right_negative"},
                "BOTH": {"side": "BOTH", "polarity": "CENTER", "lane": "center"},
            },
            "quadrants_h256": self.quadrants_h256,
            "bilateral_h256": self.bilateral_h256,
            "verified": self.verify(),
        }
