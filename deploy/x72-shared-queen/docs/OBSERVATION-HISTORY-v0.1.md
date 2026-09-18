# X72 — Observation History v0.1

Status: Worker 1 candidate / read-only bounded history.

## Purpose

`X72ObservationHistory` consumes only observation-layer frames produced by the
existing `X72ObservationAdapter`. It does not contact Queen Server itself and
never owns, reconstructs, predicts, repairs, or mutates Queen state.

Authority chain:

`Queen Server -> X72ObservationAdapter -> ObservationEnvelope -> X72ObservationHistory`

The current adapter type `ObservationEnvelope` is the concrete v0.1
ObservationFrame consumed by History.

## Read-only boundary

- `READ_ONLY = True`
- `NO_MUTATION_TRANSPORT = True`
- no HTTP/WebSocket client in History
- no POST/PUT/PATCH/DELETE route
- no `QueenCore`
- no fault/repair transport
## Stable history record

Each accepted observation becomes an `X72HistoryRecord` with:

- local `sequence_id`
- source `observed_at`
- `entity_id`
- official `tick_count` when present
- source schema and endpoint
- status and condition
- Queen mode and integrity flag when present
- official `protected_h256` and `reference_h256`
- representation-only `payload_h256`
- runtime `r_exec` / `f_rt`
- active synapses and event count

`payload_h256` hashes only the source payload representation. It is not a
Queen protection hash and never replaces `protected_h256` or
`reference_h256`.

## Identity and tick discipline

The first non-null Queen identity becomes the history identity. A conflicting
identity is rejected without modifying the existing history identity.
For authoritative state-bearing FRESH frames (`/api/state` or `/ws`),
History rejects an official tick lower than the last accepted official tick.

An equal tick is allowed because multiple observations can legitimately sample
one server tick. Exact semantic duplicates are rejected deterministically.

History never increments or synthesizes a Queen tick.

## Status semantics

- FRESH: can update the last official record when state-bearing.
- STALE: can be recorded but never promoted to FRESH.
- WEBSOCKET_DISCONNECT: recorded as STALE/UNKNOWN only.
- RECONNECTED: accepted only as FRESH and can update the official record.
- SCHEMA_MISMATCH: accepted only as UNKNOWN.
- UNKNOWN: recorded without inventing state.

## Bounded memory

The history capacity is fixed at construction time. When full, the oldest
window record is evicted before a new accepted record is appended. The latest
official state record is also retained separately in constant memory.

Duplicate tracking is bounded to the active history window.
## Determinism

The same valid frames in the same order produce the same record sequence.

`deterministic_history_report()` removes local ordering metadata
(`sequence_id`, `observed_at`) from the semantic report body and sorts the
complete semantic records canonically before hashing. Equivalent record sets
therefore produce the same report independent of input ordering.

The report hash is an observation artifact only.

## Non-goals

v0.1 does not implement:

- prediction
- decision-making
- scoring
- autonomous action
- learning
- fault injection
- repair
- Queen mutation
- local Queen authority
