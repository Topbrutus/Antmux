from __future__ import annotations

import hashlib
import os
import re
from collections import Counter, deque
from typing import Any

SCHEMA = "BRUTUS_T12_CANDIDATE_V1"
RECENT_LIMIT = 37

_FULL_RE = re.compile(r"^BUDGET_FULL_(\d+)$")
_PARTIAL_RE = re.compile(r"^BUDGET_PARTIAL_(\d+)_OF_(\d+)$")
_ZERO_RE = re.compile(r"^BUDGET_ZERO_OF_(\d+)$")


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "1" if default else "0").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _candidate_id(formula_id: str, source_value: Any, out_value: Any) -> str:
    raw = f"{formula_id}\0{source_value}\0{out_value}".encode("utf-8")
    return "CAND-" + hashlib.sha256(raw).hexdigest()[:32]


def _source_key(formula_id: str, source_value: Any) -> str:
    raw = f"{formula_id}\0{source_value}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:32]


def _parse_t11(outcome: str) -> tuple[str, int, int] | None:
    value = str(outcome).upper()
    m = _FULL_RE.match(value)
    if m:
        n = int(m.group(1))
        return "FULL", n, n
    m = _PARTIAL_RE.match(value)
    if m:
        advised = int(m.group(1))
        requested = int(m.group(2))
        if advised > requested:
            return None
        return "PARTIAL", requested, advised
    m = _ZERO_RE.match(value)
    if m:
        requested = int(m.group(1))
        return "ZERO", requested, 0
    return None


class T12CandidateTelemetry:
    """Shadow-only pre-score candidate record downstream of T11.

    The original Colonne 37 prototype places T12 Candidate immediately before
    L1 Crystal Score and represented it only as ``candidate: true``. No official
    T12 score, threshold, proof rule, or scientific qualification rule is
    defined by the inspected source material.

    T12 v1 therefore does one conservative thing: when T11 emits a recognized
    budget advisory, it records a deterministic technical candidate identity
    plus the T11 budget context. It does not rank, score, threshold, validate,
    promote, canonize, route, schedule, reserve resources, or execute replay.

    A zero-budget advisory is still recorded as a candidate because Budget is
    not a scientific rejection rule; the record merely carries class ZERO into
    L1. Unknown or upstream-blocked T11 outcomes are not materialized as T12
    candidates and are counted separately.
    """

    def __init__(self) -> None:
        self.enabled = _env_flag("BROTO_T12_ENABLED", False)
        self.observations = 0
        self.candidate_records = 0
        self.blocked_t11_other = 0
        self.unique_candidate_ids: set[str] = set()
        self.budget_classes: Counter[str] = Counter()
        self.by_formula: dict[str, Counter[str]] = {}
        self._recent: deque[dict[str, Any]] = deque(maxlen=RECENT_LIMIT)

    def _record_formula(self, formula_id: str, outcome: str) -> None:
        self.by_formula.setdefault(formula_id, Counter())[outcome] += 1

    def observe(
        self,
        formula_id: str,
        source: Any,
        out: Any,
        t11_outcome: str,
    ) -> str:
        if not self.enabled:
            return "DISABLED"

        self.observations += 1
        parsed = _parse_t11(t11_outcome)
        if parsed is None:
            self.blocked_t11_other += 1
            outcome = "BLOCKED_T11_OTHER"
            self._record_formula(formula_id, outcome)
            self._recent.append({
                "formula_id": formula_id,
                "source_key": _source_key(formula_id, source.value),
                "t11_outcome": str(t11_outcome).upper(),
                "outcome": outcome,
                "candidate_recorded": False,
            })
            return outcome

        budget_class, requested, advised = parsed
        candidate_id = _candidate_id(formula_id, source.value, out.value)
        is_new = candidate_id not in self.unique_candidate_ids
        self.unique_candidate_ids.add(candidate_id)
        self.candidate_records += 1
        self.budget_classes[budget_class] += 1

        if budget_class == "FULL":
            outcome = "CANDIDATE_RECORDED_FULL_BUDGET"
        elif budget_class == "PARTIAL":
            outcome = "CANDIDATE_RECORDED_PARTIAL_BUDGET"
        else:
            outcome = "CANDIDATE_RECORDED_ZERO_BUDGET"

        self._record_formula(formula_id, outcome)
        self._recent.append({
            "formula_id": formula_id,
            "source_key": _source_key(formula_id, source.value),
            "candidate_id": candidate_id,
            "candidate_id_new": is_new,
            "t11_outcome": str(t11_outcome).upper(),
            "outcome": outcome,
            "budget_class": budget_class,
            "requested_replays": requested,
            "advised_replays": advised,
            "candidate_recorded": True,
        })
        return outcome

    def status(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "mode": SCHEMA,
            "enabled": self.enabled,
            "authority": "SHADOW_ONLY",
            "source_of_truth": "T11_BUDGET_OUTCOME_CALLBACK",
            "candidate_definition": "TECHNICAL_PRE_SCORE_RECORD",
            "observations": self.observations,
            "candidate_records": self.candidate_records,
            "unique_candidate_ids": len(self.unique_candidate_ids),
            "blocked_t11_other": self.blocked_t11_other,
            "budget_classes": dict(sorted(self.budget_classes.items())),
            "by_formula": {k: dict(v) for k, v in sorted(self.by_formula.items())},
            "recent_limit": RECENT_LIMIT,
            "recent": list(self._recent),
            "candidate_key_scope": "FORMULA_SOURCE_OUTPUT_ONLY",
            "candidate_key_is_c2_fingerprint": False,
            "candidate_key_is_scientific_identity": False,
            "records_zero_budget_candidates": True,
            "l1_crystal_score_input": True,
            "assigns_score": False,
            "applies_threshold": False,
            "scientific_candidate_claim": False,
            "scientific_proof_claim": False,
            "validation_state_mutated": False,
            "canonizes": False,
            "promotes_proof": False,
            "controls_routing": False,
            "controls_scheduling": False,
            "controls_calculation": False,
            "reserves_resources": False,
            "executes_replay": False,
            "schedules_replay": False,
            "compute_skips": 0,
            "value_mutated": False,
            "proof_promotion": False,
        }
