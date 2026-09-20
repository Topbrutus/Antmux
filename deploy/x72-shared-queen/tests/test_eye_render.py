from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.eye_render import EyeLightControls, EyePairRenderFrame, PRESETS
from app.server import QueenCore


def check(name: str, condition: bool, detail: str = "") -> dict[str, object]:
    if not condition:
        raise AssertionError(f"{name}: {detail}")
    return {"name": name, "ok": True}


def run() -> dict[str, object]:
    checks: list[dict[str, object]] = []
    queen = QueenCore(seed=72)
    for _ in range(60):
        queen.step()

    stereo = queen.z3_runtime.latest.stereo_source
    frame = EyePairRenderFrame.from_stereo_source(
        stereo,
        controls=PRESETS["mouse_alert"],
    )
    payload = frame.to_dict()
    boosts = payload["native_boosts"]
    checks.append(check(
        "native channels are additive boost controls only",
        payload["native_light_rule"] == "BOOST_ONLY_NEVER_DIM"
        and all(0.0 <= value <= 1.0 for value in boosts.values()),
    ))

    linked = payload["linked_illumination"]
    checks.append(check(
        "blue ring, web lines, and blue crystals share one boost",
        linked["blue_second_ring"] == boosts["blue_second"]
        and linked["blue_web_lines"] == boosts["blue_second"]
        and linked["blue_crystals"] == boosts["blue_second"],
    ))
    checks.append(check(
        "yellow outer ring and yellow crystals share one boost",
        linked["yellow_outer_ring"] == boosts["yellow_outer"]
        and linked["yellow_crystals"] == boosts["yellow_outer"],
    ))
    checks.append(check(
        "mauve and rose preserve their native clock regions",
        linked["mauve_third_ring"] == boosts["mauve_third"]
        and linked["rose_inner_accent"] == boosts["rose_inner"],
    ))
    checks.append(check(
        "clear crystal center uses less filter alpha than the edge",
        payload["filter_transparency"]["center_is_clearer"] is True
        and payload["filter_transparency"]["center_alpha"]
        < payload["filter_transparency"]["edge_alpha"],
    ))

    left = payload["left_eye"]
    right = payload["right_eye"]
    checks.append(check(
        "visible eye render stays stable on both sides",
        left["visible_rotation"] == "NONE"
        and right["visible_rotation"] == "NONE"
        and left["visible_rotation_rad"] == 0.0
        and right["visible_rotation_rad"] == 0.0,
    ))
    checks.append(check(
        "neither eye is mirrored",
        left["mirror_x"] is False and right["mirror_x"] is False,
    ))
    checks.append(check(
        "left and right calculations run in opposite directions at source",
        left["calculation_direction"] == "COUNTERCLOCKWISE"
        and right["calculation_direction"] == "CLOCKWISE"
        and left["calculation_theta"] == -right["calculation_theta"],
    ))
    checks.append(check(
        "both eyes retain one bilateral color basis",
        payload["shared_color_basis"] == "BILATERAL_MEAN"
        and payload["bilateral_signal"] == list(stereo.bilateral_mean),
    ))
    mouse = PRESETS["mouse_alert"].native_boosts()
    checks.append(check(
        "combined alert can illuminate several native channels together",
        mouse["yellow_outer"] > 0
        and mouse["blue_second"] > 0
        and mouse["mauve_third"] > 0
        and mouse["rose_inner"] > 0,
    ))

    all_on = EyeLightControls.from_values(
        yellow_outer=1,
        blue_second=1,
        mauve_third=1,
        rose_inner=1,
    )
    all_frame = EyePairRenderFrame.from_stereo_source(
        stereo, controls=all_on
    ).to_dict()
    checks.append(check(
        "all four native channels may coexist",
        all_frame["all_native_channels_may_coexist"] is True
        and all(value == 1.0 for value in all_frame["native_boosts"].values()),
    ))
    checks.append(check(
        "eye renderer remains observation-only",
        payload["authority"] == "OBSERVATION_ONLY"
        and payload["mutates_queen"] is False
        and payload["physical_claim"] is False,
    ))

    report = {
        "schema": "ANTMUX-X72-EYE-RENDER-TEST-v0.1",
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
