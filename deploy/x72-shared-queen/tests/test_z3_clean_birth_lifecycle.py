from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.server import Persistence, QueenCore


def check(name: str, condition: bool, detail: str = "") -> dict[str, object]:
    if not condition:
        raise AssertionError(f"{name}: {detail}")
    return {"name": name, "ok": True}


def run() -> dict[str, object]:
    checks: list[dict[str, object]] = []
    queen = QueenCore(seed=72)

    checks.append(check(
        "clean birth starts exactly at zero",
        queen.tick == 0
        and queen.generation == 0
        and all(
            s.activity == 0.0 and s.memory == 0.0 and s.crystal == 0.0
            for s in queen.synapses
        ),
    ))
    checks.append(check(
        "clean birth has seven active semantic synapses",
        [s.synapse_id for s in queen.synapses] == [f"S{i}" for i in range(1, 8)]
        and all(s.enabled and s.integrity > 0 for s in queen.synapses),
    ))
    checks.append(check(
        "clean birth Z3 starts empty",
        queen.z3_runtime.visual_state()["history_count"] == 0
        and queen.z3_runtime.visual_state()["latest"] is None,
    ))
    checks.append(check(
        "clean birth integrity is valid",
        queen.integrity_match() is True,
    ))

    for _ in range(59):
        queen.step()
    checks.append(check(
        "no early Z3 sample before tick 60",
        queen.tick == 59 and queen.z3_runtime.latest is None,
    ))

    queen.step()
    first_z3 = queen.z3_runtime.visual_state()
    checks.append(check(
        "first Z3 sample appears exactly at tick 60",
        queen.tick == 60
        and first_z3["history_count"] == 1
        and first_z3["latest"]["tick"] == 60
        and first_z3["latest"]["fast_verified"] is True,
    ))
    for _ in range(60, 7200):
        queen.step()

    state = queen.visual_state()
    z3 = queen.z3_runtime.visual_state()
    checks.append(check(
        "first generation completes at tick 7200",
        queen.tick == 7200 and queen.generation == 1,
    ))
    checks.append(check(
        "generation event is present",
        any(
            event["event_type"] == "GENERATION_ADVANCED"
            and event["payload"].get("generation") == 1
            for event in queen.bus.events
        ),
    ))
    checks.append(check(
        "Z3 history is full, bounded, and verified",
        z3["history_count"] == z3["history_size"] == 32
        and z3["latest"]["tick"] == 7200
        and z3["latest"]["fast_verified"] is True,
    ))
    checks.append(check(
        "memory and crystallization grew without first-generation saturation",
        0.0 < state["memory_level"] < 0.92
        and 0.0 < state["crystallization_level"] < 0.90,
        detail=f"memory={state['memory_level']} crystal={state['crystallization_level']}",
    ))
    checks.append(check(
        "integrity remains valid through first generation",
        state["integrity_match"] is True,
    ))
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "queen.db"
        store = Persistence(db_path)
        store.save(queen)
        restored = store.load_latest()

        checks.append(check(
            "checkpoint snapshot is actually persisted",
            db_path.exists() and db_path.stat().st_size > 0,
        ))
        checks.append(check(
            "checkpoint restores exact tick and generation",
            restored is not None
            and restored.tick == queen.tick
            and restored.generation == queen.generation,
        ))
        checks.append(check(
            "checkpoint restores exact protected and whole hashes",
            restored is not None
            and restored.protected_h256() == queen.protected_h256()
            and restored.whole_h256() == queen.whole_h256(),
        ))
        restored_z3 = restored.z3_runtime.visual_state() if restored is not None else {}
        checks.append(check(
            "checkpoint restores complete Z3 history identity",
            restored is not None
            and restored_z3["history_count"] == 32
            and restored_z3["latest"]["tick"] == 7200
            and restored_z3["latest"]["center_provenance_h256"]
            == z3["latest"]["center_provenance_h256"],
        ))

    report = {
        "schema": "ANTMUX-X72-Z3-CLEAN-BIRTH-LIFECYCLE-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "checks": checks,
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["checks_total"] == result["checks_passed"] else 1)
