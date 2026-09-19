from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import tracemalloc
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from decision_candidate import X72DecisionCandidate
from observation_adapter import ObservationEnvelope
from observation_history import X72ObservationHistory
from ternary_echo import X72TernaryEchoMatrix, compute_intent_h256
from trend_analyzer import X72TrendAnalyzer

ENTITY = "QUEEN-X72-0072"
SOURCE = "QUEEN_SERVER_V0_2"
REFERENCE = "54d4cee87f7e5feed1a0735a0b8431a2dc67b1bda0492c78a6c7274109c13180"
BASE_TIME = datetime(2026, 9, 18, 22, 45, 0, tzinfo=timezone.utc)


def _mean_us(total_ns: int, count: int) -> float | None:
    return total_ns / count / 1000 if count else None


def _median(values: list[float | int]) -> float:
    return float(statistics.median(values))


def run_case(
    events: int,
    *,
    echo_every: int | None,
) -> dict[str, Any]:
    history = X72ObservationHistory(capacity=32)
    trend_analyzer = X72TrendAnalyzer()
    decision = X72DecisionCandidate()
    echo = X72TernaryEchoMatrix(capacity=32) if echo_every is not None else None

    stage_ns = {
        "history_append": 0,
        "trend_analysis": 0,
        "candidate_generation": 0,
        "echo_register": 0,
        "echo_observe": 0,
    }
    echo_count = 0
    echo_positive = echo_unknown = echo_negative = 0
    prov_match = prov_unknown = prov_mismatch = 0
    last_sources = None

    tracemalloc.start()
    mem_before, peak_before = tracemalloc.get_traced_memory()
    cpu0 = time.process_time_ns()
    wall0 = time.perf_counter_ns()

    for index in range(events):
        tick = 1000 + index
        observed = (
            BASE_TIME + timedelta(milliseconds=index)
        ).isoformat().replace("+00:00", "Z")
        payload = {
            "source": SOURCE,
            "entity_id": ENTITY,
            "tick_count": tick,
            "queen_mode": "STABLE",
            "integrity_match": True,
            "protected_h256": REFERENCE,
            "reference_h256": REFERENCE,
            "r_exec": 100.0,
            "f_rt": 0.5,
            "active_synapses": 7,
            "event_count": index,
        }
        frame = ObservationEnvelope(
            observed_at_utc=observed,
            entity_id=ENTITY,
            source_schema=SOURCE,
            source_endpoint="/ws",
            freshness_ms=0,
            status="FRESH",
            condition="STREAM_STATE",
            payload=payload,
            error=None,
        )

        t0 = time.perf_counter_ns()
        append_result = history.append(frame)
        stage_ns["history_append"] += time.perf_counter_ns() - t0
        if not append_result.accepted:
            raise RuntimeError(append_result.to_dict())

        t0 = time.perf_counter_ns()
        trend = trend_analyzer.analyze(history)
        stage_ns["trend_analysis"] += time.perf_counter_ns() - t0

        t0 = time.perf_counter_ns()
        candidate = decision.generate(history, trend)
        stage_ns["candidate_generation"] += time.perf_counter_ns() - t0
        last_sources = (history, trend, candidate)

        should_echo = (
            echo_every is not None and index % echo_every == 0
        )
        if echo is not None and should_echo:
            correlation_id = f"BENCH-{index}"
            intent_h256 = compute_intent_h256(
                entity_id=ENTITY,
                correlation_id=correlation_id,
                origin_id="BENCH_ORIGIN",
                target_id="BENCH_TARGET",
                source_candidate_h256=candidate.candidate_h256,
            )

            t0 = time.perf_counter_ns()
            echo.register_intent(
                history=history,
                trend=trend,
                candidate=candidate,
                correlation_id=correlation_id,
                origin_id="BENCH_ORIGIN",
                target_id="BENCH_TARGET",
                intent_h256=intent_h256,
                observed_at_utc=observed,
            )
            stage_ns["echo_register"] += time.perf_counter_ns() - t0

            t0 = time.perf_counter_ns()
            echo_frame = echo.observe_echo(
                correlation_id=correlation_id,
                observed_at_utc=observed,
                explicit_confirmation=True,
                echo_origin_id="BENCH_ORIGIN",
                evidence={"benchmark": True},
            )
            stage_ns["echo_observe"] += time.perf_counter_ns() - t0

            echo_count += 1
            echo_positive += echo_frame.echo_state == 1
            echo_unknown += echo_frame.echo_state == 0
            echo_negative += echo_frame.echo_state == -1
            prov_match += echo_frame.provenance_state == 1
            prov_unknown += echo_frame.provenance_state == 0
            prov_mismatch += echo_frame.provenance_state == -1

    wall1 = time.perf_counter_ns()
    cpu1 = time.process_time_ns()
    mem_after, peak_after = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    hash_validation_us = None
    if echo is not None and last_sources is not None:
        h, t, c = last_sources
        validation_samples = min(100, max(10, events // 10))
        validation_ns = 0
        for _ in range(validation_samples):
            t0 = time.perf_counter_ns()
            X72TernaryEchoMatrix._validate_sources(h, t, c)
            validation_ns += time.perf_counter_ns() - t0
        hash_validation_us = validation_ns / validation_samples / 1000

    cpu_ns = cpu1 - cpu0
    wall_ns = wall1 - wall0
    report: dict[str, Any] = {
        "events_processed": events,
        "echo_every": echo_every,
        "echo_events_total": echo_count,
        "cpu_time_seconds": cpu_ns / 1e9,
        "wall_time_seconds": wall_ns / 1e9,
        "cpu_time_per_event_us": cpu_ns / events / 1000,
        "wall_time_per_event_us": wall_ns / events / 1000,
        "history_append_us": _mean_us(stage_ns["history_append"], events),
        "trend_analysis_us": _mean_us(stage_ns["trend_analysis"], events),
        "candidate_generation_us": _mean_us(
            stage_ns["candidate_generation"], events
        ),
        "echo_register_us": _mean_us(stage_ns["echo_register"], echo_count),
        "echo_observe_us": _mean_us(stage_ns["echo_observe"], echo_count),
        "hash_validation_us": hash_validation_us,
        "memory_current_delta_bytes": mem_after - mem_before,
        "memory_peak_delta_bytes": peak_after - peak_before,
        "retry_count": "NOT_AVAILABLE",
        "unresolved_event_count": "NOT_AVAILABLE",
        "echo_positive_count": echo_positive,
        "echo_unknown_count": echo_unknown,
        "echo_negative_count": echo_negative,
        "provenance_match_count": prov_match,
        "provenance_unknown_count": prov_unknown,
        "provenance_mismatch_count": prov_mismatch,
        "correlation_lookups": echo_count,
        "echo_frames_retained": len(echo.frames) if echo else 0,
        "echo_capacity": echo.capacity if echo else 0,
    }
    return report


def summarize(runs: list[dict[str, Any]]) -> dict[str, Any]:
    numeric_keys = (
        "cpu_time_per_event_us",
        "wall_time_per_event_us",
        "history_append_us",
        "trend_analysis_us",
        "candidate_generation_us",
        "memory_peak_delta_bytes",
        "memory_current_delta_bytes",
    )
    optional_numeric_keys = (
        "echo_register_us",
        "echo_observe_us",
        "hash_validation_us",
    )
    summary: dict[str, Any] = {
        "runs": runs,
        "repetitions": len(runs),
        "events_processed": runs[0]["events_processed"],
        "echo_every": runs[0]["echo_every"],
        "echo_events_total_per_run": runs[0]["echo_events_total"],
    }
    for key in numeric_keys:
        summary[f"median_{key}"] = _median([r[key] for r in runs])
    for key in optional_numeric_keys:
        values = [r[key] for r in runs if r[key] is not None]
        summary[f"median_{key}"] = _median(values) if values else None
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", nargs="+", type=int, default=[200, 1000])
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--sparse-every", type=int, default=10)
    parser.add_argument("--output")
    args = parser.parse_args()

    if any(size < 1 for size in args.sizes):
        raise SystemExit("all --sizes values must be >= 1")
    if args.repetitions < 1:
        raise SystemExit("--repetitions must be >= 1")
    if args.sparse_every < 2:
        raise SystemExit("--sparse-every must be >= 2")

    result: dict[str, Any] = {
        "schema": "ANTMUX-X72-ECHO-PERFORMANCE-BENCHMARK-v0.2",
        "method": {
            "repetitions": args.repetitions,
            "sparse_echo_policy": (
                f"one echo every {args.sparse_every} observed events"
            ),
            "sparse_policy_reason": (
                "fixed 10% density by default; chosen before measurement "
                "as a simple event-driven workload, not tuned for outcome"
            ),
            "retry_metric": "NOT_AVAILABLE",
            "unresolved_metric": "NOT_AVAILABLE",
        },
        "sizes": {},
    }

    for events in args.sizes:
        scenarios = {
            "A_BASELINE": None,
            "B_ECHO_EVERY_EVENT": 1,
            "C_ECHO_SPARSE": args.sparse_every,
        }
        size_result = {}
        for name, echo_every in scenarios.items():
            runs = [
                run_case(events, echo_every=echo_every)
                for _ in range(args.repetitions)
            ]
            size_result[name] = summarize(runs)

        baseline = size_result["A_BASELINE"]
        every = size_result["B_ECHO_EVERY_EVENT"]
        sparse = size_result["C_ECHO_SPARSE"]
        base_cpu = baseline["median_cpu_time_per_event_us"]
        base_wall = baseline["median_wall_time_per_event_us"]
        size_result["comparison"] = {
            "every_event_cpu_overhead_percent": (
                every["median_cpu_time_per_event_us"] / base_cpu - 1
            ) * 100,
            "every_event_wall_overhead_percent": (
                every["median_wall_time_per_event_us"] / base_wall - 1
            ) * 100,
            "sparse_cpu_overhead_percent": (
                sparse["median_cpu_time_per_event_us"] / base_cpu - 1
            ) * 100,
            "sparse_wall_overhead_percent": (
                sparse["median_wall_time_per_event_us"] / base_wall - 1
            ) * 100,
            "retry_reduction": "NOT_AVAILABLE",
            "unresolved_reduction": "NOT_AVAILABLE",
        }
        result["sizes"][str(events)] = size_result

    encoded = json.dumps(result, sort_keys=True)
    print(encoded)
    if args.output:
        Path(args.output).write_text(encoded + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
