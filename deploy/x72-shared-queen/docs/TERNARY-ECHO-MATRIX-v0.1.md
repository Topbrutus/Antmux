# X72 — Ternary Echo Matrix v0.1

Status: Worker 1 candidate / read-only event-driven correlation and confirmation layer.

## Authority boundary

Architecture:

`Queen Server -> ObservationAdapter -> ObservationHistory -> TrendAnalyzer -> DecisionCandidate -> TernaryEchoMatrix -> NO ACTION`

The Queen Server remains the only official state authority.

X72TernaryEchoMatrix declares:

- `READ_ONLY = True`
- `NO_MUTATION_TRANSPORT = True`
- `NO_ACTION_EXECUTION = True`
- `DETERMINISTIC = True`
- `EVENT_DRIVEN = True`
- `NO_BUSY_LOOP = True`

It has no QueenCore, no HTTP/WebSocket client, no fault/repair call, no
POST/PUT/PATCH/DELETE transport, no prediction and no action execution.

## [CONCEPT FORMALISÉ] Two ternary dimensions

Echo:

- `+1 = POSITIVE_ECHO`: explicit confirmation.
- `0 = UNKNOWN_ECHO`: silence, timeout or insufficient confirmation.
- `-1 = NEGATIVE_ECHO`: explicit negative confirmation.

Provenance:

- `+1 = PROVENANCE_MATCH`: observed echo origin explicitly matches the
  registered origin.
- `0 = PROVENANCE_UNKNOWN`: origin cannot be established.
- `-1 = PROVENANCE_MISMATCH`: observed echo origin explicitly identifies a
  different origin.

Absolute rules:

- silence != negative
- unknown != negative
- correlation != proof
- candidate != action
- echo != action

A `-1` echo is produced only from an explicit negative observation.
`expire()` always produces echo state `0`.

## [CALCULÉ] 3 x 3 = 9

The state is `S = (E, P)`.

| Echo \ Provenance | +1 | 0 | -1 |
| --- | --- | --- | --- |
| +1 | (+1,+1) | (+1,0) | (+1,-1) |
| 0 | (0,+1) | (0,0) | (0,-1) |
| -1 | (-1,+1) | (-1,0) | (-1,-1) |

All nine states are represented by `TERNARY_MATRIX` and are exercised by the
acceptance test.

Trit validation is type-strict. Only Python integers `-1`, `0`, `1`
are valid as trits. Booleans, NaN, infinity, floats, strings and values outside
the set are rejected.

## Correlation and intent seal

Each registered intent carries:

- entity_id
- correlation_id
- origin_id
- target_id
- intent_h256
- source_history_h256
- source_trend_h256
- source_candidate_h256
- registration time

`intent_h256` is the SHA-256 of a canonical identity representation containing
entity, correlation, origin, target and source Candidate hash. It is a
correlation seal, not proof that an echo is true or belongs to the intent.

Before registration, the module recomputes TrendFrame and CandidateFrame from
History and requires type-strict equality with the supplied sources. A stale,
forged or unrelated source frame is rejected.

## X72EchoFrame

The immutable frame contains:

- schema
- entity_id
- correlation_id
- origin_id
- target_id
- intent_h256
- echo_state
- provenance_state
- condition
- observed_at_utc
- source_history_h256
- source_trend_h256
- source_candidate_h256
- immutable evidence
- echo_h256

`echo_h256` is a deterministic representation hash only. It is not a Queen
protection hash and does not replace protected_h256/reference_h256.

Same canonical sources + correlation + observation => same frame and same
`echo_h256`.

## Event-driven lifecycle

`register_intent(...)` records a pending correlation.

`observe_echo(...)` resolves an explicit incoming observation.

`expire(...)` is called by an external event/deadline mechanism and resolves
silence as `echo_state = 0`.

The module starts no timer, thread, polling loop or busy-wait.

Pending correlations, resolved correlations and retained frames are bounded.
When resolved-memory capacity is reached, the oldest resolved correlation is
evicted. Pending memory never silently evicts an unresolved intent; registration
raises an explicit capacity error instead.

## Duplicate, repeated and late observations

- same resolved echo state/provenance => idempotent duplicate;
- conflicting repeated echo => `ECHO_MISMATCH`;
- echo after a `NO_ECHO_TIMEOUT` => `ECHO_LATE`;
- timeout remains UNKNOWN and is never rewritten as an explicit negative.

## Signed plouf acceptance

The explicit ROCK_A scenario produces:

1. positive echo + origin A => `(+1,+1)`
2. positive echo + unknown origin => `(+1,0)`
3. positive echo + origin B => `(+1,-1)`
4. no echo before expiration => `(0,0)`

The fourth case is never automatically converted to `(-1,*)`.

## [MESURÉ] Pre-Echo baseline

A pre-module local synthetic benchmark measured the existing
History -> Trend -> Decision pipeline over 2,000 stable events:

- PROCESS_CPU_TIME: 25.0625 s
- CPU_TIME_PER_EVENT: 12,531.25 us/event
- WALL_TIME: 25.3078802 s
- mean event latency: 12,653.9401 us/event
- memory current delta: 389,754 bytes
- memory peak delta: 436,329 bytes
- RETRY_COUNT: NOT_AVAILABLE
- UNRESOLVED_EVENT_COUNT: NOT_AVAILABLE

This is a local synthetic measurement, not a production claim.

## [MESURÉ] Paired before/after benchmark

A paired local run used 200 stable events for each side with identical pipeline
inputs.

Pre-Echo:

- CPU: 11,562.5 us/event
- wall/event: 11,697.318 us

Post-Echo:

- CPU: 27,734.375 us/event
- wall/event: 28,074.72 us
- mean echo-resolution call: 223.434 us
- ECHO_EVENTS_TOTAL: 200
- ECHO_POSITIVE_COUNT: 200
- ECHO_UNKNOWN_COUNT: 0
- ECHO_NEGATIVE_COUNT: 0
- PROVENANCE_MATCH_COUNT: 200
- PROVENANCE_UNKNOWN_COUNT: 0
- PROVENANCE_MISMATCH_COUNT: 0
- CORRELATION_LOOKUPS: 200
- retained echo frames: 32 / capacity 32

[CALCULÉ]

- CPU overhead: +139.86486486486487 %
- wall-time overhead: +140.00988944645263 %

The large measured overhead is dominated by source-traceability validation,
which recomputes deterministic Trend/Candidate lineage during registration.

## [HYPOTHÈSE]

A small amount of correlation context may reduce total system cost when it
prevents retries, repeated searches, recalculations or unresolved events.

## [NON DÉMONTRÉ]

The performance hypothesis is not confirmed by the current benchmark.

`RETRY_COUNT` and `UNRESOLVED_EVENT_COUNT` are not exposed by this synthetic
workload, so no retry or unresolved reduction can be calculated. The measured
v0.1 cost is an overhead, not a speedup.

## [FUTUR]

Not implemented in v0.1:

- TDOA
- triangulation
- trilateration
- x/y/z localization
- physical geolocation
- physical direction inference

These remain future hypotheses/modules. The v0.1 kernel is only
`Echo x Provenance = 3 x 3`.

## Reproducible benchmark

Run:

`python deploy/x72-shared-queen/tests/benchmark_ternary_echo.py --events 200`

Benchmark output is JSON and labels retry/unresolved metrics
`NOT_AVAILABLE` when they cannot be measured.
