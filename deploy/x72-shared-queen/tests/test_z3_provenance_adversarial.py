from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from z3_echo import (
    FiniteZTriad,
    Triad3,
    Z3EchoTransfer,
    deep_verify_provenance,
    euler_zyz,
    seal_provenance,
    series_h256,
    verify_provenance,
)
from z3_echo.provenance import _frame_h256


def check(name: str, condition: bool, detail: str = "") -> dict[str, object]:
    if not condition:
        raise AssertionError(f"{name}: {detail}")
    return {"name": name, "ok": True}


def reseal(frame, **changes):
    modified = replace(frame, **changes, provenance_h256="0" * 64)
    return replace(modified, provenance_h256=_frame_h256(modified))


def run() -> dict[str, object]:
    checks: list[dict[str, object]] = []

    angles = (0.23, -1.1, 0.91)
    transfer = Z3EchoTransfer(
        gain=complex(-0.6, 0.4),
        delay=2,
        rotation=euler_zyz(*angles),
    )
    source = FiniteZTriad.from_samples(
        (
            Triad3(1, 2, 3),
            Triad3(-4, 5, 6),
            Triad3(0.25, -0.5, 1.5),
        )
    )
    echoed = transfer.apply(source)
    frame = seal_provenance(
        source=source,
        transfer=transfer,
        echoed=echoed,
        euler_zyz_angles=angles,
        source_x72_candidate_h256="c" * 64,
        source_x72_echo_h256="d" * 64,
    )

    cases = []

    bad_topology = reseal(frame, total_node_count=12)
    try:
        verify_provenance(bad_topology, source=source, echoed=echoed)
    except ValueError as exc:
        cases.append("topology" in str(exc))
    else:
        cases.append(False)

    bad_rotation_source = reseal(frame, rotation_source="EULER_XYZ")
    try:
        verify_provenance(bad_rotation_source, source=source, echoed=echoed)
    except ValueError as exc:
        cases.append("rotation_source" in str(exc))
    else:
        cases.append(False)

    bad_order = reseal(frame, euler_order="Z-X-Z")
    try:
        verify_provenance(bad_order, source=source, echoed=echoed)
    except ValueError as exc:
        cases.append("euler_order" in str(exc))
    else:
        cases.append(False)

    bad_series_hash = reseal(frame, source_series_h256="x" * 64)
    try:
        verify_provenance(bad_series_hash, source=source, echoed=echoed)
    except ValueError:
        cases.append(True)
    else:
        cases.append(False)

    uppercase_upstream = reseal(frame, source_x72_echo_h256="D" * 64)
    try:
        verify_provenance(uppercase_upstream, source=source, echoed=echoed)
    except ValueError:
        cases.append(True)
    else:
        cases.append(False)

    checks.append(check("self-consistent metadata tampering rejected", all(cases), detail=str(cases)))

    wrong_source = FiniteZTriad.from_samples(
        (
            Triad3(1, 2, 3),
            Triad3(-4, 5, 6),
            Triad3(9, 9, 9),
        )
    )
    try:
        verify_provenance(frame, source=wrong_source, echoed=echoed)
    except ValueError as exc:
        wrong_source_rejected = "source series hash mismatch" in str(exc)
    else:
        wrong_source_rejected = False
    checks.append(check("wrong source coefficients rejected", wrong_source_rejected))

    wrong_echoed = FiniteZTriad.from_samples(
        (
            *echoed.samples[:-1],
            Triad3(0, 0, 0),
        )
    )
    try:
        verify_provenance(frame, source=source, echoed=wrong_echoed)
    except ValueError as exc:
        wrong_echo_rejected = "echoed series hash mismatch" in str(exc)
    else:
        wrong_echo_rejected = False
    checks.append(check("wrong echoed coefficients rejected", wrong_echo_rejected))

    original_apply = Z3EchoTransfer.apply

    def forbidden_apply(self, input_source):
        raise AssertionError("fast verify must not recompute transfer.apply")

    Z3EchoTransfer.apply = forbidden_apply
    try:
        fast_no_recompute = verify_provenance(frame, source=source, echoed=echoed)
    finally:
        Z3EchoTransfer.apply = original_apply
    checks.append(check("fast verify avoids transfer recomputation", fast_no_recompute))

    checks.append(
        check(
            "deep verify still recomputes semantic derivation",
            deep_verify_provenance(frame, source=source, echoed=echoed),
        )
    )

    try:
        series_h256("not-a-series")
    except TypeError:
        wrong_type_rejected = True
    else:
        wrong_type_rejected = False
    checks.append(check("series hash type discipline", wrong_type_rejected))

    repeated = [series_h256(source) for _ in range(20)]
    checks.append(check("series hash deterministic across repeated calls", len(set(repeated)) == 1))

    checks.append(
        check(
            "sealed frame JSON output stable",
            json.dumps(frame.to_dict(), sort_keys=True)
            == json.dumps(frame.to_dict(), sort_keys=True),
        )
    )

    forged_transfer = Z3EchoTransfer(
        gain=2.0,
        delay=frame.delay,
        rotation=frame.rotation,
    )
    forged_echoed = forged_transfer.apply(source)
    forged = seal_provenance(
        source=source,
        transfer=forged_transfer,
        echoed=forged_echoed,
        euler_zyz_angles=angles,
    )
    checks.append(
        check(
            "unkeyed seal accepts a new self-consistent producer-independent chain",
            verify_provenance(forged, source=source, echoed=forged_echoed),
        )
    )

    report = {
        "schema": "ANTMUX-Z3-ECHO-PROVENANCE-ADVERSARIAL-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "checks": checks,
        "security_limit": (
            "unkeyed SHA-256 detects inconsistency/tampering against a sealed chain "
            "but does not authenticate who produced a new self-consistent chain"
        ),
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["checks_total"] == result["checks_passed"] else 1)
