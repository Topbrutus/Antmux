# Astra checkpoint — Brotoculateur Papillon rarity VPS

Local date: 2026-10-12 (America/Toronto)
VPS validation UTC: 2026-10-13
Branch: `astra/vps-papillon-rarity-20261012`

## Goal

Deploy the Papillon hierarchical rarity law to the VPS without replacing the VPS-specific Brotoculateur features (Sleeping Pool and Papillon Mass), and without importing the local 46-seed experiment.

## VPS baseline audit

GitHub Actions run: `38339545109` — PASS.

- host: `server1.antmux.com`
- service: `brotoculateur.service` active
- API: `127.0.0.1:8781`
- state before deployment: `PAUSED`
- run id before deployment: `run-20261013T005012-807772Z`
- processed packets: `0`
- crystals: `1,466,546`
- root disk: `57%` used, about 51 GB free
- VPS seeds preserved: `343,703,2701,6337,11611`
- orchestrator SHA256: `e68f662ff17e1b70dfb3ca393e45e92326df131565c061f67d49b35fe6396e77`
- dashboard SHA256: `87ae9f700e72a035f2a58d53120670c64d7e5934c7632385d5f0e171fbb1d26c`
- papillon_engine SHA256: `ca45f4ebd9ac4efc241626b9322c2e6d57870873d27982f287d99a9f773871ef`

## Canary deployment

GitHub Actions run: `38339612160` — PASS.

Backup created on VPS before patch:
`~/brotoculateur/backups/papillon-rarity-20261013T030042Z`

Feature configuration:

- `BROTO_RARITY_ENABLED=1`
- `BROTO_RARITY_PERCENT=10`
- `BROTO_PAPILLON_MASTER_ENABLED=1`
- `BROTO_PAPILLON_MASTER_PERCENT=10`

The other 90% of values keep the previous scheduler/routing behavior for comparison.

The source patch is guarded by exact pre-patch SHA256 values and aborts on source drift.

Targeted patch test: PASS.
Deployment verification: PASS.
State after restart: `PAUSED`.
Crystals after restart: `1,466,546` (preserved).

## Hierarchical rarity law

- 1–2 hits: 8 recalculation rights
- 3–4 hits: 6 rights
- 5–8 hits: 4 rights
- 9–16 hits: 2 rights
- 17+ hits: 1 normal right plus one periodic control pass every 32 additional hits

Priority also receives bounded bonuses for independent paths and formula diversity.
Replays preserve the existing packet lineage; they do not create fake independent evidence.

## Controlled canary measurement

GitHub Actions run: `38339724407` — PASS.

The service remained PAUSED; the official `/api/step` endpoint executed 300 controlled steps.

Observed deltas:

- processed packets: `+300`
- crystals: `+31`
- rarity-selected queue pops: `+7`
- baseline/pass-through queue pops: `+293`
- rarity replays enqueued: `+6`
- rarity suppressions: `0`
- periodic control passes: `0`
- Papillon evaluations: `+363`
- active branches after measurement: `127`
- sleeping branches after measurement: `2,829`
- root disk after measurement: `57%` used

## Current decision

Keep the VPS at a 10% canary. The mechanism is operational and did not produce an immediate storage or service regression in the controlled measurement. Do not promote to 100% until a larger observation window shows useful suppression/rarity behavior and stable resource use.
