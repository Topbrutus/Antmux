# ANTMUX-X72 — PATH CAPACITY v0.1

Status: **CANDIDATE / OBSERVATION_ONLY / BOUNDED SAMPLER**

This experiment implements Stage 6 of the ten-image test plan as a finite combinatorics/capacity test. The Gabriel's Horn image is treated only as a prompt to ask whether a bounded working representation can characterize and sample a much larger route space. No Gabriel's Horn geometry or infinite-space claim is made.

## Complete route space

With 12 distinct channels, the number of complete channel-order permutations is:

`12! = 479001600`

The theoretical prefix count at depth `d` is:

`P(12,d) = 12! / (12-d)!`

The code computes these counts exactly without materializing all prefixes.

## Bounded deterministic beam

v0.1 uses a fixed beam width of `64`.

At each depth:

1. expand the currently retained prefixes by every unused channel;
2. rank candidates deterministically with SHA-256 over `source_h256 + prefix`;
3. retain at most the best 64 prefixes;
4. continue until depth 12.

This is a deterministic bounded sampler, not a full enumeration.

Hard working bounds with the default policy:

- retained prefixes per stage: at most 64;
- stored channel slots: at most `64 * 12 = 768`;
- generated candidates in any tested stage: at most 640;
- retained complete routes: 64.

The implementation explicitly reports:

- `materializes_all_paths = false`;
- `full_coverage_claim = false`.

## What is and is not compressed

The system preserves the **exact combinatorial count** of the full route space and a deterministic bounded sample of complete routes.

It does **not** preserve the detailed identity of all 479,001,600 routes. Therefore this is not lossless compression of the entire route space.

## Geometry of retained routes

Each retained complete route is also measured with the current C12 graph distance. The bounded sample contains multiple graph-walk lengths, so it is not restricted to one traversal family.

## Full-cycle result

Across 7200 Queen ticks / 120 sampled frames:

- 120/120 capacity frames verified;
- the complete path count remained exactly `479001600`;
- every frame retained exactly 64 complete routes;
- working bounds remained respected;
- maximum generated candidates in any stage was 640;
- 120 distinct capacity provenance hashes were observed;
- 120 distinct deterministic route samples were observed as the source changed.

## Authority boundary

Path Capacity is excluded from `whole_projection()` and cannot mutate Queen, Z, Da'at, Bayes, Hopscotch, oscillator, coupled-field, graph geometry, or eye state.

Still unmapped:

- infinite path space;
- Gabriel's Horn geometry;
- lossless storage of every route;
- vertical axis;
- depth axis.
