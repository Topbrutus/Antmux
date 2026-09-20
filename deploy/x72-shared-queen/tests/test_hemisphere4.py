from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.server import QueenCore


def check(name: str, condition: bool, detail: str = "") -> dict[str, object]:
    if not condition:
        raise AssertionError(f"{name}: {detail}")
    return {"name": name, "ok": True}


def run() -> dict[str, object]:
    checks: list[dict[str, object]] = []

    queen = QueenCore(seed=72)
    protected_before = queen.protected_h256()
    for _ in range(60):
        queen.step()

    state = queen.visual_state()
    latest = state["z3_runtime"]["latest"]
    hemi = latest["hemisphere4"]
    checks.append(check(
        "hemisphere4 exposes four distinct quadrant lanes",
        set(hemi["quadrants"]) == {
            "left_positive", "left_negative",
            "right_positive", "right_negative",
        }
        and all(len(values) == 12 for values in hemi["quadrants"].values()),
    ))

    left_p = hemi["quadrants"]["left_positive"]
    left_n = hemi["quadrants"]["left_negative"]
    right_p = hemi["quadrants"]["right_positive"]
    right_n = hemi["quadrants"]["right_negative"]
    checks.append(check(
        "each hemisphere owns its own sign mirror",
        left_n == [-value for value in reversed(left_p)]
        and right_n == [-value for value in reversed(right_p)],
    ))

    expected_mean = [
        (left_p[index] + right_p[index]) / 2.0
        for index in range(12)
    ]
    checks.append(check(
        "bilateral mean combines left and right instead of cloning one eye",
        hemi["bilateral_mean"] == expected_mean,
    ))
    checks.append(check(
        "center is tagged BOTH for crystallization/routing",
        len(hemi["center"]) == 3
        and hemi["signal_side_tags"]["left"] == "G"
        and hemi["signal_side_tags"]["right"] == "D"
        and hemi["signal_side_tags"]["center"] == "BOTH",
    ))
    checks.append(check(
        "figure-eight candidate traverses all four corners through center",
        hemi["figure8_route_candidate"] == [
            "LEFT_POSITIVE", "CENTER",
            "RIGHT_POSITIVE", "CENTER",
            "LEFT_NEGATIVE", "CENTER",
            "RIGHT_NEGATIVE", "CENTER",
        ],
    ))
    legacy = hemi["legacy_diagnostic"]
    checks.append(check(
        "hemisphere4 sign-mirror layer is retained only as a legacy diagnostic",
        legacy["used_by_eye_render"] is False
        and "compatibility" in legacy["note"],
    ))
    routes = hemi["carrier_routes"]
    checks.append(check(
        "carrier tags distinguish G, D, polarity, and BOTH center",
        routes["G_POS"] == {"side": "G", "polarity": "POS", "lane": "left_positive"}
        and routes["G_NEG"] == {"side": "G", "polarity": "NEG", "lane": "left_negative"}
        and routes["D_POS"] == {"side": "D", "polarity": "POS", "lane": "right_positive"}
        and routes["D_NEG"] == {"side": "D", "polarity": "NEG", "lane": "right_negative"}
        and routes["BOTH"] == {"side": "BOTH", "polarity": "CENTER", "lane": "center"},
    ))
    checks.append(check(
        "hemisphere projection is observation-only and verified",
        hemi["authority"] == "OBSERVATION_ONLY"
        and hemi["mutates_queen"] is False
        and hemi["physical_claim"] is False
        and hemi["verified"] is True,
    ))
    checks.append(check(
        "hemisphere layer does not mutate protected Queen state",
        queen.protected_h256() == protected_before,
    ))
    whole_projection = queen.z3_runtime.whole_projection()
    checks.append(check(
        "hemisphere derivative stays outside authoritative whole-state hash",
        "hemisphere4" not in whole_projection["latest"],
    ))

    whole_before = queen.whole_h256()
    bilateral_hash = hemi["bilateral_h256"]
    restored = QueenCore.from_checkpoint(queen.to_checkpoint())
    restored_hemi = restored.visual_state()["z3_runtime"]["latest"]["hemisphere4"]
    checks.append(check(
        "checkpoint round trip preserves authoritative whole hash",
        restored.whole_h256() == whole_before,
    ))
    checks.append(check(
        "checkpoint rebuilds same bilateral stereo projection",
        restored_hemi["bilateral_h256"] == bilateral_hash
        and restored_hemi["verified"] is True,
    ))

    report = {
        "schema": "ANTMUX-X72-HEMISPHERE4-TEST-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "checks": checks,
    }
    print(json.dumps(report, sort_keys=True))
    return report

if __name__ == "__main__":
    result = run()
    raise SystemExit(
        0 if result["checks_total"] == result["checks_passed"] else 1
    )
