# ASTRA CHECKPOINT — Brutus C5 Structural Rarity — 2026-10-13

## Scope
C5 is the fifth Brutus vertebra in the recorded path:
C1 Z-STAMP -> C2 fingerprint -> C3 library -> C4 novelty -> C5 structural rarity.

C5 is SHADOW_ONLY. It does not skip computation, influence scheduling, mutate values, or promote proof.

## Source of truth
C5 reads the exact recurrence count already maintained by C3 for each full 256-bit C2 fingerprint.
It does not create a second fingerprint library.

## Structural rarity tiers
- observations 1-2: RARE_8 (reference rights 8)
- 3-4: RARE_6 (reference rights 6)
- 5-8: SCARCE_4 (reference rights 4)
- 9-16: CONVERGENT_2 (reference rights 2)
- 17+: COMMON_1_CONTROL (reference rights 1)

The reference rights are labels only in C5 v1. They are NOT applied to scheduling.
This is structural recurrence of exact C2 fingerprints, not a scientific rarity claim and not the existing value-based Papillon rarity controller.

## Capacity behavior
If C3 cannot retain a new fingerprint because its bounded capacity is full, C5 labels that observation UNTRACKED_CAPACITY instead of inventing a rarity count.

## Local exact-source validation
Built against exact post-C4 live-source hashes:
- orchestrator pre-C5: 0c29aae538c5ea69a3f3a235d7fd377bddd83b339a7f6cda5b091bbd9ae2642f
- dashboard pre-C5: a55b055ee31816fda113f71d28499b1c4a697a8b123ee01dc852d86984dbc7fe
- c3_library: b7970583e688488d0f9fd8a90838d9163d00b08b7e6afedd499434e79a06c434
- c4_novelty: d9669cdcdbd300529ff63a07fc088be6a9e60fdc65315015b1904f83d42e10f2

Expected post-C5 hashes:
- orchestrator: 0582f5c443d67015ab88286591cbca71650a574ef38859b1563223a93c53285d
- dashboard: 1f571adba61d948d0e5189843e0565ebb225f20bbeed9d9159f1f719e804efe9
- c5_rarity: d8a02ccecffddffc6db8d8810e84875184861d5446eea8304d23cc8adc483999

Validation:
- YAML parse PASS
- patch idempotence PASS
- tier boundaries PASS
- C2=C3=C4=C5 chain PASS
- runner rollover persistence PASS

## VPS deployment policy
Workflow: .github/workflows/deploy-brotoculateur-c5-vps.yml
Modes: audit, canary_start, disable.
Mutations require explicit confirmation token BRUTUS-C5-VPS.
The workflow verifies C1/C2/C3/C4 first, stages and tests an exact live copy before pause, then save/pause/backup/restart/start with rollback on error.

No C5 live deployment is claimed by this checkpoint until the workflow has succeeded and an independent audit has passed.

## Live deployment result
PR #266 was merged into main as merge commit `5beb3297fe6d8aa77d235af7a833395b7ae675b6`.

VPS audit before deployment:
- run `38353666664`: PASS
- source state: PRE_C5
- state: RUNNING
- C2 = C3 = C4 = 152,830 observations
- C5 absent

C5 canary deployment:
- run `38353735968`: SUCCESS
- exact live-stage tests: PASS
- save/pause/backup/restart/start: PASS
- first live sample: 23 observations, all RARE_8, max fingerprint count 2, untracked capacity 0
- backup: `brotoculateur/backups/c5-20261013T055347Z`

Independent post-deploy audit:
- run `38353812518`: PASS
- source state: POST_C5
- state: RUNNING
- processed packets: 13,294
- crystals reported: 1,604,771
- C2 = C3 = C4 = C5 = 75,302 observations
- C5 classes:
  - RARE_8: 25,175
  - RARE_6: 16,653
  - SCARCE_4: 17,946
  - CONVERGENT_2: 12,278
  - COMMON_1_CONTROL: 3,250
- root disk used: 58%
- root disk free: 49,478,336 KB

C5 remains SHADOW_ONLY: reference rights are not applied, scheduling is unchanged, compute skips remain zero, values are unchanged, and proof promotion remains disabled.
