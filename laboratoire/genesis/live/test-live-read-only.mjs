#!/usr/bin/env node
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { evaluateLiveReadOnlyCandidate } from './evaluate-live-read-only.mjs';
import { adaptPublicCandidate } from '../adapter/public-adapter.mjs';

const fixturePath=fileURLToPath(new URL('./fixtures/live-public-candidate.json',import.meta.url));
const snapshotPath=fileURLToPath(new URL('../snapshot/genesis-public-snapshot-0001.json',import.meta.url));
const indexPath=fileURLToPath(new URL('../index.html',import.meta.url));
const fixture=JSON.parse(await readFile(fixturePath,'utf8'));
const clone=()=>structuredClone(fixture);
let passed=0;

function pass(name){ passed++; console.log(`PASS  ${name}`); }
function expectPass(name,fn){ try{ const result=fn(); if(!result?.ok) throw new Error('ok=false'); pass(name); }catch(error){ console.error(`FAIL  ${name}: ${error.message}`); process.exitCode=1; } }
function expectFail(name,mutate){ const value=clone(); mutate(value); try{ evaluateLiveReadOnlyCandidate(value); console.error(`FAIL  ${name}: accepted unexpectedly`); process.exitCode=1; }catch{ pass(name); } }

expectPass('canonical evaluation candidate is eligible but not activated',()=>{
  const result=evaluateLiveReadOnlyCandidate(clone());
  if(result.decision!=='READY_FOR_CONTROLLED_IMPLEMENTATION_NOT_ACTIVATED') throw new Error('wrong decision');
  if(result.public_live_enabled!==false || result.live_read_only_gate!=='PENDING') throw new Error('live accidentally enabled');
  return result;
});

try{
  adaptPublicCandidate({mode:'LIVE_READ_ONLY'});
  console.error('FAIL  production Public Adapter must still block LIVE_READ_ONLY');
  process.exitCode=1;
}catch{ pass('production Public Adapter still blocks LIVE_READ_ONLY'); }

expectFail('live gate cannot be PASSED during evaluation',x=>{x.publication_gates.live_read_only='PASSED'});
expectFail('write capability must remain NONE',x=>{x.source_attestation.write_capability='READ_WRITE'});
expectFail('browser cannot access private source',x=>{x.source_attestation.browser_private_access=true});
expectFail('source must remain adapter-only',x=>{x.source_attestation.adapter_only=false});
expectFail('server-side bridge is mandatory',x=>{x.transport.server_side_pull_required=false});
expectFail('public endpoint boundary is mandatory',x=>{x.transport.public_endpoint_only=false});
expectFail('fail-closed behavior is mandatory',x=>{x.transport.fail_closed=false});
expectFail('stale data must be rejected',x=>{x.transport.stale_behavior='SERVE_STALE'});
expectFail('freshness window cannot exceed 900 seconds',x=>{x.transport.max_age_seconds=901});
expectFail('freshness window cannot be below 30 seconds',x=>{x.transport.max_age_seconds=29});
expectFail('browser credentials are forbidden',x=>{x.transport.browser_credentials_present=true});
expectFail('snapshot fallback must remain available',x=>{x.transport.snapshot_fallback_available=false});
expectFail('direct private repository reference is rejected',x=>{x.source_attestation.source_identity='https://github.com/Topbrutus/seedgenesis'});
expectFail('private branch reference is rejected',x=>{x.source_attestation.source_identity='refs/heads/private-live'});
expectFail('token-shaped data is rejected',x=>{x.source_attestation.source_identity='ghp_123456789012345678901234567890'});
expectFail('unknown top-level field is rejected',x=>{x.private_payload={}});
expectFail('source state cannot silently change',x=>{x.source_attestation.source_state='UNKNOWN'});
expectFail('selected experiment cannot be relabelled executed',x=>{x.source_attestation.selected_experiment_status='EXECUTED'});
expectFail('adapter gate must already be PASSED',x=>{x.publication_gates.adapter='PENDING'});

const snapshot=JSON.parse(await readFile(snapshotPath,'utf8'));
const liveGate=snapshot.payload?.publication_gates?.gates?.find(g=>g.id==='live-read-only');
if(snapshot.mode==='SNAPSHOT' && snapshot.source_status==='PUBLIC_SNAPSHOT' && liveGate?.status==='PENDING') pass('canonical deployed-source snapshot remains SNAPSHOT with live gate PENDING');
else { console.error('FAIL  canonical snapshot boundary changed'); process.exitCode=1; }

const index=await readFile(indexPath,'utf8');
if(index.includes("const DATA_PATH='./snapshot/genesis-public-snapshot-0001.json'") && index.includes('LIVE_READ_ONLY') && index.includes('PENDING')) pass('Vision Center source remains the frozen snapshot during evaluation');
else { console.error('FAIL  Vision Center appears to have been switched away from frozen snapshot'); process.exitCode=1; }

const expected=23;
if(process.exitCode) process.exit(process.exitCode);
if(passed!==expected){ console.error(`FAIL  expected ${expected} passes, got ${passed}`); process.exit(1); }
console.log(`GENESIS_LIVE_READ_ONLY_TESTS_PASSED ${passed}/${expected}`);
