from __future__ import annotations

import json
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
    protected_before = queen.protected_h256()
    for _ in range(60):
        queen.step()

    latest = queen.visual_state()["z3_runtime"]["latest"]
    stereo = latest["stereo_source"]

    checks.append(check(
        "stereo source is verified observation-only",
        stereo["verified"] is True
        and stereo["authority"] == "OBSERVATION_ONLY"
        and stereo["mutates_queen"] is False
        and stereo["physical_claim"] is False,
    ))
    checks.append(check(
        "left and right are explicit G and D sides",
        stereo["left"]["side"] == "G"
        and stereo["right"]["side"] == "D",
    ))
    checks.append(check(
        "Z calculation direction is opposite at the stereo source",
        stereo["left"]["theta"] == -stereo["right"]["theta"]
        and stereo["left"]["calculation_direction"] == "COUNTERCLOCKWISE"
        and stereo["right"]["calculation_direction"] == "CLOCKWISE",
    ))
    checks.append(check(
        "left and right each carry twelve calculated channels",
        len(stereo["left"]["channels"]) == 12
        and len(stereo["right"]["channels"]) == 12,
    ))
    checks.append(check(
        "bilateral mean is calculated from both sides",
        stereo["bilateral_mean"] == [
            (stereo["left"]["channels"][i] + stereo["right"]["channels"][i]) / 2.0
            for i in range(12)
        ],
    ))
    checks.append(check(
        "render contract forbids visual rotation mirror and negative eye",
        stereo["render_contract"] == {
            "visible_rotation": False,
            "mirror_x": False,
            "negative_eye": False,
            "rule": "OPPOSITE_CALCULATION_DIRECTION_STABLE_RENDER",
        },
    ))
    checks.append(check(
        "stereo source does not mutate protected Queen state",
        queen.protected_h256() == protected_before,
    ))

    whole = queen.z3_runtime.whole_projection()
    checks.append(check(
        "stereo source stays outside authoritative whole-state hash",
        "stereo_source" not in whole["latest"],
    ))

    before_hash = stereo["bilateral_h256"]
    whole_before = queen.whole_h256()
    restored = QueenCore.from_checkpoint(queen.to_checkpoint())
    restored_latest = restored.visual_state()["z3_runtime"]["latest"]
    checks.append(check(
        "checkpoint rebuilds same stereo source projection",
        restored_latest["stereo_source"]["bilateral_h256"] == before_hash
        and restored_latest["stereo_source"]["verified"] is True,
    ))
    checks.append(check(
        "checkpoint keeps authoritative whole hash unchanged",
        restored.whole_h256() == whole_before,
    ))

    report = {
        "schema": "ANTMUX-X72-STEREO-SOURCE-TEST-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "checks": checks,
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["checks_total"] == result["checks_passed"] else 1)
