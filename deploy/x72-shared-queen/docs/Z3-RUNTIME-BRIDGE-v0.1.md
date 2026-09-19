# Z3 Runtime Bridge v0.1

Status: **CANDIDATE / OBSERVATION_ONLY**

This bridge integrates the tested Z3 v0.1 math/provenance stack into the live X72 Queen Server without granting Z3 mutation authority over Queen state.

## Purpose

The live Queen still owns the authoritative seven-synapse state.

The bridge observes that state and constructs a deterministic four-triad / twelve-channel projection so the existing Z3 pipeline can run live:

```text
QueenCore
  ↓ read-only
7 synapses
  ↓ deterministic adapter
4 triads × 3 channels = 12 channels
  ↓ finite Z coefficient history
identity Echo transfer
  ↓
12×12 center coupling
  ↓
3 center + 9 residual numerical view
  ↓
Z3 provenance seals
```

No Z3 result currently changes a synapse, repairs Queen state, executes an action, or alters the protected reference.

## Runtime adapter mapping

Each triad uses the same three observable channels:

```text
x = activity
y = memory
z = crystal
```

The seven Queen synapses are grouped deterministically and must arrive in the exact semantic order `S1..S7`:

```text
G0 = mean(S1,S2)
G1 = mean(S3,S4)
G2 = mean(S5,S6)
G3 = S7
```

The runtime adapter rejects reordered or mislabeled synapse lists instead of silently changing channel meaning.

This grouping is a **project integration choice**, not a physical law or scientific claim.

All seven existing synapses contribute to the projection.

## Sampling

Live Queen execution target:

```text
240 ticks/second
```

Z3 runtime sampling:

```text
1 sample / 60 Queen ticks
≈ 4 samples/second
history = 32 samples
≈ 8 seconds of coefficient history
```

The history is bounded and persisted with the Queen checkpoint.

## Echo transfer

The first live integration deliberately uses a neutral transfer:

```text
gain = 1
delay = 0
Euler Z-Y-Z = (0,0,0)
```

This proves the execution path without inventing a live gain, delay, or Euler control law.

Any non-neutral live Echo law requires a separate versioned decision.

## Center coupling phase

Candidate v0.1 runtime phase:

```text
theta = 2π × ((tick mod 7200) / 7200)
```

Thus one direct center-coupling phase cycle corresponds to one Queen generation period.

This is an internal design mapping only.

It is not a physical interpretation of theta.

## Provenance

For every sampled runtime frame:

- each of the four Echo triads is sealed with the existing Z3 Echo provenance contract;
- the four-triad coupled state is sealed with the existing center provenance contract;
- fast verification must pass before the frame reports `fast_verified=true`.

The live visual state exposes hashes and concise metrics, not the full 12×12 matrix.

Unkeyed SHA-256 remains an integrity/provenance seal, not producer authentication.

## Event bus

The bridge updates internally at approximately 4 Hz.

A concise:

```text
Z3_RUNTIME_FRAME
```

event is emitted once per 240 Queen ticks, approximately once per second at nominal runtime.

This avoids flooding the 512-event ring buffer.

## Clean birth rule

A new Queen now starts with:

```text
activity = 0
memory = 0
crystal = 0
generation = 0
tick = 0
```

Memory and crystallization must therefore be earned by subsequent runtime dynamics rather than being preloaded at birth.

## Measured local integration result — 2026-09-19

With the Z3 runtime bridge enabled:

```text
R_exec ≈ 239.83 ticks/s
F_rt   ≈ 0.99929×
generation = 3
events = 192
Z3 history = 32/32
Z3 fast verification = PASS
Queen Server regression = 40/40 PASS
Z3 runtime bridge test = 10/10 PASS
Z3 runtime bridge adversarial = 11/11 PASS
```

These are local integration measurements, not production measurements.

## Explicit limits

- Z3 is observation-only in v0.1.
- The adapter grouping is a candidate design.
- The Echo transfer is neutral in this version.
- The center phase mapping is a candidate internal clock mapping.
- No autonomous action is produced from a Z3 frame.
- No claim of intelligence, cognition, new physics, or physical extra dimensions is made.
- The binary64 3+9 representation retains the documented numerical limitations from the Z3 center-coupling contract.

## Next safe step

1. keep this work isolated from `main`;
2. publish it on the integration branch;
3. require CI and independent review;
4. only after explicit authorization, deploy the integrated runtime;
5. perform a final production reset to zero after deployment so the new Z3-enabled Queen starts from a genuinely clean state.
