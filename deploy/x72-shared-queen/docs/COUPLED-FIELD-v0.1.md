# ANTMUX-X72 — COUPLED SOFTWARE FIELD v0.1

Status: **CANDIDATE / OBSERVATION_ONLY / NON-PHYSICAL**

This experiment implements Stage 4 of the ten-image test plan as a local software propagation rule. The electromagnetism images are used only as a prompt for paired components, local flux, and accounting discipline. No electric, magnetic, or physical-energy claim is made.

## Input

The field consumes the twelve bounded oscillator modes from the same source/tick/generation.

Two mathematical components are used:

- `X_i` = oscillator x coordinate;
- `Y_i` = oscillator y coordinate.

These are software coordinates only.

## Candidate topology

v0.1 uses a temporary periodic **index ring**:

`0 -> 1 -> ... -> 11 -> 0`

This means only "next channel index" for the propagation experiment. It does not claim spatial geometry, Tree-of-Life geometry, anatomy, or a vertical/depth axis.

## Synchronous local propagation

For either component `v`, define the oriented edge flux:

`F_i = kappa * (v_i - v_(i+1))`

Then update every lane from the same pre-update snapshot:

`v'_i = v_i - F_i + F_(i-1)`

Equivalent form:

`v'_i = (1 - 2*kappa)v_i + kappa*v_(i-1) + kappa*v_(i+1)`

The allowed coupling is `0 <= kappa <= 0.5`; v0.1 defaults to `kappa = 0.125`.

The implementation is explicitly `READ_ALL_THEN_WRITE_ALL`: no lane can observe a neighbor that has already been updated during the same frame.

## Accounting invariants

The ring divergence cancels globally, so the software component sums are conserved:

`sum(X') = sum(X)`

`sum(Y') = sum(Y)`

For the convex coupling range, the squared software norm does not increase:

`E = sum_i (X_i^2 + Y_i^2)`

`E_after <= E_before`

The difference is reported as `software_dissipation`. This is bookkeeping terminology only, not physical energy.

The X and Y spans must also remain non-expanding after one propagation step.

## Full-cycle result

Across 7200 Queen ticks / 120 sampled frames:

- 120/120 coupled-field frames verified;
- X and Y sums stayed conserved;
- software energy never increased;
- X/Y spans never expanded;
- 120 distinct field hashes were observed;
- maximum sum-accounting error was `4.440892098500626e-16`;
- maximum observed energy increase was exactly `0.0`.

## Authority boundary

The coupled field is excluded from `whole_projection()` and cannot mutate Queen state, Z, Da'at, Bayes, Hopscotch, oscillator state, or the CAT renderer.

Still unmapped:

- electric field;
- magnetic field;
- physical energy;
- spatial geometry;
- vertical axis;
- depth axis.
