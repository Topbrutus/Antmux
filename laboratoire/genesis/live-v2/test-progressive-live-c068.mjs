#!/usr/bin/env node
import assert from 'node:assert/strict';
import { extractProgressiveGenesisStatusC068, buildProgressiveBridgeInputC068 } from './build-public-source-progressive-c068.mjs';
import { buildProgressivePublicEnvelopeC068 } from './bridge-public-progressive-c068.mjs';

const C067=`science_baseline=GREEN
genesis003_c041_c060=COMPLETE_VALIDATED
experiment_selection_performed=true
selected_experiment_status=PLANNED_NOT_EXECUTED
hypothesis_selection_performed=false
hypothesis_ranking_produced=false
uncertainty_promotion_performed=false
probabilities_produced=false
evidence_ledger_auto_promotion=false
GENESIS_AUDIT_FAILED=0
genesis003_validated_through=C067
genesis003_c061=VALIDATED_10_OF_10
c061_execution_input=SYNTHETIC_C060_FIXTURE
execution_admissibility=BLOCKED_INCOMPLETE_REAL_EXECUTION_CONTRACT
next_scientific_action=SELECT_REAL_GENERATOR_PROVIDER_MODEL_BUILD
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
execution_bindings_bound=3
execution_bindings_complete=false
genesis003_c064=VALIDATED_10_OF_10
real_execution_contract_id=REAL-EXECUTION-CONTRACT-001
real_execution_contract_status=PARTIALLY_BOUND_BLOCKED
execution_bindings_unbound=8
generator_seed_policy_bound=true
gesis_primary_profile_compatible=false
gesis_observed_candidate_recorded=true
genesis003_c065=VALIDATED_10_OF_10
gesis_neutral_path_compatible=true
default_az_profile_still_incompatible=true
analysis_decision_rule_bound=false
genesis003_c066=VALIDATED_10_OF_10
binding_dependency_audit=COMPLETE_NO_NEW_PROVEN_BINDINGS
new_bindings_proven=0
generator_execution_profile_frozen=false
genesis003_c067=VALIDATED_10_OF_10
control_generator_profile=FROZEN_VALIDATED_CONTROL_ONLY
control_generator_deterministic=true
real_generator_bindings_added=0
real_generator_profile_frozen=false
`;
function c068(){return C067
 .replace('genesis003_validated_through=C067','genesis003_validated_through=C068')
 .replace('next_scientific_action=SELECT_REAL_GENERATOR_PROVIDER_MODEL_BUILD','next_scientific_action=FREEZE_REAL_GENERATION_REQUEST_PROFILE')
 .replace('execution_bindings_bound=3','execution_bindings_bound=6')
 .replace('execution_bindings_unbound=8','execution_bindings_unbound=5')
 .replace('real_generator_bindings_added=0','real_generator_bindings_added=3')+
 `genesis003_c068=VALIDATED_10_OF_10\nreal_generator_identity_frozen=true\nruntime_compatibility_verified=false\nlanguage_coverage_verified=false\nlanguage_confound_registered=true\n`;}
function mustFail(text,needle){assert.throws(()=>extractProgressiveGenesisStatusC068(text),e=>e instanceof Error&&e.message.includes(needle));}

const legacy=extractProgressiveGenesisStatusC068(C067);assert.equal(legacy.validatedThrough,'C067');console.log('PASS 01 exact C067 remains accepted');
const status=extractProgressiveGenesisStatusC068(c068());assert.equal(status.validatedThrough,'C068');
const input=buildProgressiveBridgeInputC068(status,{now:'2026-09-04T06:00:00Z',liveActive:true});
const {envelope}=buildProgressivePublicEnvelopeC068(input,{now:'2026-09-04T06:00:00Z'});
const metrics=Object.fromEntries(envelope.payload.metrics.map(x=>[x.id,x.value]));
assert.equal(metrics['genesis003-validated-through'],'C068');assert.equal(metrics['execution-bindings-bound'],6);assert.equal(metrics['execution-bindings-unbound'],5);assert.equal(metrics['real-generator-bindings-added'],3);assert.equal(metrics['real-generator-identity-frozen'],true);assert.equal(metrics['runtime-compatibility-verified'],false);assert.equal(metrics['language-coverage-verified'],false);assert.equal(metrics['language-confound-registered'],true);assert.equal(metrics['bridge-write-capability'],'NONE');console.log('PASS 02 exact C068 becomes read-only public envelope');
mustFail(c068().replace('execution_bindings_bound=6','execution_bindings_bound=7'),'Comptage bindings');console.log('PASS 03 wrong binding count rejected');
mustFail(c068().replace('runtime_compatibility_verified=false','runtime_compatibility_verified=true'),'runtime_compatibility_verified');console.log('PASS 04 invented runtime compatibility rejected');
mustFail(c068().replace('language_coverage_verified=false','language_coverage_verified=true'),'language_coverage_verified');console.log('PASS 05 invented language coverage rejected');
mustFail(c068()+`model_name=MiniMaxAI/MiniMax-Music3\n`,'56 lignes');console.log('PASS 06 private model leakage rejected');
mustFail(c068()+`generator_provider=LOCAL_HUGGINGFACE_DIFFUSERS\n`,'56 lignes');console.log('PASS 07 private provider leakage rejected');
mustFail(c068().replace('language_confound_registered=true','language_confound_registered=false'),'language_confound_registered');console.log('PASS 08 removed language confound rejected');
const serialized=JSON.stringify(envelope);for(const forbidden of ['MiniMaxAI/MiniMax-Music3','LOCAL_HUGGINGFACE_DIFFUSERS','fbdf52fbaaca799592917417eb05f1899f1255ec','dafe3733fcfdbf3c48915fe77be3aef65b5d6a2d'])assert.equal(serialized.includes(forbidden),false);console.log('PASS 09 envelope contains no private generator identity');
assert.equal(envelope.mode,'LIVE_READ_ONLY');assert.equal(envelope.source_status,'PUBLIC_READ_ONLY');assert.equal(envelope.integrity_status,'VERIFIED_PUBLIC');console.log('PASS 10 public boundary remains fail-closed read-only');
console.log('GENESIS_PROGRESSIVE_LIVE_C068_TESTS=10/10');

// Extend the already-authorized progressive PR suite without adding or changing workflow permissions.
await import('./test-progressive-live-c069-c070-signal.mjs');
await import('./test-progressive-live-c071-kernel.mjs');
