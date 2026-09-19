from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from typing import Any

from .echo_domain import Z3EchoTransfer
from .math_core import (
    CHANNELS_PER_TRIAD,
    TOTAL_NODE_COUNT,
    TRIAD_COUNT,
    FiniteZTriad,
    Matrix3,
    euler_zyz,
)

SERIES_HASH_SCHEMA = "ANTMUX-Z3-FINITE-Z-SERIES-H256-v0.1"
TRANSFER_HASH_SCHEMA = "ANTMUX-Z3-ECHO-TRANSFER-H256-v0.1"
PROVENANCE_SCHEMA = "ANTMUX-Z3-ECHO-PROVENANCE-v0.1"
REPRESENTATION = "FINITE_Z_COEFFICIENTS"
_H256_RE = re.compile(r"^[0-9a-f]{64}$")


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _validate_h256(value: str | None, field: str, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str) or not _H256_RE.fullmatch(value):
        raise ValueError(f"{field} must be 64 lowercase hexadecimal characters")
    return value


def _float_hex(value: float | int) -> str:
    out = float(value)
    if not math.isfinite(out):
        raise ValueError("canonical float must be finite")
    if out == 0.0:
        out = 0.0
    return out.hex()


def _complex_payload(value: complex) -> dict[str, str]:
    return {
        "real_hex": _float_hex(value.real),
        "imag_hex": _float_hex(value.imag),
    }


def _matrix_payload(matrix: Matrix3) -> list[list[str]]:
    return [[_float_hex(value) for value in row] for row in matrix]


def _series_payload(series: FiniteZTriad) -> dict[str, Any]:
    if type(series) is not FiniteZTriad:
        raise TypeError("series must be exactly FiniteZTriad")
    return {
        "schema": SERIES_HASH_SCHEMA,
        "representation": REPRESENTATION,
        "samples": [
            [_complex_payload(value) for value in sample.as_tuple()]
            for sample in series.samples
        ],
    }


def series_h256(series: FiniteZTriad) -> str:
    return hashlib.sha256(_canonical_json(_series_payload(series))).hexdigest()


def _angles_payload(
    euler_zyz_angles: tuple[float, float, float] | None,
) -> list[str] | None:
    if euler_zyz_angles is None:
        return None
    if (
        type(euler_zyz_angles) is not tuple
        or len(euler_zyz_angles) != 3
        or any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in euler_zyz_angles)
    ):
        raise TypeError("euler_zyz_angles must be exactly a 3-tuple of real numbers")
    return [_float_hex(value) for value in euler_zyz_angles]


def _matrix_max_delta(left: Matrix3, right: Matrix3) -> float:
    return max(
        abs(left[row][col] - right[row][col])
        for row in range(3)
        for col in range(3)
    )


def _transfer_payload(
    transfer: Z3EchoTransfer,
    *,
    euler_zyz_angles: tuple[float, float, float] | None,
) -> dict[str, Any]:
    if type(transfer) is not Z3EchoTransfer:
        raise TypeError("transfer must be exactly Z3EchoTransfer")
    angle_payload = _angles_payload(euler_zyz_angles)
    if euler_zyz_angles is not None:
        expected = euler_zyz(*euler_zyz_angles)
        if _matrix_max_delta(expected, transfer.rotation) > 1e-12:
            raise ValueError("Euler Z-Y-Z angles do not reproduce transfer rotation")
        rotation_source = "EULER_ZYZ"
    else:
        rotation_source = "EXPLICIT_MATRIX3"

    return {
        "schema": TRANSFER_HASH_SCHEMA,
        "gain": _complex_payload(transfer.gain),
        "delay": transfer.delay,
        "rotation": _matrix_payload(transfer.rotation),
        "rotation_source": rotation_source,
        "euler_order": "Z-Y-Z" if angle_payload is not None else None,
        "euler_angles_hex": angle_payload,
    }


def transfer_h256(
    transfer: Z3EchoTransfer,
    *,
    euler_zyz_angles: tuple[float, float, float] | None = None,
) -> str:
    payload = _transfer_payload(transfer, euler_zyz_angles=euler_zyz_angles)
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


@dataclass(frozen=True)
class Z3ProvenanceFrame:
    schema: str
    representation: str
    triad_count: int
    channels_per_triad: int
    total_node_count: int
    source_series_h256: str
    echoed_series_h256: str
    transfer_h256: str
    gain: complex
    delay: int
    rotation: Matrix3
    rotation_source: str
    euler_order: str | None
    euler_zyz_angles: tuple[float, float, float] | None
    source_x72_candidate_h256: str | None
    source_x72_echo_h256: str | None
    provenance_h256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "representation": self.representation,
            "topology": {
                "triad_count": self.triad_count,
                "channels_per_triad": self.channels_per_triad,
                "total_node_count": self.total_node_count,
            },
            "source_series_h256": self.source_series_h256,
            "echoed_series_h256": self.echoed_series_h256,
            "transfer_h256": self.transfer_h256,
            "gain": {
                "real": self.gain.real,
                "imag": self.gain.imag,
            },
            "delay": self.delay,
            "rotation": [list(row) for row in self.rotation],
            "rotation_source": self.rotation_source,
            "euler_order": self.euler_order,
            "euler_zyz_angles": (
                list(self.euler_zyz_angles)
                if self.euler_zyz_angles is not None
                else None
            ),
            "source_x72_candidate_h256": self.source_x72_candidate_h256,
            "source_x72_echo_h256": self.source_x72_echo_h256,
            "provenance_h256": self.provenance_h256,
        }


def _frame_body(frame: Z3ProvenanceFrame) -> dict[str, Any]:
    return {
        "schema": frame.schema,
        "representation": frame.representation,
        "topology": {
            "triad_count": frame.triad_count,
            "channels_per_triad": frame.channels_per_triad,
            "total_node_count": frame.total_node_count,
        },
        "source_series_h256": frame.source_series_h256,
        "echoed_series_h256": frame.echoed_series_h256,
        "transfer_h256": frame.transfer_h256,
        "gain": _complex_payload(frame.gain),
        "delay": frame.delay,
        "rotation": _matrix_payload(frame.rotation),
        "rotation_source": frame.rotation_source,
        "euler_order": frame.euler_order,
        "euler_angles_hex": _angles_payload(frame.euler_zyz_angles),
        "source_x72_candidate_h256": frame.source_x72_candidate_h256,
        "source_x72_echo_h256": frame.source_x72_echo_h256,
    }


def _frame_h256(frame: Z3ProvenanceFrame) -> str:
    return hashlib.sha256(_canonical_json(_frame_body(frame))).hexdigest()


def seal_provenance(
    *,
    source: FiniteZTriad,
    transfer: Z3EchoTransfer,
    echoed: FiniteZTriad,
    euler_zyz_angles: tuple[float, float, float] | None = None,
    source_x72_candidate_h256: str | None = None,
    source_x72_echo_h256: str | None = None,
) -> Z3ProvenanceFrame:
    candidate_h256 = _validate_h256(
        source_x72_candidate_h256,
        "source_x72_candidate_h256",
        optional=True,
    )
    echo_h256 = _validate_h256(
        source_x72_echo_h256,
        "source_x72_echo_h256",
        optional=True,
    )
    transfer_payload = _transfer_payload(
        transfer,
        euler_zyz_angles=euler_zyz_angles,
    )
    frame = Z3ProvenanceFrame(
        schema=PROVENANCE_SCHEMA,
        representation=REPRESENTATION,
        triad_count=TRIAD_COUNT,
        channels_per_triad=CHANNELS_PER_TRIAD,
        total_node_count=TOTAL_NODE_COUNT,
        source_series_h256=series_h256(source),
        echoed_series_h256=series_h256(echoed),
        transfer_h256=hashlib.sha256(_canonical_json(transfer_payload)).hexdigest(),
        gain=transfer.gain,
        delay=transfer.delay,
        rotation=transfer.rotation,
        rotation_source=transfer_payload["rotation_source"],
        euler_order=transfer_payload["euler_order"],
        euler_zyz_angles=euler_zyz_angles,
        source_x72_candidate_h256=candidate_h256,
        source_x72_echo_h256=echo_h256,
        provenance_h256="0" * 64,
    )
    return Z3ProvenanceFrame(
        **{
            **frame.__dict__,
            "provenance_h256": _frame_h256(frame),
        }
    )


def verify_provenance(
    frame: Z3ProvenanceFrame,
    *,
    source: FiniteZTriad,
    echoed: FiniteZTriad,
) -> bool:
    if type(frame) is not Z3ProvenanceFrame:
        raise TypeError("frame must be exactly Z3ProvenanceFrame")
    if frame.schema != PROVENANCE_SCHEMA or frame.representation != REPRESENTATION:
        raise ValueError("unexpected Z3 provenance schema or representation")
    if (
        frame.triad_count != TRIAD_COUNT
        or frame.channels_per_triad != CHANNELS_PER_TRIAD
        or frame.total_node_count != TOTAL_NODE_COUNT
    ):
        raise ValueError("Z3 provenance topology mismatch")

    _validate_h256(frame.provenance_h256, "provenance_h256")
    _validate_h256(frame.source_series_h256, "source_series_h256")
    _validate_h256(frame.echoed_series_h256, "echoed_series_h256")
    _validate_h256(frame.transfer_h256, "transfer_h256")
    if _frame_h256(frame) != frame.provenance_h256:
        raise ValueError("provenance_h256 does not match canonical frame content")
    if series_h256(source) != frame.source_series_h256:
        raise ValueError("source series hash mismatch")
    if series_h256(echoed) != frame.echoed_series_h256:
        raise ValueError("echoed series hash mismatch")

    transfer = Z3EchoTransfer(
        gain=frame.gain,
        delay=frame.delay,
        rotation=frame.rotation,
    )
    transfer_payload = _transfer_payload(
        transfer,
        euler_zyz_angles=frame.euler_zyz_angles,
    )
    if frame.rotation_source != transfer_payload["rotation_source"]:
        raise ValueError("rotation_source mismatch")
    if frame.euler_order != transfer_payload["euler_order"]:
        raise ValueError("euler_order mismatch")
    observed_transfer_h256 = hashlib.sha256(
        _canonical_json(transfer_payload)
    ).hexdigest()
    if observed_transfer_h256 != frame.transfer_h256:
        raise ValueError("transfer hash mismatch")

    _validate_h256(
        frame.source_x72_candidate_h256,
        "source_x72_candidate_h256",
        optional=True,
    )
    _validate_h256(
        frame.source_x72_echo_h256,
        "source_x72_echo_h256",
        optional=True,
    )
    return True


def deep_verify_provenance(
    frame: Z3ProvenanceFrame,
    *,
    source: FiniteZTriad,
    echoed: FiniteZTriad,
) -> bool:
    verify_provenance(frame, source=source, echoed=echoed)
    transfer = Z3EchoTransfer(
        gain=frame.gain,
        delay=frame.delay,
        rotation=frame.rotation,
    )
    expected = transfer.apply(source)
    if series_h256(expected) != frame.echoed_series_h256:
        raise ValueError("echoed series does not match transfer applied to source")
    return True
