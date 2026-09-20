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
    min_link = 1.0
    max_link = 0.0
    all_verified = True
    finite = True
    reconstructable = True

    for _ in range(7200):
        queen.step()
        latest = queen.z3_runtime.latest
        if latest is None or latest.tick != queen.tick:
            continue

        sampled += 1
        link = latest.daat_link
        gate = latest.daat_gate
        min_link = min(min_link, link.link_score)
        max_link = max(max_link, link.link_score)
        all_verified = all_verified and link.verify()
        finite = finite and math.isfinite(link.link_score)
        reconstructable = reconstructable and all(
            math.isclose(
                gate.left[i],
                link.common_b[i] + link.differential_a[i],
                rel_tol=0.0,
                abs_tol=1e-12,
            )
            and math.isclose(
                gate.right[i],
                link.common_b[i] - link.differential_a[i],
                rel_tol=0.0,
                abs_tol=1e-12,
            )
            for i in range(12)
        )

    checks.append(check("full cycle yields 120 link frames", sampled == 120))
    checks.append(check("all link frames verify", all_verified))
    checks.append(check("all link scores remain finite", finite))
    checks.append(check(
        "all link scores remain in unit interval",
        0.0 <= min_link <= max_link <= 1.0,
    ))
    checks.append(check(
        "B/A reconstruct G/D over the full cycle",
        reconstructable,
    ))

    report = {
        "schema": "ANTMUX-X72-DAAT-LINK-SWEEP-TEST-v0.2",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "sampled_frames": sampled,
        "min_link_score": min_link,
        "max_link_score": max_link,
        "checks": checks,
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["checks_total"] == result["checks_passed"] else 1)
