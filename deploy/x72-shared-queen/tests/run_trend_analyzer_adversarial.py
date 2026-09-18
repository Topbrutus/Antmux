from __future__ import annotations

import argparse
import copy
import importlib
import inspect
import json
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from observation_adapter import ObservationEnvelope
from observation_history import X72ObservationHistory
from trend_analyzer_adversarial_contract import (
    MAX_WINDOW,
    build_cases,
    canonical_json,
    self_check_contract,
)

DEFAULT_MODULE = "trend_analyzer"
DEFAULT_CLASS = "X72TrendAnalyzer"

EXPECTED_UPSTREAM_CASES = frozenset(
    {
        "entity_change_mid_window",
        "tick_regression",
        "numeric_wrong_type",
        "synapse_count_wrong_type",
        "history_order_reversed",
        "nan_r_exec",
        "inf_f_rt",
    }
)
EXPECTED_CANDIDATE_REJECTIONS = frozenset()


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
    raise TypeError(f"unsupported analyzer result type: {type(value).__name__}")


def structured_rejection(result: Any) -> bool:
    value = normalize_result(result)
    if not isinstance(value, dict):
        return False
    if value.get("accepted") is False:
        return True
    status = str(value.get("status", "")).upper()
    condition = str(value.get("condition", "")).upper()
    verdict = str(value.get("verdict", "")).upper()
    return (
        status in {"INVALID", "REJECTED", "EXPECTED_REJECTION"}
        or verdict in {"INVALID", "REJECTED", "EXPECTED_REJECTION"}
        or condition.startswith("INVALID")
        or condition.startswith("REJECT")
    )


def instantiate(cls: type[Any]) -> Any:
    return cls()


PAYLOAD_FIELDS = (
    "entity_id",
    "tick_count",
    "queen_mode",
    "integrity_match",
    "protected_h256",
    "reference_h256",
    "r_exec",
    "f_rt",
    "active_synapses",
    "event_count",
)


def record_to_envelope(item: dict[str, Any]) -> ObservationEnvelope:
    payload: dict[str, Any] = {}
    if "source_schema" in item:
        payload["source"] = item["source_schema"]
    for field in PAYLOAD_FIELDS:
        if field in item:
            payload[field] = copy.deepcopy(item[field])

    return ObservationEnvelope(
        observed_at_utc=str(item.get("observed_at", "")),
        entity_id=item.get("entity_id"),
        source_schema=str(item.get("source_schema", "")),
        source_endpoint=str(item.get("source_endpoint", "")),
        freshness_ms=0,
        status=str(item.get("status", "")),
        condition=str(item.get("condition", "")),
        payload=payload,
        error=None if item.get("status") == "FRESH" else str(item.get("condition", "")),
    )


def build_public_history(
    source_records: tuple[dict[str, Any], ...],
) -> tuple[X72ObservationHistory, list[dict[str, Any]], int]:
    history = X72ObservationHistory(capacity=MAX_WINDOW)
    upstream_rejections: list[dict[str, Any]] = []
    evictions = 0

    for index, source in enumerate(source_records):
        frame = record_to_envelope(source)
        result = history.append(frame)
        if not result.accepted:
            upstream_rejections.append(
                {
                    "index": index,
                    "condition": result.condition,
                    "error": result.error,
                }
            )
            break
        if result.evicted_sequence_id is not None:
            evictions += 1

    return history, upstream_rejections, evictions


def invoke(analyzer: Any, history: X72ObservationHistory) -> Any:
    if not hasattr(analyzer, "analyze") or not callable(analyzer.analyze):
        raise TypeError("candidate must expose analyze(history: X72ObservationHistory)")
    return analyzer.analyze(history)


def candidate_source_guard(module: Any, cls: type[Any]) -> dict[str, Any]:
    paths: list[Path] = []
    module_file = getattr(module, "__file__", None)
    if module_file:
        paths.append(Path(module_file))
    try:
        cls_file = inspect.getsourcefile(cls)
        if cls_file:
            paths.append(Path(cls_file))
    except (TypeError, OSError):
        pass

    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(set(paths))
        if path.exists()
    )
    forbidden = {
        "QueenCore": "local Queen authority",
        "/api/fault": "fault mutation transport",
        "/api/repair": "repair mutation transport",
        "urllib.": "HTTP transport",
        "requests.": "HTTP transport",
        "websockets.": "WebSocket transport",
        'method="POST"': "POST transport",
        'method="PUT"': "PUT transport",
        'method="PATCH"': "PATCH transport",
        'method="DELETE"': "DELETE transport",
    }
    hits = {token: reason for token, reason in forbidden.items() if token in text}
    return {
        "ok": not hits,
        "hits": hits,
        "files": [str(path) for path in sorted(set(paths))],
    }


def blocker_report(contract: dict[str, Any], blocker: str) -> dict[str, Any]:
    return {
        "schema": "ANTMUX-X72-TREND-ANALYZER-ADVERSARIAL-RUN-v0.2",
        "contract": contract,
        "candidate": "BLOCKER",
        "blocker": blocker,
        "tests_total": contract["tests_total"],
        "tests_pass": contract["tests_pass"],
        "tests_fail": 0,
        "expected_rejections": contract["expected_rejections"],
        "upstream_rejections": 0,
    }


def run_candidate(module_name: str, class_name: str) -> dict[str, Any]:
    contract = self_check_contract()
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        return blocker_report(contract, f"TREND_ANALYZER_NOT_PRESENT:{module_name}")

    cls = getattr(module, class_name, None)
    if cls is None:
        return blocker_report(contract, f"TREND_ANALYZER_CLASS_NOT_PRESENT:{class_name}")

    guard = candidate_source_guard(module, cls)
    if not guard["ok"]:
        return {
            "schema": "ANTMUX-X72-TREND-ANALYZER-ADVERSARIAL-RUN-v0.2",
            "contract": contract,
            "candidate": "FAIL",
            "blocker": "FORBIDDEN_MUTATION_OR_LOCAL_QUEEN",
            "source_guard": guard,
            "tests_total": 1,
            "tests_pass": 0,
            "tests_fail": 1,
            "expected_rejections": 0,
            "upstream_rejections": 0,
        }

    outcomes: list[dict[str, Any]] = []
    failures = 0
    upstream_count = 0
    candidate_rejection_count = 0


    for case in build_cases():
        source_before = copy.deepcopy(case.records)
        history, upstream, evictions = build_public_history(case.records)

        if case.records != source_before:
            failures += 1
            outcomes.append(
                {
                    "case_id": case.case_id,
                    "classification": "FAIL",
                    "detail": "source adversarial records mutated while building History",
                }
            )
            continue

        if upstream:
            if case.case_id in EXPECTED_UPSTREAM_CASES:
                upstream_count += 1
                outcomes.append(
                    {
                        "case_id": case.case_id,
                        "classification": "EXPECTED_REJECTION_UPSTREAM",
                        "detail": upstream[0],
                    }
                )
            else:
                failures += 1
                outcomes.append(
                    {
                        "case_id": case.case_id,
                        "classification": "FAIL",
                        "detail": {
                            "unexpected_upstream_rejection": upstream[0],
                        },
                    }
                )
            continue

        if case.case_id in EXPECTED_UPSTREAM_CASES:
            failures += 1
            outcomes.append(
                {
                    "case_id": case.case_id,
                    "classification": "FAIL",
                    "detail": "History should have rejected this case but accepted it",
                }
            )
            continue

        before_records = [record.to_dict() for record in history.records]
        before_report = history.deterministic_report()
        analyzer = instantiate(cls)
        rejected = False
        error = None
        result = None
        try:
            result = invoke(analyzer, history)
            rejected = structured_rejection(result)
        except (ValueError, TypeError, AssertionError) as exc:
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

        after_records = [record.to_dict() for record in history.records]
        after_report = history.deterministic_report()
        if before_records != after_records or before_report != after_report:
            failures += 1
            outcomes.append(
                {
                    "case_id": case.case_id,
                    "classification": "FAIL",
                    "detail": "candidate mutated X72ObservationHistory input",
                }
            )
            continue


        if case.case_id in EXPECTED_CANDIDATE_REJECTIONS:
            if rejected:
                candidate_rejection_count += 1
                outcomes.append(
                    {
                        "case_id": case.case_id,
                        "classification": "EXPECTED_REJECTION",
                        "detail": error or "structured candidate rejection",
                    }
                )
            else:
                failures += 1
                outcomes.append(
                    {
                        "case_id": case.case_id,
                        "classification": "FAIL",
                        "detail": "non-finite numeric input was accepted",
                    }
                )
            continue

        if rejected:
            failures += 1
            outcomes.append(
                {
                    "case_id": case.case_id,
                    "classification": "FAIL",
                    "detail": error or "candidate rejected a valid bounded History",
                }
            )
            continue

        try:
            second = invoke(instantiate(cls), history)
            first_norm = normalize_result(result)
            second_norm = normalize_result(second)
            deterministic = canonical_json(first_norm) == canonical_json(second_norm)
        except Exception as exc:
            deterministic = False
            error = f"second-run {type(exc).__name__}: {exc}"

        if not deterministic:
            failures += 1
            outcomes.append(
                {
                    "case_id": case.case_id,
                    "classification": "FAIL",
                    "detail": error or "non-deterministic result across identical History",
                }
            )
            continue

        detail: dict[str, Any] = {
            "records_in_history": len(history.records),
            "evictions": evictions,
        }
        if case.case_id == "over_capacity" and (
            len(history.records) != MAX_WINDOW or evictions < 1
        ):
            failures += 1
            outcomes.append(
                {
                    "case_id": case.case_id,
                    "classification": "FAIL",
                    "detail": "bounded History did not evict oldest record",
                }
            )
            continue

        outcomes.append(
            {
                "case_id": case.case_id,
                "classification": "PASS",
                "detail": detail,
            }
        )


    meta_checks = [
        {
            "case_id": "source_guard",
            "classification": "PASS" if guard["ok"] else "FAIL",
            "detail": guard,
        },
        {
            "case_id": "public_interface_alignment",
            "classification": "PASS",
            "detail": "candidate invoked only as analyze(X72ObservationHistory)",
        },
    ]
    failures += sum(1 for item in meta_checks if item["classification"] == "FAIL")
    outcomes.extend(meta_checks)

    passed = sum(
        1
        for item in outcomes
        if item["classification"]
        in {"PASS", "EXPECTED_REJECTION", "EXPECTED_REJECTION_UPSTREAM"}
    )
    return {
        "schema": "ANTMUX-X72-TREND-ANALYZER-ADVERSARIAL-RUN-v0.2",
        "contract": contract,
        "candidate": "PASS" if failures == 0 else "FAIL",
        "blocker": None,
        "module_target": module_name,
        "class_target": class_name,
        "interface_alignment": "PASS",
        "source_guard": guard,
        "tests_total": len(outcomes),
        "tests_pass": passed,
        "tests_fail": failures,
        "expected_rejections": upstream_count + candidate_rejection_count,
        "upstream_rejections": upstream_count,
        "candidate_rejections": candidate_rejection_count,
        "deterministic": "PASS" if failures == 0 else "CHECK_OUTCOMES",
        "no_input_mutation": "PASS"
        if not any(
            item["classification"] == "FAIL"
            and "mutat" in str(item["detail"]).lower()
            for item in outcomes
        )
        else "FAIL",
        "outcomes": outcomes,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=DEFAULT_MODULE)
    parser.add_argument("--class-name", default=DEFAULT_CLASS)
    parser.add_argument("--report")
    parser.add_argument("--require-candidate", action="store_true")
    args = parser.parse_args()

    report = run_candidate(args.module, args.class_name)
    if args.report:
        Path(args.report).write_text(
            json.dumps(report, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    print(json.dumps(report, sort_keys=True))

    if report.get("candidate") == "FAIL":
        raise SystemExit(1)
    if args.require_candidate and report.get("candidate") == "BLOCKER":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
