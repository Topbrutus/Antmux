# X72 — Decision Candidate v0.1

Status: Worker 1 candidate / deterministic internal descriptive classification.

## Purpose

`X72DecisionCandidate` consumes only an already validated
`X72ObservationHistory` plus the matching deterministic `X72TrendFrame`.

Authority chain:

`Queen Server -> ObservationAdapter -> ObservationHistory -> TrendAnalyzer -> DecisionCandidate -> CandidateFrame -> NO ACTION`

The Queen Server remains the sole authority for official state. CandidateFrame
is a representation of evidence, never an action request.

## Absolute boundary

- `READ_ONLY = True`
- `NO_MUTATION_TRANSPORT = True`
- `NO_ACTION_EXECUTION = True`
- `DETERMINISTIC = True`
- no QueenCore
- no network client
- no POST/PUT/PATCH/DELETE transport
- no fault/repair call
- no production deployment
- no prediction
- no cognitive scoring
## CandidateFrame

The stable v0.1 frame contains:

- schema
- entity_id
- source_history_h256
- source_trend_h256
- window_start_tick / window_end_tick
- candidate_type
- condition
- immutable evidence mapping
- source_records_count
- integrity_state
- latest observed queen_mode
- generated_from lineage
- candidate_h256

`candidate_h256` is a deterministic representation hash only. It is not an
authority hash and never replaces protected_h256/reference_h256.

Evidence always contains both source hashes and the source counters used by the
rule that produced the candidate.
## Input verification

Before classification, the module:

1. requires a real `X72ObservationHistory`;
2. requires a real `X72TrendFrame`;
3. recomputes the deterministic TrendFrame from History;
4. verifies `source_history_h256`;
5. verifies entity identity;
6. requires the supplied TrendFrame to equal the recomputed TrendFrame with type-strict structural comparison.

A stale, forged, or unrelated TrendFrame is rejected.

## Deterministic descriptive rule order

1. empty History -> OBSERVE_MORE
2. fewer than two records -> OBSERVE_MORE
3. schema mismatch -> INVESTIGATE_SCHEMA_MISMATCH
4. reconnect/stale evidence -> INVESTIGATE_DISCONNECT
5. unresolved UNKNOWN observation -> OBSERVE_MORE
6. active repair interval -> INVESTIGATE_REPAIR
7. open fault interval -> INVESTIGATE_FAULT
8. open H256 without fault interval -> VERIFY_INTEGRITY
9. observed repair interval -> INVESTIGATE_REPAIR
10. reclosed fault -> VERIFY_INTEGRITY
11. runtime metric variation or in-window excursion -> INVESTIGATE_RUNTIME_CHANGE
12. stable closed window -> NO_CHANGE
13. otherwise -> OBSERVE_MORE

The ordering is part of the v0.1 contract.
## Candidate types

Allowed descriptive categories:

- NO_CHANGE
- OBSERVE_MORE
- VERIFY_INTEGRITY
- INVESTIGATE_FAULT
- INVESTIGATE_REPAIR
- INVESTIGATE_DISCONNECT
- INVESTIGATE_SCHEMA_MISMATCH
- INVESTIGATE_RUNTIME_CHANGE

These labels are internal analysis candidates. They do not trigger anything.

## Non-goals

v0.1 does not implement actuation, Queen control, automatic repair, autonomous
decision execution, network action, active planning, machine learning,
predictive modeling, or external colony behavior.
