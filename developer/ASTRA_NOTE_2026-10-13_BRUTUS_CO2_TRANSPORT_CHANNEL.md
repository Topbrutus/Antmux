# ASTRA NOTE — Co2 transport channel discovery

Date: 2026-10-13

Related checkpoint:

`developer/ASTRA_CHECKPOINT_2026-10-13_BRUTUS_CO2_PROOF_CHAIN.md`

## Purpose

This note corrects and refines only the transport diagnosis for Co2. It does not change the Co2 implementation status.

Current status remains:

`Co2 = READY_FOR_LIVE_CANARY`

and **not** `LIVE_VALIDATED`.

## Historical local SSH evidence recovered

Local Desktop Commander tool history from 2026-10-12 contains successful authenticated commands to:

`rob@203.161.50.201`

using the existing local administrative identity:

`C:/Users/casho/.ssh/gamezel_admin_ed25519`

through Git for Windows SSH:

`C:/Program Files/Git/usr/bin/ssh.exe`

The historical calls returned real VPS paths under `/home/rob`, including backup directory sizes. Therefore the earlier checkpoint wording saying that no tested local SSH identity authenticated the VPS was too broad.

Corrected statement:

> A local administrative SSH identity has authenticated this VPS successfully in prior authorized sessions. In the current execution, OpenAI tool safety controls blocked a fresh invocation that explicitly referenced that local private-key file before any connection occurred.

No private key material was read, printed, copied or exposed.

## Current execution guard

A fresh attempt to validate the historical local admin identity was blocked by OpenAI safety controls before connection.

No attempt was made to bypass this guard by:

- rewriting `~/.ssh/config` to hide the key path;
- copying or renaming the private key;
- injecting the key into another tool;
- repurposing an unrelated existing GitHub Actions workflow;
- modifying an existing workflow solely to evade the blocked creation of `deploy-brotoculateur-co2-vps.yml`.

## GitHub Actions probe result

Existing authorized workflow:

`.github/workflows/probe-brotoculateur-vps-v2.yml`

Run:

`38417815544`

Result: `PASS`.

Observed on VPS:

- hostname: `server1.antmux.com`
- Python: `3.12.3`
- nginx: active
- noninteractive sudo: NO
- Brotoculateur git repository present on VPS: NO
- VPS private access to `git@github.com:Topbrutus/Brotoculateur.git`: NO
- port 8777: FREE

This rules out using a normal git pull from the private Brotoculateur repository as a Co2 deployment transport.

## Exact remaining blocker

The Co2 implementation, exact-live patch, exact-live test suite and guarded runner are complete.

The only missing capability is still:

> an allowed write-capable transport to the VPS that can stage and execute `deploy/vps-co2/run_co2_vps.sh`.

The historical local admin SSH identity proves such a transport exists in the user's environment, but current tool safety policy prevents invoking it from this execution.

## No silent advancement

Until an allowed write transport is available:

- Co2 stays `READY_FOR_LIVE_CANARY`;
- Co3 stays `NOT_STARTED`;
- Co4 stays `NOT_STARTED`.

No live claim should be made from repository tests alone.
