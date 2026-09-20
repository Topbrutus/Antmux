from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.oscillator_modes import CHANNELS, BoundedOscillatorFrame
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

    latest = queen.z3_runtime.latest
    assert latest is not None
    osc = latest.oscillator
    payload = osc.to_dict()

    checks.append(check(
        "oscillator reuses the same source/tick as Daat Link",
        osc.source_h256 == latest.daat_link.source_h256
        and osc.tick == latest.daat_link.tick
        and osc.generation == latest.daat_link.generation,
    ))
    checks.append(check(
        "twelve bounded modes are exposed",
        len(osc.modes) == CHANNELS
        and [mode.mode_number for mode in osc.modes] == list(range(1, 13)),
    ))
    checks.append(check(
        "amplitude is derived only from explicit B/A components",
        all(
            math.isclose(
                mode.amplitude,
                max(
                    0.0,
                    min(
                        1.0,
                        math.hypot(
                            latest.daat_link.common_b[i],
                            latest.daat_link.differential_a[i],
                        ),
                    ),
                ),
                rel_tol=0.0,
                abs_tol=1e-15,
            )
            for i, mode in enumerate(osc.modes)
        ),
    ))
    checks.append(check(
        "state is bounded on the mode circle",
        payload["bounded"] is True
        and all(
            abs(mode.x) <= mode.amplitude + 1e-12
            and abs(mode.y) <= mode.amplitude + 1e-12
            for mode in osc.modes
        ),
    ))
    checks.append(check(
        "radius invariant holds per mode",
        all(
            math.isclose(
                mode.x * mode.x + mode.y * mode.y,
                mode.amplitude * mode.amplitude,
                rel_tol=0.0,
                abs_tol=1e-12,
            )
            for mode in osc.modes
        ),
    ))
    duplicate = BoundedOscillatorFrame.from_link(
        latest.daat_link,
        theta=latest.theta,
    )
    checks.append(check(
        "same source and theta reproduce identical oscillator hash",
        duplicate.oscillator_h256 == osc.oscillator_h256,
    ))
    checks.append(check(
        "phase rule is deterministic mode_number times theta",
        all(
            math.isclose(
                mode.phase,
                math.remainder(mode.mode_number * latest.theta, math.tau),
                rel_tol=0.0,
                abs_tol=1e-15,
            )
            for mode in osc.modes
        ),
    ))
    before = osc.to_dict()
    queen.z3_runtime.daat_evidence.observe(
        stereo=latest.stereo_source,
        daat=latest.daat_gate,
        tick=latest.tick,
    )
    checks.append(check(
        "Bayes update cannot alter oscillator frame",
        latest.oscillator.to_dict() == before,
    ))
    checks.append(check(
        "oscillator layer is explicitly non-quantum and observation-only",
        payload["authority"] == "OBSERVATION_ONLY"
        and payload["mutates_queen"] is False
        and payload["physical_claim"] is False
        and payload["quantum_claim"] is False,
    ))
    checks.append(check(
        "oscillator does not mutate protected Queen state",
        queen.protected_h256() == protected_before,
    ))
    whole = queen.z3_runtime.whole_projection()
    checks.append(check(
        "oscillator stays outside authoritative whole-state hash",
        "oscillator" not in whole["latest"],
    ))
    osc_hash = osc.oscillator_h256
    whole_before = queen.whole_h256()
    restored = QueenCore.from_checkpoint(queen.to_checkpoint())
    restored_osc = restored.visual_state()["z3_runtime"]["latest"]["oscillator"]
    checks.append(check(
        "checkpoint reconstructs same oscillator frame",
        restored_osc["oscillator_h256"] == osc_hash
        and restored_osc["verified"] is True,
    ))
    checks.append(check(
        "checkpoint preserves authoritative whole hash",
        restored.whole_h256() == whole_before,
    ))

    report = {
        "schema": "ANTMUX-X72-OSCILLATOR-TEST-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "max_radius_error": payload["max_radius_error"],
        "checks": checks,
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["checks_total"] == result["checks_passed"] else 1)
