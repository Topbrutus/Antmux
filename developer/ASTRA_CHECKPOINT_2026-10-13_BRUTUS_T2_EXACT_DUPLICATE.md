# ASTRA CHECKPOINT — BRUTUS T2 EXACT DUPLICATE

Date: 2026-10-13
Stage: T2_EXACT_DUPLICATE
Authority: SHADOW_ONLY
Live deployment at checkpoint creation: NOT YET DEPLOYED

## Purpose

T2 observes exact recurrence of the canonical C2 fingerprint after T1 family classification.
It does not collapse, delete, merge, suppress, reroute, reschedule, or promote any packet.

Identity rule:

- exact duplicate key = full C2 fingerprint;
- T1 family is checked as a consistency invariant;
- physical branch path is NOT part of exact C2 identity;
- alternate physical paths are counted separately as provenance information.

## Shadow outputs

- observations
- unique_fingerprints
- exact_duplicates
- same_family_duplicates
- same_path_duplicates
- alternate_path_duplicates
- cross_family_conflicts
- untracked_capacity
- max_duplicate_count

Hard guards:

- deduplication_applied = false
- packets_collapsed = 0
- controls_routing = false
- controls_scheduling = false
- compute_skips = 0
- value_mutated = false
- proof_promotion = false

## Capacity

Default bounded key count: 131072 exact C2 fingerprints.
If capacity is reached, new keys are counted as UNTRACKED_CAPACITY instead of growing memory without bound.

## Local validation

Exact POST-T1 source was reconstructed and verified before patching.

Test result:

- T2_MODULE = PASS
- T2_CHAIN = PASS
- chain observations = 296
- first-run exact duplicates = 24
- T2_ROLLOVER = PASS
- duplicate count across retained memory = 24 -> 88
- T2_EXACT_DUPLICATE = PASS
- patch idempotence = PASS
- workflow YAML parse = PASS

Expected POST-T2 hashes before Git-normalization verification:

- orchestrator.py = 1dcf3c224e0a8cdfbf819a6ce97a8f5e3c19757a0a310444c1d477418f2c4012
- dashboard.py = 6eb9c68e143f6488c15d8d96861c59980555c124895b2128f3676a0d56b9d44b
- t2_exact_duplicate.py = 52b9a8a39480e0e5201d524eec330effdabb1642988fdeefebb47d00c2421e12

## Live deployment guard

Deployment workflow must:

1. audit exact POST-T1 state;
2. require C1/C2/C3/C4/C5/C6/C7/T1 enabled and synchronized;
3. test T2 against a copied live tree before pause;
4. save + pause;
5. create rollback backup;
6. patch + enable T2;
7. restart and resume;
8. require C2..T2 observation synchronization;
9. require cross_family_conflicts = 0;
10. require packets_collapsed = 0.

A successful T2 observation is NOT a proof claim and does NOT authorize deduplication.

## Live validation — VPS

Deployment run: 38361116013 — SUCCESS
Independent audit run: 38361213202 — PASS
Source state: POST_T2
Service state: RUNNING

Independent live sample:

- processed_packets: 11403
- total_crystals: 1669820
- C2/T1/T2 synchronized observations: 64189
- exact_duplicates: 51479
- duplicate_rate: 80.1991%
- alternate_path_duplicates: 51320
- alternate_path_share_of_duplicates: 99.6911%
- cross_family_conflicts: 0
- estimated unique exact C2 fingerprints in this retained sample: 12710
- root disk used: 59%
- root disk free KB: 48677832

Safety invariants remained true:

- deduplication_applied = false
- packets_collapsed = 0
- controls_routing = false
- controls_scheduling = false
- compute_skips = 0
- proof_promotion = false

Interpretation: T2 is successfully measuring exact structural recurrence. The high duplicate rate is an observation about the current live sample and C2 identity law; it is not yet authorization to skip or collapse computation.
