from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.z3_runtime import Z3RuntimeBridge


def synapse(index: int, *, activity: float = 0.1, memory: float = 0.2, crystal: float = 0.3):
    return SimpleNamespace(
        synapse_id=f"S{index}",
        activity=activity,
        memory=memory,
        crystal=crystal,
    )


def queen_synapses():
    return [synapse(i) for i in range(1, 8)]


def expect_raises(name: str, exc_type, fn):
    try:
        fn()
    except exc_type:
        return {"name": name, "ok": True}
    raise AssertionError(f"{name}: expected {exc_type.__name__}")


def run() -> dict[str, object]:
    checks: list[dict[str, object]] = []

    checks.append(expect_raises(
        "zero sample interval rejected",
        ValueError,
        lambda: Z3RuntimeBridge(sample_interval_ticks=0),
    ))
    checks.append(expect_raises(
        "zero history size rejected",
        ValueError,
        lambda: Z3RuntimeBridge(history_size=0),
    ))

    bridge = Z3RuntimeBridge()
    checks.append(expect_raises(
        "wrong synapse count rejected",
        ValueError,
        lambda: bridge.observe(tick=60, generation=0, synapses=queen_synapses()[:-1]),
    ))

    bad_nan = queen_synapses()
    bad_nan[2].activity = math.nan
    checks.append(expect_raises(
        "NaN observable rejected",
        ValueError,
        lambda: Z3RuntimeBridge().observe(tick=60, generation=0, synapses=bad_nan),
    ))

    bad_inf = queen_synapses()
    bad_inf[4].memory = math.inf
    checks.append(expect_raises(
        "infinite observable rejected",
        ValueError,
        lambda: Z3RuntimeBridge().observe(tick=60, generation=0, synapses=bad_inf),
    ))

    original = queen_synapses()
    before = copy.deepcopy(original)
    mutation_bridge = Z3RuntimeBridge()
    assert mutation_bridge.observe(tick=60, generation=0, synapses=original) is True
    checks.append({
        "name": "observe leaves caller synapses unchanged",
        "ok": [vars(item) for item in original] == [vars(item) for item in before],
    })

    count_before = len(mutation_bridge.history)
    latest_before = mutation_bridge.latest
    duplicate = mutation_bridge.observe(tick=60, generation=0, synapses=original)
    checks.append({
        "name": "duplicate sample tick ignored",
        "ok": duplicate is False
        and len(mutation_bridge.history) == count_before
        and mutation_bridge.latest == latest_before,
    })
    reordered = queen_synapses()
    reordered[0], reordered[1] = reordered[1], reordered[0]
    checks.append(expect_raises(
        "reordered semantic synapse ids rejected",
        ValueError,
        lambda: Z3RuntimeBridge().observe(
            tick=60,
            generation=0,
            synapses=reordered,
        ),
    ))

    bounded = Z3RuntimeBridge(history_size=3)
    for tick in (60, 120, 180, 240, 300):
        assert bounded.observe(
            tick=tick,
            generation=tick // 7200,
            synapses=queen_synapses(),
        ) is True
    checks.append({
        "name": "history remains bounded",
        "ok": len(bounded.history) == 3 and bounded.latest.sample_count == 3,
    })

    empty = Z3RuntimeBridge.from_checkpoint(
        {"schema": "WRONG"},
        tick=999,
        generation=7,
    )
    checks.append({
        "name": "foreign checkpoint schema resets empty",
        "ok": empty.latest is None and empty.history == [],
    })
    malformed_checkpoint = {
        "schema": "ANTMUX-X72-Z3-RUNTIME-v0.1",
        "sample_interval_ticks": 60,
        "history_size": 32,
        "history": [[0.0] * 11],
        "last_sample_tick": 60,
    }
    checks.append(expect_raises(
        "malformed checkpoint channel count rejected",
        ValueError,
        lambda: Z3RuntimeBridge.from_checkpoint(
            malformed_checkpoint,
            tick=60,
            generation=0,
        ),
    ))

    report = {
        "schema": "ANTMUX-X72-Z3-RUNTIME-BRIDGE-ADVERSARIAL-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "checks": checks,
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["checks_total"] == result["checks_passed"] else 1)
