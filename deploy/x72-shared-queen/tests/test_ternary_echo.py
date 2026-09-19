from __future__ import annotations

import inspect
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from decision_candidate import X72DecisionCandidate
from observation_adapter import ObservationEnvelope
from observation_history import X72ObservationHistory
from ternary_echo import (
    TERNARY_MATRIX,
    X72TernaryEchoMatrix,
    compute_intent_h256,
)
from ternary_echo.echo import _validate_trit
from trend_analyzer import X72TrendAnalyzer

ENTITY = "QUEEN-X72-0072"
SOURCE = "QUEEN_SERVER_V0_2"
REFERENCE = "54d4cee87f7e5feed1a0735a0b8431a2dc67b1bda0492c78a6c7274109c13180"


def payload(tick: int) -> dict[str, Any]:
    return {
        "source": SOURCE,
        "entity_id": ENTITY,
        "tick_count": tick,
        "queen_mode": "STABLE",
        "integrity_match": True,
        "protected_h256": REFERENCE,
        "reference_h256": REFERENCE,
        "r_exec": 100.0,
        "f_rt": 0.5,
        "active_synapses": 7,
        "event_count": tick,
    }


def envelope(tick: int, second: int) -> ObservationEnvelope:
    return ObservationEnvelope(
        observed_at_utc=f"2026-09-18T22:00:{second:02d}.000Z",
        entity_id=ENTITY,
        source_schema=SOURCE,
        source_endpoint="/ws",
        freshness_ms=0,
        status="FRESH",
        condition="STREAM_STATE",
        payload=payload(tick),
        error=None,
    )


def stable_sources():
    history = X72ObservationHistory(capacity=32)
    for item in (envelope(100, 0), envelope(101, 1)):
        result = history.append(item)
        if not result.accepted:
            raise AssertionError(result.to_dict())
    trend = X72TrendAnalyzer().analyze(history)
    candidate = X72DecisionCandidate().generate(history, trend)
    return history, trend, candidate


def intent_hash(candidate, correlation_id: str, origin_id: str = "ROCK_A") -> str:
    return compute_intent_h256(
        entity_id=ENTITY,
        correlation_id=correlation_id,
        origin_id=origin_id,
        target_id="LAKE",
        source_candidate_h256=candidate.candidate_h256,
    )


def register(
    matrix: X72TernaryEchoMatrix,
    history,
    trend,
    candidate,
    correlation_id: str,
    *,
    origin_id: str = "ROCK_A",
    second: int = 2,
):
    return matrix.register_intent(
        history=history,
        trend=trend,
        candidate=candidate,
        correlation_id=correlation_id,
        origin_id=origin_id,
        target_id="LAKE",
        intent_h256=intent_hash(candidate, correlation_id, origin_id),
        observed_at_utc=f"2026-09-18T22:00:{second:02d}.000Z",
    )


def check(name: str, condition: bool, detail: str = "") -> dict[str, Any]:
    if not condition:
        raise AssertionError(f"{name}: {detail}")
    return {"name": name, "ok": True}


def run() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    history, trend, candidate = stable_sources()

    checks.append(
        check(
            "matrix is exact 3x3",
            len(TERNARY_MATRIX) == 9
            and set(TERNARY_MATRIX)
            == {(e, p) for e in (-1, 0, 1) for p in (-1, 0, 1)},
        )
    )

    confirmation_for = {-1: False, 0: None, 1: True}
    origin_for = {-1: "ROCK_B", 0: None, 1: "ROCK_A"}
    observed_states: set[tuple[int, int]] = set()

    for index, (echo_state, provenance_state) in enumerate(TERNARY_MATRIX):
        matrix = X72TernaryEchoMatrix(capacity=4)
        correlation_id = f"MATRIX-{index}"
        register(matrix, history, trend, candidate, correlation_id)
        frame = matrix.observe_echo(
            correlation_id=correlation_id,
            observed_at_utc=f"2026-09-18T22:01:{index:02d}.000Z",
            explicit_confirmation=confirmation_for[echo_state],
            echo_origin_id=origin_for[provenance_state],
            evidence={"matrix_case": index},
        )
        observed_states.add((frame.echo_state, frame.provenance_state))

    checks.append(
        check("all nine states representable", observed_states == set(TERNARY_MATRIX))
    )
    plouf = X72TernaryEchoMatrix(capacity=8)
    signed_results: list[tuple[int, int]] = []
    for correlation_id, confirmation, echo_origin, second in (
        ("ROCK-A-1", True, "ROCK_A", 10),
        ("ROCK-A-2", True, None, 11),
        ("ROCK-A-3", True, "ROCK_B", 12),
    ):
        register(plouf, history, trend, candidate, correlation_id, second=second)
        frame = plouf.observe_echo(
            correlation_id=correlation_id,
            observed_at_utc=f"2026-09-18T22:02:{second:02d}.000Z",
            explicit_confirmation=confirmation,
            echo_origin_id=echo_origin,
            evidence={"test": "signed_plouf"},
        )
        signed_results.append((frame.echo_state, frame.provenance_state))

    register(plouf, history, trend, candidate, "ROCK-A-4", second=13)
    silence_frame = plouf.expire(
        correlation_id="ROCK-A-4",
        observed_at_utc="2026-09-18T22:02:20.000Z",
        evidence={"reason": "deadline_elapsed"},
    )
    signed_results.append((silence_frame.echo_state, silence_frame.provenance_state))

    checks.append(
        check(
            "signed plouf test",
            signed_results == [(1, 1), (1, 0), (1, -1), (0, 0)],
            detail=str(signed_results),
        )
    )
    checks.append(
        check(
            "silence is unknown",
            silence_frame.echo_state == 0
            and silence_frame.condition == "NO_ECHO_TIMEOUT",
        )
    )

    negative_matrix = X72TernaryEchoMatrix(capacity=4)
    register(negative_matrix, history, trend, candidate, "NEGATIVE", second=14)
    negative = negative_matrix.observe_echo(
        correlation_id="NEGATIVE",
        observed_at_utc="2026-09-18T22:03:00.000Z",
        explicit_confirmation=False,
        echo_origin_id="ROCK_A",
        evidence={"explicit_negative": True},
    )
    checks.append(
        check(
            "explicit negative only",
            negative.echo_state == -1
            and negative.condition == "ECHO_NEGATIVE_CONFIRMED",
        )
    )

    provenance_matrix = X72TernaryEchoMatrix(capacity=4)
    register(provenance_matrix, history, trend, candidate, "KNOWN-SILENCE", second=15)
    known_silence = provenance_matrix.expire(
        correlation_id="KNOWN-SILENCE",
        observed_at_utc="2026-09-18T22:03:10.000Z",
        provenance_origin_id="ROCK_A",
        evidence={"origin_observed": True},
    )
    checks.append(
        check(
            "echo and provenance independent",
            (known_silence.echo_state, known_silence.provenance_state) == (0, 1),
        )
    )

    correlation_only = X72TernaryEchoMatrix(capacity=4)
    register(correlation_only, history, trend, candidate, "CORR-ONLY", second=16)
    corr_frame = correlation_only.observe_echo(
        correlation_id="CORR-ONLY",
        observed_at_utc="2026-09-18T22:03:20.000Z",
        explicit_confirmation=True,
        echo_origin_id=None,
        evidence={"correlation_seen": True},
    )
    checks.append(
        check(
            "correlation is not proof",
            corr_frame.echo_state == 1 and corr_frame.provenance_state == 0,
        )
    )

    try:
        X72TernaryEchoMatrix().register_intent(
            history=history,
            trend=trend,
            candidate=candidate,
            correlation_id="",
            origin_id="ROCK_A",
            target_id="LAKE",
            intent_h256="0" * 64,
            observed_at_utc="2026-09-18T22:04:00.000Z",
        )
    except ValueError:
        absent_correlation_rejected = True
    else:
        absent_correlation_rejected = False
    checks.append(check("absent correlation rejected", absent_correlation_rejected))

    try:
        X72TernaryEchoMatrix().observe_echo(
            correlation_id="DIFFERENT",
            observed_at_utc="2026-09-18T22:04:01.000Z",
            explicit_confirmation=True,
            echo_origin_id="ROCK_A",
        )
    except KeyError:
        different_correlation_rejected = True
    else:
        different_correlation_rejected = False
    checks.append(
        check("different correlation rejected", different_correlation_rejected)
    )
    intent_matrix = X72TernaryEchoMatrix(capacity=4)
    correct_intent = intent_hash(candidate, "INTENT-CORRECT")
    accepted_intent = intent_matrix.register_intent(
        history=history,
        trend=trend,
        candidate=candidate,
        correlation_id="INTENT-CORRECT",
        origin_id="ROCK_A",
        target_id="LAKE",
        intent_h256=correct_intent,
        observed_at_utc="2026-09-18T22:04:02.000Z",
    )
    checks.append(
        check(
            "intent h256 correct",
            accepted_intent.intent_h256 == correct_intent
            and len(correct_intent) == 64,
        )
    )

    try:
        X72TernaryEchoMatrix().register_intent(
            history=history,
            trend=trend,
            candidate=candidate,
            correlation_id="INTENT-MISMATCH",
            origin_id="ROCK_A",
            target_id="LAKE",
            intent_h256="0" * 64,
            observed_at_utc="2026-09-18T22:04:03.000Z",
        )
    except ValueError as exc:
        intent_mismatch_rejected = "intent_h256" in str(exc)
    else:
        intent_mismatch_rejected = False

    try:
        X72TernaryEchoMatrix().register_intent(
            history=history,
            trend=trend,
            candidate=candidate,
            correlation_id="INTENT-MALFORMED",
            origin_id="ROCK_A",
            target_id="LAKE",
            intent_h256="xyz",
            observed_at_utc="2026-09-18T22:04:04.000Z",
        )
    except ValueError:
        malformed_h256_rejected = True
    else:
        malformed_h256_rejected = False
    checks.append(
        check(
            "intent mismatch and malformed h256 rejected",
            intent_mismatch_rejected and malformed_h256_rejected,
        )
    )

    late_matrix = X72TernaryEchoMatrix(capacity=4)
    register(late_matrix, history, trend, candidate, "LATE", second=17)
    timeout = late_matrix.expire(
        correlation_id="LATE",
        observed_at_utc="2026-09-18T22:05:00.000Z",
    )
    late = late_matrix.observe_echo(
        correlation_id="LATE",
        observed_at_utc="2026-09-18T22:05:01.000Z",
        explicit_confirmation=True,
        echo_origin_id="ROCK_A",
        evidence={"arrived_after_timeout": True},
    )
    checks.append(
        check(
            "late echo represented",
            timeout.echo_state == 0
            and late.echo_state == 1
            and late.provenance_state == 1
            and late.condition == "ECHO_LATE",
        )
    )

    duplicate_matrix = X72TernaryEchoMatrix(capacity=8)
    register(duplicate_matrix, history, trend, candidate, "DUP", second=18)
    first_echo = duplicate_matrix.observe_echo(
        correlation_id="DUP",
        observed_at_utc="2026-09-18T22:05:02.000Z",
        explicit_confirmation=True,
        echo_origin_id="ROCK_A",
        evidence={"packet": 1},
    )
    frames_before_duplicate = len(duplicate_matrix.frames)
    duplicate_echo = duplicate_matrix.observe_echo(
        correlation_id="DUP",
        observed_at_utc="2026-09-18T22:05:03.000Z",
        explicit_confirmation=True,
        echo_origin_id="ROCK_A",
        evidence={"packet": 2},
    )
    checks.append(
        check(
            "duplicate echo idempotent",
            duplicate_echo.echo_h256 == first_echo.echo_h256
            and len(duplicate_matrix.frames) == frames_before_duplicate,
        )
    )

    conflicting_echo = duplicate_matrix.observe_echo(
        correlation_id="DUP",
        observed_at_utc="2026-09-18T22:05:04.000Z",
        explicit_confirmation=False,
        echo_origin_id="ROCK_A",
        evidence={"packet": 3},
    )
    checks.append(
        check(
            "repeated conflicting echo is mismatch",
            conflicting_echo.condition == "ECHO_MISMATCH"
            and conflicting_echo.echo_state == -1,
        )
    )
    matrix_a = X72TernaryEchoMatrix(capacity=8)
    matrix_b = X72TernaryEchoMatrix(capacity=8)
    for corr in ("ORDER-A", "ORDER-B"):
        register(matrix_a, history, trend, candidate, corr, second=19)
    for corr in ("ORDER-B", "ORDER-A"):
        register(matrix_b, history, trend, candidate, corr, second=19)

    hashes_a = {}
    hashes_b = {}
    for corr in ("ORDER-A", "ORDER-B"):
        hashes_a[corr] = matrix_a.observe_echo(
            correlation_id=corr,
            observed_at_utc="2026-09-18T22:06:00.000Z",
            explicit_confirmation=True,
            echo_origin_id="ROCK_A",
            evidence={"a": 1, "b": 2},
        ).echo_h256
        hashes_b[corr] = matrix_b.observe_echo(
            correlation_id=corr,
            observed_at_utc="2026-09-18T22:06:00.000Z",
            explicit_confirmation=True,
            echo_origin_id="ROCK_A",
            evidence={"b": 2, "a": 1},
        ).echo_h256
    checks.append(
        check("registration/evidence order deterministic", hashes_a == hashes_b)
    )

    empty_history = X72ObservationHistory(capacity=4)
    empty_trend = X72TrendAnalyzer().analyze(empty_history)
    empty_candidate = X72DecisionCandidate().generate(empty_history, empty_trend)
    try:
        X72TernaryEchoMatrix().register_intent(
            history=empty_history,
            trend=empty_trend,
            candidate=empty_candidate,
            correlation_id="EMPTY",
            origin_id="ROCK_A",
            target_id="LAKE",
            intent_h256="0" * 64,
            observed_at_utc="2026-09-18T22:06:01.000Z",
        )
    except ValueError:
        empty_input_rejected = True
    else:
        empty_input_rejected = False
    checks.append(check("empty source rejected", empty_input_rejected))

    bad_entity_candidate = replace(candidate, entity_id="QUEEN-X72-OTHER")
    try:
        X72TernaryEchoMatrix().register_intent(
            history=history,
            trend=trend,
            candidate=bad_entity_candidate,
            correlation_id="BAD-ENTITY",
            origin_id="ROCK_A",
            target_id="LAKE",
            intent_h256="0" * 64,
            observed_at_utc="2026-09-18T22:06:02.000Z",
        )
    except ValueError:
        bad_entity_rejected = True
    else:
        bad_entity_rejected = False

    bad_candidate = replace(candidate, candidate_type="OBSERVE_MORE")
    try:
        X72TernaryEchoMatrix().register_intent(
            history=history,
            trend=trend,
            candidate=bad_candidate,
            correlation_id="BAD-CANDIDATE",
            origin_id="ROCK_A",
            target_id="LAKE",
            intent_h256="0" * 64,
            observed_at_utc="2026-09-18T22:06:03.000Z",
        )
    except ValueError:
        bad_candidate_rejected = True
    else:
        bad_candidate_rejected = False

    bad_source_hash = replace(candidate, candidate_h256="0" * 64)
    try:
        X72TernaryEchoMatrix().register_intent(
            history=history,
            trend=trend,
            candidate=bad_source_hash,
            correlation_id="BAD-SOURCE-HASH",
            origin_id="ROCK_A",
            target_id="LAKE",
            intent_h256="0" * 64,
            observed_at_utc="2026-09-18T22:06:04.000Z",
        )
    except ValueError:
        bad_source_hash_rejected = True
    else:
        bad_source_hash_rejected = False

    checks.append(
        check(
            "source identity/candidate/hash discipline",
            bad_entity_rejected and bad_candidate_rejected and bad_source_hash_rejected,
        )
    )

    tampered_trend = replace(trend, r_exec_mean=999.0)
    tampered_candidate = replace(candidate, condition="FORGED_CONDITION")
    try:
        X72TernaryEchoMatrix._validate_sources(
            history, tampered_trend, candidate
        )
    except ValueError:
        tampered_trend_rejected = True
    else:
        tampered_trend_rejected = False
    try:
        X72TernaryEchoMatrix._validate_sources(
            history, trend, tampered_candidate
        )
    except ValueError:
        tampered_candidate_rejected = True
    else:
        tampered_candidate_rejected = False
    checks.append(
        check(
            "fast hash integrity rejects frame tampering",
            tampered_trend_rejected and tampered_candidate_rejected,
        )
    )

    original_analyze = X72TrendAnalyzer.analyze
    original_generate = X72DecisionCandidate.generate

    def forbidden_analyze(*args, **kwargs):
        raise AssertionError("fast path must not recompute TrendAnalyzer")

    def forbidden_generate(*args, **kwargs):
        raise AssertionError("fast path must not recompute DecisionCandidate")

    X72TrendAnalyzer.analyze = forbidden_analyze
    X72DecisionCandidate.generate = forbidden_generate
    try:
        fast_matrix = X72TernaryEchoMatrix(capacity=4)
        register(
            fast_matrix,
            history,
            trend,
            candidate,
            "FAST-PATH-NO-RECOMPUTE",
            second=27,
        )
        fast_path_no_recompute = True
    finally:
        X72TrendAnalyzer.analyze = original_analyze
        X72DecisionCandidate.generate = original_generate

    deep_result = X72TernaryEchoMatrix._deep_validate_sources(
        history, trend, candidate
    )
    fast_result = X72TernaryEchoMatrix._validate_sources(
        history, trend, candidate
    )
    checks.append(
        check(
            "fast path avoids recomputation and deep verify remains available",
            fast_path_no_recompute and fast_result == deep_result,
        )
    )

    invalid_trits = [True, False, float("nan"), float("inf"), 0.5, 2, -2, "1"]
    trit_rejections = 0
    for value in invalid_trits:
        try:
            _validate_trit(value, "test_trit")
        except ValueError:
            trit_rejections += 1
    checks.append(
        check(
            "strict trit validation",
            trit_rejections == len(invalid_trits)
            and [_validate_trit(v, "valid") for v in (-1, 0, 1)] == [-1, 0, 1],
        )
    )
    before_history = [record.to_dict() for record in history.records]
    before_trend = trend.to_dict()
    before_candidate = candidate.to_dict()

    det_a = X72TernaryEchoMatrix(capacity=4)
    det_b = X72TernaryEchoMatrix(capacity=4)
    for matrix in (det_a, det_b):
        register(matrix, history, trend, candidate, "DETERMINISTIC", second=20)
    frame_a = det_a.observe_echo(
        correlation_id="DETERMINISTIC",
        observed_at_utc="2026-09-18T22:07:00.000Z",
        explicit_confirmation=True,
        echo_origin_id="ROCK_A",
        evidence={"proof": ["explicit", "correlated"]},
    )
    frame_b = det_b.observe_echo(
        correlation_id="DETERMINISTIC",
        observed_at_utc="2026-09-18T22:07:00.000Z",
        explicit_confirmation=True,
        echo_origin_id="ROCK_A",
        evidence={"proof": ["explicit", "correlated"]},
    )
    checks.append(
        check(
            "deterministic echo frame",
            frame_a.to_dict() == frame_b.to_dict()
            and frame_a.echo_h256 == frame_b.echo_h256,
        )
    )
    checks.append(
        check(
            "input immutability",
            before_history == [record.to_dict() for record in history.records]
            and before_trend == trend.to_dict()
            and before_candidate == candidate.to_dict(),
        )
    )

    try:
        frame_a.evidence["tamper"] = True  # type: ignore[index]
    except TypeError:
        outer_evidence_immutable = True
    else:
        outer_evidence_immutable = False

    nested_matrix = X72TernaryEchoMatrix(capacity=4)
    register(
        nested_matrix,
        history,
        trend,
        candidate,
        "NESTED-EVIDENCE",
        second=28,
    )
    nested_frame = nested_matrix.observe_echo(
        correlation_id="NESTED-EVIDENCE",
        observed_at_utc="2026-09-18T22:09:00.000Z",
        explicit_confirmation=True,
        echo_origin_id="ROCK_A",
        evidence={"proof": ["a"], "nested": {"items": [1, 2]}},
    )
    nested_hash_before = nested_frame.echo_h256
    try:
        nested_frame.evidence["observed_evidence"]["proof"].append("tamper")  # type: ignore[union-attr]
    except (AttributeError, TypeError):
        nested_list_immutable = True
    else:
        nested_list_immutable = False
    try:
        nested_frame.evidence["observed_evidence"]["nested"]["items"] += (3,)  # type: ignore[index,operator]
    except (AttributeError, TypeError):
        nested_mapping_immutable = True
    else:
        nested_mapping_immutable = False

    defensive_copy = nested_frame.to_dict()
    defensive_copy["evidence"]["observed_evidence"]["proof"].append("copy-only")
    copy_isolated = (
        "copy-only"
        not in nested_frame.to_dict()["evidence"]["observed_evidence"]["proof"]
        and nested_frame.echo_h256 == nested_hash_before
    )
    checks.append(
        check(
            "echo evidence immutable",
            outer_evidence_immutable
            and nested_list_immutable
            and nested_mapping_immutable
            and copy_isolated,
        )
    )

    checks.append(
        check(
            "hash chain traceability",
            frame_a.source_history_h256 == history.deterministic_report()["report_h256"]
            and frame_a.source_trend_h256 == trend.trend_h256
            and frame_a.source_candidate_h256 == candidate.candidate_h256
            and frame_a.intent_h256
            == intent_hash(candidate, "DETERMINISTIC"),
        )
    )

    bounded = X72TernaryEchoMatrix(capacity=2)
    for idx, corr in enumerate(("BOUND-1", "BOUND-2", "BOUND-3")):
        register(bounded, history, trend, candidate, corr, second=21 + idx)
        bounded.observe_echo(
            correlation_id=corr,
            observed_at_utc=f"2026-09-18T22:08:0{idx}.000Z",
            explicit_confirmation=True,
            echo_origin_id="ROCK_A",
            evidence={"index": idx},
        )
    checks.append(
        check(
            "bounded resolved memory",
            len(bounded.frames) == 2 and bounded.resolved_count == 2,
        )
    )

    pending = X72TernaryEchoMatrix(capacity=2)
    register(pending, history, trend, candidate, "PENDING-1", second=24)
    register(pending, history, trend, candidate, "PENDING-2", second=25)
    try:
        register(pending, history, trend, candidate, "PENDING-3", second=26)
    except OverflowError:
        pending_bounded = True
    else:
        pending_bounded = False
    checks.append(
        check(
            "bounded pending memory",
            pending_bounded and pending.pending_count == 2,
        )
    )

    source = (ROOT / "ternary_echo" / "echo.py").read_text(encoding="utf-8")
    forbidden_transport = (
        "QueenCore",
        "/api/fault",
        "/api/repair",
        "requests.",
        "urllib.",
        "websockets.",
        'method="POST"',
        'method="PUT"',
        'method="PATCH"',
        'method="DELETE"',
    )
    checks.append(
        check(
            "no mutation transport or local Queen",
            not any(token in source for token in forbidden_transport),
        )
    )
    checks.append(
        check(
            "event driven no busy loop",
            "while " not in source
            and "threading" not in source
            and "sleep(" not in source
            and X72TernaryEchoMatrix.EVENT_DRIVEN is True
            and X72TernaryEchoMatrix.NO_BUSY_LOOP is True,
        )
    )

    public_methods = {
        name
        for name, value in inspect.getmembers(
            X72TernaryEchoMatrix, predicate=inspect.isfunction
        )
        if not name.startswith("_")
    }
    checks.append(
        check(
            "no action execution surface",
            public_methods
            == {"register_intent", "observe_echo", "expire", "matrix_states"},
            detail=str(sorted(public_methods)),
        )
    )

    checks.append(
        check(
            "read only invariants",
            X72TernaryEchoMatrix.READ_ONLY is True
            and X72TernaryEchoMatrix.NO_MUTATION_TRANSPORT is True
            and X72TernaryEchoMatrix.NO_ACTION_EXECUTION is True
            and X72TernaryEchoMatrix.DETERMINISTIC is True,
        )
    )

    encoded = json.dumps(frame_a.to_dict(), sort_keys=True, separators=(",", ":"))
    checks.append(
        check(
            "echo frame serializable",
            '"echo_h256"' in encoded and len(frame_a.echo_h256) == 64,
        )
    )

    report = {
        "schema": "ANTMUX-X72-TERNARY-ECHO-ACCEPTANCE-v0.1",
        "checks_total": len(checks),
        "checks_passed": sum(1 for item in checks if item["ok"]),
        "checks_failed": sum(1 for item in checks if not item["ok"]),
        "matrix_states": [list(item) for item in TERNARY_MATRIX],
        "signed_plouf": [list(item) for item in signed_results],
        "deterministic_echo_h256": frame_a.echo_h256,
        "verdict": "PASS" if all(item["ok"] for item in checks) else "FAIL",
        "checks": checks,
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    result = run()
    if result["verdict"] != "PASS":
        raise SystemExit(1)
