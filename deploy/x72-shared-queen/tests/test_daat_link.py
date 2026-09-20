from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.daat_link import DaatLinkFrame
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

    latest_obj = queen.z3_runtime.latest
    assert latest_obj is not None
    gate = latest_obj.daat_gate
    link = latest_obj.daat_link
    payload = link.to_dict()
    checks.append(check(
        "B is the explicit common Da'at component",
        payload["common_b"] == list(gate.center),
    ))
    checks.append(check(
        "A is the explicit differential Da'at component",
        payload["differential_a"] == list(gate.residual),
    ))
    checks.append(check(
        "B/A still reconstruct G and D through the gate",
        all(
            math.isclose(
                gate.left[i],
                payload["common_b"][i] + payload["differential_a"][i],
                rel_tol=0.0,
                abs_tol=1e-12,
            )
            and math.isclose(
                gate.right[i],
                payload["common_b"][i] - payload["differential_a"][i],
                rel_tol=0.0,
                abs_tol=1e-12,
            )
            for i in range(12)
        ),
    ))
    checks.append(check(
        "default link score is bounded",
        0.0 <= payload["link_score"] <= 1.0
        and payload["verified"] is True,
    ))
    zero = DaatLinkFrame.from_gate(gate, weights=[0.0] * 12)
    checks.append(check(
        "zero weights produce zero central link",
        zero.link_score == 0.0,
    ))

    half = DaatLinkFrame.from_gate(gate, weights=[0.5] * 12)
    full = DaatLinkFrame.from_gate(gate, weights=[1.0] * 12)
    checks.append(check(
        "increasing all nonnegative weights cannot reduce Lc",
        0.0 <= half.link_score <= full.link_score <= 1.0,
    ))

    manual = 1.0 - math.prod(
        1.0 - s * w
        for s, w in zip(full.signal_strengths, full.weights)
    )
    checks.append(check(
        "Lc implements the declared complement-product formula",
        math.isclose(full.link_score, manual, rel_tol=0.0, abs_tol=1e-15),
    ))

    checks.append(check(
        "normalization is explicit and bounded per B channel",
        all(
            s == max(0.0, min(1.0, abs(b)))
            for s, b in zip(full.signal_strengths, full.common_b)
        ),
    ))
    before_stereo = latest_obj.stereo_source.to_dict()
    before_gate = latest_obj.daat_gate.to_dict()
    before_link = latest_obj.daat_link.to_dict()

    # Evidence accounting must observe, not feed back into Z / Da'at / Lc.
    queen.z3_runtime.daat_evidence.observe(
        stereo=latest_obj.stereo_source,
        daat=latest_obj.daat_gate,
        tick=latest_obj.tick,
    )

    checks.append(check(
        "Bayesian evidence update does not alter Z stereo",
        latest_obj.stereo_source.to_dict() == before_stereo,
    ))
    checks.append(check(
        "Bayesian evidence update does not alter Da'at B/A",
        latest_obj.daat_gate.to_dict() == before_gate,
    ))
    checks.append(check(
        "Bayesian evidence update does not alter Lc",
        latest_obj.daat_link.to_dict() == before_link,
    ))

    checks.append(check(
        "link candidate remains observation-only",
        payload["authority"] == "OBSERVATION_ONLY"
        and payload["mutates_queen"] is False
        and payload["physical_claim"] is False,
    ))
    checks.append(check(
        "link calculation does not mutate protected Queen state",
        queen.protected_h256() == protected_before,
    ))
    whole = queen.z3_runtime.whole_projection()
    checks.append(check(
        "link candidate stays outside authoritative whole-state hash",
        "daat_link" not in whole["latest"],
    ))

    report = {
        "schema": "ANTMUX-X72-DAAT-LINK-TEST-v0.2",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "link_score": payload["link_score"],
        "checks": checks,
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["checks_total"] == result["checks_passed"] else 1)
