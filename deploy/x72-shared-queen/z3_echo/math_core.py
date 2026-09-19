from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

TRIAD_COUNT = 4
CHANNELS_PER_TRIAD = 3
PERIPHERAL_NODE_COUNT = TRIAD_COUNT * CHANNELS_PER_TRIAD
TOTAL_NODE_COUNT = 1 + PERIPHERAL_NODE_COUNT

Matrix3 = tuple[
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
]


def _finite_complex(value: complex | float | int, field: str) -> complex:
    if isinstance(value, bool) or not isinstance(value, (int, float, complex)):
        raise TypeError(f"{field} must be a real or complex number")
    out = complex(value)
    if not math.isfinite(out.real) or not math.isfinite(out.imag):
        raise ValueError(f"{field} must be finite")
    return out


@dataclass(frozen=True)
class Triad3:
    x: complex
    y: complex
    z: complex

    def __post_init__(self) -> None:
        object.__setattr__(self, "x", _finite_complex(self.x, "x"))
        object.__setattr__(self, "y", _finite_complex(self.y, "y"))
        object.__setattr__(self, "z", _finite_complex(self.z, "z"))

    def as_tuple(self) -> tuple[complex, complex, complex]:
        return (self.x, self.y, self.z)

    def norm_squared(self) -> float:
        return float(abs(self.x) ** 2 + abs(self.y) ** 2 + abs(self.z) ** 2)


@dataclass(frozen=True)
class FiniteZTriad:
    """Finite Z-domain polynomial representation of a 3-channel sample sequence."""

    samples: tuple[Triad3, ...]

    def __post_init__(self) -> None:
        if not self.samples:
            raise ValueError("samples must contain at least one triad")
        if any(type(item) is not Triad3 for item in self.samples):
            raise TypeError("samples must contain exactly Triad3 values")

    @classmethod
    def from_samples(cls, samples: Iterable[Triad3]) -> "FiniteZTriad":
        return cls(tuple(samples))

    def evaluate(self, z: complex | float | int) -> Triad3:
        point = _finite_complex(z, "z")
        if point == 0:
            raise ValueError("z must be non-zero for finite Z-transform evaluation")

        sx = 0j
        sy = 0j
        sz = 0j
        for n, sample in enumerate(self.samples):
            factor = point ** (-n)
            sx += sample.x * factor
            sy += sample.y * factor
            sz += sample.z * factor
        return Triad3(sx, sy, sz)

    def inverse_coefficients(self) -> tuple[Triad3, ...]:
        """Return the exact coefficient/sample sequence represented by this polynomial."""
        return self.samples


def _identity3() -> Matrix3:
    return (
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
    )


def rotation_z(theta: float) -> Matrix3:
    c = math.cos(theta)
    s = math.sin(theta)
    return (
        (c, -s, 0.0),
        (s, c, 0.0),
        (0.0, 0.0, 1.0),
    )


def rotation_y(theta: float) -> Matrix3:
    c = math.cos(theta)
    s = math.sin(theta)
    return (
        (c, 0.0, s),
        (0.0, 1.0, 0.0),
        (-s, 0.0, c),
    )


def matmul3(left: Matrix3, right: Matrix3) -> Matrix3:
    return tuple(
        tuple(
            sum(left[row][k] * right[k][col] for k in range(3))
            for col in range(3)
        )
        for row in range(3)
    )  # type: ignore[return-value]


def transpose3(matrix: Matrix3) -> Matrix3:
    return tuple(
        tuple(matrix[col][row] for col in range(3))
        for row in range(3)
    )  # type: ignore[return-value]


def apply_matrix3(matrix: Matrix3, triad: Triad3) -> Triad3:
    values = triad.as_tuple()
    out = tuple(
        sum(matrix[row][col] * values[col] for col in range(3))
        for row in range(3)
    )
    return Triad3(*out)


def euler_zyz(alpha: float, beta: float, gamma: float) -> Matrix3:
    """Rz(alpha) @ Ry(beta) @ Rz(gamma). Order is intentional."""
    return matmul3(matmul3(rotation_z(alpha), rotation_y(beta)), rotation_z(gamma))


def determinant3(matrix: Matrix3) -> float:
    a, b, c = matrix[0]
    d, e, f = matrix[1]
    g, h, i = matrix[2]
    return (
        a * (e * i - f * h)
        - b * (d * i - f * g)
        + c * (d * h - e * g)
    )


def orthogonality_error(matrix: Matrix3) -> float:
    product = matmul3(transpose3(matrix), matrix)
    identity = _identity3()
    return max(
        abs(product[row][col] - identity[row][col])
        for row in range(3)
        for col in range(3)
    )


def beta_y_to_zero_z(triad: Triad3) -> float:
    """Return a Y-axis rotation angle that drives z' to zero for a real triad."""
    if any(abs(value.imag) > 0.0 for value in triad.as_tuple()):
        raise ValueError("beta_y_to_zero_z requires a real-valued triad")
    x = triad.x.real
    z = triad.z.real
    if x == 0.0 and z == 0.0:
        return 0.0
    return math.atan2(z, x)


def is_rotation_matrix(matrix: Matrix3, *, tolerance: float = 1e-12) -> bool:
    return (
        orthogonality_error(matrix) <= tolerance
        and abs(determinant3(matrix) - 1.0) <= tolerance
    )
