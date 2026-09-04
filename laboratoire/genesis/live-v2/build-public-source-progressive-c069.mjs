#!/usr/bin/env node
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { extractProgressiveGenesisStatusC068, buildProgressiveBridgeInputC068 } from './build-public-source-progressive-c068.mjs';

const C069_NEW_KEYS=Object.freeze({
  genesis003_c069:'VALIDATED_10_OF_10',
  signal_gesis_reproducibility_validated:'true',
  cross_runner_reproducibility_proven:'true',
  calibration_control_passed:'true',
  provider_model_kernel_dependency:'false',
});
function fail(message){throw new Error(message);}
function parse(text){const found=new Map();if(typeof text!=='string'||!text.length)fail('Source Genesis absente.');for(const raw of text.split(/\r?\n/)){if(!raw)continue;const m=raw.match(/^([A-Za-z0-9_]+)=(.*)$/);if(!m)fail(`Ligne invalide: ${raw}.`);const[,k,v]=m;if(found.has(k))fail(`Clé dupliquée: ${k}.`);found.set(k,v);}return found;}
function serialize(found){return `${[...found.entries()].map(([k,v])=>`${k}=${v}`).join('\n')}\n`;}
export function c069ToExactC068Text(found){const copy=new Map(found);for(const k of Object.keys(C069_NEW_KEYS))copy.delete(k);copy.set('genesis003_validated_through','C068');copy.set('next_scientific_action','FREEZE_REAL_GENERATION_REQUEST_PROFILE');copy.set('execution_bindings_bound','6');copy.set('execution_bindings_unbound','5');copy.set('analysis_decision_rule_bound','false');return serialize(copy);}
function assertExactC069(found){
  if(found.size!==61)fail(`Projection C069 attendue sur 61 lignes; reçu ${found.size}.`);
  if(found.get('genesis003_validated_through')!=='C069')fail('Stage C069 manquant.');
  if(found.get('next_scientific_action')!=='FREEZE_ANALYSIS_THRESHOLDS_AND_DECISION_RULE')fail('Action C069 inattendue.');
  if(found.get('execution_bindings_required')!=='11'||found.get('execution_bindings_bound')!=='6'||found.get('execution_bindings_unbound')!=='5'||found.get('execution_bindings_complete')!=='false')fail('Comptage bindings C069 invalide.');
  if(found.get('analysis_decision_rule_bound')!=='false')fail('Règle C069 ne doit pas être liée.');
  if(found.get('real_generator_bindings_added')!=='3'||found.get('real_generator_identity_frozen')!=='true'||found.get('runtime_compatibility_verified')!=='false'||found.get('language_coverage_verified')!=='false'||found.get('language_confound_registered')!=='true')fail('Frontière C068 héritée invalide.');
  for(const[k,v]of Object.entries(C069_NEW_KEYS))if(found.get(k)!==v)fail(`Champ C069 invalide: ${k}.`);
  const forbidden=['generator_provider','model_name','model_version_or_build','runtime_repository','runtime_revision','model_revision','prompt_hash','prompt_bytes','request_profile_digest','contract_c069_digest','c069_digest','signal_sha256','gesis_measurement_digest','gesis_main_commit','gesis_analyzer_blob','audit_run_id'];
  for(const k of forbidden)if(found.has(k))fail(`Clé privée interdite dans C069 public: ${k}.`);
  extractProgressiveGenesisStatusC068(c069ToExactC068Text(found));
}
export function extractProgressiveGenesisStatusC069(text){try{return extractProgressiveGenesisStatusC068(text);}catch{const found=parse(text);assertExactC069(found);return{schema:'GENESIS_PUBLIC_PROGRESSIVE_STATUS_V5_SIGNAL',validatedThrough:'C069',values:Object.freeze(Object.fromEntries(found))};}}
export function buildProgressiveBridgeInputC069(status,options={}){if(status?.validatedThrough!=='C069')return buildProgressiveBridgeInputC068(status,options);if(status.schema!=='GENESIS_PUBLIC_PROGRESSIVE_STATUS_V5_SIGNAL')fail('Statut C069 invalide.');const found=new Map(Object.entries(status.values??{}));assertExactC069(found);const c068=extractProgressiveGenesisStatusC068(c069ToExactC068Text(found));const base=buildProgressiveBridgeInputC068(c068,options);return{...base,bridge_input_version:'5.1.0',publication_intent:'SERVER_SIDE_PUBLIC_READ_ONLY_PROGRESSIVE_BRIDGE_C069_SIGNAL',source_attestation:{...base.source_attestation,source_state:'C041_C069_SIGNAL_REPRO_COMPLETE_VALIDATED',validated_through:'C069',public_status:status.values}};}
export function assertProgressiveBridgeInputC069(input){if(input?.publication_intent!=='SERVER_SIDE_PUBLIC_READ_ONLY_PROGRESSIVE_BRIDGE_C069_SIGNAL')return false;if(input.bridge_input_version!=='5.1.0')fail('Version C069 invalide.');const a=input.source_attestation;if(!a||a.validated_through!=='C069'||a.source_state!=='C041_C069_SIGNAL_REPRO_COMPLETE_VALIDATED')fail('Attestation C069 invalide.');if(a.read_capability!=='READ_ONLY'||a.write_capability!=='NONE'||a.adapter_only!==true)fail('Frontière source C069 invalide.');assertExactC069(new Map(Object.entries(a.public_status??{})));return true;}
async function main(){const sourcePath=process.argv[2];if(!sourcePath)fail('Usage: build-public-source-progressive-c069.mjs <status.env> [output.json]');const outputPath=process.argv[3]??'.build/genesis-progressive-live/bridge-input.json';const source=await readFile(path.resolve(sourcePath),'utf8');const status=extractProgressiveGenesisStatusC069(source);const input=buildProgressiveBridgeInputC069(status,{liveActive:(process.env.GENESIS_PUBLIC_LIVE_ACTIVE??'1')==='1'});const resolved=path.resolve(outputPath);await mkdir(path.dirname(resolved),{recursive:true});await writeFile(resolved,`${JSON.stringify(input,null,2)}\n`,'utf8');console.log('GENESIS_PROGRESSIVE_C069_SIGNAL_SOURCE_VALID');}
if(process.argv[1]===fileURLToPath(import.meta.url))main().catch(e=>{console.error(`GENESIS_PROGRESSIVE_C069_SIGNAL_SOURCE_INVALID: ${e.message}`);process.exit(1);});
