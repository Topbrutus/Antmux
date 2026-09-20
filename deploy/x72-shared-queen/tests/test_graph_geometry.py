from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.graph_geometry import CHANNELS, ring_distance
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
    geo = latest.graph_geometry
    payload = geo.to_dict()

    checks.append(check(
        "geometry reuses Hopscotch source/tick/generation",
        geo.source_h256 == latest.hopscotch.source_h256
        and geo.tick == latest.hopscotch.tick
        and geo.generation == latest.hopscotch.generation,
    ))

    checks.append(check(
        "candidate graph is exactly an operational C12 cycle",
        payload["topology"] == "CYCLE_C12_OPERATIONAL_ONLY"
        and geo.edge_count == 12
        and geo.degree_sequence == tuple(2 for _ in range(12))
        and geo.diameter == 6,
    ))

    checks.append(check(
        "mean pair distance matches exact C12 value",
        math.isclose(
            geo.mean_pair_distance,
            36 / 11,
            rel_tol=0.0,
            abs_tol=1e-15,
        ),
    ))

    checks.append(check(
        "unweighted Forman diagnostic is uniformly zero on C12",
        geo.forman_edge_curvature == tuple(0 for _ in range(12)),
    ))

    metric_ok = True
    for a in range(CHANNELS):
        for b in range(CHANNELS):
            metric_ok = metric_ok and ring_distance(a, b) == ring_distance(b, a)
            for c in range(CHANNELS):
                metric_ok = metric_ok and (
                    ring_distance(a, c)
                    <= ring_distance(a, b) + ring_distance(b, c)
                )
    checks.append(check(
        "shortest-path distance satisfies symmetry and triangle inequality",
        metric_ok,
    ))

    checks.append(check(
        "cycle rotations and reflections preserve each route metric",
        all(route.verify() for route in geo.routes),
    ))

    lengths = {route.name: route.walk_length for route in geo.routes}
    checks.append(check(
        "route lengths distinguish at least two traversal families",
        len(set(lengths.values())) > 1
        and payload["route_lengths_distinguish_some_paths"] is True,
    ))

    by_name = {route.name: route for route in geo.routes}
    checks.append(check(
        "forward and reverse have identical graph length",
        by_name["FORWARD"].walk_length == by_name["REVERSE"].walk_length,
    ))

    before = geo.to_dict()
    queen.z3_runtime.daat_evidence.observe(
        stereo=latest.stereo_source,
        daat=latest.daat_gate,
        tick=latest.tick,
    )
    checks.append(check(
        "Bayes update cannot alter graph geometry",
        latest.graph_geometry.to_dict() == before,
    ))

    checks.append(check(
        "graph layer makes no continuous or physical curvature claim",
        payload["authority"] == "OBSERVATION_ONLY"
        and payload["mutates_queen"] is False
        and payload["physical_claim"] is False
        and payload["riemannian_claim"] is False,
    ))

    checks.append(check(
        "graph calculation does not mutate protected Queen state",
        queen.protected_h256() == protected_before,
    ))

    whole = queen.z3_runtime.whole_projection()
    checks.append(check(
        "graph geometry stays outside authoritative whole-state hash",
        "graph_geometry" not in whole["latest"],
    ))

    geometry_hash = geo.geometry_h256
    whole_before = queen.whole_h256()
    restored = QueenCore.from_checkpoint(queen.to_checkpoint())
    restored_geo = restored.visual_state()["z3_runtime"]["latest"]["graph_geometry"]
    checks.append(check(
        "checkpoint reconstructs identical graph geometry",
        restored_geo["geometry_h256"] == geometry_hash
        and restored_geo["verified"] is True,
    ))
    checks.append(check(
        "checkpoint preserves authoritative whole hash",
        restored.whole_h256() == whole_before,
    ))

    report = {
        "schema": "ANTMUX-X72-GRAPH-GEOMETRY-TEST-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "route_lengths": lengths,
        "checks": checks,
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["checks_total"] == result["checks_passed"] else 1)
