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

Before registration, the normal hot path verifies the current History report
hash, the canonical TrendFrame hash, the canonical CandidateFrame hash, entity
identity, tick/count coherence, source-hash links and candidate evidence links.

The SHA-256 values are deterministic integrity/provenance seals, not signed
producer authentication. The fast path assumes the supplied typed frames came
from the already validated upstream X72 pipeline. A private deep verification
path remains available to tests/audits and reconstructs TrendFrame and
CandidateFrame completely when semantic recomputation is required.

A frame whose content changes without a matching canonical hash is rejected.

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

The large measured overhead was dominated by source-traceability validation,
which recomputed deterministic Trend/Candidate lineage during registration.

## [MESURÉ] Performance optimization pass

Profiling of the original hot path over 50 registrations confirmed redundant
work inside `_validate_sources()`:

- TrendAnalyzer.analyze calls: 100 = 2 per registration
- DecisionCandidate.generate calls: 50 = 1 per registration
- History deterministic report calls: 100 = 2 per registration
- mean register_intent: 2,494.118 us

After replacing the normal hot path with canonical hash/provenance validation:

- TrendAnalyzer.analyze calls: 0
- DecisionCandidate.generate calls: 0
- History deterministic report calls: 50 = 1 per registration
- mean register_intent in the same microprofile: 653.902 us

A second 100-sample microprofile measured:

- hash/provenance validation: 631.35 us
- register_intent: 642.417 us
- observe_echo: 43.782 us

The remaining register cost is therefore dominated by validating the History
report and canonical source hash chain rather than recomputing Trend/Decision.

### Paired benchmark v0.2

Method:

- sizes: 200 and 1000 observed events
- repetitions: 3 per scenario
- reported CPU/wall values: medians
- A: History + Trend + Candidate only
- B: Echo on every observed event
- C: sparse Echo, one Echo every 10 observed events
- sparse density was fixed at 10% before measurement and was not tuned to
  produce a favorable result

At 200 events:

- A baseline CPU: 11,328.125 us/event
- A baseline wall: 11,376.5585 us/event
- B every-event CPU: 16,406.25 us/event
- B every-event wall: 16,737.16 us/event
- B CPU overhead: +44.827586206896555 %
- B wall overhead: +47.119711114745286 %
- C sparse CPU: 12,031.25 us/event
- C sparse wall: 12,338.8985 us/event
- C CPU overhead: +6.206896551724128 %
- C wall overhead: +8.458972895889394 %
- median B echo register: 4,195.812 us with tracemalloc instrumentation
- median B echo observe: 212.1285 us with tracemalloc instrumentation
- median B hash validation micro-sample: 626.505 us
- baseline median peak-memory delta: 72,184 bytes
- B median peak-memory delta: 128,438 bytes
- C median peak-memory delta: 105,944 bytes

At 1000 events:

- A baseline CPU: 11,921.875 us/event
- A baseline wall: 11,989.4187 us/event
- B every-event CPU: 16,546.875 us/event
- B every-event wall: 16,666.0217 us/event
- B CPU overhead: +38.79423328964613 %
- B wall overhead: +39.00608625837714 %
- C sparse CPU: 12,046.875 us/event
- C sparse wall: 12,152.0301 us/event
- C CPU overhead: +1.0484927916120546 %
- C wall overhead: +1.3562909434466697 %
- median B echo register: 4,185.8777 us with tracemalloc instrumentation
- median B echo observe: 195.107 us with tracemalloc instrumentation
- median B hash validation micro-sample: 617.527 us
- baseline median peak-memory delta: 74,036 bytes
- B median peak-memory delta: 129,262 bytes
- C median peak-memory delta: 131,498 bytes

The tracemalloc-enabled per-stage register figures are intentionally reported
separately from the lighter hot-path microprofile; instrumentation materially
changes absolute timings.

## [CALCULÉ] Optimization result

Compared with the original 200-event paired measurement:

- old post-Echo CPU: 27,734.375 us/event
- new 200-event median every-event CPU: 16,406.25 us/event
- old CPU overhead: +139.86486486486487 %
- new CPU overhead: +44.827586206896555 %
- old post-Echo wall: 28,074.72 us/event
- new 200-event median every-event wall: 16,737.16 us/event
- old wall overhead: +140.00988944645263 %
- new wall overhead: +47.119711114745286 %

The optimization removes redundant recomputation and materially lowers the
Echo hot-path cost. Echo-every-event remains slower than the pre-Echo pipeline.
The 10% sparse workload approaches baseline at 1000 events but is still
measured as overhead, not a speedup.

## [HYPOTHÈSE]

A small amount of correlation context may reduce total system cost when it
prevents retries, repeated searches, recalculations or unresolved events.

## [NON DÉMONTRÉ]

The broader total-system-cost hypothesis is still not demonstrated.

`RETRY_COUNT` and `UNRESOLVED_EVENT_COUNT` are not exposed by this synthetic
workload, so no retry or unresolved reduction can be calculated. The optimized
v0.1 hot path is substantially cheaper than the original implementation, but
the measured every-event and sparse scenarios remain overhead rather than a
demonstrated speedup.

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

`python deploy/x72-shared-queen/tests/benchmark_ternary_echo.py --sizes 200 1000 --repetitions 3 --sparse-every 10`

Benchmark output is JSON, reports per-stage timings and median run metrics, and
labels retry/unresolved metrics `NOT_AVAILABLE` when they cannot be measured.

The recorded optimization run is preserved in:

`deploy/x72-shared-queen/reports/TERNARY-ECHO-PERFORMANCE-OPTIMIZATION-2026-09-18.json`
