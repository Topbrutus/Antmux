#!/usr/bin/env node
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  extractProgressiveGenesisStatusC068,
  buildProgressiveBridgeInputC068,
} from './build-public-source-progressive-c068.mjs';

const C069_NEW_KEYS=Object.freeze({
  genesis003_c069:'VALIDATED_10_OF_10',
  real_generation_request_profile_frozen:'true',
  prompt_hashes_frozen:'true',
  style_structure_template_frozen:'true',
  duration_export_profile_frozen:'true',
  real_request_bindings_added:'4',
  translation_equivalence_verified:'false',
  request_profile_only:'true',
});

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
function serialize(found){return `${[...found.entries()].map(([k,v])=>`${k}=${v}`).join('\n')}\n`;}

export function c069ToExactC068Text(found){
  const copy=new Map(found);
  for(const key of Object.keys(C069_NEW_KEYS))copy.delete(key);
  copy.set('genesis003_validated_through','C068');
  copy.set('next_scientific_action','FREEZE_REAL_GENERATION_REQUEST_PROFILE');
  copy.set('execution_bindings_bound','6');
  copy.set('execution_bindings_unbound','5');
  return serialize(copy);
}

function assertExactC069(found){
  if(found.size!==64)fail(`Projection C069 attendue sur 64 lignes; reçu ${found.size}.`);
  if(found.get('genesis003_validated_through')!=='C069')fail('Stage C069 manquant.');
  if(found.get('next_scientific_action')!=='FREEZE_ANALYSIS_THRESHOLDS_AND_DECISION_RULE')fail('Action C069 inattendue.');
  if(found.get('execution_bindings_required')!=='11'||found.get('execution_bindings_bound')!=='10'||found.get('execution_bindings_unbound')!=='1'||found.get('execution_bindings_complete')!=='false')fail('Comptage bindings C069 invalide.');
  if(found.get('analysis_decision_rule_bound')!=='false')fail('analysis_decision_rule_bound doit rester false en C069.');
  if(found.get('real_generator_bindings_added')!=='3'||found.get('real_generator_profile_frozen')!=='false'||found.get('real_generator_identity_frozen')!=='true')fail('Frontière générateur C069 invalide.');
  if(found.get('runtime_compatibility_verified')!=='false'||found.get('language_coverage_verified')!=='false'||found.get('language_confound_registered')!=='true')fail('Frontière incertitude C069 invalide.');
  for(const[key,value]of Object.entries(C069_NEW_KEYS))if(found.get(key)!==value)fail(`Champ C069 invalide: ${key}.`);
  const forbidden=['generator_provider','model_name','model_version_or_build','runtime_repository','runtime_revision','model_revision','prompt_hash','prompt_bytes','target_duration_seconds','audio_export_format','request_profile_digest','contract_c069_digest','c069_digest'];
  for(const key of forbidden)if(found.has(key))fail(`Clé privée interdite dans C069 public: ${key}.`);
  extractProgressiveGenesisStatusC068(c069ToExactC068Text(found));
}

export function extractProgressiveGenesisStatusC069(text){
  try{return extractProgressiveGenesisStatusC068(text);}catch(error){
    const found=parse(text);assertExactC069(found);
    return{schema:'GENESIS_PUBLIC_PROGRESSIVE_STATUS_V5',validatedThrough:'C069',values:Object.freeze(Object.fromEntries(found))};
  }
}

export function buildProgressiveBridgeInputC069(status,options={}){
  if(status?.validatedThrough!=='C069')return buildProgressiveBridgeInputC068(status,options);
  if(status.schema!=='GENESIS_PUBLIC_PROGRESSIVE_STATUS_V5')fail('Statut progressif C069 invalide.');
  const found=new Map(Object.entries(status.values??{}));assertExactC069(found);
  const c068=extractProgressiveGenesisStatusC068(c069ToExactC068Text(found));
  const base=buildProgressiveBridgeInputC068(c068,options);
  return{
    ...base,
    bridge_input_version:'5.0.0',
    publication_intent:'SERVER_SIDE_PUBLIC_READ_ONLY_PROGRESSIVE_BRIDGE_C069',
    source_attestation:{...base.source_attestation,source_state:'C041_C069_COMPLETE_VALIDATED',validated_through:'C069',public_status:status.values},
  };
}

export function assertProgressiveBridgeInputC069(input){
  if(input?.publication_intent!=='SERVER_SIDE_PUBLIC_READ_ONLY_PROGRESSIVE_BRIDGE_C069')return false;
  if(input.bridge_input_version!=='5.0.0')fail('Version bridge C069 invalide.');
  const a=input.source_attestation;if(!a||a.validated_through!=='C069'||a.source_state!=='C041_C069_COMPLETE_VALIDATED')fail('Attestation C069 invalide.');
  if(a.source_kind!=='PRIVATE_GENESIS_PUBLIC_PROJECTION'||a.source_identity!=='OPAQUE_PUBLIC_ATTESTATION'||a.read_capability!=='READ_ONLY'||a.write_capability!=='NONE'||a.adapter_only!==true)fail('Frontière source C069 invalide.');
  const found=new Map(Object.entries(a.public_status??{}));assertExactC069(found);
  const t=input.transport;if(!t||t.server_side_pull!==true||t.public_endpoint_only!==true||t.fail_closed!==true||t.snapshot_fallback_available!==true||t.browser_credentials_present!==false||t.private_browser_request!==false)fail('Transport C069 invalide.');
  if(typeof input.live_active!=='boolean'||!Number.isInteger(input.max_age_seconds)||input.max_age_seconds<30||input.max_age_seconds>900)fail('Paramètres bridge C069 invalides.');
  return true;
}

async function main(){
  const sourcePath=process.argv[2];if(!sourcePath)fail('Usage: build-public-source-progressive-c069.mjs <status.env> [output.json]');
  const outputPath=process.argv[3]??'.build/genesis-progressive-live/bridge-input.json';
  const source=await readFile(path.resolve(sourcePath),'utf8');const status=extractProgressiveGenesisStatusC069(source);
  const flag=process.env.GENESIS_PUBLIC_LIVE_ACTIVE??'1';if(!['0','1'].includes(flag))fail('GENESIS_PUBLIC_LIVE_ACTIVE doit être 0 ou 1.');
  const input=buildProgressiveBridgeInputC069(status,{liveActive:flag==='1'});const resolved=path.resolve(outputPath);await mkdir(path.dirname(resolved),{recursive:true});await writeFile(resolved,`${JSON.stringify(input,null,2)}\n`,'utf8');
  console.log('GENESIS_PROGRESSIVE_C069_PRIVATE_SOURCE_VALID');console.log(JSON.stringify({validated_through:status.validatedThrough,private_request_profile_projected:false},null,2));
}
if(process.argv[1]===fileURLToPath(import.meta.url))main().catch(error=>{console.error(`GENESIS_PROGRESSIVE_C069_PRIVATE_SOURCE_INVALID: ${error.message}`);process.exit(1);});
