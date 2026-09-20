# ANTMUX-X72 — HOPSCOTCH PATH ENSEMBLE v0.1

Status: **CANDIDATE / OBSERVATION_ONLY / CHANNEL-ORDER ONLY**

This experiment turns the "marelle" idea into explicit legal traversals without inventing the still-unmapped vertical/depth geometry.

## Input

Every route receives the exact same Da'at Link frame:

- same pre-stereo Z source;
- same sampled tick;
- same generation;
- same B/A decomposition;
- same 12 channel contributions;
- same target `Lc`.

No route gets a privileged source.

## Legal routes

v0.1 defines four deterministic permutations of the 12 channel indices:

- `FORWARD`: 0 -> 11;
- `REVERSE`: 11 -> 0;
- `EVEN_THEN_ODD`;
- `ODD_THEN_EVEN`.

These are software traversal orders only. Channel indices are **not** assigned spatial, anatomical, sefirotic, vertical, or depth meaning.

Every legal route must visit all 12 channels exactly once.

## Per-hop accumulation

For route contributions `c_i = s_i * w_i`, each hop records the cumulative complement-product:

`L_k = 1 - product_(visited i through step k)(1 - c_i)`

The trace therefore measures how quickly a route accumulates link support while it travels.

Each trace records:

- cumulative `L_k` after every hop;
- final `Lc`;
- mean prefix level;
- first step reaching 0.50, 0.75, and 0.90 when reached.

## Important result

The final Da'at Link score is currently commutative:

`Lc = 1 - product_i(1 - c_i)`

Therefore every complete permutation must finish at the **same final Lc**.

What changes with route order is the **intermediate traversal history**, not the final score.

This distinction is useful: if a future model requires the final result itself to depend on route order, it will require an explicitly stateful/non-commutative hop transform. That is **not** assumed in v0.1.

## Full-cycle test

Across one 7200-tick candidate phase cycle:

- 120 synchronized frames were sampled;
- all route ensembles verified;
- all four legal routes ended at the same final `Lc` on every frame;
- cumulative traces remained bounded and monotonic;
- route histories were distinct on 120/120 sampled frames;
- target `Lc` stayed inside `[0,1]`.

## Authority boundary

Hopscotch is removed from `whole_projection()` and cannot modify Queen state or the evidence ledger.

Still deliberately unmapped:

- vertical axis;
- depth axis;
- Tree node geometry;
- sefirah semantics.
