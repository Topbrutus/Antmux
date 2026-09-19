from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from z3_echo import (
    CENTER_CHANNEL_COUNT,
    CHANNEL_COUNT,
    RESIDUAL_CHANNEL_COUNT,
    CenterCoupling12,
    CenterSummary3WithResidual,
    FourTriadZState,
    FiniteZTriad,
    Triad3,
    orthogonality_error12,
)


def check(name: str, condition: bool, detail: str = "") -> dict[str, object]:
    if not condition:
        raise AssertionError(f"{name}: {detail}")
    return {"name": name, "ok": True}


def same_state(
    left: FourTriadZState,
    right: FourTriadZState,
    tolerance: float = 1e-10,
) -> bool:
    if left.coefficient_count != right.coefficient_count:
        return False
    for group in range(4):
        for ls, rs in zip(left.triads[group].samples, right.triads[group].samples):
            for lv, rv in zip(ls.as_tuple(), rs.as_tuple()):
                if abs(lv - rv) > tolerance:
                    return False
    return True


def make_state() -> FourTriadZState:
    triads = []
    for group in range(4):
        samples = []
        for index in range(5):
            samples.append(
                Triad3(
                    group * 10 + index + 0.25,
                    complex(group + index / 10, (group - index) / 20),
                    (-1) ** group * (index + 1.5),
                )
            )
        triads.append(FiniteZTriad.from_samples(samples))
    return FourTriadZState(tuple(triads))


def run() -> dict[str, object]:
    checks: list[dict[str, object]] = []

    checks.append(
        check(
            "12 channels split as 3 center + 9 residual",
            CHANNEL_COUNT == 12
            and CENTER_CHANNEL_COUNT == 3
            and RESIDUAL_CHANNEL_COUNT == 9
            and CENTER_CHANNEL_COUNT + RESIDUAL_CHANNEL_COUNT == CHANNEL_COUNT,
        )
    )

    source = make_state()
    snapshot = source.triads
    coupling = CenterCoupling12.from_theta(0.37)

    checks.append(
        check(
            "center coupling matrix is orthogonal",
            orthogonality_error12(coupling.matrix) <= 1e-10,
        )
    )

    coupled = coupling.apply(source)
    restored = coupling.reconstruct(coupled)
    checks.append(
        check(
            "12-to-12 coupling round trip reconstructs source",
            same_state(restored, source),
        )
    )

    checks.append(
        check(
            "center coupling preserves coefficient count",
            coupled.coefficient_count == source.coefficient_count,
        )
    )

    norm_preserved = True
    for index in range(source.coefficient_count):
        before = source.channels_at(index).norm_squared()
        after = coupled.channels_at(index).norm_squared()
        norm_preserved = norm_preserved and abs(before - after) <= 1e-8
    checks.append(check("12-channel coupling preserves norm", norm_preserved))

    checks.append(
        check(
            "center coupling does not mutate source",
            source.triads == snapshot,
        )
    )

    full_turn = CenterCoupling12.from_theta(2 * math.pi)
    closed = full_turn.apply(source)
    checks.append(
        check(
            "360-degree center schedule closes to identity",
            same_state(closed, source, tolerance=1e-9),
        )
    )

    nontrivial = any(
        abs(a - b) > 1e-9
        for a, b in zip(
            source.channels_at(0).values,
            coupled.channels_at(0).values,
        )
    )
    checks.append(check("nonzero center angle mixes channels", nontrivial))

    summary = CenterSummary3WithResidual.decompose(coupled)
    reconstructed_from_summary = summary.reconstruct()
    checks.append(
        check(
            "3-center plus 9-residual representation is reconstructible",
            same_state(reconstructed_from_summary, coupled),
        )
    )

    center_is_mean = True
    for index in range(coupled.coefficient_count):
        center_values = summary.center.samples[index].as_tuple()
        for channel in range(3):
            expected = sum(
                coupled.triads[group].samples[index].as_tuple()[channel]
                for group in range(4)
            ) / 4
            center_is_mean = center_is_mean and abs(center_values[channel] - expected) <= 1e-12
    checks.append(check("center 3-vector is four-triad channel mean", center_is_mean))

    residual_closure = True
    for index in range(coupled.coefficient_count):
        center_values = summary.center.samples[index].as_tuple()
        for channel in range(3):
            explicit_residuals = [
                summary.residuals[group].samples[index].as_tuple()[channel]
                for group in range(3)
            ]
            derived_fourth = -sum(explicit_residuals)
            observed_fourth = (
                coupled.triads[3].samples[index].as_tuple()[channel]
                - center_values[channel]
            )
            residual_closure = residual_closure and abs(
                observed_fourth - derived_fourth
            ) <= 1e-12
    checks.append(check("fourth residual is exactly derivable from first three", residual_closure))

    different_state = FourTriadZState(
        (
            summary.center,
            summary.center,
            summary.center,
            summary.center,
        )
    )
    checks.append(
        check(
            "center-only 12-to-3 summary is not a reconstruction",
            not same_state(different_state, coupled),
        )
    )

    zero_angle = CenterCoupling12.from_theta(0.0)
    checks.append(
        check(
            "zero center angle is identity",
            same_state(zero_angle.apply(source), source),
        )
    )

    checks.append(
        check(
            "complex coefficients survive coupling and reconstruction",
            all(
                math.isfinite(value.real) and math.isfinite(value.imag)
                for index in range(restored.coefficient_count)
                for value in restored.channels_at(index).values
            ),
        )
    )

    report = {
        "schema": "ANTMUX-Z3-CENTER-COUPLING-TEST-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "checks": checks,
        "architecture": (
            "one 13-node system; reversible 12-to-12 center coupling; "
            "3-value center summary is lossless only with 9 residual side values"
        ),
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["checks_total"] == result["checks_passed"] else 1)
