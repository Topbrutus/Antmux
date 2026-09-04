#!/usr/bin/env node
import assert from 'node:assert/strict';
import { extractProgressiveGenesisStatusC069, buildProgressiveBridgeInputC069 } from './build-public-source-progressive-c069.mjs';
import { buildProgressivePublicEnvelopeC069 } from './bridge-public-progressive-c069.mjs';

const C068=`science_baseline=GREEN
genesis003_c041_c060=COMPLETE_VALIDATED
experiment_selection_performed=true
selected_experiment_status=PLANNED_NOT_EXECUTED
hypothesis_selection_performed=false
hypothesis_ranking_produced=false
uncertainty_promotion_performed=false
probabilities_produced=false
evidence_ledger_auto_promotion=false
GENESIS_AUDIT_FAILED=0
genesis003_validated_through=C068
genesis003_c061=VALIDATED_10_OF_10
c061_execution_input=SYNTHETIC_C060_FIXTURE
execution_admissibility=BLOCKED_INCOMPLETE_REAL_EXECUTION_CONTRACT
next_scientific_action=FREEZE_REAL_GENERATION_REQUEST_PROFILE
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
execution_bindings_bound=6
execution_bindings_complete=false
genesis003_c064=VALIDATED_10_OF_10
real_execution_contract_id=REAL-EXECUTION-CONTRACT-001
real_execution_contract_status=PARTIALLY_BOUND_BLOCKED
execution_bindings_unbound=5
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
real_generator_bindings_added=3
real_generator_profile_frozen=false
genesis003_c068=VALIDATED_10_OF_10
real_generator_identity_frozen=true
runtime_compatibility_verified=false
language_coverage_verified=false
language_confound_registered=true
`;
function c069(){return C068
 .replace('genesis003_validated_through=C068','genesis003_validated_through=C069')
 .replace('next_scientific_action=FREEZE_REAL_GENERATION_REQUEST_PROFILE','next_scientific_action=FREEZE_ANALYSIS_THRESHOLDS_AND_DECISION_RULE')
 .replace('execution_bindings_bound=6','execution_bindings_bound=10')
 .replace('execution_bindings_unbound=5','execution_bindings_unbound=1')+
 `genesis003_c069=VALIDATED_10_OF_10\nreal_generation_request_profile_frozen=true\nprompt_hashes_frozen=true\nstyle_structure_template_frozen=true\nduration_export_profile_frozen=true\nreal_request_bindings_added=4\ntranslation_equivalence_verified=false\nrequest_profile_only=true\n`;}
function mustFail(text,needle){assert.throws(()=>extractProgressiveGenesisStatusC069(text),e=>e instanceof Error&&e.message.includes(needle));}

const legacy=extractProgressiveGenesisStatusC069(C068);assert.equal(legacy.validatedThrough,'C068');console.log('PASS 01 exact C068 remains accepted');
const status=extractProgressiveGenesisStatusC069(c069());assert.equal(status.validatedThrough,'C069');
const input=buildProgressiveBridgeInputC069(status,{now:'2026-09-04T07:00:00Z',liveActive:true});
const {envelope}=buildProgressivePublicEnvelopeC069(input,{now:'2026-09-04T07:00:00Z'});
const metrics=Object.fromEntries(envelope.payload.metrics.map(x=>[x.id,x.value]));
assert.equal(metrics['genesis003-validated-through'],'C069');assert.equal(metrics['execution-bindings-bound'],10);assert.equal(metrics['execution-bindings-unbound'],1);assert.equal(metrics['real-generation-request-profile-frozen'],true);assert.equal(metrics['real-request-bindings-added'],4);assert.equal(metrics['translation-equivalence-verified'],false);assert.equal(metrics['request-profile-only'],true);assert.equal(metrics['analysis-decision-rule-bound'],false);assert.equal(metrics['bridge-write-capability'],'NONE');console.log('PASS 02 exact C069 becomes read-only public envelope');
mustFail(c069().replace('execution_bindings_bound=10','execution_bindings_bound=11'),'Comptage bindings');console.log('PASS 03 premature complete binding count rejected');
mustFail(c069().replace('analysis_decision_rule_bound=false','analysis_decision_rule_bound=true'),'analysis_decision_rule_bound');console.log('PASS 04 invented analysis decision binding rejected');
mustFail(c069().replace('translation_equivalence_verified=false','translation_equivalence_verified=true'),'translation_equivalence_verified');console.log('PASS 05 invented translation equivalence rejected');
mustFail(c069()+`target_duration_seconds=60\n`,'64 lignes');console.log('PASS 06 private duration leakage rejected');
mustFail(c069()+`audio_export_format=WAV_PCM16_LE_44100HZ_STEREO\n`,'64 lignes');console.log('PASS 07 private export leakage rejected');
mustFail(c069()+`prompt_hash=78f850157a54a099dc0f20009b5a4865d5b16e32b8c3eaf3ee3b63237460e7ff\n`,'64 lignes');console.log('PASS 08 private prompt hash leakage rejected');
const serialized=JSON.stringify(envelope);for(const forbidden of ['MiniMaxAI/MiniMax-Music3','LOCAL_HUGGINGFACE_DIFFUSERS','WAV_PCM16_LE_44100HZ_STEREO','78f850157a54a099dc0f20009b5a4865d5b16e32b8c3eaf3ee3b63237460e7ff','97eac2e27fa1e47065e15c2e69143226f4248cae0623f3b6f723b9356c811a5c'])assert.equal(serialized.includes(forbidden),false);console.log('PASS 09 envelope contains no private C069 request evidence');
assert.equal(envelope.mode,'LIVE_READ_ONLY');assert.equal(envelope.source_status,'PUBLIC_READ_ONLY');assert.equal(envelope.integrity_status,'VERIFIED_PUBLIC');console.log('PASS 10 public boundary remains fail-closed read-only');
console.log('GENESIS_PROGRESSIVE_LIVE_C069_TESTS=10/10');
