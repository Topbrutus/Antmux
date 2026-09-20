from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.daat_evidence import DaatEvidenceTracker
from app.server import QueenCore


def check(name: str, condition: bool) -> dict[str, object]:
    if not condition:
        raise AssertionError(name)
    return {"name": name, "ok": True}


def run() -> dict[str, object]:
    checks: list[dict[str, object]] = []
    queen = QueenCore(seed=72)
    protected_before = queen.protected_h256()

    for _ in range(600):
        queen.step()

    evidence = queen.visual_state()["z3_runtime"]["daat_evidence"]
    checks.append(check(
        "evidence ledger receives one sample per Z3 observation",
        evidence["samples"] == 10,
    ))
    checks.append(check(
        "all six invariant criteria are tracked separately",
        set(evidence["criteria"]) == {
            "same_source",
            "same_tick",
            "opposite_theta",
            "left_right_reconstructable",
            "energy_identity",
            "gate_verified",
        },
    ))
    checks.append(check(
        "uniform Beta(1,1) prior produces 11/12 posterior after ten passes",
        all(
            item["alpha"] == 11
            and item["beta"] == 1
            and abs(item["posterior_mean"] - (11 / 12)) < 1e-15
            for item in evidence["criteria"].values()
        ),
    ))
    checks.append(check(
        "confidence floor is conservative minimum across criteria",
        abs(evidence["confidence_floor"] - (11 / 12)) < 1e-15,
    ))
    checks.append(check(
        "evidence ledger stays observation-only",
        evidence["authority"] == "OBSERVATION_ONLY"
        and evidence["mutates_queen"] is False
        and evidence["physical_claim"] is False,
    ))
    checks.append(check(
        "evidence ledger does not mutate protected Queen state",
        queen.protected_h256() == protected_before,
    ))

    whole = queen.z3_runtime.whole_projection()
    checks.append(check(
        "evidence ledger stays outside authoritative whole-state hash",
        "daat_evidence" not in whole,
    ))

    checkpoint = queen.to_checkpoint()
    restored = QueenCore.from_checkpoint(checkpoint)
    restored_evidence = restored.visual_state()["z3_runtime"]["daat_evidence"]
    checks.append(check(
        "checkpoint preserves evidence counts without changing whole hash",
        restored_evidence["samples"] == evidence["samples"]
        and restored_evidence["criteria"] == evidence["criteria"]
        and restored.whole_h256() == queen.whole_h256(),
    ))
    latest = queen.z3_runtime.latest
    assert latest is not None
    tracker = DaatEvidenceTracker()
    tracker.observe(
        stereo=latest.stereo_source,
        daat=latest.daat_gate,
        tick=latest.tick + 1,
    )
    failed = tracker.visual_state()
    checks.append(check(
        "contradictory tick evidence lowers only the same_tick posterior",
        failed["criteria"]["same_tick"]["alpha"] == 1
        and failed["criteria"]["same_tick"]["beta"] == 2
        and failed["criteria"]["same_tick"]["posterior_mean"] == 1 / 3
        and all(
            item["posterior_mean"] == 2 / 3
            for name, item in failed["criteria"].items()
            if name != "same_tick"
        ),
    ))

    report = {
        "schema": "ANTMUX-X72-DAAT-EVIDENCE-TEST-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "checks": checks,
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["checks_total"] == result["checks_passed"] else 1)
