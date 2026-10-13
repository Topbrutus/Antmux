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

## First canary guard event

The first live canary attempt paused and backed up the running engine, patched the three source files, then stopped before restart because the precomputed patched hashes had been produced on Windows with CRLF line endings. The Linux patch output used LF and therefore had different SHA-256 values. No patched process was started during that failed attempt.

Verified Linux patched hashes from the VPS patch output:

- `engine.py`: `4aa5c6b9f8feed9559ded55b1db72016ebb45c00d2fbc00ff9e92b74ea677db5`
- `orchestrator.py`: `8f644bbfe8bdef4a9f5ebec66b1d540fa762c8ff8524f967e523967fd78b2662`
- `dashboard.py`: `1892c2abf4b3dc535a2b1feeb08678e372bfe925bb786dadeaab1a85c49d61e9`

The workflow is corrected to require these Linux hashes before restart.

## Second canary and observability correction

The corrected-hash canary successfully restarted the patched service with Cortex Z at 10 percent. Live status showed root stamping active (`root_selected` increased rapidly) with no worker error, but `children_stamped` was zero at the sampled instant. Investigation showed that all three Z counters belong to the current `ExperimentRunner`, while `DashboardService._advance_round_unlocked()` replaces that runner at every completed round. The sampled zero therefore cannot serve as session-wide evidence of no propagation.

For safety, Cortex Z was immediately disabled through the guarded workflow. Disable verification passed: service RUNNING, Z enabled false, rollout 0, selected 0, children 0. Patched code remains on disk, but unstamped packets retain the exact legacy state hash and behavior.

A cumulative observability patch now adds session totals across runner/round replacement:

- `total_root_selected`
- `total_root_passthrough`
- `total_children_stamped`
- `cumulative_across_rounds = true`

A deterministic DashboardService test stamps descendants, rolls the runner over, and verifies that the current counter resets while the cumulative child total survives. Local result: `ZSTAMP_CUMULATIVE=PASS 5 5`.

The next canary must require `total_root_selected > 0` and `total_children_stamped > 0` before it is accepted as live lineage evidence.
