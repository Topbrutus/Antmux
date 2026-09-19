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
    apply_matrix3,
    euler_zyz,
)


def check(name: str, condition: bool, detail: str = "") -> dict[str, object]:
    if not condition:
        raise AssertionError(f"{name}: {detail}")
    return {"name": name, "ok": True}


def same_series(left: FiniteZTriad, right: FiniteZTriad, tol: float = 1e-10) -> bool:
    if len(left.samples) != len(right.samples):
        return False
    return all(
        abs(a - b) <= tol
        for ls, rs in zip(left.samples, right.samples)
        for a, b in zip(ls.as_tuple(), rs.as_tuple())
    )


def run() -> dict[str, object]:
    checks: list[dict[str, object]] = []

    source = FiniteZTriad.from_samples(
        tuple(
            Triad3(
                index + 0.25,
                complex((-1) ** index * (index + 1), index / 10),
                -0.5 * index,
            )
            for index in range(6)
        )
    )
    rotation = euler_zyz(0.73, -1.11, 2.03)

    rejected = 0
    for bad_gain in (True, float("nan"), float("inf"), float("-inf"), complex(0, float("nan"))):
        try:
            Z3EchoTransfer(gain=bad_gain, delay=0, rotation=rotation)
        except (TypeError, ValueError):
            rejected += 1
    checks.append(check("invalid gains rejected", rejected == 5))

    reflection = (
        (-1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
    )
    try:
        Z3EchoTransfer(gain=1.0, delay=0, rotation=reflection)
    except ValueError:
        reflection_rejected = True
    else:
        reflection_rejected = False
    checks.append(check("det=-1 reflection rejected as rotation", reflection_rejected))

    complex_transfer = Z3EchoTransfer(
        gain=complex(-0.4, 1.3),
        delay=7,
        rotation=rotation,
    )
    echoed = complex_transfer.apply(source)
    restored = complex_transfer.reconstruct(echoed)
    checks.append(
        check(
            "complex gain plus long delay round trip",
            same_series(source, restored),
        )
    )

    checks.append(
        check(
            "long delay length is exact",
            len(echoed.samples) == len(source.samples) + 7
            and all(
                value == 0
                for sample in echoed.samples[:7]
                for value in sample.as_tuple()
            ),
        )
    )

    z = complex(1.2, 0.4)
    observed = echoed.evaluate(z)
    source_at_z = source.evaluate(z)
    rotated = apply_matrix3(rotation, source_at_z)
    expected = Triad3(
        rotated.x * complex_transfer.gain * z ** (-complex_transfer.delay),
        rotated.y * complex_transfer.gain * z ** (-complex_transfer.delay),
        rotated.z * complex_transfer.gain * z ** (-complex_transfer.delay),
    )
    checks.append(
        check(
            "coefficient implementation matches G*z^-d*R*X(z)",
            all(
                abs(a - b) <= 1e-9
                for a, b in zip(observed.as_tuple(), expected.as_tuple())
            ),
            detail=f"observed={observed} expected={expected}",
        )
    )

    source_snapshot = source.samples
    _ = complex_transfer.apply(source)
    checks.append(check("adversarial apply does not mutate source", source.samples == source_snapshot))

    zero_transfer = Z3EchoTransfer(
        gain=0.0,
        delay=0,
        rotation=rotation,
    )
    checks.append(check("zero gain reports non-reversible", zero_transfer.reversible is False))
    try:
        zero_transfer.reconstruct(zero_transfer.apply(source))
    except ValueError:
        zero_reconstruct_rejected = True
    else:
        zero_reconstruct_rejected = False
    checks.append(check("zero gain reconstruction rejected", zero_reconstruct_rejected))

    tiny_transfer = Z3EchoTransfer(
        gain=1e-12 + 2e-12j,
        delay=1,
        rotation=euler_zyz(-2.2, 0.4, 0.17),
    )
    tiny_restored = tiny_transfer.reconstruct(tiny_transfer.apply(source))
    checks.append(
        check(
            "very small nonzero gain remains algebraically reconstructible",
            same_series(source, tiny_restored, tol=1e-8),
        )
    )

    wrong_prefix = list(echoed.samples)
    wrong_prefix[3] = Triad3(0.0, 1e-6, 0.0)
    try:
        complex_transfer.reconstruct(FiniteZTriad(tuple(wrong_prefix)))
    except ValueError as exc:
        prefix_tamper_rejected = "delay prefix" in str(exc)
    else:
        prefix_tamper_rejected = False
    checks.append(check("delay-prefix tamper rejected", prefix_tamper_rejected))

    no_delay = Z3EchoTransfer(
        gain=-2.0,
        delay=0,
        rotation=euler_zyz(2 * math.pi, 0.0, -2 * math.pi),
    )
    checks.append(
        check(
            "zero-delay full-turn path round trips",
            same_series(source, no_delay.reconstruct(no_delay.apply(source))),
        )
    )

    report = {
        "schema": "ANTMUX-Z3-ECHO-TRANSFER-ADVERSARIAL-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "checks": checks,
        "known_limit": "math transfer alone does not authenticate non-prefix coefficient tampering",
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["checks_total"] == result["checks_passed"] else 1)
