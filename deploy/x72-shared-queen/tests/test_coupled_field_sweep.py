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
    sums_conserved = True
    energy_nonincreasing = True
    spans_nonexpanding = True
    max_sum_error = 0.0
    max_energy_increase = 0.0
    distinct_hashes: set[str] = set()
    for _ in range(7200):
        queen.step()
        latest = queen.z3_runtime.latest
        if latest is None or latest.tick != queen.tick:
            continue

        sampled += 1
        field = latest.coupled_field
        payload = field.to_dict()
        all_verified = all_verified and field.verify()
        distinct_hashes.add(field.field_h256)

        x_err = abs(field.x_sum_after - field.x_sum_before)
        y_err = abs(field.y_sum_after - field.y_sum_before)
        max_sum_error = max(max_sum_error, x_err, y_err)
        sums_conserved = sums_conserved and x_err <= 1e-12 and y_err <= 1e-12

        energy_delta = field.energy_after - field.energy_before
        max_energy_increase = max(max_energy_increase, energy_delta)
        energy_nonincreasing = energy_nonincreasing and energy_delta <= 1e-12

        spans_nonexpanding = spans_nonexpanding and (
            payload["contraction"]["x_nonexpanding"] is True
            and payload["contraction"]["y_nonexpanding"] is True
        )
    checks.append(check(
        "full cycle yields 120 coupled-field frames",
        sampled == 120,
    ))
    checks.append(check(
        "all coupled-field frames verify",
        all_verified,
    ))
    checks.append(check(
        "X/Y sums remain conserved over full cycle",
        sums_conserved,
    ))
    checks.append(check(
        "software energy never increases over full cycle",
        energy_nonincreasing,
    ))
    checks.append(check(
        "field spans remain nonexpanding over full cycle",
        spans_nonexpanding,
    ))
    checks.append(check(
        "field evolves across sampled cycle",
        len(distinct_hashes) > 1,
    ))
    checks.append(check(
        "numerical accounting errors remain finite",
        math.isfinite(max_sum_error)
        and math.isfinite(max_energy_increase),
    ))
    report = {
        "schema": "ANTMUX-X72-COUPLED-FIELD-SWEEP-TEST-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "sampled_frames": sampled,
        "distinct_field_hashes": len(distinct_hashes),
        "max_sum_error": max_sum_error,
        "max_energy_increase": max_energy_increase,
        "checks": checks,
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["checks_total"] == result["checks_passed"] else 1)
