# X72 — Legacy Progressive Pump Candidate v0.1

## Status

This file documents the previous direct-mount experiment retained for comparison.

- STATUS: EXPERIENCE / CANDIDATE
- AUTHORITY: OBSERVATION_ONLY
- PHYSICAL_CLAIM: false
- CURRENT_RUNTIME_MOUNT: REMOVED

The candidate module remains available as `app/chakra_pump.py`, but it is no
longer instantiated, stepped, checkpointed or exposed from `QueenCore`.

## Why the mount was removed

The previous branch mounted the candidate inside `QueenCore.__init__()`,
advanced it from `QueenCore.step()`, exposed it through `visual_state()`,
and included it in Queen checkpoints.

That coupling is now treated as Architecture A for comparison only.

The current architecture requires:

```
ROUE EXISTANTE
      |
      | controlled interface
      v
BRIDGE
      |
      v
NEW RESONANCE STRUCTURE
```

The wheel must run without the new structure. The new structure must run
without the wheel.

## Legacy candidate behavior

The preserved pump still models:

```
cycle 1: CH1 -> CH2 -> CH1
cycle 2: CH1 -> CH2 -> CH3 -> CH2 -> CH1
cycle 3: CH1 -> CH2 -> CH3 -> CH4 -> CH3 -> CH2 -> CH1
...
```

This remains useful as a deterministic replay candidate. It is not the
authoritative Route A architecture.

## Comparison rule

Architecture A:
- previous direct coupling;
- replayed only as a standalone candidate;
- not mounted in QueenCore.

Architecture B:
- independent instrumented resonance structure;
- REF + C1..C7;
- signal generator;
- FFT, amplitude, phase, delay, coherence and bandwidth;
- Route A sensors;
- read-only bridge by default.

No conclusion is based on visual similarity alone. Measurements decide whether
any candidate behavior is retained.
