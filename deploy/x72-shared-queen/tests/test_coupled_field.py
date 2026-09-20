from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.coupled_field import CHANNELS, CoupledFieldFrame
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
    field = latest.coupled_field
    payload = field.to_dict()

    checks.append(check(
        "field reuses oscillator source/tick/generation",
        field.source_h256 == latest.oscillator.source_h256
        and field.tick == latest.oscillator.tick
        and field.generation == latest.oscillator.generation,
    ))

    checks.append(check(
        "two software field components expose twelve lanes",
        len(field.x_before) == CHANNELS
        and len(field.y_before) == CHANNELS
        and len(field.x_after) == CHANNELS
        and len(field.y_after) == CHANNELS,
    ))

    checks.append(check(
        "X and Y sums are conserved by synchronous propagation",
        math.isclose(field.x_sum_before, field.x_sum_after, rel_tol=0.0, abs_tol=1e-12)
        and math.isclose(field.y_sum_before, field.y_sum_after, rel_tol=0.0, abs_tol=1e-12),
    ))

    checks.append(check(
        "software energy cannot increase under candidate diffusion",
        field.energy_after <= field.energy_before + 1e-12
        and payload["accounting"]["no_software_energy_creation"] is True,
    ))

    checks.append(check(
        "component spans do not expand",
        payload["contraction"]["x_nonexpanding"] is True
        and payload["contraction"]["y_nonexpanding"] is True,
    ))

    checks.append(check(
        "causal update is read-all then write-all",
        payload["causal_update"] == "READ_ALL_THEN_WRITE_ALL",
    ))

    zero = CoupledFieldFrame.from_oscillator(
        latest.oscillator,
        coupling=0.0,
    )
    checks.append(check(
        "zero coupling is exact identity",
        zero.x_after == zero.x_before
        and zero.y_after == zero.y_before
        and all(value == 0.0 for value in zero.flux_x)
        and all(value == 0.0 for value in zero.flux_y),
    ))

    duplicate = CoupledFieldFrame.from_oscillator(
        latest.oscillator,
        coupling=field.coupling,
    )
    checks.append(check(
        "same oscillator and coupling reproduce identical field hash",
        duplicate.field_h256 == field.field_h256,
    ))

    try:
        CoupledFieldFrame.from_oscillator(
            latest.oscillator,
            coupling=0.500001,
        )
        invalid_rejected = False
    except ValueError:
        invalid_rejected = True
    checks.append(check(
        "non-convex coupling above one-half is rejected",
        invalid_rejected,
    ))

    before = field.to_dict()
    queen.z3_runtime.daat_evidence.observe(
        stereo=latest.stereo_source,
        daat=latest.daat_gate,
        tick=latest.tick,
    )
    checks.append(check(
        "Bayes update cannot alter coupled field",
        latest.coupled_field.to_dict() == before,
    ))

    checks.append(check(
        "field is explicitly software-only and not electromagnetic",
        payload["authority"] == "OBSERVATION_ONLY"
        and payload["mutates_queen"] is False
        and payload["physical_claim"] is False
        and payload["electromagnetic_claim"] is False,
    ))

    checks.append(check(
        "field calculation does not mutate protected Queen state",
        queen.protected_h256() == protected_before,
    ))

    whole = queen.z3_runtime.whole_projection()
    checks.append(check(
        "coupled field stays outside authoritative whole-state hash",
        "coupled_field" not in whole["latest"],
    ))

    field_hash = field.field_h256
    whole_before = queen.whole_h256()
    restored = QueenCore.from_checkpoint(queen.to_checkpoint())
    restored_field = restored.visual_state()["z3_runtime"]["latest"]["coupled_field"]
    checks.append(check(
        "checkpoint reconstructs same field frame",
        restored_field["field_h256"] == field_hash
        and restored_field["verified"] is True,
    ))
    checks.append(check(
        "checkpoint preserves authoritative whole hash",
        restored.whole_h256() == whole_before,
    ))

    report = {
        "schema": "ANTMUX-X72-COUPLED-FIELD-TEST-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "software_dissipation": payload["accounting"]["software_dissipation"],
        "checks": checks,
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["checks_total"] == result["checks_passed"] else 1)
