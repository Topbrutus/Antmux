# ROB INTENT — C071 KERNEL SIGNAL LIVE

Date: 2026-09-04
Authority: Topbrutus
Repository: Topbrutus/Antmux
Base main: `b2fd6b092a86af2c9f61dcb19cad32a531eefe79`
Branch: `rob/genesis-c071-kernel-signal-live-20260904`

## Purpose

Prepare Antmux to understand a future public C071 projection without changing the current C070 LIVE source and without deploying from this branch.

C071 public meaning must preserve the architectural correction:
- kernel source of truth = signal + measurement provenance;
- historical 11-field real execution contract remains historical and incomplete;
- new kernel contract is 8/8 complete;
- provider/model and prompt/style metadata are not kernel dependencies;
- real experiment remains unauthorized and unexecuted.

## Allowed

- add C071 progressive builder/bridge/test modules;
- preserve C060-C070 backward compatibility;
- expose only safe high-level C071 fields;
- keep all private hashes, repository paths, run IDs and generator identities out of the public envelope;
- validate through existing read-only PR workflows.

## Forbidden

- no VPS deployment from this branch;
- no direct LIVE source write;
- no GESIS write;
- no model/provider identity publication;
- no C072;
- no claim that the historical 11-field execution contract is complete.

## Proposed exact C071 public extension

Starting from exact 63-line C070 projection, change only:
- `genesis003_validated_through=C071`
- `next_scientific_action=DEFINE_KERNEL_NEUTRAL_SIGNAL_INGEST_INTERFACE`

Add exactly ten safe lines:
- `genesis003_c071=VALIDATED_10_OF_10`
- `kernel_signal_contract_frozen=true`
- `kernel_source_of_truth=SIGNAL_AND_MEASUREMENT_PROVENANCE`
- `kernel_bindings_required=8`
- `kernel_bindings_bound=8`
- `kernel_bindings_complete=true`
- `external_generation_metadata_required_by_kernel=false`
- `prompt_style_kernel_dependency=false`
- `real_experiment_execution_authorized=false`
- `historical_execution_contract_policy=IMMUTABLE_HISTORY_NOT_KERNEL_SOURCE_OF_TRUTH`

Expected C071 projection length: 73 lines.

The inherited public `execution_bindings_required=11`, `execution_bindings_bound=7`, `execution_bindings_unbound=4`, and `execution_bindings_complete=false` remain historical execution-contract state; they are not reinterpreted as kernel bindings.
