from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any

from .daat_gate import DaatGateFrame
from .stereo_source import StereoZSourceFrame

DAAT_EVIDENCE_SCHEMA = "ANTMUX-X72-DAAT-EVIDENCE-v0.1"
DAAT_EVIDENCE_STATUS = "CANDIDATE"
DAAT_EVIDENCE_AUTHORITY = "OBSERVATION_ONLY"

CRITERIA = (
    "same_source",
    "same_tick",
    "opposite_theta",
    "left_right_reconstructable",
    "energy_identity",
    "gate_verified",
)


def _canonical_hash(payload: Any) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class BetaEvidence:
    alpha: int = 1
    beta: int = 1

    def update(self, passed: bool) -> "BetaEvidence":
        return BetaEvidence(
            alpha=self.alpha + int(bool(passed)),
            beta=self.beta + int(not bool(passed)),
        )

    @property
    def mean(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    @property
    def observations(self) -> int:
        return self.alpha + self.beta - 2

    def to_dict(self) -> dict[str, Any]:
        return {
            "alpha": self.alpha,
            "beta": self.beta,
            "observations": self.observations,
            "posterior_mean": self.mean,
        }
class DaatEvidenceTracker:
    """Bayesian-style software evidence ledger for the Da'at candidate.

    This tracks repeatability of explicit invariants. It is not evidence for
    metaphysical, physical, or neurological claims.
    """

    def __init__(self) -> None:
        self._criteria = {name: BetaEvidence() for name in CRITERIA}
        self.samples = 0
        self.last_tick: int | None = None
        self.last_generation: int | None = None
        self.last_evidence_h256: str | None = None

    def observe(
        self,
        *,
        stereo: StereoZSourceFrame,
        daat: DaatGateFrame,
        tick: int,
    ) -> None:
        if type(stereo) is not StereoZSourceFrame:
            raise TypeError("stereo must be exactly StereoZSourceFrame")
        if type(daat) is not DaatGateFrame:
            raise TypeError("daat must be exactly DaatGateFrame")

        energy_scale = max(
            1.0,
            abs(daat.pair_energy),
            abs(daat.decomposed_energy),
        )
        outcomes = {
            "same_source": daat.source_h256 == stereo.source_h256,
            "same_tick": daat.tick == tick,
            "opposite_theta": math.isclose(
                stereo.left_theta,
                -stereo.right_theta,
                rel_tol=0.0,
                abs_tol=1e-15,
            ),
            "left_right_reconstructable": bool(
                daat.to_dict()["invariants"]["lossless_left_right_reconstruction"]
            ),
            "energy_identity": (
                abs(daat.pair_energy - daat.decomposed_energy)
                <= 1e-12 * energy_scale
            ),
            "gate_verified": daat.verify(),
        }

        for name, passed in outcomes.items():
            self._criteria[name] = self._criteria[name].update(passed)

        self.samples += 1
        self.last_tick = daat.tick
        self.last_generation = daat.generation
        self.last_evidence_h256 = _canonical_hash(
            {
                "schema": DAAT_EVIDENCE_SCHEMA,
                "samples": self.samples,
                "tick": self.last_tick,
                "generation": self.last_generation,
                "outcomes": outcomes,
                "criteria": {
                    name: item.to_dict()
                    for name, item in self._criteria.items()
                },
            }
        )

    def visual_state(self) -> dict[str, Any]:
        criteria = {
            name: evidence.to_dict()
            for name, evidence in self._criteria.items()
        }
        floor = min(
            (item["posterior_mean"] for item in criteria.values()),
            default=0.5,
        )
        return {
            "schema": DAAT_EVIDENCE_SCHEMA,
            "status": DAAT_EVIDENCE_STATUS,
            "authority": DAAT_EVIDENCE_AUTHORITY,
            "mutates_queen": False,
            "physical_claim": False,
            "semantic_scope": "SOFTWARE_INVARIANT_REPEATABILITY_ONLY",
            "prior": "BETA_1_1_PER_CRITERION",
            "samples": self.samples,
            "last_tick": self.last_tick,
            "last_generation": self.last_generation,
            "criteria": criteria,
            "confidence_floor": floor,
            "evidence_h256": self.last_evidence_h256,
        }

    def whole_projection(self) -> dict[str, Any]:
        return {
            "schema": DAAT_EVIDENCE_SCHEMA,
            "samples": self.samples,
        }

    def to_checkpoint(self) -> dict[str, Any]:
        return {
            "schema": DAAT_EVIDENCE_SCHEMA,
            "samples": self.samples,
            "last_tick": self.last_tick,
            "last_generation": self.last_generation,
            "last_evidence_h256": self.last_evidence_h256,
            "criteria": {
                name: {
                    "alpha": evidence.alpha,
                    "beta": evidence.beta,
                }
                for name, evidence in self._criteria.items()
            },
        }

    @classmethod
    def from_checkpoint(cls, payload: Any) -> "DaatEvidenceTracker":
        tracker = cls()
        if not isinstance(payload, dict):
            return tracker
        if payload.get("schema") != DAAT_EVIDENCE_SCHEMA:
            return tracker

        raw_criteria = payload.get("criteria") or {}
        restored: dict[str, BetaEvidence] = {}
        for name in CRITERIA:
            raw = raw_criteria.get(name) or {}
            alpha = int(raw.get("alpha", 1))
            beta = int(raw.get("beta", 1))
            if alpha < 1 or beta < 1:
                return cls()
            restored[name] = BetaEvidence(alpha=alpha, beta=beta)

        tracker._criteria = restored
        tracker.samples = int(payload.get("samples", 0))
        tracker.last_tick = payload.get("last_tick")
        tracker.last_generation = payload.get("last_generation")
        tracker.last_evidence_h256 = payload.get("last_evidence_h256")
        return tracker
