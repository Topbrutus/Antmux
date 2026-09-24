# X72 — Progressive Chakra Pump Overlay v0.1

## Purpose

This module models the progressive software traversal requested for X72:

    cycle 1: CH1 -> CH2 -> CH1
    cycle 2: CH1 -> CH2 -> CH3 -> CH2 -> CH1
    cycle 3: CH1 -> CH2 -> CH3 -> CH4 -> CH3 -> CH2 -> CH1
    ...
    cycle 6+: CH1 -> CH2 -> CH3 -> CH4 -> CH5 -> CH6 -> CH7
              -> CH6 -> CH5 -> CH4 -> CH3 -> CH2 -> CH1

A completed return to CH1 is required before the next target level is unlocked.

## Separation from the NoyauEngine

The existing NoyauEngine remains unchanged.

The pump is an overlay mounted beside it:

    NoyauEngine --------------------+
                                    |
    QueenCore -> ChakraPumpOverlay  +-> VisualState / WebSocket

The overlay is explicitly marked CANDIDATE, OBSERVATION_ONLY, non-mutating for QueenCore and NoyauEngine, and physical_claim=false.

CH1..CH7 are software-state labels. They do not constitute a biological or medical claim.

## Progression rule

The software state keeps current_level, target_level, direction, completed_cycles, completed_escalations and retained_boost.

retained_boost is a normalized software progress indicator from 0.0 to 1.0. It is not a physical-energy measurement.

The target increases only after a complete return to CH1:

    return_to_CH1
    AND integrity_ready
    AND stability_ready
    => unlock next target, up to CH7

## Runtime guards

Progress is paused when Queen protected integrity does not match the reference or when the Noyau basin has not reached its crystallized stability flag.

Blocked ticks do not accumulate toward the next level transition.

## Cadence

Default deployment cadence:

    ticks_per_level = 240
    Queen dt_sim = 1 / 240 s

Therefore one level-to-level software transition requires one simulated second at the current Queen cadence.

The cadence is configurable and tests use ticks_per_level=1 to verify the exact traversal sequence without changing production defaults.

## Checkpoint and compatibility

The overlay has its own canonical SHA-256 state and checkpoint hash.

It is included in Queen checkpoints but deliberately excluded from the historical Queen whole_projection and protected projection. This preserves the existing Queen H256 semantics.

Historical Queen checkpoints that do not contain the overlay are accepted and receive a fresh CH1 -> CH2 candidate pump.

## Falsifiable software expectations

The implementation is wrong if any of these occur:

1. target level advances before a complete return to CH1;
2. traversal skips an intermediate level;
3. target exceeds CH7;
4. progression continues while integrity or stability guards are false;
5. checkpoint restoration changes the next deterministic state;
6. adding the overlay changes the historical Queen whole/protected hashes.

These are software invariants only; they are not claims about human physiology, chakras, consciousness, or physical energy.
