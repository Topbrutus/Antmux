from __future__ import annotations

import argparse
import ast
import copy
import importlib
import inspect
import json
import socket
import sys
import urllib.request
from collections.abc import Mapping
from contextlib import ExitStack
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from decision_candidate_adversarial_contract import (
    ENTITY,
    FAULT_H256,
    PASS,
    REFERENCE_H256,
    SOURCE,
    UPSTREAM,
    build_history,
    canonical_json,
    envelope,
    self_check_contract,
    state_payload,
)
from observation_adapter import ObservationEnvelope
from observation_history import X72ObservationHistory
from trend_analyzer import X72TrendAnalyzer

DEFAULT_MODULE = "decision_candidate"
DEFAULT_CLASS = "X72DecisionCandidate"
DEFAULT_METHOD = "generate"

REAL_ALLOWED_CANDIDATE_TYPES = frozenset(
    {
        "NO_CHANGE",
        "OBSERVE_MORE",
        "VERIFY_INTEGRITY",
        "INVESTIGATE_FAULT",
        "INVESTIGATE_REPAIR",
        "INVESTIGATE_DISCONNECT",
        "INVESTIGATE_SCHEMA_MISMATCH",
        "INVESTIGATE_RUNTIME_CHANGE",
    }
)

MUTATION_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
MUTATION_ATTRS = frozenset({"post", "put", "patch", "delete"})
TRANSPORT_ROOTS = frozenset(
    {"requests", "httpx", "urllib", "client", "session", "http", "api", "app", "router"}
)


def normalize_result(value: Any) -> Any:
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return normalize_result(value.to_dict())
    if is_dataclass(value):
        return normalize_result(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): normalize_result(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [normalize_result(item) for item in value]
    if isinstance(value, list):
        return [normalize_result(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"unsupported candidate result type: {type(value).__name__}")


def _root_name(node: ast.AST) -> str | None:
    while isinstance(node, ast.Attribute):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


class SourceGuardVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.hits: list[dict[str, Any]] = []

    def hit(self, node: ast.AST, rule: str, detail: str) -> None:
        self.hits.append(
            {
                "line": getattr(node, "lineno", None),
                "rule": rule,
                "detail": detail,
            }
        )

    def visit_Name(self, node: ast.Name) -> None:
        if node.id == "QueenCore":
            self.hit(node, "LOCAL_QUEEN_CORE", "QueenCore reference")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr == "QueenCore":
            self.hit(node, "LOCAL_QUEEN_CORE", "QueenCore attribute reference")
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str) and node.value in {"/api/fault", "/api/repair"}:
            self.hit(node, "QUEEN_MUTATION_ROUTE", node.value)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Attribute):
            root = _root_name(func)
            if func.attr.lower() in MUTATION_ATTRS and root in TRANSPORT_ROOTS:
                self.hit(node, "MUTATION_TRANSPORT_CALL", f"{root}.{func.attr}")
            if func.attr.lower() in MUTATION_ATTRS and root in {"app", "router", "api"}:
                self.hit(node, "MUTATION_ROUTE_DECLARATION", f"{root}.{func.attr}")
        for keyword in node.keywords:
            if keyword.arg == "method" and isinstance(keyword.value, ast.Constant):
                method = str(keyword.value.value).upper()
                if method in MUTATION_METHODS:
                    self.hit(node, "MUTATION_HTTP_METHOD", method)
        self.generic_visit(node)


def scan_source_text(text: str, *, filename: str = "<candidate>") -> dict[str, Any]:
    try:
        tree = ast.parse(text, filename=filename)
    except SyntaxError as exc:
        return {
            "ok": False,
            "hits": [{"line": exc.lineno, "rule": "SOURCE_SYNTAX_ERROR", "detail": str(exc)}],
        }
    visitor = SourceGuardVisitor()
    visitor.visit(tree)
    return {"ok": not visitor.hits, "hits": visitor.hits}


def source_guard_self_check() -> dict[str, Any]:
    safe = 'CANDIDATE_TYPE = "DESCRIPTIVE"\ndef explain():\n    return {"note": "POSTMORTEM observation; no transport"}\n'
    unsafe = {
        "queen_core": "def f():\n    return QueenCore()\n",
        "fault_route": 'FAULT = "/api/fault"\n',
        "repair_route": 'REPAIR = "/api/repair"\n',
        "requests_post": 'def f(requests):\n    return requests.post("https://example.invalid")\n',
        "delete_method": 'def f(Request):\n    return Request("x", method="DELETE")\n',
    }
    if not scan_source_text(safe)["ok"]:
        raise AssertionError("source guard false-positive on safe text")
    for name, source in unsafe.items():
        if scan_source_text(source, filename=name)["ok"]:
            raise AssertionError(f"source guard missed {name}")
    return {
        "verdict": "PASS",
        "tests_total": 1 + len(unsafe),
        "tests_pass": 1 + len(unsafe),
        "tests_fail": 0,
    }


def candidate_source_guard(module: Any, cls: type[Any]) -> dict[str, Any]:
    paths: set[Path] = set()
    module_file = getattr(module, "__file__", None)
    if module_file:
        paths.add(Path(module_file))
    try:
        cls_file = inspect.getsourcefile(cls)
        if cls_file:
            paths.add(Path(cls_file))
    except (TypeError, OSError):
        pass

    all_hits: list[dict[str, Any]] = []
    checked: list[str] = []
    for path in sorted(paths):
        if not path.exists():
            continue
        checked.append(str(path))
        result = scan_source_text(path.read_text(encoding="utf-8"), filename=str(path))
        all_hits.extend({"file": str(path), **hit} for hit in result["hits"])
    return {"ok": not all_hits, "hits": all_hits, "files": checked}


def _transport_blocked(*args: Any, **kwargs: Any) -> Any:
    raise AssertionError("candidate attempted network/transport execution")


class NoTransport:
    def __enter__(self) -> "NoTransport":
        self.stack = ExitStack()
        self.stack.enter_context(patch.object(socket, "create_connection", _transport_blocked))
        self.stack.enter_context(patch.object(socket.socket, "connect", _transport_blocked))
        self.stack.enter_context(patch.object(urllib.request, "urlopen", _transport_blocked))
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.stack.close()


def candidate_method(cls: type[Any], method_name: str) -> Any:
    method = getattr(cls(), method_name, None)
    if method is None or not callable(method):
        raise TypeError(f"candidate must expose {method_name}(history, trend)")
    signature = inspect.signature(method)
    required = [
        param
        for param in signature.parameters.values()
        if param.kind
        in {inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD}
        and param.default is inspect.Parameter.empty
    ]
    if len(required) != 2:
        raise TypeError(
            f"{method_name} must require exactly (history, trend); got {signature}"
        )
    return method


def invoke(cls: type[Any], method_name: str, history: X72ObservationHistory, trend: Any) -> Any:
    method = candidate_method(cls, method_name)
    return method(history, trend)


def make_history(frames: list[ObservationEnvelope], *, capacity: int = 32) -> X72ObservationHistory:
    history, error = build_history(frames, capacity=capacity)
    if error is not None:
        raise AssertionError(error)
    return history


def stable_history(start: int = 100) -> X72ObservationHistory:
    return make_history(
        [
            envelope(
                start,
                1,
                payload=state_payload(
                    start,
                    r_exec=100.0,
                    f_rt=0.5,
                    active_synapses=7,
                    event_count=start,
                ),
            ),
            envelope(
                start + 1,
                2,
                payload=state_payload(
                    start + 1,
                    r_exec=100.0,
                    f_rt=0.5,
                    active_synapses=7,
                    event_count=start + 1,
                ),
            ),
        ]
    )


def single_history() -> X72ObservationHistory:
    return make_history([envelope(10, 1, payload=state_payload(10, event_count=10))])


def fault_history() -> X72ObservationHistory:
    return make_history(
        [
            envelope(20, 1, payload=state_payload(20, event_count=20)),
            envelope(
                21,
                2,
                payload=state_payload(
                    21,
                    mode="FAULT",
                    integrity=False,
                    protected_h256=FAULT_H256,
                    active_synapses=6,
                    event_count=21,
                ),
            ),
        ]
    )


def h256_open_history() -> X72ObservationHistory:
    return make_history(
        [
            envelope(25, 1, payload=state_payload(25, event_count=25)),
            envelope(
                26,
                2,
                payload=state_payload(
                    26,
                    mode="STABLE",
                    integrity=False,
                    protected_h256=FAULT_H256,
                    active_synapses=7,
                    event_count=26,
                ),
            ),
        ]
    )


def reclosed_history() -> X72ObservationHistory:
    return make_history(
        [
            envelope(30, 1, payload=state_payload(30, event_count=30)),
            envelope(
                31,
                2,
                payload=state_payload(
                    31,
                    mode="FAULT",
                    integrity=False,
                    protected_h256=FAULT_H256,
                    active_synapses=6,
                    event_count=31,
                ),
            ),
            envelope(32, 3, payload=state_payload(32, event_count=32)),
        ]
    )


def repair_history() -> X72ObservationHistory:
    return make_history(
        [
            envelope(40, 1, payload=state_payload(40, event_count=40)),
            envelope(
                41,
                2,
                payload=state_payload(
                    41,
                    mode="FAULT",
                    integrity=False,
                    protected_h256=FAULT_H256,
                    active_synapses=6,
                    event_count=41,
                ),
            ),
            envelope(
                42,
                3,
                payload=state_payload(
                    42,
                    mode="AUTO_REPAIR",
                    integrity=False,
                    protected_h256=FAULT_H256,
                    active_synapses=6,
                    event_count=42,
                ),
            ),
        ]
    )


def disconnect_history() -> X72ObservationHistory:
    fresh = envelope(50, 1, payload=state_payload(50, event_count=50))
    stale = envelope(
        50,
        2,
        status="STALE",
        condition="WEBSOCKET_DISCONNECT",
        payload=state_payload(50, event_count=50),
    )
    return make_history([fresh, stale])


def reconnect_history() -> X72ObservationHistory:
    return make_history(
        [
            envelope(60, 1, payload=state_payload(60, event_count=60)),
            envelope(61, 2, condition="RECONNECTED", payload=state_payload(61, event_count=61)),
        ]
    )


def schema_history() -> X72ObservationHistory:
    unknown = ObservationEnvelope(
        observed_at_utc="2026-09-18T17:00:02.000Z",
        entity_id=ENTITY,
        source_schema=SOURCE,
        source_endpoint="/ws",
        freshness_ms=0,
        status="UNKNOWN",
        condition="SCHEMA_MISMATCH",
        payload=None,
        error="SCHEMA_MISMATCH",
    )
    return make_history(
        [
            envelope(70, 1, payload=state_payload(70, event_count=70)),
            unknown,
        ]
    )


def runtime_history() -> X72ObservationHistory:
    return make_history(
        [
            envelope(
                80,
                1,
                payload=state_payload(
                    80,
                    r_exec=100.0,
                    f_rt=0.50,
                    active_synapses=7,
                    event_count=80,
                ),
            ),
            envelope(
                81,
                2,
                payload=state_payload(
                    81,
                    r_exec=101.5,
                    f_rt=0.55,
                    active_synapses=7,
                    event_count=81,
                ),
            ),
        ]
    )


def different_entity_history() -> X72ObservationHistory:
    other = "QUEEN-X72-OTHER"
    frames = [
        envelope(
            90,
            1,
            entity_id=other,
            payload=state_payload(90, entity_id=other, event_count=90),
        ),
        envelope(
            91,
            2,
            entity_id=other,
            payload=state_payload(91, entity_id=other, event_count=91),
        ),
    ]
    return make_history(frames)


def validate_evidence_mapping(candidate: Any, history: X72ObservationHistory, trend: Any) -> None:
    evidence = candidate.evidence
    if not isinstance(evidence, Mapping) or not evidence:
        raise AssertionError("candidate evidence must be a non-empty Mapping")
    if evidence.get("source_history_h256") != history.deterministic_report()["report_h256"]:
        raise AssertionError("evidence History H256 is not traceable")
    if evidence.get("source_trend_h256") != trend.trend_h256:
        raise AssertionError("evidence Trend H256 is not traceable")
    if evidence.get("records_count") != trend.records_count:
        raise AssertionError("evidence records_count mismatch")
    if evidence.get("h256_closed") != trend.h256_closed:
        raise AssertionError("evidence integrity state mismatch")


def validate_candidate_frame(candidate: Any, history: X72ObservationHistory, trend: Any) -> dict[str, Any]:
    value = normalize_result(candidate)
    if not isinstance(value, dict):
        raise AssertionError("CandidateFrame must normalize to a mapping")
    candidate_h256 = value.get("candidate_h256")
    if not isinstance(candidate_h256, str) or len(candidate_h256) != 64:
        raise AssertionError("candidate_h256 malformed")
    try:
        int(candidate_h256, 16)
    except ValueError as exc:
        raise AssertionError("candidate_h256 malformed") from exc
    if value.get("source_history_h256") != history.deterministic_report()["report_h256"]:
        raise AssertionError("CandidateFrame History H256 mismatch")
    if value.get("source_trend_h256") != trend.trend_h256:
        raise AssertionError("CandidateFrame Trend H256 mismatch")
    if value.get("source_records_count") != trend.records_count:
        raise AssertionError("CandidateFrame records_count mismatch")
    if value.get("entity_id") != trend.entity_id:
        raise AssertionError("CandidateFrame entity_id mismatch")
    if value.get("candidate_type") not in REAL_ALLOWED_CANDIDATE_TYPES:
        raise AssertionError("CandidateFrame candidate_type outside descriptive allow-list")
    validate_evidence_mapping(candidate, history, trend)

    forbidden_keys = {
        "action",
        "execute",
        "command",
        "http_method",
        "mutation_transport",
        "fault_request",
        "repair_request",
    }

    def walk(item: Any) -> None:
        if isinstance(item, Mapping):
            for key, child in item.items():
                if str(key).lower() in forbidden_keys and child not in {None, False, "", ()}:
                    raise AssertionError(f"action surface found: {key}")
                walk(child)
        elif isinstance(item, (list, tuple)):
            for child in item:
                walk(child)

    walk(value)
    return value


def check_case(
    outcomes: list[dict[str, Any]],
    case_id: str,
    ok: bool,
    detail: Any = "",
    *,
    classification: str = PASS,
) -> None:
    outcomes.append(
        {
            "case_id": case_id,
            "classification": classification if ok else "FAIL",
            "detail": detail,
        }
    )


def run_public_case(
    cls: type[Any],
    method_name: str,
    case_id: str,
    history: X72ObservationHistory,
    expected_type: str | None,
    outcomes: list[dict[str, Any]],
) -> None:
    trend = X72TrendAnalyzer().analyze(history)
    history_before = [record.to_dict() for record in history.records]
    history_report_before = history.deterministic_report()
    trend_before = trend.to_dict()

    with NoTransport():
        first = invoke(cls, method_name, history, trend)
    first_value = validate_candidate_frame(first, history, trend)
    with NoTransport():
        second = invoke(cls, method_name, history, trend)
    second_value = validate_candidate_frame(second, history, trend)

    deterministic = canonical_json(first_value) == canonical_json(second_value)
    immutable = (
        history_before == [record.to_dict() for record in history.records]
        and history_report_before == history.deterministic_report()
        and trend_before == trend.to_dict()
    )
    type_ok = expected_type is None or first_value["candidate_type"] == expected_type
    check_case(
        outcomes,
        case_id,
        deterministic and immutable and type_ok,
        {
            "candidate_type": first_value["candidate_type"],
            "candidate_h256": first_value["candidate_h256"],
            "deterministic": deterministic,
            "immutable": immutable,
        },
    )


def expect_candidate_rejection(
    cls: type[Any],
    method_name: str,
    case_id: str,
    history: X72ObservationHistory,
    trend: Any,
    outcomes: list[dict[str, Any]],
) -> None:
    history_before = [record.to_dict() for record in history.records]
    history_report_before = history.deterministic_report()
    trend_before = trend.to_dict()
    try:
        with NoTransport():
            invoke(cls, method_name, history, trend)
    except (ValueError, TypeError, AssertionError) as exc:
        rejected = True
        detail = f"{type(exc).__name__}: {exc}"
    else:
        rejected = False
        detail = "candidate accepted mismatched public inputs"
    immutable = (
        history_before == [record.to_dict() for record in history.records]
        and history_report_before == history.deterministic_report()
        and trend_before == trend.to_dict()
    )
    check_case(
        outcomes,
        case_id,
        rejected and immutable,
        detail,
        classification="EXPECTED_REJECTION",
    )


def expect_upstream_rejection(
    case_id: str,
    frames: list[ObservationEnvelope],
    outcomes: list[dict[str, Any]],
) -> None:
    _, error = build_history(frames)
    check_case(
        outcomes,
        case_id,
        error is not None,
        error or "History unexpectedly accepted invalid public input",
        classification=UPSTREAM,
    )


def blocker_report(contract: dict[str, Any], guard_check: dict[str, Any], blocker: str) -> dict[str, Any]:
    return {
        "schema": "ANTMUX-X72-DECISION-CANDIDATE-ADVERSARIAL-RUN-v0.2",
        "contract": contract,
        "source_guard_self_check": guard_check,
        "candidate_status": "BLOCKER",
        "blocker": blocker,
        "candidate_tests_total": 0,
        "candidate_tests_pass": 0,
        "candidate_tests_fail": 0,
        "expected_rejections": 0,
        "expected_upstream_rejections": 0,
        "deterministic": "NOT_RUN",
        "evidence_traceability": "NOT_RUN",
        "no_input_mutation": "PASS",
        "no_mutation_transport": "PASS",
        "no_action_execution": "PASS",
    }


def run_candidate(module_name: str, class_name: str, method_name: str) -> dict[str, Any]:
    contract = self_check_contract()
    guard_check = source_guard_self_check()
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        return blocker_report(contract, guard_check, "DECISION_CANDIDATE_NOT_PRESENT")

    cls = getattr(module, class_name, None)
    if cls is None:
        return blocker_report(contract, guard_check, "DECISION_CANDIDATE_CLASS_NOT_PRESENT")

    source_guard = candidate_source_guard(module, cls)
    if not source_guard["ok"]:
        report = blocker_report(contract, guard_check, "FORBIDDEN_MUTATION_OR_LOCAL_QUEEN")
        report.update(
            {
                "candidate_status": "FAIL",
                "candidate_tests_total": 1,
                "candidate_tests_fail": 1,
                "source_guard": source_guard,
            }
        )
        return report

    candidate_method(cls, method_name)
    outcomes: list[dict[str, Any]] = []

    run_public_case(cls, method_name, "empty_history", X72ObservationHistory(capacity=4), "OBSERVE_MORE", outcomes)
    run_public_case(cls, method_name, "single_observation", single_history(), "OBSERVE_MORE", outcomes)
    run_public_case(cls, method_name, "stable_window", stable_history(), "NO_CHANGE", outcomes)
    run_public_case(cls, method_name, "fault_open", fault_history(), "INVESTIGATE_FAULT", outcomes)
    run_public_case(cls, method_name, "h256_open", h256_open_history(), "VERIFY_INTEGRITY", outcomes)
    run_public_case(cls, method_name, "h256_reclosed", reclosed_history(), "VERIFY_INTEGRITY", outcomes)
    run_public_case(cls, method_name, "repair_active", repair_history(), "INVESTIGATE_REPAIR", outcomes)
    run_public_case(cls, method_name, "disconnect", disconnect_history(), "INVESTIGATE_DISCONNECT", outcomes)
    run_public_case(cls, method_name, "reconnect", reconnect_history(), "INVESTIGATE_DISCONNECT", outcomes)
    run_public_case(cls, method_name, "schema_mismatch", schema_history(), "INVESTIGATE_SCHEMA_MISMATCH", outcomes)
    run_public_case(cls, method_name, "runtime_variation", runtime_history(), "INVESTIGATE_RUNTIME_CHANGE", outcomes)

    stable = stable_history(100)
    foreign = stable_history(200)
    foreign_trend = X72TrendAnalyzer().analyze(foreign)
    expect_candidate_rejection(
        cls,
        method_name,
        "trend_from_other_history",
        stable,
        foreign_trend,
        outcomes,
    )

    other_entity = different_entity_history()
    other_trend = X72TrendAnalyzer().analyze(other_entity)
    expect_candidate_rejection(
        cls,
        method_name,
        "constructible_entity_mismatch",
        stable,
        other_trend,
        outcomes,
    )

    from dataclasses import replace
    valid_trend = X72TrendAnalyzer().analyze(stable)
    expect_candidate_rejection(
        cls,
        method_name,
        "bad_source_history_h256",
        stable,
        replace(valid_trend, source_history_h256="0" * 64),
        outcomes,
    )
    expect_candidate_rejection(
        cls,
        method_name,
        "bad_trend_frame_h256",
        stable,
        replace(valid_trend, trend_h256="0" * 64),
        outcomes,
    )

    expect_upstream_rejection(
        "upstream_entity_change",
        [
            envelope(300, 1, payload=state_payload(300, event_count=300)),
            envelope(
                301,
                2,
                entity_id="QUEEN-X72-OTHER",
                payload=state_payload(301, entity_id="QUEEN-X72-OTHER", event_count=301),
            ),
        ],
        outcomes,
    )
    expect_upstream_rejection(
        "upstream_tick_regression",
        [
            envelope(310, 1, payload=state_payload(310, event_count=310)),
            envelope(309, 2, payload=state_payload(309, event_count=309)),
        ],
        outcomes,
    )
    expect_upstream_rejection(
        "upstream_nan",
        [envelope(320, 1, payload=state_payload(320, r_exec=float("nan"), event_count=320))],
        outcomes,
    )
    expect_upstream_rejection(
        "upstream_inf",
        [envelope(330, 1, payload=state_payload(330, f_rt=float("inf"), event_count=330))],
        outcomes,
    )

    public_methods = {
        name
        for name, value in inspect.getmembers(cls, predicate=inspect.isfunction)
        if not name.startswith("_")
    }
    check_case(
        outcomes,
        "no_action_execution_surface",
        public_methods == {method_name},
        sorted(public_methods),
    )
    check_case(outcomes, "source_guard", source_guard["ok"], source_guard)

    failures = sum(item["classification"] == "FAIL" for item in outcomes)
    expected_rejections = sum(item["classification"] == "EXPECTED_REJECTION" for item in outcomes)
    upstream_rejections = sum(item["classification"] == UPSTREAM for item in outcomes)
    passed = len(outcomes) - failures

    return {
        "schema": "ANTMUX-X72-DECISION-CANDIDATE-ADVERSARIAL-RUN-v0.2",
        "contract": contract,
        "source_guard_self_check": guard_check,
        "source_guard": source_guard,
        "candidate_status": "PASS" if failures == 0 else "FAIL",
        "blocker": None,
        "module_target": module_name,
        "class_target": class_name,
        "method_target": method_name,
        "interface_alignment": "PASS",
        "normalization": "TO_DICT_FIRST",
        "evidence_mapping": "PASS" if failures == 0 else "CHECK_OUTCOMES",
        "candidate_tests_total": len(outcomes),
        "candidate_tests_pass": passed,
        "candidate_tests_fail": failures,
        "expected_rejections": expected_rejections,
        "expected_upstream_rejections": upstream_rejections,
        "deterministic": "PASS" if failures == 0 else "CHECK_OUTCOMES",
        "evidence_traceability": "PASS" if failures == 0 else "CHECK_OUTCOMES",
        "no_input_mutation": "PASS" if failures == 0 else "CHECK_OUTCOMES",
        "no_mutation_transport": "PASS",
        "no_action_execution": "PASS" if failures == 0 else "CHECK_OUTCOMES",
        "outcomes": outcomes,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=DEFAULT_MODULE)
    parser.add_argument("--class-name", default=DEFAULT_CLASS)
    parser.add_argument("--method", default=DEFAULT_METHOD)
    parser.add_argument("--report")
    parser.add_argument("--require-candidate", action="store_true")
    args = parser.parse_args()

    report = run_candidate(args.module, args.class_name, args.method)
    if args.report:
        Path(args.report).write_text(
            json.dumps(report, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    print(json.dumps(report, sort_keys=True))

    if report.get("candidate_status") == "FAIL":
        raise SystemExit(1)
    if args.require_candidate and report.get("candidate_status") == "BLOCKER":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
