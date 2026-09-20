# ANTMUX-X72 — DA'AT LINK v0.2

Status: **CANDIDATE / OBSERVATION_ONLY / LEFT-RIGHT ONLY**

This layer makes the two Da'at outputs explicit and adds a bounded central link score without changing Z, the stereo calculation, or Queen authority.

## Explicit outputs

For every synchronized left/right channel:

`B_i = (G_i + D_i) / 2`

`A_i = (G_i - D_i) / 2`

`B` is the common component. `A` is the left/right differential component.

Both sides remain reconstructable:

`G_i = B_i + A_i`

`D_i = B_i - A_i`

## Candidate central link score

The declared software score is:

`Lc = 1 - product_i(1 - s_i * w_i)`

Current v0.2 normalization is deliberately simple and replaceable:

`s_i = clamp(abs(B_i), 0, 1)`

Default weights are `w_i = 1` for all 12 channels. Custom weights are accepted only inside `[0,1]`.

Properties tested:

- `0 <= Lc <= 1`;
- zero weights imply `Lc = 0`;
- increasing non-negative weights cannot reduce `Lc`;
- the implementation matches the complement-product formula exactly within floating-point tolerance.

## Separation from Bayes

The evidence ledger may observe Z, Da'at, and Lc, but it does not feed back into any of them.

Bayesian confidence is therefore an evidence/accounting layer, not a transformation of the Z state.

## Authority boundary

`daat_link` is observation-only and is removed from `whole_projection()`. It does not change Queen state, ticks, checkpoints, authoritative hashes, or the CAT-eye renderer.

Vertical axis, depth axis, full Tree paths, and sefirah semantics remain unmapped.
