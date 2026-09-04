#!/usr/bin/env node
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import {
  extractProgressiveGenesisStatusC073,
  buildProgressiveBridgeInputC073,
  c073ToExactC072Text,
} from './build-public-source-progressive-c073.mjs';
import { extractProgressiveGenesisStatusC072 } from './build-public-source-progressive-c072.mjs';
import { buildProgressivePublicEnvelopeC073 } from './bridge-public-progressive-c073.mjs';

const C072 = `science_baseline=GREEN
genesis003_c041_c060=COMPLETE_VALIDATED
experiment_selection_performed=true
selected_experiment_status=PLANNED_NOT_EXECUTED
hypothesis_selection_performed=false
hypothesis_ranking_produced=false
uncertainty_promotion_performed=false
probabilities_produced=false
evidence_ledger_auto_promotion=false
GENESIS_AUDIT_FAILED=0
genesis003_validated_through=C072
genesis003_c061=VALIDATED_10_OF_10
c061_execution_input=SYNTHETIC_C060_FIXTURE
execution_admissibility=BLOCKED_INCOMPLETE_REAL_EXECUTION_CONTRACT
next_scientific_action=DEFINE_GESIS_SIGNAL_DECODE_ADAPTER_CONTRACT
genesis003_c062=VALIDATED_10_OF_10
real_experiment_spec_id=REAL-EXPERIMENT-SPEC-001
real_experiment_spec_status=FROZEN_CANDIDATE_NOT_SELECTED
real_experiment_family=BLIND_MULTILINGUAL_GESIS_COMPARISON
trial_class=PILOT_COMPARATIVE_NOT_CONFIRMATORY
replicates_per_arm=3
blinded_primary_analysis=true
pretargeted_symbolic_search=false
real_plan_selection_performed=true
genesis003_c063=VALIDATED_10_OF_10
real_next_test_plan_id=REAL-NEXT-TEST-PLAN-001
real_next_test_plan_status=FROZEN_PLAN_AWAITING_EXECUTION_BINDINGS
sample_count=12
execution_bindings_required=11
execution_bindings_bound=7
execution_bindings_complete=false
genesis003_c064=VALIDATED_10_OF_10
real_execution_contract_id=REAL-EXECUTION-CONTRACT-001
real_execution_contract_status=PARTIALLY_BOUND_BLOCKED
execution_bindings_unbound=4
generator_seed_policy_bound=true
gesis_primary_profile_compatible=false
gesis_observed_candidate_recorded=true
genesis003_c065=VALIDATED_10_OF_10
gesis_neutral_path_compatible=true
default_az_profile_still_incompatible=true
analysis_decision_rule_bound=true
genesis003_c066=VALIDATED_10_OF_10
binding_dependency_audit=COMPLETE_NO_NEW_PROVEN_BINDINGS
new_bindings_proven=0
generator_execution_profile_frozen=false
genesis003_c067=VALIDATED_10_OF_10
control_generator_profile=FROZEN_VALIDATED_CONTROL_ONLY
control_generator_deterministic=true
real_generator_bindings_added=3
real_generator_profile_frozen=false
genesis003_c068=VALIDATED_10_OF_10
real_generator_identity_frozen=true
runtime_compatibility_verified=false
language_coverage_verified=false
language_confound_registered=true
genesis003_c069=VALIDATED_10_OF_10
signal_gesis_reproducibility_validated=true
cross_runner_reproducibility_proven=true
calibration_control_passed=true
provider_model_kernel_dependency=false
genesis003_c070=VALIDATED_10_OF_10
measurement_qc_rule_frozen=true
genesis003_c071=VALIDATED_10_OF_10
kernel_signal_contract_frozen=true
kernel_source_of_truth=SIGNAL_AND_MEASUREMENT_PROVENANCE
kernel_bindings_required=8
kernel_bindings_bound=8
kernel_bindings_complete=true
external_generation_metadata_required_by_kernel=false
prompt_style_kernel_dependency=false
real_experiment_execution_authorized=false
historical_execution_contract_policy=IMMUTABLE_HISTORY_NOT_KERNEL_SOURCE_OF_TRUTH
genesis003_c072=VALIDATED_10_OF_10
kernel_signal_ingest_interface_frozen=true
kernel_signal_ingest_interface_id=KERNEL-SIGNAL-INGEST-INTERFACE-001
kernel_ingest_input_mode=EXACT_BYTES_IN_MEMORY_ONLY
kernel_ingest_required_fields=5
kernel_ingest_unknown_fields_allowed=false
kernel_ingest_content_addressed=true
kernel_ingest_provenance_addressed=true
kernel_ingest_transport_dependency=false
kernel_ingest_signal_decode_performed=false
kernel_ingest_gesis_execution_performed=false
`;

function c073() {
  return C072
    .replace('genesis003_validated_through=C072', 'genesis003_validated_through=C073')
    .replace('next_scientific_action=DEFINE_GESIS_SIGNAL_DECODE_ADAPTER_CONTRACT', 'next_scientific_action=VERIFY_GESIS_DECODE_ADAPTER_WITH_DETERMINISTIC_WAV_CONTROL') +
`genesis003_c073=VALIDATED_10_OF_10
gesis_signal_decode_adapter_contract_frozen=true
gesis_signal_decode_adapter_contract_id=GESIS-SIGNAL-DECODE-ADAPTER-CONTRACT-001
gesis_decode_adapter_input_mode=C072_EXACT_BYTES_AND_VALIDATED_DESCRIPTOR_IN_MEMORY_ONLY
gesis_decode_adapter_arraybuffer_policy=COPY_EXACT_BYTES_TO_NEW_ARRAYBUFFER
gesis_decode_runtime_dependency=true
gesis_decode_runtime_identity_required=true
gesis_decode_cross_runtime_equivalence_proven=false
gesis_decode_signal_performed=false
gesis_decode_analysis_performed=false
gesis_decode_pcm_serialization_policy=CHANNEL_MAJOR_FLOAT32_LITTLE_ENDIAN_IEEE754
`;
}

const status = extractProgressiveGenesisStatusC073(c073());
assert.equal(status.validatedThrough, 'C073');
assert.equal(Object.keys(status.values).length, 95);
console.log('PASS C073-LIVE-01 exact 95-line C073 projection accepted');

const input = buildProgressiveBridgeInputC073(status, { now: '2026-09-04T21:40:00Z', liveActive: true });
const envelope = buildProgressivePublicEnvelopeC073(input, { now: '2026-09-04T21:40:00Z' }).envelope;
const metrics = Object.fromEntries(envelope.payload.metrics.map((entry) => [entry.id, entry.value]));
assert.equal(metrics['genesis003-validated-through'], 'C073');
assert.equal(metrics['next-scientific-action'], 'VERIFY_GESIS_DECODE_ADAPTER_WITH_DETERMINISTIC_WAV_CONTROL');
assert.equal(metrics['bridge-write-capability'], 'NONE');
assert.equal(envelope.mode, 'LIVE_READ_ONLY');
assert.equal(envelope.source_status, 'PUBLIC_READ_ONLY');
assert.equal(envelope.integrity_status, 'VERIFIED_PUBLIC');
console.log('PASS C073-LIVE-02 C073 public envelope remains exact read-only');

assert.equal(metrics['execution-bindings-required'], 11);
assert.equal(metrics['execution-bindings-bound'], 7);
assert.equal(metrics['execution-bindings-unbound'], 4);
assert.equal(metrics['execution-bindings-complete'], false);
assert.equal(metrics['kernel-bindings-required'], 8);
assert.equal(metrics['kernel-bindings-bound'], 8);
assert.equal(metrics['kernel-bindings-complete'], true);
assert.equal(metrics['kernel-ingest-required-fields'], 5);
assert.equal(metrics['kernel-ingest-transport-dependency'], false);
assert.equal(metrics['kernel-ingest-signal-decode-performed'], false);
assert.equal(metrics['kernel-ingest-gesis-execution-performed'], false);
console.log('PASS C073-LIVE-03 inherited execution, kernel and C072 ingest states remain intact');

assert.equal(metrics['genesis003-c073'], 'VALIDATED_10_OF_10');
assert.equal(metrics['gesis-signal-decode-adapter-contract-frozen'], true);
assert.equal(metrics['gesis-signal-decode-adapter-contract-id'], 'GESIS-SIGNAL-DECODE-ADAPTER-CONTRACT-001');
assert.equal(metrics['gesis-decode-adapter-input-mode'], 'C072_EXACT_BYTES_AND_VALIDATED_DESCRIPTOR_IN_MEMORY_ONLY');
assert.equal(metrics['gesis-decode-adapter-arraybuffer-policy'], 'COPY_EXACT_BYTES_TO_NEW_ARRAYBUFFER');
assert.equal(metrics['gesis-decode-runtime-dependency'], true);
assert.equal(metrics['gesis-decode-runtime-identity-required'], true);
assert.equal(metrics['gesis-decode-cross-runtime-equivalence-proven'], false);
assert.equal(metrics['gesis-decode-signal-performed'], false);
assert.equal(metrics['gesis-decode-analysis-performed'], false);
assert.equal(metrics['gesis-decode-pcm-serialization-policy'], 'CHANNEL_MAJOR_FLOAT32_LITTLE_ENDIAN_IEEE754');
console.log('PASS C073-LIVE-04 C073 decode-adapter boundary is explicit and non-executing');

const c072 = c073ToExactC072Text(new Map(Object.entries(status.values)));
const trustedC072 = extractProgressiveGenesisStatusC072(c072);
assert.equal(trustedC072.validatedThrough, 'C072');
assert.equal(Object.keys(trustedC072.values).length, 84);
assert.equal(c072, C072);
console.log('PASS C073-LIVE-05 C073 reduces byte-exactly to trusted C072');

assert.throws(() => extractProgressiveGenesisStatusC073(c073().replace('gesis_decode_runtime_dependency=true', 'gesis_decode_runtime_dependency=false')));
assert.throws(() => extractProgressiveGenesisStatusC073(c073().replace('gesis_decode_runtime_identity_required=true', 'gesis_decode_runtime_identity_required=false')));
assert.throws(() => extractProgressiveGenesisStatusC073(c073().replace('gesis_decode_cross_runtime_equivalence_proven=false', 'gesis_decode_cross_runtime_equivalence_proven=true')));
assert.throws(() => extractProgressiveGenesisStatusC073(c073().replace('gesis_decode_signal_performed=false', 'gesis_decode_signal_performed=true')));
assert.throws(() => extractProgressiveGenesisStatusC073(c073().replace('gesis_decode_analysis_performed=false', 'gesis_decode_analysis_performed=true')));
console.log('PASS C073-LIVE-06 invalid runtime/decode/analysis claims fail closed');

for (const extra of [
  'adapter_contract_spec_digest=private',
  'gesis_commit_sha=private',
  'gesis_decoder_blob_sha=private',
  'runtime_identity_sha256=private',
  'handoff_descriptor_sha256=private',
  'decoded_pcm_sha256=private',
  'model_name=private',
]) assert.throws(() => extractProgressiveGenesisStatusC073(c073() + `${extra}\n`));
console.log('PASS C073-LIVE-07 private decoder/model evidence fields are rejected');

const serialized = JSON.stringify(envelope);
for (const token of [
  'Topbrutus/seedgenesis',
  'Topbrutus/gesis',
  '20ea3c3d77c8d934db17ae60bb3032b023dff5a6',
  'b6efdff8639264a48d269806ad6507f5e2bee5d9',
  '203f94de2824a1f904a004ce5092f5c5d423b7bd3f7264a7a08f51e7a96830ec',
  'e9bf65407aaf1072601de7c5f68a80255f4ff0a1d947bfad9cc621b13440d204',
  '14aa571228918a7665358a93cb1b0f5da8a711222f48105d3e615b01239a8283',
  '6c8256a5fcb7a11b44f519880eb792f936f44f49',
  '8b97673a2228af397fa949bf5f7921c8cdc54be4',
]) assert.equal(serialized.includes(token), false);
console.log('PASS C073-LIVE-08 public envelope contains no private C073/GESIS evidence identifiers');

assert.equal(metrics['provider-model-kernel-dependency'], false);
assert.equal(metrics['prompt-style-kernel-dependency'], false);
assert.equal(metrics['real-experiment-execution-authorized'], false);
assert.equal(metrics['gesis-decode-cross-runtime-equivalence-proven'], false);
assert.equal(metrics['gesis-decode-signal-performed'], false);
assert.equal(metrics['gesis-decode-analysis-performed'], false);
console.log('PASS C073-LIVE-09 inherited and new safety semantics remain fail-closed');

const cliStatus = '/tmp/antmux-c073-cli-status.env';
const cliInput = '/tmp/antmux-c073-cli-input.json';
writeFileSync(cliStatus, c073(), 'utf8');
const buildCli = spawnSync(process.execPath, ['laboratoire/genesis/live-v2/build-public-source-progressive-c073.mjs', cliStatus, cliInput], {
  encoding: 'utf8',
  env: { ...process.env, GENESIS_PUBLIC_LIVE_ACTIVE: '1' },
});
assert.equal(buildCli.status, 0, buildCli.stderr || buildCli.stdout);
assert.equal(existsSync(cliInput), true);
const bridgeCli = spawnSync(process.execPath, ['laboratoire/genesis/live-v2/bridge-public-progressive-c073.mjs', cliInput], { encoding: 'utf8' });
assert.equal(bridgeCli.status, 0, bridgeCli.stderr || bridgeCli.stdout);
const cliEnvelope = JSON.parse(readFileSync('.build/genesis-public-read-only-bridge/public-read-only-envelope.json', 'utf8'));
assert.equal(cliEnvelope.payload.metrics.find((entry) => entry.id === 'genesis003-validated-through')?.value, 'C073');
assert.equal(cliEnvelope.payload.metrics.find((entry) => entry.id === 'gesis-decode-signal-performed')?.value, false);
assert.equal(cliEnvelope.mode, 'LIVE_READ_ONLY');
console.log('PASS C073-LIVE-10 C073 runtime CLI smoke');
console.log('GENESIS_PROGRESSIVE_LIVE_C073_DECODE_ADAPTER_TESTS=10/10');
console.log('C073_RUNTIME_CLI_SMOKE=PASS');
