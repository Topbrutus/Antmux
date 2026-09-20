from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.path_capacity import CHANNELS, PathCapacityFrame
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
    cap = latest.path_capacity
    payload = cap.to_dict()

    checks.append(check(
        "capacity frame reuses Daat Link source/tick/generation",
        cap.source_h256 == latest.daat_link.source_h256
        and cap.tick == latest.daat_link.tick
        and cap.generation == latest.daat_link.generation,
    ))

    checks.append(check(
        "complete 12-channel permutation space is counted exactly",
        cap.complete_path_space == math.factorial(12) == 479001600,
    ))

    checks.append(check(
        "theoretical prefix counts are exact permutations",
        all(
            stage.theoretical_prefixes == math.perm(CHANNELS, stage.depth)
            for stage in cap.stages
        )
        and cap.stages[-1].theoretical_prefixes == cap.complete_path_space,
    ))

    checks.append(check(
        "bounded beam never retains more than configured width",
        cap.beam_width == 64
        and cap.max_retained_prefixes <= 64
        and len(cap.sampled_routes) == 64,
    ))

    checks.append(check(
        "stored channel slots have a hard finite bound",
        cap.max_stored_channel_slots == 64 * 12 == 768,
    ))

    checks.append(check(
        "per-stage candidate generation is also bounded",
        cap.max_generated_candidates <= cap.beam_width * CHANNELS,
    ))

    checks.append(check(
        "all retained complete routes are unique legal permutations",
        len(set(cap.sampled_routes)) == len(cap.sampled_routes)
        and all(
            len(route) == 12 and set(route) == set(range(12))
            for route in cap.sampled_routes
        ),
    ))

    checks.append(check(
        "bounded sample does not pretend to materialize or cover all routes",
        payload["materializes_all_paths"] is False
        and payload["full_coverage_claim"] is False
        and payload["sampled_route_count"] < payload["complete_path_space"],
    ))

    checks.append(check(
        "sampled routes span more than one graph walk length",
        payload["sampled_route_length_min"]
        <= payload["sampled_route_length_mean"]
        <= payload["sampled_route_length_max"]
        and payload["sampled_route_length_min"]
        < payload["sampled_route_length_max"],
    ))

    duplicate = PathCapacityFrame.from_link(
        latest.daat_link,
        beam_width=cap.beam_width,
    )
    checks.append(check(
        "same source and beam policy reproduce identical capacity hash",
        duplicate.capacity_h256 == cap.capacity_h256
        and duplicate.sampled_routes == cap.sampled_routes,
    ))

    try:
        PathCapacityFrame.from_link(latest.daat_link, beam_width=0)
        invalid_rejected = False
    except ValueError:
        invalid_rejected = True
    checks.append(check(
        "invalid zero-width beam is rejected",
        invalid_rejected,
    ))

    before = cap.to_dict()
    queen.z3_runtime.daat_evidence.observe(
        stereo=latest.stereo_source,
        daat=latest.daat_gate,
        tick=latest.tick,
    )
    checks.append(check(
        "Bayes update cannot alter path-capacity frame",
        latest.path_capacity.to_dict() == before,
    ))

    checks.append(check(
        "capacity layer is observation-only and makes no Gabriel Horn claim",
        payload["authority"] == "OBSERVATION_ONLY"
        and payload["mutates_queen"] is False
        and payload["physical_claim"] is False
        and payload["gabriels_horn_claim"] is False,
    ))

    checks.append(check(
        "capacity calculation does not mutate protected Queen state",
        queen.protected_h256() == protected_before,
    ))

    whole = queen.z3_runtime.whole_projection()
    checks.append(check(
        "path capacity stays outside authoritative whole-state hash",
        "path_capacity" not in whole["latest"],
    ))

    capacity_hash = cap.capacity_h256
    whole_before = queen.whole_h256()
    restored = QueenCore.from_checkpoint(queen.to_checkpoint())
    restored_cap = restored.visual_state()["z3_runtime"]["latest"]["path_capacity"]
    checks.append(check(
        "checkpoint reconstructs identical capacity frame",
        restored_cap["capacity_h256"] == capacity_hash
        and restored_cap["verified"] is True,
    ))
    checks.append(check(
        "checkpoint preserves authoritative whole hash",
        restored.whole_h256() == whole_before,
    ))

    report = {
        "schema": "ANTMUX-X72-PATH-CAPACITY-TEST-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "complete_path_space": cap.complete_path_space,
        "sampled_route_count": len(cap.sampled_routes),
        "max_generated_candidates": cap.max_generated_candidates,
        "checks": checks,
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["checks_total"] == result["checks_passed"] else 1)
