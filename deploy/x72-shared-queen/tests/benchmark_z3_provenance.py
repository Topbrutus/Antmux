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
    FiniteZTriad,
    Triad3,
    Z3EchoTransfer,
    deep_verify_provenance,
    euler_zyz,
    seal_provenance,
    verify_provenance,
)


def median_us(samples_ns: list[int], calls: int) -> float:
    return statistics.median(samples_ns) / calls / 1000.0


def timed_batch(fn: Callable[[], object], calls: int) -> int:
    start = time.perf_counter_ns()
    for _ in range(calls):
        fn()
    return time.perf_counter_ns() - start


def make_source(length: int) -> FiniteZTriad:
    return FiniteZTriad.from_samples(
        Triad3(
            index + 0.125,
            (-1) ** index * (index + 0.5),
            (index % 7) / 3.0,
        )
        for index in range(length)
    )


def benchmark_size(length: int, calls: int, repetitions: int) -> dict[str, object]:
    angles = (0.37, -0.81, 1.19)
    transfer = Z3EchoTransfer(
        gain=complex(0.73, -0.21),
        delay=3,
        rotation=euler_zyz(*angles),
    )
    source = make_source(length)
    echoed = transfer.apply(source)
    frame = seal_provenance(
        source=source,
        transfer=transfer,
        echoed=echoed,
        euler_zyz_angles=angles,
        source_x72_candidate_h256="a" * 64,
        source_x72_echo_h256="b" * 64,
    )

    verify_provenance(frame, source=source, echoed=echoed)
    deep_verify_provenance(frame, source=source, echoed=echoed)

    seal_runs: list[int] = []
    fast_runs: list[int] = []
    deep_runs: list[int] = []

    for _ in range(repetitions):
        seal_runs.append(
            timed_batch(
                lambda: seal_provenance(
                    source=source,
                    transfer=transfer,
                    echoed=echoed,
                    euler_zyz_angles=angles,
                    source_x72_candidate_h256="a" * 64,
                    source_x72_echo_h256="b" * 64,
                ),
                calls,
            )
        )
        fast_runs.append(
            timed_batch(
                lambda: verify_provenance(
                    frame,
                    source=source,
                    echoed=echoed,
                ),
                calls,
            )
        )
        deep_runs.append(
            timed_batch(
                lambda: deep_verify_provenance(
                    frame,
                    source=source,
                    echoed=echoed,
                ),
                calls,
            )
        )

    fast_us = median_us(fast_runs, calls)
    deep_us = median_us(deep_runs, calls)
    return {
        "coefficients_per_channel": length,
        "triad_coefficients": length * 3,
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
    parser.add_argument("--calls", type=int, default=200)
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--output")
    args = parser.parse_args()

    if any(size < 1 for size in args.sizes):
        raise SystemExit("all sizes must be positive")
    if args.calls < 1 or args.repetitions < 1:
        raise SystemExit("calls and repetitions must be positive")

    result = {
        "schema": "ANTMUX-Z3-PROVENANCE-BENCHMARK-v0.1",
        "clock": "time.perf_counter_ns",
        "method": {
            "sizes": args.sizes,
            "calls_per_repetition": args.calls,
            "repetitions": args.repetitions,
            "summary": "median wall time per call across repetitions",
            "note": (
                "fast verify hashes sealed source/echoed bodies but does not "
                "rerun transfer.apply; deep verify additionally recomputes transfer semantics"
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
