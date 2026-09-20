from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Iterable

from .daat_gate import CHANNELS, DaatGateFrame

DAAT_LINK_SCHEMA = "ANTMUX-X72-DAAT-LINK-v0.2"
DAAT_LINK_STATUS = "CANDIDATE"
DAAT_LINK_AUTHORITY = "OBSERVATION_ONLY"


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
        raise ValueError("link values must be finite")
    return max(0.0, min(1.0, item))


def _weights(values: Iterable[float] | None) -> tuple[float, ...]:
    if values is None:
        return (1.0,) * CHANNELS
    out = tuple(_clamp01(value) for value in values)
    if len(out) != CHANNELS:
        raise ValueError(f"weights must contain exactly {CHANNELS} values")
    return out
@dataclass(frozen=True)
class DaatLinkFrame:
    tick: int
    generation: int
    source_h256: str
    common_b: tuple[float, ...]
    differential_a: tuple[float, ...]
    signal_strengths: tuple[float, ...]
    weights: tuple[float, ...]
    contributions: tuple[float, ...]
    link_score: float
    link_h256: str

    @classmethod
    def from_gate(
        cls,
        gate: DaatGateFrame,
        *,
        weights: Iterable[float] | None = None,
    ) -> "DaatLinkFrame":
        if type(gate) is not DaatGateFrame:
            raise TypeError("gate must be exactly DaatGateFrame")
        if not gate.verify():
            raise ValueError("Da'at gate must verify")

        common_b = tuple(float(value) for value in gate.center)
        differential_a = tuple(float(value) for value in gate.residual)
        link_weights = _weights(weights)

        # Candidate software normalization only:
        # the absolute common component is clipped into [0,1].
        # This is intentionally explicit and replaceable later.
        signal_strengths = tuple(
            _clamp01(abs(value))
            for value in common_b
        )
        contributions = tuple(
            signal_strengths[index] * link_weights[index]
            for index in range(CHANNELS)
        )
        complement = math.prod(
            1.0 - contribution
            for contribution in contributions
        )
        link_score = _clamp01(1.0 - complement)

        payload = {
            "schema": DAAT_LINK_SCHEMA,
            "tick": gate.tick,
            "generation": gate.generation,
            "source_h256": gate.source_h256,
            "common_b": common_b,
            "differential_a": differential_a,
            "signal_strengths": signal_strengths,
            "weights": link_weights,
            "link_score": link_score,
        }

        return cls(
            tick=gate.tick,
            generation=gate.generation,
            source_h256=gate.source_h256,
            common_b=common_b,
            differential_a=differential_a,
            signal_strengths=signal_strengths,
            weights=link_weights,
            contributions=contributions,
            link_score=link_score,
            link_h256=_canonical_hash(payload),
        )
    def verify(self, *, tolerance: float = 1e-12) -> bool:
        if len(self.common_b) != CHANNELS:
            return False
        if len(self.differential_a) != CHANNELS:
            return False
        if len(self.signal_strengths) != CHANNELS:
            return False
        if len(self.weights) != CHANNELS:
            return False
        if len(self.contributions) != CHANNELS:
            return False

        expected_signals = tuple(
            _clamp01(abs(value))
            for value in self.common_b
        )
        expected_contrib = tuple(
            expected_signals[index] * self.weights[index]
            for index in range(CHANNELS)
        )
        expected_link = _clamp01(
            1.0 - math.prod(1.0 - value for value in expected_contrib)
        )

        if any(
            abs(self.signal_strengths[index] - expected_signals[index]) > tolerance
            for index in range(CHANNELS)
        ):
            return False
        if any(
            abs(self.contributions[index] - expected_contrib[index]) > tolerance
            for index in range(CHANNELS)
        ):
            return False
        if abs(self.link_score - expected_link) > tolerance:
            return False
        if not 0.0 <= self.link_score <= 1.0:
            return False

        payload = {
            "schema": DAAT_LINK_SCHEMA,
            "tick": self.tick,
            "generation": self.generation,
            "source_h256": self.source_h256,
            "common_b": self.common_b,
            "differential_a": self.differential_a,
            "signal_strengths": self.signal_strengths,
            "weights": self.weights,
            "link_score": self.link_score,
        }
        return self.link_h256 == _canonical_hash(payload)
    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": DAAT_LINK_SCHEMA,
            "status": DAAT_LINK_STATUS,
            "authority": DAAT_LINK_AUTHORITY,
            "mutates_queen": False,
            "physical_claim": False,
            "tick": self.tick,
            "generation": self.generation,
            "source_h256": self.source_h256,
            "common_b": list(self.common_b),
            "differential_a": list(self.differential_a),
            "signal_strengths": list(self.signal_strengths),
            "weights": list(self.weights),
            "contributions": list(self.contributions),
            "link_score": self.link_score,
            "formula": "Lc = 1 - product_i(1 - s_i*w_i)",
            "normalization": "s_i = clamp(abs(B_i), 0, 1)",
            "semantic_boundary": {
                "B": "COMMON_COMPONENT_ONLY",
                "A": "LEFT_RIGHT_DIFFERENCE_ONLY",
                "Lc": "SOFTWARE_LINK_SCORE_ONLY",
                "bayes_changes_z": False,
                "bayes_changes_daat": False,
            },
            "verified": self.verify(),
            "link_h256": self.link_h256,
        }
