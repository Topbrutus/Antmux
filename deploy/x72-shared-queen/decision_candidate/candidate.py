from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from observation_history import X72ObservationHistory
from trend_analyzer import X72TrendAnalyzer, X72TrendFrame


CANDIDATE_SCHEMA = "ANTMUX-X72-DECISION-CANDIDATE-v0.1"
GENERATED_FROM = (
    "X72ObservationHistory-v0.1",
    "X72TrendAnalyzer-v0.1",
)
ALLOWED_CANDIDATE_TYPES = frozenset(
    {
        "NO_CHANGE",
        "OBSERVE_MORE",
        "VERIFY_INTEGRITY",
        "INVESTIGATE_FAULT",
        "INVESTIGATE_REPAIR",
        "INVESTIGATE_DISCONNECT",
        "INVESTIGATE_SCHEMA_MISMATCH",
        "INVESTIGATE_RUNTIME_CHANGE",
    }
)


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


@dataclass(frozen=True)
class X72CandidateFrame:
    schema: str
    entity_id: str | None
    source_history_h256: str
    source_trend_h256: str
    window_start_tick: int | None
    window_end_tick: int | None
    candidate_type: str
    condition: str
    evidence: Mapping[str, Any]
    source_records_count: int
    integrity_state: str
    queen_mode: str | None
    generated_from: tuple[str, ...]
    candidate_h256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "entity_id": self.entity_id,
            "source_history_h256": self.source_history_h256,
            "source_trend_h256": self.source_trend_h256,
            "window_start_tick": self.window_start_tick,
            "window_end_tick": self.window_end_tick,
            "candidate_type": self.candidate_type,
            "condition": self.condition,
            "evidence": copy.deepcopy(dict(self.evidence)),
            "source_records_count": self.source_records_count,
            "integrity_state": self.integrity_state,
            "queen_mode": self.queen_mode,
            "generated_from": list(self.generated_from),
            "candidate_h256": self.candidate_h256,
        }
class X72DecisionCandidate:
    """Read-only deterministic candidate classification. Candidate != action."""

    READ_ONLY = True
    NO_MUTATION_TRANSPORT = True
    NO_ACTION_EXECUTION = True
    DETERMINISTIC = True

    def generate(
        self,
        history: X72ObservationHistory,
        trend: X72TrendFrame,
    ) -> X72CandidateFrame:
        if not isinstance(history, X72ObservationHistory):
            raise TypeError("history must be X72ObservationHistory")
        if not isinstance(trend, X72TrendFrame):
            raise TypeError("trend must be X72TrendFrame")

        expected_trend = X72TrendAnalyzer().analyze(history)
        expected_history_h256 = history.deterministic_report()["report_h256"]

        if trend.source_history_h256 != expected_history_h256:
            raise ValueError("trend source_history_h256 does not match History")
        if trend.entity_id != history.entity_id:
            raise ValueError("trend entity_id does not match History")
        if trend.to_dict() != expected_trend.to_dict():
            raise ValueError("trend frame does not match deterministic History analysis")

        records = tuple(history.records)
        latest = records[-1] if records else None
        latest_mode = None
        latest_integrity = None
        if latest is not None:
            latest_integrity = latest.integrity_match
            for record in reversed(records):
                if record.queen_mode is not None:
                    latest_mode = record.queen_mode
                    break

        integrity_state = self._integrity_state(
            trend=trend,
            latest_integrity=latest_integrity,
        )
        candidate_type, condition, specific_evidence = self._classify(
            trend=trend,
            integrity_state=integrity_state,
            latest_mode=latest_mode,
        )

        if candidate_type not in ALLOWED_CANDIDATE_TYPES:
            raise AssertionError("candidate type outside descriptive allow-list")

        evidence = {
            "source_history_h256": expected_history_h256,
            "source_trend_h256": trend.trend_h256,
            "records_count": trend.records_count,
            "fresh_count": trend.fresh_count,
            "stale_count": trend.stale_count,
            "unknown_count": trend.unknown_count,
            "reconnect_count": trend.reconnect_count,
            "schema_mismatch_count": trend.schema_mismatch_count,
            "h256_closed": trend.h256_closed,
            "integrity_state": integrity_state,
            "queen_mode": latest_mode,
            **specific_evidence,
        }

        body = {
            "schema": CANDIDATE_SCHEMA,
            "entity_id": trend.entity_id,
            "source_history_h256": expected_history_h256,
            "source_trend_h256": trend.trend_h256,
            "window_start_tick": trend.window_start_tick,
            "window_end_tick": trend.window_end_tick,
            "candidate_type": candidate_type,
            "condition": condition,
            "evidence": evidence,
            "source_records_count": trend.records_count,
            "integrity_state": integrity_state,
            "queen_mode": latest_mode,
            "generated_from": GENERATED_FROM,
        }
        candidate_h256 = hashlib.sha256(_canonical_json(body)).hexdigest()

        return X72CandidateFrame(
            schema=body["schema"],
            entity_id=body["entity_id"],
            source_history_h256=body["source_history_h256"],
            source_trend_h256=body["source_trend_h256"],
            window_start_tick=body["window_start_tick"],
            window_end_tick=body["window_end_tick"],
            candidate_type=body["candidate_type"],
            condition=body["condition"],
            evidence=MappingProxyType(copy.deepcopy(evidence)),
            source_records_count=body["source_records_count"],
            integrity_state=body["integrity_state"],
            queen_mode=body["queen_mode"],
            generated_from=GENERATED_FROM,
            candidate_h256=candidate_h256,
        )
    @staticmethod
    def _integrity_state(
        *,
        trend: X72TrendFrame,
        latest_integrity: bool | None,
    ) -> str:
        if trend.h256_closed is False or latest_integrity is False:
            return "OPEN"
        if trend.h256_closed is True and latest_integrity is not False:
            return "CLOSED"
        return "UNKNOWN"

    @staticmethod
    def _runtime_changed(trend: X72TrendFrame) -> bool:
        deltas = (
            trend.r_exec_delta,
            trend.f_rt_delta,
            trend.active_synapses_delta,
        )
        return any(value is not None and value != 0 for value in deltas)

    def _classify(
        self,
        *,
        trend: X72TrendFrame,
        integrity_state: str,
        latest_mode: str | None,
    ) -> tuple[str, str, dict[str, Any]]:
        if trend.records_count == 0:
            return (
                "OBSERVE_MORE",
                "EMPTY_HISTORY",
                {"reason": "no validated History records available"},
            )

        if trend.records_count < 2:
            return (
                "OBSERVE_MORE",
                "INSUFFICIENT_WINDOW",
                {"reason": "at least two records are required for comparison"},
            )

        if trend.schema_mismatch_count > 0:
            return (
                "INVESTIGATE_SCHEMA_MISMATCH",
                "SCHEMA_MISMATCH_OBSERVED",
                {"schema_mismatch_count": trend.schema_mismatch_count},
            )

        if trend.reconnect_count > 0 or trend.stale_count > 0:
            return (
                "INVESTIGATE_DISCONNECT",
                "CONNECTIVITY_ANOMALY_OBSERVED",
                {
                    "reconnect_count": trend.reconnect_count,
                    "stale_count": trend.stale_count,
                },
            )

        repair_active = latest_mode in {"AUTO_REPAIR", "REPAIR"}
        if trend.repair_intervals and repair_active:
            return (
                "INVESTIGATE_REPAIR",
                "REPAIR_INTERVAL_ACTIVE",
                {
                    "repair_intervals": len(trend.repair_intervals),
                    "h256_closed": trend.h256_closed,
                },
            )

        if trend.fault_intervals and integrity_state == "OPEN":
            return (
                "INVESTIGATE_FAULT",
                "FAULT_INTERVAL_OPEN",
                {
                    "fault_intervals": len(trend.fault_intervals),
                    "h256_closed": trend.h256_closed,
                },
            )

        if integrity_state == "OPEN":
            return (
                "VERIFY_INTEGRITY",
                "H256_NOT_CLOSED",
                {
                    "fault_intervals": len(trend.fault_intervals),
                    "h256_closed": trend.h256_closed,
                },
            )

        if trend.repair_intervals:
            return (
                "INVESTIGATE_REPAIR",
                "REPAIR_INTERVAL_OBSERVED",
                {
                    "repair_intervals": len(trend.repair_intervals),
                    "h256_reclosure_count": trend.h256_reclosure_count,
                },
            )

        if trend.fault_intervals and integrity_state == "CLOSED":
            return (
                "VERIFY_INTEGRITY",
                "FAULT_RECLOSED",
                {
                    "fault_intervals": len(trend.fault_intervals),
                    "h256_reclosure_count": trend.h256_reclosure_count,
                },
            )

        if self._runtime_changed(trend):
            return (
                "INVESTIGATE_RUNTIME_CHANGE",
                "RUNTIME_VARIATION_OBSERVED",
                {
                    "r_exec_delta": trend.r_exec_delta,
                    "f_rt_delta": trend.f_rt_delta,
                    "active_synapses_delta": trend.active_synapses_delta,
                },
            )

        if integrity_state == "CLOSED":
            return (
                "NO_CHANGE",
                "STABLE_CLOSED_WINDOW",
                {
                    "fault_intervals": len(trend.fault_intervals),
                    "repair_intervals": len(trend.repair_intervals),
                },
            )

        return (
            "OBSERVE_MORE",
            "INSUFFICIENT_INTEGRITY_EVIDENCE",
            {"h256_closed": trend.h256_closed},
        )
