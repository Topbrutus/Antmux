from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.relation_runtime import RelationRuntime
from app.server import COMPLETE_RELATIONS_K7, QueenCore, SynapseState


def check(name: str, condition: bool, detail: str = "") -> dict[str, object]:
    if not condition:
        raise AssertionError(f"{name}: {detail}")
    return {"name": name, "ok": True}


def expect_raises(name: str, exc_type, fn) -> dict[str, object]:
    try:
        fn()
    except exc_type:
        return {"name": name, "ok": True}
    raise AssertionError(f"{name}: expected {exc_type.__name__}")


def make_synapses() -> list[SynapseState]:
    out = []
    for index in range(7):
        out.append(
            SynapseState(
                synapse_id=f"S{index + 1}",
                role=f"R{index + 1}",
                activity=0.1 * (index + 1),
                memory=0.05 * (index + 1),
                crystal=0.02 * (index + 1),
            )
        )
    return out


def run() -> dict[str, object]:
    checks: list[dict[str, object]] = []
    relations = [list(edge) for edge in COMPLETE_RELATIONS_K7]
    synapses = make_synapses()
    runtime = RelationRuntime()

    checks.append(check(
        "relation runtime starts observation-only and empty",
        runtime.last_sample_tick == -1 and runtime.stats == {},
    ))
    checks.append(check(
        "non-sample tick is ignored",
        runtime.observe(
            tick=59,
            generation=0,
            synapses=synapses,
            relations=relations,
        ) is False,
    ))

    expected_active = sum(
        1
        for left, right in COMPLETE_RELATIONS_K7
        if (synapses[left].activity + synapses[right].activity) / 2.0 > 0.25
    )
    checks.append(check(
        "sample tick records the deterministic relation sample",
        runtime.observe(
            tick=60,
            generation=0,
            synapses=synapses,
            relations=relations,
        ) is True,
    ))
    state = runtime.visual_state(
        tick=60,
        generation=0,
        synapses=synapses,
        relations=relations,
    )
    checks.append(check(
        "all 21 K7 relations are measured",
        state["relation_count"] == 21 and len(state["relations"]) == 21,
    ))
    checks.append(check(
        "pulse total equals active sampled relations",
        state["active_relation_count"] == expected_active
        and state["pulse_total"] == expected_active,
        detail=str(state),
    ))

    s1s7 = next(item for item in state["relations"] if item["relation_id"] == "S1-S7")
    checks.append(check(
        "activity gradient direction is explicit and non-physical",
        s1s7["activity_gradient_direction"] == "S7_TO_S1"
        and abs(s1s7["activity_gap"] - 0.6) < 1e-12
        and state["physical_claim"] is False
        and state["mutates_queen"] is False,
    ))
    checks.append(check(
        "same sample tick cannot double-count",
        runtime.observe(
            tick=60,
            generation=0,
            synapses=synapses,
            relations=relations,
        ) is False
        and runtime.visual_state(
            tick=60,
            generation=0,
            synapses=synapses,
            relations=relations,
        )["pulse_total"] == expected_active,
    ))

    runtime.observe(
        tick=120,
        generation=0,
        synapses=synapses,
        relations=relations,
    )
    checks.append(check(
        "next sample advances pulse counters",
        runtime.visual_state(
            tick=120,
            generation=0,
            synapses=synapses,
            relations=relations,
        )["pulse_total"] == expected_active * 2,
    ))

    checkpoint = runtime.to_checkpoint()
    restored = RelationRuntime.from_checkpoint(copy.deepcopy(checkpoint))
    restored_state = restored.visual_state(
        tick=120,
        generation=0,
        synapses=synapses,
        relations=relations,
    )
    checks.append(check(
        "relation telemetry checkpoint preserves counters and hash",
        restored_state["pulse_total"] == expected_active * 2
        and restored_state["runtime_h256"] == state_after_hash(runtime, synapses, relations),
    ))

    malformed = copy.deepcopy(checkpoint)
    first_key = next(iter(malformed["stats"]))
    malformed["stats"][first_key]["pulse_count"] = -1
    checks.append(expect_raises(
        "negative pulse count is rejected",
        ValueError,
        lambda: RelationRuntime.from_checkpoint(malformed),
    ))

    queen = QueenCore(seed=72)
    protected_before = queen.protected_h256()
    whole_before = queen.whole_h256()
    for _ in range(720):
        queen.step()
    queen_state = queen.visual_state()
    checks.append(check(
        "Queen exposes live 21-edge relation telemetry",
        queen_state["relation_runtime"]["relation_count"] == 21
        and queen_state["relation_runtime"]["last_sample_tick"] == 720,
    ))
    checks.append(check(
        "relation telemetry never mutates protected Queen identity",
        queen.protected_h256() == protected_before,
    ))
    checks.append(check(
        "relation telemetry stays outside authoritative whole hash",
        "relation_runtime" not in queen.whole_projection()
        and whole_before != queen.whole_h256(),
    ))

    round_trip = QueenCore.from_checkpoint(queen.to_checkpoint())
    checks.append(check(
        "Queen checkpoint preserves relation telemetry counters",
        round_trip.visual_state()["relation_runtime"]["pulse_total"]
        == queen_state["relation_runtime"]["pulse_total"],
    ))
    checks.append(check(
        "Queen checkpoint preserves authoritative whole hash",
        round_trip.whole_h256() == queen.whole_h256(),
    ))

    legacy_checkpoint = queen.to_checkpoint()
    legacy_checkpoint.pop("relation_runtime", None)
    legacy = QueenCore.from_checkpoint(legacy_checkpoint)
    checks.append(check(
        "new runtime accepts K7 checkpoint without telemetry history",
        legacy.visual_state()["relation_runtime"]["pulse_total"] == 0
        and legacy.whole_h256() == queen.whole_h256(),
    ))

    report = {
        "schema": "ANTMUX-X72-RELATION-RUNTIME-TEST-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "checks": checks,
    }
    print(json.dumps(report, sort_keys=True))
    return report


def state_after_hash(
    runtime: RelationRuntime,
    synapses: list[SynapseState],
    relations: list[list[int]],
) -> str:
    return runtime.visual_state(
        tick=120,
        generation=0,
        synapses=synapses,
        relations=relations,
    )["runtime_h256"]


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["checks_total"] == result["checks_passed"] else 1)
