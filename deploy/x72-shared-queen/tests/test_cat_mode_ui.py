from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LAB = ROOT / "laboratoire" / "embryon-x72"
DEPLOY = ROOT / "deploy" / "x72-shared-queen" / "frontend"


def check(name: str, condition: bool) -> dict[str, object]:
    if not condition:
        raise AssertionError(name)
    return {"name": name, "ok": True}


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def run() -> dict[str, object]:
    checks: list[dict[str, object]] = []
    lab_app = text(LAB / "app.js")
    lab_cat = text(LAB / "cat_mode.js")
    lab_emotion = text(LAB / "emotion_map.js")
    lab_html = text(LAB / "index.html")
    lab_css = text(LAB / "styles.css")
    for name in ("app.js", "cat_mode.js", "emotion_map.js", "index.html", "styles.css"):
        checks.append(check(
            f"deploy copy matches lab for {name}",
            text(LAB / name) == text(DEPLOY / name),
        ))

    checks.append(check(
        "chat view toggle is present",
        'id="viewBtn"' in lab_html
        and 'id="catControls"' in lab_html
        and 'viewMode==="chat"' in lab_app,
    ))

    for control_id in ("yellowBoost", "blueBoost", "mauveBoost", "roseBoost"):
        checks.append(check(
            f"native light control {control_id} exists",
            f'id="{control_id}"' in lab_html,
        ))

    checks.append(check(
        "emotion map loads before cat renderer and app",
        lab_html.index("./emotion_map.js")
        < lab_html.index("./cat_mode.js")
        < lab_html.index("./app.js"),
    ))
    checks.append(check(
        "emotion map exposes four triads and twelve state IDs",
        lab_emotion.count('states:[') == 4
        and lab_emotion.count('id:"') >= 16
        and 'schema:"ANTMUX-X72-EMOTION-MAP-v0.1"' in lab_emotion,
    ))
    checks.append(check(
        "emotion controls are generated and persisted separately",
        'id="emotionControls"' in lab_html
        and "buildEmotionControls" in lab_app
        and "catCal.emotions[state.id]" in lab_app,
    ))
    checks.append(check(
        "cat renderer consumes blended emotion channels",
        "window.X72EmotionMap.blend" in lab_cat
        and "emotion.yellow_outer" in lab_cat
        and "emotion.red_tint" in lab_cat,
    ))

    checks.append(check(
        "calibration offers six requested direction/size buttons",
        lab_html.count("data-cat-adjust=") == 6,
    ))
    checks.append(check(
        "calibration persists as visual-only browser state",
        "localStorage.setItem(CAT_CAL_KEY" in lab_app
        and "aucune mutation de la Queen" in lab_html,
    ))

    checks.append(check(
        "blue illumination links ring web and crystals",
        "blue_second_ring" in text(ROOT / "deploy" / "x72-shared-queen" / "app" / "eye_render.py")
        and "blue_web_lines" in text(ROOT / "deploy" / "x72-shared-queen" / "app" / "eye_render.py")
        and "blue_crystals" in text(ROOT / "deploy" / "x72-shared-queen" / "app" / "eye_render.py"),
    ))

    checks.append(check(
        "cat renderer draws yellow and blue crystal families",
        "drawCrystals(ctx,radius*1.02,COLORS.yellow" in lab_cat
        and "drawCrystals(ctx,radius*.86,COLORS.blue" in lab_cat,
    ))

    checks.append(check(
        "four native rings preserve their fixed order",
        lab_cat.index("COLORS.yellow,.42")
        < lab_cat.index("COLORS.blue,.30")
        < lab_cat.index("COLORS.mauve,.24")
        < lab_cat.index("COLORS.rose,.18"),
    ))
    checks.append(check(
        "eye image is stable with no visual rotation or mirror",
        "ctx.rotate(" not in lab_cat
        and "mirror?" not in lab_cat
        and "leftRotation" not in lab_cat
        and "rightRotation" not in lab_cat
        and "drawEye(ctx,cx-eyeGap" in lab_cat
        and "drawEye(ctx,cx+eyeGap" in lab_cat,
    ))

    checks.append(check(
        "cat view consumes server eye_render metadata",
        "state?.z3_runtime?.latest?.eye_render" in lab_cat,
    ))

    checks.append(check(
        "frontend keeps authoritative tick immutable",
        "tick_count++" not in lab_app
        and "tick_count +=" not in lab_app
        and "tick_count =" not in lab_app,
    ))

    report = {
        "schema": "ANTMUX-X72-CAT-MODE-UI-TEST-v0.1",
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
