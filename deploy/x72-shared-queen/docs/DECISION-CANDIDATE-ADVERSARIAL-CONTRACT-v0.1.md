# X72 Decision Candidate — Adversarial Contract v0.1

Status: independent Worker 2 hardening layer.

## Purpose

This harness validates the boundary:

`Candidate != Action`

The future `X72DecisionCandidate` may describe a possible interpretation or
decision candidate, but it must never become an execution path, mutation
transport, second Queen authority, or repair/fault controller.

Authoritative chain remains:

`Queen Server -> ObservationAdapter -> ObservationHistory -> TrendAnalyzer -> DecisionCandidate`

The Queen Server remains the only state authority.

## Current candidate binding

The runner defaults to:

- module: `decision_candidate`
- class: `X72DecisionCandidate`
- method: `analyze`

The runner accepts only public callable shapes that can be inspected without
private-state manipulation:

- `analyze(source)`
- `analyze(history, trend)`
- `analyze(history, trend, source)`

CLI flags can override module, class, and method when Worker 1 publishes the
actual public contract.

If no module exists, the runner returns:

`CANDIDATE_STATUS=BLOCKER`
`BLOCKER=DECISION_CANDIDATE_NOT_PRESENT`

It does not invent candidate-level PASS.

## Public upstream construction

All History data is created only through:

`X72ObservationHistory.append(ObservationEnvelope)`

Trend data is created only through:

`X72TrendAnalyzer.analyze(history)`

Impossible source states rejected by History are classified:

`EXPECTED_REJECTION_UPSTREAM`

The harness never modifies History private attributes or fabricates an invalid
internal History object.

## Decision source contract

The independent test envelope carries provenance and descriptive fields,
including:

- `entity_id`
- `source_history_h256`
- `source_trend_h256`
- `candidate_type`
- `evidence`
- bounded tick/window counters
- runtime summaries
- active synapse summary
- reconnect/schema/fault/repair counters
- H256 closure state

Allowed candidate types are descriptive only:

- `DESCRIPTIVE_CANDIDATE`
- `OBSERVATION_GAP`
- `INTEGRITY_ANOMALY`
- `SCHEMA_ANOMALY`
- `INSUFFICIENT_EVIDENCE`

## Traceability

History and Trend H256 values are transported provenance.

They must:

1. be valid lowercase H256 values;
2. equal the actual public History/Trend hashes;
3. remain unchanged by the candidate;
4. be referenced by non-empty evidence.

Evidence is canonically sorted for the independent deterministic source hash,
so reversing evidence input order does not alter the expected candidate seed.

## Source guard

The guard parses Python AST rather than doing a blind text grep.

It detects:

- local `QueenCore` references;
- `/api/fault`;
- `/api/repair`;
- mutation HTTP calls or route declarations using POST/PUT/PATCH/DELETE;
- explicit mutation `method=` values.

A self-test verifies both unsafe examples and a safe string containing
`POSTMORTEM`, reducing false-positive risk.

## Runtime no-action guard

When a real candidate exists, candidate invocation occurs with common outbound
socket and URL-opening operations patched to fail immediately. Any attempted
transport execution therefore fails the adversarial run.

The CandidateFrame must also remain action-free and preserve source provenance.

## Determinism and immutability

For every valid candidate case:

- the same canonical source is executed twice;
- canonical CandidateFrame representations must match;
- `candidate_h256` must be a valid H256;
- History records and deterministic report must be unchanged;
- TrendFrame must be unchanged;
- the candidate source object must be unchanged.

## Current contract result

Baseline:

`dc0a9f5b42a9d724e034988d21fed85b6890f4b3`

Contract self-check:

- 36/36 PASS
- 32 adversarial cases
- 21 EXPECTED_REJECTION
- 6 EXPECTED_REJECTION_UPSTREAM
- deterministic: PASS
- evidence traceability: PASS
- no input mutation: PASS
- source guard self-check: 6/6 PASS

No `decision_candidate` module exists on this baseline, so real-candidate
execution is correctly blocked until Worker 1 publishes a candidate.
