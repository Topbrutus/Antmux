# ASTRA CHECKPOINT â€” BRUTUS C7 ROUTER

Date: 2026-10-13
Status before live deployment: local exact-live stage PASS

## Position

C1 Z-STAMP -> C2 Empreinte -> C3 Bibliotheque -> C4 Nouveaute -> C5 Rarete -> C6 Provenance -> C7 Routeur

C7 is implemented as `BRUTUS_C7_SHADOW_ROUTER_V1`.

## Authority

C7 is SHADOW_ONLY.

It does not:
- change queue priority;
- move a packet to another queue;
- skip a computation;
- mutate a value;
- promote proof;
- claim scientific discovery or independence.

`actual_routes_applied` must remain 0.

## Inputs

C7 consumes only already-observed signals:
- C3 exact hit/miss and retention;
- C5 structural rarity class;
- C6 public target summary for the packet Z-ID.

C6 receives a read-only public method `target_summary(z_id)` so C7 does not access C6 private state.

## Shadow route recommendations

Priority order:
1. `CAPACITY_REVIEW` when C3 could not retain the fingerprint;
2. `PROVENANCE_REVIEW` for a C6 operational-independence candidate;
3. `NOVELTY_REVIEW` for a C3 miss / C4 novelty candidate;
4. `RARE_REPLAY` for known RARE_8 / RARE_6 / SCARCE_4 traces;
5. `CONVERGENCE_REVIEW` for CONVERGENT_2 or C6 route diversity;
6. `KNOWN_CONTROL` for COMMON_1_CONTROL;
7. `OBSERVE_ONLY` fallback.

These names are recommendations, not active destinations.

## Local exact-live verification

The patch was applied to an exact POST-C6 copy.

Post-C7 hashes:
- `c6_provenance.py`: `81a24a088817274e423688b3133ca3b7d568b1790fb8a7df2ccb37c31aaeeefd`
- `c7_router.py` Git/Linux: `9290fd8db6a34b0df3e94ad0281963ee3b7c5531fa955eb946e1aa10675c30f6`
- `orchestrator.py`: `e22f0f8dc54765243f2e62a20c2dc841efa6d6bb860a3f0b48fa8f67b7cfb7ee`
- `dashboard.py`: `a146aa18a5ff01c82a879e8810a9a58b359709dd469cb1aa94c571c44224ab6e`

Tests:
- `C7_DECISIONS=PASS`
- `C7_C6_PUBLIC_SUMMARY=PASS`
- `C7_CHAIN=PASS`
- `C7_ROLLOVER=PASS`
- `C7_SHADOW_ROUTER=PASS`

Observed local chain sample: 34 synchronized observations, then 35 after runner rollover.

## Deployment discipline

Workflow: `.github/workflows/deploy-brotoculateur-c7-vps.yml`

Sequence:
1. audit exact PRE/POST hashes;
2. test a staged copy before mutation;
3. save and pause;
4. backup source/status/drop-in;
5. install C7 and the C6 read-only accessor;
6. restart service;
7. resume only after health verification;
8. require C7 observations == C6 observations and `actual_routes_applied == 0`;
9. rollback automatically on failure.

No reset of crystal data is authorized by this workflow.

