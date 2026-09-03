#!/usr/bin/env node
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { adaptPublicCandidate } from '../adapter/public-adapter.mjs';
import { validatePublicV2 } from '../validate-public-v2.mjs';
import { verifySnapshot0001 } from './validate-snapshot-0001.mjs';

const input=JSON.parse(await readFile(fileURLToPath(new URL('./public-snapshot-0001-input.json',import.meta.url)),'utf8'));
const output=JSON.parse(await readFile(fileURLToPath(new URL('./genesis-public-snapshot-0001.json',import.meta.url)),'utf8'));
const clone=value=>structuredClone(value);

let passed=0,total=0;
function test(name,fn){
  total+=1;
  try{fn();passed+=1;console.log(`PASS  ${name}`)}
  catch(error){console.error(`FAIL  ${name}`);console.error(error instanceof Error?error.message:String(error));process.exitCode=1}
}
function expectThrow(fn,fragment){
  let thrown=null;try{fn()}catch(error){thrown=error}
  if(!thrown)throw new Error('Une erreur était attendue.');
  const message=thrown instanceof Error?thrown.message:String(thrown);
  if(fragment&&!message.includes(fragment))throw new Error(`Erreur inattendue: ${message}`);
}

test('canonical public snapshot 0001 passes',()=>{
  const result=verifySnapshot0001(clone(input),clone(output));
  if(!result.ok)throw new Error('Résultat snapshot non OK.');
});

test('SNAPSHOT plus SYNTHETIC is rejected',()=>{
  const x=clone(input);x.source_status='SYNTHETIC';
  expectThrow(()=>adaptPublicCandidate(x),'PUBLIC_SNAPSHOT');
});

test('DEMO plus PUBLIC_SNAPSHOT is rejected',()=>{
  const x=clone(input);x.mode='DEMO';x.adapter_input_version='1.0.0-test';
  expectThrow(()=>adaptPublicCandidate(x),'SYNTHETIC');
});

test('LIVE_READ_ONLY remains blocked',()=>{
  const x=clone(input);x.mode='LIVE_READ_ONLY';
  expectThrow(()=>adaptPublicCandidate(x),'DEMO ou SNAPSHOT');
});

test('SNAPSHOT requires production adapter input version',()=>{
  const x=clone(input);x.adapter_input_version='1.0.0-test';
  expectThrow(()=>adaptPublicCandidate(x),'1.0.0');
});

test('unknown public payload field is rejected',()=>{
  const x=clone(input);x.public_payload.private_state={enabled:true};
  expectThrow(()=>adaptPublicCandidate(x),'private_state');
});

test('snapshot gate cannot regress to PENDING',()=>{
  const x=clone(input);x.public_payload.publication_gates.gates.find(g=>g.id==='snapshot').status='PENDING';
  expectThrow(()=>adaptPublicCandidate(x),'snapshot');
});

test('live read only cannot be marked PASSED',()=>{
  const x=clone(input);x.public_payload.publication_gates.gates.find(g=>g.id==='live-read-only').status='PASSED';
  expectThrow(()=>adaptPublicCandidate(x),'LIVE_READ_ONLY');
});

test('DEMO identity contamination is rejected',()=>{
  const x=clone(input);x.public_payload.identity.root_version='DEMO-ROOT-v2';
  expectThrow(()=>adaptPublicCandidate(x),'identité DEMO');
});

test('synthetic metric contamination is rejected',()=>{
  const x=clone(input);x.public_payload.metrics[0].status='SYNTHETIC';
  expectThrow(()=>adaptPublicCandidate(x),'SYNTHETIC');
});

test('PUBLIC_HASH evidence is mandatory',()=>{
  const x=clone(input);x.public_payload.evidence=x.public_payload.evidence.filter(e=>e.type!=='PUBLIC_HASH');
  expectThrow(()=>adaptPublicCandidate(x),'PUBLIC_HASH');
});

test('privacy integrity check is mandatory',()=>{
  const x=clone(input);x.public_payload.integrity.checks=x.public_payload.integrity.checks.filter(c=>c.id!=='snapshot-private-raw-data-not-copied');
  expectThrow(()=>adaptPublicCandidate(x),'snapshot-private-raw-data-not-copied');
});

test('private path placed in public evidence is rejected',()=>{
  const x=clone(input);x.public_payload.evidence[0].public_ref='C:\\private\\source.json';
  expectThrow(()=>adaptPublicCandidate(x),'chemin Windows absolu');
});

test('projection digest mismatch is rejected',()=>{
  const x=clone(output);x.payload.metrics.find(m=>m.id==='probabilities-produced').value=true;
  expectThrow(()=>verifySnapshot0001(clone(input),x),'diverge');
});

test('generic validator accepts verified canonical snapshot',()=>{
  const result=validatePublicV2(clone(output));
  if(result.snapshot_gate!=='PASSED')throw new Error('snapshot_gate absent.');
});

console.log(`GENESIS_PUBLIC_SNAPSHOT_0001_TESTS_PASSED ${passed}/${total}`);
if(passed!==total)process.exitCode=1;
