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
    max_energy_error = 0.0
    sampled = 0
    opposite_theta = True
    all_verified = True
    same_tick = True
    source_consistent = True
    for _ in range(7200):
        queen.step()
        latest_obj = queen.z3_runtime.latest
        if latest_obj is None or latest_obj.tick != queen.tick:
            continue

        sampled += 1
        latest = queen.visual_state()["z3_runtime"]["latest"]
        stereo = latest["stereo_source"]
        daat = latest["daat_gate"]

        all_verified = all_verified and stereo["verified"] and daat["verified"]
        opposite_theta = opposite_theta and math.isclose(
            stereo["left"]["theta"],
            -stereo["right"]["theta"],
            rel_tol=0.0,
            abs_tol=1e-15,
        )
        same_tick = same_tick and daat["tick"] == latest["tick"]
        source_consistent = source_consistent and (
            daat["source_h256"] == stereo["source_h256"]
        )
        max_energy_error = max(
            max_energy_error,
            float(daat["invariants"]["energy_identity_error"]),
        )
    checks.append(check(
        "full cycle yields 120 synchronized Da'at samples",
        sampled == 120,
    ))
    checks.append(check(
        "all stereo and Da'at frames verify over the full cycle",
        all_verified,
    ))
    checks.append(check(
        "left/right calculation angle stays opposite over the full cycle",
        opposite_theta,
    ))
    checks.append(check(
        "Da'at frame stays on the same sampled tick",
        same_tick,
    ))
    checks.append(check(
        "Da'at frame keeps the same pre-stereo source identity",
        source_consistent,
    ))
    checks.append(check(
        "energy identity error remains finite and negligible",
        math.isfinite(max_energy_error) and max_energy_error <= 1e-10,
    ))
    report = {
        "schema": "ANTMUX-X72-DAAT-GATE-SWEEP-TEST-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "sampled_frames": sampled,
        "max_energy_identity_error": max_energy_error,
        "checks": checks,
    }
    print(json.dumps(report, sort_keys=True))
    return report

if __name__ == "__main__":
    result = run()
    if result["checks_total"] != result["checks_passed"]:
        sys.exit(1)
