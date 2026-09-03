#!/usr/bin/env node
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const TOP_KEYS = new Set([
  'evaluation_input_version','publication_intent','mode','source_status',
  'source_attestation','transport','publication_gates'
]);
const SOURCE_KEYS = new Set([
  'source_kind','source_identity','source_state','selected_experiment_status',
  'write_capability','browser_private_access','adapter_only'
]);
const TRANSPORT_KEYS = new Set([
  'server_side_pull_required','public_endpoint_only','fail_closed','stale_behavior',
  'max_age_seconds','snapshot_fallback_available','browser_credentials_present'
]);
const GATE_KEYS = new Set(['contract_v2','adapter','snapshot','live_read_only']);

function fail(message){ throw new Error(message); }
function obj(value,p){ if(!value || typeof value!=='object' || Array.isArray(value)) fail(`${p} doit être un objet.`); }
function exactKeys(value, allowed, p){ obj(value,p); for(const key of Object.keys(value)) if(!allowed.has(key)) fail(`${p}.${key} n'est pas autorisé.`); }
function requireKeys(value, keys, p){ for(const key of keys) if(!(key in value)) fail(`${p}.${key} est obligatoire.`); }
function eq(value, expected, p){ if(value!==expected) fail(`${p} doit être ${JSON.stringify(expected)}.`); }

function scanSensitive(value,p='$'){
  if(typeof value==='string'){
    const patterns = [
      [/-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/i,'private key'],
      [/\bghp_[A-Za-z0-9_]{20,}\b/,'GitHub token'],
      [/\bgithub_pat_[A-Za-z0-9_]{20,}\b/,'GitHub token'],
      [/\bsk-[A-Za-z0-9_-]{20,}\b/,'API key'],
      [/^[A-Za-z]:\\/,'absolute Windows path'],
      [/^\\\\/,'UNC path'],
      [/^file:\/\//i,'file URL'],
      [/https?:\/\/(?:localhost|127\.0\.0\.1)(?::\d+)?(?:\/|$)/i,'local endpoint'],
      [/https?:\/\/10\.\d+\.\d+\.\d+(?::\d+)?(?:\/|$)/i,'private IP'],
      [/https?:\/\/192\.168\.\d+\.\d+(?::\d+)?(?:\/|$)/i,'private IP'],
      [/https?:\/\/172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+(?::\d+)?(?:\/|$)/i,'private IP'],
      [/Topbrutus\/seedgenesis/i,'direct private repository reference'],
      [/refs\/heads\//i,'private branch reference'],
      [/\b[0-9a-f]{40}\b/i,'commit-like identifier']
    ];
    for(const [re,label] of patterns) if(re.test(value)) fail(`${p} contient un motif interdit (${label}).`);
    return;
  }
  if(Array.isArray(value)){ value.forEach((item,i)=>scanSensitive(item,`${p}[${i}]`)); return; }
  if(value && typeof value==='object') for(const [key,item] of Object.entries(value)) scanSensitive(item,`${p}.${key}`);
}

export function evaluateLiveReadOnlyCandidate(input){
  exactKeys(input,TOP_KEYS,'$');
  requireKeys(input,TOP_KEYS,'$');
  eq(input.evaluation_input_version,'1.0.0','$.evaluation_input_version');
  eq(input.publication_intent,'EVALUATE_ONLY_NO_ACTIVATION','$.publication_intent');
  eq(input.mode,'LIVE_READ_ONLY','$.mode');
  eq(input.source_status,'PUBLIC_READ_ONLY','$.source_status');

  exactKeys(input.source_attestation,SOURCE_KEYS,'$.source_attestation');
  requireKeys(input.source_attestation,SOURCE_KEYS,'$.source_attestation');
  const s=input.source_attestation;
  eq(s.source_kind,'PRIVATE_GENESIS_PUBLIC_PROJECTION','$.source_attestation.source_kind');
  eq(s.source_identity,'OPAQUE_PUBLIC_ATTESTATION','$.source_attestation.source_identity');
  eq(s.source_state,'C041_C060_COMPLETE_VALIDATED','$.source_attestation.source_state');
  eq(s.selected_experiment_status,'PLANNED_NOT_EXECUTED','$.source_attestation.selected_experiment_status');
  eq(s.write_capability,'NONE','$.source_attestation.write_capability');
  eq(s.browser_private_access,false,'$.source_attestation.browser_private_access');
  eq(s.adapter_only,true,'$.source_attestation.adapter_only');

  exactKeys(input.transport,TRANSPORT_KEYS,'$.transport');
  requireKeys(input.transport,TRANSPORT_KEYS,'$.transport');
  const t=input.transport;
  eq(t.server_side_pull_required,true,'$.transport.server_side_pull_required');
  eq(t.public_endpoint_only,true,'$.transport.public_endpoint_only');
  eq(t.fail_closed,true,'$.transport.fail_closed');
  eq(t.stale_behavior,'REJECT','$.transport.stale_behavior');
  if(!Number.isInteger(t.max_age_seconds) || t.max_age_seconds < 30 || t.max_age_seconds > 900) fail('$.transport.max_age_seconds doit être un entier entre 30 et 900.');
  eq(t.snapshot_fallback_available,true,'$.transport.snapshot_fallback_available');
  eq(t.browser_credentials_present,false,'$.transport.browser_credentials_present');

  exactKeys(input.publication_gates,GATE_KEYS,'$.publication_gates');
  requireKeys(input.publication_gates,GATE_KEYS,'$.publication_gates');
  eq(input.publication_gates.contract_v2,'PASSED','$.publication_gates.contract_v2');
  eq(input.publication_gates.adapter,'PASSED','$.publication_gates.adapter');
  eq(input.publication_gates.snapshot,'PASSED','$.publication_gates.snapshot');
  eq(input.publication_gates.live_read_only,'PENDING','$.publication_gates.live_read_only');

  scanSensitive(input);

  return {
    ok:true,
    decision:'READY_FOR_CONTROLLED_IMPLEMENTATION_NOT_ACTIVATED',
    public_live_enabled:false,
    live_read_only_gate:'PENDING',
    private_source_read_by_public_browser:false,
    write_capability:'NONE',
    fail_closed:true,
    stale_behavior:'REJECT',
    max_age_seconds:t.max_age_seconds,
    required_next_phase:'IMPLEMENT_SERVER_SIDE_PUBLIC_READ_ONLY_BRIDGE'
  };
}

async function main(){
  const defaultPath=fileURLToPath(new URL('./fixtures/live-public-candidate.json',import.meta.url));
  const inputPath=process.argv[2] ? path.resolve(process.argv[2]) : defaultPath;
  const input=JSON.parse(await readFile(inputPath,'utf8'));
  const result=evaluateLiveReadOnlyCandidate(input);
  const outDir=path.resolve('.build/genesis-live-read-only-evaluation');
  await mkdir(outDir,{recursive:true});
  await writeFile(path.join(outDir,'result.json'),`${JSON.stringify(result,null,2)}\n`,'utf8');
  console.log('GENESIS_LIVE_READ_ONLY_EVALUATION_VALID');
  console.log(JSON.stringify(result,null,2));
}

if(process.argv[1]===fileURLToPath(import.meta.url)){
  main().catch(error=>{ console.error(`GENESIS_LIVE_READ_ONLY_EVALUATION_FAILED: ${error.message}`); process.exit(1); });
}
