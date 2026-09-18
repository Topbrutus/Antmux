# X72 — Next Module Integration v1

Status: contract implemented by the read-only `X72ObservationAdapter` candidate; Queen authority remains unchanged.

## Goal

Prepare the next X72 module without coupling it to Queen internals.
The module must consume explicit server interfaces and remain replaceable.

## Boundary

Authoritative runtime:
`QueenCore -> persistence -> API/WebSocket -> consumers`

The next module is a consumer/adapter. It is not allowed to become a second Queen.

## Inputs

1. `GET /api/health` for liveness gating.
2. `GET /api/telemetry` for operational observations.
3. `GET /api/state` for a point-in-time functional snapshot.
4. `WS /ws` for continuous shared VisualState.
5. `GET /api/events` and `/api/report` for bounded diagnostics.

## Required consumer behavior

- validate `source/authority` before accepting payloads;
- preserve `entity_id` across correlated observations;
- treat disconnect as UNKNOWN/STALE, never as zero;
- keep timestamps local to the observation layer;
- never synthesize missing Queen values;
- ignore unknown additive fields for forward compatibility.

## Proposed adapter interface

```text
X72ObservationAdapter
  read_health() -> HealthSnapshot
  read_telemetry() -> OperationalSnapshot
  read_state() -> VisualState
  stream_state() -> AsyncIterator[VisualState]
  read_events() -> EventWindow
  read_report() -> RepairReport
```

## Output envelope

Every derived record should carry:

- `observed_at_utc`;
- `entity_id`;
- `source_schema`;
- `source_endpoint`;
- `freshness_ms`;
- `status = FRESH | STALE | UNKNOWN`;
- original payload or a lossless reference to it.

## Failure semantics

HTTP failure, timeout, invalid JSON, schema mismatch and WebSocket disconnect are
separate observable conditions. They must not be collapsed into a cognitive state.

## Gate for implementation

Implementation starts only after the observability contract is merged and deployed.
Minimal acceptance proof: one adapter reads health + telemetry + state, survives one
WebSocket disconnect/reconnect, and produces a deterministic report without mutating
the Queen.
