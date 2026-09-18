# X72 — Observation Adapter v1

Status: implemented candidate / read-only consumer.

## Purpose

`X72ObservationAdapter` is the first replaceable consumer of the shared Queen
interfaces. It observes the Queen Server without owning, reconstructing,
simulating, or mutating a Queen.

Authoritative chain remains:

`QueenCore -> persistence -> API/WebSocket -> X72ObservationAdapter -> consumers`

## Read-only inputs

- `GET /api/health`
- `GET /api/telemetry`
- `GET /api/state`
- `GET /api/events`
- `GET /api/report`
- `WS /ws`

The adapter contains no fault, repair, reset, reseed, shell, exec, or database
mutation transport.

## Observation envelope

Each observation carries:

- `observed_at_utc`
- `entity_id`
- `source_schema`
- `source_endpoint`
- `freshness_ms`
- `status = FRESH | STALE | UNKNOWN`
- `condition`
- original payload when one exists
- bounded error text when observation failed

## Authority validation

The adapter rejects or marks UNKNOWN when source contracts do not match:

- Queen state / health authority: `QUEEN_SERVER_V0_2`
- telemetry schema: `ANTMUX-X72-OBSERVABILITY-v1`
- telemetry authority: `QUEEN_SERVER_V0_2`

Once an `entity_id` is observed, a different identity in the same adapter
instance is a schema mismatch instead of an implicit Queen replacement.

## Failure semantics

Failures remain observation-layer conditions:

- `HTTP_ERROR`
- `HTTP_CONNECT_ERROR`
- `HTTP_TIMEOUT`
- `HTTP_IO_ERROR`
- `INVALID_JSON`
- `SCHEMA_MISMATCH`
- `WEBSOCKET_CONNECT_ERROR`
- `WEBSOCKET_DISCONNECT`
- `WEBSOCKET_INVALID_JSON`
- `WEBSOCKET_SCHEMA_MISMATCH`

A WebSocket disconnect with a previous valid state yields `STALE` and carries
the exact last authoritative payload. No zero state or local Queen state is
synthesized.

## Reconnect

The stream retries after disconnect. The first valid VisualState after a
successful reconnect is marked `RECONNECTED` and immediately becomes the
authoritative observation.

## Deterministic report

`deterministic_report()` produces a stable observation summary from the same
record set by hashing canonical source payloads and excluding local timestamps
and request latency from the deterministic body.

This report is an observation artifact, not a new Queen identity or state hash.

## Acceptance gate

The candidate passes when it:

1. reads health, telemetry, state, events, and repair report;
2. preserves one Queen identity across observations;
3. validates server source/schema;
4. exposes no mutation transport;
5. leaves protected Queen state unchanged;
6. classifies an unavailable HTTP source as UNKNOWN;
7. freezes the last real VisualState as STALE on disconnect;
8. reconnects to the same Queen;
9. supports two simultaneous observing clients;
10. ends with protected H256 equal to reference H256.