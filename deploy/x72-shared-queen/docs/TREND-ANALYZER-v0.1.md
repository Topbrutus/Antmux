# X72 — Trend Analyzer v0.1

Status: Worker 1 candidate / deterministic read-only descriptive analyzer.

## Purpose

`X72TrendAnalyzer` consumes only `X72ObservationHistory`. It never contacts
Queen Server, never reconstructs Queen state, and never predicts future state.

Authority chain:

`Queen Server -> ObservationAdapter -> ObservationHistory -> X72TrendAnalyzer -> X72TrendFrame`

The Queen Server remains the sole authority for official state, tick, identity,
protected H256, and reference H256.

## Read-only boundary

- `READ_ONLY = True`
- `NO_MUTATION_TRANSPORT = True`
- `DETERMINISTIC = True`
- no HTTP/WebSocket client
- no POST/PUT/PATCH/DELETE route
- no `QueenCore`
- no fault/repair transport
- no prediction or cognitive scoring
## TrendFrame

The stable v0.1 frame contains:

- entity and bounded window sequence/tick boundaries
- FRESH / STALE / UNKNOWN counters
- RECONNECTED and SCHEMA_MISMATCH counters
- tick delta and observation timing statistics
- r_exec min/max/mean/delta
- f_rt min/max/mean/delta
- active_synapses min/max/mean/delta
- event delta
- integrity transitions
- queen_mode transitions
- FAULT intervals
- AUTO_REPAIR / REPAIR intervals
- current H256 closure state
- H256 reclosure count
- source history report H256
- deterministic trend H256

The trend H256 is a representation hash only. It is never a Queen protection
hash and never replaces protected_h256 or reference_h256.
## Temporal semantics

The analyzer preserves the current ordered History window. It never sorts the
window for trend calculations.

Tick delta is the last observed official tick minus the first observed official
tick in the current window. The analyzer never increments or invents ticks.

Observation duration and gap statistics use the source `observed_at`
timestamps when parseable. Missing/unparseable timestamps remain unavailable;
no synthetic duration is created.

## Fault / repair / H256

FAULT intervals are contiguous records where `queen_mode == FAULT`.

Repair intervals are contiguous records where `queen_mode` is
`AUTO_REPAIR` or `REPAIR`.

`h256_closed` describes whether the latest comparable protected/reference
pair is equal. `h256_reclosure_count` counts mismatch -> equality transitions.
## Determinism and provenance

The same History window produces the same TrendFrame and the same trend H256.

`source_history_h256` is the deterministic History report H256 and preserves
the relationship between a TrendFrame and the observation set it summarizes.

The analyzer copies the History record tuple for analysis and does not mutate
History records or source ObservationFrames.

## Non-goals

v0.1 does not implement:

- prediction
- autonomous decisions
- cognitive scoring
- machine learning
- fault injection
- repair
- Queen mutation
- extrapolated official state
- external colony or active agent behavior
