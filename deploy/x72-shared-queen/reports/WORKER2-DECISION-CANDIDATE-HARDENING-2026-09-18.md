# Worker 2 — X72 Decision Candidate Hardening — 2026-09-18

Branch: `worker2/x72-decision-hardening`

Base main:

`dc0a9f5b42a9d724e034988d21fed85b6890f4b3`

## Mission

Prepared an independent adversarial hardening layer for
`X72DecisionCandidate v0.1`.

The contract enforces:

`Candidate != Action`

A future candidate may describe a possible interpretation, anomaly, gap, or
insufficient-evidence state. It must remain deterministic, traceable, read-only,
and unable to act on Queen Server.

## Contract self-check

- contract tests: 36/36 PASS
- adversarial cases: 32
- expected candidate-level rejections: 21
- expected upstream rejections: 6
- evidence traceability: PASS
- deterministic source hash: PASS
- input immutability: PASS

Manifest H256:

`68bd6c5f143e3fc2912a1b5671e36009f445c4ba75175edaa7500e045ae1e58c`

## Upstream discipline

All impossible History inputs are exercised through
`X72ObservationHistory.append(ObservationEnvelope)`.

Six current cases are rejected upstream:

- entity change;
- official tick regression;
- NaN;
- infinity;
- bool used as tick integer;
- numeric string used as runtime value.

No private History state is changed to bypass those rejections.

## Candidate-level adversarial coverage

The independent source validator covers:

- missing source_history_h256;
- missing source_trend_h256;
- malformed and untraceable H256;
- entity mismatch;
- empty History / empty TrendFrame;
- partial/contradictory trend source;
- fault without H256 proof;
- repair without prior fault evidence;
- disconnect without reconnect;
- reconnect without disconnect;
- multiple schema mismatches;
- negative runtime;
- impossible active_synapses;
- wrong numeric type;
- bool as count;
- negative/regressive source tick window;
- unknown candidate_type;
- empty/untraceable evidence;
- reversed evidence order;
- repeated identical canonical input.

## Source guard

AST-based source guard self-check: 6/6 PASS.

The guard detects QueenCore, Queen mutation routes, mutation HTTP calls/route
declarations, and explicit POST/PUT/PATCH/DELETE methods while avoiding a blind
substring-only policy.

Real candidate invocation will additionally block common outbound socket and
URL-opening operations.

## Existing X72 validation target

Before merge, the branch must preserve:

- TrendAnalyzer 23/23 PASS
- Trend adversarial PASS
- ObservationHistory 29/29 PASS
- ObservationAdapter 22/22 PASS
- Robustness 30/30 PASS
- Shared Queen 40/40 PASS
- Server Authority 12/12 PASS
- Core H256 PASS
- Python compile PASS
- git diff --check PASS

## Real candidate cross-validation

The verified main baseline still does not contain `decision_candidate`, so
PR #57 correctly remains contract-only when tested alone.

Worker 1 candidate PR #56 was tested independently at exact SHA:

`8d57669bbcc7ebb51018a01bf565b458c6c081ba`

A detached temporary integration worktree was created from that SHA. Only these
Worker 2 hardening files were copied into it:

- `decision_candidate_adversarial_contract.py`
- `run_decision_candidate_adversarial.py`

No DecisionCandidate implementation was copied into PR #57.

Real public API:

`X72DecisionCandidate.generate(history, trend)`

Real adversarial result:

- 21/21 PASS
- 4 EXPECTED_REJECTION
- 4 EXPECTED_REJECTION_UPSTREAM
- candidate failures: 0
- deterministic: PASS
- evidence Mapping: PASS
- evidence traceability: PASS
- normalization via `to_dict()` before `asdict()`: PASS
- History immutability: PASS
- TrendFrame immutability: PASS
- candidate_h256 stability: PASS
- no mutation transport: PASS
- no action execution: PASS
- no local QueenCore: PASS
- source guard: PASS

Candidate regressions at the same SHA:

- DecisionCandidate 23/23 PASS
- TrendAnalyzer 23/23 PASS
- Trend adversarial 30/30 PASS
- ObservationHistory 29/29 PASS
- ObservationAdapter 22/22 PASS
- Robustness 30/30 PASS
- Shared Queen 40/40 PASS
- Server Authority 12/12 PASS
- Core H256 PASS
- Python compile PASS
- git diff --check PASS

## CI integration

The X72 integration workflow now always runs the DecisionCandidate contract
self-check.

If a `decision_candidate` module exists in the branch under test, CI invokes:

`--require-candidate --module decision_candidate --class-name X72DecisionCandidate --method generate`

Otherwise it validates contract-only mode and retains
`DECISION_CANDIDATE_NOT_PRESENT` as the expected structured blocker.

## Boundary

No deployment.
No Queen mutation.
No QueenCore copy.
No direct modification of main.
No PR merge.
