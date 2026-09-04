#!/usr/bin/env node
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import {
  extractProgressiveGenesisStatusC072,
  buildProgressiveBridgeInputC072,
  c072ToExactC071Text,
} from './build-public-source-progressive-c072.mjs';
import { extractProgressiveGenesisStatusC071 } from './build-public-source-progressive-c071.mjs';
import { buildProgressivePublicEnvelopeC072 } from './bridge-public-progressive-c072.mjs';

const C071 = `science_baseline=GREEN
genesis003_c041_c060=COMPLETE_VALIDATED
experiment_selection_performed=true
selected_experiment_status=PLANNED_NOT_EXECUTED
hypothesis_selection_performed=false
hypothesis_ranking_produced=false
uncertainty_promotion_performed=false
probabilities_produced=false
evidence_ledger_auto_promotion=false
GENESIS_AUDIT_FAILED=0
genesis003_validated_through=C071
genesis003_c061=VALIDATED_10_OF_10
c061_execution_input=SYNTHETIC_C060_FIXTURE
execution_admissibility=BLOCKED_INCOMPLETE_REAL_EXECUTION_CONTRACT
next_scientific_action=DEFINE_KERNEL_NEUTRAL_SIGNAL_INGEST_INTERFACE
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
`;

function c072() {
  return C071
    .replace('genesis003_validated_through=C071', 'genesis003_validated_through=C072')
    .replace('next_scientific_action=DEFINE_KERNEL_NEUTRAL_SIGNAL_INGEST_INTERFACE', 'next_scientific_action=DEFINE_GESIS_SIGNAL_DECODE_ADAPTER_CONTRACT') +
`genesis003_c072=VALIDATED_10_OF_10
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
}

const status = extractProgressiveGenesisStatusC072(c072());
assert.equal(status.validatedThrough, 'C072');
assert.equal(Object.keys(status.values).length, 84);
console.log('PASS C072-LIVE-01 exact 84-line C072 projection accepted');

const input = buildProgressiveBridgeInputC072(status, { now: '2026-09-04T12:20:00Z', liveActive: true });
const envelope = buildProgressivePublicEnvelopeC072(input, { now: '2026-09-04T12:20:00Z' }).envelope;
const metrics = Object.fromEntries(envelope.payload.metrics.map((entry) => [entry.id, entry.value]));
assert.equal(metrics['genesis003-validated-through'], 'C072');
assert.equal(metrics['next-scientific-action'], 'DEFINE_GESIS_SIGNAL_DECODE_ADAPTER_CONTRACT');
assert.equal(metrics['bridge-write-capability'], 'NONE');
console.log('PASS C072-LIVE-02 C072 public envelope remains read-only');

assert.equal(metrics['execution-bindings-required'], 11);
assert.equal(metrics['execution-bindings-bound'], 7);
assert.equal(metrics['execution-bindings-unbound'], 4);
assert.equal(metrics['execution-bindings-complete'], false);
assert.equal(metrics['kernel-bindings-required'], 8);
assert.equal(metrics['kernel-bindings-bound'], 8);
assert.equal(metrics['kernel-bindings-complete'], true);
console.log('PASS C072-LIVE-03 historical execution and C071 kernel state remain distinct');

assert.equal(metrics['kernel-signal-ingest-interface-frozen'], true);
assert.equal(metrics['kernel-signal-ingest-interface-id'], 'KERNEL-SIGNAL-INGEST-INTERFACE-001');
assert.equal(metrics['kernel-ingest-input-mode'], 'EXACT_BYTES_IN_MEMORY_ONLY');
assert.equal(metrics['kernel-ingest-required-fields'], 5);
assert.equal(metrics['kernel-ingest-unknown-fields-allowed'], false);
assert.equal(metrics['kernel-ingest-content-addressed'], true);
assert.equal(metrics['kernel-ingest-provenance-addressed'], true);
assert.equal(metrics['kernel-ingest-transport-dependency'], false);
assert.equal(metrics['kernel-ingest-signal-decode-performed'], false);
assert.equal(metrics['kernel-ingest-gesis-execution-performed'], false);
console.log('PASS C072-LIVE-04 C072 neutral ingest boundary is explicit');

const c071 = c072ToExactC071Text(new Map(Object.entries(status.values)));
assert.equal(extractProgressiveGenesisStatusC071(c071).validatedThrough, 'C071');
console.log('PASS C072-LIVE-05 C072 reduces exactly to trusted C071');

assert.throws(() => extractProgressiveGenesisStatusC072(c072().replace('kernel_ingest_required_fields=5', 'kernel_ingest_required_fields=6')));
assert.throws(() => extractProgressiveGenesisStatusC072(c072().replace('kernel_ingest_transport_dependency=false', 'kernel_ingest_transport_dependency=true')));
assert.throws(() => extractProgressiveGenesisStatusC072(c072().replace('kernel_ingest_gesis_execution_performed=false', 'kernel_ingest_gesis_execution_performed=true')));
console.log('PASS C072-LIVE-06 invalid ingest state fails closed');

for (const extra of [
  'interface_spec_digest=private',
  'signal_sha256=private',
  'provenance_sha256=private',
  'model_name=private',
]) assert.throws(() => extractProgressiveGenesisStatusC072(c072() + `${extra}\n`));
console.log('PASS C072-LIVE-07 private ingest/model fields are rejected');

const serialized = JSON.stringify(envelope);
for (const token of [
  'Topbrutus/seedgenesis',
  'Topbrutus/gesis',
  '3910ba8431504196c02d3b1550b50fc51166aa8b',
  'e49962faf07627c9ca35cf292ec17336933c95c3',
  'a2d9685f6437ebc3d42fd8bc893e40d649bf817b7c4b2bc37bdc4093c304f28a',
  'dae4c8995ea19d51a4acc354bd97d882e28ba9fdb8217ea7779368562c6cc4eb',
  '6c8256a5fcb7a11b44f519880eb792f936f44f49',
]) assert.equal(serialized.includes(token), false);
console.log('PASS C072-LIVE-08 public envelope contains no private C072 evidence identifiers');

assert.equal(envelope.mode, 'LIVE_READ_ONLY');
assert.equal(envelope.source_status, 'PUBLIC_READ_ONLY');
assert.equal(envelope.integrity_status, 'VERIFIED_PUBLIC');
assert.equal(metrics['provider-model-kernel-dependency'], false);
assert.equal(metrics['prompt-style-kernel-dependency'], false);
assert.equal(metrics['real-experiment-execution-authorized'], false);
console.log('PASS C072-LIVE-09 inherited public safety semantics remain intact');

const cliStatus = '/tmp/antmux-c072-cli-status.env';
const cliInput = '/tmp/antmux-c072-cli-input.json';
writeFileSync(cliStatus, c072(), 'utf8');
const buildCli = spawnSync(process.execPath, ['laboratoire/genesis/live-v2/build-public-source-progressive-c072.mjs', cliStatus, cliInput], {
  encoding: 'utf8',
  env: { ...process.env, GENESIS_PUBLIC_LIVE_ACTIVE: '1' },
});
assert.equal(buildCli.status, 0, buildCli.stderr || buildCli.stdout);
assert.equal(existsSync(cliInput), true);
const bridgeCli = spawnSync(process.execPath, ['laboratoire/genesis/live-v2/bridge-public-progressive-c072.mjs', cliInput], { encoding: 'utf8' });
assert.equal(bridgeCli.status, 0, bridgeCli.stderr || bridgeCli.stdout);
const cliEnvelope = JSON.parse(readFileSync('.build/genesis-public-read-only-bridge/public-read-only-envelope.json', 'utf8'));
assert.equal(cliEnvelope.payload.metrics.find((entry) => entry.id === 'genesis003-validated-through')?.value, 'C072');
assert.equal(cliEnvelope.mode, 'LIVE_READ_ONLY');
console.log('PASS C072-LIVE-10 C072 runtime CLI smoke');
console.log('GENESIS_PROGRESSIVE_LIVE_C072_INGEST_TESTS=10/10');
console.log('C072_RUNTIME_CLI_SMOKE=PASS');
