from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from observation_adapter import ObservationEnvelope
from observation_history import X72ObservationHistory
from trend_analyzer import X72TrendAnalyzer

ENTITY = "QUEEN-X72-0072"
SOURCE = "QUEEN_SERVER_V0_2"
REFERENCE = "54d4cee87f7e5feed1a0735a0b8431a2dc67b1bda0492c78a6c7274109c13180"
FAULT_H256 = "f" * 64


def state_payload(
    tick: int,
    *,
    mode: str = "STABLE",
    integrity: bool = True,
    protected_h256: str = REFERENCE,
    r_exec: float = 100.0,
    f_rt: float = 0.5,
    active_synapses: int = 7,
    event_count: int = 0,
) -> dict[str, Any]:
    return {
        "source": SOURCE,
        "entity_id": ENTITY,
        "tick_count": tick,
        "queen_mode": mode,
        "integrity_match": integrity,
        "protected_h256": protected_h256,
        "reference_h256": REFERENCE,
        "r_exec": r_exec,
        "f_rt": f_rt,
        "active_synapses": active_synapses,
        "event_count": event_count,
    }


def envelope(
    *,
    tick: int | None,
    second: int,
    status: str = "FRESH",
    condition: str = "STREAM_STATE",
    payload: dict[str, Any] | None = None,
) -> ObservationEnvelope:
    if payload is None and tick is not None:
        payload = state_payload(tick)
    return ObservationEnvelope(
        observed_at_utc=f"2026-09-18T16:00:{second:02d}.000Z",
        entity_id=ENTITY,
        source_schema=SOURCE,
        source_endpoint="/ws",
        freshness_ms=0,
        status=status,
        condition=condition,
        payload=payload,
        error=None if status == "FRESH" else condition,
    )


def check(name: str, condition: bool, detail: str = "") -> dict[str, Any]:
    if not condition:
        raise AssertionError(f"{name}: {detail}")
    return {"name": name, "ok": True}


def append_ok(history: X72ObservationHistory, item: ObservationEnvelope) -> None:
    result = history.append(item)
    if not result.accepted:
        raise AssertionError(f"append failed: {result.to_dict()}")

def run() -> dict[str, Any]:
    analyzer = X72TrendAnalyzer()
    checks: list[dict[str, Any]] = []

    empty = X72ObservationHistory(capacity=4)
    empty_frame = analyzer.analyze(empty)
    checks.append(
        check(
            "empty history",
            empty_frame.records_count == 0
            and empty_frame.entity_id is None
            and empty_frame.tick_delta is None
            and empty_frame.h256_closed is None,
        )
    )

    single = X72ObservationHistory(capacity=4)
    append_ok(
        single,
        envelope(
            tick=10,
            second=0,
            payload=state_payload(10, event_count=5),
        ),
    )
    single_frame = analyzer.analyze(single)
    checks.append(
        check(
            "single observation",
            single_frame.records_count == 1
            and single_frame.window_start_tick == 10
            and single_frame.window_end_tick == 10
            and single_frame.tick_delta == 0
            and single_frame.duration_seconds is None,
        )
    )
    checks.append(
        check(
            "single h256 closed",
            single_frame.h256_closed is True
            and single_frame.h256_reclosure_count == 0,
        )
    )

    constant = X72ObservationHistory(capacity=8)
    for index, tick in enumerate((20, 21, 22)):
        append_ok(
            constant,
            envelope(
                tick=tick,
                second=index,
                payload=state_payload(
                    tick,
                    r_exec=100.0,
                    f_rt=0.5,
                    active_synapses=7,
                    event_count=5 + index,
                ),
            ),
        )
    constant_frame = analyzer.analyze(constant)
    checks.append(
        check(
            "constant runtime values",
            constant_frame.r_exec_min == 100.0
            and constant_frame.r_exec_max == 100.0
            and constant_frame.r_exec_mean == 100.0
            and constant_frame.r_exec_delta == 0.0
            and constant_frame.f_rt_delta == 0.0
            and constant_frame.active_synapses_delta == 0.0,
        )
    )
    checks.append(
        check(
            "duration and event delta",
            constant_frame.duration_seconds == 2.0
            and constant_frame.observation_gap_min == 1.0
            and constant_frame.observation_gap_max == 1.0
            and constant_frame.observation_gap_mean == 1.0
            and constant_frame.event_delta == 2,
        )
    )

    increasing = X72ObservationHistory(capacity=8)
    for index, tick in enumerate((30, 31, 32)):
        append_ok(
            increasing,
            envelope(
                tick=tick,
                second=10 + index,
                payload=state_payload(
                    tick,
                    r_exec=90.0 + index * 10,
                    f_rt=0.4 + index * 0.1,
                    active_synapses=5 + index,
                    event_count=10 + index * 2,
                ),
            ),
        )
    inc_frame = analyzer.analyze(increasing)
    checks.append(
        check(
            "increasing values",
            inc_frame.tick_delta == 2
            and inc_frame.r_exec_delta == 20.0
            and inc_frame.f_rt_delta == 0.2
            and inc_frame.active_synapses_delta == 2.0
            and inc_frame.event_delta == 4,
        )
    )

    decreasing = X72ObservationHistory(capacity=8)
    values = ((120.0, 0.8, 7), (110.0, 0.7, 6), (100.0, 0.6, 5))
    for index, (r_exec, f_rt, synapses) in enumerate(values):
        tick = 40 + index
        append_ok(
            decreasing,
            envelope(
                tick=tick,
                second=20 + index,
                payload=state_payload(
                    tick,
                    r_exec=r_exec,
                    f_rt=f_rt,
                    active_synapses=synapses,
                    event_count=20 + index,
                ),
            ),
        )
    dec_frame = analyzer.analyze(decreasing)
    checks.append(
        check(
            "decreasing values",
            dec_frame.r_exec_delta == -20.0
            and dec_frame.f_rt_delta == -0.2
            and dec_frame.active_synapses_delta == -2.0,
        )
    )

    mixed = X72ObservationHistory(capacity=16)
    append_ok(
        mixed,
        envelope(
            tick=50,
            second=30,
            payload=state_payload(50, event_count=30),
        ),
    )
    stale_payload = state_payload(50, event_count=30)
    append_ok(
        mixed,
        envelope(
            tick=50,
            second=31,
            status="STALE",
            condition="WEBSOCKET_DISCONNECT",
            payload=stale_payload,
        ),
    )
    append_ok(
        mixed,
        envelope(
            tick=51,
            second=32,
            condition="RECONNECTED",
            payload=state_payload(51, event_count=31),
        ),
    )

    append_ok(
        mixed,
        envelope(
            tick=None,
            second=33,
            status="UNKNOWN",
            condition="SCHEMA_MISMATCH",
            payload=None,
        ),
    )
    append_ok(
        mixed,
        envelope(
            tick=None,
            second=34,
            status="UNKNOWN",
            condition="HTTP_TIMEOUT",
            payload=None,
        ),
    )
    mixed_frame = analyzer.analyze(mixed)
    checks.append(
        check(
            "status counters",
            mixed_frame.fresh_count == 2
            and mixed_frame.stale_count == 1
            and mixed_frame.unknown_count == 2
            and mixed_frame.reconnect_count == 1
            and mixed_frame.schema_mismatch_count == 1,
        )
    )

    lifecycle = X72ObservationHistory(capacity=16)
    lifecycle_rows = [
        (60, "STABLE", True, REFERENCE, 7, 40),
        (61, "FAULT", False, FAULT_H256, 6, 41),
        (62, "FAULT", False, FAULT_H256, 6, 42),
        (63, "AUTO_REPAIR", False, FAULT_H256, 6, 43),
        (64, "AUTO_REPAIR", False, FAULT_H256, 6, 44),
        (65, "STABLE", True, REFERENCE, 7, 45),
    ]
    for index, (tick, mode, integrity, protected, synapses, events) in enumerate(
        lifecycle_rows
    ):
        append_ok(
            lifecycle,
            envelope(
                tick=tick,
                second=40 + index,
                payload=state_payload(
                    tick,
                    mode=mode,
                    integrity=integrity,
                    protected_h256=protected,
                    active_synapses=synapses,
                    event_count=events,
                ),
            ),
        )
    lifecycle_frame = analyzer.analyze(lifecycle)
    checks.append(
        check(
            "mode transitions",
            [item["to"] for item in lifecycle_frame.mode_transitions]
            == ["FAULT", "AUTO_REPAIR", "STABLE"],
        )
    )
    checks.append(
        check(
            "integrity transitions",
            [item["to"] for item in lifecycle_frame.integrity_transitions]
            == [False, True],
        )
    )
    checks.append(
        check(
            "fault interval",
            len(lifecycle_frame.fault_intervals) == 1
            and lifecycle_frame.fault_intervals[0]["start_tick"] == 61
            and lifecycle_frame.fault_intervals[0]["end_tick"] == 62
            and lifecycle_frame.fault_intervals[0]["records_count"] == 2,
        )
    )
    checks.append(
        check(
            "repair interval",
            len(lifecycle_frame.repair_intervals) == 1
            and lifecycle_frame.repair_intervals[0]["start_tick"] == 63
            and lifecycle_frame.repair_intervals[0]["end_tick"] == 64
            and lifecycle_frame.repair_intervals[0]["records_count"] == 2,
        )
    )
    checks.append(
        check(
            "h256 reclosure",
            lifecycle_frame.h256_closed is True
            and lifecycle_frame.h256_reclosure_count == 1,
        )
    )
    checks.append(
        check(
            "synapse analysis",
            lifecycle_frame.active_synapses_min == 6.0
            and lifecycle_frame.active_synapses_max == 7.0
            and lifecycle_frame.active_synapses_delta == 0.0,
        )
    )

    bounded = X72ObservationHistory(capacity=3)
    for index, tick in enumerate((70, 71, 72, 73)):
        append_ok(
            bounded,
            envelope(
                tick=tick,
                second=50 + index,
                payload=state_payload(tick, event_count=50 + index),
            ),
        )
    bounded_frame = analyzer.analyze(bounded)
    checks.append(
        check(
            "bounded window",
            bounded_frame.records_count == 3
            and bounded_frame.window_start_sequence_id == 2
            and bounded_frame.window_end_sequence_id == 4
            and bounded_frame.window_start_tick == 71
            and bounded_frame.window_end_tick == 73
            and bounded_frame.tick_delta == 2,
        )
    )

    before_records = [record.to_dict() for record in lifecycle.records]
    before_report = lifecycle.deterministic_report()
    deterministic_a = analyzer.analyze(lifecycle)
    deterministic_b = analyzer.analyze(lifecycle)
    after_records = [record.to_dict() for record in lifecycle.records]
    after_report = lifecycle.deterministic_report()

    checks.append(
        check(
            "deterministic trend frame",
            deterministic_a.to_dict() == deterministic_b.to_dict()
            and deterministic_a.trend_h256 == deterministic_b.trend_h256,
        )
    )
    checks.append(
        check(
            "history immutable",
            before_records == after_records
            and before_report == after_report,
        )
    )
    checks.append(
        check(
            "source history hash",
            deterministic_a.source_history_h256
            == before_report["report_h256"],
        )
    )

    encoded = json.dumps(
        deterministic_a.to_dict(),
        sort_keys=True,
        separators=(",", ":"),
    )
    checks.append(
        check(
            "trend frame serializable",
            '"trend_h256"' in encoded
            and len(deterministic_a.trend_h256) == 64,
        )
    )
    checks.append(
        check(
            "read only constants",
            X72TrendAnalyzer.READ_ONLY is True
            and X72TrendAnalyzer.NO_MUTATION_TRANSPORT is True
            and X72TrendAnalyzer.DETERMINISTIC is True,
        )
    )

    source = (ROOT / "trend_analyzer" / "analyzer.py").read_text(
        encoding="utf-8"
    )
    forbidden_transport = (
        "QueenCore",
        "/api/fault",
        "/api/repair",
        "urllib.",
        "requests.",
        "websockets.",
        'method="POST"',
        'method="PUT"',
        'method="PATCH"',
        'method="DELETE"',
    )
    checks.append(
        check(
            "no mutation transport",
            not any(token in source for token in forbidden_transport),
        )
    )
    forbidden_behavior = ("predict(", "prediction", "cognitive_score")
    checks.append(
        check(
            "no prediction or cognitive scoring",
            not any(token in source.lower() for token in forbidden_behavior),
        )
    )

    try:
        analyzer.analyze(object())  # type: ignore[arg-type]
    except TypeError:
        invalid_type_rejected = True
    else:
        invalid_type_rejected = False
    checks.append(check("history type discipline", invalid_type_rejected))

    report = {
        "schema": "ANTMUX-X72-TREND-ANALYZER-ACCEPTANCE-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "checks_failed": sum(1 for item in checks if not item["ok"]),
        "trend_h256": deterministic_a.trend_h256,
        "source_history_h256": deterministic_a.source_history_h256,
        "verdict": "PASS" if all(item["ok"] for item in checks) else "FAIL",
        "checks": checks,
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    if result["verdict"] != "PASS":
        raise SystemExit(1)
