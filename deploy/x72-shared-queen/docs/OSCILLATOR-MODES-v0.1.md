# ANTMUX-X72 — BOUNDED OSCILLATOR MODES v0.1

Status: **CANDIDATE / OBSERVATION_ONLY / NON-QUANTUM**

This experiment implements ordinary bounded software oscillators as the next stage of the ten-image test plan. It does not import quantum energy levels, Planck's constant, or physical-frequency claims.

## Input

Each frame reuses the same Da'at Link source/tick/generation and the explicit center outputs:

- common component `B_i`;
- differential component `A_i`;
- runtime angle `theta`.

No oscillator writes back into Z, Da'at, Hopscotch, Bayes, or Queen.

## Candidate mode definition

Twelve deterministic modes are defined, one per channel:

`mode_number_i = i + 1`

Amplitude:

`a_i = clamp(hypot(B_i, A_i), 0, 1)`

Phase:

`phi_i = remainder(mode_number_i * theta, 2*pi)`

Bounded two-coordinate state:

`x_i = a_i cos(phi_i)`

`y_i = a_i sin(phi_i)`

Therefore the software radius invariant is:

`x_i^2 + y_i^2 = a_i^2`

within floating-point tolerance.

## Why this candidate is useful

The transform separates:

- **amplitude**: derived from the magnitude already present in the Da'at B/A pair;
- **phase**: deterministic from the shared runtime angle and a channel-specific mode number.

It gives a bounded periodic state for experimentation without inventing a physical oscillator.

## Tests

Single-frame verification checks:

- same source/tick as Da'at Link;
- exactly 12 modes numbered 1..12;
- bounded amplitude/state;
- radius identity;
- deterministic phase;
- deterministic hash reproduction;
- Bayes cannot feed back into the oscillator;
- checkpoint reconstruction;
- authoritative Queen hash unchanged.

A full 7200-tick / 120-frame sweep additionally checks:

- every frame verifies;
- every mode remains bounded;
- phase rule remains deterministic;
- maximum radius error remains numerically tiny;
- the oscillator evolves rather than freezing.

## Deliberately unmapped

- quantum energy levels;
- Planck constant;
- physical frequency;
- vertical axis;
- depth axis.

Those require separate justification and are not inferred from the harmonic-oscillator image.
