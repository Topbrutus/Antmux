from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any

from z3_echo import CenterCoupling12, FourTriadZState

STEREO_SOURCE_SCHEMA = "ANTMUX-X72-STEREO-SOURCE-v0.1"
STEREO_SOURCE_STATUS = "CANDIDATE"
STEREO_SOURCE_AUTHORITY = "OBSERVATION_ONLY"
SIDE_CHANNELS = 12
ZERO_TOLERANCE = 1e-12


def _canonical_hash(payload: Any) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _state_payload(state: FourTriadZState) -> list[list[list[float]]]:
    payload: list[list[list[float]]] = []
    for index in range(state.coefficient_count):
        row: list[list[float]] = []
        for value in state.channels_at(index).values:
            item = complex(value)
            if not math.isfinite(item.real) or not math.isfinite(item.imag):
                raise ValueError("stereo source state must stay finite")
            row.append([float(item.real), float(item.imag)])
        payload.append(row)
    return payload


def _latest_real_channels(state: FourTriadZState, field: str) -> tuple[float, ...]:
    values = state.channels_at(state.coefficient_count - 1).values
    out: list[float] = []
    for index, value in enumerate(values):
        item = complex(value)
        if not math.isfinite(item.real) or not math.isfinite(item.imag):
            raise ValueError(f"{field}[{index}] must be finite")
        if abs(item.imag) > ZERO_TOLERANCE:
            raise ValueError(f"{field}[{index}] must remain real on the live path")
        out.append(float(item.real))
    if len(out) != SIDE_CHANNELS:
        raise ValueError("stereo source requires exactly 12 channels per side")
    return tuple(out)
@dataclass(frozen=True)
class StereoZSourceFrame:
    source: FourTriadZState
    left_state: FourTriadZState
    right_state: FourTriadZState
    left_theta: float
    right_theta: float
    left_channels: tuple[float, ...]
    right_channels: tuple[float, ...]
    bilateral_mean: tuple[float, ...]
    source_h256: str
    left_h256: str
    right_h256: str
    bilateral_h256: str

    @classmethod
    def from_source(
        cls,
        *,
        source: FourTriadZState,
        theta: float,
    ) -> "StereoZSourceFrame":
        if type(source) is not FourTriadZState:
            raise TypeError("source must be exactly FourTriadZState")
        angle = float(theta)
        if not math.isfinite(angle):
            raise ValueError("theta must be finite")

        left_theta = angle
        right_theta = -angle
        left_state = CenterCoupling12.from_theta(left_theta).apply(source)
        right_state = CenterCoupling12.from_theta(right_theta).apply(source)

        left_channels = _latest_real_channels(left_state, "left_channels")
        right_channels = _latest_real_channels(right_state, "right_channels")
        bilateral_mean = tuple(
            (left_channels[index] + right_channels[index]) / 2.0
            for index in range(SIDE_CHANNELS)
        )

        return cls(
            source=source,
            left_state=left_state,
            right_state=right_state,
            left_theta=left_theta,
            right_theta=right_theta,
            left_channels=left_channels,
            right_channels=right_channels,
            bilateral_mean=bilateral_mean,
            source_h256=_canonical_hash(_state_payload(source)),
            left_h256=_canonical_hash(_state_payload(left_state)),
            right_h256=_canonical_hash(_state_payload(right_state)),
            bilateral_h256=_canonical_hash(bilateral_mean),
        )
    def verify(self) -> bool:
        if self.right_theta != -self.left_theta:
            return False
        expected_left = CenterCoupling12.from_theta(self.left_theta).apply(self.source)
        expected_right = CenterCoupling12.from_theta(self.right_theta).apply(self.source)
        if self.left_state != expected_left or self.right_state != expected_right:
            return False
        if self.left_channels != _latest_real_channels(expected_left, "left_channels"):
            return False
        if self.right_channels != _latest_real_channels(expected_right, "right_channels"):
            return False
        expected_mean = tuple(
            (self.left_channels[index] + self.right_channels[index]) / 2.0
            for index in range(SIDE_CHANNELS)
        )
        return (
            self.bilateral_mean == expected_mean
            and self.source_h256 == _canonical_hash(_state_payload(self.source))
            and self.left_h256 == _canonical_hash(_state_payload(self.left_state))
            and self.right_h256 == _canonical_hash(_state_payload(self.right_state))
            and self.bilateral_h256 == _canonical_hash(self.bilateral_mean)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": STEREO_SOURCE_SCHEMA,
            "status": STEREO_SOURCE_STATUS,
            "authority": STEREO_SOURCE_AUTHORITY,
            "mutates_queen": False,
            "physical_claim": False,
            "source_transform": "CENTER_COUPLING12_AT_STEREO_ENTRY",
            "left": {
                "side": "G",
                "theta": self.left_theta,
                "calculation_direction": "COUNTERCLOCKWISE",
                "channels": list(self.left_channels),
                "state_h256": self.left_h256,
            },
            "right": {
                "side": "D",
                "theta": self.right_theta,
                "calculation_direction": "CLOCKWISE",
                "channels": list(self.right_channels),
                "state_h256": self.right_h256,
            },
            "render_contract": {
                "visible_rotation": False,
                "mirror_x": False,
                "negative_eye": False,
                "rule": "OPPOSITE_CALCULATION_DIRECTION_STABLE_RENDER",
            },
            "bilateral_mean": list(self.bilateral_mean),
            "source_h256": self.source_h256,
            "bilateral_h256": self.bilateral_h256,
            "verified": self.verify(),
        }
