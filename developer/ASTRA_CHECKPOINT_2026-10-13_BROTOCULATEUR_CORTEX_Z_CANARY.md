# ASTRA CHECKPOINT — Brotoculateur Cortex Z canary

Date: 2026-10-13
Status: ready for guarded VPS canary; not a proof or publication mechanism.

## Intent

Insert the Brutus Cortex / Z-STAMP at the packet-entry boundary without changing integer values:

C1 input -> Brutus Cortex / Z-STAMP -> C2 technical trace -> existing engine.

The 33+4 Colonne 37 architecture remains unchanged. Z-STAMP is part of the Brutus master organ, not an extra vertebra.

## Z identity and lineage

- `z_id = "Z-" + sha256("ZSTAMP-V1|" + integer_value)[:32]`.
- Path is excluded from Z identity, so the same integer material reached by different paths has the same canonical Z-ID.
- Existing `parent_id`, `branch_path`, and `formula_chain` remain the provenance trace.
- Added `z_parent_id` and `z_origin_id` carry Z lineage.
- The integer value is never changed by Z-STAMP.
- No proof or novelty promotion is added.
- Unstamped packets preserve the legacy `state_hash` exactly.

## Canary

Environment flags:

- `BROTO_ZSTAMP_ENABLED=1`
- `BROTO_ZSTAMP_PERCENT=10`

The canary bucket is deterministic from `sha256("ZSTAMP-V1|<value>")`. For the current VPS seed set `343,703,2701,6337,11611`, only `6337` is selected at 10 percent; the other four pass through unstamped.

Selected roots propagate the Z lineage to descendants. Structureur39/crystal-separator reinjections are also entry points because they pass through `ExperimentRunner.seed()`.

## Guard rails

Deployment requires the official API save/pause sequence before mutation. The workflow backs up `engine.py`, `orchestrator.py`, `dashboard.py`, and the pre-deploy status, verifies exact pre-patch SHA-256 hashes, compiles the patched code, runs targeted smoke tests, then restarts and verifies the service before starting the engine again.

Existing Papillon rarity/master configuration is left intact in its separate systemd drop-in.

## Pre-Z rollback artifact

Local rollback ZIP captured from the actual VPS before Colonne 37/Z-STAMP deployment:

`D:\Brutus-backups\BRUTUS_VPS_PRE_COLONNE37_20261013T042355Z.zip`

SHA-256:

`67ea791e1941361ddb111040784246f7ab3e6bb8291b993346ddea7c6df8f14a`

## Local validation

- exact source snapshot patch: PASS
- patched Python compile: PASS
- 100% Z lineage smoke: PASS
- Z disabled legacy compatibility: PASS
- 10% current-seed canary selection: PASS (`6337` selected)
- patcher idempotency: PASS
- workflow YAML parse: PASS
