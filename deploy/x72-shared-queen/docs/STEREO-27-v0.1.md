# X72 Stereo-27 v0.1

Status: CANDIDATE  
Authority: OBSERVATION_ONLY  
Mutates Queen: NO  
Physical claim: NO

## Purpose

Stereo-27 is the first explicit two-sided observation layer after the live Z3 bridge.
It turns one canonical 27-unit observation into two complementary 27-unit faces,
for 54 observable stereo channels, with a neutral comparison plane between them.

## Canonical 27-unit input

The current Z3 runtime already exposes enough structure to form 27 scalar units:

```text
V27 = SOURCE12 || COUPLED12 || CENTER3
      12          12          3
```

For v0.1 the current live path is real-valued. A non-negligible imaginary
component is rejected rather than silently discarded.

## Stereo law

For indices i = 0..26:

```text
P[i] = V27[i]
N[i] = -P[26-i]
Z[i] = P[i] + N[26-i]
```

Therefore the exact mirror has:

```text
Z[i] = 0
```

The zero plane is not stored memory and is not a third authority. It is the
measured residual between the two stereo faces.

## PLOUF / PAS-PLOUF

With tolerance epsilon = 1e-12:

```text
PLOUF     <=> max_i |Z[i]| <= epsilon
PAS-PLOUF <=> max_i |Z[i]| >  epsilon
```

This gives the earlier metaphor a deterministic software definition:
an expected mirror closure is PLOUF; a measurable disagreement is PAS-PLOUF.

## Hashes

Each face, the zero plane, and the complete stereo frame are SHA-256 sealed.
The stereo frame verifies its own mirror law and hashes.

Stereo-27 is derived observation state, so it is deliberately excluded from
the authoritative Queen whole-state hash. This keeps existing Z3 v0.1
checkpoints hash-compatible while allowing the new layer to be rebuilt
deterministically after restore.

## Current validation

```text
Stereo-27 dedicated test: 13/13 PASS
Z3 runtime bridge regression: 10/10 PASS
```

No production deployment is authorized by this document. The next safe step is
CI validation on the isolated stereo branch, followed by review before any
live integration.
