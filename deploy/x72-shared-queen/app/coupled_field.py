from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any

from .daat_gate import CHANNELS
from .oscillator_modes import BoundedOscillatorFrame

COUPLED_FIELD_SCHEMA = "ANTMUX-X72-COUPLED-FIELD-v0.1"
COUPLED_FIELD_STATUS = "CANDIDATE"
COUPLED_FIELD_AUTHORITY = "OBSERVATION_ONLY"
DEFAULT_COUPLING = 0.125


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
        raise ValueError(f"{field} must contain exactly {CHANNELS} values")
    out = tuple(float(value) for value in values)
    if any(not math.isfinite(value) for value in out):
        raise ValueError(f"{field} must stay finite")
    return out


def _energy(x: tuple[float, ...], y: tuple[float, ...]) -> float:
    return math.fsum(
        x[index] * x[index] + y[index] * y[index]
        for index in range(CHANNELS)
    )
def _propagate(
    values: tuple[float, ...],
    coupling: float,
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    flux = tuple(
        coupling * (values[index] - values[(index + 1) % CHANNELS])
        for index in range(CHANNELS)
    )
    updated = tuple(
        values[index]
        - flux[index]
        + flux[(index - 1) % CHANNELS]
        for index in range(CHANNELS)
    )
    return flux, updated


@dataclass(frozen=True)
class CoupledFieldFrame:
    tick: int
    generation: int
    source_h256: str
    coupling: float
    x_before: tuple[float, ...]
    y_before: tuple[float, ...]
    flux_x: tuple[float, ...]
    flux_y: tuple[float, ...]
    x_after: tuple[float, ...]
    y_after: tuple[float, ...]
    x_sum_before: float
    x_sum_after: float
    y_sum_before: float
    y_sum_after: float
    energy_before: float
    energy_after: float
    field_h256: str

    @classmethod
    def from_oscillator(
        cls,
        oscillator: BoundedOscillatorFrame,
        *,
        coupling: float = DEFAULT_COUPLING,
    ) -> "CoupledFieldFrame":
        if type(oscillator) is not BoundedOscillatorFrame:
            raise TypeError("oscillator must be exactly BoundedOscillatorFrame")
        if not oscillator.verify():
            raise ValueError("oscillator frame must verify")

        kappa = float(coupling)
        if not math.isfinite(kappa) or not 0.0 <= kappa <= 0.5:
            raise ValueError("coupling must be finite and inside [0,0.5]")

        x_before = _finite_tuple(
            tuple(mode.x for mode in oscillator.modes),
            "x_before",
        )
        y_before = _finite_tuple(
            tuple(mode.y for mode in oscillator.modes),
            "y_before",
        )

        flux_x, x_after = _propagate(x_before, kappa)
        flux_y, y_after = _propagate(y_before, kappa)

        x_sum_before = math.fsum(x_before)
        x_sum_after = math.fsum(x_after)
        y_sum_before = math.fsum(y_before)
        y_sum_after = math.fsum(y_after)
        energy_before = _energy(x_before, y_before)
        energy_after = _energy(x_after, y_after)

        payload = {
            "schema": COUPLED_FIELD_SCHEMA,
            "tick": oscillator.tick,
            "generation": oscillator.generation,
            "source_h256": oscillator.source_h256,
            "coupling": kappa,
            "x_before": x_before,
            "y_before": y_before,
            "flux_x": flux_x,
            "flux_y": flux_y,
            "x_after": x_after,
            "y_after": y_after,
        }

        return cls(
            tick=oscillator.tick,
            generation=oscillator.generation,
            source_h256=oscillator.source_h256,
            coupling=kappa,
            x_before=x_before,
            y_before=y_before,
            flux_x=flux_x,
            flux_y=flux_y,
            x_after=x_after,
            y_after=y_after,
            x_sum_before=x_sum_before,
            x_sum_after=x_sum_after,
            y_sum_before=y_sum_before,
            y_sum_after=y_sum_after,
            energy_before=energy_before,
            energy_after=energy_after,
            field_h256=_canonical_hash(payload),
        )
    def verify(self, *, tolerance: float = 1e-12) -> bool:
        if not 0.0 <= self.coupling <= 0.5:
            return False
        expected_flux_x, expected_x_after = _propagate(
            self.x_before,
            self.coupling,
        )
        expected_flux_y, expected_y_after = _propagate(
            self.y_before,
            self.coupling,
        )

        def close(a: float, b: float) -> bool:
            return abs(a - b) <= tolerance * max(1.0, abs(a), abs(b))

        if any(
            not close(self.flux_x[i], expected_flux_x[i])
            or not close(self.flux_y[i], expected_flux_y[i])
            or not close(self.x_after[i], expected_x_after[i])
            or not close(self.y_after[i], expected_y_after[i])
            for i in range(CHANNELS)
        ):
            return False

        if not close(self.x_sum_before, math.fsum(self.x_before)):
            return False
        if not close(self.x_sum_after, math.fsum(self.x_after)):
            return False
        if not close(self.y_sum_before, math.fsum(self.y_before)):
            return False
        if not close(self.y_sum_after, math.fsum(self.y_after)):
            return False

        if not close(self.x_sum_before, self.x_sum_after):
            return False
        if not close(self.y_sum_before, self.y_sum_after):
            return False

        expected_energy_before = _energy(self.x_before, self.y_before)
        expected_energy_after = _energy(self.x_after, self.y_after)
        if not close(self.energy_before, expected_energy_before):
            return False
        if not close(self.energy_after, expected_energy_after):
            return False
        if self.energy_after > self.energy_before + tolerance * max(
            1.0,
            abs(self.energy_before),
        ):
            return False

        payload = {
            "schema": COUPLED_FIELD_SCHEMA,
            "tick": self.tick,
            "generation": self.generation,
            "source_h256": self.source_h256,
            "coupling": self.coupling,
            "x_before": self.x_before,
            "y_before": self.y_before,
            "flux_x": self.flux_x,
            "flux_y": self.flux_y,
            "x_after": self.x_after,
            "y_after": self.y_after,
        }
        return self.field_h256 == _canonical_hash(payload)
    def to_dict(self) -> dict[str, Any]:
        x_span_before = max(self.x_before) - min(self.x_before)
        x_span_after = max(self.x_after) - min(self.x_after)
        y_span_before = max(self.y_before) - min(self.y_before)
        y_span_after = max(self.y_after) - min(self.y_after)
        dissipation = self.energy_before - self.energy_after

        return {
            "schema": COUPLED_FIELD_SCHEMA,
            "status": COUPLED_FIELD_STATUS,
            "authority": COUPLED_FIELD_AUTHORITY,
            "mutates_queen": False,
            "physical_claim": False,
            "electromagnetic_claim": False,
            "tick": self.tick,
            "generation": self.generation,
            "source_h256": self.source_h256,
            "coupling": self.coupling,
            "topology": "INDEX_RING_ONLY_NO_SPATIAL_MEANING",
            "causal_update": "READ_ALL_THEN_WRITE_ALL",
            "field_components": ["OSCILLATOR_X", "OSCILLATOR_Y"],
            "x_before": list(self.x_before),
            "y_before": list(self.y_before),
            "flux_x": list(self.flux_x),
            "flux_y": list(self.flux_y),
            "x_after": list(self.x_after),
            "y_after": list(self.y_after),
            "accounting": {
                "x_sum_before": self.x_sum_before,
                "x_sum_after": self.x_sum_after,
                "x_sum_error": self.x_sum_after - self.x_sum_before,
                "y_sum_before": self.y_sum_before,
                "y_sum_after": self.y_sum_after,
                "y_sum_error": self.y_sum_after - self.y_sum_before,
                "software_energy_before": self.energy_before,
                "software_energy_after": self.energy_after,
                "software_dissipation": dissipation,
                "no_software_energy_creation": (
                    self.energy_after <= self.energy_before + 1e-12
                    * max(1.0, abs(self.energy_before))
                ),
            },
            "contraction": {
                "x_span_before": x_span_before,
                "x_span_after": x_span_after,
                "y_span_before": y_span_before,
                "y_span_after": y_span_after,
                "x_nonexpanding": x_span_after <= x_span_before + 1e-12,
                "y_nonexpanding": y_span_after <= y_span_before + 1e-12,
            },
            "unmapped": [
                "ELECTRIC_FIELD",
                "MAGNETIC_FIELD",
                "PHYSICAL_ENERGY",
                "SPATIAL_GEOMETRY",
                "VERTICAL_AXIS",
                "DEPTH_AXIS",
            ],
            "verified": self.verify(),
            "field_h256": self.field_h256,
        }
