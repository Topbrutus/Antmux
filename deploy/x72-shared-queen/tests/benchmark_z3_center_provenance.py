from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from z3_echo import (
    CenterCoupling12,
    CenterSummary3WithResidual,
    FourTriadZState,
    FiniteZTriad,
    Triad3,
    deep_verify_center_provenance,
    seal_center_provenance,
    verify_center_provenance,
)


def timed_batch(fn: Callable[[], object], calls: int) -> int:
    start = time.perf_counter_ns()
    for _ in range(calls):
        fn()
    return time.perf_counter_ns() - start


def median_us(samples_ns: list[int], calls: int) -> float:
    return statistics.median(samples_ns) / calls / 1000.0


def make_state(length: int) -> FourTriadZState:
    groups = []
    for group in range(4):
        groups.append(
            FiniteZTriad.from_samples(
                Triad3(
                    complex(group * 10 + index + 0.125, index / 20),
                    complex((-1) ** group * (index + 0.5), group / 11),
                    complex((group + 1) * (index + 1) / 7, -index / 13),
                )
                for index in range(length)
            )
        )
    return FourTriadZState(tuple(groups))


def benchmark_size(length: int, calls: int, repetitions: int) -> dict[str, object]:
    source = make_state(length)
    coupling = CenterCoupling12.from_theta(0.43)
    coupled = coupling.apply(source)
    summary = CenterSummary3WithResidual.decompose(coupled)
    frame = seal_center_provenance(
        source=source,
        coupling=coupling,
        coupled=coupled,
        summary=summary,
        source_z3_echo_provenance_h256="e" * 64,
    )

    verify_center_provenance(
        frame,
        source=source,
        coupled=coupled,
        summary=summary,
    )
    deep_verify_center_provenance(
        frame,
        source=source,
        coupled=coupled,
        summary=summary,
    )

    seal_runs: list[int] = []
    fast_runs: list[int] = []
    deep_runs: list[int] = []

    for _ in range(repetitions):
        seal_runs.append(
            timed_batch(
                lambda: seal_center_provenance(
                    source=source,
                    coupling=coupling,
                    coupled=coupled,
                    summary=summary,
                    source_z3_echo_provenance_h256="e" * 64,
                ),
                calls,
            )
        )
        fast_runs.append(
            timed_batch(
                lambda: verify_center_provenance(
                    frame,
                    source=source,
                    coupled=coupled,
                    summary=summary,
                ),
                calls,
            )
        )
        deep_runs.append(
            timed_batch(
                lambda: deep_verify_center_provenance(
                    frame,
                    source=source,
                    coupled=coupled,
                    summary=summary,
                ),
                calls,
            )
        )

    fast_us = median_us(fast_runs, calls)
    deep_us = median_us(deep_runs, calls)

    return {
        "coefficients_per_triad": length,
        "complex_channel_values": length * 12,
        "calls_per_repetition": calls,
        "repetitions": repetitions,
        "seal_median_us_per_call": median_us(seal_runs, calls),
        "fast_verify_median_us_per_call": fast_us,
        "deep_verify_median_us_per_call": deep_us,
        "deep_vs_fast_overhead_percent": (deep_us / fast_us - 1.0) * 100.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", nargs="+", type=int, default=[8, 32, 128])
    parser.add_argument("--calls", type=int, default=100)
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--output")
    args = parser.parse_args()

    if any(size < 1 for size in args.sizes):
        raise SystemExit("all sizes must be positive")
    if args.calls < 1 or args.repetitions < 1:
        raise SystemExit("calls and repetitions must be positive")

    result = {
        "schema": "ANTMUX-Z3-CENTER-PROVENANCE-BENCHMARK-v0.1",
        "clock": "time.perf_counter_ns",
        "method": {
            "sizes": args.sizes,
            "calls_per_repetition": args.calls,
            "repetitions": args.repetitions,
            "summary": "median wall time per call across repetitions",
            "note": (
                "fast center verify hashes sealed source/coupled/3+9 bodies but "
                "does not rerun coupling.apply or decomposition; deep verify does both"
            ),
        },
        "results": [
            benchmark_size(size, args.calls, args.repetitions)
            for size in args.sizes
        ],
    }

    encoded = json.dumps(result, sort_keys=True)
    print(encoded)
    if args.output:
        Path(args.output).write_text(encoded + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
