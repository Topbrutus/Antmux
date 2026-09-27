# BRUTUS VERSO DOOR v1

Status: **CANDIDATE / LOCAL MACHINE CONTROL SURFACE**

## Purpose

The Verso Door is the single machine-facing entry point for BRUTUS five-screen workspace control.

Human interaction remains available on the recto (drag/drop, buttons, menus).
Machine interaction uses structured JSON mission cards through one read/execute surface:

```text
RECTO (human)
  -> workspace.js
  -> BRUTUS_DESKTOP_WORKSPACE_V1

VERSO (machine)
  -> BRUTUS_VERSO.execute(JSON mission)
  -> BRUTUS_WORKSPACE_CONTROL
  -> same workspace state
  -> BroadcastChannel/localStorage
  -> SCREEN 1..5
```

The Verso Door does **not** evaluate arbitrary JavaScript and does not expose a network write endpoint.
It only accepts an allow-list of workspace actions.

## Mission card schema

```json
{
  "schema": "ANTMUX-BRUTUS-VERSO-MISSION-v1",
  "mission_id": "MISSION-001",
  "issued_by": "ASTRA",
  "stop_on_error": true,
  "commands": [
    {"action": "DESKTOP_SET", "enabled": true},
    {"action": "WINDOW_ROUTE", "window": "CORE-ENGINE", "screen": 3},
    {
      "action": "WINDOW_PLACE",
      "window": "CORE-ENGINE",
      "screen": 3,
      "x": 16,
      "y": 48,
      "w": 720,
      "h": 560
    },
    {"action": "STATE_SNAPSHOT"}
  ]
}
```

## Allowed actions

- `STATE_SNAPSHOT`
- `WINDOW_LIST`
- `DESKTOP_SET`
- `WINDOW_OPEN`
- `WINDOW_CLOSE`
- `WINDOW_MINIMIZE`
- `WINDOW_ROUTE`
- `WINDOW_PLACE`

Screens are strictly limited to integers `1..5`.
Window identifiers must already exist in the BRUTUS workspace directory.
A mission contains at most 64 commands.

## Receipt / proof trail

Each mission returns:

- mission id;
- issuer label;
- per-command results;
- final workspace snapshot;
- SHA-256 of the input mission;
- SHA-256 of the receipt;
- start/completion timestamps.

The browser stores the latest 100 receipts under:

`BRUTUS_VERSO_AUDIT_V1`

The receipt is also emitted as:

`BRUTUS_VERSO_RECEIPT`

## Browser API

```js
BRUTUS_VERSO.ready()
BRUTUS_VERSO.snapshot()
BRUTUS_VERSO.example()
await BRUTUS_VERSO.execute(missionCard)
```

The lower-level workspace surface is intentionally separate:

`BRUTUS_WORKSPACE_CONTROL`

This keeps one public machine door while preserving the existing workspace engine.

## Safety boundary

v1 controls **workspace/UI state only**.

It does not yet command:

- scientific calculations;
- ZELSTÉRÉOS audio;
- Queen mutations;
- server-side privileged actions.

Those can later become separate validated domains behind the same Verso mission envelope instead of creating multiple unrelated doors.
