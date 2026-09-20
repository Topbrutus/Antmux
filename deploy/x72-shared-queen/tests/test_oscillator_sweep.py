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
    max_radius_error = 0.0
    distinct_hashes: set[str] = set()
    deterministic_phases = True
    for _ in range(7200):
        queen.step()
        latest = queen.z3_runtime.latest
        if latest is None or latest.tick != queen.tick:
            continue

        sampled += 1
        osc = latest.oscillator
        all_verified = all_verified and osc.verify()
        distinct_hashes.add(osc.oscillator_h256)

        for mode in osc.modes:
            bounded = bounded and (
                0.0 <= mode.amplitude <= 1.0
                and abs(mode.x) <= mode.amplitude + 1e-12
                and abs(mode.y) <= mode.amplitude + 1e-12
            )
            max_radius_error = max(max_radius_error, mode.radius_error)
            deterministic_phases = deterministic_phases and math.isclose(
                mode.phase,
                math.remainder(mode.mode_number * latest.theta, math.tau),
                rel_tol=0.0,
                abs_tol=1e-15,
            )
    checks.append(check(
        "full cycle yields 120 oscillator frames",
        sampled == 120,
    ))
    checks.append(check(
        "all oscillator frames verify",
        all_verified,
    ))
    checks.append(check(
        "all modes remain bounded over full cycle",
        bounded,
    ))
    checks.append(check(
        "mode phases follow the deterministic theta rule",
        deterministic_phases,
    ))
    checks.append(check(
        "radius identity remains numerically tight",
        max_radius_error <= 1e-12,
    ))
    checks.append(check(
        "oscillator evolves across the sampled cycle",
        len(distinct_hashes) > 1,
    ))
    report = {
        "schema": "ANTMUX-X72-OSCILLATOR-SWEEP-TEST-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "sampled_frames": sampled,
        "distinct_frame_hashes": len(distinct_hashes),
        "max_radius_error": max_radius_error,
        "checks": checks,
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["checks_total"] == result["checks_passed"] else 1)
