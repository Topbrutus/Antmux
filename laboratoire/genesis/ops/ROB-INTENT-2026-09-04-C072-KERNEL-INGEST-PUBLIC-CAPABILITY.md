# ROB INTENT — ANTMUX C072 KERNEL INGEST PUBLIC CAPABILITY

Date: 2026-09-04
Authority: Topbrutus
Base Antmux main: `dbaf42dc2c27b2b6519060ffb69591b2a3bf86e9`
Seed C072 closure: `3910ba8431504196c02d3b1550b50fc51166aa8b`
Branch: `rob/genesis-c072-kernel-ingest-live-20260904`

## Purpose

Prepare Antmux to render the validated C072 kernel signal ingest interface as a read-only public progression while preserving C071 as the active public Seed source until an explicit Seed publisher dispatch advances it.

## Public C072 state

C071 public state remains the inherited prefix. C072 adds only safe non-secret facts:

- `genesis003_c072=VALIDATED_10_OF_10`
- `kernel_signal_ingest_interface_frozen=true`
- `kernel_signal_ingest_interface_id=KERNEL-SIGNAL-INGEST-INTERFACE-001`
- `kernel_ingest_input_mode=EXACT_BYTES_IN_MEMORY_ONLY`
- `kernel_ingest_required_fields=5`
- `kernel_ingest_unknown_fields_allowed=false`
- `kernel_ingest_content_addressed=true`
- `kernel_ingest_provenance_addressed=true`
- `kernel_ingest_transport_dependency=false`
- `kernel_ingest_signal_decode_performed=false`
- `kernel_ingest_gesis_execution_performed=false`

The public status therefore advances from 73 to exactly 84 lines.

## Safety boundary

- read-only only;
- no Seed private checkout persistence;
- no private closure/candidate/spec/fixture hashes projected;
- no GESIS repo identifier projected;
- no provider/model/prompt/style identity;
- no credentials, paths or URLs;
- no real experiment or experimental audio;
- historical execution state remains 11/7/4 incomplete;
- C071 kernel state remains 8/8 complete;
- no C073;
- no Seed public publication from this Antmux branch.

## Deployment rule

Before merge, PR validation must prove C072 10/10 and smoke-test the exact C072-capable runtime package. Only after merge may the existing authorized deploy workflow install a `MAX_STAGE=C072` runtime. The endpoint must remain C071 until the Seed manual publisher advances the private read-only source.
