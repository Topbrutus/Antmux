from __future__ import annotations

import hashlib
import json
from collections import deque
from dataclasses import asdict, dataclass
from typing import Any, Iterable

from observation_adapter import ObservationEnvelope

HISTORY_SCHEMA = "ANTMUX-X72-OBSERVATION-HISTORY-v0.1"
HISTORY_REPORT_SCHEMA = "ANTMUX-X72-OBSERVATION-HISTORY-REPORT-v0.1"
ALLOWED_STATUS = frozenset({"FRESH", "STALE", "UNKNOWN"})
STATE_ENDPOINTS = frozenset({"/api/state", "/ws"})

def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _payload_h256(payload: dict[str, Any] | None) -> str | None:
    if payload is None:
        return None
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


def _optional_int(value: Any, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} must be an integer")
    if value < 0:
        raise ValueError(f"{field} must be >= 0")
    return value

def _optional_float(value: Any, field: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be numeric")
    return float(value)


@dataclass(frozen=True)
class X72HistoryRecord:
    sequence_id: int
    observed_at: str
    entity_id: str | None
    tick_count: int | None
    source_schema: str
    source_endpoint: str
    status: str
    condition: str
    queen_mode: str | None
    integrity_match: bool | None
    protected_h256: str | None
    reference_h256: str | None
    payload_h256: str | None
    r_exec: float | None
    f_rt: float | None

    active_synapses: int | None
    event_count: int | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def semantic_dict(self) -> dict[str, Any]:
        data = self.to_dict()
        data.pop("sequence_id")
        data.pop("observed_at")
        return data


@dataclass(frozen=True)
class HistoryAppendResult:
    accepted: bool
    duplicate: bool
    condition: str
    record: X72HistoryRecord | None
    error: str | None = None
    evicted_sequence_id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        if self.record is not None:
            result["record"] = self.record.to_dict()

        return result


def deterministic_history_report(
    records: Iterable[X72HistoryRecord],
) -> dict[str, Any]:
    stable_records = [record.semantic_dict() for record in records]
    stable_records.sort(key=lambda item: _canonical_json(item))
    entity_ids = sorted(
        {
            str(item["entity_id"])
            for item in stable_records
            if item.get("entity_id") is not None
        }
    )
    body = {
        "schema": HISTORY_REPORT_SCHEMA,
        "entity_ids": entity_ids,
        "record_count": len(stable_records),
        "records": stable_records,
    }
    return {
        **body,
        "report_h256": hashlib.sha256(_canonical_json(body)).hexdigest(),
    }

class X72ObservationHistory:
    """Bounded, deterministic, read-only history of validated observations."""

    READ_ONLY = True
    NO_MUTATION_TRANSPORT = True

    def __init__(self, *, capacity: int = 128) -> None:
        if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 1:
            raise ValueError("capacity must be a positive integer")
        self.capacity = capacity
        self._records: deque[X72HistoryRecord] = deque()
        self._fingerprints: deque[str] = deque()
        self._entity_id: str | None = None
        self._next_sequence_id = 1
        self._last_official_record: X72HistoryRecord | None = None

    @property
    def records(self) -> tuple[X72HistoryRecord, ...]:
        return tuple(self._records)

    @property
    def entity_id(self) -> str | None:
        return self._entity_id

    @property
    def last_official_record(self) -> X72HistoryRecord | None:
        return self._last_official_record

    def __len__(self) -> int:
        return len(self._records)

    def _validate_frame(
        self, frame: ObservationEnvelope
    ) -> tuple[str | None, int | None]:
        if not isinstance(frame, ObservationEnvelope):
            raise ValueError("history accepts ObservationEnvelope frames only")
        if frame.status not in ALLOWED_STATUS:
            raise ValueError(f"unsupported status: {frame.status}")
        if not isinstance(frame.observed_at_utc, str) or not frame.observed_at_utc:
            raise ValueError("observed_at_utc is required")
        if not isinstance(frame.source_schema, str) or not frame.source_schema:
            raise ValueError("source_schema is required")
        if not isinstance(frame.source_endpoint, str) or not frame.source_endpoint:
            raise ValueError("source_endpoint is required")
        if not isinstance(frame.condition, str) or not frame.condition:
            raise ValueError("condition is required")
        if frame.payload is not None and not isinstance(frame.payload, dict):
            raise ValueError("payload must be an object or None")

class X72ObservationHistory:
    """Bounded, deterministic, read-only history of validated observations."""

    READ_ONLY = True
    NO_MUTATION_TRANSPORT = True

    def __init__(self, *, capacity: int = 128) -> None:
        if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 1:
            raise ValueError("capacity must be a positive integer")
        self.capacity = capacity
        self._records: deque[X72HistoryRecord] = deque()
        self._fingerprints: deque[str] = deque()
        self._entity_id: str | None = None
        self._next_sequence_id = 1
        self._last_official_record: X72HistoryRecord | None = None

    @property
    def records(self) -> tuple[X72HistoryRecord, ...]:
        return tuple(self._records)

    @property
    def entity_id(self) -> str | None:
        return self._entity_id

    @property
    def last_official_record(self) -> X72HistoryRecord | None:
        return self._last_official_record

    def __len__(self) -> int:
        return len(self._records)

    def _validate_frame(
        self, frame: ObservationEnvelope
    ) -> tuple[str | None, int | None]:
        if not isinstance(frame, ObservationEnvelope):
            raise ValueError("history accepts ObservationEnvelope frames only")
        if frame.status not in ALLOWED_STATUS:
            raise ValueError(f"unsupported status: {frame.status}")
        if not isinstance(frame.observed_at_utc, str) or not frame.observed_at_utc:
            raise ValueError("observed_at_utc is required")
        if not isinstance(frame.source_schema, str) or not frame.source_schema:
            raise ValueError("source_schema is required")
        if not isinstance(frame.source_endpoint, str) or not frame.source_endpoint:
            raise ValueError("source_endpoint is required")
        if not isinstance(frame.condition, str) or not frame.condition:
            raise ValueError("condition is required")
        if frame.payload is not None and not isinstance(frame.payload, dict):
            raise ValueError("payload must be an object or None")

        payload_entity = None
        tick_count = None
        if frame.payload is not None:
            if frame.payload.get("entity_id") is not None:
                payload_entity = str(frame.payload["entity_id"])
            tick_count = _optional_int(
                frame.payload.get("tick_count"), "tick_count"
            )

        frame_entity = (
            str(frame.entity_id) if frame.entity_id is not None else None
        )
        if frame_entity and payload_entity and frame_entity != payload_entity:
            raise ValueError("frame entity_id disagrees with payload entity_id")
        entity_id = frame_entity or payload_entity

        if frame.status == "FRESH" and entity_id is None:
            raise ValueError("FRESH frame requires entity_id")
        if frame.condition == "RECONNECTED" and frame.status != "FRESH":
            raise ValueError("RECONNECTED requires FRESH")
        if (
            frame.condition == "WEBSOCKET_DISCONNECT"
            and frame.status not in {"STALE", "UNKNOWN"}
        ):

            raise ValueError(
                "WEBSOCKET_DISCONNECT requires STALE or UNKNOWN"
            )
        if frame.condition == "SCHEMA_MISMATCH" and frame.status != "UNKNOWN":
            raise ValueError("SCHEMA_MISMATCH requires UNKNOWN")
        if frame.status == "STALE" and frame.condition == "RECONNECTED":
            raise ValueError("STALE cannot be RECONNECTED")

        if entity_id is not None and self._entity_id is not None:
            if entity_id != self._entity_id:
                raise ValueError(
                    f"entity_id changed from {self._entity_id} to {entity_id}"
                )

        if self._is_official_fresh(frame, tick_count):
            last = self._last_official_record
            if (
                last is not None
                and last.tick_count is not None
                and tick_count is not None
                and tick_count < last.tick_count
            ):
                raise ValueError(
                    f"official tick regressed from {last.tick_count} "
                    f"to {tick_count}"
                )

        return entity_id, tick_count

    @staticmethod
    def _is_official_fresh(
        frame: ObservationEnvelope,
        tick_count: int | None,
    ) -> bool:
        return (
            frame.status == "FRESH"
            and frame.source_endpoint in STATE_ENDPOINTS
            and tick_count is not None
            and frame.payload is not None
        )

    def _build_record(
        self,
        frame: ObservationEnvelope,
        *,
        entity_id: str | None,
        tick_count: int | None,
    ) -> X72HistoryRecord:
        payload = frame.payload or {}
        integrity = payload.get("integrity_match")
        if integrity is not None and not isinstance(integrity, bool):
            raise ValueError("integrity_match must be boolean when present")

        active_synapses = _optional_int(
            payload.get("active_synapses"), "active_synapses"
        )
        event_count = _optional_int(payload.get("event_count"), "event_count")

        def optional_text(name: str) -> str | None:
            value = payload.get(name)
            return None if value is None else str(value)

        return X72HistoryRecord(
            sequence_id=self._next_sequence_id,
            observed_at=frame.observed_at_utc,
            entity_id=entity_id,
            tick_count=tick_count,
            source_schema=frame.source_schema,
            source_endpoint=frame.source_endpoint,
            status=frame.status,
            condition=frame.condition,
            queen_mode=optional_text("queen_mode"),
            integrity_match=integrity,
            protected_h256=optional_text("protected_h256"),
            reference_h256=optional_text("reference_h256"),
            payload_h256=_payload_h256(frame.payload),
            r_exec=_optional_float(payload.get("r_exec"), "r_exec"),

            f_rt=_optional_float(payload.get("f_rt"), "f_rt"),
            active_synapses=active_synapses,
            event_count=event_count,
        )

    @staticmethod
    def _fingerprint(record: X72HistoryRecord) -> str:
        return hashlib.sha256(
            _canonical_json(record.semantic_dict())
        ).hexdigest()

    def append(self, frame: ObservationEnvelope) -> HistoryAppendResult:
        try:
            entity_id, tick_count = self._validate_frame(frame)
            record = self._build_record(
                frame,
                entity_id=entity_id,
                tick_count=tick_count,
            )
        except Exception as exc:
            return HistoryAppendResult(
                accepted=False,
                duplicate=False,
                condition="INVALID_FRAME",
                record=None,
                error=str(exc),

            )

        fingerprint = self._fingerprint(record)
        if fingerprint in self._fingerprints:
            return HistoryAppendResult(
                accepted=False,
                duplicate=True,
                condition="DUPLICATE",
                record=None,
                error=None,
            )

        evicted_sequence_id = None
        if len(self._records) >= self.capacity:
            evicted_sequence_id = self._records.popleft().sequence_id
            self._fingerprints.popleft()

        self._records.append(record)
        self._fingerprints.append(fingerprint)
        self._next_sequence_id += 1

        if self._entity_id is None and entity_id is not None:
            self._entity_id = entity_id

        if self._is_official_fresh(frame, tick_count):
            self._last_official_record = record

        return HistoryAppendResult(
            accepted=True,
            duplicate=False,
            condition="ACCEPTED",
            record=record,
            error=None,
            evicted_sequence_id=evicted_sequence_id,
        )

    def deterministic_report(self) -> dict[str, Any]:
        return deterministic_history_report(self._records)
