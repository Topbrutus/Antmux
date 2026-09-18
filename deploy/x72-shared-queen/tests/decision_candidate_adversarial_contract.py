from __future__ import annotations

import copy
import hashlib
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from observation_adapter import ObservationEnvelope
from observation_history import X72ObservationHistory
from trend_analyzer import X72TrendAnalyzer

ENTITY = "QUEEN-X72-0072"
SOURCE = "QUEEN_SERVER_V0_2"
REFERENCE_H256 = "49e75d92d8fde33f402c3b60482bc5dcf13c12f09bd8c07c7937961d42ceaff9"
FAULT_H256 = "f" * 64
CONTRACT_SCHEMA = "ANTMUX-X72-DECISION-CANDIDATE-ADVERSARIAL-CONTRACT-v0.1"

PASS = "PASS"
REJECT = "EXPECTED_REJECTION"
UPSTREAM = "EXPECTED_REJECTION_UPSTREAM"

ALLOWED_CANDIDATE_TYPES = frozenset(
    {
        "DESCRIPTIVE_CANDIDATE",
        "OBSERVATION_GAP",
        "INTEGRITY_ANOMALY",
        "SCHEMA_ANOMALY",
        "INSUFFICIENT_EVIDENCE",
    }
)


class ContractViolation(ValueError):
    pass


@dataclass(frozen=True)
class DecisionCase:
    case_id: str
    category: str
    expectation: str
    build: Callable[[], tuple[X72ObservationHistory | None, Any | None, dict[str, Any] | None, str | None]]
    rationale: str


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def canonical_h256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def valid_h256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value.lower() == value


def finite_nonnegative(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractViolation(f"{field} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise ContractViolation(f"{field} must be finite")
    if number < 0:
        raise ContractViolation(f"{field} must be >= 0")
    return number


def nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ContractViolation(f"{field} must be an integer")
    if value < 0:
        raise ContractViolation(f"{field} must be >= 0")
    return value


def state_payload(
    tick: Any,
    *,
    entity_id: str = ENTITY,
    mode: str = "STABLE",
    integrity: bool = True,
    protected_h256: str = REFERENCE_H256,
    r_exec: Any = 120.0,
    f_rt: Any = 0.5,
    active_synapses: Any = 7,
    event_count: Any = 0,
) -> dict[str, Any]:
    return {
        "source": SOURCE,
        "entity_id": entity_id,
        "tick_count": tick,
        "queen_mode": mode,
        "integrity_match": integrity,
        "protected_h256": protected_h256,
        "reference_h256": REFERENCE_H256,
        "r_exec": r_exec,
        "f_rt": f_rt,
        "active_synapses": active_synapses,
        "event_count": event_count,
    }


def envelope(
    tick: Any,
    second: int,
    *,
    entity_id: str = ENTITY,
    status: str = "FRESH",
    condition: str = "STREAM_STATE",
    payload: dict[str, Any] | None = None,
) -> ObservationEnvelope:
    if payload is None:
        payload = state_payload(tick, entity_id=entity_id, event_count=second)
    return ObservationEnvelope(
        observed_at_utc=f"2026-09-18T17:00:{second:02d}.000Z",
        entity_id=entity_id,
        source_schema=SOURCE,
        source_endpoint="/ws",
        freshness_ms=0,
        status=status,
        condition=condition,
        payload=payload,
        error=None if status == "FRESH" else condition,
    )


def build_history(
    frames: list[ObservationEnvelope],
    *,
    capacity: int = 32,
) -> tuple[X72ObservationHistory, str | None]:
    history = X72ObservationHistory(capacity=capacity)
    for frame in frames:
        result = history.append(frame)
        if not result.accepted:
            return history, result.error or result.condition
    return history, None


def baseline_history() -> X72ObservationHistory:
    frames = [
        envelope(
            100 + index,
            index,
            payload=state_payload(
                100 + index,
                r_exec=120.0 + index,
                f_rt=0.5 + index / 100.0,
                active_synapses=7,
                event_count=200 + index,
            ),
        )
        for index in range(3)
    ]
    history, error = build_history(frames)
    if error:
        raise AssertionError(error)
    return history


def analyze(history: X72ObservationHistory) -> Any:
    return X72TrendAnalyzer().analyze(history)


def trace_evidence(history: X72ObservationHistory, trend: Any) -> list[dict[str, Any]]:
    history_h256 = history.deterministic_report()["report_h256"]
    return [
        {
            "source": "history",
            "source_h256": history_h256,
            "path": "records",
        },
        {
            "source": "trend",
            "source_h256": trend.trend_h256,
            "path": "records_count",
        },
    ]


def decision_source(
    history: X72ObservationHistory,
    trend: Any,
    *,
    candidate_type: str | None = None,
    evidence: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    history_h256 = history.deterministic_report()["report_h256"]
    if candidate_type is None:
        if trend.records_count == 0:
            candidate_type = "INSUFFICIENT_EVIDENCE"
        elif trend.h256_closed is False:
            candidate_type = "INTEGRITY_ANOMALY"
        elif trend.schema_mismatch_count:
            candidate_type = "SCHEMA_ANOMALY"
        elif trend.stale_count and not trend.reconnect_count:
            candidate_type = "OBSERVATION_GAP"
        else:
            candidate_type = "DESCRIPTIVE_CANDIDATE"

    return {
        "entity_id": trend.entity_id,
        "source_history_h256": history_h256,
        "source_trend_h256": trend.trend_h256,
        "candidate_type": candidate_type,
        "evidence": copy.deepcopy(
            evidence if evidence is not None else trace_evidence(history, trend)
        ),
        "records_count": trend.records_count,
        "window_start_tick": trend.window_start_tick,
        "window_end_tick": trend.window_end_tick,
        "r_exec_mean": trend.r_exec_mean,
        "f_rt_mean": trend.f_rt_mean,
        "active_synapses_mean": trend.active_synapses_mean,
        "fresh_count": trend.fresh_count,
        "stale_count": trend.stale_count,
        "unknown_count": trend.unknown_count,
        "reconnect_count": trend.reconnect_count,
        "schema_mismatch_count": trend.schema_mismatch_count,
        "fault_interval_count": len(trend.fault_intervals),
        "repair_interval_count": len(trend.repair_intervals),
        "h256_closed": trend.h256_closed,
    }


def _check_optional_tick(value: Any, field: str) -> int | None:
    if value is None:
        return None
    return nonnegative_int(value, field)


def _check_optional_metric(value: Any, field: str) -> float | None:
    if value is None:
        return None
    return finite_nonnegative(value, field)


def validate_decision_source(
    source: dict[str, Any],
    history: X72ObservationHistory,
    trend: Any,
) -> dict[str, Any]:
    if not isinstance(source, dict):
        raise ContractViolation("decision source must be an object")

    required = {
        "entity_id",
        "source_history_h256",
        "source_trend_h256",
        "candidate_type",
        "evidence",
        "records_count",
        "window_start_tick",
        "window_end_tick",
        "r_exec_mean",
        "f_rt_mean",
        "active_synapses_mean",
        "fresh_count",
        "stale_count",
        "unknown_count",
        "reconnect_count",
        "schema_mismatch_count",
        "fault_interval_count",
        "repair_interval_count",
        "h256_closed",
    }
    missing = sorted(required.difference(source))
    if missing:
        raise ContractViolation("missing fields: " + ",".join(missing))

    history_h256 = history.deterministic_report()["report_h256"]
    trend_h256 = trend.trend_h256
    if not valid_h256(source["source_history_h256"]):
        raise ContractViolation("source_history_h256 malformed")
    if not valid_h256(source["source_trend_h256"]):
        raise ContractViolation("source_trend_h256 malformed")
    if source["source_history_h256"] != history_h256:
        raise ContractViolation("source_history_h256 is not traceable to History")
    if source["source_trend_h256"] != trend_h256:
        raise ContractViolation("source_trend_h256 is not traceable to TrendFrame")

    if source["entity_id"] != trend.entity_id:
        raise ContractViolation("entity_id disagrees with TrendFrame")
    if history.entity_id is not None and source["entity_id"] != history.entity_id:
        raise ContractViolation("entity_id disagrees with History")

    candidate_type = source["candidate_type"]
    if candidate_type not in ALLOWED_CANDIDATE_TYPES:
        raise ContractViolation("unknown candidate_type")

    records_count = nonnegative_int(source["records_count"], "records_count")
    if records_count != trend.records_count:
        raise ContractViolation("records_count disagrees with TrendFrame")

    start_tick = _check_optional_tick(source["window_start_tick"], "window_start_tick")
    end_tick = _check_optional_tick(source["window_end_tick"], "window_end_tick")
    if start_tick != trend.window_start_tick or end_tick != trend.window_end_tick:
        raise ContractViolation("tick window disagrees with TrendFrame")
    if start_tick is not None and end_tick is not None and end_tick < start_tick:
        raise ContractViolation("tick window regressed")

    for field in ("r_exec_mean", "f_rt_mean", "active_synapses_mean"):
        checked = _check_optional_metric(source[field], field)
        if checked != getattr(trend, field):
            raise ContractViolation(f"{field} disagrees with TrendFrame")
    active = source["active_synapses_mean"]
    if active is not None and float(active) > 7:
        raise ContractViolation("active_synapses_mean must be <= 7")

    for field in (
        "fresh_count",
        "stale_count",
        "unknown_count",
        "reconnect_count",
        "schema_mismatch_count",
        "fault_interval_count",
        "repair_interval_count",
    ):
        nonnegative_int(source[field], field)

    if source["fresh_count"] != trend.fresh_count:
        raise ContractViolation("fresh_count disagrees with TrendFrame")
    if source["stale_count"] != trend.stale_count:
        raise ContractViolation("stale_count disagrees with TrendFrame")
    if source["unknown_count"] != trend.unknown_count:
        raise ContractViolation("unknown_count disagrees with TrendFrame")
    if source["reconnect_count"] != trend.reconnect_count:
        raise ContractViolation("reconnect_count disagrees with TrendFrame")
    if source["schema_mismatch_count"] != trend.schema_mismatch_count:
        raise ContractViolation("schema_mismatch_count disagrees with TrendFrame")
    if source["fault_interval_count"] != len(trend.fault_intervals):
        raise ContractViolation("fault interval count disagrees with TrendFrame")
    if source["repair_interval_count"] != len(trend.repair_intervals):
        raise ContractViolation("repair interval count disagrees with TrendFrame")

    if source["h256_closed"] is not None and not isinstance(source["h256_closed"], bool):
        raise ContractViolation("h256_closed must be boolean or None")
    if source["h256_closed"] != trend.h256_closed:
        raise ContractViolation("h256_closed disagrees with TrendFrame")


    if source["repair_interval_count"] and not source["fault_interval_count"]:
        raise ContractViolation("repair evidence exists without prior fault evidence")
    if source["reconnect_count"] and not source["stale_count"]:
        raise ContractViolation("reconnect evidence exists without disconnect/stale evidence")
    if candidate_type == "INTEGRITY_ANOMALY" and source["h256_closed"] is not False:
        raise ContractViolation("integrity candidate has no H256 fault proof")
    if candidate_type == "OBSERVATION_GAP" and source["stale_count"] < 1:
        raise ContractViolation("observation-gap candidate has no disconnect evidence")
    if candidate_type == "SCHEMA_ANOMALY" and source["schema_mismatch_count"] < 1:
        raise ContractViolation("schema candidate has no schema mismatch evidence")
    if trend.records_count == 0 and candidate_type != "INSUFFICIENT_EVIDENCE":
        raise ContractViolation("empty TrendFrame requires INSUFFICIENT_EVIDENCE")

    evidence = source["evidence"]
    if not isinstance(evidence, list) or not evidence:
        raise ContractViolation("evidence must be a non-empty list")
    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            raise ContractViolation(f"evidence[{index}] must be an object")
        if set(item) != {"source", "source_h256", "path"}:
            raise ContractViolation(f"evidence[{index}] has unsupported fields")
        source_name = item["source"]
        if source_name not in {"history", "trend"}:
            raise ContractViolation(f"evidence[{index}] source unknown")
        expected_h256 = history_h256 if source_name == "history" else trend_h256
        if item["source_h256"] != expected_h256:
            raise ContractViolation(f"evidence[{index}] is not traceable")
        if not isinstance(item["path"], str) or not item["path"].strip():
            raise ContractViolation(f"evidence[{index}] path required")

    stable_evidence = sorted(
        copy.deepcopy(evidence),
        key=lambda item: canonical_json(item),
    )
    canonical_source = copy.deepcopy(source)
    canonical_source["evidence"] = stable_evidence
    return {
        "schema": "ANTMUX-X72-DECISION-CANDIDATE-SOURCE-v0.1",
        "source": canonical_source,
        "expected_candidate_h256": canonical_h256(canonical_source),
    }


def _valid_case() -> tuple[X72ObservationHistory, Any, dict[str, Any], None]:
    history = baseline_history()
    trend = analyze(history)
    return history, trend, decision_source(history, trend), None


def _empty_case() -> tuple[X72ObservationHistory, Any, dict[str, Any], None]:
    history = X72ObservationHistory(capacity=4)
    trend = analyze(history)
    return history, trend, decision_source(history, trend), None


def mutate_source(**changes: Any) -> Callable[[], tuple[X72ObservationHistory, Any, dict[str, Any], None]]:
    def build() -> tuple[X72ObservationHistory, Any, dict[str, Any], None]:
        history = baseline_history()
        trend = analyze(history)
        source = decision_source(history, trend)
        source.update(copy.deepcopy(changes))
        return history, trend, source, None
    return build


def upstream_case(frames: list[ObservationEnvelope]) -> Callable[[], tuple[X72ObservationHistory | None, Any | None, dict[str, Any] | None, str | None]]:
    def build() -> tuple[X72ObservationHistory | None, Any | None, dict[str, Any] | None, str | None]:
        history, error = build_history(copy.deepcopy(frames))
        if error:
            return history, None, None, error
        trend = analyze(history)
        return history, trend, decision_source(history, trend), None
    return build


def repair_without_fault_case() -> tuple[X72ObservationHistory, Any, dict[str, Any], None]:
    payload = state_payload(100, mode="REPAIR", event_count=1)
    history, error = build_history([envelope(100, 1, payload=payload)])
    if error:
        raise AssertionError(error)
    trend = analyze(history)
    return history, trend, decision_source(history, trend), None


def reconnect_without_disconnect_case() -> tuple[X72ObservationHistory, Any, dict[str, Any], None]:
    history, error = build_history(
        [
            envelope(100, 1),
            envelope(101, 2, condition="RECONNECTED"),
        ]
    )
    if error:
        raise AssertionError(error)
    trend = analyze(history)
    return history, trend, decision_source(history, trend), None


def disconnect_without_reconnect_case() -> tuple[X72ObservationHistory, Any, dict[str, Any], None]:
    fresh = envelope(100, 1)
    stale_payload = state_payload(100, event_count=1)
    stale = envelope(
        100,
        2,
        status="STALE",
        condition="WEBSOCKET_DISCONNECT",
        payload=stale_payload,
    )
    history, error = build_history([fresh, stale])
    if error:
        raise AssertionError(error)
    trend = analyze(history)
    return history, trend, decision_source(history, trend), None


def multiple_schema_mismatch_case() -> tuple[X72ObservationHistory, Any, dict[str, Any], None]:
    frames = [envelope(100, 1)]
    for second, endpoint in ((2, "/ws"), (3, "/api/state")):
        frames.append(
            ObservationEnvelope(
                observed_at_utc=f"2026-09-18T17:00:{second:02d}.000Z",
                entity_id=ENTITY,
                source_schema=SOURCE,
                source_endpoint=endpoint,
                freshness_ms=0,
                status="UNKNOWN",
                condition="SCHEMA_MISMATCH",
                payload=None,
                error="SCHEMA_MISMATCH",
            )
        )
    history, error = build_history(frames)
    if error:
        raise AssertionError(error)
    trend = analyze(history)
    source = decision_source(history, trend, candidate_type="SCHEMA_ANOMALY")
    return history, trend, source, None


def fault_without_proof_case() -> tuple[X72ObservationHistory, Any, dict[str, Any], None]:
    history = baseline_history()
    trend = analyze(history)
    source = decision_source(history, trend, candidate_type="INTEGRITY_ANOMALY")
    return history, trend, source, None


def evidence_reversed_case() -> tuple[X72ObservationHistory, Any, dict[str, Any], None]:
    history = baseline_history()
    trend = analyze(history)
    source = decision_source(history, trend)
    source["evidence"] = list(reversed(source["evidence"]))
    return history, trend, source, None


def source_hash_mismatch(field: str) -> Callable[[], tuple[X72ObservationHistory, Any, dict[str, Any], None]]:
    def build() -> tuple[X72ObservationHistory, Any, dict[str, Any], None]:
        history = baseline_history()
        trend = analyze(history)
        source = decision_source(history, trend)
        source[field] = "0" * 64
        return history, trend, source, None
    return build


def build_cases() -> tuple[DecisionCase, ...]:
    base = baseline_history()
    first = base.records[0].to_dict()
    return (
        DecisionCase("valid_baseline", "baseline", PASS, _valid_case, "valid traceable descriptive source"),
        DecisionCase("empty_history", "history", PASS, _empty_case, "empty history must remain descriptive and non-actioning"),
        DecisionCase("source_history_h256_absent", "h256", REJECT, mutate_source(source_history_h256=None), "missing History provenance"),
        DecisionCase("source_trend_h256_absent", "h256", REJECT, mutate_source(source_trend_h256=None), "missing Trend provenance"),
        DecisionCase("history_h256_malformed", "h256", REJECT, mutate_source(source_history_h256="xyz"), "malformed H256"),
        DecisionCase("trend_h256_malformed", "h256", REJECT, mutate_source(source_trend_h256="123"), "malformed H256"),
        DecisionCase("history_h256_untraceable", "h256", REJECT, source_hash_mismatch("source_history_h256"), "History H256 not source-derived"),
        DecisionCase("trend_h256_untraceable", "h256", REJECT, source_hash_mismatch("source_trend_h256"), "Trend H256 not source-derived"),
        DecisionCase("entity_incoherent", "entity", REJECT, mutate_source(entity_id="QUEEN-X72-OTHER"), "entity mismatch"),
        DecisionCase("partial_trend_source", "trend", REJECT, mutate_source(records_count=None), "partial Trend source"),
        DecisionCase("contradictory_records_count", "trend", REJECT, mutate_source(records_count=999), "records_count contradiction"),
        DecisionCase("unknown_candidate_type", "candidate", REJECT, mutate_source(candidate_type="EXECUTE_REPAIR"), "candidate type outside descriptive contract"),
        DecisionCase("empty_evidence", "evidence", REJECT, mutate_source(evidence=[]), "candidate must be traceable"),
        DecisionCase("untraceable_evidence", "evidence", REJECT, mutate_source(evidence=[{"source":"history","source_h256":"0"*64,"path":"records"}]), "evidence hash mismatch"),
        DecisionCase("fault_without_proof", "fault_repair", REJECT, fault_without_proof_case, "integrity candidate requires transported proof"),
        DecisionCase("repair_without_fault", "fault_repair", REJECT, repair_without_fault_case, "repair evidence without fault"),
        DecisionCase("disconnect_without_reconnect", "disconnect", PASS, disconnect_without_reconnect_case, "descriptive observation gap"),
        DecisionCase("reconnect_without_disconnect", "reconnect", REJECT, reconnect_without_disconnect_case, "reconnect requires prior disconnect evidence"),
        DecisionCase("multiple_schema_mismatch", "schema", PASS, multiple_schema_mismatch_case, "traceable schema anomaly"),
        DecisionCase("runtime_negative", "numeric", REJECT, mutate_source(r_exec_mean=-1.0), "negative runtime metric"),
        DecisionCase("active_synapses_impossible", "numeric", REJECT, mutate_source(active_synapses_mean=8.0), "impossible synapse count"),
        DecisionCase("numeric_wrong_type", "numeric", REJECT, mutate_source(f_rt_mean="0.5"), "numeric type discipline"),
        DecisionCase("records_count_bool", "numeric", REJECT, mutate_source(records_count=True), "bool is not integer count"),
        DecisionCase("tick_negative", "numeric", REJECT, mutate_source(window_start_tick=-1), "negative tick"),
        DecisionCase("tick_regressive_source", "numeric", REJECT, mutate_source(window_start_tick=200, window_end_tick=100), "regressive source tick window"),
        DecisionCase("evidence_order_reversed", "determinism", PASS, evidence_reversed_case, "evidence ordering canonicalized"),
        DecisionCase(
            "upstream_entity_change",
            "upstream",
            UPSTREAM,
            upstream_case([
                envelope(100, 1),
                envelope(101, 2, entity_id="QUEEN-X72-OTHER", payload=state_payload(101, entity_id="QUEEN-X72-OTHER", event_count=2)),
            ]),
            "History rejects entity change",
        ),
        DecisionCase(
            "upstream_tick_regression",
            "upstream",
            UPSTREAM,
            upstream_case([envelope(100, 1), envelope(99, 2, payload=state_payload(99, event_count=2))]),
            "History rejects regressive official tick",
        ),
        DecisionCase(
            "upstream_nan",
            "upstream",
            UPSTREAM,
            upstream_case([envelope(100, 1, payload=state_payload(100, r_exec=float("nan"), event_count=1))]),
            "History canonical JSON rejects NaN",
        ),
        DecisionCase(
            "upstream_inf",
            "upstream",
            UPSTREAM,
            upstream_case([envelope(100, 1, payload=state_payload(100, f_rt=float("inf"), event_count=1))]),
            "History canonical JSON rejects infinity",
        ),
        DecisionCase(
            "upstream_bool_tick",
            "upstream",
            UPSTREAM,
            upstream_case([envelope(True, 1, payload=state_payload(True, event_count=1))]),
            "History rejects bool as tick integer",
        ),
        DecisionCase(
            "upstream_numeric_string",
            "upstream",
            UPSTREAM,
            upstream_case([envelope(100, 1, payload=state_payload(100, r_exec="120", event_count=1))]),
            "History rejects numeric string",
        ),
    )


def classify_case(case: DecisionCase) -> dict[str, Any]:
    history, trend, source, upstream_error = case.build()
    if upstream_error is not None:
        observed = UPSTREAM
        detail = upstream_error
    else:
        if history is None or trend is None or source is None:
            raise AssertionError(f"{case.case_id}: incomplete case builder")
        history_before = [record.to_dict() for record in history.records]
        history_report_before = history.deterministic_report()
        trend_before = trend.to_dict()
        source_before = copy.deepcopy(source)
        try:
            result = validate_decision_source(source, history, trend)
            observed = PASS
            detail = result["expected_candidate_h256"]
        except ContractViolation as exc:
            observed = REJECT
            detail = str(exc)

        if [record.to_dict() for record in history.records] != history_before:
            raise AssertionError(f"{case.case_id}: History mutated")
        if history.deterministic_report() != history_report_before:
            raise AssertionError(f"{case.case_id}: History report mutated")
        if trend.to_dict() != trend_before:
            raise AssertionError(f"{case.case_id}: TrendFrame mutated")
        if source != source_before:
            raise AssertionError(f"{case.case_id}: source input mutated")

    if observed != case.expectation:
        raise AssertionError(
            f"{case.case_id}: expected {case.expectation}, got {observed}: {detail}"
        )
    return {
        "case_id": case.case_id,
        "category": case.category,
        "expectation": case.expectation,
        "classification": observed,
        "detail": detail,
    }


def self_check_contract() -> dict[str, Any]:
    cases = build_cases()
    if len({case.case_id for case in cases}) != len(cases):
        raise AssertionError("duplicate decision case_id")

    outcomes = [classify_case(case) for case in cases]

    history = baseline_history()
    trend = analyze(history)
    source = decision_source(history, trend)
    first = validate_decision_source(copy.deepcopy(source), history, trend)
    second = validate_decision_source(copy.deepcopy(source), history, trend)
    if first != second:
        raise AssertionError("same canonical source produced non-deterministic contract output")

    reversed_source = copy.deepcopy(source)
    reversed_source["evidence"] = list(reversed(reversed_source["evidence"]))
    reversed_result = validate_decision_source(reversed_source, history, trend)
    if first["expected_candidate_h256"] != reversed_result["expected_candidate_h256"]:
        raise AssertionError("evidence order changed canonical candidate seed")

    manifest_rows = sorted(
        (
            case.case_id,
            case.category,
            case.expectation,
            case.rationale,
        )
        for case in cases
    )
    manifest_h256 = canonical_h256(manifest_rows)

    expected_rejections = sum(item["classification"] == REJECT for item in outcomes)
    upstream_rejections = sum(item["classification"] == UPSTREAM for item in outcomes)
    meta_tests = 4
    return {
        "schema": CONTRACT_SCHEMA,
        "verdict": "PASS",
        "contract_tests_total": len(outcomes) + meta_tests,
        "contract_tests_pass": len(outcomes) + meta_tests,
        "contract_tests_fail": 0,
        "case_count": len(outcomes),
        "expected_rejections": expected_rejections,
        "expected_upstream_rejections": upstream_rejections,
        "deterministic": "PASS",
        "evidence_traceability": "PASS",
        "no_input_mutation": "PASS",
        "manifest_h256": manifest_h256,
        "outcomes": outcomes,
    }


if __name__ == "__main__":
    print(json.dumps(self_check_contract(), sort_keys=True))
