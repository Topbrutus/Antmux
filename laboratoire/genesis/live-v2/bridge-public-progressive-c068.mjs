#!/usr/bin/env node
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { validatePublicV2 } from '../validate-public-v2.mjs';
import { buildProgressivePublicEnvelopeC067 } from './bridge-public-progressive-c067.mjs';
import {
  assertProgressiveBridgeInputC068,
  c068ToExactC067Text,
} from './build-public-source-progressive-c068.mjs';
import {
  extractProgressiveGenesisStatusC067,
  buildProgressiveBridgeInputC067,
} from './build-public-source-progressive-c067.mjs';

function fail(message){throw new Error(message);}
function stable(value){if(Array.isArray(value))return value.map(stable);if(value&&typeof value==='object')return Object.fromEntries(Object.keys(value).sort().map(k=>[k,stable(value[k])]));return value;}
function digestPayload(payload,observedAt){return createHash('sha256').update(JSON.stringify(stable({observed_at:observedAt,payload})),'utf8').digest('hex');}
function metric(id,label,value){return{id,label,value,status:'VERIFIED_PUBLIC',provenance_ref:'SERVER-SIDE-WHITELIST-V4'};}
function scanPrivateC068(value){
  const text=JSON.stringify(value);
  const forbidden=[
    'MiniMaxAI/MiniMax-Music3','LOCAL_HUGGINGFACE_DIFFUSERS','huggingface/diffusers',
    'fbdf52fbaaca799592917417eb05f1899f1255ec','dafe3733fcfdbf3c48915fe77be3aef65b5d6a2d',
    'c302f498bf518f7e9b2c15a7c6fa552343ee8cb3a6e639112a98d191635cfbc5',
    'dfcdae683b561ffb1379d8f7d92fed67439ae5d593e90e29a39100a22a3cc4d2',
    '779a78432902c898dc37e05a62f90d69317638c38c0e1e1002e2d7077e953bdf',
    'generator_provider','model_name','model_version_or_build','runtime_repository','runtime_revision','model_revision',
    'Topbrutus/seedgenesis','Topbrutus/gesis','public/live-source','public/live/status.env','refs/heads/'
  ];
  for(const item of forbidden)if(text.includes(item))fail(`Projection C068 contient une donnée privée interdite: ${item}.`);
}
function byId(metrics,id){const found=metrics.find(x=>x.id===id);if(!found)fail(`Metric C067 manquante: ${id}.`);return found;}

export function buildProgressivePublicEnvelopeC068(input,options={}){
  if(input?.publication_intent!=='SERVER_SIDE_PUBLIC_READ_ONLY_PROGRESSIVE_BRIDGE_C068')return buildProgressivePublicEnvelopeC067(input,options);
  assertProgressiveBridgeInputC068(input);
  const found=new Map(Object.entries(input.source_attestation.public_status));
  const c067Status=extractProgressiveGenesisStatusC067(c068ToExactC067Text(found));
  const baseInput=buildProgressiveBridgeInputC067(c067Status,{now:input.bridge_received_at,liveActive:input.live_active});
  baseInput.source_observed_at=input.source_observed_at;baseInput.bridge_received_at=input.bridge_received_at;baseInput.max_age_seconds=input.max_age_seconds;
  const result=buildProgressivePublicEnvelopeC067(baseInput,options);
  const envelope=structuredClone(result.envelope),metrics=envelope.payload.metrics;
  byId(metrics,'genesis003-validated-through').value='C068';
  byId(metrics,'next-scientific-action').value='FREEZE_REAL_GENERATION_REQUEST_PROFILE';
  byId(metrics,'execution-bindings-bound').value=6;
  byId(metrics,'execution-bindings-unbound').value=5;
  byId(metrics,'real-generator-bindings-added').value=3;
  metrics.splice(metrics.findIndex(x=>x.id==='hypothesis-selection'),0,
    metric('genesis003-c068','C068 · identité générateur réel','VALIDATED_10_OF_10'),
    metric('real-generator-identity-frozen','Identité générateur réel gelée',true),
    metric('runtime-compatibility-verified','Compatibilité runtime vérifiée',false),
    metric('language-coverage-verified','Couverture linguistique vérifiée',false),
    metric('language-confound-registered','Risque de confondant linguistique enregistré',true),
  );
  envelope.payload.identity.root_version='GENESIS-003-C068-PUBLIC-PROGRESS-v4';
  envelope.payload.evidence=envelope.payload.evidence.filter(x=>x.id!=='LIVE-PUBLIC-PROJECTION-HASH');
  envelope.payload.evidence[0]={id:'SERVER-SIDE-WHITELIST-V4',type:'PUBLIC_ATTESTATION',status:'VERIFIED_PUBLIC',public_ref:'Whitelisted progressive Genesis C060-C068 status projection'};
  envelope.payload.integrity.checks=envelope.payload.integrity.checks.map(x=>x.id==='live-public-projection-hash'?{...x,public_ref:'PUBLIC-READ-ONLY-SHA256'}:x);
  const digest=digestPayload(envelope.payload,input.source_observed_at);
  envelope.payload.identity.root_digest=`PUBLIC-READ-ONLY-SHA256:${digest}`;
  envelope.payload.evidence.push({id:'LIVE-PUBLIC-PROJECTION-HASH',type:'PUBLIC_HASH',status:'VERIFIED_PUBLIC',public_ref:'Server-side progressive public read-only projection',hash:`sha256:${digest}`});
  envelope.publication_id='GENESIS-PUBLIC-READ-ONLY-PROGRESSIVE-0004';
  validatePublicV2(envelope);scanPrivateC068(envelope);
  return{envelope,sourceAgeSeconds:result.sourceAgeSeconds};
}

async function main(){
  const inputPath=process.argv[2];if(!inputPath)fail('Usage: bridge-public-progressive-c068.mjs <bridge-input.json>');
  const input=JSON.parse(await readFile(path.resolve(inputPath),'utf8'));const result=buildProgressivePublicEnvelopeC068(input);
  const outDir=path.resolve('.build/genesis-public-read-only-bridge');await mkdir(outDir,{recursive:true});await writeFile(path.join(outDir,'public-read-only-envelope.json'),`${JSON.stringify(result.envelope,null,2)}\n`,'utf8');
  console.log('GENESIS_PROGRESSIVE_C068_PUBLIC_READ_ONLY_BRIDGE_VALID');console.log(JSON.stringify({mode:result.envelope.mode,validated_through:result.envelope.payload.metrics.find(x=>x.id==='genesis003-validated-through')?.value,private_generator_identity_projected:false},null,2));
}
if(process.argv[1]===fileURLToPath(import.meta.url))main().catch(error=>{console.error(`GENESIS_PROGRESSIVE_C068_PUBLIC_READ_ONLY_BRIDGE_INVALID: ${error.message}`);process.exit(1);});
