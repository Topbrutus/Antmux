# ASTRA CHECKPOINT — Brutus C2 Empreinte canonique

Date: 2026-10-13
Status: local exact-source validation complete; guarded VPS deployment not yet executed at checkpoint creation.

## Position in Colonne 37

C1 / Brutus Cortex Z-STAMP -> C2 / Empreinte canonique -> existing engine.

C2 is a derived measurement. It does not change the integer, packet routing, proof state, Z identity, or `state_hash`.

## Canonical law

Schema: `BRUTUS_C2_FINGERPRINT_V1`.

C2 is full SHA-256 over canonical compact JSON containing:

- `value`
- `depth`
- `formula_chain`
- `state`
- `z_id`
- `z_parent_id`
- `z_origin_id`

Prefix: `C2-`.

Deliberately excluded volatile physical provenance:

- `packet_id`
- `parent_id`
- `branch_path`

Therefore two physical Y paths carrying the same structural/Z state can share one C2 fingerprint while their original provenance remains fully available elsewhere.

C2 is computed on demand and is not materialized as another field on every `TracePacket`; this avoids per-packet string memory growth.

## Feature guard

Environment flag: `BROTO_C2_ENABLED`.

When disabled, no C2 fingerprint is computed in the runner and C2 counters stay at zero.

When enabled, C2 observes only packets already carrying a Z stamp. Therefore the current Z-STAMP 10 percent canary is also the C2 exposure boundary; C2 does not create a second independent sampling law.

## Exact live baseline

Fresh audit run `38349767104` at 2026-10-13T05:07Z:

- state RUNNING
- processed 93,918
- crystals 1,555,984
- Z enabled 10 percent
- Z selected roots 11
- Z stamped children 150,953
- rarity 10 percent
- disk 58 percent used
- free KB 50,157,780
- audit PASS

Exact current source hashes:

- engine.py `4aa5c6b9f8feed9559ded55b1db72016ebb45c00d2fbc00ff9e92b74ea677db5`
- orchestrator.py `d562dede20d171684d7d5d6d4bcd3f001260fce6b716ce28c1e91168623a0b06`
- dashboard.py `1c47b3f596cf8341f7a0ea54b6118f725349e41b7941e2494684a17766fd43f6`
- sleeping_pool.py `1fe651ff70e4cad7afc8ec216cbad5f361ff839c072408dcc0233e0a0c637124`

The exact Linux source state was reproduced locally after normalizing CRLF/LF and applying the already-live Z sleeping-lineage patch. All four hashes match the VPS audit.

## Expected C2 hashes

After C2 patch on the exact live source copy:

- engine.py `ac956512699ab0bb527449e08fdaeafab9c883eea3565c4abc5d8e4fcc9ac31b`
- orchestrator.py `20e019e58f77fbd0ea5a983112b8ed5809bad236d8f02df52ea3c65f710f0f83`
- dashboard.py `5410dc0aebb273eddf616dc3b08e53666f6473c25eb5a00ebb44003f2bb00ce2`
- sleeping_pool.py unchanged.

## Validation

- patch exact live source: PASS
- Python compile: PASS
- patch idempotency: PASS
- canonical equivalence across different packet_id/parent_id/branch_path: PASS
- value/depth/formula/Z-parent/Z-origin changes alter C2: PASS
- C2 does not mutate packet: PASS
- C2 OFF counters zero: PASS
- current five-seed Z 10 percent canary: PASS (`343` is the selected root; C2 roots=1 and child fingerprint appears after one step)
- cumulative C2 counters survive runner/round replacement: PASS (`5 -> 5` children)
- workflow YAML parse: PASS
- `git diff --check`: PASS

Local microbenchmark only, not a VPS performance claim: 100,000 fingerprint calculations in 0.894843 s, about 8.948 microseconds each on the authorized Topbrutus computer.

## Guarded deployment design

The VPS workflow first copies the exact live package into `/tmp`, applies C2 there, verifies exact post-patch hashes, compiles it, and runs the C2 tests while the live engine continues running.

Only after this staging PASS does it use the official save/pause API, create a backup, copy the three patched files, enable C2, restart, and resume.

Live acceptance requires one-to-one C1 -> C2 counts in the new process:

- C2 total roots == Z total selected roots
- C2 total children == Z total stamped children
- both child counts > 0
- no worker error
- C2 does not alter value or state hash

An ERR trap restores source files, the previous C2 systemd drop-in, and the prior running/paused posture if a post-backup deployment step fails.

No proof or novelty promotion is introduced.
