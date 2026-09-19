from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Iterable

from z3_echo import FourTriadZState, Triad3

STEREO_SCHEMA = "ANTMUX-X72-STEREO27-v0.1"
STEREO_STATUS = "CANDIDATE"
STEREO_AUTHORITY = "OBSERVATION_ONLY"
UNIT_COUNT = 27
CHANNEL_COUNT = 54
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


def _finite_real(value: Any, field: str) -> float:
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"{field} must be finite")
    return out


def _real_component(value: complex | float | int, field: str) -> float:
    item = complex(value)
    if not math.isfinite(item.real) or not math.isfinite(item.imag):
        raise ValueError(f"{field} must be finite")
    if abs(item.imag) > ZERO_TOLERANCE:
        raise ValueError(
            f"{field} has a non-zero imaginary component; stereo27 v0.1 "
            "only accepts the current real-valued live path"
        )
    return float(item.real)


def _values27(values: Iterable[float | int]) -> tuple[float, ...]:
    out = tuple(_finite_real(value, f"values[{index}]") for index, value in enumerate(values))
    if len(out) != UNIT_COUNT:
        raise ValueError("stereo27 requires exactly 27 scalar units")
    return out


@dataclass(frozen=True)
class Stereo27Frame:
    positive: tuple[float, ...]
    negative: tuple[float, ...]
    zero_plane: tuple[float, ...]
    plouf: bool
    max_zero_error: float
    positive_h256: str
    negative_h256: str
    zero_h256: str
    stereo_h256: str

    @classmethod
    def from_values(cls, values: Iterable[float | int]) -> "Stereo27Frame":
        positive = _values27(values)
        negative = tuple(-value for value in reversed(positive))
        return cls.from_sides(positive=positive, negative=negative)

    @classmethod
    def from_sides(
        cls,
        *,
        positive: Iterable[float | int],
        negative: Iterable[float | int],
    ) -> "Stereo27Frame":
        positive27 = _values27(positive)
        negative27 = _values27(negative)
        zero_plane = tuple(
            positive27[index] + negative27[UNIT_COUNT - 1 - index]
            for index in range(UNIT_COUNT)
        )
        max_zero_error = max(abs(value) for value in zero_plane)
        plouf = max_zero_error <= ZERO_TOLERANCE
        positive_h256 = _canonical_hash(positive27)
        negative_h256 = _canonical_hash(negative27)
        zero_h256 = _canonical_hash(zero_plane)
        stereo_h256 = _canonical_hash(
            {
                "schema": STEREO_SCHEMA,
                "positive_h256": positive_h256,
                "negative_h256": negative_h256,
                "zero_h256": zero_h256,
                "plouf": plouf,
            }
        )
        return cls(
            positive=positive27,
            negative=negative27,
            zero_plane=zero_plane,
            plouf=plouf,
            max_zero_error=max_zero_error,
            positive_h256=positive_h256,
            negative_h256=negative_h256,
            zero_h256=zero_h256,
            stereo_h256=stereo_h256,
        )

    @classmethod
    def from_z3(
        cls,
        *,
        source: FourTriadZState,
        coupled: FourTriadZState,
        center: Triad3,
    ) -> "Stereo27Frame":
        if type(source) is not FourTriadZState:
            raise TypeError("source must be exactly FourTriadZState")
        if type(coupled) is not FourTriadZState:
            raise TypeError("coupled must be exactly FourTriadZState")
        if type(center) is not Triad3:
            raise TypeError("center must be exactly Triad3")
        if source.coefficient_count != coupled.coefficient_count:
            raise ValueError("source and coupled coefficient counts must match")
        index = source.coefficient_count - 1
        source12 = tuple(
            _real_component(value, f"source[{i}]")
            for i, value in enumerate(source.channels_at(index).values)
        )
        coupled12 = tuple(
            _real_component(value, f"coupled[{i}]")
            for i, value in enumerate(coupled.channels_at(index).values)
        )
        center3 = tuple(
            _real_component(value, f"center[{i}]")
            for i, value in enumerate(center.as_tuple())
        )
        return cls.from_values(source12 + coupled12 + center3)


    def verify(self) -> bool:
        expected_negative = tuple(-value for value in reversed(self.positive))
        if self.negative != expected_negative:
            return False
        expected_zero = tuple(
            self.positive[index] + self.negative[UNIT_COUNT - 1 - index]
            for index in range(UNIT_COUNT)
        )
        if self.zero_plane != expected_zero:
            return False
        max_zero_error = max(abs(value) for value in expected_zero)
        if self.plouf != (max_zero_error <= ZERO_TOLERANCE):
            return False
        if self.max_zero_error != max_zero_error:
            return False
        positive_h256 = _canonical_hash(self.positive)
        negative_h256 = _canonical_hash(self.negative)
        zero_h256 = _canonical_hash(self.zero_plane)
        stereo_h256 = _canonical_hash(
            {
                "schema": STEREO_SCHEMA,
                "positive_h256": positive_h256,
                "negative_h256": negative_h256,
                "zero_h256": zero_h256,
                "plouf": self.plouf,
            }
        )
        return (
            self.positive_h256 == positive_h256
            and self.negative_h256 == negative_h256
            and self.zero_h256 == zero_h256
            and self.stereo_h256 == stereo_h256
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": STEREO_SCHEMA,
            "status": STEREO_STATUS,
            "authority": STEREO_AUTHORITY,
            "mutates_queen": False,
            "physical_claim": False,
            "units_per_side": UNIT_COUNT,
            "stereo_channels": CHANNEL_COUNT,
            "layout": {
                "positive": "27 canonical units",
                "negative": "27 reversed sign-mirror units",
                "zero_plane": "pairwise neutral residual",
                "source_partition": ["source12", "coupled12", "center3"],
            },
            "positive": list(self.positive),
            "negative": list(self.negative),
            "zero_plane": list(self.zero_plane),
            "plouf": self.plouf,
            "pas_plouf": not self.plouf,
            "max_zero_error": self.max_zero_error,
            "positive_h256": self.positive_h256,
            "negative_h256": self.negative_h256,
            "zero_h256": self.zero_h256,
            "stereo_h256": self.stereo_h256,
            "verified": self.verify(),
        }
