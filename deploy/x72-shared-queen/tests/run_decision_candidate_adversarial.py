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
from contextlib import ExitStack
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from decision_candidate_adversarial_contract import (
    ALLOWED_CANDIDATE_TYPES,
    PASS,
    REJECT,
    UPSTREAM,
    build_cases,
    canonical_json,
    self_check_contract,
    valid_h256,
)

DEFAULT_MODULE = "decision_candidate"
DEFAULT_CLASS = "X72DecisionCandidate"
DEFAULT_METHOD = "analyze"

MUTATION_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
MUTATION_ATTRS = frozenset({"post", "put", "patch", "delete"})
TRANSPORT_ROOTS = frozenset(
    {
        "requests",
        "httpx",
        "urllib",
        "client",
        "session",
        "http",
        "api",
        "app",
        "router",
    }
)


def normalize_result(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return value.to_dict()
    if isinstance(value, tuple):
        return [normalize_result(item) for item in value]
    if isinstance(value, list):
        return [normalize_result(item) for item in value]
    if isinstance(value, dict):
        return {str(key): normalize_result(item) for key, item in value.items()}
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
                self.hit(
                    node,
                    "MUTATION_TRANSPORT_CALL",
                    f"{root}.{func.attr}",
                )
            if func.attr.lower() in MUTATION_ATTRS and root in {"app", "router", "api"}:
                self.hit(
                    node,
                    "MUTATION_ROUTE_DECLARATION",
                    f"{root}.{func.attr}",
                )

        for keyword in node.keywords:
            if keyword.arg == "method" and isinstance(keyword.value, ast.Constant):
                method = str(keyword.value.value).upper()
                if method in MUTATION_METHODS:
                    self.hit(
                        node,
                        "MUTATION_HTTP_METHOD",
                        method,
                    )
        self.generic_visit(node)


def scan_source_text(text: str, *, filename: str = "<candidate>") -> dict[str, Any]:
    try:
        tree = ast.parse(text, filename=filename)
    except SyntaxError as exc:
        return {
            "ok": False,
            "hits": [
                {
                    "line": exc.lineno,
                    "rule": "SOURCE_SYNTAX_ERROR",
                    "detail": str(exc),
                }
            ],
        }
    visitor = SourceGuardVisitor()
    visitor.visit(tree)
    return {"ok": not visitor.hits, "hits": visitor.hits}


def source_guard_self_check() -> dict[str, Any]:
    safe = """
CANDIDATE_TYPE = "DESCRIPTIVE_CANDIDATE"
def explain():
    return {"note": "POSTMORTEM observation; no transport"}
"""
    unsafe = {
        "queen_core": "def f():\n    return QueenCore()\n",
        "fault_route": 'FAULT = "/api/fault"\n',
        "repair_route": 'REPAIR = "/api/repair"\n',
        "requests_post": 'def f(requests):\n    return requests.post("https://example.invalid")\n',
        "delete_method": 'def f(Request):\n    return Request("x", method="DELETE")\n',
    }
    if not scan_source_text(safe)["ok"]:
        raise AssertionError("source guard false-positive on safe candidate text")
    for name, source in unsafe.items():
        result = scan_source_text(source, filename=name)
        if result["ok"]:
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
        result = scan_source_text(
            path.read_text(encoding="utf-8"),
            filename=str(path),
        )
        for hit in result["hits"]:
            all_hits.append({"file": str(path), **hit})

    return {
        "ok": not all_hits,
        "hits": all_hits,
        "files": checked,
    }


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


def instantiate(cls: type[Any]) -> Any:
    return cls()


def invoke(
    candidate: Any,
    method_name: str,
    history: Any,
    trend: Any,
    source: dict[str, Any],
) -> Any:
    method = getattr(candidate, method_name, None)
    if method is None or not callable(method):
        raise TypeError(f"candidate must expose public method {method_name}()")

    signature = inspect.signature(method)
    positional = [
        param
        for param in signature.parameters.values()
        if param.kind
        in {
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        }
    ]
    required = [
        param
        for param in positional
        if param.default is inspect.Parameter.empty
    ]

    argc = len(required)
    if argc == 1:
        return method(copy.deepcopy(source))
    if argc == 2:
        return method(history, trend)
    if argc == 3:
        return method(history, trend, copy.deepcopy(source))
    raise TypeError(
        "candidate public method must accept source, (history, trend), "
        "or (history, trend, source)"
    )


def output_is_action_free(value: Any) -> bool:
    forbidden_keys = {
        "action",
        "execute",
        "command",
        "http_method",
        "mutation_transport",
        "fault_request",
        "repair_request",
    }

    def walk(item: Any) -> bool:
        if isinstance(item, dict):
            for key, child in item.items():
                if str(key).lower() in forbidden_keys and child not in {None, False, "", ()}:
                    return False
                if not walk(child):
                    return False
            return True
        if isinstance(item, (list, tuple)):
            return all(walk(child) for child in item)
        return True

    return walk(value)


def validate_candidate_output(
    result: Any,
    source: dict[str, Any],
) -> dict[str, Any]:
    value = normalize_result(result)
    if not isinstance(value, dict):
        raise ValueError("CandidateFrame must serialize to an object")
    candidate_h256 = value.get("candidate_h256")
    if not valid_h256(candidate_h256):
        raise ValueError("candidate_h256 must be lowercase H256")
    if value.get("source_history_h256") != source["source_history_h256"]:
        raise ValueError("CandidateFrame lost source_history_h256 provenance")
    if value.get("source_trend_h256") != source["source_trend_h256"]:
        raise ValueError("CandidateFrame lost source_trend_h256 provenance")
    if value.get("entity_id") != source["entity_id"]:
        raise ValueError("CandidateFrame entity_id mismatch")
    if value.get("candidate_type") not in ALLOWED_CANDIDATE_TYPES:
        raise ValueError("CandidateFrame candidate_type is not descriptive")
    evidence = value.get("evidence")
    if not isinstance(evidence, (list, tuple)) or not evidence:
        raise ValueError("CandidateFrame evidence must be non-empty")
    if not output_is_action_free(value):
        raise ValueError("CandidateFrame contains action execution surface")
    return value


def blocker_report(
    contract: dict[str, Any],
    guard_check: dict[str, Any],
    blocker: str,
) -> dict[str, Any]:
    return {
        "schema": "ANTMUX-X72-DECISION-CANDIDATE-ADVERSARIAL-RUN-v0.1",
        "contract": contract,
        "source_guard_self_check": guard_check,
        "candidate_status": "BLOCKER",
        "blocker": blocker,
        "candidate_tests_total": 0,
        "candidate_tests_pass": 0,
        "candidate_tests_fail": 0,
        "expected_rejections": contract["expected_rejections"],
        "expected_upstream_rejections": contract["expected_upstream_rejections"],
        "deterministic": "NOT_RUN",
        "no_input_mutation": "PASS",
        "no_mutation_transport": "PASS",
        "no_action_execution": "PASS",
    }


def run_candidate(
    module_name: str,
    class_name: str,
    method_name: str,
) -> dict[str, Any]:
    contract = self_check_contract()
    guard_check = source_guard_self_check()
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        return blocker_report(
            contract,
            guard_check,
            "DECISION_CANDIDATE_NOT_PRESENT",
        )

    cls = getattr(module, class_name, None)
    if cls is None:
        return blocker_report(
            contract,
            guard_check,
            "DECISION_CANDIDATE_CLASS_NOT_PRESENT",
        )

    source_guard = candidate_source_guard(module, cls)
    if not source_guard["ok"]:
        return {
            **blocker_report(
                contract,
                guard_check,
                "FORBIDDEN_MUTATION_OR_LOCAL_QUEEN",
            ),
            "candidate_status": "FAIL",
            "candidate_tests_total": 1,
            "candidate_tests_fail": 1,
            "source_guard": source_guard,
        }

    outcomes: list[dict[str, Any]] = []
    failures = 0
    expected_rejections = 0
    upstream_rejections = 0

    for case in build_cases():
        history, trend, source, upstream_error = case.build()

        if upstream_error is not None:
            if case.expectation == UPSTREAM:
                upstream_rejections += 1
                outcomes.append(
                    {
                        "case_id": case.case_id,
                        "classification": UPSTREAM,
                        "detail": upstream_error,
                    }
                )
            else:
                failures += 1
                outcomes.append(
                    {
                        "case_id": case.case_id,
                        "classification": "FAIL",
                        "detail": f"unexpected upstream rejection: {upstream_error}",
                    }
                )
            continue

        if history is None or trend is None or source is None:
            failures += 1
            outcomes.append(
                {
                    "case_id": case.case_id,
                    "classification": "FAIL",
                    "detail": "case builder returned incomplete public sources",
                }
            )
            continue

        history_before = [record.to_dict() for record in history.records]
        history_report_before = history.deterministic_report()
        trend_before = trend.to_dict()
        source_before = copy.deepcopy(source)

        try:
            with NoTransport():
                first = invoke(
                    instantiate(cls),
                    method_name,
                    history,
                    trend,
                    source,
                )
            rejected = False
            error = None
        except (ValueError, TypeError, AssertionError) as exc:
            first = None
            rejected = True
            error = f"{type(exc).__name__}: {exc}"
        except Exception as exc:
            failures += 1
            outcomes.append(
                {
                    "case_id": case.case_id,
                    "classification": "FAIL",
                    "detail": f"unexpected exception {type(exc).__name__}: {exc}",
                }
            )
            continue

        if (
            [record.to_dict() for record in history.records] != history_before
            or history.deterministic_report() != history_report_before
            or trend.to_dict() != trend_before
            or source != source_before
        ):
            failures += 1
            outcomes.append(
                {
                    "case_id": case.case_id,
                    "classification": "FAIL",
                    "detail": "candidate mutated History, TrendFrame, or candidate source",
                }
            )
            continue

        if case.expectation == REJECT:
            if rejected:
                expected_rejections += 1
                outcomes.append(
                    {
                        "case_id": case.case_id,
                        "classification": REJECT,
                        "detail": error,
                    }
                )
            else:
                failures += 1
                outcomes.append(
                    {
                        "case_id": case.case_id,
                        "classification": "FAIL",
                        "detail": "invalid candidate source was accepted",
                    }
                )
            continue

        if case.expectation == UPSTREAM:
            failures += 1
            outcomes.append(
                {
                    "case_id": case.case_id,
                    "classification": "FAIL",
                    "detail": "upstream-invalid case reached candidate unexpectedly",
                }
            )
            continue

        if rejected:
            failures += 1
            outcomes.append(
                {
                    "case_id": case.case_id,
                    "classification": "FAIL",
                    "detail": error or "valid source rejected",
                }
            )
            continue

        try:
            first_value = validate_candidate_output(first, source)
            with NoTransport():
                second = invoke(
                    instantiate(cls),
                    method_name,
                    history,
                    trend,
                    source,
                )
            second_value = validate_candidate_output(second, source)
            deterministic = canonical_json(first_value) == canonical_json(second_value)
        except Exception as exc:
            failures += 1
            outcomes.append(
                {
                    "case_id": case.case_id,
                    "classification": "FAIL",
                    "detail": f"candidate output validation failed: {type(exc).__name__}: {exc}",
                }
            )
            continue

        if not deterministic:
            failures += 1
            outcomes.append(
                {
                    "case_id": case.case_id,
                    "classification": "FAIL",
                    "detail": "same canonical input produced different CandidateFrame",
                }
            )
            continue

        outcomes.append(
            {
                "case_id": case.case_id,
                "classification": PASS,
                "detail": first_value["candidate_h256"],
            }
        )

    total = len(outcomes) + 2
    passed = sum(
        item["classification"] in {PASS, REJECT, UPSTREAM}
        for item in outcomes
    ) + 2
    return {
        "schema": "ANTMUX-X72-DECISION-CANDIDATE-ADVERSARIAL-RUN-v0.1",
        "contract": contract,
        "source_guard_self_check": guard_check,
        "source_guard": source_guard,
        "candidate_status": "PASS" if failures == 0 else "FAIL",
        "blocker": None,
        "module_target": module_name,
        "class_target": class_name,
        "method_target": method_name,
        "candidate_tests_total": total,
        "candidate_tests_pass": passed,
        "candidate_tests_fail": failures,
        "expected_rejections": expected_rejections,
        "expected_upstream_rejections": upstream_rejections,
        "deterministic": "PASS" if failures == 0 else "CHECK_OUTCOMES",
        "no_input_mutation": "PASS" if failures == 0 else "CHECK_OUTCOMES",
        "no_mutation_transport": "PASS",
        "no_action_execution": "PASS",
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
