from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from z3_echo import (
    PROVENANCE_SCHEMA,
    FiniteZTriad,
    Triad3,
    Z3EchoTransfer,
    deep_verify_provenance,
    euler_zyz,
    seal_provenance,
    series_h256,
    transfer_h256,
    verify_provenance,
)


def check(name: str, condition: bool, detail: str = "") -> dict[str, object]:
    if not condition:
        raise AssertionError(f"{name}: {detail}")
    return {"name": name, "ok": True}


def run() -> dict[str, object]:
    checks: list[dict[str, object]] = []

    angles = (0.41, -0.83, 1.37)
    transfer = Z3EchoTransfer(
        gain=complex(0.7, -0.2),
        delay=3,
        rotation=euler_zyz(*angles),
    )
    source = FiniteZTriad.from_samples(
        (
            Triad3(1.0, 2.0, 3.0),
            Triad3(-2.5, 0.25, 4.5),
            Triad3(0.0, -1.0, 2.0),
        )
    )
    echoed = transfer.apply(source)
    x72_candidate = "a" * 64
    x72_echo = "b" * 64

    frame = seal_provenance(
        source=source,
        transfer=transfer,
        echoed=echoed,
        euler_zyz_angles=angles,
        source_x72_candidate_h256=x72_candidate,
        source_x72_echo_h256=x72_echo,
    )

    checks.append(
        check(
            "frame schema and 13-node topology",
            frame.schema == PROVENANCE_SCHEMA
            and frame.triad_count == 4
            and frame.channels_per_triad == 3
            and frame.total_node_count == 13,
        )
    )

    checks.append(check("fast provenance verify", verify_provenance(frame, source=source, echoed=echoed)))
    checks.append(check("deep provenance verify", deep_verify_provenance(frame, source=source, echoed=echoed)))

    frame2 = seal_provenance(
        source=source,
        transfer=transfer,
        echoed=echoed,
        euler_zyz_angles=angles,
        source_x72_candidate_h256=x72_candidate,
        source_x72_echo_h256=x72_echo,
    )
    checks.append(
        check(
            "provenance seal deterministic",
            frame.provenance_h256 == frame2.provenance_h256
            and frame.transfer_h256 == frame2.transfer_h256
            and frame.source_series_h256 == frame2.source_series_h256
            and frame.echoed_series_h256 == frame2.echoed_series_h256,
        )
    )

    checks.append(
        check(
            "upstream X72 hashes preserved",
            frame.source_x72_candidate_h256 == x72_candidate
            and frame.source_x72_echo_h256 == x72_echo,
        )
    )

    checks.append(
        check(
            "Euler metadata is traceable",
            frame.rotation_source == "EULER_ZYZ"
            and frame.euler_order == "Z-Y-Z"
            and frame.euler_zyz_angles == angles,
        )
    )

    explicit_frame = seal_provenance(
        source=source,
        transfer=transfer,
        echoed=echoed,
    )
    checks.append(
        check(
            "explicit matrix mode does not invent Euler angles",
            explicit_frame.rotation_source == "EXPLICIT_MATRIX3"
            and explicit_frame.euler_order is None
            and explicit_frame.euler_zyz_angles is None,
        )
    )

    plus_zero = FiniteZTriad.from_samples((Triad3(0.0, 1.0, 2.0),))
    minus_zero = FiniteZTriad.from_samples((Triad3(-0.0, 1.0, 2.0),))
    checks.append(
        check(
            "signed zero canonicalizes identically",
            series_h256(plus_zero) == series_h256(minus_zero),
        )
    )

    same_transfer_hash = transfer_h256(
        transfer,
        euler_zyz_angles=angles,
    )
    checks.append(check("transfer hash matches frame", same_transfer_hash == frame.transfer_h256))

    tampered_echoed = FiniteZTriad.from_samples(
        (
            *echoed.samples[:-1],
            Triad3(99.0, 0.0, 0.0),
        )
    )
    try:
        verify_provenance(frame, source=source, echoed=tampered_echoed)
    except ValueError as exc:
        body_tamper_rejected = "echoed series hash mismatch" in str(exc)
    else:
        body_tamper_rejected = False
    checks.append(check("echoed body tamper rejected", body_tamper_rejected))

    tampered_frame = replace(frame, delay=frame.delay + 1)
    try:
        verify_provenance(tampered_frame, source=source, echoed=echoed)
    except ValueError as exc:
        frame_tamper_rejected = "provenance_h256" in str(exc)
    else:
        frame_tamper_rejected = False
    checks.append(check("frame content tamper rejected", frame_tamper_rejected))

    bad_angles = (angles[0], angles[1] + 0.2, angles[2])
    try:
        seal_provenance(
            source=source,
            transfer=transfer,
            echoed=echoed,
            euler_zyz_angles=bad_angles,
        )
    except ValueError as exc:
        bad_angle_rejected = "do not reproduce" in str(exc)
    else:
        bad_angle_rejected = False
    checks.append(check("false Euler metadata rejected", bad_angle_rejected))

    try:
        seal_provenance(
            source=source,
            transfer=transfer,
            echoed=echoed,
            source_x72_candidate_h256="not-a-hash",
        )
    except ValueError:
        malformed_upstream_rejected = True
    else:
        malformed_upstream_rejected = False
    checks.append(check("malformed upstream X72 hash rejected", malformed_upstream_rejected))

    unrelated_echoed = Z3EchoTransfer(
        gain=1.1,
        delay=3,
        rotation=euler_zyz(*angles),
    ).apply(source)
    forged_but_self_consistent = seal_provenance(
        source=source,
        transfer=transfer,
        echoed=unrelated_echoed,
        euler_zyz_angles=angles,
    )
    checks.append(
        check(
            "fast verify checks integrity chain but not semantic derivation",
            verify_provenance(
                forged_but_self_consistent,
                source=source,
                echoed=unrelated_echoed,
            ),
        )
    )
    try:
        deep_verify_provenance(
            forged_but_self_consistent,
            source=source,
            echoed=unrelated_echoed,
        )
    except ValueError as exc:
        deep_catches_semantic_forgery = "does not match transfer" in str(exc)
    else:
        deep_catches_semantic_forgery = False
    checks.append(
        check(
            "deep verify catches self-consistent semantic forgery",
            deep_catches_semantic_forgery,
        )
    )

    checks.append(
        check(
            "frame is serializable",
            isinstance(json.dumps(frame.to_dict(), sort_keys=True), str),
        )
    )

    report = {
        "schema": "ANTMUX-Z3-ECHO-PROVENANCE-TEST-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "checks": checks,
        "security_note": (
            "SHA-256 is an unkeyed deterministic integrity/provenance seal, "
            "not producer authentication"
        ),
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["checks_total"] == result["checks_passed"] else 1)
