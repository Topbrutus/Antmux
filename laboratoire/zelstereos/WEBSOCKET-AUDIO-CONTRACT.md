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

## Intended transport

PC PUBLIC_SAFE source -> authenticated HTTPS ingest -> Queen relay -> ZELSTERÉOS WebSocket -> browser render -> local audio synthesis.

The ingest endpoint must remain disabled until a dedicated authentication secret is configured.
