#!/usr/bin/env node
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { adaptPublicCandidate } from './public-adapter.mjs';

const fixturePath = fileURLToPath(new URL('./fixtures/synthetic-private-like.json', import.meta.url));
const canonical = JSON.parse(await readFile(fixturePath, 'utf8'));
const clone = value => structuredClone(value);

let passed = 0;
let total = 0;
function test(name, fn){
  total += 1;
  try{
    fn();
    passed += 1;
    console.log(`PASS  ${name}`);
  }catch(error){
    console.error(`FAIL  ${name}`);
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  }
}
function expectThrow(fn, fragment){
  let thrown = null;
  try{ fn(); }catch(error){ thrown = error; }
  if(!thrown) throw new Error('Une erreur était attendue.');
  const message = thrown instanceof Error ? thrown.message : String(thrown);
  if(fragment && !message.includes(fragment)) throw new Error(`Erreur inattendue: ${message}`);
}

test('canonical synthetic private-like candidate passes', ()=>{
  const out = adaptPublicCandidate(clone(canonical));
  if(out.integrity_status !== 'VERIFIED_PUBLIC') throw new Error('VERIFIED_PUBLIC absent.');
});

test('private context is never copied', ()=>{
  const out = adaptPublicCandidate(clone(canonical));
  const text = JSON.stringify(out);
  for(const marker of ['Topbrutus/seedgenesis','C:\\private\\seedgenesis','ghp_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA','http://127.0.0.1:9999/private']){
    if(text.includes(marker)) throw new Error(`Fuite: ${marker}`);
  }
});

test('unknown payload category is rejected', ()=>{
  const x = clone(canonical); x.public_payload.writeback = {enabled:true};
  expectThrow(()=>adaptPublicCandidate(x),'writeback');
});

test('unknown identity field is rejected', ()=>{
  const x = clone(canonical); x.public_payload.identity.private_seed = 'NOPE';
  expectThrow(()=>adaptPublicCandidate(x),'private_seed');
});

test('unknown pipeline step field is rejected', ()=>{
  const x = clone(canonical); x.public_payload.pipeline.steps[0].private_path = '/secret';
  expectThrow(()=>adaptPublicCandidate(x),'private_path');
});

test('SNAPSHOT mode is blocked in adapter validation phase', ()=>{
  const x = clone(canonical); x.mode = 'SNAPSHOT';
  expectThrow(()=>adaptPublicCandidate(x),'mode=DEMO');
});

test('LIVE_READ_ONLY mode is blocked in adapter validation phase', ()=>{
  const x = clone(canonical); x.mode = 'LIVE_READ_ONLY';
  expectThrow(()=>adaptPublicCandidate(x),'mode=DEMO');
});

test('non-synthetic source is blocked in adapter validation phase', ()=>{
  const x = clone(canonical); x.source_status = 'PUBLIC_SNAPSHOT';
  expectThrow(()=>adaptPublicCandidate(x),'source_status=SYNTHETIC');
});

test('explicit publication intent is mandatory', ()=>{
  const x = clone(canonical); x.publication_intent = 'AUTO_PUBLISH';
  expectThrow(()=>adaptPublicCandidate(x),'publication_intent');
});

test('token-shaped value in allowed public field is rejected', ()=>{
  const x = clone(canonical); x.public_payload.identity.root_digest = 'ghp_BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB';
  expectThrow(()=>adaptPublicCandidate(x),'token GitHub');
});

test('private Windows path in allowed public field is rejected', ()=>{
  const x = clone(canonical); x.public_payload.evidence[0].public_ref = 'C:\\secret\\audit.json';
  expectThrow(()=>adaptPublicCandidate(x),'chemin Windows absolu');
});

test('localhost endpoint in allowed public field is rejected', ()=>{
  const x = clone(canonical); x.public_payload.observatory.latest_export_ref = 'http://127.0.0.1:3000/private';
  expectThrow(()=>adaptPublicCandidate(x),'endpoint local');
});

test('scientific rule cannot be weakened', ()=>{
  const x = clone(canonical); x.public_payload.observatory.scientific_rule = 'MESURE = INTERPRÉTATION';
  expectThrow(()=>adaptPublicCandidate(x),'MESURE != INTERPRÉTATION');
});

test('pipeline cannot hide an incomplete stage 5', ()=>{
  const x = clone(canonical); x.public_payload.pipeline.steps[4].status = 'PENDING';
  expectThrow(()=>adaptPublicCandidate(x),'étape 5');
});

test('return source invariants remain mandatory', ()=>{
  const x = clone(canonical); x.public_payload.continuity.return_status = 'FAILED';
  expectThrow(()=>adaptPublicCandidate(x),'return_status=PASSED');
});

console.log(`GENESIS_PUBLIC_ADAPTER_TESTS_PASSED ${passed}/${total}`);
if(passed !== total) process.exitCode = 1;
