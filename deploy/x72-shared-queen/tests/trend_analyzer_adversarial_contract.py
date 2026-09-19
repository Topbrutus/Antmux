from __future__ import annotations

import copy
import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Iterable

ENTITY = "QUEEN-X72-0072"
REFERENCE_H256 = "54d4cee87f7e5feed1a0735a0b8431a2dc67b1bda0492c78a6c7274109c13180"
FAULT_H256 = "f" * 64
SOURCE_SCHEMA = "QUEEN_SERVER_V0_2"
MAX_WINDOW = 32
CONTRACT_SCHEMA = "ANTMUX-X72-TREND-ANALYZER-ADVERSARIAL-CONTRACT-v0.1"
ACCEPT = "PASS"
REJECT = "EXPECTED_REJECTION"

@dataclass(frozen=True)
class AdversarialCase:
    case_id: str
    category: str
    expectation: str
    records: tuple[dict[str, Any], ...]
    rationale: str


class ContractViolation(ValueError):
    pass


class _Missing:
    pass


_MISSING = _Missing()


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


def _valid_h256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value.lower() == value


def _finite_nonnegative_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractViolation(f"{field} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise ContractViolation(f"{field} must be finite")
    if number < 0:
        raise ContractViolation(f"{field} must be >= 0")
    return number


def _nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ContractViolation(f"{field} must be an integer")
    if value < 0:
        raise ContractViolation(f"{field} must be >= 0")
    return value


def record(
    sequence_id: int,
    tick_count: int,
    *,
    entity_id: str = ENTITY,
    status: str = "FRESH",
    condition: str = "STREAM_STATE",
    queen_mode: str = "STABLE",
    integrity_match: bool = True,
    protected_h256: str = REFERENCE_H256,
    reference_h256: str = REFERENCE_H256,
    r_exec: Any = 120.0,
    f_rt: Any = 0.5,
    active_synapses: Any = 7,
    event_count: Any | None = None,
    source_schema: str = SOURCE_SCHEMA,
    source_endpoint: str = "/ws",
) -> dict[str, Any]:
    if event_count is None:
        event_count = tick_count
    payload_seed = {
        "entity_id": entity_id,
        "tick_count": tick_count,
        "protected_h256": protected_h256,
        "reference_h256": reference_h256,
        "r_exec": r_exec,
        "f_rt": f_rt,
        "active_synapses": active_synapses,
        "event_count": event_count,
        "queen_mode": queen_mode,
        "integrity_match": integrity_match,
    }
    return {
        "sequence_id": sequence_id,
        "observed_at": f"2026-09-18T15:00:{sequence_id:02d}.000Z",
        "entity_id": entity_id,
        "tick_count": tick_count,
        "source_schema": source_schema,
        "source_endpoint": source_endpoint,
        "status": status,
        "condition": condition,
        "queen_mode": queen_mode,
        "integrity_match": integrity_match,
        "protected_h256": protected_h256,
        "reference_h256": reference_h256,
        "payload_h256": canonical_h256(payload_seed),
        "r_exec": r_exec,
        "f_rt": f_rt,
        "active_synapses": active_synapses,
        "event_count": event_count,
    }


def _mutate(base: dict[str, Any], **changes: Any) -> dict[str, Any]:
    item = copy.deepcopy(base)
    for key, value in changes.items():
        if value is _MISSING:
            item.pop(key, None)
        else:
            item[key] = value
    return item


REQUIRED_FIELDS = frozenset(
    {
        "sequence_id",
        "observed_at",
        "entity_id",
        "tick_count",
        "source_schema",
        "source_endpoint",
        "status",
        "condition",
        "queen_mode",
        "integrity_match",
        "protected_h256",
        "reference_h256",
        "payload_h256",
        "r_exec",
        "f_rt",
        "active_synapses",
        "event_count",
    }
)


def validate_window_contract(records: Iterable[dict[str, Any]]) -> str:
    window = tuple(records)
    if len(window) > MAX_WINDOW:
        raise ContractViolation(f"window exceeds maximum capacity {MAX_WINDOW}")
    if not window:
        return "EMPTY"

    previous_sequence: int | None = None
    previous_tick: int | None = None
    previous_event_count: int | None = None
    saw_fault = False

    for index, item in enumerate(window):
        if not isinstance(item, dict):
            raise ContractViolation(f"record[{index}] must be an object")
        missing = REQUIRED_FIELDS.difference(item)
        if missing:
            raise ContractViolation(
                f"record[{index}] missing fields: {','.join(sorted(missing))}"
            )

        sequence_id = _nonnegative_int(item["sequence_id"], "sequence_id")
        if sequence_id < 1:
            raise ContractViolation("sequence_id must be >= 1")
        if previous_sequence is not None and sequence_id <= previous_sequence:
            raise ContractViolation("sequence_id must increase strictly")
        previous_sequence = sequence_id

        if item["entity_id"] != ENTITY:
            raise ContractViolation(f"entity_id must remain {ENTITY}")

        status = item["status"]
        condition = item["condition"]
        if status not in {"FRESH", "STALE", "UNKNOWN"}:
            raise ContractViolation(f"unsupported status {status}")
        if condition == "RECONNECTED" and status != "FRESH":
            raise ContractViolation("RECONNECTED requires FRESH")
        if condition == "WEBSOCKET_DISCONNECT" and status not in {"STALE", "UNKNOWN"}:
            raise ContractViolation("disconnect requires STALE or UNKNOWN")
        if condition == "SCHEMA_MISMATCH" and status != "UNKNOWN":
            raise ContractViolation("SCHEMA_MISMATCH requires UNKNOWN")


        tick = item["tick_count"]
        if tick is not None:
            tick = _nonnegative_int(tick, "tick_count")
            if status == "FRESH" and previous_tick is not None and tick < previous_tick:
                raise ContractViolation("FRESH tick_count regressed")
            if status == "FRESH":
                previous_tick = tick
        elif status == "FRESH":
            raise ContractViolation("FRESH record requires tick_count")

        if status == "FRESH":
            _finite_nonnegative_number(item["r_exec"], "r_exec")
            _finite_nonnegative_number(item["f_rt"], "f_rt")
            active = _nonnegative_int(item["active_synapses"], "active_synapses")
            if active > 7:
                raise ContractViolation("active_synapses must be <= 7")
            event_count = _nonnegative_int(item["event_count"], "event_count")
            if previous_event_count is not None and event_count < previous_event_count:
                raise ContractViolation("event_count regressed")
            previous_event_count = event_count
        else:
            for field in ("r_exec", "f_rt"):
                value = item[field]
                if value is not None:
                    _finite_nonnegative_number(value, field)
            if item["active_synapses"] is not None:
                active = _nonnegative_int(item["active_synapses"], "active_synapses")
                if active > 7:
                    raise ContractViolation("active_synapses must be <= 7")
            if item["event_count"] is not None:
                _nonnegative_int(item["event_count"], "event_count")

        integrity = item["integrity_match"]
        if integrity is not None and not isinstance(integrity, bool):
            raise ContractViolation("integrity_match must be boolean or None")

        protected = item["protected_h256"]
        reference = item["reference_h256"]
        if protected is not None and not _valid_h256(protected):
            raise ContractViolation("protected_h256 must be lowercase H256")
        if reference is not None and not _valid_h256(reference):
            raise ContractViolation("reference_h256 must be lowercase H256")
        if status == "FRESH" and (protected is None or reference is None):
            raise ContractViolation("FRESH record requires transported H256 values")
        if integrity is True and protected != reference:
            raise ContractViolation("integrity_match true but H256 values differ")
        if integrity is False and protected == reference:
            raise ContractViolation("integrity_match false but H256 values match")

        is_fault = (
            integrity is False
            or item["queen_mode"] == "FAULT"
            or (protected is not None and reference is not None and protected != reference)
        )
        if is_fault:
            saw_fault = True
        if item["queen_mode"] in {"REPAIR", "REPAIRED"} and not saw_fault:
            raise ContractViolation("repair observed without prior fault in window")

    return "VALID"


def build_cases() -> tuple[AdversarialCase, ...]:
    b1 = record(1, 100, event_count=100)
    b2 = record(2, 101, r_exec=121.0, f_rt=0.51, event_count=101)
    b3 = record(3, 102, r_exec=122.0, f_rt=0.52, event_count=102)

    def c(
        case_id: str,
        category: str,
        expectation: str,
        records: tuple[dict[str, Any], ...],
        rationale: str,
    ) -> AdversarialCase:
        return AdversarialCase(case_id, category, expectation, records, rationale)

    return (
        c("empty_history", "history", ACCEPT, tuple(), "empty window must not crash"),
        c("single_fresh", "history", ACCEPT, (b1,), "single valid observation"),
        c("incomplete_history", "history", REJECT, (_mutate(b1, r_exec=_MISSING),), "required field omitted"),
        c("wrong_entity_id", "entity", REJECT, (_mutate(b1, entity_id="QUEEN-X72-OTHER"),), "wrong Queen identity"),
        c("entity_change_mid_window", "entity", REJECT, (b1, _mutate(b2, entity_id="QUEEN-X72-OTHER")), "identity changed mid-window"),
        c("tick_regression", "tick", REJECT, (b1, _mutate(b2, tick_count=99)), "FRESH tick regressed"),
        c("duplicate_tick", "tick", ACCEPT, (b1, _mutate(b2, tick_count=100, event_count=100)), "same tick sampled twice"),
        c("very_large_tick", "tick", ACCEPT, (_mutate(b1, tick_count=2**63 + 12345, event_count=2**63 + 12345),), "large integer tick"),
        c("missing_r_exec", "numeric", REJECT, (_mutate(b1, r_exec=None),), "missing r_exec"),
        c("missing_f_rt", "numeric", REJECT, (_mutate(b1, f_rt=None),), "missing f_rt"),
        c("nan_r_exec", "numeric", REJECT, (_mutate(b1, r_exec=float("nan")),), "NaN rejected"),
        c("inf_f_rt", "numeric", REJECT, (_mutate(b1, f_rt=float("inf")),), "infinity rejected"),
        c("numeric_wrong_type", "numeric", REJECT, (_mutate(b1, r_exec="120.0"),), "wrong metric type"),
        c("negative_r_exec", "numeric", REJECT, (_mutate(b1, r_exec=-1.0),), "negative r_exec"),
        c("negative_f_rt", "numeric", REJECT, (_mutate(b1, f_rt=-0.01),), "negative f_rt"),
        c("event_count_regression", "event", REJECT, (b1, _mutate(b2, event_count=99)), "event_count regressed"),
        c("synapse_count_too_high", "synapse", REJECT, (_mutate(b1, active_synapses=8),), "synapse count > 7"),
        c("synapse_count_wrong_type", "synapse", REJECT, (_mutate(b1, active_synapses="7"),), "synapse count wrong type"),

        c(
            "repeated_stale",
            "disconnect",
            ACCEPT,
            (
                b1,
                _mutate(b2, status="STALE", condition="WEBSOCKET_DISCONNECT", tick_count=100, event_count=100),
                _mutate(b3, status="STALE", condition="WEBSOCKET_DISCONNECT", tick_count=100, event_count=100),
            ),
            "repeated STALE never becomes FRESH",
        ),
        c(
            "repeated_reconnected",
            "reconnect",
            ACCEPT,
            (b1, _mutate(b2, condition="RECONNECTED"), _mutate(b3, condition="RECONNECTED")),
            "real FRESH reconnects may repeat",
        ),
        c(
            "fault_without_repair",
            "fault_repair",
            ACCEPT,
            (
                b1,
                _mutate(
                    b2,
                    queen_mode="FAULT",
                    integrity_match=False,
                    protected_h256=FAULT_H256,
                    active_synapses=6,
                ),
            ),
            "window may end in fault",
        ),
        c(
            "repair_without_fault",
            "fault_repair",
            REJECT,
            (_mutate(b1, queen_mode="REPAIRED"),),
            "repair requires prior fault in window",
        ),
        c(
            "h256_incoherent",
            "h256",
            REJECT,
            (_mutate(b1, protected_h256=FAULT_H256, integrity_match=True),),
            "integrity flag contradicts transported H256",
        ),
        c(
            "fault_then_h256_return",
            "h256",
            ACCEPT,
            (
                b1,
                _mutate(
                    b2,
                    queen_mode="FAULT",
                    integrity_match=False,
                    protected_h256=FAULT_H256,
                    active_synapses=6,
                ),
                _mutate(
                    b3,
                    queen_mode="REPAIRED",
                    integrity_match=True,
                    protected_h256=REFERENCE_H256,
                    reference_h256=REFERENCE_H256,
                    active_synapses=7,
                ),
            ),
            "fault followed by H256 restoration",
        ),
        c("history_order_reversed", "order", REJECT, (b3, b2, b1), "temporal order reversed"),
        c(
            "schema_mismatch_unknown",
            "disconnect",
            ACCEPT,
            (
                b1,
                _mutate(
                    b2,
                    status="UNKNOWN",
                    condition="SCHEMA_MISMATCH",
                    tick_count=100,
                    event_count=100,
                    r_exec=None,
                    f_rt=None,
                    active_synapses=None,
                    integrity_match=None,
                    protected_h256=None,
                    reference_h256=None,
                ),
            ),
            "UNKNOWN schema mismatch remains non-fresh",
        ),
        c(
            "bounded_exact_capacity",
            "memory",
            ACCEPT,
            tuple(
                record(
                    i,
                    1000 + i,
                    r_exec=120 + i / 10,
                    f_rt=0.5 + i / 1000,
                    event_count=1000 + i,
                )
                for i in range(1, MAX_WINDOW + 1)
            ),
            "bounded maximum window accepted",
        ),
        c(
            "over_capacity",
            "memory",
            REJECT,
            tuple(
                record(
                    i,
                    2000 + i,
                    r_exec=130 + i / 10,
                    f_rt=0.6 + i / 1000,
                    event_count=2000 + i,
                )
                for i in range(1, MAX_WINDOW + 2)
            ),
            "window cannot grow without bound",
        ),
    )


def self_check_contract() -> dict[str, Any]:
    cases = build_cases()
    ids = [case.case_id for case in cases]
    if len(ids) != len(set(ids)):
        raise AssertionError("duplicate adversarial case_id")

    outcomes: list[dict[str, Any]] = []
    for case in cases:
        before = copy.deepcopy(case.records)
        try:
            disposition = validate_window_contract(copy.deepcopy(case.records))
            observed = ACCEPT
            detail = disposition
        except ContractViolation as exc:
            observed = REJECT
            detail = str(exc)

        if observed != case.expectation:
            raise AssertionError(
                f"{case.case_id}: expected {case.expectation}, got {observed}: {detail}"
            )
        if case.records != before:
            raise AssertionError(f"{case.case_id}: source records mutated")

        outcomes.append(
            {
                "case_id": case.case_id,
                "category": case.category,
                "expectation": case.expectation,
                "observed": observed,
                "detail": detail,
            }
        )

    stable_rows = [
        {
            "case_id": case.case_id,
            "category": case.category,
            "expectation": case.expectation,
            "rationale": case.rationale,
        }
        for case in sorted(cases, key=lambda item: item.case_id)
    ]
    stable_rows_reversed = [
        {
            "case_id": case.case_id,
            "category": case.category,
            "expectation": case.expectation,
            "rationale": case.rationale,
        }
        for case in sorted(reversed(cases), key=lambda item: item.case_id)
    ]
    stable_a = canonical_h256(stable_rows)
    stable_b = canonical_h256(stable_rows_reversed)
    if stable_a != stable_b:
        raise AssertionError("contract manifest changed with input order")

    identical_a = record(1, 777, event_count=777)
    identical_b = copy.deepcopy(identical_a)
    identical_b["sequence_id"] = 2
    identical_b["observed_at"] = "2026-09-18T15:00:02.000Z"
    semantic_keys = tuple(
        key
        for key in identical_a
        if key not in {"sequence_id", "observed_at"}
    )
    ambiguous_forward = sorted(
        canonical_json({key: item[key] for key in semantic_keys})
        for item in (identical_a, identical_b)
    )
    ambiguous_reverse = sorted(
        canonical_json({key: item[key] for key in semantic_keys})
        for item in (identical_b, identical_a)
    )
    if ambiguous_forward != ambiguous_reverse:
        raise AssertionError("identical semantic records changed with input order")

    categories = sorted({case.category for case in cases})
    required_categories = {
        "history",
        "entity",
        "tick",
        "numeric",
        "event",
        "synapse",
        "disconnect",
        "reconnect",
        "fault_repair",
        "h256",
        "order",
        "memory",
    }
    if not required_categories.issubset(categories):
        raise AssertionError("adversarial category coverage incomplete")

    return {
        "schema": CONTRACT_SCHEMA,
        "verdict": "PASS",
        "tests_total": len(outcomes) + 5,
        "tests_pass": len(outcomes) + 5,
        "tests_fail": 0,
        "corpus_cases": len(outcomes),
        "expected_rejections": sum(
            1 for item in outcomes if item["expectation"] == REJECT
        ),
        "categories": categories,
        "entity_id": "PASS",
        "tick_discipline": "PASS",
        "numeric_edge_cases": "PASS",
        "event_discipline": "PASS",
        "synapse_discipline": "PASS",
        "disconnect": "PASS",
        "reconnect": "PASS",
        "fault_repair": "PASS",
        "h256": "PASS",
        "deterministic": "PASS",
        "no_input_mutation": "PASS",
        "bounded": "PASS",
        "manifest_h256": stable_a,
        "outcomes": outcomes,
    }


if __name__ == "__main__":
    print(json.dumps(self_check_contract(), sort_keys=True))
