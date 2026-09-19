from __future__ import annotations

from dataclasses import dataclass

from .math_core import (
    FiniteZTriad,
    Matrix3,
    Triad3,
    apply_matrix3,
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


def _scale_triad(triad: Triad3, gain: complex) -> Triad3:
    return Triad3(triad.x * gain, triad.y * gain, triad.z * gain)


def _zero_triad() -> Triad3:
    return Triad3(0.0, 0.0, 0.0)


@dataclass(frozen=True)
class Z3EchoTransfer:
    """Reversible transformed-domain echo transfer when gain is non-zero."""

    gain: complex
    delay: int
    rotation: Matrix3

    def __post_init__(self) -> None:
        object.__setattr__(self, "gain", _finite_gain(self.gain))
        if type(self.delay) is not int or self.delay < 0:
            raise ValueError("delay must be a non-negative integer")
        if not is_rotation_matrix(self.rotation, tolerance=1e-10):
            raise ValueError("rotation must be a proper 3D rotation matrix")

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
        inverse_gain = 1 / self.gain
        restored = tuple(
            apply_matrix3(inverse_rotation, _scale_triad(sample, inverse_gain))
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
