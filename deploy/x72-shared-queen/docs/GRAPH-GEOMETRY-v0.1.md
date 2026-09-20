# ANTMUX-X72 — GRAPH GEOMETRY v0.1

Status: **CANDIDATE / OBSERVATION_ONLY / DISCRETE GRAPH ONLY**

This experiment implements Stage 5 of the ten-image test plan using ordinary discrete graph metrics. The Riemann image is treated only as a prompt to measure geometry rigorously before considering any continuous manifold.

## Candidate topology

The only topology currently justified by the previous software experiments is the temporary operational cycle:

`C12 = 0-1-2-...-11-0`

It is **not** assigned physical, anatomical, sefirotic, vertical, or depth meaning.

## Metric

Distance is unweighted shortest-path distance on `C12`:

`d(i,j) = min(|i-j|, 12-|i-j|)`

Verified graph invariants:

- 12 nodes;
- 12 edges;
- degree sequence: twelve 2s;
- diameter: 6;
- mean unordered-pair distance: `36/11`;
- metric symmetry and triangle inequality hold exhaustively.

## Relabeling invariance

Route geometry is tested under automorphisms of the cycle:

- rotations;
- reflections.

The hop-distance sequence, total walk length, and endpoint distance are unchanged by these relabelings.

## Route geometry

For every Hopscotch route, the layer records:

- graph distance of every hop;
- total walk length;
- endpoint shortest-path distance;
- mean hop distance;
- maximum hop distance;
- endpoint efficiency = endpoint distance / walk length.

Current route lengths:

- `FORWARD = 11`
- `REVERSE = 11`
- `EVEN_THEN_ODD = 23`
- `ODD_THEN_EVEN = 21`

So graph geometry distinguishes traversal families even though the current commutative `Lc` gives them the same final link score.

## Curvature-like diagnostic

For the unweighted cycle only, the code reports the elementary Forman edge diagnostic:

`F(e) = 4 - deg(u) - deg(v)`

Since every endpoint degree is 2 on `C12`, every edge reports `0`.

This is a discrete graph diagnostic only. It is not a Riemann curvature tensor and carries no physical-space interpretation.

## Full-cycle result

Across 7200 Queen ticks / 120 sampled frames:

- 120/120 graph frames verified;
- all C12 metric invariants stayed fixed;
- route-length geometry stayed stable while runtime values changed;
- 120 distinct provenance hashes were observed.

## Authority boundary

Graph Geometry is excluded from `whole_projection()` and cannot mutate Queen, Z, Da'at, Bayes, Hopscotch, oscillator, coupled-field, or eye state.

Still unmapped:

- continuous manifold;
- Riemann metric tensor;
- physical curvature;
- Tree-node geometry;
- vertical axis;
- depth axis.
