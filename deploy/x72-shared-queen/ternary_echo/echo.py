from __future__ import annotations

import copy
import hashlib
import json
import re
from collections import OrderedDict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

from decision_candidate import (
    CANDIDATE_SCHEMA,
    X72CandidateFrame,
    X72DecisionCandidate,
)
from observation_history import X72ObservationHistory
from trend_analyzer import (
    TREND_SCHEMA,
    X72TrendAnalyzer,
    X72TrendFrame,
)


ECHO_SCHEMA = "ANTMUX-X72-TERNARY-ECHO-FRAME-v0.1"
INTENT_SCHEMA = "ANTMUX-X72-ECHO-INTENT-v0.1"
TRITS = (-1, 0, 1)
TERNARY_MATRIX = tuple((echo, provenance) for echo in TRITS for provenance in TRITS)
ALLOWED_CONDITIONS = frozenset(
    {
        "ECHO_CONFIRMED",
        "ECHO_NEGATIVE_CONFIRMED",
        "NO_ECHO_TIMEOUT",
        "PROVENANCE_MATCH",
        "PROVENANCE_UNKNOWN",
        "PROVENANCE_MISMATCH",
        "ECHO_LATE",
        "ECHO_MISMATCH",
        "INSUFFICIENT_EVIDENCE",
    }
)
_H256_RE = re.compile(r"^[0-9a-f]{64}$")


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _strict_equal(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        if left.keys() != right.keys():
            return False
        return all(_strict_equal(left[key], right[key]) for key in left)
    if isinstance(left, (list, tuple)):
        return len(left) == len(right) and all(
            _strict_equal(a, b) for a, b in zip(left, right)
        )
    return left == right


def _validate_trit(value: Any, field: str) -> int:
    if type(value) is not int or value not in TRITS:
        raise ValueError(f"{field} must be exactly -1, 0, or +1")
    return value


def _validate_h256(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _H256_RE.fullmatch(value):
        raise ValueError(f"{field} must be 64 lowercase hexadecimal characters")
    return value


def _validate_id(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _validate_timestamp(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("observed_at_utc must be a non-empty string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("observed_at_utc must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError("observed_at_utc must include a timezone")
    parsed.astimezone(timezone.utc)
    return value


def compute_intent_h256(
    *,
    entity_id: str,
    correlation_id: str,
    origin_id: str,
    target_id: str,
    source_candidate_h256: str,
) -> str:
    body = {
        "schema": INTENT_SCHEMA,
        "entity_id": _validate_id(entity_id, "entity_id"),
        "correlation_id": _validate_id(correlation_id, "correlation_id"),
        "origin_id": _validate_id(origin_id, "origin_id"),
        "target_id": _validate_id(target_id, "target_id"),
        "source_candidate_h256": _validate_h256(
            source_candidate_h256, "source_candidate_h256"
        ),
    }
    return hashlib.sha256(_canonical_json(body)).hexdigest()


@dataclass(frozen=True)
class X72EchoIntent:
    schema: str
    entity_id: str
    correlation_id: str
    origin_id: str
    target_id: str
    intent_h256: str
    registered_at_utc: str
    source_history_h256: str
    source_trend_h256: str
    source_candidate_h256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "entity_id": self.entity_id,
            "correlation_id": self.correlation_id,
            "origin_id": self.origin_id,
            "target_id": self.target_id,
            "intent_h256": self.intent_h256,
            "registered_at_utc": self.registered_at_utc,
            "source_history_h256": self.source_history_h256,
            "source_trend_h256": self.source_trend_h256,
            "source_candidate_h256": self.source_candidate_h256,
        }


@dataclass(frozen=True)
class X72EchoFrame:
    schema: str
    entity_id: str
    correlation_id: str
    origin_id: str
    target_id: str
    intent_h256: str
    echo_state: int
    provenance_state: int
    condition: str
    observed_at_utc: str
    source_history_h256: str
    source_trend_h256: str
    source_candidate_h256: str
    evidence: Mapping[str, Any]
    echo_h256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "entity_id": self.entity_id,
            "correlation_id": self.correlation_id,
            "origin_id": self.origin_id,
            "target_id": self.target_id,
            "intent_h256": self.intent_h256,
            "echo_state": self.echo_state,
            "provenance_state": self.provenance_state,
            "condition": self.condition,
            "observed_at_utc": self.observed_at_utc,
            "source_history_h256": self.source_history_h256,
            "source_trend_h256": self.source_trend_h256,
            "source_candidate_h256": self.source_candidate_h256,
            "evidence": copy.deepcopy(dict(self.evidence)),
            "echo_h256": self.echo_h256,
        }
class X72TernaryEchoMatrix:
    """Event-driven, bounded, deterministic correlation/confirmation layer."""

    READ_ONLY = True
    NO_MUTATION_TRANSPORT = True
    NO_ACTION_EXECUTION = True
    DETERMINISTIC = True
    EVENT_DRIVEN = True
    NO_BUSY_LOOP = True

    def __init__(self, *, capacity: int = 128) -> None:
        if type(capacity) is not int or capacity < 1:
            raise ValueError("capacity must be a positive integer")
        self.capacity = capacity
        self._pending: OrderedDict[str, X72EchoIntent] = OrderedDict()
        self._resolved: OrderedDict[str, tuple[X72EchoIntent, X72EchoFrame]] = (
            OrderedDict()
        )
        self._frames: deque[X72EchoFrame] = deque(maxlen=capacity)

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    @property
    def resolved_count(self) -> int:
        return len(self._resolved)

    @property
    def frames(self) -> tuple[X72EchoFrame, ...]:
        return tuple(self._frames)

    @staticmethod
    def matrix_states() -> tuple[tuple[int, int], ...]:
        return TERNARY_MATRIX

    @staticmethod
    def _canonical_frame_h256(
        frame_dict: Mapping[str, Any],
        hash_field: str,
    ) -> str:
        body = copy.deepcopy(dict(frame_dict))
        observed = body.pop(hash_field, None)
        _validate_h256(observed, hash_field)
        expected = hashlib.sha256(_canonical_json(body)).hexdigest()
        if observed != expected:
            raise ValueError(f"{hash_field} does not match canonical frame content")
        return observed

    @classmethod
    def _validate_sources(
        cls,
        history: X72ObservationHistory,
        trend: X72TrendFrame,
        candidate: X72CandidateFrame,
    ) -> tuple[str, str, str, str]:
        if type(history) is not X72ObservationHistory:
            raise TypeError("history must be exactly X72ObservationHistory")
        if type(trend) is not X72TrendFrame:
            raise TypeError("trend must be exactly X72TrendFrame")
        if type(candidate) is not X72CandidateFrame:
            raise TypeError("candidate must be exactly X72CandidateFrame")

        if history.entity_id is None:
            raise ValueError("History entity_id is required for echo correlation")
        if trend.schema != TREND_SCHEMA:
            raise ValueError("unexpected TrendFrame schema")
        if candidate.schema != CANDIDATE_SCHEMA:
            raise ValueError("unexpected CandidateFrame schema")

        history_h256 = history.deterministic_report()["report_h256"]
        _validate_h256(history_h256, "history_h256")
        trend_h256 = cls._canonical_frame_h256(
            trend.to_dict(), "trend_h256"
        )
        candidate_h256 = cls._canonical_frame_h256(
            candidate.to_dict(), "candidate_h256"
        )

        if trend.entity_id != history.entity_id:
            raise ValueError("TrendFrame entity_id mismatch")
        if candidate.entity_id != history.entity_id:
            raise ValueError("CandidateFrame entity_id mismatch")
        if trend.source_history_h256 != history_h256:
            raise ValueError("TrendFrame source_history_h256 mismatch")
        if candidate.source_history_h256 != history_h256:
            raise ValueError("CandidateFrame source_history_h256 mismatch")
        if candidate.source_trend_h256 != trend_h256:
            raise ValueError("CandidateFrame source_trend_h256 mismatch")

        records = tuple(history.records)
        first_tick = next(
            (record.tick_count for record in records if record.tick_count is not None),
            None,
        )
        last_tick = next(
            (
                record.tick_count
                for record in reversed(records)
                if record.tick_count is not None
            ),
            None,
        )
        if trend.records_count != len(records):
            raise ValueError("TrendFrame records_count mismatch")
        if candidate.source_records_count != trend.records_count:
            raise ValueError("CandidateFrame source_records_count mismatch")
        if trend.window_start_tick != first_tick or trend.window_end_tick != last_tick:
            raise ValueError("TrendFrame tick window mismatch")
        if (
            candidate.window_start_tick != trend.window_start_tick
            or candidate.window_end_tick != trend.window_end_tick
        ):
            raise ValueError("CandidateFrame tick window mismatch")

        evidence = dict(candidate.evidence)
        if evidence.get("source_history_h256") != history_h256:
            raise ValueError("Candidate evidence history hash mismatch")
        if evidence.get("source_trend_h256") != trend_h256:
            raise ValueError("Candidate evidence trend hash mismatch")
        if evidence.get("records_count") != trend.records_count:
            raise ValueError("Candidate evidence records_count mismatch")

        return (
            history.entity_id,
            history_h256,
            trend_h256,
            candidate_h256,
        )

    @staticmethod
    def _deep_validate_sources(
        history: X72ObservationHistory,
        trend: X72TrendFrame,
        candidate: X72CandidateFrame,
    ) -> tuple[str, str, str, str]:
        expected_trend = X72TrendAnalyzer().analyze(history)
        if not _strict_equal(trend.to_dict(), expected_trend.to_dict()):
            raise ValueError("TrendFrame does not match deterministic History analysis")

        expected_candidate = X72DecisionCandidate().generate(history, trend)
        if not _strict_equal(candidate.to_dict(), expected_candidate.to_dict()):
            raise ValueError(
                "CandidateFrame does not match deterministic History/Trend analysis"
            )

        history_h256 = history.deterministic_report()["report_h256"]
        return (
            history.entity_id,
            history_h256,
            trend.trend_h256,
            candidate.candidate_h256,
        )

    def register_intent(
        self,
        *,
        history: X72ObservationHistory,
        trend: X72TrendFrame,
        candidate: X72CandidateFrame,
        correlation_id: str,
        origin_id: str,
        target_id: str,
        intent_h256: str,
        observed_at_utc: str,
    ) -> X72EchoIntent:
        entity_id, history_h256, trend_h256, candidate_h256 = self._validate_sources(
            history, trend, candidate
        )
        correlation_id = _validate_id(correlation_id, "correlation_id")
        origin_id = _validate_id(origin_id, "origin_id")
        target_id = _validate_id(target_id, "target_id")
        _validate_timestamp(observed_at_utc)
        _validate_h256(intent_h256, "intent_h256")

        expected_intent_h256 = compute_intent_h256(
            entity_id=entity_id,
            correlation_id=correlation_id,
            origin_id=origin_id,
            target_id=target_id,
            source_candidate_h256=candidate_h256,
        )
        if intent_h256 != expected_intent_h256:
            raise ValueError("intent_h256 does not match canonical intent identity")

        intent = X72EchoIntent(
            schema=INTENT_SCHEMA,
            entity_id=entity_id,
            correlation_id=correlation_id,
            origin_id=origin_id,
            target_id=target_id,
            intent_h256=intent_h256,
            registered_at_utc=observed_at_utc,
            source_history_h256=history_h256,
            source_trend_h256=trend_h256,
            source_candidate_h256=candidate_h256,
        )

        existing = self._pending.get(correlation_id)
        if existing is not None:
            if _strict_equal(existing.to_dict(), intent.to_dict()):
                return existing
            raise ValueError("correlation_id already registered with different intent")

        if correlation_id in self._resolved:
            raise ValueError("correlation_id already resolved")
        if len(self._pending) >= self.capacity:
            raise OverflowError("pending echo memory capacity reached")

        self._pending[correlation_id] = intent
        return intent
    @staticmethod
    def _provenance_state(intent: X72EchoIntent, echo_origin_id: str | None) -> int:
        if echo_origin_id is None:
            return 0
        _validate_id(echo_origin_id, "echo_origin_id")
        return 1 if echo_origin_id == intent.origin_id else -1

    @staticmethod
    def _echo_state(explicit_confirmation: bool | None) -> int:
        if explicit_confirmation is None:
            return 0
        if type(explicit_confirmation) is not bool:
            raise ValueError("explicit_confirmation must be True, False, or None")
        return 1 if explicit_confirmation else -1

    @staticmethod
    def _base_condition(
        *, echo_state: int, provenance_state: int
    ) -> str:
        _validate_trit(echo_state, "echo_state")
        _validate_trit(provenance_state, "provenance_state")
        if provenance_state == -1:
            return "ECHO_MISMATCH"
        if echo_state == 1:
            return "ECHO_CONFIRMED"
        if echo_state == -1:
            return "ECHO_NEGATIVE_CONFIRMED"
        return "INSUFFICIENT_EVIDENCE"

    @staticmethod
    def _normalize_evidence(
        evidence: Mapping[str, Any] | None,
        *,
        explicit_confirmation: bool | None,
        echo_origin_id: str | None,
        intent: X72EchoIntent,
    ) -> dict[str, Any]:
        if evidence is None:
            supplied: dict[str, Any] = {}
        elif isinstance(evidence, Mapping):
            supplied = copy.deepcopy(dict(evidence))
        else:
            raise TypeError("evidence must be a mapping or None")

        base = {
            "correlation_id": intent.correlation_id,
            "origin_id": intent.origin_id,
            "target_id": intent.target_id,
            "intent_h256": intent.intent_h256,
            "explicit_confirmation": explicit_confirmation,
            "echo_origin_id": echo_origin_id,
            "observed_evidence": supplied,
        }
        _canonical_json(base)
        return base

    @staticmethod
    def _build_frame(
        *,
        intent: X72EchoIntent,
        echo_state: int,
        provenance_state: int,
        condition: str,
        observed_at_utc: str,
        evidence: Mapping[str, Any],
    ) -> X72EchoFrame:
        echo_state = _validate_trit(echo_state, "echo_state")
        provenance_state = _validate_trit(provenance_state, "provenance_state")
        if condition not in ALLOWED_CONDITIONS:
            raise ValueError("unsupported echo condition")
        _validate_timestamp(observed_at_utc)

        evidence_dict = copy.deepcopy(dict(evidence))
        body = {
            "schema": ECHO_SCHEMA,
            "entity_id": intent.entity_id,
            "correlation_id": intent.correlation_id,
            "origin_id": intent.origin_id,
            "target_id": intent.target_id,
            "intent_h256": intent.intent_h256,
            "echo_state": echo_state,
            "provenance_state": provenance_state,
            "condition": condition,
            "observed_at_utc": observed_at_utc,
            "source_history_h256": intent.source_history_h256,
            "source_trend_h256": intent.source_trend_h256,
            "source_candidate_h256": intent.source_candidate_h256,
            "evidence": evidence_dict,
        }
        echo_h256 = hashlib.sha256(_canonical_json(body)).hexdigest()
        return X72EchoFrame(
            schema=ECHO_SCHEMA,
            entity_id=intent.entity_id,
            correlation_id=intent.correlation_id,
            origin_id=intent.origin_id,
            target_id=intent.target_id,
            intent_h256=intent.intent_h256,
            echo_state=echo_state,
            provenance_state=provenance_state,
            condition=condition,
            observed_at_utc=observed_at_utc,
            source_history_h256=intent.source_history_h256,
            source_trend_h256=intent.source_trend_h256,
            source_candidate_h256=intent.source_candidate_h256,
            evidence=MappingProxyType(evidence_dict),
            echo_h256=echo_h256,
        )

    def _remember_resolution(
        self, intent: X72EchoIntent, frame: X72EchoFrame
    ) -> None:
        if intent.correlation_id in self._resolved:
            self._resolved.pop(intent.correlation_id)
        if len(self._resolved) >= self.capacity:
            self._resolved.popitem(last=False)
        self._resolved[intent.correlation_id] = (intent, frame)
        self._frames.append(frame)

    def _recent_frame_by_hash(self, echo_h256: str) -> X72EchoFrame | None:
        for frame in self._frames:
            if frame.echo_h256 == echo_h256:
                return frame
        return None

    def observe_echo(
        self,
        *,
        correlation_id: str,
        observed_at_utc: str,
        explicit_confirmation: bool | None,
        echo_origin_id: str | None,
        evidence: Mapping[str, Any] | None = None,
    ) -> X72EchoFrame:
        correlation_id = _validate_id(correlation_id, "correlation_id")
        _validate_timestamp(observed_at_utc)

        intent = self._pending.get(correlation_id)
        prior: X72EchoFrame | None = None
        is_late = False
        if intent is None:
            resolved = self._resolved.get(correlation_id)
            if resolved is None:
                raise KeyError("unknown correlation_id")
            intent, prior = resolved
            is_late = prior.condition == "NO_ECHO_TIMEOUT"

        echo_state = self._echo_state(explicit_confirmation)
        provenance_state = self._provenance_state(intent, echo_origin_id)
        normalized_evidence = self._normalize_evidence(
            evidence,
            explicit_confirmation=explicit_confirmation,
            echo_origin_id=echo_origin_id,
            intent=intent,
        )

        if is_late:
            condition = "ECHO_LATE"
        elif prior is not None:
            if (
                prior.echo_state == echo_state
                and prior.provenance_state == provenance_state
            ):
                return prior
            condition = "ECHO_MISMATCH"
        else:
            condition = self._base_condition(
                echo_state=echo_state,
                provenance_state=provenance_state,
            )

        frame = self._build_frame(
            intent=intent,
            echo_state=echo_state,
            provenance_state=provenance_state,
            condition=condition,
            observed_at_utc=observed_at_utc,
            evidence=normalized_evidence,
        )
        duplicate = self._recent_frame_by_hash(frame.echo_h256)
        if duplicate is not None:
            return duplicate

        if correlation_id in self._pending:
            self._pending.pop(correlation_id)
            self._remember_resolution(intent, frame)
        else:
            self._frames.append(frame)
        return frame
    def expire(
        self,
        *,
        correlation_id: str,
        observed_at_utc: str,
        provenance_origin_id: str | None = None,
        evidence: Mapping[str, Any] | None = None,
    ) -> X72EchoFrame:
        correlation_id = _validate_id(correlation_id, "correlation_id")
        _validate_timestamp(observed_at_utc)

        intent = self._pending.get(correlation_id)
        if intent is None:
            resolved = self._resolved.get(correlation_id)
            if resolved is not None and resolved[1].condition == "NO_ECHO_TIMEOUT":
                return resolved[1]
            raise ValueError("correlation_id is not pending")

        provenance_state = self._provenance_state(intent, provenance_origin_id)
        normalized_evidence = self._normalize_evidence(
            evidence,
            explicit_confirmation=None,
            echo_origin_id=provenance_origin_id,
            intent=intent,
        )
        normalized_evidence["timeout"] = True

        frame = self._build_frame(
            intent=intent,
            echo_state=0,
            provenance_state=provenance_state,
            condition="NO_ECHO_TIMEOUT",
            observed_at_utc=observed_at_utc,
            evidence=normalized_evidence,
        )
        self._pending.pop(correlation_id)
        self._remember_resolution(intent, frame)
        return frame
