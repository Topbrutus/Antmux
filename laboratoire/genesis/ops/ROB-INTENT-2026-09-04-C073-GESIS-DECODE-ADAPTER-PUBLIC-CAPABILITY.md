# ROB INTENT — Antmux C073 GESIS decode-adapter public capability

Date: 2026-09-04
Authority: Topbrutus
Trigger: GO
Base Antmux main: `ea734993a8368b7fce2268a7c0a5d2557bb26334`
Seed scientific C073 closure: `20ea3c3d77c8d934db17ae60bb3032b023dff5a6`
Current Seed public LIVE: C072 / 84 lines

## Objective
Prepare Antmux to understand and render a future validated C073 public projection while remaining strictly read-only and while preserving C072 as the active public stage until Seed performs an explicit manual publication.

## Public C073 facts allowed
The future C073 public projection may add only non-secret contract facts:
- `genesis003_c073=VALIDATED_10_OF_10`
- `gesis_signal_decode_adapter_contract_frozen=true`
- `gesis_signal_decode_adapter_contract_id=GESIS-SIGNAL-DECODE-ADAPTER-CONTRACT-001`
- `gesis_decode_adapter_input_mode=C072_EXACT_BYTES_AND_VALIDATED_DESCRIPTOR_IN_MEMORY_ONLY`
- `gesis_decode_adapter_arraybuffer_policy=COPY_EXACT_BYTES_TO_NEW_ARRAYBUFFER`
- `gesis_decode_runtime_dependency=true`
- `gesis_decode_runtime_identity_required=true`
- `gesis_decode_cross_runtime_equivalence_proven=false`
- `gesis_decode_signal_performed=false`
- `gesis_decode_analysis_performed=false`
- `gesis_decode_pcm_serialization_policy=CHANNEL_MAJOR_FLOAT32_LITTLE_ENDIAN_IEEE754`

C073 next scientific action becomes `VERIFY_GESIS_DECODE_ADAPTER_WITH_DETERMINISTIC_WAV_CONTROL`.

## Forbidden public material
Do not project:
- Seed or GESIS repository identifiers or paths;
- C073 closure/candidate/audit identifiers;
- GESIS commit/blob identifiers;
- contract, runtime, handoff, signal, provenance, ingest or PCM hashes;
- provider/model/prompt/style identities;
- credentials or transport metadata.

## Required implementation discipline
- add C073 source builder, bridge and focused tests using the existing progressive C072 chain;
- exact C072 source remains accepted unchanged;
- exact C073 source must be 95 lines and reduce exactly to trusted C072 / 84 lines;
- all historical 11/7/4 and kernel 8/8 states stay unchanged;
- bridge remains `LIVE_READ_ONLY`, `PUBLIC_READ_ONLY`, `VERIFIED_PUBLIC`, write capability `NONE`;
- C073 public state must explicitly preserve no decode/no analysis and unproven cross-runtime equivalence;
- validate exact package before any VPS deployment;
- modify only the existing progressive validation/deployment path; no new privileged publisher.

## Hard boundary
This Antmux work must not publish Seed C073. Before Seed publication, the deployed runtime may report `MAX_STAGE=C073` internally but the public endpoint must remain exact C072.

No C074 work is authorized here.
