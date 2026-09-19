from __future__ import annotations

import math
from dataclasses import dataclass

from .math_core import (
    FiniteZTriad,
    Matrix3,
    Triad3,
    apply_matrix3,
    canonical_real_matrix3,
    is_rotation_matrix,
    transpose3,
)


def _finite_gain(value: complex | float | int) -> complex:
    if isinstance(value, bool) or not isinstance(value, (int, float, complex)):
        raise TypeError("gain must be a real or complex number")
    out = complex(value)
    if not (out.real == out.real and out.imag == out.imag):
        raise ValueError("gain must be finite")
    if out.real in (float("inf"), float("-inf")):
        raise ValueError("gain must be finite")
    if out.imag in (float("inf"), float("-inf")):
        raise ValueError("gain must be finite")
    return out


def _robust_complex_multiply(left: complex, right: complex) -> complex:
    """Multiply finite complex values using power-of-two scaling."""
    if left == 0 or right == 0:
        return 0j

    a = left.real
    b = left.imag
    c = right.real
    d = right.imag

    left_exp = max(
        math.frexp(abs(a))[1] if a != 0 else -1074,
        math.frexp(abs(b))[1] if b != 0 else -1074,
    )
    right_exp = max(
        math.frexp(abs(c))[1] if c != 0 else -1074,
        math.frexp(abs(d))[1] if d != 0 else -1074,
    )

    a_scaled = math.ldexp(a, -left_exp)
    b_scaled = math.ldexp(b, -left_exp)
    c_scaled = math.ldexp(c, -right_exp)
    d_scaled = math.ldexp(d, -right_exp)

    real_scaled = a_scaled * c_scaled - b_scaled * d_scaled
    imag_scaled = a_scaled * d_scaled + b_scaled * c_scaled
    exponent_total = left_exp + right_exp

    try:
        real = math.ldexp(real_scaled, exponent_total)
        imag = math.ldexp(imag_scaled, exponent_total)
    except OverflowError as exc:
        raise ArithmeticError("complex multiplication overflowed binary64 range") from exc

    if not math.isfinite(real) or not math.isfinite(imag):
        raise ArithmeticError("complex multiplication produced a non-finite result")
    return complex(real, imag)


def _robust_complex_divide(numerator: complex, denominator: complex) -> complex:
    """Divide finite complex values using power-of-two scaling."""
    if denominator == 0:
        raise ZeroDivisionError("complex division by zero")
    if numerator == 0:
        return 0j

    a = numerator.real
    b = numerator.imag
    c = denominator.real
    d = denominator.imag

    num_exp = max(
        math.frexp(abs(a))[1] if a != 0 else -1074,
        math.frexp(abs(b))[1] if b != 0 else -1074,
    )
    den_exp = max(
        math.frexp(abs(c))[1] if c != 0 else -1074,
        math.frexp(abs(d))[1] if d != 0 else -1074,
    )

    a_scaled = math.ldexp(a, -num_exp)
    b_scaled = math.ldexp(b, -num_exp)
    c_scaled = math.ldexp(c, -den_exp)
    d_scaled = math.ldexp(d, -den_exp)

    denominator_scaled = c_scaled * c_scaled + d_scaled * d_scaled
    real_scaled = (
        a_scaled * c_scaled + b_scaled * d_scaled
    ) / denominator_scaled
    imag_scaled = (
        b_scaled * c_scaled - a_scaled * d_scaled
    ) / denominator_scaled

    exponent_delta = num_exp - den_exp
    try:
        real = math.ldexp(real_scaled, exponent_delta)
        imag = math.ldexp(imag_scaled, exponent_delta)
    except OverflowError as exc:
        raise ArithmeticError("complex division overflowed binary64 range") from exc

    if not math.isfinite(real) or not math.isfinite(imag):
        raise ArithmeticError("complex division produced a non-finite result")
    return complex(real, imag)


def _numerically_close_complex(
    observed: complex,
    expected: complex,
    *,
    relative_tolerance: float = 1e-12,
) -> bool:
    if observed == expected:
        return True
    scale = max(abs(expected.real), abs(expected.imag))
    if scale == 0:
        return observed == 0
    tolerance = relative_tolerance * scale
    return (
        abs(observed.real - expected.real) <= tolerance
        and abs(observed.imag - expected.imag) <= tolerance
    )


def _scale_component(value: complex, gain: complex) -> complex:
    scaled = _robust_complex_multiply(value, gain)
    if value != 0 and gain != 0:
        recovered = _robust_complex_divide(scaled, gain)
        if not _numerically_close_complex(recovered, value):
            raise ArithmeticError(
                "gain scaling is not numerically reversible within tolerance"
            )
    return scaled


def _scale_triad(triad: Triad3, gain: complex) -> Triad3:
    return Triad3(
        _scale_component(triad.x, gain),
        _scale_component(triad.y, gain),
        _scale_component(triad.z, gain),
    )


def _divide_triad(triad: Triad3, gain: complex) -> Triad3:
    return Triad3(
        _robust_complex_divide(triad.x, gain),
        _robust_complex_divide(triad.y, gain),
        _robust_complex_divide(triad.z, gain),
    )


def _zero_triad() -> Triad3:
    return Triad3(0.0, 0.0, 0.0)


@dataclass(frozen=True)
class Z3EchoTransfer:
    """Algebraically reversible transformed-domain transfer when gain is non-zero."""

    gain: complex
    delay: int
    rotation: Matrix3

    def __post_init__(self) -> None:
        object.__setattr__(self, "gain", _finite_gain(self.gain))
        if type(self.delay) is not int or self.delay < 0:
            raise ValueError("delay must be a non-negative integer")
        try:
            rotation = canonical_real_matrix3(self.rotation)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "rotation must be an immutable-compatible finite real 3x3 matrix"
            ) from exc
        if not is_rotation_matrix(rotation, tolerance=1e-10):
            raise ValueError("rotation must be a proper real 3D rotation matrix")
        object.__setattr__(self, "rotation", rotation)

    @property
    def reversible(self) -> bool:
        return self.gain != 0

    def apply(self, source: FiniteZTriad) -> FiniteZTriad:
        if type(source) is not FiniteZTriad:
            raise TypeError("source must be exactly FiniteZTriad")

        transformed = tuple(
            _scale_triad(apply_matrix3(self.rotation, sample), self.gain)
            for sample in source.samples
        )
        delayed = (_zero_triad(),) * self.delay + transformed
        return FiniteZTriad(delayed)

    def reconstruct(
        self,
        echoed: FiniteZTriad,
        *,
        zero_tolerance: float = 1e-12,
    ) -> FiniteZTriad:
        if type(echoed) is not FiniteZTriad:
            raise TypeError("echoed must be exactly FiniteZTriad")
        if self.gain == 0:
            raise ValueError("zero gain is non-invertible")
        if self.delay >= len(echoed.samples):
            raise ValueError("echoed sequence is shorter than the configured delay")

        prefix = echoed.samples[: self.delay]
        if any(
            abs(value) > zero_tolerance
            for sample in prefix
            for value in sample.as_tuple()
        ):
            raise ValueError("echoed sequence does not contain the expected delay prefix")

        inverse_rotation = transpose3(self.rotation)
        restored = tuple(
            apply_matrix3(inverse_rotation, _divide_triad(sample, self.gain))
            for sample in echoed.samples[self.delay :]
        )
        return FiniteZTriad(restored)


def apply_echo_transfer(
    source: FiniteZTriad,
    *,
    gain: complex | float | int,
    delay: int,
    rotation: Matrix3,
) -> FiniteZTriad:
    return Z3EchoTransfer(gain=gain, delay=delay, rotation=rotation).apply(source)
