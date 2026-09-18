from __future__ import annotations

import argparse
import json
import sys
import time
import tracemalloc
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from decision_candidate import X72DecisionCandidate
from observation_adapter import ObservationEnvelope
from observation_history import X72ObservationHistory
from ternary_echo import X72TernaryEchoMatrix, compute_intent_h256
from trend_analyzer import X72TrendAnalyzer

ENTITY = "QUEEN-X72-0072"
SOURCE = "QUEEN_SERVER_V0_2"
REFERENCE = "49e75d92d8fde33f402c3b60482bc5dcf13c12f09bd8c07c7937961d42ceaff9"
BASE_TIME = datetime(2026, 9, 18, 22, 45, 0, tzinfo=timezone.utc)


def run_case(events: int, *, include_echo: bool) -> dict[str, object]:
    history = X72ObservationHistory(capacity=32)
    trend_analyzer = X72TrendAnalyzer()
    decision = X72DecisionCandidate()
    echo = X72TernaryEchoMatrix(capacity=32) if include_echo else None

    echo_positive = echo_unknown = echo_negative = 0
    prov_match = prov_unknown = prov_mismatch = 0
    echo_resolution_ns = 0

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
        result = history.append(frame)
        if not result.accepted:
            raise RuntimeError(result.to_dict())
        trend = trend_analyzer.analyze(history)
        candidate = decision.generate(history, trend)

        if echo is not None:
            correlation_id = f"BENCH-{index}"
            intent_h256 = compute_intent_h256(
                entity_id=ENTITY,
                correlation_id=correlation_id,
                origin_id="BENCH_ORIGIN",
                target_id="BENCH_TARGET",
                source_candidate_h256=candidate.candidate_h256,
            )
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
            start_echo = time.perf_counter_ns()
            echo_frame = echo.observe_echo(
                correlation_id=correlation_id,
                observed_at_utc=observed,
                explicit_confirmation=True,
                echo_origin_id="BENCH_ORIGIN",
                evidence={"benchmark": True},
            )
            echo_resolution_ns += time.perf_counter_ns() - start_echo
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

    cpu_ns = cpu1 - cpu0
    wall_ns = wall1 - wall0
    report: dict[str, object] = {
        "events_processed": events,
        "cpu_time_seconds": cpu_ns / 1e9,
        "wall_time_seconds": wall_ns / 1e9,
        "cpu_time_per_event_us": cpu_ns / events / 1000,
        "event_resolution_latency_mean_us": wall_ns / events / 1000,
        "memory_current_delta_bytes": mem_after - mem_before,
        "memory_peak_delta_bytes": peak_after - peak_before,
        "retry_count": "NOT_AVAILABLE",
        "unresolved_event_count": "NOT_AVAILABLE",
    }

    if echo is not None:
        report.update(
            {
                "echo_events_total": events,
                "echo_positive_count": echo_positive,
                "echo_unknown_count": echo_unknown,
                "echo_negative_count": echo_negative,
                "provenance_match_count": prov_match,
                "provenance_unknown_count": prov_unknown,
                "provenance_mismatch_count": prov_mismatch,
                "echo_resolution_latency_mean_us": echo_resolution_ns
                / events
                / 1000,
                "correlation_lookups": events,
                "echo_frames_retained": len(echo.frames),
                "echo_capacity": echo.capacity,
            }
        )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=int, default=200)
    args = parser.parse_args()
    if args.events < 1:
        raise SystemExit("--events must be >= 1")

    pre = run_case(args.events, include_echo=False)
    post = run_case(args.events, include_echo=True)

    cpu_overhead = (
        post["cpu_time_per_event_us"] / pre["cpu_time_per_event_us"] - 1
    ) * 100
    wall_overhead = (
        post["event_resolution_latency_mean_us"]
        / pre["event_resolution_latency_mean_us"]
        - 1
    ) * 100

    result = {
        "schema": "ANTMUX-X72-ECHO-PAIRED-BENCHMARK-v0.1",
        "pre_echo": pre,
        "post_echo": post,
        "comparison": {
            "cpu_overhead_percent": cpu_overhead,
            "wall_overhead_percent": wall_overhead,
            "retry_reduction": "NOT_AVAILABLE",
            "unresolved_reduction": "NOT_AVAILABLE",
            "performance_hypothesis_confirmed": False,
            "reason": (
                "retry/unresolved metrics are unavailable in this "
                "synthetic benchmark"
            ),
        },
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
