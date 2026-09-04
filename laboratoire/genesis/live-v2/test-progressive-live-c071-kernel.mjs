#!/usr/bin/env node
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import {
  extractProgressiveGenesisStatusC071,
  buildProgressiveBridgeInputC071,
  c071ToExactC070Text,
} from './build-public-source-progressive-c071.mjs';
import { extractProgressiveGenesisStatusC070 } from './build-public-source-progressive-c070.mjs';
import { buildProgressivePublicEnvelopeC071 } from './bridge-public-progressive-c071.mjs';

const C070 = `science_baseline=GREEN
genesis003_c041_c060=COMPLETE_VALIDATED
experiment_selection_performed=true
selected_experiment_status=PLANNED_NOT_EXECUTED
hypothesis_selection_performed=false
hypothesis_ranking_produced=false
uncertainty_promotion_performed=false
probabilities_produced=false
evidence_ledger_auto_promotion=false
GENESIS_AUDIT_FAILED=0
genesis003_validated_through=C070
genesis003_c061=VALIDATED_10_OF_10
c061_execution_input=SYNTHETIC_C060_FIXTURE
execution_admissibility=BLOCKED_INCOMPLETE_REAL_EXECUTION_CONTRACT
next_scientific_action=FREEZE_REMAINING_GENERATION_IO_BINDINGS
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
`;

function c071() {
  return C070
    .replace('genesis003_validated_through=C070', 'genesis003_validated_through=C071')
    .replace('next_scientific_action=FREEZE_REMAINING_GENERATION_IO_BINDINGS', 'next_scientific_action=DEFINE_KERNEL_NEUTRAL_SIGNAL_INGEST_INTERFACE') +
`genesis003_c071=VALIDATED_10_OF_10
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
}

const status = extractProgressiveGenesisStatusC071(c071());
assert.equal(status.validatedThrough, 'C071');
assert.equal(Object.keys(status.values).length, 73);
console.log('PASS C071-LIVE-01 exact 73-line C071 projection accepted');

const input = buildProgressiveBridgeInputC071(status, { now: '2026-09-04T11:00:00Z', liveActive: true });
const envelope = buildProgressivePublicEnvelopeC071(input, { now: '2026-09-04T11:00:00Z' }).envelope;
const metrics = Object.fromEntries(envelope.payload.metrics.map((entry) => [entry.id, entry.value]));
assert.equal(metrics['genesis003-validated-through'], 'C071');
assert.equal(metrics['next-scientific-action'], 'DEFINE_KERNEL_NEUTRAL_SIGNAL_INGEST_INTERFACE');
assert.equal(metrics['bridge-write-capability'], 'NONE');
console.log('PASS C071-LIVE-02 C071 public envelope remains read-only');

assert.equal(metrics['execution-bindings-bound'], 7);
assert.equal(metrics['execution-bindings-unbound'], 4);
assert.equal(metrics['kernel-bindings-required'], 8);
assert.equal(metrics['kernel-bindings-bound'], 8);
assert.equal(metrics['kernel-bindings-complete'], true);
console.log('PASS C071-LIVE-03 historical execution bindings and kernel bindings remain distinct');

assert.equal(metrics['kernel-source-of-truth'], 'SIGNAL_AND_MEASUREMENT_PROVENANCE');
assert.equal(metrics['external-generation-metadata-required-by-kernel'], false);
assert.equal(metrics['prompt-style-kernel-dependency'], false);
assert.equal(metrics['real-experiment-execution-authorized'], false);
assert.equal(metrics['historical-execution-contract-policy'], 'IMMUTABLE_HISTORY_NOT_KERNEL_SOURCE_OF_TRUTH');
console.log('PASS C071-LIVE-04 kernel-neutral boundary is explicit');

const c070 = c071ToExactC070Text(new Map(Object.entries(status.values)));
assert.equal(extractProgressiveGenesisStatusC070(c070).validatedThrough, 'C070');
console.log('PASS C071-LIVE-05 C071 reduces exactly to trusted C070');

assert.throws(() => extractProgressiveGenesisStatusC071(c071().replace('kernel_bindings_bound=8', 'kernel_bindings_bound=7')));
assert.throws(() => extractProgressiveGenesisStatusC071(c071().replace('external_generation_metadata_required_by_kernel=false', 'external_generation_metadata_required_by_kernel=true')));
console.log('PASS C071-LIVE-06 invalid kernel state fails closed');

assert.throws(() => extractProgressiveGenesisStatusC071(c071() + 'signal_sha256=private\n'));
assert.throws(() => extractProgressiveGenesisStatusC071(c071() + 'model_name=private\n'));
console.log('PASS C071-LIVE-07 private signal/model fields are rejected');

const serialized = JSON.stringify(envelope);
for (const token of [
  'Topbrutus/seedgenesis',
  'Topbrutus/gesis',
  'a5acd442d9a851496c9f3bdc706b6f408e4fd92a03cff83c663b85e6b583a0e4',
  '932c41a38dc8cce2e7cccee436f26a200d269c058e69e5de9ec09105013407aa',
  '6c8256a5fcb7a11b44f519880eb792f936f44f49',
]) assert.equal(serialized.includes(token), false);
console.log('PASS C071-LIVE-08 public envelope contains no private evidence identifiers');

assert.equal(envelope.mode, 'LIVE_READ_ONLY');
assert.equal(envelope.source_status, 'PUBLIC_READ_ONLY');
assert.equal(envelope.integrity_status, 'VERIFIED_PUBLIC');
assert.equal(metrics['provider-model-kernel-dependency'], false);
console.log('PASS C071-LIVE-09 inherited public safety semantics remain intact');

const cliStatus = '/tmp/antmux-c071-cli-status.env';
const cliInput = '/tmp/antmux-c071-cli-input.json';
writeFileSync(cliStatus, c071(), 'utf8');
const buildCli = spawnSync(process.execPath, ['laboratoire/genesis/live-v2/build-public-source-progressive-c071.mjs', cliStatus, cliInput], {
  encoding: 'utf8',
  env: { ...process.env, GENESIS_PUBLIC_LIVE_ACTIVE: '1' },
});
assert.equal(buildCli.status, 0, buildCli.stderr || buildCli.stdout);
assert.equal(existsSync(cliInput), true);
const bridgeCli = spawnSync(process.execPath, ['laboratoire/genesis/live-v2/bridge-public-progressive-c071.mjs', cliInput], { encoding: 'utf8' });
assert.equal(bridgeCli.status, 0, bridgeCli.stderr || bridgeCli.stdout);
const cliEnvelope = JSON.parse(readFileSync('.build/genesis-public-read-only-bridge/public-read-only-envelope.json', 'utf8'));
assert.equal(cliEnvelope.payload.metrics.find((entry) => entry.id === 'genesis003-validated-through')?.value, 'C071');
assert.equal(cliEnvelope.mode, 'LIVE_READ_ONLY');
console.log('PASS C071-LIVE-10 C071 runtime CLI smoke');
console.log('GENESIS_PROGRESSIVE_LIVE_C071_KERNEL_TESTS=10/10');
console.log('C071_RUNTIME_CLI_SMOKE=PASS');
