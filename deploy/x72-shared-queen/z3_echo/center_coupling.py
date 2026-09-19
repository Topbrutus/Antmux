from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

from .math_core import FiniteZTriad, Triad3

CHANNEL_COUNT = 12
CENTER_CHANNEL_COUNT = 3
RESIDUAL_CHANNEL_COUNT = 9

# Candidate routing schedule for one mirrored 4x3 system.
# First six rotations couple mirror positions. The remaining rotations
# couple the same channel position around the four triads.
CENTER_COUPLING_SCHEDULE_V0_1: tuple[tuple[int, int], ...] = (
    (0, 11),
    (1, 10),
    (2, 9),
    (3, 8),
    (4, 7),
    (5, 6),
    (0, 3),
    (3, 6),
    (6, 9),
    (9, 0),
    (1, 4),
    (4, 7),
    (7, 10),
    (10, 1),
    (2, 5),
    (5, 8),
    (8, 11),
    (11, 2),
)

Matrix12 = tuple[tuple[float, ...], ...]


def _finite_real(value: float | int, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field} must be a real number")
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"{field} must be finite")
    return out


def _finite_complex(value: complex | float | int, field: str) -> complex:
    if isinstance(value, bool) or not isinstance(value, (int, float, complex)):
        raise TypeError(f"{field} must be a real or complex number")
    out = complex(value)
    if not math.isfinite(out.real) or not math.isfinite(out.imag):
        raise ValueError(f"{field} must be finite")
    return out


@dataclass(frozen=True)
class Channels12:
    values: tuple[complex, ...]

    def __post_init__(self) -> None:
        if type(self.values) is not tuple or len(self.values) != CHANNEL_COUNT:
            raise ValueError("values must be exactly a 12-tuple")
        object.__setattr__(
            self,
            "values",
            tuple(
                _finite_complex(value, f"values[{index}]")
                for index, value in enumerate(self.values)
            ),
        )

    @classmethod
    def from_values(cls, values: Iterable[complex | float | int]) -> "Channels12":
        return cls(tuple(values))

    def norm_squared(self) -> float:
        return float(sum(abs(value) ** 2 for value in self.values))


@dataclass(frozen=True)
class FourTriadZState:
    triads: tuple[FiniteZTriad, ...]

    def __post_init__(self) -> None:
        if type(self.triads) is not tuple or len(self.triads) != 4:
            raise ValueError("triads must contain exactly four FiniteZTriad values")
        if any(type(triad) is not FiniteZTriad for triad in self.triads):
            raise TypeError("triads must contain exactly FiniteZTriad values")
        lengths = {len(triad.samples) for triad in self.triads}
        if len(lengths) != 1:
            raise ValueError("all four triads must have the same coefficient length")

    @property
    def coefficient_count(self) -> int:
        return len(self.triads[0].samples)

    def channels_at(self, index: int) -> Channels12:
        if type(index) is not int:
            raise TypeError("index must be an integer")
        if index < 0 or index >= self.coefficient_count:
            raise IndexError(index)
        values: list[complex] = []
        for triad in self.triads:
            values.extend(triad.samples[index].as_tuple())
        return Channels12(tuple(values))

    @classmethod
    def from_channel_series(cls, series: Iterable[Channels12]) -> "FourTriadZState":
        rows = tuple(series)
        if not rows:
            raise ValueError("series must contain at least one Channels12 coefficient")
        if any(type(row) is not Channels12 for row in rows):
            raise TypeError("series must contain exactly Channels12 values")

        grouped: list[list[Triad3]] = [[], [], [], []]
        for row in rows:
            for group in range(4):
                start = group * 3
                grouped[group].append(Triad3(*row.values[start : start + 3]))
        return cls(
            tuple(
                FiniteZTriad.from_samples(group)
                for group in grouped
            )
        )


def _identity12() -> Matrix12:
    return tuple(
        tuple(1.0 if row == col else 0.0 for col in range(CHANNEL_COUNT))
        for row in range(CHANNEL_COUNT)
    )


def transpose12(matrix: Matrix12) -> Matrix12:
    _validate_matrix12(matrix)
    return tuple(
        tuple(matrix[col][row] for col in range(CHANNEL_COUNT))
        for row in range(CHANNEL_COUNT)
    )


def matmul12(left: Matrix12, right: Matrix12) -> Matrix12:
    _validate_matrix12(left)
    _validate_matrix12(right)
    return tuple(
        tuple(
            sum(left[row][k] * right[k][col] for k in range(CHANNEL_COUNT))
            for col in range(CHANNEL_COUNT)
        )
        for row in range(CHANNEL_COUNT)
    )


def apply_matrix12(matrix: Matrix12, channels: Channels12) -> Channels12:
    _validate_matrix12(matrix)
    if type(channels) is not Channels12:
        raise TypeError("channels must be exactly Channels12")
    return Channels12(
        tuple(
            sum(matrix[row][col] * channels.values[col] for col in range(CHANNEL_COUNT))
            for row in range(CHANNEL_COUNT)
        )
    )


def _validate_matrix12(matrix: Matrix12) -> None:
    if type(matrix) is not tuple or len(matrix) != CHANNEL_COUNT:
        raise ValueError("matrix must contain exactly 12 rows")
    for row_index, row in enumerate(matrix):
        if type(row) is not tuple or len(row) != CHANNEL_COUNT:
            raise ValueError("matrix must be exactly 12x12")
        for col_index, value in enumerate(row):
            _finite_real(value, f"matrix[{row_index}][{col_index}]")


def givens12(i: int, j: int, theta: float) -> Matrix12:
    if type(i) is not int or type(j) is not int:
        raise TypeError("Givens indices must be integers")
    if i == j or not (0 <= i < CHANNEL_COUNT) or not (0 <= j < CHANNEL_COUNT):
        raise ValueError("Givens indices must be distinct values in [0, 11]")
    angle = _finite_real(theta, "theta")
    c = math.cos(angle)
    s = math.sin(angle)
    rows = [list(row) for row in _identity12()]
    rows[i][i] = c
    rows[i][j] = -s
    rows[j][i] = s
    rows[j][j] = c
    return tuple(tuple(row) for row in rows)


def build_center_coupling_matrix(
    theta: float,
    *,
    schedule: tuple[tuple[int, int], ...] = CENTER_COUPLING_SCHEDULE_V0_1,
) -> Matrix12:
    angle = _finite_real(theta, "theta")
    if type(schedule) is not tuple or not schedule:
        raise ValueError("schedule must be a non-empty tuple of channel pairs")

    matrix = _identity12()
    for pair in schedule:
        if type(pair) is not tuple or len(pair) != 2:
            raise ValueError("each coupling schedule entry must be a 2-tuple")
        rotation = givens12(pair[0], pair[1], angle)
        matrix = matmul12(rotation, matrix)
    return matrix


def orthogonality_error12(matrix: Matrix12) -> float:
    product = matmul12(transpose12(matrix), matrix)
    identity = _identity12()
    return max(
        abs(product[row][col] - identity[row][col])
        for row in range(CHANNEL_COUNT)
        for col in range(CHANNEL_COUNT)
    )


@dataclass(frozen=True)
class CenterCoupling12:
    theta: float
    matrix: Matrix12

    def __post_init__(self) -> None:
        angle = _finite_real(self.theta, "theta")
        _validate_matrix12(self.matrix)
        expected = build_center_coupling_matrix(angle)
        delta = max(
            abs(self.matrix[row][col] - expected[row][col])
            for row in range(CHANNEL_COUNT)
            for col in range(CHANNEL_COUNT)
        )
        if delta > 1e-12:
            raise ValueError("matrix does not match the v0.1 center coupling schedule")
        if orthogonality_error12(self.matrix) > 1e-10:
            raise ValueError("center coupling matrix must be orthogonal")
        object.__setattr__(self, "theta", angle)

    @classmethod
    def from_theta(cls, theta: float) -> "CenterCoupling12":
        angle = _finite_real(theta, "theta")
        return cls(theta=angle, matrix=build_center_coupling_matrix(angle))

    def apply(self, state: FourTriadZState) -> FourTriadZState:
        if type(state) is not FourTriadZState:
            raise TypeError("state must be exactly FourTriadZState")
        return FourTriadZState.from_channel_series(
            apply_matrix12(self.matrix, state.channels_at(index))
            for index in range(state.coefficient_count)
        )

    def reconstruct(self, coupled: FourTriadZState) -> FourTriadZState:
        if type(coupled) is not FourTriadZState:
            raise TypeError("coupled must be exactly FourTriadZState")
        inverse = transpose12(self.matrix)
        return FourTriadZState.from_channel_series(
            apply_matrix12(inverse, coupled.channels_at(index))
            for index in range(coupled.coefficient_count)
        )


@dataclass(frozen=True)
class CenterSummary3WithResidual:
    center: FiniteZTriad
    residuals: tuple[FiniteZTriad, ...]

    def __post_init__(self) -> None:
        if type(self.center) is not FiniteZTriad:
            raise TypeError("center must be exactly FiniteZTriad")
        if type(self.residuals) is not tuple or len(self.residuals) != 3:
            raise ValueError("residuals must contain exactly three FiniteZTriad values")
        if any(type(residual) is not FiniteZTriad for residual in self.residuals):
            raise TypeError("residuals must contain exactly FiniteZTriad values")
        expected = len(self.center.samples)
        if any(len(residual.samples) != expected for residual in self.residuals):
            raise ValueError("center and residuals must have equal coefficient lengths")

    @classmethod
    def decompose(cls, state: FourTriadZState) -> "CenterSummary3WithResidual":
        if type(state) is not FourTriadZState:
            raise TypeError("state must be exactly FourTriadZState")

        center_samples: list[Triad3] = []
        residual_samples: list[list[Triad3]] = [[], [], []]

        for index in range(state.coefficient_count):
            triad_values = [
                state.triads[group].samples[index].as_tuple()
                for group in range(4)
            ]
            center_values = tuple(
                sum(triad_values[group][channel] for group in range(4)) / 4
                for channel in range(3)
            )
            center_sample = Triad3(*center_values)
            center_samples.append(center_sample)

            for group in range(3):
                residual_samples[group].append(
                    Triad3(
                        *(
                            triad_values[group][channel] - center_values[channel]
                            for channel in range(3)
                        )
                    )
                )

        return cls(
            center=FiniteZTriad.from_samples(center_samples),
            residuals=tuple(
                FiniteZTriad.from_samples(samples)
                for samples in residual_samples
            ),
        )

    def reconstruct(self) -> FourTriadZState:
        grouped: list[list[Triad3]] = [[], [], [], []]
        for index, center_sample in enumerate(self.center.samples):
            center_values = center_sample.as_tuple()
            residual_values = [
                residual.samples[index].as_tuple()
                for residual in self.residuals
            ]

            for group in range(3):
                grouped[group].append(
                    Triad3(
                        *(
                            center_values[channel] + residual_values[group][channel]
                            for channel in range(3)
                        )
                    )
                )

            grouped[3].append(
                Triad3(
                    *(
                        center_values[channel]
                        - sum(residual_values[group][channel] for group in range(3))
                        for channel in range(3)
                    )
                )
            )

        return FourTriadZState(
            tuple(
                FiniteZTriad.from_samples(samples)
                for samples in grouped
            )
        )
