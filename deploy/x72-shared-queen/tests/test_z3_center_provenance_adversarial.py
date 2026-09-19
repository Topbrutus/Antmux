from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from z3_echo import (
    CENTER_SCHEDULE_VERSION,
    CenterCoupling12,
    CenterSummary3WithResidual,
    FourTriadZState,
    FiniteZTriad,
    Triad3,
    deep_verify_center_provenance,
    seal_center_provenance,
    verify_center_provenance,
)
from z3_echo.center_provenance import _frame_h256


def check(name: str, condition: bool, detail: str = "") -> dict[str, object]:
    if not condition:
        raise AssertionError(f"{name}: {detail}")
    return {"name": name, "ok": True}


def reseal(frame, **changes):
    candidate = replace(frame, **changes, provenance_h256="0" * 64)
    return replace(candidate, provenance_h256=_frame_h256(candidate))


def make_state(offset: float = 0.0) -> FourTriadZState:
    groups = []
    for group in range(4):
        groups.append(
            FiniteZTriad.from_samples(
                (
                    Triad3(group + 1 + offset, group + 2, group + 3),
                    Triad3(
                        complex(group + 0.5, group / 9),
                        -group - 0.25,
                        group * 1.5 + offset,
                    ),
                )
            )
        )
    return FourTriadZState(tuple(groups))


def run() -> dict[str, object]:
    checks: list[dict[str, object]] = []

    source = make_state()
    coupling = CenterCoupling12.from_theta(0.52)
    coupled = coupling.apply(source)
    summary = CenterSummary3WithResidual.decompose(coupled)
    frame = seal_center_provenance(
        source=source,
        coupling=coupling,
        coupled=coupled,
        summary=summary,
        source_z3_echo_provenance_h256="f" * 64,
    )

    tamper_results: list[bool] = []

    bad_version = reseal(frame, schedule_version="WRONG-SCHEDULE")
    try:
        verify_center_provenance(
            bad_version,
            source=source,
            coupled=coupled,
            summary=summary,
        )
    except ValueError as exc:
        tamper_results.append("schedule version" in str(exc))
    else:
        tamper_results.append(False)

    bad_source_hash = reseal(frame, source_state_h256="x" * 64)
    try:
        verify_center_provenance(
            bad_source_hash,
            source=source,
            coupled=coupled,
            summary=summary,
        )
    except ValueError:
        tamper_results.append(True)
    else:
        tamper_results.append(False)

    bad_residual_hashes = reseal(
        frame,
        residual_series_h256=("a" * 64, "b" * 64, "c" * 64),
    )
    try:
        verify_center_provenance(
            bad_residual_hashes,
            source=source,
            coupled=coupled,
            summary=summary,
        )
    except ValueError as exc:
        tamper_results.append("residual" in str(exc))
    else:
        tamper_results.append(False)

    bad_upstream = reseal(
        frame,
        source_z3_echo_provenance_h256="F" * 64,
    )
    try:
        verify_center_provenance(
            bad_upstream,
            source=source,
            coupled=coupled,
            summary=summary,
        )
    except ValueError:
        tamper_results.append(True)
    else:
        tamper_results.append(False)

    checks.append(
        check(
            "self-consistent metadata/hash tampering rejected",
            all(tamper_results),
            detail=str(tamper_results),
        )
    )

    wrong_source = make_state(offset=7.0)
    try:
        verify_center_provenance(
            frame,
            source=wrong_source,
            coupled=coupled,
            summary=summary,
        )
    except ValueError as exc:
        wrong_source_rejected = "source center-state hash mismatch" in str(exc)
    else:
        wrong_source_rejected = False
    checks.append(check("wrong source rejected", wrong_source_rejected))

    wrong_coupled = CenterCoupling12.from_theta(0.9).apply(source)
    try:
        verify_center_provenance(
            frame,
            source=source,
            coupled=wrong_coupled,
            summary=summary,
        )
    except ValueError as exc:
        wrong_coupled_rejected = "coupled center-state hash mismatch" in str(exc)
    else:
        wrong_coupled_rejected = False
    checks.append(check("wrong coupled state rejected", wrong_coupled_rejected))

    wrong_summary = CenterSummary3WithResidual.decompose(wrong_coupled)
    try:
        verify_center_provenance(
            frame,
            source=source,
            coupled=coupled,
            summary=wrong_summary,
        )
    except ValueError as exc:
        wrong_summary_rejected = "center summary hash mismatch" in str(exc)
    else:
        wrong_summary_rejected = False
    checks.append(check("wrong 3+9 summary rejected", wrong_summary_rejected))

    original_apply = CenterCoupling12.apply
    original_decompose = CenterSummary3WithResidual.decompose

    def forbidden_apply(self, input_state):
        raise AssertionError("fast center verify must not recompute coupling.apply")

    def forbidden_decompose(input_state):
        raise AssertionError("fast center verify must not recompute decomposition")

    CenterCoupling12.apply = forbidden_apply
    CenterSummary3WithResidual.decompose = staticmethod(forbidden_decompose)
    try:
        fast_no_recompute = verify_center_provenance(
            frame,
            source=source,
            coupled=coupled,
            summary=summary,
        )
    finally:
        CenterCoupling12.apply = original_apply
        CenterSummary3WithResidual.decompose = staticmethod(original_decompose)

    checks.append(check("fast center verify avoids semantic recomputation", fast_no_recompute))

    checks.append(
        check(
            "deep center verify recomputes derivation when restored",
            deep_verify_center_provenance(
                frame,
                source=source,
                coupled=coupled,
                summary=summary,
            ),
        )
    )

    mismatched_matrix = CenterCoupling12.from_theta(0.7).matrix
    bad_matrix_frame = reseal(frame, matrix=mismatched_matrix)
    try:
        verify_center_provenance(
            bad_matrix_frame,
            source=source,
            coupled=coupled,
            summary=summary,
        )
    except ValueError:
        matrix_theta_mismatch_rejected = True
    else:
        matrix_theta_mismatch_rejected = False
    checks.append(check("theta/matrix mismatch rejected", matrix_theta_mismatch_rejected))

    unrelated_coupling = CenterCoupling12.from_theta(-0.31)
    unrelated_coupled = unrelated_coupling.apply(source)
    unrelated_summary = CenterSummary3WithResidual.decompose(unrelated_coupled)
    independent_chain = seal_center_provenance(
        source=source,
        coupling=unrelated_coupling,
        coupled=unrelated_coupled,
        summary=unrelated_summary,
    )
    checks.append(
        check(
            "unkeyed seal permits a new producer-independent valid chain",
            verify_center_provenance(
                independent_chain,
                source=source,
                coupled=unrelated_coupled,
                summary=unrelated_summary,
            ),
        )
    )

    checks.append(
        check(
            "schedule version remains frozen",
            frame.schedule_version == CENTER_SCHEDULE_VERSION,
        )
    )

    repeated = [
        seal_center_provenance(
            source=source,
            coupling=coupling,
            coupled=coupled,
            summary=summary,
            source_z3_echo_provenance_h256="f" * 64,
        ).provenance_h256
        for _ in range(10)
    ]
    checks.append(check("center provenance deterministic over repeated seals", len(set(repeated)) == 1))

    checks.append(
        check(
            "center provenance JSON stable",
            json.dumps(frame.to_dict(), sort_keys=True)
            == json.dumps(frame.to_dict(), sort_keys=True),
        )
    )

    report = {
        "schema": "ANTMUX-Z3-CENTER-PROVENANCE-ADVERSARIAL-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "checks": checks,
        "security_limit": (
            "unkeyed SHA-256 validates integrity/coherence against a sealed chain "
            "but does not authenticate the producer of a new chain"
        ),
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["checks_total"] == result["checks_passed"] else 1)
