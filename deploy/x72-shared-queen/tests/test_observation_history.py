from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from observation_adapter import ObservationEnvelope
from observation_history import (
    X72ObservationHistory,
    deterministic_history_report,
)

ENTITY = "QUEEN-X72-0072"
REFERENCE = "49e75d92d8fde33f402c3b60482bc5dcf13c12f09bd8c07c7937961d42ceaff9"
FAULT_H256 = "f" * 64
SOURCE = "QUEEN_SERVER_V0_2"


def payload(
    tick: int,
    *,
    protected: str = REFERENCE,
    reference: str = REFERENCE,
    integrity: bool = True,
    entity_id: str = ENTITY,
    event_count: int | None = None,
) -> dict[str, Any]:
    return {
        "source": SOURCE,
        "entity_id": entity_id,
        "tick_count": tick,
        "queen_mode": "FAULT" if not integrity else "STABLE",
        "integrity_match": integrity,
        "protected_h256": protected,
        "reference_h256": reference,
        "r_exec": 109.091 + tick / 1000,
        "f_rt": 0.455 + tick / 100000,
        "active_synapses": 6 if not integrity else 7,
        "event_count": tick if event_count is None else event_count,
    }


def frame(
    tick: int | None,
    *,
    status: str = "FRESH",
    condition: str = "STREAM_STATE",
    entity_id: str | None = ENTITY,
    source_endpoint: str = "/ws",
    body: dict[str, Any] | None = None,
    observed_at: str = "2026-09-18T14:30:00.000Z",
) -> ObservationEnvelope:
    if body is None and tick is not None:
        body = payload(tick, entity_id=entity_id or ENTITY)
    return ObservationEnvelope(
        observed_at_utc=observed_at,
        entity_id=entity_id,
        source_schema=SOURCE,
        source_endpoint=source_endpoint,
        freshness_ms=0,
        status=status,
        condition=condition,
        payload=body,
        error=None if status == "FRESH" else condition,
    )


def check(name: str, condition: bool, detail: str = "") -> dict[str, Any]:
    if not condition:
        raise AssertionError(f"{name}: {detail}")
    return {"name": name, "ok": True}


def run() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    h = X72ObservationHistory(capacity=8)
    first = frame(10)
    first_before = copy.deepcopy(first.to_dict())
    r1 = h.append(first)
    checks.append(check("fresh insertion", r1.accepted and len(h) == 1))
    checks.append(
        check(
            "source immutability",
            first.to_dict() == first_before,
            "source ObservationEnvelope mutated",
        )
    )
    checks.append(
        check(
            "first official state retained",
            h.last_official_record is not None
            and h.last_official_record.tick_count == 10,
        )
    )
    r2 = h.append(frame(11, observed_at="2026-09-18T14:30:00.100Z"))
    r3 = h.append(frame(12, observed_at="2026-09-18T14:30:00.200Z"))
    checks.append(
        check(
            "increasing ticks",
            r2.accepted
            and r3.accepted
            and [x.tick_count for x in h.records[-3:]] == [10, 11, 12],
        )
    )
    checks.append(check("same entity", h.entity_id == ENTITY))

    wrong_body = payload(13, entity_id="QUEEN-X72-OTHER")
    wrong = frame(
        13,
        entity_id="QUEEN-X72-OTHER",
        body=wrong_body,
        observed_at="2026-09-18T14:30:00.300Z",
    )
    wrong_result = h.append(wrong)
    checks.append(
        check(
            "entity change rejected",
            not wrong_result.accepted
            and "entity_id changed" in (wrong_result.error or ""),
        )
    )
    checks.append(
        check(
            "entity mismatch no contamination",
            h.entity_id == ENTITY and h.last_official_record.tick_count == 12,
        )
    )
    regressed = h.append(
        frame(9, observed_at="2026-09-18T14:30:00.400Z")
    )
    checks.append(
        check(
            "decreasing tick rejected",
            not regressed.accepted and "tick regressed" in (regressed.error or ""),
        )
    )

    same_tick_body = payload(12, event_count=999)
    same_tick = h.append(
        frame(
            12,
            body=same_tick_body,
            observed_at="2026-09-18T14:30:00.500Z",
        )
    )
    checks.append(check("same tick allowed", same_tick.accepted))

    duplicate = h.append(
        frame(
            12,
            body=same_tick_body,
            observed_at="2026-09-18T14:30:05.000Z",
        )
    )
    checks.append(
        check(
            "duplicate detected",
            not duplicate.accepted
            and duplicate.duplicate
            and duplicate.condition == "DUPLICATE",
        )
    )
    stale_frame = frame(
        12,
        status="STALE",
        condition="STREAM_STALE",
        body=same_tick_body,
        observed_at="2026-09-18T14:30:06.000Z",
    )
    stale_result = h.append(stale_frame)
    checks.append(check("stale accepted", stale_result.accepted))
    checks.append(
        check(
            "stale not promoted",
            h.last_official_record is not None
            and h.last_official_record.status == "FRESH"
            and h.last_official_record.tick_count == 12,
        )
    )

    disconnect = h.append(
        frame(
            12,
            status="STALE",
            condition="WEBSOCKET_DISCONNECT",
            body=same_tick_body,
            observed_at="2026-09-18T14:30:07.000Z",
        )
    )
    checks.append(check("disconnect recorded", disconnect.accepted))

    reconnect = h.append(
        frame(
            13,
            status="FRESH",
            condition="RECONNECTED",
            observed_at="2026-09-18T14:30:08.000Z",
        )
    )
    checks.append(
        check(
            "reconnect authoritative",
            reconnect.accepted
            and h.last_official_record is not None
            and h.last_official_record.tick_count == 13
            and h.last_official_record.condition == "RECONNECTED",
        )
    )
    schema_mismatch = h.append(
        frame(
            None,
            status="UNKNOWN",
            condition="SCHEMA_MISMATCH",
            entity_id=ENTITY,
            body=None,
            source_endpoint="/api/telemetry",
            observed_at="2026-09-18T14:30:09.000Z",
        )
    )
    checks.append(check("schema mismatch recorded", schema_mismatch.accepted))

    unknown = h.append(
        frame(
            None,
            status="UNKNOWN",
            condition="HTTP_TIMEOUT",
            entity_id=ENTITY,
            body=None,
            source_endpoint="/api/state",
            observed_at="2026-09-18T14:30:10.000Z",
        )
    )
    checks.append(check("unknown recorded", unknown.accepted))
    checks.append(
        check(
            "unknown not promoted",
            h.last_official_record is not None
            and h.last_official_record.tick_count == 13,
        )
    )

    h256_history = X72ObservationHistory(capacity=8)
    base_result = h256_history.append(frame(20))
    fault_result = h256_history.append(
        frame(
            21,
            body=payload(
                21,
                protected=FAULT_H256,
                reference=REFERENCE,
                integrity=False,
            ),
            observed_at="2026-09-18T14:31:00.000Z",
        )
    )
    restore_result = h256_history.append(
        frame(
            22,
            body=payload(22),
            observed_at="2026-09-18T14:31:01.000Z",
        )
    )
    checks.append(
        check(
            "h256 baseline preserved",
            base_result.record is not None
            and base_result.record.protected_h256 == REFERENCE
            and base_result.record.reference_h256 == REFERENCE,
        )
    )
    checks.append(
        check(
            "h256 fault transported",
            fault_result.record is not None
            and fault_result.record.protected_h256 == FAULT_H256
            and fault_result.record.reference_h256 == REFERENCE
            and fault_result.record.integrity_match is False,
        )
    )
    checks.append(
        check(
            "h256 restored transported",
            restore_result.record is not None
            and restore_result.record.protected_h256 == REFERENCE
            and restore_result.record.reference_h256 == REFERENCE
            and restore_result.record.integrity_match is True,
        )
    )

    deterministic_frames = [
        frame(30, observed_at="2026-09-18T14:32:00.000Z"),
        frame(31, observed_at="2026-09-18T14:32:01.000Z"),
        frame(
            31,
            status="STALE",
            condition="WEBSOCKET_DISCONNECT",
            observed_at="2026-09-18T14:32:02.000Z",
        ),
    ]
    dh1 = X72ObservationHistory(capacity=8)
    dh2 = X72ObservationHistory(capacity=8)
    for item in deterministic_frames:
        assert dh1.append(item).accepted
        assert dh2.append(item).accepted

    checks.append(
        check(
            "same input same history",
            [record.to_dict() for record in dh1.records]
            == [record.to_dict() for record in dh2.records],
        )
    )
    report_forward = deterministic_history_report(dh1.records)
    report_reverse = deterministic_history_report(reversed(dh1.records))
    checks.append(
        check(
            "deterministic report order independent",
            report_forward["report_h256"] == report_reverse["report_h256"]
            and report_forward["records"] == report_reverse["records"],
        )
    )

    bounded = X72ObservationHistory(capacity=3)
    eviction = None
    for tick in (40, 41, 42, 43):
        result = bounded.append(
            frame(
                tick,
                observed_at=f"2026-09-18T14:33:{tick-40:02d}.000Z",
            )
        )
        if tick == 43:
            eviction = result
    checks.append(
        check(
            "bounded capacity",
            len(bounded) == 3
            and [record.sequence_id for record in bounded.records] == [2, 3, 4],
        )
    )
    checks.append(
        check(
            "oldest eviction",
            eviction is not None and eviction.evicted_sequence_id == 1,
        )
    )
    checks.append(
        check(
            "last official retained beyond window",
            bounded.last_official_record is not None
            and bounded.last_official_record.tick_count == 43,
        )
    )

    malformed = h.append(object())  # type: ignore[arg-type]
    checks.append(
        check(
            "invalid frame rejected",
            not malformed.accepted
            and malformed.condition == "INVALID_FRAME",
        )
    )

    record_json = json.dumps(
        h256_history.records[-1].to_dict(),
        sort_keys=True,
        separators=(",", ":"),
    )
    checks.append(
        check(
            "record serializable",
            '"protected_h256"' in record_json
            and '"payload_h256"' in record_json,
        )
    )

    module_path = ROOT / "observation_history" / "history.py"
    source = module_path.read_text(encoding="utf-8")
    forbidden = (
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
            not any(token in source for token in forbidden),
        )
    )
    checks.append(
        check(
            "read only constants",
            X72ObservationHistory.READ_ONLY is True
            and X72ObservationHistory.NO_MUTATION_TRANSPORT is True,
        )
    )

    report = {
        "schema": "ANTMUX-X72-OBSERVATION-HISTORY-ACCEPTANCE-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "checks_failed": sum(1 for item in checks if not item["ok"]),
        "verdict": "PASS" if all(item["ok"] for item in checks) else "FAIL",
        "deterministic_report_h256": report_forward["report_h256"],
        "checks": checks,
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    if result["verdict"] != "PASS":
        raise SystemExit(1)
