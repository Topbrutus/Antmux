#!/usr/bin/env node
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { validatePublicV2 } from '../validate-public-v2.mjs';

const TOP_KEYS = new Set(['bridge_input_version','publication_intent','bridge_received_at','source_observed_at','max_age_seconds','source_attestation','transport','public_payload']);
const SOURCE_KEYS = new Set(['source_kind','source_identity','source_state','selected_experiment_status','read_capability','write_capability','adapter_only']);
const TRANSPORT_KEYS = new Set(['server_side_pull','public_endpoint_only','fail_closed','snapshot_fallback_available','browser_credentials_present','private_browser_request']);
const PAYLOAD_KEYS = new Set(['identity','publication_gates','metrics','evidence','integrity']);
const IDENTITY_KEYS = new Set(['seed_label','root_status','root_version','continuity_policy']);

function fail(message){ throw new Error(message); }
function obj(value,label){ if(!value || typeof value!=='object' || Array.isArray(value)) fail(`${label} doit être un objet.`); }
function allowed(value, keys, label){ obj(value,label); for(const key of Object.keys(value)) if(!keys.has(key)) fail(`${label}.${key} n'est pas autorisé.`); }
function required(value, keys, label){ for(const key of keys) if(!(key in value)) fail(`${label}.${key} est obligatoire.`); }
function eq(value, expected, label){ if(value!==expected) fail(`${label} doit être ${JSON.stringify(expected)}.`); }
function clone(value){ return structuredClone(value); }
function stable(value){
  if(Array.isArray(value)) return value.map(stable);
  if(value && typeof value==='object') return Object.fromEntries(Object.keys(value).sort().map(key=>[key, stable(value[key])]));
  return value;
}

function scanSensitive(value, label='$'){
  if(typeof value==='string'){
    const patterns = [
      [/-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/i, 'private key'],
      [/\bghp_[A-Za-z0-9_]{20,}\b/, 'GitHub token'],
      [/\bgithub_pat_[A-Za-z0-9_]{20,}\b/, 'GitHub token'],
      [/\bsk-[A-Za-z0-9_-]{20,}\b/, 'API key'],
      [/^[A-Za-z]:\\/, 'absolute Windows path'],
      [/^\\\\/, 'UNC path'],
      [/^file:\/\//i, 'file URL'],
      [/https?:\/\/(?:localhost|127\.0\.0\.1)(?::\d+)?(?:\/|$)/i, 'local endpoint'],
      [/https?:\/\/10\.\d+\.\d+\.\d+(?::\d+)?(?:\/|$)/i, 'private IP'],
      [/https?:\/\/192\.168\.\d+\.\d+(?::\d+)?(?:\/|$)/i, 'private IP'],
      [/https?:\/\/172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+(?::\d+)?(?:\/|$)/i, 'private IP'],
      [/Topbrutus\/seedgenesis/i, 'direct private repository reference'],
      [/refs\/heads\//i, 'private branch reference']
    ];
    for(const [pattern, name] of patterns) if(pattern.test(value)) fail(`${label} contient un motif interdit (${name}).`);
    return;
  }
  if(Array.isArray(value)){ value.forEach((item,index)=>scanSensitive(item,`${label}[${index}]`)); return; }
  if(value && typeof value==='object') for(const [key,item] of Object.entries(value)) scanSensitive(item,`${label}.${key}`);
}

function digestProjection(payload, observedAt){
  const projection = {
    observed_at: observedAt,
    identity: payload.identity,
    publication_gates: payload.publication_gates,
    metrics: payload.metrics,
    evidence_without_hash: payload.evidence,
    integrity_checks: payload.integrity.checks
  };
  return createHash('sha256').update(JSON.stringify(stable(projection)),'utf8').digest('hex');
}

export function buildPublicReadOnlyEnvelope(input, options={}){
  allowed(input, TOP_KEYS, '$');
  required(input, TOP_KEYS, '$');
  eq(input.bridge_input_version, '1.0.0', '$.bridge_input_version');
  eq(input.publication_intent, 'SERVER_SIDE_PUBLIC_READ_ONLY_BRIDGE', '$.publication_intent');
  if(!Number.isInteger(input.max_age_seconds) || input.max_age_seconds < 30 || input.max_age_seconds > 900) fail('$.max_age_seconds doit être un entier entre 30 et 900.');

  allowed(input.source_attestation, SOURCE_KEYS, '$.source_attestation');
  required(input.source_attestation, SOURCE_KEYS, '$.source_attestation');
  eq(input.source_attestation.source_kind, 'PRIVATE_GENESIS_PUBLIC_PROJECTION', '$.source_attestation.source_kind');
  eq(input.source_attestation.source_identity, 'OPAQUE_PUBLIC_ATTESTATION', '$.source_attestation.source_identity');
  eq(input.source_attestation.source_state, 'C041_C060_COMPLETE_VALIDATED', '$.source_attestation.source_state');
  eq(input.source_attestation.selected_experiment_status, 'PLANNED_NOT_EXECUTED', '$.source_attestation.selected_experiment_status');
  eq(input.source_attestation.read_capability, 'READ_ONLY', '$.source_attestation.read_capability');
  eq(input.source_attestation.write_capability, 'NONE', '$.source_attestation.write_capability');
  eq(input.source_attestation.adapter_only, true, '$.source_attestation.adapter_only');

  allowed(input.transport, TRANSPORT_KEYS, '$.transport');
  required(input.transport, TRANSPORT_KEYS, '$.transport');
  eq(input.transport.server_side_pull, true, '$.transport.server_side_pull');
  eq(input.transport.public_endpoint_only, true, '$.transport.public_endpoint_only');
  eq(input.transport.fail_closed, true, '$.transport.fail_closed');
  eq(input.transport.snapshot_fallback_available, true, '$.transport.snapshot_fallback_available');
  eq(input.transport.browser_credentials_present, false, '$.transport.browser_credentials_present');
  eq(input.transport.private_browser_request, false, '$.transport.private_browser_request');

  allowed(input.public_payload, PAYLOAD_KEYS, '$.public_payload');
  required(input.public_payload, PAYLOAD_KEYS, '$.public_payload');
  allowed(input.public_payload.identity, IDENTITY_KEYS, '$.public_payload.identity');
  required(input.public_payload.identity, IDENTITY_KEYS, '$.public_payload.identity');

  scanSensitive(input);
  const observed = Date.parse(input.source_observed_at);
  const now = Date.parse(options.now ?? input.bridge_received_at);
  if(Number.isNaN(observed) || Number.isNaN(now)) fail('Horodatage bridge invalide.');
  const ageSeconds = Math.floor((now - observed) / 1000);
  if(ageSeconds < 0) fail('La source ne peut pas venir du futur.');
  if(ageSeconds > input.max_age_seconds) fail('Source PUBLIC_READ_ONLY périmée: fail closed.');

  const payload = clone(input.public_payload);
  const digest = digestProjection(payload, input.source_observed_at);
  payload.identity.root_digest = `PUBLIC-READ-ONLY-SHA256:${digest}`;
  payload.evidence = [
    ...payload.evidence,
    {id:'LIVE-PUBLIC-PROJECTION-HASH',type:'PUBLIC_HASH',status:'VERIFIED_PUBLIC',public_ref:'Server-side public read-only projection',hash:`sha256:${digest}`}
  ];

  const envelope = {
    contract_version: '2.0.0-draft',
    mode: 'LIVE_READ_ONLY',
    publication_id: 'GENESIS-PUBLIC-READ-ONLY-BRIDGE-0001',
    published_at: new Date(now).toISOString(),
    source_status: 'PUBLIC_READ_ONLY',
    integrity_status: 'VERIFIED_PUBLIC',
    payload
  };
  validatePublicV2(envelope);
  const liveActive = envelope.payload.publication_gates.current_gate === 'LIVE_READ_ONLY_ACTIVE';
  return {
    ok: true,
    bridge: 'SERVER_SIDE_PUBLIC_READ_ONLY',
    public_live_enabled: liveActive,
    deployment_required: !liveActive,
    snapshot_fallback_available: true,
    source_age_seconds: ageSeconds,
    envelope
  };
}

async function main(){
  const defaultPath = fileURLToPath(new URL('./fixtures/server-side-public-source.json', import.meta.url));
  const inputPath = process.argv[2] ? path.resolve(process.argv[2]) : defaultPath;
  const input = JSON.parse(await readFile(inputPath, 'utf8'));
  const result = buildPublicReadOnlyEnvelope(input);
  const outDir = path.resolve('.build/genesis-public-read-only-bridge');
  await mkdir(outDir, {recursive:true});
  await writeFile(path.join(outDir, 'public-read-only-envelope.json'), `${JSON.stringify(result.envelope,null,2)}\n`, 'utf8');
  await writeFile(path.join(outDir, 'result.json'), `${JSON.stringify({...result,envelope:undefined},null,2)}\n`, 'utf8');
  console.log('GENESIS_PUBLIC_READ_ONLY_BRIDGE_VALID');
  console.log(JSON.stringify({
    ok: result.ok,
    bridge: result.bridge,
    mode: result.envelope.mode,
    source_status: result.envelope.source_status,
    publication_id: result.envelope.publication_id,
    integrity_status: result.envelope.integrity_status,
    public_live_enabled: result.public_live_enabled,
    deployment_required: result.deployment_required,
    source_age_seconds: result.source_age_seconds
  }, null, 2));
}

if(process.argv[1] === fileURLToPath(import.meta.url)){
  main().catch(error=>{ console.error(`GENESIS_PUBLIC_READ_ONLY_BRIDGE_INVALID: ${error.message}`); process.exit(1); });
}
