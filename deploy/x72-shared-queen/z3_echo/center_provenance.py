from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from typing import Any

from .center_coupling import (
    CENTER_COUPLING_SCHEDULE_V0_1,
    CenterCoupling12,
    CenterSummary3WithResidual,
    FourTriadZState,
    Matrix12,
)
from .provenance import series_h256

CENTER_STATE_HASH_SCHEMA = "ANTMUX-Z3-CENTER-STATE-H256-v0.1"
CENTER_COUPLING_HASH_SCHEMA = "ANTMUX-Z3-CENTER-COUPLING-H256-v0.1"
CENTER_SUMMARY_HASH_SCHEMA = "ANTMUX-Z3-CENTER-SUMMARY-H256-v0.1"
CENTER_PROVENANCE_SCHEMA = "ANTMUX-Z3-CENTER-PROVENANCE-v0.1"
CENTER_SCHEDULE_VERSION = "Z3-MIRROR-RING-SCHEDULE-v0.1"
_H256_RE = re.compile(r"^[0-9a-f]{64}$")


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _float_hex(value: float | int) -> str:
    out = float(value)
    if not math.isfinite(out):
        raise ValueError("canonical float must be finite")
    if out == 0.0:
        out = 0.0
    return out.hex()


def _validate_h256(value: str | None, field: str, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str) or not _H256_RE.fullmatch(value):
        raise ValueError(f"{field} must be 64 lowercase hexadecimal characters")
    return value


def _matrix_payload(matrix: Matrix12) -> list[list[str]]:
    if type(matrix) is not tuple or len(matrix) != 12:
        raise ValueError("matrix must be exactly 12x12")
    payload: list[list[str]] = []
    for row in matrix:
        if type(row) is not tuple or len(row) != 12:
            raise ValueError("matrix must be exactly 12x12")
        payload.append([_float_hex(value) for value in row])
    return payload


def center_state_h256(state: FourTriadZState) -> str:
    if type(state) is not FourTriadZState:
        raise TypeError("state must be exactly FourTriadZState")
    payload = {
        "schema": CENTER_STATE_HASH_SCHEMA,
        "triad_series_h256": [
            series_h256(triad)
            for triad in state.triads
        ],
    }
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


def center_summary_h256(summary: CenterSummary3WithResidual) -> str:
    if type(summary) is not CenterSummary3WithResidual:
        raise TypeError("summary must be exactly CenterSummary3WithResidual")
    payload = {
        "schema": CENTER_SUMMARY_HASH_SCHEMA,
        "center_series_h256": series_h256(summary.center),
        "residual_series_h256": [
            series_h256(residual)
            for residual in summary.residuals
        ],
    }
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


def center_coupling_h256(coupling: CenterCoupling12) -> str:
    if type(coupling) is not CenterCoupling12:
        raise TypeError("coupling must be exactly CenterCoupling12")
    payload = {
        "schema": CENTER_COUPLING_HASH_SCHEMA,
        "schedule_version": CENTER_SCHEDULE_VERSION,
        "schedule": [list(pair) for pair in CENTER_COUPLING_SCHEDULE_V0_1],
        "theta_hex": _float_hex(coupling.theta),
        "matrix": _matrix_payload(coupling.matrix),
    }
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


@dataclass(frozen=True)
class Z3CenterProvenanceFrame:
    schema: str
    schedule_version: str
    source_state_h256: str
    coupling_h256: str
    coupled_state_h256: str
    summary_h256: str
    center_series_h256: str
    residual_series_h256: tuple[str, str, str]
    theta: float
    matrix: Matrix12
    source_z3_echo_provenance_h256: str | None
    provenance_h256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "schedule_version": self.schedule_version,
            "source_state_h256": self.source_state_h256,
            "coupling_h256": self.coupling_h256,
            "coupled_state_h256": self.coupled_state_h256,
            "summary_h256": self.summary_h256,
            "center_series_h256": self.center_series_h256,
            "residual_series_h256": list(self.residual_series_h256),
            "theta": self.theta,
            "matrix": [list(row) for row in self.matrix],
            "source_z3_echo_provenance_h256": self.source_z3_echo_provenance_h256,
            "provenance_h256": self.provenance_h256,
        }


def _frame_body(frame: Z3CenterProvenanceFrame) -> dict[str, Any]:
    return {
        "schema": frame.schema,
        "schedule_version": frame.schedule_version,
        "source_state_h256": frame.source_state_h256,
        "coupling_h256": frame.coupling_h256,
        "coupled_state_h256": frame.coupled_state_h256,
        "summary_h256": frame.summary_h256,
        "center_series_h256": frame.center_series_h256,
        "residual_series_h256": list(frame.residual_series_h256),
        "theta_hex": _float_hex(frame.theta),
        "matrix": _matrix_payload(frame.matrix),
        "source_z3_echo_provenance_h256": frame.source_z3_echo_provenance_h256,
    }


def _frame_h256(frame: Z3CenterProvenanceFrame) -> str:
    return hashlib.sha256(_canonical_json(_frame_body(frame))).hexdigest()


def seal_center_provenance(
    *,
    source: FourTriadZState,
    coupling: CenterCoupling12,
    coupled: FourTriadZState,
    summary: CenterSummary3WithResidual,
    source_z3_echo_provenance_h256: str | None = None,
) -> Z3CenterProvenanceFrame:
    upstream = _validate_h256(
        source_z3_echo_provenance_h256,
        "source_z3_echo_provenance_h256",
        optional=True,
    )
    frame = Z3CenterProvenanceFrame(
        schema=CENTER_PROVENANCE_SCHEMA,
        schedule_version=CENTER_SCHEDULE_VERSION,
        source_state_h256=center_state_h256(source),
        coupling_h256=center_coupling_h256(coupling),
        coupled_state_h256=center_state_h256(coupled),
        summary_h256=center_summary_h256(summary),
        center_series_h256=series_h256(summary.center),
        residual_series_h256=tuple(
            series_h256(residual)
            for residual in summary.residuals
        ),
        theta=coupling.theta,
        matrix=coupling.matrix,
        source_z3_echo_provenance_h256=upstream,
        provenance_h256="0" * 64,
    )
    return Z3CenterProvenanceFrame(
        **{
            **frame.__dict__,
            "provenance_h256": _frame_h256(frame),
        }
    )


def verify_center_provenance(
    frame: Z3CenterProvenanceFrame,
    *,
    source: FourTriadZState,
    coupled: FourTriadZState,
    summary: CenterSummary3WithResidual,
) -> bool:
    if type(frame) is not Z3CenterProvenanceFrame:
        raise TypeError("frame must be exactly Z3CenterProvenanceFrame")
    if frame.schema != CENTER_PROVENANCE_SCHEMA:
        raise ValueError("unexpected center provenance schema")
    if frame.schedule_version != CENTER_SCHEDULE_VERSION:
        raise ValueError("unexpected center coupling schedule version")

    for field, value in (
        ("source_state_h256", frame.source_state_h256),
        ("coupling_h256", frame.coupling_h256),
        ("coupled_state_h256", frame.coupled_state_h256),
        ("summary_h256", frame.summary_h256),
        ("center_series_h256", frame.center_series_h256),
        ("provenance_h256", frame.provenance_h256),
    ):
        _validate_h256(value, field)
    for index, value in enumerate(frame.residual_series_h256):
        _validate_h256(value, f"residual_series_h256[{index}]")
    _validate_h256(
        frame.source_z3_echo_provenance_h256,
        "source_z3_echo_provenance_h256",
        optional=True,
    )

    if _frame_h256(frame) != frame.provenance_h256:
        raise ValueError("center provenance_h256 does not match canonical frame content")
    if center_state_h256(source) != frame.source_state_h256:
        raise ValueError("source center-state hash mismatch")
    if center_state_h256(coupled) != frame.coupled_state_h256:
        raise ValueError("coupled center-state hash mismatch")
    if center_summary_h256(summary) != frame.summary_h256:
        raise ValueError("center summary hash mismatch")
    if series_h256(summary.center) != frame.center_series_h256:
        raise ValueError("center series hash mismatch")

    observed_residuals = tuple(
        series_h256(residual)
        for residual in summary.residuals
    )
    if observed_residuals != frame.residual_series_h256:
        raise ValueError("center residual series hash mismatch")

    coupling = CenterCoupling12(theta=frame.theta, matrix=frame.matrix)
    if center_coupling_h256(coupling) != frame.coupling_h256:
        raise ValueError("center coupling hash mismatch")
    return True


def _states_close(
    left: FourTriadZState,
    right: FourTriadZState,
    *,
    tolerance: float = 1e-10,
) -> bool:
    if type(left) is not FourTriadZState or type(right) is not FourTriadZState:
        return False
    if left.coefficient_count != right.coefficient_count:
        return False
    return all(
        abs(left_value - right_value) <= tolerance
        for group in range(4)
        for left_sample, right_sample in zip(
            left.triads[group].samples,
            right.triads[group].samples,
        )
        for left_value, right_value in zip(
            left_sample.as_tuple(),
            right_sample.as_tuple(),
        )
    )


def deep_verify_center_provenance(
    frame: Z3CenterProvenanceFrame,
    *,
    source: FourTriadZState,
    coupled: FourTriadZState,
    summary: CenterSummary3WithResidual,
) -> bool:
    verify_center_provenance(
        frame,
        source=source,
        coupled=coupled,
        summary=summary,
    )
    coupling = CenterCoupling12(theta=frame.theta, matrix=frame.matrix)
    expected_coupled = coupling.apply(source)
    if center_state_h256(expected_coupled) != frame.coupled_state_h256:
        raise ValueError("coupled state does not match center coupling applied to source")

    expected_summary = CenterSummary3WithResidual.decompose(expected_coupled)
    if center_summary_h256(expected_summary) != frame.summary_h256:
        raise ValueError("center summary does not match coupled-state decomposition")

    reconstructed = summary.reconstruct()
    if not _states_close(reconstructed, coupled, tolerance=1e-10):
        raise ValueError(
            "3+9 center representation does not reconstruct coupled state "
            "within floating-point tolerance"
        )
    return True
