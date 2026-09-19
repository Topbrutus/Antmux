from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.server import QueenCore
from app.stereo27 import Stereo27Frame


def check(name: str, condition: bool, detail: str = "") -> dict[str, object]:
    if not condition:
        raise AssertionError(f"{name}: {detail}")
    return {"name": name, "ok": True}


def expect_raises(name: str, exc_type, fn) -> dict[str, object]:
    try:
        fn()
    except exc_type:
        return {"name": name, "ok": True}
    raise AssertionError(f"{name}: expected {exc_type.__name__}")


def run() -> dict[str, object]:
    checks: list[dict[str, object]] = []

    values = tuple(float(i) / 10.0 for i in range(27))
    frame = Stereo27Frame.from_values(values)
    checks.append(check(
        "stereo27 creates exactly 27 units per side and 54 channels",
        len(frame.positive) == 27
        and len(frame.negative) == 27
        and frame.to_dict()["stereo_channels"] == 54,
    ))
    checks.append(check(
        "negative side is the exact reversed sign mirror",
        frame.negative == tuple(-value for value in reversed(values)),
    ))
    checks.append(check(
        "zero plane closes exact mirror to PLOUF",
        frame.plouf is True
        and frame.max_zero_error == 0.0
        and all(value == 0.0 for value in frame.zero_plane),
    ))
    checks.append(check(
        "stereo frame verifies its own hashes and mirror law",
        frame.verify() is True and frame.to_dict()["verified"] is True,
    ))

    broken_negative = list(frame.negative)
    broken_negative[0] += 0.125
    broken = Stereo27Frame.from_sides(
        positive=frame.positive,
        negative=broken_negative,
    )
    checks.append(check(
        "PAS-PLOUF detects a stereo mismatch",
        broken.plouf is False
        and broken.to_dict()["pas_plouf"] is True
        and broken.max_zero_error > 0.0,
    ))

    checks.append(expect_raises(
        "stereo27 rejects fewer than 27 units",
        ValueError,
        lambda: Stereo27Frame.from_values(range(26)),
    ))
    checks.append(expect_raises(
        "stereo27 rejects non-finite values",
        ValueError,
        lambda: Stereo27Frame.from_values([0.0] * 26 + [math.nan]),
    ))

    queen = QueenCore(seed=72)
    protected_before = queen.protected_h256()
    for _ in range(60):
        queen.step()

    state = queen.visual_state()
    stereo = state["z3_runtime"]["latest"]["stereo27"]
    checks.append(check(
        "live Z3 projection exposes stereo27 as observation-only",
        stereo["schema"] == "ANTMUX-X72-STEREO27-v0.1"
        and stereo["authority"] == "OBSERVATION_ONLY"
        and stereo["mutates_queen"] is False
        and stereo["physical_claim"] is False,
    ))
    checks.append(check(
        "live stereo27 is 27x2 with a neutral zero plane",
        stereo["units_per_side"] == 27
        and stereo["stereo_channels"] == 54
        and len(stereo["positive"]) == 27
        and len(stereo["negative"]) == 27
        and len(stereo["zero_plane"]) == 27
        and stereo["plouf"] is True
        and stereo["verified"] is True,
    ))
    checks.append(check(
        "stereo observation does not mutate protected Queen state",
        queen.protected_h256() == protected_before,
    ))

    whole_projection = queen.z3_runtime.whole_projection()
    checks.append(check(
        "derived stereo layer stays outside authoritative whole-state hash",
        "stereo27" not in whole_projection["latest"],
    ))

    whole_before = queen.whole_h256()
    stereo_hash_before = stereo["stereo_h256"]
    restored = QueenCore.from_checkpoint(queen.to_checkpoint())
    restored_state = restored.visual_state()
    restored_stereo = restored_state["z3_runtime"]["latest"]["stereo27"]
    checks.append(check(
        "checkpoint round trip preserves authoritative whole hash",
        restored.whole_h256() == whole_before,
    ))
    checks.append(check(
        "checkpoint rebuilds identical stereo projection",
        restored_stereo["stereo_h256"] == stereo_hash_before
        and restored_stereo["plouf"] is True
        and restored_stereo["verified"] is True,
    ))

    report = {
        "schema": "ANTMUX-X72-STEREO27-TEST-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "checks": checks,
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["checks_total"] == result["checks_passed"] else 1)
