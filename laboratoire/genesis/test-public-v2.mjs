#!/usr/bin/env node
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { validatePublicV2 } from './validate-public-v2.mjs';

const canonical = JSON.parse(await readFile(fileURLToPath(new URL('./demo/genesis-demo-v2.json', import.meta.url)), 'utf8'));
const clone = value => JSON.parse(JSON.stringify(value));

const cases = [
  ['canonical v2 complete-cycle demo passes', true, d => d],
  ['unknown top-level field rejected', false, d => (d.private_debug='x',d)],
  ['non-DEMO/SNAPSHOT canonical mode rejected', false, d => (d.mode='LIVE_READ_ONLY',d)],
  ['non-synthetic/public_snapshot canonical source rejected', false, d => (d.source_status='PUBLIC_READ_ONLY',d)],
  ['unknown payload category rejected', false, d => (d.payload.private_state={},d)],
  ['invalid semantic class rejected', false, d => (d.payload.training_field.observations[0].semantic_class='MAGIC',d)],
  ['invalid pipeline status rejected', false, d => (d.payload.pipeline.steps[0].status='SECRET_RUNNING',d)],
  ['invalid publication gate status rejected', false, d => (d.payload.publication_gates.gates[0].status='AUTO_MERGED',d)],
  ['scientific rule cannot be weakened', false, d => (d.payload.observatory.scientific_rule='MESURE = INTERPRÉTATION',d)],
  ['private Windows path rejected', false, d => (d.payload.evidence[0].public_ref='C:\\private\\secret.json',d)],
  ['localhost endpoint rejected', false, d => (d.payload.evidence[0].public_ref='http://127.0.0.1:8080/private',d)],
  ['private RFC1918 endpoint rejected', false, d => (d.payload.evidence[0].public_ref='https://192.168.1.44/state',d)],
  ['GitHub token-shaped string rejected', false, d => (d.payload.evidence[0].public_ref='ghp_123456789012345678901234567890123456',d)],
  ['private key marker rejected', false, d => (d.payload.evidence[0].public_ref='-----BEGIN PRIVATE KEY-----',d)],
  ['non-finite metric rejected', false, d => (d.payload.metrics[0].value=Infinity,d)],
  ['missing ROOT field rejected', false, d => (delete d.payload.identity.root_status,d)],
  ['negative continuity cycle rejected', false, d => (d.payload.continuity.cycle=-1,d)],
  ['training observations require provenance', false, d => (delete d.payload.training_field.observations[0].provenance_ref,d)],
  ['cycle must contain exactly seven stages', false, d => (d.payload.pipeline.steps.pop(),d)],
  ['cycle stage order is frozen', false, d => ([d.payload.pipeline.steps[4],d.payload.pipeline.steps[5]]=[d.payload.pipeline.steps[5],d.payload.pipeline.steps[4]],d)],
  ['stage 5 exploration must be passed', false, d => (d.payload.pipeline.steps[4].status='RUNNING_PUBLIC',d)],
  ['stage 6 validation must be passed', false, d => (d.payload.pipeline.steps[5].status='PENDING',d)],
  ['stage 7 return source must be passed', false, d => (d.payload.pipeline.steps[6].status='PENDING',d)],
  ['metacognition must declare completed demo cycle', false, d => (d.payload.metacognition.status='DEMO_ONLY',d)],
  ['C041-C060 demo completion marker required', false, d => (d.payload.metacognition.c041_c060_status='PLANNED_DEMO',d)],
  ['exploration requires competing hypotheses', false, d => (d.payload.metacognition.competing_hypotheses=1,d)],
  ['return source requires parent link', false, d => (d.payload.continuity.parent_link_status='FAILED',d)],
  ['return source requires preserved ROOT identity', false, d => (d.payload.continuity.root_identity_status='FAILED',d)],
  ['return source requires return status passed', false, d => (d.payload.continuity.return_status='FAILED',d)],
  ['return source requires checkpoint advance', false, d => (d.payload.continuity.current_checkpoint_ref=d.payload.continuity.previous_checkpoint_ref,d)],
  ['validation must preserve accepted or rejected verdict', false, d => (d.payload.continuity.accepted_candidates=0,d.payload.continuity.rejected_candidates=0,d)],
  ['cycle proof evidence is mandatory', false, d => (d.payload.evidence=d.payload.evidence.filter(x=>x.id!=='DEMO-CYCLE-5-6-7'),d)],
  ['cycle integrity check must pass', false, d => (d.payload.integrity.checks.find(x=>x.id==='demo-check-cycle-5-6-7').status='FAILED',d)]
];

let failures=0;
for(const [name,shouldPass,mutate] of cases){
  let passed=false,msg='';
  try{validatePublicV2(mutate(clone(canonical)));passed=true}catch(e){msg=e instanceof Error?e.message:String(e)}
  if(passed===shouldPass) console.log(`PASS  ${name}`);
  else {failures++;console.error(`FAIL  ${name}`);console.error(`      expected=${shouldPass?'PASS':'REJECT'} actual=${passed?'PASS':'REJECT'}`);if(msg)console.error(`      ${msg}`)}
}
if(failures){console.error(`GENESIS_PUBLIC_V2_TESTS_FAILED ${failures}/${cases.length}`);process.exitCode=1}
else console.log(`GENESIS_PUBLIC_V2_TESTS_PASSED ${cases.length}/${cases.length}`);
