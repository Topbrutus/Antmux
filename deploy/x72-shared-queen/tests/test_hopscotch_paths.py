from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.hopscotch_paths import CHANNELS, ROUTES, HopscotchRouteTrace
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
    hop = latest.hopscotch
    payload = hop.to_dict()
    checks.append(check(
        "ensemble reuses the same source and tick as Da'at link",
        hop.source_h256 == latest.daat_link.source_h256
        and hop.tick == latest.daat_link.tick
        and hop.generation == latest.daat_link.generation,
    ))

    checks.append(check(
        "four deterministic legal routes are exposed",
        set(route["name"] for route in payload["routes"]) == set(ROUTES)
        and len(payload["routes"]) == 4,
    ))

    checks.append(check(
        "every route visits each channel exactly once",
        all(
            len(route["route"]) == CHANNELS
            and set(route["route"]) == set(range(CHANNELS))
            for route in payload["routes"]
        ),
    ))

    checks.append(check(
        "all legal paths finish at the same commutative Lc",
        payload["route_invariant_final_link"] is True
        and all(
            math.isclose(
                route["final_link"],
                latest.daat_link.link_score,
                rel_tol=0.0,
                abs_tol=1e-12,
            )
            for route in payload["routes"]
        ),
    ))
    checks.append(check(
        "each route trace is monotonic and bounded",
        all(
            all(0.0 <= value <= 1.0 for value in route["cumulative_link"])
            and all(
                route["cumulative_link"][i]
                >= route["cumulative_link"][i - 1] - 1e-12
                for i in range(1, CHANNELS)
            )
            for route in payload["routes"]
        ),
    ))

    unequal = len({
        round(value, 15)
        for value in latest.daat_link.contributions
    }) > 1
    unique_traces = {
        tuple(round(value, 15) for value in route["cumulative_link"])
        for route in payload["routes"]
    }
    checks.append(check(
        "route order changes traversal history when channel contributions differ",
        (not unequal) or len(unique_traces) > 1,
    ))

    checks.append(check(
        "route semantics do not invent geometry",
        payload["route_semantics"] == "CHANNEL_ORDER_ONLY_NO_SPATIAL_MEANING"
        and payload["unmapped"] == [
            "VERTICAL_AXIS",
            "DEPTH_AXIS",
            "TREE_NODE_GEOMETRY",
            "SEFIROT_SEMANTICS",
        ],
    ))
    try:
        HopscotchRouteTrace.from_link(
            name="INVALID",
            route=tuple([0] * CHANNELS),
            link=latest.daat_link,
        )
        invalid_rejected = False
    except ValueError:
        invalid_rejected = True
    checks.append(check(
        "invalid route with repeated channel is rejected",
        invalid_rejected,
    ))

    before = latest.hopscotch.to_dict()
    queen.z3_runtime.daat_evidence.observe(
        stereo=latest.stereo_source,
        daat=latest.daat_gate,
        tick=latest.tick,
    )
    checks.append(check(
        "Bayesian evidence update does not alter hopscotch paths",
        latest.hopscotch.to_dict() == before,
    ))

    checks.append(check(
        "hopscotch layer is observation-only",
        payload["authority"] == "OBSERVATION_ONLY"
        and payload["mutates_queen"] is False
        and payload["physical_claim"] is False
        and payload["verified"] is True,
    ))
    checks.append(check(
        "hopscotch calculation does not mutate protected Queen state",
        queen.protected_h256() == protected_before,
    ))
    whole = queen.z3_runtime.whole_projection()
    checks.append(check(
        "hopscotch stays outside authoritative whole-state hash",
        "hopscotch" not in whole["latest"],
    ))

    hop_hash = payload["ensemble_h256"]
    whole_before = queen.whole_h256()
    restored = QueenCore.from_checkpoint(queen.to_checkpoint())
    restored_hop = restored.visual_state()["z3_runtime"]["latest"]["hopscotch"]
    checks.append(check(
        "checkpoint reconstructs same hopscotch ensemble",
        restored_hop["ensemble_h256"] == hop_hash
        and restored_hop["verified"] is True,
    ))
    checks.append(check(
        "checkpoint preserves authoritative whole hash",
        restored.whole_h256() == whole_before,
    ))

    report = {
        "schema": "ANTMUX-X72-HOPSCOTCH-TEST-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "target_link_score": payload["target_link_score"],
        "checks": checks,
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["checks_total"] == result["checks_passed"] else 1)
