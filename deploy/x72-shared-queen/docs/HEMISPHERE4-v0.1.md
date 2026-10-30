# ANTMUX-X72 — HEMISPHERE4 v0.1

Status: **CANDIDATE / OBSERVATION_ONLY**

This module adds a four-corner bilateral projection without mutating Queen state.

## Four corners

- `G_POS` — left / positive lane
- `G_NEG` — left / mirrored-negative lane
- `D_POS` — right / positive lane
- `D_NEG` — right / mirrored-negative lane
- `BOTH` — shared center / crystallization route

The labels POS/NEG are mathematical polarity labels. They are not a claim about moral good/evil,
and this module makes no biological or physical claim.
## Stereo rule

Left and right are evaluated from the same Z3 runtime frame.

The two live positive lanes remain distinct:

- left positive = `source12`
- right positive = `coupled12`

Each side owns its own mirror:

- left negative = reversed sign-mirror of left positive
- right negative = reversed sign-mirror of right positive

The center is the existing 3-channel Z3 center and is tagged `BOTH`.
## Figure-eight routing candidate

The exposed candidate route is:

`LEFT_POSITIVE → CENTER → RIGHT_POSITIVE → CENTER → LEFT_NEGATIVE → CENTER → RIGHT_NEGATIVE → CENTER`

This is routing metadata for the next visual/interaction layer.
It is not yet an autonomous control law.

Every carrier can therefore be identified by both side and polarity:
`G_POS`, `G_NEG`, `D_POS`, `D_NEG`, or `BOTH`.
## Eye render contract

The two eye motifs are intentionally not duplicated animations.

- left motif: `COUNTERCLOCKWISE`
- right motif: `CLOCKWISE`
- right visual: horizontal mirror enabled
- rotation relationship: opposite directions
- visual goal: paired inward/outward motion, never two motifs drifting in the same screen direction

The color basis is bilateral: the exported `bilateral_mean` combines the left and right positive
lanes so the two eyes can receive the same tone while retaining different internal animations.
## Authority and compatibility

`hemisphere4` is derived telemetry only.

- `mutates_queen = false`
- `physical_claim = false`
- excluded from authoritative `whole_projection()` hash
- reconstructed deterministically after checkpoint restore
- existing Stereo27 remains unchanged

This keeps the current authoritative Queen/checkpoint contract compatible while exposing the new
four-corner structure to the UI and later emotion/filter mapping.
