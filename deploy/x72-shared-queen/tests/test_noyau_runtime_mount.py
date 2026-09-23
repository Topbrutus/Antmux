from __future__ import annotations

import copy
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["ANTMUX_X72_DATA_DIR"] = tempfile.mkdtemp(prefix="antmux-x72-noyau-test-")

from app.server import QueenCore


def check(name: str, condition: bool, detail: str = "") -> dict[str, object]:
    if not condition:
        raise AssertionError(f"{name}: {detail}")
    return {"name": name, "ok": True}


def run() -> dict[str, object]:
    checks: list[dict[str, object]] = []
    queen = QueenCore(seed=72)

    first = queen.visual_state()["noyau_runtime"]["noyau"]
    second = queen.visual_state()["noyau_runtime"]["noyau"]
    checks.append(check(
        "read-only visual observation does not advance nucleus",
        first["tick"] == 0 and first == second,
        detail=f"{first['tick']} / {second['tick']}",
    ))

    queen.step()
    state = queen.visual_state()
    nucleus = state["noyau_runtime"]["noyau"]
    checks.append(check(
        "one Queen step advances nucleus exactly once",
        queen.tick == 1 and nucleus["tick"] == 1,
        detail=f"queen={queen.tick} noyau={nucleus['tick']}",
    ))
    checks.append(check(
        "nucleus cadence is mounted on Queen dt_sim",
        abs(nucleus["dt"] - queen.dt_sim) < 1e-12
        and abs(nucleus["sim_time"] - queen.sim_time) < 1e-8,
        detail=f"dt={nucleus['dt']} queen_dt={queen.dt_sim}",
    ))
    checks.append(check(
        "all three central gates are exposed",
        nucleus["center_gates"] == ["C1", "C2", "C3"]
        and nucleus["up_route"] == ["SOURCE", "C1", "C2", "C3", "SORTIE"]
        and nucleus["down_route"] == ["SORTIE", "C3", "C2", "C1", "SOURCE"],
    ))
    checks.append(check(
        "nucleus state carries canonical H256",
        isinstance(nucleus["whole_h256"], str) and len(nucleus["whole_h256"]) == 64,
    ))

    checkpoint = queen.to_checkpoint()
    restored = QueenCore.from_checkpoint(copy.deepcopy(checkpoint))
    restored_nucleus = restored.visual_state()["noyau_runtime"]["noyau"]
    checks.append(check(
        "server checkpoint preserves nucleus exactly",
        restored_nucleus == nucleus,
    ))
    checks.append(check(
        "existing Queen whole H256 remains stable across nucleus restore",
        restored.whole_h256() == queen.whole_h256(),
    ))

    legacy = copy.deepcopy(checkpoint)
    legacy.pop("noyau_runtime", None)
    legacy_restored = QueenCore.from_checkpoint(legacy)
    legacy_nucleus = legacy_restored.visual_state()["noyau_runtime"]["noyau"]
    checks.append(check(
        "legacy checkpoint receives fresh compatible nucleus",
        legacy_nucleus["tick"] == 0
        and abs(legacy_nucleus["dt"] - legacy_restored.dt_sim) < 1e-12,
    ))

    return {"ok": True, "checks": checks, "count": len(checks)}


if __name__ == "__main__":
    result = run()
    for item in result["checks"]:
        print(f"PASS {item['name']}")
    print(f"PASS {result['count']}/{result['count']}")
