from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.server import QueenCore


def check(name: str, condition: bool) -> dict[str, object]:
    if not condition:
        raise AssertionError(name)
    return {"name": name, "ok": True}


def run() -> dict[str, object]:
    checks: list[dict[str, object]] = []
    queen = QueenCore(seed=72)
    sampled = 0
    all_verified = True
    route_lengths_reference = None
    route_lengths_stable = True
    metric_stable = True
    distinct_hashes: set[str] = set()
    for _ in range(7200):
        queen.step()
        latest = queen.z3_runtime.latest
        if latest is None or latest.tick != queen.tick:
            continue

        sampled += 1
        geo = latest.graph_geometry
        payload = geo.to_dict()
        all_verified = all_verified and geo.verify()
        distinct_hashes.add(geo.geometry_h256)

        lengths = tuple(
            sorted(payload["route_lengths"].items())
        )
        if route_lengths_reference is None:
            route_lengths_reference = lengths
        else:
            route_lengths_stable = route_lengths_stable and (
                lengths == route_lengths_reference
            )

        metric_stable = metric_stable and (
            geo.edge_count == 12
            and geo.degree_sequence == tuple(2 for _ in range(12))
            and geo.diameter == 6
            and math.isclose(
                geo.mean_pair_distance,
                36 / 11,
                rel_tol=0.0,
                abs_tol=1e-15,
            )
            and geo.forman_edge_curvature == tuple(0 for _ in range(12))
        )
    checks.append(check(
        "full cycle yields 120 graph-geometry frames",
        sampled == 120,
    ))
    checks.append(check(
        "all graph-geometry frames verify",
        all_verified,
    ))
    checks.append(check(
        "candidate C12 metric invariants remain stable",
        metric_stable,
    ))
    checks.append(check(
        "route-length geometry remains stable across changing values",
        route_lengths_stable,
    ))
    checks.append(check(
        "geometry frame provenance evolves with source/tick",
        len(distinct_hashes) == sampled,
    ))

    report = {
        "schema": "ANTMUX-X72-GRAPH-GEOMETRY-SWEEP-TEST-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "sampled_frames": sampled,
        "distinct_geometry_hashes": len(distinct_hashes),
        "route_lengths": dict(route_lengths_reference or ()),
        "checks": checks,
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["checks_total"] == result["checks_passed"] else 1)
