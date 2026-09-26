# ZELSTERÉOS — WebSocket audio contract

## Rule

The real calculation audio cycle MUST be driven by WebSocket events, never by polling.

For each public-safe calculation step:

1. The calculation state/value is produced upstream.
2. Only the public-safe numeric/state payload is transported.
3. The browser receives that payload through the ZELSTERÉOS WebSocket.
4. The browser updates the screen immediately.
5. The browser synthesizes the corresponding sound locally.

Audio data is never transported over the network.

## Polling

HTTP polling is allowed only as a read-only display/state fallback. A polling response MUST NOT trigger cycle audio.

## Diagnostic button

TEST SON is diagnostic-only and is independent from the real calculation cycle. Do not use it as the production trigger.

## Event identity and replay

Each accepted PUBLIC_SAFE ingest receives a monotonically increasing `transport_event_version` when emitted on the ZELSTÉRÉOS WebSocket.

A state replayed only because a browser has just connected is marked `transport_replay=true`. Replays update the screen but MUST NOT trigger production audio.

A newly ingested stage is marked `transport_replay=false`. Its unique transport event version, not only its stage index, identifies the audio event. This allows a new run to audibly start at stage 0 even when the previously displayed state was already stage 0.

## Ordered cycle

The production transport must preserve the seven-stage order:

`1 -> 3 -> 9 -> 36 -> 9 -> 3 -> 1`

A dedicated runner test publishes all seven stages through the authenticated ingest endpoint and verifies their WebSocket order, channel counts, transport versions, and stage workload metrics before deployment.

## Intended transport

PC PUBLIC_SAFE source -> authenticated HTTPS ingest -> Queen relay -> ZELSTERÉRÉOS WebSocket -> browser render -> local audio synthesis.

The ingest endpoint must remain disabled until a dedicated authentication secret is configured.
