from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from z3_echo import (
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


def check(name: str, condition: bool, detail: str = "") -> dict[str, object]:
    if not condition:
        raise AssertionError(f"{name}: {detail}")
    return {"name": name, "ok": True}


def max_matrix_delta(left, right) -> float:
    return max(
        abs(left[r][c] - right[r][c])
        for r in range(3)
        for c in range(3)
    )


def run() -> dict[str, object]:
    checks: list[dict[str, object]] = []

    bad_scalars = [True, float("nan"), float("inf"), float("-inf"), complex(float("nan"), 0)]
    rejected = 0
    for value in bad_scalars:
        try:
            Triad3(value, 0.0, 0.0)
        except (TypeError, ValueError):
            rejected += 1
    checks.append(check("non-finite and bool scalars rejected", rejected == len(bad_scalars)))

    try:
        FiniteZTriad.from_samples(())
    except ValueError:
        empty_rejected = True
    else:
        empty_rejected = False
    checks.append(check("empty Z sequence rejected", empty_rejected))

    try:
        FiniteZTriad.from_samples((Triad3(1, 2, 3),)).evaluate(0j)
    except ValueError:
        zero_rejected = True
    else:
        zero_rejected = False
    checks.append(check("Z evaluation at zero rejected", zero_rejected))

    try:
        beta_y_to_zero_z(Triad3(1 + 1j, 2, 3))
    except ValueError:
        complex_flatten_rejected = True
    else:
        complex_flatten_rejected = False
    checks.append(check("real-only flatten helper rejects complex triad", complex_flatten_rejected))

    angle_cases = (
        (0.0, 0.0, 0.0),
        (0.1, 0.2, 0.3),
        (-1.2, 2.1, -0.7),
        (math.pi, math.pi / 2, -math.pi / 3),
        (2 * math.pi, -2 * math.pi, 4 * math.pi),
    )
    rotation_ok = True
    worst_orth = 0.0
    worst_det = 0.0
    for angles in angle_cases:
        matrix = euler_zyz(*angles)
        worst_orth = max(worst_orth, orthogonality_error(matrix))
        worst_det = max(worst_det, abs(determinant3(matrix) - 1.0))
        rotation_ok = rotation_ok and is_rotation_matrix(matrix, tolerance=1e-11)
    checks.append(
        check(
            "Euler rotation stays orthogonal across adversarial angles",
            rotation_ok and worst_orth <= 1e-11 and worst_det <= 1e-11,
            detail=f"orth={worst_orth} det={worst_det}",
        )
    )

    vectors = (
        Triad3(1, 0, 0),
        Triad3(0, 1, 0),
        Triad3(0, 0, 1),
        Triad3(3, -4, 12),
        Triad3(-2.5, 7.75, 0.125),
    )
    norm_ok = True
    for angles in angle_cases[1:]:
        matrix = euler_zyz(*angles)
        for vector in vectors:
            before = vector.norm_squared()
            after = apply_matrix3(matrix, vector).norm_squared()
            norm_ok = norm_ok and abs(before - after) <= 1e-9
    checks.append(check("rotations preserve norm across vector set", norm_ok))

    order_a = matmul3(rotation_z(0.91), rotation_y(-0.37))
    order_b = matmul3(rotation_y(-0.37), rotation_z(0.91))
    checks.append(
        check(
            "Z/Y order cannot be silently swapped",
            max_matrix_delta(order_a, order_b) > 1e-4,
        )
    )

    closure_ok = True
    identity = euler_zyz(0.0, 0.0, 0.0)
    for turns in (-4, -2, -1, 0, 1, 2, 5):
        closure_ok = closure_ok and max_matrix_delta(
            rotation_z(turns * 2 * math.pi),
            identity,
        ) <= 1e-11
    checks.append(check("integer 360-degree turns close", closure_ok))

    flatten_cases = (
        Triad3(3, 7, 4),
        Triad3(-3, 1, 4),
        Triad3(0, 9, 8),
        Triad3(5, -2, 0),
        Triad3(0, 0, 0),
    )
    flatten_ok = True
    for source in flatten_cases:
        beta = beta_y_to_zero_z(source)
        flat = apply_matrix3(rotation_y(beta), source)
        flatten_ok = flatten_ok and abs(flat.z) <= 1e-11
        flatten_ok = flatten_ok and abs(flat.norm_squared() - source.norm_squared()) <= 1e-9
    checks.append(check("flattening zeroes z without changing norm", flatten_ok))

    samples = tuple(
        Triad3(index + 1, (-1) ** index * (index + 0.5), index / 3)
        for index in range(8)
    )
    transform = FiniteZTriad.from_samples(samples)
    z = complex(0.73, -0.21)
    observed = transform.evaluate(z)
    direct = [0j, 0j, 0j]
    for n, sample in enumerate(samples):
        for idx, value in enumerate(sample.as_tuple()):
            direct[idx] += value * z ** (-n)
    checks.append(
        check(
            "finite Z equals direct polynomial evaluation",
            all(abs(a - b) <= 1e-11 for a, b in zip(observed.as_tuple(), direct)),
        )
    )

    checks.append(
        check(
            "finite Z representation reconstructs coefficient sequence exactly",
            transform.inverse_coefficients() == samples,
        )
    )

    source = Triad3(0, 4, 9)
    beta = beta_y_to_zero_z(source)
    flattened = apply_matrix3(rotation_y(beta), source)
    checks.append(
        check(
            "x=0 flatten edge case remains finite",
            all(math.isfinite(v.real) and math.isfinite(v.imag) for v in flattened.as_tuple())
            and abs(flattened.z) <= 1e-11,
        )
    )

    report = {
        "schema": "ANTMUX-Z3-ECHO-FALSIFICATION-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "checks": checks,
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["checks_total"] == result["checks_passed"] else 1)
