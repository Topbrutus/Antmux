from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Iterable

from observation_history import (
    X72HistoryRecord,
    X72ObservationHistory,
    deterministic_history_report,
)


TREND_SCHEMA = "ANTMUX-X72-TREND-FRAME-v0.1"


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")

def _round(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 12)


def _parse_time(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _series_stats(
    values: Iterable[int | float | None],
) -> tuple[float | None, float | None, float | None, float | None]:
    present = [float(value) for value in values if value is not None]
    if not present:
        return None, None, None, None
    return (
        _round(min(present)),
        _round(max(present)),
        _round(sum(present) / len(present)),
        _round(present[-1] - present[0]),
    )

def _duration_stats(
    records: tuple[X72HistoryRecord, ...],
) -> tuple[float | None, float | None, float | None, float | None]:
    parsed = [_parse_time(record.observed_at) for record in records]
    gaps: list[float] = []
    for left, right in zip(parsed, parsed[1:]):
        if left is None or right is None:
            continue
        gaps.append((right - left).total_seconds())
    duration = None
    valid = [item for item in parsed if item is not None]
    if len(valid) >= 2:
        duration = (valid[-1] - valid[0]).total_seconds()
    if not gaps:
        return _round(duration), None, None, None
    return (
        _round(duration),
        _round(min(gaps)),
        _round(max(gaps)),
        _round(sum(gaps) / len(gaps)),
    )

def _transitions(
    records: tuple[X72HistoryRecord, ...],
    getter: Callable[[X72HistoryRecord], Any],
) -> tuple[dict[str, Any], ...]:
    result: list[dict[str, Any]] = []
    previous: Any = None
    have_previous = False
    for record in records:
        current = getter(record)
        if current is None:
            continue
        if have_previous and current != previous:
            result.append(
                {
                    "sequence_id": record.sequence_id,
                    "tick_count": record.tick_count,
                    "from": previous,
                    "to": current,
                }
            )
        previous = current
        have_previous = True
    return tuple(result)

def _intervals(
    records: tuple[X72HistoryRecord, ...],
    predicate: Callable[[X72HistoryRecord], bool],
) -> tuple[dict[str, Any], ...]:
    result: list[dict[str, Any]] = []
    start: X72HistoryRecord | None = None
    end: X72HistoryRecord | None = None
    count = 0
    for record in records:
        if predicate(record):
            if start is None:
                start = record
                count = 0
            end = record
            count += 1
            continue
        if start is not None and end is not None:
            result.append(_interval_dict(start, end, count))
            start = None
            end = None
            count = 0
    if start is not None and end is not None:
        result.append(_interval_dict(start, end, count))
    return tuple(result)

def _interval_dict(
    start: X72HistoryRecord,
    end: X72HistoryRecord,
    count: int,
) -> dict[str, Any]:
    return {
        "start_sequence_id": start.sequence_id,
        "end_sequence_id": end.sequence_id,
        "start_tick": start.tick_count,
        "end_tick": end.tick_count,
        "records_count": count,
    }


def _h256_summary(
    records: tuple[X72HistoryRecord, ...],
) -> tuple[bool | None, int]:
    comparable = [
        record
        for record in records
        if record.protected_h256 is not None
        and record.reference_h256 is not None
    ]
    if not comparable:
        return None, 0
    closed = comparable[-1].protected_h256 == comparable[-1].reference_h256

    reclosures = 0
    previous_closed = (
        comparable[0].protected_h256 == comparable[0].reference_h256
    )
    for record in comparable[1:]:
        current_closed = record.protected_h256 == record.reference_h256
        if not previous_closed and current_closed:
            reclosures += 1
        previous_closed = current_closed
    return closed, reclosures


@dataclass(frozen=True)
class X72TrendFrame:
    schema: str
    entity_id: str | None
    window_start_sequence_id: int | None
    window_end_sequence_id: int | None
    window_start_tick: int | None
    window_end_tick: int | None
    records_count: int
    fresh_count: int
    stale_count: int
    unknown_count: int
    reconnect_count: int

    schema_mismatch_count: int
    tick_delta: int | None
    duration_seconds: float | None
    observation_gap_min: float | None
    observation_gap_max: float | None
    observation_gap_mean: float | None
    r_exec_min: float | None
    r_exec_max: float | None
    r_exec_mean: float | None
    r_exec_delta: float | None
    f_rt_min: float | None
    f_rt_max: float | None
    f_rt_mean: float | None
    f_rt_delta: float | None
    active_synapses_min: float | None
    active_synapses_max: float | None
    active_synapses_mean: float | None
    active_synapses_delta: float | None
    event_delta: int | None
    integrity_transitions: tuple[dict[str, Any], ...]
    mode_transitions: tuple[dict[str, Any], ...]
    fault_intervals: tuple[dict[str, Any], ...]
    repair_intervals: tuple[dict[str, Any], ...]
    h256_closed: bool | None

    h256_reclosure_count: int
    source_history_h256: str
    trend_h256: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class X72TrendAnalyzer:
    """Deterministic, descriptive, read-only analysis of observation history."""

    READ_ONLY = True
    NO_MUTATION_TRANSPORT = True
    DETERMINISTIC = True

    def analyze(self, history: X72ObservationHistory) -> X72TrendFrame:
        if not isinstance(history, X72ObservationHistory):
            raise TypeError("history must be X72ObservationHistory")

        records = tuple(history.records)
        entities = {r.entity_id for r in records if r.entity_id is not None}
        if len(entities) > 1:
            raise ValueError("history contains multiple entity_id values")
        entity_id = next(iter(entities), history.entity_id)

        ticks = [r.tick_count for r in records if r.tick_count is not None]
        window_start_tick = ticks[0] if ticks else None
        window_end_tick = ticks[-1] if ticks else None
        tick_delta = (
            window_end_tick - window_start_tick
            if window_start_tick is not None and window_end_tick is not None
            else None
        )

        r_min, r_max, r_mean, r_delta = _series_stats(
            r.r_exec for r in records
        )
        f_min, f_max, f_mean, f_delta = _series_stats(
            r.f_rt for r in records
        )
        a_min, a_max, a_mean, a_delta = _series_stats(
            r.active_synapses for r in records
        )
        duration, gap_min, gap_max, gap_mean = _duration_stats(records)

        events = [r.event_count for r in records if r.event_count is not None]
        event_delta = events[-1] - events[0] if events else None

        integrity_transitions = _transitions(
            records, lambda record: record.integrity_match
        )
        mode_transitions = _transitions(
            records, lambda record: record.queen_mode
        )
        fault_intervals = _intervals(
            records, lambda record: record.queen_mode == "FAULT"
        )
        repair_intervals = _intervals(
            records,
            lambda record: record.queen_mode in {"AUTO_REPAIR", "REPAIR"},
        )
        h256_closed, h256_reclosure_count = _h256_summary(records)

        source_history_h256 = deterministic_history_report(
            records
        )["report_h256"]

        first_sequence = records[0].sequence_id if records else None
        last_sequence = records[-1].sequence_id if records else None

        body = {
            "schema": TREND_SCHEMA,
            "entity_id": entity_id,
            "window_start_sequence_id": first_sequence,
            "window_end_sequence_id": last_sequence,
            "window_start_tick": window_start_tick,
            "window_end_tick": window_end_tick,
            "records_count": len(records),
            "fresh_count": sum(r.status == "FRESH" for r in records),
            "stale_count": sum(r.status == "STALE" for r in records),
            "unknown_count": sum(r.status == "UNKNOWN" for r in records),
            "reconnect_count": sum(
                r.condition == "RECONNECTED" for r in records
            ),
            "schema_mismatch_count": sum(
                "SCHEMA_MISMATCH" in r.condition for r in records
            ),
            "tick_delta": tick_delta,
            "duration_seconds": duration,
            "observation_gap_min": gap_min,
            "observation_gap_max": gap_max,
            "observation_gap_mean": gap_mean,
            "r_exec_min": r_min,

            "r_exec_max": r_max,
            "r_exec_mean": r_mean,
            "r_exec_delta": r_delta,
            "f_rt_min": f_min,
            "f_rt_max": f_max,
            "f_rt_mean": f_mean,
            "f_rt_delta": f_delta,
            "active_synapses_min": a_min,
            "active_synapses_max": a_max,
            "active_synapses_mean": a_mean,
            "active_synapses_delta": a_delta,
            "event_delta": event_delta,
            "integrity_transitions": integrity_transitions,
            "mode_transitions": mode_transitions,
            "fault_intervals": fault_intervals,
            "repair_intervals": repair_intervals,
            "h256_closed": h256_closed,
            "h256_reclosure_count": h256_reclosure_count,
            "source_history_h256": source_history_h256,
        }
        trend_h256 = hashlib.sha256(_canonical_json(body)).hexdigest()

        return X72TrendFrame(
            schema=body["schema"],
            entity_id=body["entity_id"],
            window_start_sequence_id=body["window_start_sequence_id"],
            window_end_sequence_id=body["window_end_sequence_id"],
            window_start_tick=body["window_start_tick"],
            window_end_tick=body["window_end_tick"],
            records_count=body["records_count"],
            fresh_count=body["fresh_count"],
            stale_count=body["stale_count"],
            unknown_count=body["unknown_count"],
            reconnect_count=body["reconnect_count"],
            schema_mismatch_count=body["schema_mismatch_count"],
            tick_delta=body["tick_delta"],
            duration_seconds=body["duration_seconds"],
            observation_gap_min=body["observation_gap_min"],
            observation_gap_max=body["observation_gap_max"],
            observation_gap_mean=body["observation_gap_mean"],
            r_exec_min=body["r_exec_min"],
            r_exec_max=body["r_exec_max"],
            r_exec_mean=body["r_exec_mean"],

            r_exec_delta=body["r_exec_delta"],
            f_rt_min=body["f_rt_min"],
            f_rt_max=body["f_rt_max"],
            f_rt_mean=body["f_rt_mean"],
            f_rt_delta=body["f_rt_delta"],
            active_synapses_min=body["active_synapses_min"],
            active_synapses_max=body["active_synapses_max"],
            active_synapses_mean=body["active_synapses_mean"],
            active_synapses_delta=body["active_synapses_delta"],
            event_delta=body["event_delta"],
            integrity_transitions=body["integrity_transitions"],
            mode_transitions=body["mode_transitions"],
            fault_intervals=body["fault_intervals"],
            repair_intervals=body["repair_intervals"],
            h256_closed=body["h256_closed"],
            h256_reclosure_count=body["h256_reclosure_count"],
            source_history_h256=body["source_history_h256"],
            trend_h256=trend_h256,
        )
