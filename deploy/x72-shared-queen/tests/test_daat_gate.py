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
    daat = latest["daat_gate"]

    checks.append(check(
        "Da'at gate consumes synchronized G/D stereo source",
        daat["source_h256"] == stereo["source_h256"]
        and stereo["left"]["side"] == "G"
        and stereo["right"]["side"] == "D",
    ))

    checks.append(check(
        "current candidate maps only left-right and leaves remaining axes open",
        daat["mapped_now"] == {
            "axis": "LEFT_RIGHT_ONLY",
            "left": "G",
            "right": "D",
            "meeting_point": "DAAT",
        }
        and daat["deliberately_unmapped"] == [
            "VERTICAL_AXIS",
            "DEPTH_AXIS",
            "FULL_TREE_PATHS",
            "SEFIROT_SEMANTICS",
        ],
    ))

    left = daat["left"]
    right = daat["right"]
    center = daat["daat"]["center"]
    residual = daat["daat"]["residual"]

    checks.append(check(
        "Da'at center is exact bilateral mean",
        center == [(left[i] + right[i]) / 2.0 for i in range(12)],
    ))

    checks.append(check(
        "Da'at residual preserves left-right difference",
        residual == [(left[i] - right[i]) / 2.0 for i in range(12)],
    ))

    checks.append(check(
        "left side is losslessly reconstructable from Da'at",
        all(
            abs(left[i] - (center[i] + residual[i]))
            <= 1e-12 * max(1.0, abs(left[i]), abs(center[i] + residual[i]))
            for i in range(12)
        ),
    ))

    checks.append(check(
        "right side is losslessly reconstructable from Da'at",
        all(
            abs(right[i] - (center[i] - residual[i]))
            <= 1e-12 * max(1.0, abs(right[i]), abs(center[i] - residual[i]))
            for i in range(12)
        ),
    ))

    inv = daat["invariants"]
    checks.append(check(
        "energy identity is preserved by center-residual transform",
        inv["lossless_left_right_reconstruction"] is True
        and inv["energy_identity_error"] <= 1e-12
        * max(1.0, abs(inv["pair_energy"]), abs(inv["decomposed_energy"])),
    ))

    checks.append(check(
        "hopscotch route is ordered and side identity survives until Da'at",
        daat["route"] == ["Z_INPUT", "STEREO_G_D", "DAAT"]
        and daat["hopscotch_model"]["ordered_route"] is True
        and daat["hopscotch_model"]["same_tick_pair_required"] is True
        and daat["hopscotch_model"]["side_identity_preserved"] is True,
    ))

    checks.append(check(
        "Da'at candidate remains observation-only",
        daat["authority"] == "OBSERVATION_ONLY"
        and daat["mutates_queen"] is False
        and daat["physical_claim"] is False
        and daat["verified"] is True,
    ))

    checks.append(check(
        "Da'at observation does not mutate protected Queen state",
        queen.protected_h256() == protected_before,
    ))

    whole_projection = queen.z3_runtime.whole_projection()
    checks.append(check(
        "Da'at candidate stays outside authoritative whole-state hash",
        "daat_gate" not in whole_projection["latest"],
    ))

    whole_before = queen.whole_h256()
    daat_hash = daat["daat_h256"]
    restored = QueenCore.from_checkpoint(queen.to_checkpoint())
    restored_daat = restored.visual_state()["z3_runtime"]["latest"]["daat_gate"]
    checks.append(check(
        "checkpoint reconstructs identical Da'at gate",
        restored_daat["daat_h256"] == daat_hash
        and restored_daat["verified"] is True,
    ))
    checks.append(check(
        "checkpoint preserves authoritative whole hash",
        restored.whole_h256() == whole_before,
    ))

    report = {
        "schema": "ANTMUX-X72-DAAT-GATE-TEST-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "checks": checks,
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["checks_total"] == result["checks_passed"] else 1)
