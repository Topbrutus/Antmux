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
    final_invariant = True
    monotonic = True
    differentiated_histories = 0
    min_target = 1.0
    max_target = 0.0
    for _ in range(7200):
        queen.step()
        latest = queen.z3_runtime.latest
        if latest is None or latest.tick != queen.tick:
            continue

        sampled += 1
        hop = latest.hopscotch
        target = hop.target_link_score
        min_target = min(min_target, target)
        max_target = max(max_target, target)

        all_verified = all_verified and hop.verify()
        final_invariant = final_invariant and all(
            math.isclose(
                route.final_link,
                target,
                rel_tol=0.0,
                abs_tol=1e-12,
            )
            for route in hop.routes
        )
        monotonic = monotonic and all(
            all(
                route.cumulative_link[i]
                >= route.cumulative_link[i - 1] - 1e-12
                for i in range(1, len(route.cumulative_link))
            )
            for route in hop.routes
        )

        histories = {
            tuple(round(value, 15) for value in route.cumulative_link)
            for route in hop.routes
        }
        if len(histories) > 1:
            differentiated_histories += 1
    checks.append(check(
        "full cycle yields 120 hopscotch frames",
        sampled == 120,
    ))
    checks.append(check(
        "all hopscotch frames verify",
        all_verified,
    ))
    checks.append(check(
        "all route permutations preserve final Lc over full cycle",
        final_invariant,
    ))
    checks.append(check(
        "all route traces remain monotonic",
        monotonic,
    ))
    checks.append(check(
        "route order produces distinct traversal histories on observed frames",
        differentiated_histories > 0,
    ))
    checks.append(check(
        "target Lc remains finite and bounded over cycle",
        math.isfinite(min_target)
        and math.isfinite(max_target)
        and 0.0 <= min_target <= max_target <= 1.0,
    ))

    report = {
        "schema": "ANTMUX-X72-HOPSCOTCH-SWEEP-TEST-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "sampled_frames": sampled,
        "frames_with_distinct_histories": differentiated_histories,
        "min_target_link": min_target,
        "max_target_link": max_target,
        "checks": checks,
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["checks_total"] == result["checks_passed"] else 1)
