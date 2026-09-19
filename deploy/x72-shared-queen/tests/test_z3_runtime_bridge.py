from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
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

    checks.append(
        check(
            "clean birth has zero learned observable state",
            all(
                s.activity == 0.0 and s.memory == 0.0 and s.crystal == 0.0
                for s in queen.synapses
            ),
        )
    )
    checks.append(
        check(
            "Z3 runtime starts empty",
            queen.z3_runtime.visual_state()["latest"] is None
            and queen.z3_runtime.visual_state()["history_count"] == 0,
        )
    )

    protected_before = queen.protected_h256()
    for _ in range(59):
        queen.step()
    checks.append(
        check(
            "Z3 runtime respects 60-tick sampling cadence",
            queen.z3_runtime.latest is None,
        )
    )

    queen.step()
    z3 = queen.z3_runtime.visual_state()
    latest = z3["latest"]
    checks.append(
        check(
            "first Z3 runtime frame is sealed and verified",
            latest is not None
            and latest["tick"] == 60
            and latest["sample_count"] == 1
            and latest["fast_verified"] is True,
        )
    )
    checks.append(
        check(
            "Z3 runtime topology is explicit 13-node candidate",
            z3["status"] == "CANDIDATE"
            and z3["authority"] == "OBSERVATION_ONLY"
            and z3["mutates_queen"] is False
            and z3["topology"]["total_nodes"] == 13
            and z3["topology"]["peripheral_channels"] == 12,
        )
    )
    checks.append(
        check(
            "Z3 observation does not mutate protected Queen structure",
            queen.protected_h256() == protected_before,
        )
    )

    for _ in range(180):
        queen.step()
    z3_after = queen.z3_runtime.visual_state()
    checks.append(
        check(
            "Z3 runtime history advances while bounded",
            z3_after["history_count"] == 4
            and z3_after["latest"]["tick"] == 240
            and z3_after["latest"]["fast_verified"] is True,
        )
    )
    checks.append(
        check(
            "Z3 frame event is present at one-second cadence",
            any(event["event_type"] == "Z3_RUNTIME_FRAME" for event in queen.bus.events),
        )
    )

    for _ in range(17):
        queen.step()
    checkpoint = queen.to_checkpoint()
    restored = QueenCore.from_checkpoint(checkpoint)
    restored_z3 = restored.z3_runtime.visual_state()
    checks.append(
        check(
            "checkpoint restores Z3 runtime history and provenance",
            restored_z3["history_count"] == z3_after["history_count"]
            and restored_z3["latest"]["center_provenance_h256"]
            == z3_after["latest"]["center_provenance_h256"],
        )
    )
    checks.append(
        check(
            "whole-state hash survives checkpoint round trip",
            restored.whole_h256() == queen.whole_h256(),
        )
    )

    report = {
        "schema": "ANTMUX-X72-Z3-RUNTIME-BRIDGE-TEST-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "checks": checks,
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["checks_total"] == result["checks_passed"] else 1)
