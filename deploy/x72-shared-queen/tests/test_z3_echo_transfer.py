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
    Z3EchoTransfer,
    euler_zyz,
)


def close(a: complex | float, b: complex | float, tol: float = 1e-10) -> bool:
    return abs(a - b) <= tol


def same_series(left: FiniteZTriad, right: FiniteZTriad, tol: float = 1e-10) -> bool:
    if len(left.samples) != len(right.samples):
        return False
    for a, b in zip(left.samples, right.samples):
        for av, bv in zip(a.as_tuple(), b.as_tuple()):
            if not close(av, bv, tol):
                return False
    return True


def check(name: str, condition: bool, detail: str = "") -> dict[str, object]:
    if not condition:
        raise AssertionError(f"{name}: {detail}")
    return {"name": name, "ok": True}


def run() -> dict[str, object]:
    checks: list[dict[str, object]] = []

    source = FiniteZTriad.from_samples(
        (
            Triad3(1.0, 2.0, 3.0),
            Triad3(-2.0, 0.5, 4.0),
            Triad3(0.25, -3.5, 1.25),
        )
    )
    source_before = source.samples

    transfer = Z3EchoTransfer(
        gain=complex(0.75, -0.25),
        delay=2,
        rotation=euler_zyz(0.37, -0.92, 1.11),
    )
    echoed = transfer.apply(source)
    restored = transfer.reconstruct(echoed)

    checks.append(
        check(
            "nonzero gain round trip reconstructs source",
            same_series(restored, source),
        )
    )

    checks.append(
        check(
            "delay appears as exact zero coefficient prefix",
            len(echoed.samples) == len(source.samples) + 2
            and all(
                value == 0
                for sample in echoed.samples[:2]
                for value in sample.as_tuple()
            ),
        )
    )

    checks.append(
        check(
            "source transformed representation is not mutated",
            source.samples == source_before,
        )
    )

    checks.append(
        check(
            "transfer remains entirely coefficient/Z representation",
            type(echoed) is FiniteZTriad and type(restored) is FiniteZTriad,
        )
    )

    zero_gain = Z3EchoTransfer(
        gain=0.0,
        delay=1,
        rotation=euler_zyz(0.0, 0.0, 0.0),
    )
    zero_echo = zero_gain.apply(source)
    checks.append(
        check(
            "zero numerical gain produces zero transformed coefficients",
            all(
                value == 0
                for sample in zero_echo.samples
                for value in sample.as_tuple()
            ),
        )
    )
    try:
        zero_gain.reconstruct(zero_echo)
    except ValueError as exc:
        zero_gain_noninvertible = "non-invertible" in str(exc)
    else:
        zero_gain_noninvertible = False
    checks.append(check("zero numerical gain is explicitly non-invertible", zero_gain_noninvertible))

    try:
        Z3EchoTransfer(
            gain=1.0,
            delay=True,
            rotation=euler_zyz(0.0, 0.0, 0.0),
        )
    except ValueError:
        bool_delay_rejected = True
    else:
        bool_delay_rejected = False
    checks.append(check("boolean delay rejected", bool_delay_rejected))

    try:
        Z3EchoTransfer(
            gain=1.0,
            delay=-1,
            rotation=euler_zyz(0.0, 0.0, 0.0),
        )
    except ValueError:
        negative_delay_rejected = True
    else:
        negative_delay_rejected = False
    checks.append(check("negative delay rejected", negative_delay_rejected))

    bad_rotation = (
        (1.0, 0.0, 0.0),
        (0.0, 2.0, 0.0),
        (0.0, 0.0, 1.0),
    )
    try:
        Z3EchoTransfer(gain=1.0, delay=0, rotation=bad_rotation)
    except ValueError:
        bad_rotation_rejected = True
    else:
        bad_rotation_rejected = False
    checks.append(check("non-rotation matrix rejected", bad_rotation_rejected))

    tampered = FiniteZTriad.from_samples(
        (
            Triad3(1.0, 0.0, 0.0),
            *echoed.samples[1:],
        )
    )
    try:
        transfer.reconstruct(tampered)
    except ValueError as exc:
        tampered_prefix_rejected = "delay prefix" in str(exc)
    else:
        tampered_prefix_rejected = False
    checks.append(check("tampered delay prefix rejected", tampered_prefix_rejected))

    real_gain_transfer = Z3EchoTransfer(
        gain=2.0,
        delay=0,
        rotation=euler_zyz(math.pi, 0.0, 2 * math.pi),
    )
    real_echo = real_gain_transfer.apply(source)
    real_restored = real_gain_transfer.reconstruct(real_echo)
    checks.append(
        check(
            "phase closure and nonzero gain remain reconstructible",
            same_series(real_restored, source),
        )
    )

    report = {
        "schema": "ANTMUX-Z3-ECHO-TRANSFER-TEST-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "checks": checks,
        "semantic_note": "signal gain is separate from X72 ternary echo_state",
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["checks_total"] == result["checks_passed"] else 1)
