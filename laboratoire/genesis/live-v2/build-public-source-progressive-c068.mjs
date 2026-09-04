#!/usr/bin/env node
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  extractProgressiveGenesisStatusC067,
  buildProgressiveBridgeInputC067,
} from './build-public-source-progressive-c067.mjs';

const C068_NEW_KEYS=Object.freeze({
  genesis003_c068:'VALIDATED_10_OF_10',
  real_generator_identity_frozen:'true',
  runtime_compatibility_verified:'false',
  language_coverage_verified:'false',
  language_confound_registered:'true',
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

export function c068ToExactC067Text(found){
  const copy=new Map(found);
  for(const key of Object.keys(C068_NEW_KEYS))copy.delete(key);
  copy.set('genesis003_validated_through','C067');
  copy.set('next_scientific_action','SELECT_REAL_GENERATOR_PROVIDER_MODEL_BUILD');
  copy.set('execution_bindings_bound','3');
  copy.set('execution_bindings_unbound','8');
  copy.set('real_generator_bindings_added','0');
  return serialize(copy);
}

function assertExactC068(found){
  if(found.size!==56)fail(`Projection C068 attendue sur 56 lignes; reçu ${found.size}.`);
  if(found.get('genesis003_validated_through')!=='C068')fail('Stage C068 manquant.');
  if(found.get('next_scientific_action')!=='FREEZE_REAL_GENERATION_REQUEST_PROFILE')fail('Action C068 inattendue.');
  if(found.get('execution_bindings_required')!=='11'||found.get('execution_bindings_bound')!=='6'||found.get('execution_bindings_unbound')!=='5'||found.get('execution_bindings_complete')!=='false')fail('Comptage bindings C068 invalide.');
  if(found.get('real_generator_bindings_added')!=='3'||found.get('real_generator_profile_frozen')!=='false')fail('Frontière profil générateur C068 invalide.');
  for(const[key,value]of Object.entries(C068_NEW_KEYS))if(found.get(key)!==value)fail(`Champ C068 invalide: ${key}.`);
  const forbidden=['generator_provider','model_name','model_version_or_build','runtime_repository','runtime_revision','model_revision','prompt_hash','selection_digest','contract_c068_digest','c068_digest'];
  for(const key of forbidden)if(found.has(key))fail(`Clé privée interdite dans C068 public: ${key}.`);
  extractProgressiveGenesisStatusC067(c068ToExactC067Text(found));
}

export function extractProgressiveGenesisStatusC068(text){
  try{return extractProgressiveGenesisStatusC067(text);}catch(error){
    const found=parse(text);assertExactC068(found);
    return{schema:'GENESIS_PUBLIC_PROGRESSIVE_STATUS_V4',validatedThrough:'C068',values:Object.freeze(Object.fromEntries(found))};
  }
}

export function buildProgressiveBridgeInputC068(status,options={}){
  if(status?.validatedThrough!=='C068')return buildProgressiveBridgeInputC067(status,options);
  if(status.schema!=='GENESIS_PUBLIC_PROGRESSIVE_STATUS_V4')fail('Statut progressif C068 invalide.');
  const found=new Map(Object.entries(status.values??{}));assertExactC068(found);
  const c067=extractProgressiveGenesisStatusC067(c068ToExactC067Text(found));
  const base=buildProgressiveBridgeInputC067(c067,options);
  return{
    ...base,
    bridge_input_version:'4.0.0',
    publication_intent:'SERVER_SIDE_PUBLIC_READ_ONLY_PROGRESSIVE_BRIDGE_C068',
    source_attestation:{...base.source_attestation,source_state:'C041_C068_COMPLETE_VALIDATED',validated_through:'C068',public_status:status.values},
  };
}

export function assertProgressiveBridgeInputC068(input){
  if(input?.publication_intent!=='SERVER_SIDE_PUBLIC_READ_ONLY_PROGRESSIVE_BRIDGE_C068')return false;
  if(input.bridge_input_version!=='4.0.0')fail('Version bridge C068 invalide.');
  const a=input.source_attestation;if(!a||a.validated_through!=='C068'||a.source_state!=='C041_C068_COMPLETE_VALIDATED')fail('Attestation C068 invalide.');
  if(a.source_kind!=='PRIVATE_GENESIS_PUBLIC_PROJECTION'||a.source_identity!=='OPAQUE_PUBLIC_ATTESTATION'||a.read_capability!=='READ_ONLY'||a.write_capability!=='NONE'||a.adapter_only!==true)fail('Frontière source C068 invalide.');
  const found=new Map(Object.entries(a.public_status??{}));assertExactC068(found);
  const t=input.transport;if(!t||t.server_side_pull!==true||t.public_endpoint_only!==true||t.fail_closed!==true||t.snapshot_fallback_available!==true||t.browser_credentials_present!==false||t.private_browser_request!==false)fail('Transport C068 invalide.');
  if(typeof input.live_active!=='boolean'||!Number.isInteger(input.max_age_seconds)||input.max_age_seconds<30||input.max_age_seconds>900)fail('Paramètres bridge C068 invalides.');
  return true;
}

async function main(){
  const sourcePath=process.argv[2];if(!sourcePath)fail('Usage: build-public-source-progressive-c068.mjs <status.env> [output.json]');
  const outputPath=process.argv[3]??'.build/genesis-progressive-live/bridge-input.json';
  const source=await readFile(path.resolve(sourcePath),'utf8');const status=extractProgressiveGenesisStatusC068(source);
  const flag=process.env.GENESIS_PUBLIC_LIVE_ACTIVE??'1';if(!['0','1'].includes(flag))fail('GENESIS_PUBLIC_LIVE_ACTIVE doit être 0 ou 1.');
  const input=buildProgressiveBridgeInputC068(status,{liveActive:flag==='1'});const resolved=path.resolve(outputPath);await mkdir(path.dirname(resolved),{recursive:true});await writeFile(resolved,`${JSON.stringify(input,null,2)}\n`,'utf8');
  console.log('GENESIS_PROGRESSIVE_C068_PRIVATE_SOURCE_VALID');console.log(JSON.stringify({validated_through:status.validatedThrough,private_generator_identity_projected:false},null,2));
}
if(process.argv[1]===fileURLToPath(import.meta.url))main().catch(error=>{console.error(`GENESIS_PROGRESSIVE_C068_PRIVATE_SOURCE_INVALID: ${error.message}`);process.exit(1);});
