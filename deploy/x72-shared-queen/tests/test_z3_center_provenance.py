from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from z3_echo import (
    CENTER_PROVENANCE_SCHEMA,
    CENTER_SCHEDULE_VERSION,
    CenterCoupling12,
    CenterSummary3WithResidual,
    FourTriadZState,
    FiniteZTriad,
    Triad3,
    center_coupling_h256,
    center_state_h256,
    center_summary_h256,
    deep_verify_center_provenance,
    seal_center_provenance,
    verify_center_provenance,
)


def check(name: str, condition: bool, detail: str = "") -> dict[str, object]:
    if not condition:
        raise AssertionError(f"{name}: {detail}")
    return {"name": name, "ok": True}


def make_state() -> FourTriadZState:
    groups = []
    for group in range(4):
        groups.append(
            FiniteZTriad.from_samples(
                (
                    Triad3(group + 1, group + 2, group + 3),
                    Triad3(
                        complex(group + 0.25, 0.1 * group),
                        complex(-group - 0.5, 0.05 * group),
                        group * 2.0 + 0.75,
                    ),
                    Triad3(
                        3.0 - group,
                        complex(group / 3.0, -group / 7.0),
                        (-1) ** group * 1.25,
                    ),
                )
            )
        )
    return FourTriadZState(tuple(groups))


def run() -> dict[str, object]:
    checks: list[dict[str, object]] = []

    source = make_state()
    coupling = CenterCoupling12.from_theta(0.43)
    coupled = coupling.apply(source)
    summary = CenterSummary3WithResidual.decompose(coupled)

    upstream = "e" * 64
    frame = seal_center_provenance(
        source=source,
        coupling=coupling,
        coupled=coupled,
        summary=summary,
        source_z3_echo_provenance_h256=upstream,
    )

    checks.append(
        check(
            "center provenance schema/version",
            frame.schema == CENTER_PROVENANCE_SCHEMA
            and frame.schedule_version == CENTER_SCHEDULE_VERSION,
        )
    )

    checks.append(
        check(
            "fast center provenance verify",
            verify_center_provenance(
                frame,
                source=source,
                coupled=coupled,
                summary=summary,
            ),
        )
    )

    checks.append(
        check(
            "deep center provenance verify",
            deep_verify_center_provenance(
                frame,
                source=source,
                coupled=coupled,
                summary=summary,
            ),
        )
    )

    frame2 = seal_center_provenance(
        source=source,
        coupling=coupling,
        coupled=coupled,
        summary=summary,
        source_z3_echo_provenance_h256=upstream,
    )
    checks.append(
        check(
            "center provenance deterministic",
            frame.provenance_h256 == frame2.provenance_h256
            and frame.source_state_h256 == frame2.source_state_h256
            and frame.coupled_state_h256 == frame2.coupled_state_h256
            and frame.summary_h256 == frame2.summary_h256,
        )
    )

    checks.append(
        check(
            "center state/coupling/summary hashes traceable",
            frame.source_state_h256 == center_state_h256(source)
            and frame.coupling_h256 == center_coupling_h256(coupling)
            and frame.coupled_state_h256 == center_state_h256(coupled)
            and frame.summary_h256 == center_summary_h256(summary),
        )
    )

    checks.append(
        check(
            "upstream Z3 echo provenance preserved",
            frame.source_z3_echo_provenance_h256 == upstream,
        )
    )

    checks.append(
        check(
            "center frame exposes exactly three residual hashes",
            len(frame.residual_series_h256) == 3,
        )
    )

    tampered_source = FourTriadZState(
        (
            source.triads[0],
            source.triads[1],
            source.triads[2],
            FiniteZTriad.from_samples(
                (
                    Triad3(99, 99, 99),
                    *source.triads[3].samples[1:],
                )
            ),
        )
    )
    try:
        verify_center_provenance(
            frame,
            source=tampered_source,
            coupled=coupled,
            summary=summary,
        )
    except ValueError as exc:
        source_tamper_rejected = "source center-state hash mismatch" in str(exc)
    else:
        source_tamper_rejected = False
    checks.append(check("source state tamper rejected", source_tamper_rejected))

    tampered_coupled = FourTriadZState(
        (
            coupled.triads[0],
            coupled.triads[1],
            coupled.triads[2],
            FiniteZTriad.from_samples(
                (
                    *coupled.triads[3].samples[:-1],
                    Triad3(77, 0, 0),
                )
            ),
        )
    )
    try:
        verify_center_provenance(
            frame,
            source=source,
            coupled=tampered_coupled,
            summary=summary,
        )
    except ValueError as exc:
        coupled_tamper_rejected = "coupled center-state hash mismatch" in str(exc)
    else:
        coupled_tamper_rejected = False
    checks.append(check("coupled state tamper rejected", coupled_tamper_rejected))

    wrong_summary = CenterSummary3WithResidual.decompose(source)
    try:
        verify_center_provenance(
            frame,
            source=source,
            coupled=coupled,
            summary=wrong_summary,
        )
    except ValueError as exc:
        summary_tamper_rejected = "center summary hash mismatch" in str(exc)
    else:
        summary_tamper_rejected = False
    checks.append(check("wrong center summary rejected", summary_tamper_rejected))

    frame_tampered = replace(frame, theta=frame.theta + 0.1)
    try:
        verify_center_provenance(
            frame_tampered,
            source=source,
            coupled=coupled,
            summary=summary,
        )
    except ValueError as exc:
        frame_tamper_rejected = "provenance_h256" in str(exc)
    else:
        frame_tamper_rejected = False
    checks.append(check("center frame metadata tamper rejected", frame_tamper_rejected))

    try:
        seal_center_provenance(
            source=source,
            coupling=coupling,
            coupled=coupled,
            summary=summary,
            source_z3_echo_provenance_h256="bad",
        )
    except ValueError:
        bad_upstream_rejected = True
    else:
        bad_upstream_rejected = False
    checks.append(check("malformed upstream Z3 hash rejected", bad_upstream_rejected))

    unrelated_coupling = CenterCoupling12.from_theta(0.9)
    unrelated_coupled = unrelated_coupling.apply(source)
    forged = seal_center_provenance(
        source=source,
        coupling=coupling,
        coupled=unrelated_coupled,
        summary=CenterSummary3WithResidual.decompose(unrelated_coupled),
    )
    checks.append(
        check(
            "fast verify checks sealed chain without semantic recomputation",
            verify_center_provenance(
                forged,
                source=source,
                coupled=unrelated_coupled,
                summary=CenterSummary3WithResidual.decompose(unrelated_coupled),
            ),
        )
    )
    try:
        deep_verify_center_provenance(
            forged,
            source=source,
            coupled=unrelated_coupled,
            summary=CenterSummary3WithResidual.decompose(unrelated_coupled),
        )
    except ValueError as exc:
        deep_catches_wrong_coupling = "does not match center coupling" in str(exc)
    else:
        deep_catches_wrong_coupling = False
    checks.append(
        check(
            "deep verify catches self-consistent wrong center derivation",
            deep_catches_wrong_coupling,
        )
    )

    checks.append(
        check(
            "center provenance frame serializable",
            isinstance(json.dumps(frame.to_dict(), sort_keys=True), str),
        )
    )

    report = {
        "schema": "ANTMUX-Z3-CENTER-PROVENANCE-TEST-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "checks": checks,
        "security_note": (
            "unkeyed SHA-256 seals deterministic integrity/provenance; "
            "deep verification proves the configured center derivation"
        ),
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["checks_total"] == result["checks_passed"] else 1)
