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
    FiniteZTriad,
    FourTriadZState,
    Triad3,
    Z3EchoTransfer,
    build_center_coupling_matrix,
    center_state_h256,
    euler_zyz,
    matmul12,
)


def check(name: str, condition: bool, detail: str = "") -> dict[str, object]:
    if not condition:
        raise AssertionError(f"{name}: {detail}")
    return {"name": name, "ok": True}


def state_from_x(values: tuple[float, float, float, float]) -> FourTriadZState:
    return FourTriadZState(
        tuple(
            FiniteZTriad.from_samples((Triad3(value, 0.0, 0.0),))
            for value in values
        )
    )


def matrix_delta_from_identity(matrix) -> float:
    return max(
        abs(matrix[row][col] - (1.0 if row == col else 0.0))
        for row in range(12)
        for col in range(12)
    )


def run() -> dict[str, object]:
    checks: list[dict[str, object]] = []

    # Codex finding: large finite inputs previously overflowed the naive sum.
    huge = state_from_x((1e308, 1e308, 1e308, 1e308))
    huge_summary = CenterSummary3WithResidual.decompose(huge)
    checks.append(
        check(
            "overflow-aware center mean accepts finite 1e308 inputs",
            huge_summary.center.samples[0].x == complex(1e308, 0.0),
        )
    )

    subnormal = state_from_x((5e-324, 5e-324, 5e-324, 5e-324))
    subnormal_summary = CenterSummary3WithResidual.decompose(subnormal)
    checks.append(
        check(
            "scaled center mean preserves equal smallest subnormals",
            subnormal_summary.center.samples[0].x == complex(5e-324, 0.0),
        )
    )

    cancellation_state = state_from_x((-1e308, -1e308, 1e308, 1e308))
    cancellation_summary = CenterSummary3WithResidual.decompose(cancellation_state)
    cancellation_restored = cancellation_summary.reconstruct()
    checks.append(
        check(
            "scaled center reconstruction survives large cancellation",
            all(
                cancellation_restored.triads[index].samples[0].x
                == cancellation_state.triads[index].samples[0].x
                for index in range(4)
            ),
        )
    )

    # Codex finding: approximate matrix tolerance admitted a noncanonical shear.
    identity = build_center_coupling_matrix(0.0)
    rows = [list(row) for row in identity]
    rows[0][1] = 2 ** -41
    shear = tuple(tuple(row) for row in rows)
    try:
        CenterCoupling12(theta=0.0, matrix=shear)
    except ValueError as exc:
        shear_rejected = "does not match" in str(exc)
    else:
        shear_rejected = False
    checks.append(check("noncanonical theta-zero shear rejected", shear_rejected))

    # Codex finding: complex-orthogonal is not a proper real spatial rotation.
    complex_rotation = (
        (1.25, -0.75j, 0.0),
        (0.75j, 1.25, 0.0),
        (0.0, 0.0, 1.0),
    )
    try:
        Z3EchoTransfer(gain=1.0, delay=0, rotation=complex_rotation)
    except ValueError:
        complex_rotation_rejected = True
    else:
        complex_rotation_rejected = False
    checks.append(
        check("complex norm-changing rotation matrix rejected", complex_rotation_rejected)
    )

    mutable_rotation = [
        list(row)
        for row in euler_zyz(0.31, -0.72, 1.08)
    ]
    copied_rotation_transfer = Z3EchoTransfer(
        gain=1.0,
        delay=0,
        rotation=mutable_rotation,
    )
    frozen_rotation_before = copied_rotation_transfer.rotation
    mutable_rotation[0][0] = 999.0
    checks.append(
        check(
            "transfer copies caller-owned mutable rotation storage",
            copied_rotation_transfer.rotation == frozen_rotation_before
            and type(copied_rotation_transfer.rotation) is tuple
            and all(type(row) is tuple for row in copied_rotation_transfer.rotation),
        )
    )

    # Codex finding: nonzero binary64 gain can still destroy data by underflow.
    tiny_transfer = Z3EchoTransfer(
        gain=1e-200,
        delay=0,
        rotation=euler_zyz(0.0, 0.0, 0.0),
    )
    tiny_source = FiniteZTriad.from_samples((Triad3(1e-200, 0.0, 0.0),))
    try:
        tiny_transfer.apply(tiny_source)
    except ArithmeticError as exc:
        underflow_rejected = "not numerically reversible" in str(exc)
    else:
        underflow_rejected = False
    checks.append(check("destructive gain underflow rejected", underflow_rejected))

    partial_underflow_transfer = Z3EchoTransfer(
        gain=5e-324,
        delay=0,
        rotation=euler_zyz(0.0, 0.0, 0.0),
    )
    partial_underflow_source = FiniteZTriad.from_samples(
        (Triad3(1.0 + 0.25j, 0.0, 0.0),)
    )
    try:
        partial_underflow_transfer.apply(partial_underflow_source)
    except ArithmeticError as exc:
        partial_underflow_rejected = "not numerically reversible" in str(exc)
    else:
        partial_underflow_rejected = False
    checks.append(
        check(
            "partial complex gain underflow rejected",
            partial_underflow_rejected,
        )
    )

    large_division_transfer = Z3EchoTransfer(
        gain=1.0 + 1.0j,
        delay=0,
        rotation=euler_zyz(0.0, 0.0, 0.0),
    )
    large_echoed = FiniteZTriad.from_samples(
        (Triad3(1e308 + 1e308j, 0.0, 0.0),)
    )
    large_restored = large_division_transfer.reconstruct(large_echoed)
    checks.append(
        check(
            "scaled complex division avoids representable-result overflow",
            large_restored.samples[0].x == complex(1e308, 0.0),
            detail=str(large_restored.samples[0].x),
        )
    )

    large_multiply_transfer = Z3EchoTransfer(
        gain=0.5 - 0.5j,
        delay=0,
        rotation=euler_zyz(0.0, 0.0, 0.0),
    )
    large_multiply_source = FiniteZTriad.from_samples(
        (Triad3(1e308 + 1e308j, 0.0, 0.0),)
    )
    large_multiplied = large_multiply_transfer.apply(large_multiply_source)
    checks.append(
        check(
            "scaled complex multiplication avoids cancellation overflow",
            large_multiplied.samples[0].x == complex(1e308, 0.0),
            detail=str(large_multiplied.samples[0].x),
        )
    )

    # Codex finding: a frozen dataclass previously retained the caller's list.
    caller_samples = [Triad3(1.0, 2.0, 3.0)]
    frozen_series = FiniteZTriad(caller_samples)
    caller_samples.clear()
    checks.append(
        check(
            "FiniteZTriad copies caller-owned mutable sample storage",
            type(frozen_series.samples) is tuple
            and len(frozen_series.samples) == 1,
        )
    )

    # The 3+9 formulas are algebraically invertible but not bitwise lossless
    # for all binary64 inputs. Keep this boundary executable and explicit.
    state_a = state_from_x((1e16, 0.0, 0.0, 0.0))
    state_b = state_from_x((1e16, 0.0, 0.0, 1.0))
    summary_a = CenterSummary3WithResidual.decompose(state_a)
    summary_b = CenterSummary3WithResidual.decompose(state_b)
    checks.append(
        check(
            "binary64 3+9 collision remains an explicit numerical boundary",
            summary_a == summary_b
            and center_state_h256(state_a) != center_state_h256(state_b),
        )
    )

    # The current routing schedule is reversible but has two invariant graph
    # components. This is a documented architectural choice pending v0.2.
    adjacency = {index: set() for index in range(12)}
    for left, right in CENTER_COUPLING_SCHEDULE_V0_1:
        adjacency[left].add(right)
        adjacency[right].add(left)
    seen: set[int] = set()
    components: list[tuple[int, ...]] = []
    for start in range(12):
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        component: list[int] = []
        while stack:
            node = stack.pop()
            component.append(node)
            for neighbor in adjacency[node]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        components.append(tuple(sorted(component)))
    components = sorted(components)
    checks.append(
        check(
            "v0.1 routing invariant subspaces are explicit",
            components
            == [
                (0, 2, 3, 5, 6, 8, 9, 11),
                (1, 4, 7, 10),
            ],
            detail=str(components),
        )
    )

    # Direct absolute-angle closure and repeated incremental application are
    # different semantics for the noncommuting schedule.
    direct_full_turn = build_center_coupling_matrix(2 * math.pi)
    quarter = build_center_coupling_matrix(math.pi / 2)
    repeated = tuple(
        tuple(1.0 if row == col else 0.0 for col in range(12))
        for row in range(12)
    )
    for _ in range(4):
        repeated = matmul12(quarter, repeated)
    checks.append(
        check(
            "direct full-turn closure is distinct from four quarter-turn applications",
            matrix_delta_from_identity(direct_full_turn) <= 1e-12
            and matrix_delta_from_identity(repeated) > 0.5,
        )
    )

    report = {
        "schema": "ANTMUX-Z3-CODEX-AUDIT-REGRESSION-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "checks": checks,
        "known_numeric_boundary": (
            "3+9 is algebraically invertible but not a bit-preserving binary64 encoding"
        ),
        "known_architecture_boundary": (
            "v0.1 routing has two invariant channel components"
        ),
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["checks_total"] == result["checks_passed"] else 1)
