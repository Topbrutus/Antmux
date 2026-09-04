#!/usr/bin/env node
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { validatePublicV2 } from '../validate-public-v2.mjs';
import { buildProgressivePublicEnvelopeC068 } from './bridge-public-progressive-c068.mjs';
import { assertProgressiveBridgeInputC069, c069ToExactC068Text } from './build-public-source-progressive-c069.mjs';
import { extractProgressiveGenesisStatusC068, buildProgressiveBridgeInputC068 } from './build-public-source-progressive-c068.mjs';

function fail(message){throw new Error(message);}
function stable(value){if(Array.isArray(value))return value.map(stable);if(value&&typeof value==='object')return Object.fromEntries(Object.keys(value).sort().map(k=>[k,stable(value[k])]));return value;}
function digestPayload(payload,observedAt){return createHash('sha256').update(JSON.stringify(stable({observed_at:observedAt,payload})),'utf8').digest('hex');}
function metric(id,label,value){return{id,label,value,status:'VERIFIED_PUBLIC',provenance_ref:'SERVER-SIDE-WHITELIST-V5'};}
function byId(metrics,id){const found=metrics.find(x=>x.id===id);if(!found)fail(`Metric C068 manquante: ${id}.`);return found;}
function scanPrivateC069(value){
  const text=JSON.stringify(value);
  const forbidden=[
    'MiniMaxAI/MiniMax-Music3','LOCAL_HUGGINGFACE_DIFFUSERS','huggingface/diffusers',
    'fbdf52fbaaca799592917417eb05f1899f1255ec','dafe3733fcfdbf3c48915fe77be3aef65b5d6a2d',
    '78f850157a54a099dc0f20009b5a4865d5b16e32b8c3eaf3ee3b63237460e7ff',
    '0ba3d5b8baf00cbabf2b4f713f9e8ca1fcf722a2bca49f1330c21f9af55b9f30',
    '21cab7963787255c8343d171da8be4bb3ed51fff1c781d7761d8dce49147a498',
    '6fafcf0def4125a1acc9f74a1d7b33b95f94318710c218dc235f546a21719a38',
    'a19eb4571217bd9d0e3f067f5862189d33cd10299c2f55bdc6adfdbdbc3fecc6',
    '97eac2e27fa1e47065e15c2e69143226f4248cae0623f3b6f723b9356c811a5c',
    'aefdc5b6d486a54845613220728124aeb486e47054a11394c0d413c9203f71c3',
    '1489c87a09e48b86e3b8675e4b6416a4462248895275e31532b75c79152bc0b4',
    'WAV_PCM16_LE_44100HZ_STEREO','target_duration_seconds','audio_export_format','promptPath','prompt_hash','prompt_bytes',
    'generator_provider','model_name','model_version_or_build','runtime_repository','runtime_revision','model_revision',
    'Topbrutus/seedgenesis','Topbrutus/gesis','public/live-source','public/live/status.env','refs/heads/',
  ];
  for(const item of forbidden)if(text.includes(item))fail(`Projection C069 contient une donnée privée interdite: ${item}.`);
}

export function buildProgressivePublicEnvelopeC069(input,options={}){
  if(input?.publication_intent!=='SERVER_SIDE_PUBLIC_READ_ONLY_PROGRESSIVE_BRIDGE_C069')return buildProgressivePublicEnvelopeC068(input,options);
  assertProgressiveBridgeInputC069(input);
  const found=new Map(Object.entries(input.source_attestation.public_status));
  const c068Status=extractProgressiveGenesisStatusC068(c069ToExactC068Text(found));
  const baseInput=buildProgressiveBridgeInputC068(c068Status,{now:input.bridge_received_at,liveActive:input.live_active});
  baseInput.source_observed_at=input.source_observed_at;baseInput.bridge_received_at=input.bridge_received_at;baseInput.max_age_seconds=input.max_age_seconds;
  const result=buildProgressivePublicEnvelopeC068(baseInput,options);
  const envelope=structuredClone(result.envelope),metrics=envelope.payload.metrics;
  byId(metrics,'genesis003-validated-through').value='C069';
  byId(metrics,'next-scientific-action').value='FREEZE_ANALYSIS_THRESHOLDS_AND_DECISION_RULE';
  byId(metrics,'execution-bindings-bound').value=10;
  byId(metrics,'execution-bindings-unbound').value=1;
  byId(metrics,'analysis-decision-rule-bound').value=false;
  metrics.splice(metrics.findIndex(x=>x.id==='hypothesis-selection'),0,
    metric('genesis003-c069','C069 · profil requête génération','VALIDATED_10_OF_10'),
    metric('real-generation-request-profile-frozen','Profil requête génération gelé',true),
    metric('prompt-hashes-frozen','Hashes prompts gelés',true),
    metric('style-structure-template-frozen','Template style/structure gelé',true),
    metric('duration-export-profile-frozen','Profil durée/export gelé',true),
    metric('real-request-bindings-added','Bindings requête réelle ajoutés',4),
    metric('translation-equivalence-verified','Équivalence traduction vérifiée',false),
    metric('request-profile-only','Profil requête seulement',true),
  );
  envelope.payload.identity.root_version='GENESIS-003-C069-PUBLIC-PROGRESS-v5';
  envelope.payload.evidence=envelope.payload.evidence.filter(x=>x.id!=='LIVE-PUBLIC-PROJECTION-HASH');
  envelope.payload.evidence[0]={id:'SERVER-SIDE-WHITELIST-V5',type:'PUBLIC_ATTESTATION',status:'VERIFIED_PUBLIC',public_ref:'Whitelisted progressive Genesis C060-C069 status projection'};
  envelope.payload.integrity.checks=envelope.payload.integrity.checks.map(x=>x.id==='live-public-projection-hash'?{...x,public_ref:'PUBLIC-READ-ONLY-SHA256'}:x);
  const digest=digestPayload(envelope.payload,input.source_observed_at);
  envelope.payload.identity.root_digest=`PUBLIC-READ-ONLY-SHA256:${digest}`;
  envelope.payload.evidence.push({id:'LIVE-PUBLIC-PROJECTION-HASH',type:'PUBLIC_HASH',status:'VERIFIED_PUBLIC',public_ref:'Server-side progressive public read-only projection',hash:`sha256:${digest}`});
  envelope.publication_id='GENESIS-PUBLIC-READ-ONLY-PROGRESSIVE-0005';
  validatePublicV2(envelope);scanPrivateC069(envelope);
  return{envelope,sourceAgeSeconds:result.sourceAgeSeconds};
}

async function main(){
  const inputPath=process.argv[2];if(!inputPath)fail('Usage: bridge-public-progressive-c069.mjs <bridge-input.json>');
  const input=JSON.parse(await readFile(path.resolve(inputPath),'utf8'));const result=buildProgressivePublicEnvelopeC069(input);
  const outDir=path.resolve('.build/genesis-public-read-only-bridge');await mkdir(outDir,{recursive:true});await writeFile(path.join(outDir,'public-read-only-envelope.json'),`${JSON.stringify(result.envelope,null,2)}\n`,'utf8');
  console.log('GENESIS_PROGRESSIVE_C069_PUBLIC_READ_ONLY_BRIDGE_VALID');console.log(JSON.stringify({mode:result.envelope.mode,validated_through:result.envelope.payload.metrics.find(x=>x.id==='genesis003-validated-through')?.value,private_request_profile_projected:false},null,2));
}
if(process.argv[1]===fileURLToPath(import.meta.url))main().catch(error=>{console.error(`GENESIS_PROGRESSIVE_C069_PUBLIC_READ_ONLY_BRIDGE_INVALID: ${error.message}`);process.exit(1);});
