# ANTMUX-X72 — DA'AT EVIDENCE v0.1

Status: **CANDIDATE / OBSERVATION_ONLY**

This module adds a Bayesian-style evidence ledger around the Da'at left/right experiment. It measures repeatability of explicit software invariants only.

## Prior

Each criterion starts with an independent `Beta(1,1)` prior.

After a pass:

`alpha <- alpha + 1`

After a failure:

`beta <- beta + 1`

Posterior mean:

`p = alpha / (alpha + beta)`

A conservative `confidence_floor` is the minimum posterior mean across all criteria. It is a software reliability indicator, not a probability that a wider interpretation is true.

## Tracked criteria

- same pre-stereo source identity;
- same sampled tick;
- opposite left/right stereo angle;
- lossless left/right reconstruction at Da'at;
- center/residual energy identity;
- Da'at gate verification.

A contradiction updates only the affected criterion rather than forcing a global pass/fail verdict.

## Persistence and authority

The ledger is checkpointed so its sample counts survive a normal restart, but it is removed from `whole_projection()` and therefore does not change the authoritative Queen hash. It remains `OBSERVATION_ONLY` and cannot mutate Queen state.
