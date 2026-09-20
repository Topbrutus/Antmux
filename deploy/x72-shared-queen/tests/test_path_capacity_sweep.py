from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.server import QueenCore


def check(name: str, condition: bool) -> dict[str, object]:
    if not condition:
        raise AssertionError(name)
    return {"name": name, "ok": True}


def run() -> dict[str, object]:
    checks: list[dict[str, object]] = []
    queen = QueenCore(seed=72)
    sampled = 0
    all_verified = True
    bounded = True
    path_count_stable = True
    sample_count_stable = True
    max_generated = 0
    distinct_hashes: set[str] = set()
    distinct_route_samples: set[tuple[tuple[int, ...], ...]] = set()
    for _ in range(7200):
        queen.step()
        latest = queen.z3_runtime.latest
        if latest is None or latest.tick != queen.tick:
            continue

        sampled += 1
        cap = latest.path_capacity
        all_verified = all_verified and cap.verify()
        bounded = bounded and (
            cap.max_retained_prefixes <= cap.beam_width
            and cap.max_stored_channel_slots == cap.beam_width * 12
            and cap.max_generated_candidates <= cap.beam_width * 12
        )
        path_count_stable = path_count_stable and (
            cap.complete_path_space == math.factorial(12)
        )
        sample_count_stable = sample_count_stable and (
            len(cap.sampled_routes) == cap.beam_width == 64
        )
        max_generated = max(max_generated, cap.max_generated_candidates)
        distinct_hashes.add(cap.capacity_h256)
        distinct_route_samples.add(cap.sampled_routes)
    checks.append(check(
        "full cycle yields 120 path-capacity frames",
        sampled == 120,
    ))
    checks.append(check(
        "all path-capacity frames verify",
        all_verified,
    ))
    checks.append(check(
        "beam memory/runtime policy remains bounded",
        bounded,
    ))
    checks.append(check(
        "theoretical complete path count stays exactly 12 factorial",
        path_count_stable,
    ))
    checks.append(check(
        "retained complete-route sample stays fixed at beam width",
        sample_count_stable,
    ))
    checks.append(check(
        "capacity provenance evolves across the sampled cycle",
        len(distinct_hashes) == sampled,
    ))
    checks.append(check(
        "source-dependent deterministic sampling explores multiple route samples",
        len(distinct_route_samples) > 1,
    ))

    report = {
        "schema": "ANTMUX-X72-PATH-CAPACITY-SWEEP-TEST-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "sampled_frames": sampled,
        "complete_path_space": math.factorial(12),
        "retained_per_frame": 64,
        "max_generated_candidates": max_generated,
        "distinct_capacity_hashes": len(distinct_hashes),
        "distinct_route_samples": len(distinct_route_samples),
        "checks": checks,
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["checks_total"] == result["checks_passed"] else 1)
