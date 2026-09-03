#!/usr/bin/env node
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { buildPublicReadOnlyEnvelope } from './bridge-public-read-only.mjs';
import { validatePublicV2 } from '../validate-public-v2.mjs';

const fixturePath = fileURLToPath(new URL('./fixtures/server-side-public-source.json', import.meta.url));
const snapshotPath = fileURLToPath(new URL('../snapshot/genesis-public-snapshot-0001.json', import.meta.url));
const indexPath = fileURLToPath(new URL('../index.html', import.meta.url));
const fixture = JSON.parse(await readFile(fixturePath, 'utf8'));
const clone = () => structuredClone(fixture);
let passed = 0;

function pass(name){ passed++; console.log(`PASS  ${name}`); }
async function expectPass(name, fn){ try{ await fn(); pass(name); }catch(error){ console.error(`FAIL  ${name}: ${error.message}`); process.exitCode = 1; } }
function expectFail(name, mutate){ const value=clone(); mutate(value); try{ buildPublicReadOnlyEnvelope(value); console.error(`FAIL  ${name}: accepted unexpectedly`); process.exitCode = 1; }catch{ pass(name); } }

await expectPass('canonical server-side bridge creates PUBLIC_READ_ONLY envelope without deployment activation', () => {
  const result = buildPublicReadOnlyEnvelope(clone());
  if(!result.ok) throw new Error('ok=false');
  if(result.public_live_enabled !== false || result.deployment_required !== true) throw new Error('activation flags incorrect');
  if(result.envelope.mode !== 'LIVE_READ_ONLY' || result.envelope.source_status !== 'PUBLIC_READ_ONLY') throw new Error('wrong public envelope mode');
  validatePublicV2(result.envelope);
});

expectFail('unknown top-level source field is rejected', x => { x.private_payload = {}; });
expectFail('write capability is rejected', x => { x.source_attestation.write_capability = 'READ_WRITE'; });
expectFail('read capability must be READ_ONLY', x => { x.source_attestation.read_capability = 'WRITE_ONLY'; });
expectFail('adapter-only attestation is mandatory', x => { x.source_attestation.adapter_only = false; });
expectFail('browser private request is rejected', x => { x.transport.private_browser_request = true; });
expectFail('browser credentials are rejected', x => { x.transport.browser_credentials_present = true; });
expectFail('server-side pull is mandatory', x => { x.transport.server_side_pull = false; });
expectFail('public endpoint boundary is mandatory', x => { x.transport.public_endpoint_only = false; });
expectFail('fail closed is mandatory', x => { x.transport.fail_closed = false; });
expectFail('snapshot fallback remains mandatory', x => { x.transport.snapshot_fallback_available = false; });
expectFail('stale source is rejected', x => { x.bridge_received_at = '2026-09-03T07:30:01Z'; });
expectFail('future source is rejected', x => { x.source_observed_at = '2026-09-03T07:25:00Z'; });
expectFail('max age cannot exceed 900 seconds', x => { x.max_age_seconds = 901; });
expectFail('max age cannot be below 30 seconds', x => { x.max_age_seconds = 29; });
expectFail('direct private repository reference is rejected', x => { x.source_attestation.source_identity = 'https://github.com/Topbrutus/seedgenesis'; });
expectFail('private branch reference is rejected', x => { x.source_attestation.source_identity = 'refs/heads/private-live'; });
expectFail('private Windows path is rejected', x => { x.public_payload.evidence[0].public_ref = 'D:\\private\\genesis.json'; });
expectFail('token-shaped public field is rejected', x => { x.public_payload.metrics[0].value = 'ghp_123456789012345678901234567890'; });
expectFail('unknown payload category is rejected', x => { x.public_payload.private_root = {}; });
expectFail('identity cannot provide its own root digest', x => { x.public_payload.identity.root_digest = 'PRIVATE-DIGEST'; });

await expectPass('canonical snapshot remains fallback with LIVE_READ_ONLY PENDING', async () => {
  const snapshot = JSON.parse(await readFile(snapshotPath, 'utf8'));
  const liveGate = snapshot.payload?.publication_gates?.gates?.find(g => g.id === 'live-read-only');
  if(snapshot.mode !== 'SNAPSHOT' || snapshot.source_status !== 'PUBLIC_SNAPSHOT' || liveGate?.status !== 'PENDING') throw new Error('snapshot fallback changed');
});

await expectPass('Vision Center consumes only guarded public LIVE with mandatory frozen snapshot fallback', async () => {
  const index = await readFile(indexPath, 'utf8');
  if(!index.includes("const LIVE_PATH='./live/public-read-only.json'")) throw new Error('public LIVE endpoint missing');
  if(!index.includes("const SNAPSHOT_PATH='./snapshot/genesis-public-snapshot-0001.json'")) throw new Error('snapshot fallback missing');
  if(!index.includes("d.payload.publication_gates?.current_gate!=='LIVE_READ_ONLY_ACTIVE'")) throw new Error('active gate guard missing');
  if(!index.includes("x=>x.id==='public-live-active'")) throw new Error('active metric guard missing');
  if(!index.includes('activeMetric?.value!==true')) throw new Error('active metric value guard missing');
  if(index.includes('GENESIS-PUBLIC-READ-ONLY-BRIDGE-0001')) throw new Error('bridge publication hard-coded into cockpit');
  if(index.includes('Topbrutus/seedgenesis') || index.includes('git@github.com:Topbrutus/seedgenesis.git')) throw new Error('private source leaked into cockpit');
});

const expected = 23;
if(process.exitCode) process.exit(process.exitCode);
if(passed !== expected){ console.error(`FAIL  expected ${expected} passes, got ${passed}`); process.exit(1); }
console.log(`GENESIS_PUBLIC_READ_ONLY_BRIDGE_TESTS_PASSED ${passed}/${expected}`);
