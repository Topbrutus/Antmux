from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DEPLOY = ROOT / "deploy" / "x72-shared-queen" / "frontend" / "app.js"
LAB = ROOT / "laboratoire" / "embryon-x72" / "app.js"


def require(ok: bool, name: str) -> dict[str, object]:
    if not ok:
        raise AssertionError(name)
    return {"name": name, "ok": True}


deploy_text = DEPLOY.read_text(encoding="utf-8")
lab_text = LAB.read_text(encoding="utf-8")
results: list[dict[str, object]] = []

results.append(require(deploy_text == lab_text, "frontend copies identical"))
results.append(require("requestAnimationFrame(animationLoop)" in deploy_text, "requestAnimationFrame loop"))
results.append(require("interpolateVisualState" in deploy_text, "visual interpolation present"))
results.append(require("_visualTick=lerp(previous.tick_count,current.tick_count,alpha);" in deploy_text, "visual tick interpolation only"))
results.append(require("class QueenCore" not in deploy_text, "no frontend QueenCore class"))
results.append(require("new QueenCore" not in deploy_text, "no frontend QueenCore instance"))
results.append(require('incoming.source!=="QUEEN_SERVER_V0_2"' in deploy_text, "server source authority"))
results.append(require('ctx.fillText("CORE DISCONNECTED",cx,cy);' in deploy_text, "disconnect overlay"))
results.append(require("drawFrame(connected?visualStateForFrame(now):lastState);" in deploy_text, "disconnect freezes last state"))
results.append(require('return {label:"READY",detail:"AUCUNE PANNE",ok:true};' in deploy_text, "healthy INVALID maps to READY"))
results.append(require("previousState=lastState;" in deploy_text and "lastState=incoming;" in deploy_text, "reconnect resumes server state"))

official_write = re.compile(
    r"(?:\.|\b)tick_count\s*(?:\+\+|--|\+=|-=|\*=|/=|=(?!=))"
)
results.append(require(not official_write.search(deploy_text), "no local official tick mutation"))

print(json.dumps({
    "verdict": "PASS",
    "checks": len(results),
    "deploy": str(DEPLOY),
    "laboratoire": str(LAB),
}, sort_keys=True))
