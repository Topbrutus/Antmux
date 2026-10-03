# Live Fourmi Transport Source / Actuator v0.1

Status: candidate.

## Purpose

Provide the first server-authoritative software transport seam for one live Fourmi carrying one exact Brutus math material.

The Queen server exposes four private endpoints:

- GET /api/live-transport/ant/{ant_id}
- POST /api/live-transport/attach
- GET /api/live-transport/state/{ant_id}/{material_id}
- POST /api/live-transport/move

All three require a dedicated Bearer transport token.

## Security

The transport token is separate from the public-journal admin token.

Resolution order:

1. ANTMUX_LIVE_TRANSPORT_TOKEN
2. ANTMUX_LIVE_TRANSPORT_TOKEN_FILE
3. $ANTMUX_X72_DATA_DIR/live-transport-token

If the default token file does not exist, the server creates it with restrictive file permissions.

The token is never returned by the API.

## Persistent runtime state

Transport state is stored in:

$ANTMUX_X72_DATA_DIR/live-transport.db

The server persists:

- ANT_ID
- MATERIAL_ID
- MATERIAL_H256
- position
- ATTACHED state
- attached/updated/move Queen ticks
- last command ID
- last authorization ID
- state version

## Persisted Ant identity

GET /ant/{ant_id} returns the exact persisted ANTMUX-ANT-BIRTH-v1 receipt from the private ant registry.

POST /attach refuses an ANT_ID that has no persisted birth receipt or whose persisted role is not SYNAPSE.

This prevents production attachment to invented ANT identifiers.

## Attach

POST /attach establishes the initial server-authoritative runtime attachment.

The operation is idempotent only when ANT, material hash and position are exactly identical.

A conflicting second attachment fails closed.

## State

GET /state returns one combined same-instant transport + Queen snapshot:

- schema = ANTMUX-LIVE-FOURMI-TRANSPORT-v0.1
- authority = QUEEN_SERVER_V0_2
- current Queen tick
- Queen entity_id
- Queen generation
- Queen mode
- Queen integrity_match
- Queen reference_h256
- ANT_ID
- world position
- exact material ID/hash
- ATTACHED state
- state version
- last movement metadata
- state_h256
- integrity_match = true

The embedded Queen tick is exactly the same tick as the transport-state tick.

state_h256 is SHA-256 over the canonical response payload excluding state_h256 and integrity_match. The embedded Queen snapshot is therefore also covered by the hash.

## Move

POST /move accepts only a previously bounded Brutus transport command.

Required invariants include:

- CLOCK_AUTHORITY = QUEEN_SERVER_V0_2
- MAX_MOVES = 1
- SINGLE_USE = true
- PROOF_REF = null
- EXECUTABLE = false
- GATE_AUTHORITY = false
- ROUTING_AUTHORIZATION = AUTHORIZED
- FROM != TO

The persistent state must already exist and match:

- ANT_ID
- MATERIAL_ID
- MATERIAL_H256
- FROM position
- ATTACHED state

COMMAND_ID and AUTHORIZATION_ID are single-use and persisted atomically.

Replay is denied.

The server updates position and command history in one SQLite transaction.

## Acknowledgment boundary

A successful move endpoint returns only:

- STATUS = ACCEPTED
- COMMAND_ID
- AUTHORIZATION_ID
- ANT_ID
- MATERIAL_ID
- FROM
- TO

This acknowledgment means the server accepted and atomically applied the transition.

Brutus still performs a fresh Queen/state read afterward before it creates ANT_MOVE or MATERIAL_MOVE.

Therefore:

ACTION_ACKNOWLEDGED != BRUTUS_MOVEMENT_RECEIPT

## Tests

Local tests passed for:

- persisted ANTMUX-ANT-BIRTH-v1 identity lookup
- rejection of nonexistent/ineligible ants
- persistent attach
- idempotent exact re-attach
- atomic move
- single-use replay rejection
- Bearer authentication
- state hash verification
- exact API acknowledgment shape
- wrong FROM rejection
- unsafe flag rejection
- same-tick Queen + transport snapshot
- full Queen-server route mounting

## Production boundary

This module provides real software runtime state and a real server-side actuator.

It does not claim physical movement.

It does not create mathematical proof.

It does not open wheel ingress.
