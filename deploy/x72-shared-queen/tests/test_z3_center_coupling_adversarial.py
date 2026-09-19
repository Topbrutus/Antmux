from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from z3_echo import (
    CENTER_COUPLING_SCHEDULE_V0_1,
    CenterCoupling12,
    CenterSummary3WithResidual,
    Channels12,
    FourTriadZState,
    FiniteZTriad,
    Triad3,
    apply_matrix12,
    build_center_coupling_matrix,
    orthogonality_error12,
)


def check(name: str, condition: bool, detail: str = "") -> dict[str, object]:
    if not condition:
        raise AssertionError(f"{name}: {detail}")
    return {"name": name, "ok": True}


def same_state(
    left: FourTriadZState,
    right: FourTriadZState,
    tolerance: float = 1e-9,
) -> bool:
    if left.coefficient_count != right.coefficient_count:
        return False
    return all(
        abs(lv - rv) <= tolerance
        for group in range(4)
        for ls, rs in zip(left.triads[group].samples, right.triads[group].samples)
        for lv, rv in zip(ls.as_tuple(), rs.as_tuple())
    )


def make_state(length: int = 8) -> FourTriadZState:
    groups = []
    for group in range(4):
        groups.append(
            FiniteZTriad.from_samples(
                Triad3(
                    complex(group * 3 + index, (group - index) / 7),
                    complex((-1) ** group * (index + 1), group / 9),
                    complex(index / 5, (-1) ** index * group / 11),
                )
                for index in range(length)
            )
        )
    return FourTriadZState(tuple(groups))


def run() -> dict[str, object]:
    checks: list[dict[str, object]] = []

    invalid_theta = 0
    for value in (True, float("nan"), float("inf"), float("-inf")):
        try:
            CenterCoupling12.from_theta(value)
        except (TypeError, ValueError):
            invalid_theta += 1
    checks.append(check("invalid center angles rejected", invalid_theta == 4))

    source = make_state()
    source_snapshot = source.triads

    angles = (
        1e-9,
        -0.37,
        math.pi / 2,
        math.pi,
        3.7,
        9 * math.pi,
    )
    roundtrip_ok = True
    orthogonal_ok = True
    norm_ok = True
    for theta in angles:
        coupling = CenterCoupling12.from_theta(theta)
        orthogonal_ok = orthogonal_ok and orthogonality_error12(coupling.matrix) <= 1e-9
        coupled = coupling.apply(source)
        restored = coupling.reconstruct(coupled)
        roundtrip_ok = roundtrip_ok and same_state(source, restored, tolerance=2e-8)
        for index in range(source.coefficient_count):
            norm_ok = norm_ok and abs(
                source.channels_at(index).norm_squared()
                - coupled.channels_at(index).norm_squared()
            ) <= 1e-7

    checks.append(check("round trip survives adversarial center angles", roundtrip_ok))
    checks.append(check("orthogonality survives adversarial center angles", orthogonal_ok))
    checks.append(check("norm survives adversarial center angles", norm_ok))

    closure_ok = True
    for turns in (-5, -2, -1, 0, 1, 3, 8):
        coupled = CenterCoupling12.from_theta(turns * 2 * math.pi).apply(source)
        closure_ok = closure_ok and same_state(source, coupled, tolerance=2e-8)
    checks.append(check("integer 360-degree center turns close", closure_ok))

    default_matrix = build_center_coupling_matrix(0.41)
    reverse_matrix = build_center_coupling_matrix(
        0.41,
        schedule=tuple(reversed(CENTER_COUPLING_SCHEDULE_V0_1)),
    )
    order_delta = max(
        abs(default_matrix[row][col] - reverse_matrix[row][col])
        for row in range(12)
        for col in range(12)
    )
    checks.append(
        check(
            "overlapping center rotation schedule is order-sensitive",
            order_delta > 1e-6,
        )
    )

    basis = Channels12.from_values((1.0,) + (0.0,) * 11)
    mixed = apply_matrix12(default_matrix, basis)
    active_outputs = sum(abs(value) > 1e-12 for value in mixed.values)
    checks.append(
        check(
            "center coupling propagates one input beyond a mirror pair",
            active_outputs >= 3,
            detail=f"active_outputs={active_outputs}",
        )
    )

    summary = CenterSummary3WithResidual.decompose(
        CenterCoupling12.from_theta(0.61).apply(source)
    )
    reconstructed = summary.reconstruct()
    checks.append(
        check(
            "center summary plus residuals round trip under complex load",
            same_state(
                reconstructed,
                CenterCoupling12.from_theta(0.61).apply(source),
                tolerance=2e-8,
            ),
        )
    )

    state_a = FourTriadZState(
        tuple(
            FiniteZTriad.from_samples(
                (Triad3(value, value * 2, -value),)
            )
            for value in (1.0, 2.0, 3.0, 4.0)
        )
    )
    state_b = FourTriadZState(
        tuple(
            FiniteZTriad.from_samples(
                (Triad3(value, value * 2, -value),)
            )
            for value in (0.0, 2.0, 4.0, 4.0)
        )
    )
    summary_a = CenterSummary3WithResidual.decompose(state_a)
    summary_b = CenterSummary3WithResidual.decompose(state_b)
    same_center = all(
        abs(a - b) <= 1e-12
        for a, b in zip(
            summary_a.center.samples[0].as_tuple(),
            summary_b.center.samples[0].as_tuple(),
        )
    )
    checks.append(
        check(
            "different 12-channel states can share the same 3-value center",
            same_center and not same_state(state_a, state_b),
        )
    )

    checks.append(
        check(
            "residual side information distinguishes same-center states",
            summary_a.residuals != summary_b.residuals,
        )
    )

    try:
        FourTriadZState(
            (
                FiniteZTriad.from_samples((Triad3(1, 2, 3),)),
                FiniteZTriad.from_samples((Triad3(1, 2, 3), Triad3(4, 5, 6))),
                FiniteZTriad.from_samples((Triad3(1, 2, 3),)),
                FiniteZTriad.from_samples((Triad3(1, 2, 3),)),
            )
        )
    except ValueError:
        unequal_lengths_rejected = True
    else:
        unequal_lengths_rejected = False
    checks.append(check("unequal triad coefficient lengths rejected", unequal_lengths_rejected))

    try:
        Channels12.from_values((1.0,) * 11)
    except ValueError:
        short_channels_rejected = True
    else:
        short_channels_rejected = False
    checks.append(check("non-12 channel vector rejected", short_channels_rejected))

    try:
        CenterCoupling12(theta=0.2, matrix=build_center_coupling_matrix(0.3))
    except ValueError as exc:
        mismatched_matrix_rejected = "does not match" in str(exc)
    else:
        mismatched_matrix_rejected = False
    checks.append(check("theta/matrix mismatch rejected", mismatched_matrix_rejected))

    checks.append(check("center operations leave source immutable", source.triads == source_snapshot))

    deterministic = (
        build_center_coupling_matrix(0.444)
        == build_center_coupling_matrix(0.444)
    )
    checks.append(check("center matrix construction deterministic", deterministic))

    report = {
        "schema": "ANTMUX-Z3-CENTER-COUPLING-ADVERSARIAL-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "checks": checks,
        "falsification_note": (
            "a 3-value center summary alone is many-to-one; 3+9 is algebraically "
            "complete but binary64 reconstruction is not bit-exact at all scales"
        ),
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["checks_total"] == result["checks_passed"] else 1)
