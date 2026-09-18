# ANTMUX X72 — Observability Contract v1

Status: WORKER 3 / branch `worker3/x72-docs-observability`
Schema: `ANTMUX-X72-OBSERVABILITY-v1`
Authority: `QUEEN_SERVER_V0_2`
Scope: operational read-only observability.

## Purpose

This contract separates service observability from cognitive/scientific interpretation.
It exposes facts about the running shared-Queen service without creating a second
runtime authority and without mutating Queen state.

## Read interfaces

- `GET /api/health`: minimum liveness and Queen identity.
- `GET /api/state`: authoritative shared `VisualState`.
- `GET /api/telemetry`: operational observability payload defined here.
- `GET /api/events`: recent EventBus window.
- `GET /api/report`: latest repair report.
- `WS /ws`: authoritative `VisualState` stream.

## Telemetry invariants

- endpoint is read-only;
- no local tick is created by a client;
- `entity_id` identifies the same Queen as `/api/state`;
- `authority` is `QUEEN_SERVER_V0_2`;
- `scope` is `operational_read_only`;
- counters describe this server process only.

## Fields

| Field | Meaning |
| --- | --- |
| `schema` | Versioned observability contract identifier |
| `uptime_seconds` | Process uptime measured with monotonic time |
| `tick_count` | Current authoritative Queen tick |
| `queen_mode` | Current server Queen mode |
| `generation` | Current Queen generation |
| `active_synapses` | Enabled synapses in current state |
| `integrity_match` | Protected state equals protected reference |
| `repair_active` | Repair procedure currently active |
| `event_count` | Number of events retained by the Queen EventBus |
| `websocket_clients` | Currently connected WebSocket clients observed by this process |
| `websocket_messages_sent` | VisualState frames sent since process start |
| `cadence_seconds` | Configured tick/checkpoint/WebSocket cadences |

## Interpretation rule

Operational telemetry is evidence about service execution, not independent proof
that a displayed cognitive metric has a validated scientific meaning.

## Consumer rule

A future module may read these interfaces, cache them, and produce reports.
It must not write directly to the SQLite database, modify in-memory Queen objects,
or infer authority from frontend rendering. Mutations remain behind the explicit
server mutation endpoints and their existing controls.

## Compatibility

Additive fields are allowed inside v1. Removing or changing field semantics requires
a new schema identifier. Consumers must ignore unknown additive fields.
