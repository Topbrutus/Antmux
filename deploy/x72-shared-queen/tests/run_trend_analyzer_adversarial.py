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

from observation_history import X72HistoryRecord
from trend_analyzer_adversarial_contract import (
    ACCEPT,
    REJECT,
    MAX_WINDOW,
    build_cases,
    canonical_json,
    self_check_contract,
)

DEFAULT_MODULE = "observation_trend"
DEFAULT_CLASS = "X72TrendAnalyzer"


def to_history_record(item: dict[str, Any]) -> X72HistoryRecord:
    return X72HistoryRecord(**copy.deepcopy(item))


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
        return {str(k): normalize_result(v) for k, v in value.items()}
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
    try:
        return cls()
    except TypeError:
        return cls(max_records=MAX_WINDOW)


def invoke(analyzer: Any, records: tuple[X72HistoryRecord, ...]) -> Any:
    if hasattr(analyzer, "analyze") and callable(analyzer.analyze):
        return analyzer.analyze(records)
    if hasattr(analyzer, "analyze_window") and callable(analyzer.analyze_window):
        return analyzer.analyze_window(records)
    if callable(analyzer):
        return analyzer(records)
    raise TypeError("candidate exposes no analyze/analyze_window/callable interface")


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


def run_candidate(module_name: str, class_name: str) -> dict[str, Any]:
    contract = self_check_contract()
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        return {
            "schema": "ANTMUX-X72-TREND-ANALYZER-ADVERSARIAL-RUN-v0.1",
            "contract": contract,
            "candidate": "BLOCKER",
            "blocker": f"TREND_ANALYZER_NOT_PRESENT:{module_name}",
            "tests_total": contract["tests_total"],
            "tests_pass": contract["tests_pass"],
            "tests_fail": 0,
            "expected_rejections": contract["expected_rejections"],
        }

    cls = getattr(module, class_name, None)
    if cls is None:
        return {
            "schema": "ANTMUX-X72-TREND-ANALYZER-ADVERSARIAL-RUN-v0.1",
            "contract": contract,
            "candidate": "BLOCKER",
            "blocker": f"TREND_ANALYZER_CLASS_NOT_PRESENT:{class_name}",
            "tests_total": contract["tests_total"],
            "tests_pass": contract["tests_pass"],
            "tests_fail": 0,
            "expected_rejections": contract["expected_rejections"],
        }

    guard = candidate_source_guard(module, cls)
    if not guard["ok"]:
        return {
            "schema": "ANTMUX-X72-TREND-ANALYZER-ADVERSARIAL-RUN-v0.1",
            "contract": contract,
            "candidate": "FAIL",
            "blocker": "FORBIDDEN_MUTATION_OR_LOCAL_QUEEN",
            "source_guard": guard,
        }

    outcomes: list[dict[str, Any]] = []
    failures = 0
    expected_rejections = 0

    for case in build_cases():
        source_before = copy.deepcopy(case.records)
        records = tuple(to_history_record(item) for item in case.records)
        analyzer = instantiate(cls)
        rejected = False
        error = None
        result = None
        try:
            result = invoke(analyzer, records)
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

        if case.records != source_before:
            failures += 1
            outcomes.append(
                {
                    "case_id": case.case_id,
                    "classification": "FAIL",
                    "detail": "source records mutated",
                }
            )
            continue

        if case.expectation == REJECT:
            if rejected:
                expected_rejections += 1
                classification = "EXPECTED_REJECTION"
                detail = error or "structured rejection"
            else:
                failures += 1
                classification = "FAIL"
                detail = "invalid adversarial window was accepted"
        else:
            if rejected:
                failures += 1
                classification = "FAIL"
                detail = error or "valid window was rejected"
            else:
                second = invoke(instantiate(cls), tuple(to_history_record(item) for item in case.records))
                first_norm = normalize_result(result)
                second_norm = normalize_result(second)
                if canonical_json(first_norm) != canonical_json(second_norm):
                    failures += 1
                    classification = "FAIL"
                    detail = "non-deterministic result across identical inputs"
                else:
                    classification = "PASS"
                    detail = "accepted deterministically"

        outcomes.append(
            {
                "case_id": case.case_id,
                "classification": classification,
                "detail": detail,
            }
        )

    return {
        "schema": "ANTMUX-X72-TREND-ANALYZER-ADVERSARIAL-RUN-v0.1",
        "contract": contract,
        "candidate": "PASS" if failures == 0 else "FAIL",
        "blocker": None,
        "source_guard": guard,
        "tests_total": len(outcomes),
        "tests_pass": sum(1 for item in outcomes if item["classification"] == "PASS"),
        "tests_fail": failures,
        "expected_rejections": expected_rejections,
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
