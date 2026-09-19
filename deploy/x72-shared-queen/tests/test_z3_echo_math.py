from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from z3_echo import (
    CHANNELS_PER_TRIAD,
    PERIPHERAL_NODE_COUNT,
    TOTAL_NODE_COUNT,
    TRIAD_COUNT,
    FiniteZTriad,
    Triad3,
    apply_matrix3,
    beta_y_to_zero_z,
    determinant3,
    euler_zyz,
    is_rotation_matrix,
    matmul3,
    orthogonality_error,
    rotation_y,
    rotation_z,
)


def close(a: complex | float, b: complex | float, tol: float = 1e-12) -> bool:
    return abs(a - b) <= tol


def check(name: str, condition: bool, detail: str = "") -> dict[str, object]:
    if not condition:
        raise AssertionError(f"{name}: {detail}")
    return {"name": name, "ok": True}


def matrix_max_delta(left, right) -> float:
    return max(
        abs(left[r][c] - right[r][c])
        for r in range(3)
        for c in range(3)
    )


def run() -> dict[str, object]:
    checks: list[dict[str, object]] = []

    checks.append(
        check(
            "13-node topology constants",
            TRIAD_COUNT == 4
            and CHANNELS_PER_TRIAD == 3
            and PERIPHERAL_NODE_COUNT == 12
            and TOTAL_NODE_COUNT == 13,
        )
    )

    samples = (
        Triad3(1.0, 2.0, 3.0),
        Triad3(2.0, 4.0, 6.0),
        Triad3(-1.0, 1.0, 0.5),
    )
    transformed = FiniteZTriad.from_samples(samples)
    at_two = transformed.evaluate(2.0)
    expected = Triad3(
        1.0 + 2.0 / 2.0 - 1.0 / 4.0,
        2.0 + 4.0 / 2.0 + 1.0 / 4.0,
        3.0 + 6.0 / 2.0 + 0.5 / 4.0,
    )
    checks.append(
        check(
            "finite Z evaluation",
            all(
                close(observed, wanted)
                for observed, wanted in zip(at_two.as_tuple(), expected.as_tuple())
            ),
            detail=f"observed={at_two} expected={expected}",
        )
    )

    checks.append(
        check(
            "finite Z coefficient inverse is exact",
            transformed.inverse_coefficients() == samples,
        )
    )

    try:
        transformed.evaluate(0)
    except ValueError:
        zero_rejected = True
    else:
        zero_rejected = False
    checks.append(check("z=0 rejected", zero_rejected))

    alpha, beta, gamma = 0.31, -0.77, 1.22
    rotation = euler_zyz(alpha, beta, gamma)
    checks.append(
        check(
            "Euler Z-Y-Z is a proper rotation",
            is_rotation_matrix(rotation)
            and orthogonality_error(rotation) <= 1e-12
            and abs(determinant3(rotation) - 1.0) <= 1e-12,
        )
    )

    identity_rotation = euler_zyz(0.0, 0.0, 0.0)
    vector = Triad3(3.0, -2.0, 5.0)
    same = apply_matrix3(identity_rotation, vector)
    checks.append(check("zero Euler angles are identity", same == vector))

    norm_before = vector.norm_squared()
    norm_after = apply_matrix3(rotation, vector).norm_squared()
    checks.append(
        check(
            "rotation preserves norm",
            close(norm_before, norm_after, 1e-10),
            detail=f"before={norm_before} after={norm_after}",
        )
    )

    rz_then_ry = matmul3(rotation_z(0.4), rotation_y(0.7))
    ry_then_rz = matmul3(rotation_y(0.7), rotation_z(0.4))
    checks.append(
        check(
            "rotation order is non-commutative",
            matrix_max_delta(rz_then_ry, ry_then_rz) > 1e-6,
        )
    )

    source = Triad3(3.0, 7.0, 4.0)
    beta_zero = beta_y_to_zero_z(source)
    flattened = apply_matrix3(rotation_y(beta_zero), source)
    checks.append(
        check(
            "Y rotation can drive selected z component to zero",
            abs(flattened.z) <= 1e-12,
            detail=f"beta={beta_zero} z'={flattened.z}",
        )
    )

    full_turn = rotation_z(2.0 * math.pi)
    checks.append(
        check(
            "360-degree closure returns orientation",
            matrix_max_delta(full_turn, euler_zyz(0.0, 0.0, 0.0)) <= 1e-12,
        )
    )

    complex_signal = FiniteZTriad.from_samples(
        (
            Triad3(1 + 2j, 0.5j, -2.0),
            Triad3(0.25, -1j, 3 + 0.5j),
        )
    )
    complex_eval = complex_signal.evaluate(complex(0.8, 0.3))
    checks.append(
        check(
            "complex Z-domain values remain finite",
            all(
                math.isfinite(v.real) and math.isfinite(v.imag)
                for v in complex_eval.as_tuple()
            ),
        )
    )

    report = {
        "schema": "ANTMUX-Z3-ECHO-MATH-CORE-TEST-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "checks": checks,
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["checks_total"] == result["checks_passed"] else 1)
