from __future__ import annotations

import copy
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.server import (
    COMPLETE_RELATIONS_K7,
    RELATION_COUNT_K7,
    RELATION_TOPOLOGY_VERSION,
    QueenCore,
    relations_are_complete_k7,
)


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


def run() -> dict[str, object]:
    checks: list[dict[str, object]] = []
    queen = QueenCore(seed=72)

    expected = {tuple(edge) for edge in COMPLETE_RELATIONS_K7}
    observed = {tuple(edge) for edge in queen.relations}

    checks.append(check(
        "K7 has exactly 21 unique relations",
        RELATION_COUNT_K7 == 21
        and len(queen.relations) == 21
        and len(observed) == 21,
    ))
    checks.append(check(
        "all 21 unordered synapse pairs are present",
        observed == expected and relations_are_complete_k7(queen.relations),
    ))

    degrees = Counter()
    for left, right in queen.relations:
        degrees[left] += 1
        degrees[right] += 1
    checks.append(check(
        "every one of seven synapses has degree six",
        all(degrees[index] == 6 for index in range(7)),
        detail=str(dict(degrees)),
    ))
    checks.append(check(
        "graph contains no self-edge and every endpoint is valid",
        all(left != right and 0 <= left < 7 and 0 <= right < 7
            for left, right in queen.relations),
    ))

    state = queen.visual_state()
    checks.append(check(
        "public state exposes complete topology evidence",
        state["relation_topology"] == RELATION_TOPOLOGY_VERSION
        and state["relation_count"] == 21
        and state["relation_possible"] == 21
        and state["relation_complete"] is True,
    ))
    checks.append(check(
        "relation topology participates in protected integrity",
        queen.protected_projection()["relation_topology"] == RELATION_TOPOLOGY_VERSION
        and queen.integrity_match() is True,
    ))

    restored = QueenCore.from_checkpoint(queen.to_checkpoint())
    checks.append(check(
        "checkpoint round trip preserves complete K7 topology",
        restored.relations == queen.relations
        and restored.visual_state()["relation_complete"] is True
        and restored.protected_h256() == queen.protected_h256(),
    ))

    legacy = copy.deepcopy(queen.to_checkpoint())
    legacy.pop("relation_topology", None)
    legacy["relations"] = legacy["relations"][:10]
    checks.append(expect_raises(
        "legacy incomplete relation checkpoint is rejected",
        ValueError,
        lambda: QueenCore.from_checkpoint(legacy),
    ))

    malformed = copy.deepcopy(queen.to_checkpoint())
    malformed["relations"][-1] = malformed["relations"][0]
    checks.append(expect_raises(
        "duplicate-edge relation checkpoint is rejected",
        ValueError,
        lambda: QueenCore.from_checkpoint(malformed),
    ))

    report = {
        "schema": "ANTMUX-X72-K7-COMPLETE-RELATIONS-TEST-v1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "checks": checks,
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["checks_total"] == result["checks_passed"] else 1)
