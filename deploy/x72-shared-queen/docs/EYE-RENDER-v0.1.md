# ANTMUX-X72 — EYE RENDER v0.1

Status: **CANDIDATE / OBSERVATION_ONLY**

This layer models how the existing Life Clock colors may be illuminated inside the two eyes without recoloring the whole eye flatly.

## Native Life Clock light channels

The eye keeps four existing regions:

- `yellow_outer` — outer yellow/orange fire ring
- `blue_second` — second turquoise/blue ring
- `mauve_third` — third mauve/purple ring
- `rose_inner` — small inner pink/rose accent

These controls are **boost-only**: they add illumination and do not dim the native color structure.
## Linked details

A single blue boost drives the native blue family together:

- blue second ring
- blue web / spiderweb lines
- blue crystals

A single yellow boost drives:

- yellow/orange outer ring
- yellow crystals

Mauve and rose keep their own native ring/accent regions.

Several channels may be bright at the same time; this is intentionally allowed for mixed states.
## Stereo eye behavior

Both eyes share one bilateral color basis, but their internal motion is not copied.

- left motif: counterclockwise
- right motif: clockwise
- right eye: horizontally mirrored
- left/right rotation magnitudes are equal and opposite for the same frame

The bilateral signal comes from the Hemisphere4 left/right mean so both eyes can keep the same overall tone while preserving independent stereo geometry.
## Crystal / transparency rule

The optical filter is clearer in the center than at the edge.

Current candidate defaults:

- center alpha: `0.10`
- edge alpha: `0.34`

This is a render parameter only. It is intended to keep the center transparent and crystal-like rather than cloudy.
## Candidate tuning presets

Presets exist only to speed visual calibration; they are not semantic truth and can be adjusted later.

- `focus_blue`
- `protection`
- `dreamy`
- `excited_love`
- `mouse_alert`

`mouse_alert` deliberately lights several native channels together to exercise the mixed-color path.

The older optical overlays are retained separately: red tint, gray filter, white reflection, and black breathing stripes.
