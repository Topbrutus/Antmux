# ANTMUX-X72 — EMOTION MAP v0.1

Status: **CANDIDATE / VISUAL_ONLY / TUNABLE**

This layer connects 12 visual state controls to the existing eye-light channels. It does not infer emotions from the Queen and it does not claim that the labels are biological measurements.

The purpose of v0.1 is calibration: Topbrutus can move the 12 controls and observe the resulting light mixture before any sensor or inference layer is connected.
## Four triads

1. **CONSCIENCE** — confirmed working labels: `Endormi`, `Méditatif`, `Réveillé`.
2. **ENGAGEMENT** — candidate labels: `Indifférent`, `Curieux`, `Excité`.
3. **RÉGULATION** — candidate labels: `Calme`, `Concentré`, `Énervé`.
4. **TEMPÉRAMENT** — confirmed working labels: `Apaisé`, `Déterminé`, `Fâché`.

The two groups marked candidate are deliberately easy to rename later; their IDs and weight table are isolated in `emotion_map.js`.
## Output channels

Each state can add light to the four native Life Clock channels: yellow outer ring, blue second ring, mauve third ring, and rose inner accent.

It can also affect visual overlays: red tint, gray filter, white reflection, and black breathing stripes.

Native channels remain boost-only. A state may increase illumination but does not erase the native color structure.
## Combination law

All 12 controls accept a continuous strength from 0 to 1.

For each output channel, simultaneous states combine with a bounded monotonic union:

`output = 1 - product(1 - strength_i * weight_i)`

This permits several states to coexist while keeping every channel inside `[0, 1]`. White reflection keeps a visual baseline of `0.35`; black stripes keep a baseline of `0.20`.
## Current visual examples

- `Réveillé` emphasizes blue with some yellow and reflection.
- `Méditatif` emphasizes mauve.
- `Excité` raises rose and blue together.
- `Déterminé` raises yellow and blue together.
- `Fâché` adds a strong red overlay plus yellow protection light and stronger black stripes.

These values are calibration candidates, not semantic truth. They are expected to be adjusted while watching the live CAT-mode eyes.

## Authority boundary

The 12 controls live in browser calibration state and feed only the CAT visual renderer. They do not mutate Queen state, ticks, checkpoints, hashes, Z3, Hemisphere4, or server-authoritative telemetry.
