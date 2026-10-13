# ASTRA CHECKPOINT — BRUTUS C6 PROVENANCE

Date: 2026-10-13
Status: ready for guarded VPS canary

## Position in the spine

C1 Z-STAMP -> C2 canonical fingerprint -> C3 Library37 -> C4 novelty -> C5 structural rarity -> C6 provenance.

## C6 purpose

C6 is a bounded shadow provenance aggregator. Exact structural identity remains C2. C6 groups exact C2 traces that converge on the same canonical Z-ID target and measures route diversity without changing computation.

Tracked dimensions are compact 64-bit digests of:
- exact C2 fingerprints;
- physical branch paths;
- formula chains;
- Z parents;
- Z origins.

The canonical grouping key is Z-ID, which is the current canonical value target. This is required because formula chain and Z lineage are already part of C2; different formula routes therefore necessarily produce different C2 fingerprints.

## Operational independence candidate

C6 may label a target as an operational independence candidate when either:
- at least two distinct Z origins converge on the same target; or
- at least two distinct Z parents and at least two distinct formula chains converge on the same target.

This is an engineering heuristic only. It is NOT a scientific independence claim, proof, novelty claim, or automatic validation.

## Safety contract

- authority: SHADOW_ONLY
- controls_scheduling: false
- compute_skips: 0
- value_mutated: false
- proof_promotion: false
- scientific_independence_claim: false
- scientific_discovery_claim: false
- persistent: false

Memory is bounded by:
- BROTO_C6_MAX_TARGETS (canary: 16384)
- BROTO_C6_SIGNATURE_CAP (canary: 16 signatures per provenance dimension per target)
- recent status window: 37 observations

## Exact pre/post hashes for guarded patch

Pre-C6 live source (POST-C5):
- orchestrator.py: 0582f5c443d67015ab88286591cbca71650a574ef38859b1563223a93c53285d
- dashboard.py: 1f571adba61d948d0e5189843e0565ebb225f20bbeed9d9159f1f719e804efe9
- c5_rarity.py: d8a02ccecffddffc6db8d8810e84875184861d5446eea8304d23cc8adc483999

Expected post-C6 source:
- orchestrator.py: ad079319b4dfc3c6d0f3994d2638a81ae686015bae9b7aa3a9b5052df69afa74
- dashboard.py: 5af116fe28120ee9c463a4a980751101294fc51e086c54594482b46f37dc7296
- c6_provenance.py: e8aa78c5834bf21a97eb11e7ce0b80a65b405a82282837485f4f23fffb2b0d84

## Local validation

- multi-origin convergence: PASS
- multi-parent + multi-formula convergence: PASS
- bounded capacity: PASS (37 tracked / 63 rejected in test)
- full C1-C6 chain synchronization: PASS
- runner rollover persistence: PASS
- YAML parse: PASS

No VPS mutation has occurred at the time this checkpoint was written.

## Live VPS validation

C6 was deployed as a bounded shadow canary after a PRE_C6 audit passed.

Deployment run:
- GitHub Actions: 38355020150
- result: SUCCESS
- automatic VPS backup created before mutation
- service returned RUNNING
- initial chain: C2=C3=C4=C5=C6 = 6 observations

Independent post-deploy audit:
- GitHub Actions: 38355108545
- result: SUCCESS / C6_AUDIT_ONLY=PASS
- source state: POST_C6
- service: RUNNING
- processed packets: 15173
- crystals: 1618875
- C2 fingerprints: 86614
- C3 observations: 86614
- C4 observations: 86614
- C5 observations: 86614
- C6 observations: 86614
- C6 tracked Z targets: 758
- C6 operational independence candidate targets: 180
- root disk used: 59%
- root disk free: 49299684 KB

Interpretation guard:
- the 180 targets are engineering provenance candidates only;
- they are not proof of mathematical/scientific independence;
- no scheduling authority, compute skip, proof promotion, or value mutation was enabled.
