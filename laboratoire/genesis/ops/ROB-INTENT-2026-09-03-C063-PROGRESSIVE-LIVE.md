# ROB INTENT — C063 progressive public LIVE

Date: 2026-09-03
Authority: Topbrutus
Scope: public read-only projection only

## Mission

Prepare Antmux to accept a future validated C063 public projection before C063 scientific closure.

## Public C063 fields allowed

- validated through C063;
- C063 validated status;
- real next-test plan public ID;
- plan status `FROZEN_PLAN_AWAITING_EXECUTION_BINDINGS`;
- sample count 12;
- execution bindings required/bound/complete = 11/0/false;
- real plan selection performed = true;
- execution admissibility `BLOCKED_MISSING_EXECUTION_BINDINGS`;
- next action `BIND_REAL_EXECUTION_CONTRACT`.

## Strict exclusions

- no private A/B/C/D allocation schedule;
- no randomization seed or allocation digest;
- no private sample-to-arm mapping;
- no provider/model/prompt/GESIS binding values;
- no prompt bytes or hashes;
- no private repository/branch/path/SHA;
- no generator or GESIS write;
- no execution control;
- no C064;
- snapshot fallback and browser read-only boundary remain mandatory.
