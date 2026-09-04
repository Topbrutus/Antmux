#!/usr/bin/env node
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const LEGACY=Object.freeze({
  science_baseline:'GREEN',genesis003_c041_c060:'COMPLETE_VALIDATED',experiment_selection_performed:'true',selected_experiment_status:'PLANNED_NOT_EXECUTED',hypothesis_selection_performed:'false',hypothesis_ranking_produced:'false',uncertainty_promotion_performed:'false',probabilities_produced:'false',evidence_ledger_auto_promotion:'false',GENESIS_AUDIT_FAILED:'0',
});
const C061=Object.freeze({...LEGACY,genesis003_validated_through:'C061',genesis003_c061:'VALIDATED_10_OF_10',c061_execution_input:'SYNTHETIC_C060_FIXTURE',execution_admissibility:'BLOCKED_SYNTHETIC_SELECTION',next_scientific_action:'AWAIT_REAL_EXPERIMENT_SPEC'});
const C062=Object.freeze({...C061,genesis003_validated_through:'C062',next_scientific_action:'BUILD_REAL_NEXT_TEST_PLAN',genesis003_c062:'VALIDATED_10_OF_10',real_experiment_spec_id:'REAL-EXPERIMENT-SPEC-001',real_experiment_spec_status:'FROZEN_CANDIDATE_NOT_SELECTED',real_experiment_family:'BLIND_MULTILINGUAL_GESIS_COMPARISON',trial_class:'PILOT_COMPARATIVE_NOT_CONFIRMATORY',replicates_per_arm:'3',blinded_primary_analysis:'true',pretargeted_symbolic_search:'false',real_plan_selection_performed:'false'});
const C063=Object.freeze({...C062,genesis003_validated_through:'C063',execution_admissibility:'BLOCKED_MISSING_EXECUTION_BINDINGS',next_scientific_action:'BIND_REAL_EXECUTION_CONTRACT',real_plan_selection_performed:'true',genesis003_c063:'VALIDATED_10_OF_10',real_next_test_plan_id:'REAL-NEXT-TEST-PLAN-001',real_next_test_plan_status:'FROZEN_PLAN_AWAITING_EXECUTION_BINDINGS',sample_count:'12',execution_bindings_required:'11',execution_bindings_bound:'0',execution_bindings_complete:'false'});
const C064=Object.freeze({...C063,genesis003_validated_through:'C064',execution_admissibility:'BLOCKED_INCOMPLETE_REAL_EXECUTION_CONTRACT',next_scientific_action:'RESOLVE_REMAINING_EXECUTION_BINDINGS',execution_bindings_bound:'1',genesis003_c064:'VALIDATED_10_OF_10',real_execution_contract_id:'REAL-EXECUTION-CONTRACT-001',real_execution_contract_status:'PARTIALLY_BOUND_BLOCKED',execution_bindings_unbound:'10',generator_seed_policy_bound:'true',gesis_primary_profile_compatible:'false',gesis_observed_candidate_recorded:'true'});
const C065=Object.freeze({...C064,genesis003_validated_through:'C065',execution_bindings_bound:'3',execution_bindings_unbound:'8',genesis003_c065:'VALIDATED_10_OF_10',gesis_neutral_path_compatible:'true',default_az_profile_still_incompatible:'true',analysis_decision_rule_bound:'false'});
const C066=Object.freeze({...C065,genesis003_validated_through:'C066',next_scientific_action:'FREEZE_GENERATOR_EXECUTION_PROFILE',genesis003_c066:'VALIDATED_10_OF_10',binding_dependency_audit:'COMPLETE_NO_NEW_PROVEN_BINDINGS',new_bindings_proven:'0',generator_execution_profile_frozen:'false'});
const C067=Object.freeze({...C066,genesis003_validated_through:'C067',next_scientific_action:'SELECT_REAL_GENERATOR_PROVIDER_MODEL_BUILD',genesis003_c067:'VALIDATED_10_OF_10',control_generator_profile:'FROZEN_VALIDATED_CONTROL_ONLY',control_generator_deterministic:'true',real_generator_bindings_added:'0',real_generator_profile_frozen:'false'});

const EXPECTED=Object.freeze({C060:LEGACY,C061,C062,C063,C064,C065,C066,C067});
const STAGES=Object.freeze(Object.keys(EXPECTED));
const SOURCE_STATE=Object.freeze(Object.fromEntries(STAGES.map(stage=>[stage,`C041_${stage}_COMPLETE_VALIDATED`])));

function fail(message){throw new Error(message);}
function parse(text){
  if(typeof text!=='string'||!text.length)fail('Source Genesis absente.');
  const found=new Map();
  for(const raw of text.split(/\r?\n/)){
    if(!raw)continue;
    const m=raw.match(/^([A-Za-z0-9_]+)=(.*)$/);if(!m)fail(`Ligne de statut invalide: ${raw}.`);
    const[,key,value]=m;if(found.has(key))fail(`Clé dupliquée: ${key}.`);found.set(key,value);
  }
  return found;
}
function exact(found,expected){const keys=Object.keys(expected);return found.size===keys.length&&keys.every(k=>found.get(k)===expected[k]);}
function asBool(found,key){const v=found.get(key);if(v===undefined)return null;if(v==='true')return true;if(v==='false')return false;fail(`${key} doit être booléen.`);}
function asNumber(found,key){const v=found.get(key);if(v===undefined)return null;const n=Number(v);if(!Number.isFinite(n))fail(`${key} doit être numérique.`);return n;}

export function extractProgressiveGenesisStatusC067(text){
  const found=parse(text);
  let stage=null;
  for(const candidate of STAGES)if(exact(found,EXPECTED[candidate])){stage=candidate;break;}
  if(!stage)fail(`Statut Genesis non autorisé par le contrat progressif C067; keys=${[...found.keys()].sort().join(',')}.`);
  return{schema:'GENESIS_PUBLIC_PROGRESSIVE_STATUS_V3',validatedThrough:stage,values:Object.freeze(Object.fromEntries(found))};
}

export function buildProgressiveBridgeInputC067(status,options={}){
  if(status?.schema!=='GENESIS_PUBLIC_PROGRESSIVE_STATUS_V3'||!STAGES.includes(status.validatedThrough))fail('Statut progressif C067 invalide.');
  const found=new Map(Object.entries(status.values??{}));
  if(!exact(found,EXPECTED[status.validatedThrough]))fail('Statut progressif C067 muté après validation.');
  const now=new Date(options.now??Date.now());if(Number.isNaN(now.getTime()))fail('Horodatage invalide.');
  const liveActive=options.liveActive!==false;
  const v=status.values;
  return{
    bridge_input_version:'3.0.0',publication_intent:'SERVER_SIDE_PUBLIC_READ_ONLY_PROGRESSIVE_BRIDGE_C067',bridge_received_at:now.toISOString(),source_observed_at:now.toISOString(),max_age_seconds:300,
    source_attestation:{source_kind:'PRIVATE_GENESIS_PUBLIC_PROJECTION',source_identity:'OPAQUE_PUBLIC_ATTESTATION',source_state:SOURCE_STATE[status.validatedThrough],validated_through:status.validatedThrough,public_status:v,read_capability:'READ_ONLY',write_capability:'NONE',adapter_only:true},
    transport:{server_side_pull:true,public_endpoint_only:true,fail_closed:true,snapshot_fallback_available:true,browser_credentials_present:false,private_browser_request:false},live_active:liveActive,
  };
}

export function publicValue(input,key,fallback=null){const v=input?.source_attestation?.public_status?.[key];return v===undefined?fallback:v;}
export function publicBool(input,key){const v=publicValue(input,key,null);if(v===null)return null;if(v==='true')return true;if(v==='false')return false;fail(`${key} doit être booléen.`);}
export function publicNumber(input,key){const v=publicValue(input,key,null);if(v===null)return null;const n=Number(v);if(!Number.isFinite(n))fail(`${key} doit être numérique.`);return n;}
export function assertProgressiveBridgeInputC067(input){
  if(!input||typeof input!=='object'||Array.isArray(input))fail('Bridge input C067 invalide.');
  if(input.bridge_input_version!=='3.0.0'||input.publication_intent!=='SERVER_SIDE_PUBLIC_READ_ONLY_PROGRESSIVE_BRIDGE_C067')fail('Version/intention bridge C067 invalide.');
  const a=input.source_attestation;if(!a||typeof a!=='object'||Array.isArray(a))fail('Attestation absente.');
  if(!STAGES.includes(a.validated_through)||a.source_state!==SOURCE_STATE[a.validated_through])fail('Stage/source_state C067 invalide.');
  if(a.source_kind!=='PRIVATE_GENESIS_PUBLIC_PROJECTION'||a.source_identity!=='OPAQUE_PUBLIC_ATTESTATION'||a.read_capability!=='READ_ONLY'||a.write_capability!=='NONE'||a.adapter_only!==true)fail('Frontière source C067 invalide.');
  const found=new Map(Object.entries(a.public_status??{}));if(!exact(found,EXPECTED[a.validated_through]))fail('Projection source C067 non exacte.');
  const t=input.transport;if(!t||t.server_side_pull!==true||t.public_endpoint_only!==true||t.fail_closed!==true||t.snapshot_fallback_available!==true||t.browser_credentials_present!==false||t.private_browser_request!==false)fail('Transport C067 invalide.');
  if(typeof input.live_active!=='boolean'||!Number.isInteger(input.max_age_seconds)||input.max_age_seconds<30||input.max_age_seconds>900)fail('Paramètres bridge C067 invalides.');
  return true;
}

async function main(){
  const sourcePath=process.argv[2];if(!sourcePath)fail('Usage: build-public-source-progressive-c067.mjs <status.env> [output.json]');
  const outputPath=process.argv[3]??'.build/genesis-progressive-live/bridge-input.json';
  const source=await readFile(path.resolve(sourcePath),'utf8');const status=extractProgressiveGenesisStatusC067(source);
  const flag=process.env.GENESIS_PUBLIC_LIVE_ACTIVE??'1';if(!['0','1'].includes(flag))fail('GENESIS_PUBLIC_LIVE_ACTIVE doit être 0 ou 1.');
  const input=buildProgressiveBridgeInputC067(status,{liveActive:flag==='1'});const resolved=path.resolve(outputPath);await mkdir(path.dirname(resolved),{recursive:true});await writeFile(resolved,`${JSON.stringify(input,null,2)}\n`,'utf8');
  console.log('GENESIS_PROGRESSIVE_C067_PRIVATE_SOURCE_VALID');console.log(JSON.stringify({validated_through:status.validatedThrough,execution_admissibility:publicValue(input,'execution_admissibility','NOT_APPLICABLE'),next_scientific_action:publicValue(input,'next_scientific_action','AWAIT_EXPLICIT_NEW_PHASE'),real_generator_profile_frozen:publicBool(input,'real_generator_profile_frozen'),private_identifiers_projected:false},null,2));
}
if(process.argv[1]===fileURLToPath(import.meta.url))main().catch(error=>{console.error(`GENESIS_PROGRESSIVE_C067_PRIVATE_SOURCE_INVALID: ${error.message}`);process.exit(1);});
