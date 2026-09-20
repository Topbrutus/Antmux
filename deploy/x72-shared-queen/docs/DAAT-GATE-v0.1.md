# ANTMUX-X72 — DA'AT GATE v0.1

Status: **CANDIDATE / OBSERVATION_ONLY / LEFT-RIGHT ONLY**

This experiment deliberately models only the part currently understood: a synchronized left/right stereo pair meeting at a center gate called `DAAT`. It does **not** map the full Tree of Life, vertical motion, depth, religious meaning, or a biological brain model.

## Current route

`Z_INPUT → STEREO_G_D → DAAT`

The existing Stereo Source produces two calculations from the same pre-stereo Z state and the same runtime frame:

- `G`: `+theta`
- `D`: `-theta`

No visual rotation, mirror, or negative-eye mapping is involved.

## Candidate Da'at transform

For every one of the 12 synchronized G/D channels:

`C = (G + D) / 2`

`R = (G - D) / 2`

where `C` is the bilateral center and `R` is the side-difference residual.

The pair is exactly recoverable (within floating-point tolerance):

`G = C + R`

`D = C - R`

This is a reversible center/residual transform. It lets information "meet in the center" without destroying which part came from the left/right difference.

## Invariants being tested

1. G and D originate from the same Z source hash.
2. G and D are calculated on the same sampled tick.
3. Their calculation angles are opposite.
4. Da'at reconstructs both sides from center + residual.
5. Pair energy satisfies `||G||² + ||D||² = 2(||C||² + ||R||²)` within numerical tolerance.
6. The gate remains observation-only and outside the authoritative Queen hash.

## Hopscotch / parcours analogy

The useful computational part of the hopscotch analogy is an **ordered legal traversal** rather than the drawing itself:

- start from one source;
- preserve left/right identity during movement;
- advance in a defined order;
- require both synchronized sides before declaring the center step complete;
- finish a route only when its completion condition is satisfied.

For v0.1, the completion condition is simply `G_AND_D_PRESENT_AT_DAAT`.

## Deliberately not mapped yet

- vertical axis;
- depth axis;
- the full 10/11-node Tree of Life topology;
- the 22 paths;
- sefirah meanings;
- any physical or neurological interpretation.

Those are separate hypotheses and must be tested one at a time rather than inferred from the left/right result.
