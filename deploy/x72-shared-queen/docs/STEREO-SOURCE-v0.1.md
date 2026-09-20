# ANTMUX-X72 — STEREO SOURCE v0.1

Status: **CANDIDATE / OBSERVATION_ONLY**

The stereo split is now calculated at the Z source path instead of being simulated by the eye renderer.

## Source rule

A single pre-stereo Z state enters two synchronized calculations on the same runtime frame:

- left / `G`: `CenterCoupling12(+theta)`
- right / `D`: `CenterCoupling12(-theta)`

Both sides therefore receive the same input and the same tick, but the calculation direction is opposite.

## Render boundary

The calculation direction must not be converted into image rotation.

- visible left rotation: none
- visible right rotation: none
- horizontal mirror: none
- negative-eye mapping: none

The renderer receives the resulting left/right data plus their bilateral mean. It does not rotate or mirror the eye motif.

## Compatibility

The previous Hemisphere4 sign-mirror projection remains available as a legacy diagnostic only and is not used by Eye Render. Stereo27 also remains unchanged for compatibility.

Stereo Source is excluded from the authoritative whole-state hash and does not mutate Queen state.
