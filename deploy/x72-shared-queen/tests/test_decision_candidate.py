from __future__ import annotations

import inspect
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from decision_candidate import X72DecisionCandidate
from observation_adapter import ObservationEnvelope
from observation_history import X72ObservationHistory
from trend_analyzer import X72TrendAnalyzer

ENTITY = "QUEEN-X72-0072"
SOURCE = "QUEEN_SERVER_V0_2"
REFERENCE = "49e75d92d8fde33f402c3b60482bc5dcf13c12f09bd8c07c7937961d42ceaff9"
FAULT_H256 = "f" * 64


def payload(
    tick: int,
    *,
    mode: str = "STABLE",
    integrity: bool = True,
    protected: str = REFERENCE,
    r_exec: float = 100.0,
    f_rt: float = 0.5,
    active_synapses: int = 7,
    event_count: int | None = None,
) -> dict[str, Any]:
    return {
        "source": SOURCE,
        "entity_id": ENTITY,
        "tick_count": tick,
        "queen_mode": mode,
        "integrity_match": integrity,
        "protected_h256": protected,
        "reference_h256": REFERENCE,
        "r_exec": r_exec,
        "f_rt": f_rt,
        "active_synapses": active_synapses,
        "event_count": tick if event_count is None else event_count,
    }


def envelope(
    tick: int | None,
    second: int,
    *,
    status: str = "FRESH",
    condition: str = "STREAM_STATE",
    body: dict[str, Any] | None = None,
) -> ObservationEnvelope:
    if body is None and tick is not None:
        body = payload(tick)
    return ObservationEnvelope(
        observed_at_utc=f"2026-09-18T18:30:{second:02d}.000Z",
        entity_id=ENTITY,
        source_schema=SOURCE,
        source_endpoint="/ws",
        freshness_ms=0,
        status=status,
        condition=condition,
        payload=body,
        error=None if status == "FRESH" else condition,
    )
def make_history(*frames: ObservationEnvelope, capacity: int = 32) -> X72ObservationHistory:
    history = X72ObservationHistory(capacity=capacity)
    for item in frames:
        result = history.append(item)
        if not result.accepted:
            raise AssertionError(f"history append failed: {result.to_dict()}")
    return history


def generate(history: X72ObservationHistory):
    trend = X72TrendAnalyzer().analyze(history)
    candidate = X72DecisionCandidate().generate(history, trend)
    return trend, candidate


def check(name: str, condition: bool, detail: str = "") -> dict[str, Any]:
    if not condition:
        raise AssertionError(f"{name}: {detail}")
    return {"name": name, "ok": True}


def run() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    empty = X72ObservationHistory(capacity=4)
    empty_trend, empty_candidate = generate(empty)
    checks.append(
        check(
            "empty history observe more",
            empty_candidate.candidate_type == "OBSERVE_MORE"
            and empty_candidate.condition == "EMPTY_HISTORY"
            and empty_candidate.source_records_count == 0,
        )
    )

    single = make_history(envelope(10, 0))
    _, single_candidate = generate(single)
    checks.append(
        check(
            "insufficient data observe more",
            single_candidate.candidate_type == "OBSERVE_MORE"
            and single_candidate.condition == "INSUFFICIENT_WINDOW",
        )
    )

    stable = make_history(
        envelope(20, 1, body=payload(20, event_count=20)),
        envelope(21, 2, body=payload(21, event_count=21)),
    )
    stable_trend, stable_candidate = generate(stable)
    checks.append(
        check(
            "stable no change",
            stable_candidate.candidate_type == "NO_CHANGE"
            and stable_candidate.integrity_state == "CLOSED"
            and stable_candidate.condition == "STABLE_CLOSED_WINDOW",
        )
    )
    fault_open = make_history(
        envelope(30, 3, body=payload(30)),
        envelope(
            31,
            4,
            body=payload(
                31,
                mode="FAULT",
                integrity=False,
                protected=FAULT_H256,
                active_synapses=6,
            ),
        ),
    )
    _, fault_open_candidate = generate(fault_open)
    checks.append(
        check(
            "fault open candidate",
            fault_open_candidate.candidate_type == "INVESTIGATE_FAULT"
            and fault_open_candidate.integrity_state == "OPEN"
            and fault_open_candidate.evidence["fault_intervals"] == 1,
        )
    )

    fault_reclosed = make_history(
        envelope(40, 5, body=payload(40)),
        envelope(
            41,
            6,
            body=payload(
                41,
                mode="FAULT",
                integrity=False,
                protected=FAULT_H256,
                active_synapses=6,
            ),
        ),
        envelope(42, 7, body=payload(42)),
    )
    _, fault_reclosed_candidate = generate(fault_reclosed)
    checks.append(
        check(
            "fault reclosed candidate",
            fault_reclosed_candidate.candidate_type == "VERIFY_INTEGRITY"
            and fault_reclosed_candidate.condition == "FAULT_RECLOSED"
            and fault_reclosed_candidate.integrity_state == "CLOSED",
        )
    )

    repair_active = make_history(
        envelope(50, 8, body=payload(50)),
        envelope(
            51,
            9,
            body=payload(
                51,
                mode="FAULT",
                integrity=False,
                protected=FAULT_H256,
                active_synapses=6,
            ),
        ),
        envelope(
            52,
            10,
            body=payload(
                52,
                mode="AUTO_REPAIR",
                integrity=False,
                protected=FAULT_H256,
                active_synapses=6,
            ),
        ),
    )
    _, repair_active_candidate = generate(repair_active)
    checks.append(
        check(
            "repair active candidate",
            repair_active_candidate.candidate_type == "INVESTIGATE_REPAIR"
            and repair_active_candidate.condition == "REPAIR_INTERVAL_ACTIVE",
        )
    )
    repair_closed = make_history(
        envelope(60, 11, body=payload(60)),
        envelope(
            61,
            12,
            body=payload(
                61,
                mode="FAULT",
                integrity=False,
                protected=FAULT_H256,
                active_synapses=6,
            ),
        ),
        envelope(
            62,
            13,
            body=payload(
                62,
                mode="AUTO_REPAIR",
                integrity=False,
                protected=FAULT_H256,
                active_synapses=6,
            ),
        ),
        envelope(63, 14, body=payload(63)),
    )
    _, repair_closed_candidate = generate(repair_closed)
    checks.append(
        check(
            "repair observed candidate",
            repair_closed_candidate.candidate_type == "INVESTIGATE_REPAIR"
            and repair_closed_candidate.condition == "REPAIR_INTERVAL_OBSERVED",
        )
    )

    h256_open = make_history(
        envelope(70, 15, body=payload(70)),
        envelope(
            71,
            16,
            body=payload(
                71,
                mode="STABLE",
                integrity=False,
                protected=FAULT_H256,
            ),
        ),
    )
    _, h256_open_candidate = generate(h256_open)
    checks.append(
        check(
            "h256 open candidate",
            h256_open_candidate.candidate_type == "VERIFY_INTEGRITY"
            and h256_open_candidate.condition == "H256_NOT_CLOSED",
        )
    )

    disconnect = make_history(
        envelope(80, 17, body=payload(80)),
        envelope(
            80,
            18,
            status="STALE",
            condition="WEBSOCKET_DISCONNECT",
            body=payload(80),
        ),
    )
    _, disconnect_candidate = generate(disconnect)
    checks.append(
        check(
            "disconnect candidate",
            disconnect_candidate.candidate_type == "INVESTIGATE_DISCONNECT"
            and disconnect_candidate.evidence["stale_count"] == 1,
        )
    )
    reconnect = make_history(
        envelope(90, 19, body=payload(90)),
        envelope(
            91,
            20,
            condition="RECONNECTED",
            body=payload(91),
        ),
    )
    _, reconnect_candidate = generate(reconnect)
    checks.append(
        check(
            "reconnect candidate",
            reconnect_candidate.candidate_type == "INVESTIGATE_DISCONNECT"
            and reconnect_candidate.evidence["reconnect_count"] == 1,
        )
    )

    schema_mismatch = make_history(
        envelope(100, 21, body=payload(100)),
        envelope(
            None,
            22,
            status="UNKNOWN",
            condition="SCHEMA_MISMATCH",
            body=None,
        ),
    )
    _, schema_candidate = generate(schema_mismatch)
    checks.append(
        check(
            "schema mismatch candidate",
            schema_candidate.candidate_type == "INVESTIGATE_SCHEMA_MISMATCH"
            and schema_candidate.evidence["schema_mismatch_count"] == 1,
        )
    )

    runtime_change = make_history(
        envelope(
            110,
            23,
            body=payload(110, r_exec=100.0, f_rt=0.5, active_synapses=7),
        ),
        envelope(
            111,
            24,
            body=payload(111, r_exec=101.5, f_rt=0.55, active_synapses=7),
        ),
    )
    _, runtime_candidate = generate(runtime_change)
    checks.append(
        check(
            "runtime change candidate",
            runtime_candidate.candidate_type == "INVESTIGATE_RUNTIME_CHANGE"
            and runtime_candidate.evidence["r_exec_delta"] == 1.5
            and runtime_candidate.evidence["f_rt_delta"] == 0.05,
        )
    )

    checks.append(
        check(
            "evidence traceability",
            stable_candidate.evidence["source_history_h256"]
            == stable_candidate.source_history_h256
            and stable_candidate.evidence["source_trend_h256"]
            == stable_candidate.source_trend_h256
            and stable_candidate.source_history_h256
            == stable_trend.source_history_h256,
        )
    )
    bad_entity_trend = replace(stable_trend, entity_id="QUEEN-X72-OTHER")
    try:
        X72DecisionCandidate().generate(stable, bad_entity_trend)
    except ValueError as exc:
        bad_entity_rejected = "entity_id" in str(exc)
    else:
        bad_entity_rejected = False
    checks.append(check("bad entity rejected", bad_entity_rejected))

    bad_trend_hash = replace(stable_trend, trend_h256="0" * 64)
    try:
        X72DecisionCandidate().generate(stable, bad_trend_hash)
    except ValueError:
        bad_trend_hash_rejected = True
    else:
        bad_trend_hash_rejected = False
    checks.append(check("bad source trend h256 rejected", bad_trend_hash_rejected))

    bad_history_hash = replace(stable_trend, source_history_h256="0" * 64)
    try:
        X72DecisionCandidate().generate(stable, bad_history_hash)
    except ValueError as exc:
        bad_history_hash_rejected = "source_history_h256" in str(exc)
    else:
        bad_history_hash_rejected = False
    checks.append(check("bad source history h256 rejected", bad_history_hash_rejected))

    before_records = [record.to_dict() for record in repair_closed.records]
    before_history_report = repair_closed.deterministic_report()
    repair_trend = X72TrendAnalyzer().analyze(repair_closed)
    before_trend = repair_trend.to_dict()

    first = X72DecisionCandidate().generate(repair_closed, repair_trend)
    second = X72DecisionCandidate().generate(repair_closed, repair_trend)

    checks.append(
        check(
            "deterministic candidate",
            first.to_dict() == second.to_dict()
            and first.candidate_h256 == second.candidate_h256,
        )
    )
    checks.append(
        check(
            "inputs immutable",
            before_records == [record.to_dict() for record in repair_closed.records]
            and before_history_report == repair_closed.deterministic_report()
            and before_trend == repair_trend.to_dict(),
        )
    )
    try:
        first.evidence["tamper"] = True  # type: ignore[index]
    except TypeError:
        evidence_immutable = True
    else:
        evidence_immutable = False
    checks.append(check("evidence immutable", evidence_immutable))

    encoded = json.dumps(first.to_dict(), sort_keys=True, separators=(",", ":"))
    checks.append(
        check(
            "candidate frame serializable",
            '"candidate_h256"' in encoded
            and len(first.candidate_h256) == 64
            and first.candidate_type in {
                "NO_CHANGE",
                "OBSERVE_MORE",
                "VERIFY_INTEGRITY",
                "INVESTIGATE_FAULT",
                "INVESTIGATE_REPAIR",
                "INVESTIGATE_DISCONNECT",
                "INVESTIGATE_SCHEMA_MISMATCH",
                "INVESTIGATE_RUNTIME_CHANGE",
            },
        )
    )

    checks.append(
        check(
            "read only invariants",
            X72DecisionCandidate.READ_ONLY is True
            and X72DecisionCandidate.NO_MUTATION_TRANSPORT is True
            and X72DecisionCandidate.NO_ACTION_EXECUTION is True
            and X72DecisionCandidate.DETERMINISTIC is True,
        )
    )

    source = (ROOT / "decision_candidate" / "candidate.py").read_text(
        encoding="utf-8"
    )
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
            "no mutation transport or local Queen",
            not any(token in source for token in forbidden),
        )
    )

    public_methods = {
        name
        for name, value in inspect.getmembers(
            X72DecisionCandidate, predicate=inspect.isfunction
        )
        if not name.startswith("_")
    }
    checks.append(
        check(
            "no action execution surface",
            public_methods == {"generate"},
            detail=str(sorted(public_methods)),
        )
    )

    report = {
        "schema": "ANTMUX-X72-DECISION-CANDIDATE-ACCEPTANCE-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "checks_failed": sum(1 for item in checks if not item["ok"]),
        "candidate_h256": first.candidate_h256,
        "verdict": "PASS" if all(item["ok"] for item in checks) else "FAIL",
        "checks": checks,
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    if result["verdict"] != "PASS":
        raise SystemExit(1)
