#!/usr/bin/env node
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { validatePublicV2 } from '../validate-public-v2.mjs';

const TOP_KEYS = new Set(['bridge_input_version','publication_intent','bridge_received_at','source_observed_at','max_age_seconds','source_attestation','transport','live_active']);
const SOURCE_KEYS = new Set([
  'source_kind','source_identity','source_state','validated_through','c061_status','c061_execution_input',
  'execution_admissibility','next_scientific_action','selected_experiment_status','c062_status',
  'real_experiment_spec_id','real_experiment_spec_status','real_experiment_family','trial_class',
  'replicates_per_arm','blinded_primary_analysis','pretargeted_symbolic_search','real_plan_selection_performed',
  'c063_status','real_next_test_plan_id','real_next_test_plan_status','sample_count',
  'execution_bindings_required','execution_bindings_bound','execution_bindings_complete',
  'read_capability','write_capability','adapter_only',
]);
const TRANSPORT_KEYS = new Set(['server_side_pull','public_endpoint_only','fail_closed','snapshot_fallback_available','browser_credentials_present','private_browser_request']);

function fail(message) { throw new Error(message); }
function obj(value, label) { if (!value || typeof value !== 'object' || Array.isArray(value)) fail(`${label} doit être un objet.`); }
function allowed(value, keys, label) { obj(value,label); for (const key of Object.keys(value)) if (!keys.has(key)) fail(`${label}.${key} n'est pas autorisé.`); }
function required(value, keys, label) { for (const key of keys) if (!(key in value)) fail(`${label}.${key} est obligatoire.`); }
function eq(value, expected, label) { if (value !== expected) fail(`${label} doit être ${JSON.stringify(expected)}.`); }
function stable(value) { if (Array.isArray(value)) return value.map(stable); if (value && typeof value === 'object') return Object.fromEntries(Object.keys(value).sort().map(k=>[k,stable(value[k])])); return value; }

function scanSensitive(value, label = '$') {
  if (typeof value === 'string') {
    const patterns = [
      [/-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/i,'private key'],
      [/\bghp_[A-Za-z0-9_]{20,}\b/,'GitHub token'], [/\bgithub_pat_[A-Za-z0-9_]{20,}\b/,'GitHub token'],
      [/\bsk-[A-Za-z0-9_-]{20,}\b/,'API key'], [/^[A-Za-z]:\\/,'absolute Windows path'], [/^\\\\/,'UNC path'], [/^file:\/\//i,'file URL'],
      [/https?:\/\/(?:localhost|127\.0\.0\.1)(?::\d+)?(?:\/|$)/i,'local endpoint'],
      [/https?:\/\/10\.\d+\.\d+\.\d+(?::\d+)?(?:\/|$)/i,'private IP'],
      [/https?:\/\/192\.168\.\d+\.\d+(?::\d+)?(?:\/|$)/i,'private IP'],
      [/https?:\/\/172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+(?::\d+)?(?:\/|$)/i,'private IP'],
      [/Topbrutus\/seedgenesis/i,'direct private repository reference'], [/refs\/heads\//i,'private branch reference'],
      [/public\/live-source/i,'private publication branch reference'], [/public\/live\/status\.env/i,'private publication path reference'],
    ];
    for (const [pattern,name] of patterns) if (pattern.test(value)) fail(`${label} contient un motif interdit (${name}).`);
    return;
  }
  if (Array.isArray(value)) { value.forEach((item,index)=>scanSensitive(item,`${label}[${index}]`)); return; }
  if (value && typeof value === 'object') for (const [key,item] of Object.entries(value)) scanSensitive(item,`${label}.${key}`);
}
function digestPayload(payload, observedAt) { return createHash('sha256').update(JSON.stringify(stable({observed_at:observedAt,payload})),'utf8').digest('hex'); }

function validateNotApplicableC062(a) {
  eq(a.c062_status,'NOT_APPLICABLE','$.source_attestation.c062_status');
  eq(a.real_experiment_spec_id,'NOT_APPLICABLE','$.source_attestation.real_experiment_spec_id');
  eq(a.real_experiment_spec_status,'NOT_APPLICABLE','$.source_attestation.real_experiment_spec_status');
  eq(a.real_experiment_family,'NOT_APPLICABLE','$.source_attestation.real_experiment_family');
  eq(a.trial_class,'NOT_APPLICABLE','$.source_attestation.trial_class');
  eq(a.replicates_per_arm,null,'$.source_attestation.replicates_per_arm');
  eq(a.blinded_primary_analysis,null,'$.source_attestation.blinded_primary_analysis');
  eq(a.pretargeted_symbolic_search,null,'$.source_attestation.pretargeted_symbolic_search');
  eq(a.real_plan_selection_performed,null,'$.source_attestation.real_plan_selection_performed');
}
function validateNotApplicableC063(a) {
  eq(a.c063_status,'NOT_APPLICABLE','$.source_attestation.c063_status');
  eq(a.real_next_test_plan_id,'NOT_APPLICABLE','$.source_attestation.real_next_test_plan_id');
  eq(a.real_next_test_plan_status,'NOT_APPLICABLE','$.source_attestation.real_next_test_plan_status');
  eq(a.sample_count,null,'$.source_attestation.sample_count');
  eq(a.execution_bindings_required,null,'$.source_attestation.execution_bindings_required');
  eq(a.execution_bindings_bound,null,'$.source_attestation.execution_bindings_bound');
  eq(a.execution_bindings_complete,null,'$.source_attestation.execution_bindings_complete');
}
function validateC062Fields(a) {
  eq(a.c062_status,'VALIDATED_10_OF_10','$.source_attestation.c062_status');
  eq(a.real_experiment_spec_id,'REAL-EXPERIMENT-SPEC-001','$.source_attestation.real_experiment_spec_id');
  eq(a.real_experiment_spec_status,'FROZEN_CANDIDATE_NOT_SELECTED','$.source_attestation.real_experiment_spec_status');
  eq(a.real_experiment_family,'BLIND_MULTILINGUAL_GESIS_COMPARISON','$.source_attestation.real_experiment_family');
  eq(a.trial_class,'PILOT_COMPARATIVE_NOT_CONFIRMATORY','$.source_attestation.trial_class');
  eq(a.replicates_per_arm,3,'$.source_attestation.replicates_per_arm');
  eq(a.blinded_primary_analysis,true,'$.source_attestation.blinded_primary_analysis');
  eq(a.pretargeted_symbolic_search,false,'$.source_attestation.pretargeted_symbolic_search');
}

function validateAttestation(a) {
  allowed(a,SOURCE_KEYS,'$.source_attestation'); required(a,SOURCE_KEYS,'$.source_attestation');
  eq(a.source_kind,'PRIVATE_GENESIS_PUBLIC_PROJECTION','$.source_attestation.source_kind');
  eq(a.source_identity,'OPAQUE_PUBLIC_ATTESTATION','$.source_attestation.source_identity');
  eq(a.selected_experiment_status,'PLANNED_NOT_EXECUTED','$.source_attestation.selected_experiment_status');
  eq(a.read_capability,'READ_ONLY','$.source_attestation.read_capability'); eq(a.write_capability,'NONE','$.source_attestation.write_capability'); eq(a.adapter_only,true,'$.source_attestation.adapter_only');
  if (a.validated_through === 'C060') {
    eq(a.source_state,'C041_C060_COMPLETE_VALIDATED','$.source_attestation.source_state');
    eq(a.c061_status,'NOT_APPLICABLE','$.source_attestation.c061_status'); eq(a.c061_execution_input,'NOT_APPLICABLE','$.source_attestation.c061_execution_input');
    eq(a.execution_admissibility,'NOT_APPLICABLE','$.source_attestation.execution_admissibility'); eq(a.next_scientific_action,'AWAIT_EXPLICIT_NEW_PHASE','$.source_attestation.next_scientific_action');
    validateNotApplicableC062(a); validateNotApplicableC063(a); return;
  }
  if (a.validated_through === 'C061') {
    eq(a.source_state,'C041_C061_COMPLETE_VALIDATED','$.source_attestation.source_state');
    eq(a.c061_status,'VALIDATED_10_OF_10','$.source_attestation.c061_status'); eq(a.c061_execution_input,'SYNTHETIC_C060_FIXTURE','$.source_attestation.c061_execution_input');
    eq(a.execution_admissibility,'BLOCKED_SYNTHETIC_SELECTION','$.source_attestation.execution_admissibility'); eq(a.next_scientific_action,'AWAIT_REAL_EXPERIMENT_SPEC','$.source_attestation.next_scientific_action');
    validateNotApplicableC062(a); validateNotApplicableC063(a); return;
  }
  if (a.validated_through === 'C062') {
    eq(a.source_state,'C041_C062_COMPLETE_VALIDATED','$.source_attestation.source_state');
    eq(a.c061_status,'VALIDATED_10_OF_10','$.source_attestation.c061_status'); eq(a.c061_execution_input,'SYNTHETIC_C060_FIXTURE','$.source_attestation.c061_execution_input');
    eq(a.execution_admissibility,'BLOCKED_SYNTHETIC_SELECTION','$.source_attestation.execution_admissibility'); eq(a.next_scientific_action,'BUILD_REAL_NEXT_TEST_PLAN','$.source_attestation.next_scientific_action');
    validateC062Fields(a); eq(a.real_plan_selection_performed,false,'$.source_attestation.real_plan_selection_performed'); validateNotApplicableC063(a); return;
  }
  if (a.validated_through === 'C063') {
    eq(a.source_state,'C041_C063_COMPLETE_VALIDATED','$.source_attestation.source_state');
    eq(a.c061_status,'VALIDATED_10_OF_10','$.source_attestation.c061_status'); eq(a.c061_execution_input,'SYNTHETIC_C060_FIXTURE','$.source_attestation.c061_execution_input');
    eq(a.execution_admissibility,'BLOCKED_MISSING_EXECUTION_BINDINGS','$.source_attestation.execution_admissibility'); eq(a.next_scientific_action,'BIND_REAL_EXECUTION_CONTRACT','$.source_attestation.next_scientific_action');
    validateC062Fields(a); eq(a.real_plan_selection_performed,true,'$.source_attestation.real_plan_selection_performed');
    eq(a.c063_status,'VALIDATED_10_OF_10','$.source_attestation.c063_status'); eq(a.real_next_test_plan_id,'REAL-NEXT-TEST-PLAN-001','$.source_attestation.real_next_test_plan_id');
    eq(a.real_next_test_plan_status,'FROZEN_PLAN_AWAITING_EXECUTION_BINDINGS','$.source_attestation.real_next_test_plan_status');
    eq(a.sample_count,12,'$.source_attestation.sample_count'); eq(a.execution_bindings_required,11,'$.source_attestation.execution_bindings_required');
    eq(a.execution_bindings_bound,0,'$.source_attestation.execution_bindings_bound'); eq(a.execution_bindings_complete,false,'$.source_attestation.execution_bindings_complete'); return;
  }
  fail('$.source_attestation.validated_through non autorisé.');
}

export function buildProgressivePublicEnvelope(input, options = {}) {
  allowed(input,TOP_KEYS,'$'); required(input,TOP_KEYS,'$');
  eq(input.bridge_input_version,'2.0.0','$.bridge_input_version'); eq(input.publication_intent,'SERVER_SIDE_PUBLIC_READ_ONLY_PROGRESSIVE_BRIDGE','$.publication_intent');
  if (!Number.isInteger(input.max_age_seconds) || input.max_age_seconds < 30 || input.max_age_seconds > 900) fail('$.max_age_seconds doit être entre 30 et 900.');
  if (typeof input.live_active !== 'boolean') fail('$.live_active doit être booléen.');
  validateAttestation(input.source_attestation);
  allowed(input.transport,TRANSPORT_KEYS,'$.transport'); required(input.transport,TRANSPORT_KEYS,'$.transport');
  eq(input.transport.server_side_pull,true,'$.transport.server_side_pull'); eq(input.transport.public_endpoint_only,true,'$.transport.public_endpoint_only');
  eq(input.transport.fail_closed,true,'$.transport.fail_closed'); eq(input.transport.snapshot_fallback_available,true,'$.transport.snapshot_fallback_available');
  eq(input.transport.browser_credentials_present,false,'$.transport.browser_credentials_present'); eq(input.transport.private_browser_request,false,'$.transport.private_browser_request');
  scanSensitive(input);
  const observed=Date.parse(input.source_observed_at); const now=Date.parse(options.now ?? input.bridge_received_at);
  if (Number.isNaN(observed)||Number.isNaN(now)) fail('Horodatage bridge invalide.');
  const ageSeconds=Math.floor((now-observed)/1000); if(ageSeconds<0) fail('La source ne peut pas venir du futur.'); if(ageSeconds>input.max_age_seconds) fail('Source progressive périmée: fail closed.');

  const a=input.source_attestation; const liveActive=input.live_active;
  const metrics=[
    {id:'genesis003-validated-through',label:'GENESIS-003 validé jusqu’à',value:a.validated_through,status:'VERIFIED_PUBLIC',provenance_ref:'SERVER-SIDE-WHITELIST-V2'},
    {id:'genesis003-c041-c060',label:'GENESIS-003 C041–C060',value:'COMPLETE_VALIDATED',status:'VERIFIED_PUBLIC',provenance_ref:'SERVER-SIDE-WHITELIST-V2'},
    {id:'selected-experiment-status',label:'État du test sélectionné',value:a.selected_experiment_status,status:'VERIFIED_PUBLIC',provenance_ref:'SERVER-SIDE-WHITELIST-V2'},
  ];
  if (['C061','C062','C063'].includes(a.validated_through)) metrics.push(
    {id:'genesis003-c061',label:'C061 · admissibilité d’exécution',value:a.c061_status,status:'VERIFIED_PUBLIC',provenance_ref:'SERVER-SIDE-WHITELIST-V2'},
    {id:'c061-execution-input',label:'Entrée d’exécution C061',value:a.c061_execution_input,status:'VERIFIED_PUBLIC',provenance_ref:'SERVER-SIDE-WHITELIST-V2'},
    {id:'execution-admissibility',label:'Gate d’exécution',value:a.execution_admissibility,status:'VERIFIED_PUBLIC',provenance_ref:'SERVER-SIDE-WHITELIST-V2'},
    {id:'next-scientific-action',label:'Prochaine action scientifique',value:a.next_scientific_action,status:'VERIFIED_PUBLIC',provenance_ref:'SERVER-SIDE-WHITELIST-V2'},
  );
  if (['C062','C063'].includes(a.validated_through)) metrics.push(
    {id:'genesis003-c062',label:'C062 · spécification réelle',value:a.c062_status,status:'VERIFIED_PUBLIC',provenance_ref:'SERVER-SIDE-WHITELIST-V2'},
    {id:'real-experiment-spec-id',label:'Expérience réelle candidate',value:a.real_experiment_spec_id,status:'VERIFIED_PUBLIC',provenance_ref:'SERVER-SIDE-WHITELIST-V2'},
    {id:'real-experiment-spec-status',label:'État de la spécification',value:a.real_experiment_spec_status,status:'VERIFIED_PUBLIC',provenance_ref:'SERVER-SIDE-WHITELIST-V2'},
    {id:'real-experiment-family',label:'Famille expérimentale',value:a.real_experiment_family,status:'VERIFIED_PUBLIC',provenance_ref:'SERVER-SIDE-WHITELIST-V2'},
    {id:'trial-class',label:'Classe d’essai',value:a.trial_class,status:'VERIFIED_PUBLIC',provenance_ref:'SERVER-SIDE-WHITELIST-V2'},
    {id:'replicates-per-arm',label:'Répétitions par condition',value:a.replicates_per_arm,status:'VERIFIED_PUBLIC',provenance_ref:'SERVER-SIDE-WHITELIST-V2'},
    {id:'blinded-primary-analysis',label:'Analyse primaire aveugle',value:a.blinded_primary_analysis,status:'VERIFIED_PUBLIC',provenance_ref:'SERVER-SIDE-WHITELIST-V2'},
    {id:'pretargeted-symbolic-search',label:'Recherche symbolique pré-ciblée',value:a.pretargeted_symbolic_search,status:'VERIFIED_PUBLIC',provenance_ref:'SERVER-SIDE-WHITELIST-V2'},
    {id:'real-plan-selection-performed',label:'Plan réel sélectionné',value:a.real_plan_selection_performed,status:'VERIFIED_PUBLIC',provenance_ref:'SERVER-SIDE-WHITELIST-V2'},
  );
  if (a.validated_through === 'C063') metrics.push(
    {id:'genesis003-c063',label:'C063 · plan réel suivant',value:a.c063_status,status:'VERIFIED_PUBLIC',provenance_ref:'SERVER-SIDE-WHITELIST-V2'},
    {id:'real-next-test-plan-id',label:'Plan réel sélectionné',value:a.real_next_test_plan_id,status:'VERIFIED_PUBLIC',provenance_ref:'SERVER-SIDE-WHITELIST-V2'},
    {id:'real-next-test-plan-status',label:'État du plan réel',value:a.real_next_test_plan_status,status:'VERIFIED_PUBLIC',provenance_ref:'SERVER-SIDE-WHITELIST-V2'},
    {id:'real-next-test-sample-count',label:'Échantillons planifiés',value:a.sample_count,status:'VERIFIED_PUBLIC',provenance_ref:'SERVER-SIDE-WHITELIST-V2'},
    {id:'execution-bindings-required',label:'Bindings requis',value:a.execution_bindings_required,status:'VERIFIED_PUBLIC',provenance_ref:'SERVER-SIDE-WHITELIST-V2'},
    {id:'execution-bindings-bound',label:'Bindings renseignés',value:a.execution_bindings_bound,status:'VERIFIED_PUBLIC',provenance_ref:'SERVER-SIDE-WHITELIST-V2'},
    {id:'execution-bindings-complete',label:'Bindings complets',value:a.execution_bindings_complete,status:'VERIFIED_PUBLIC',provenance_ref:'SERVER-SIDE-WHITELIST-V2'},
  );
  metrics.push(
    {id:'hypothesis-selection',label:'Hypothèse sélectionnée',value:false,status:'VERIFIED_PUBLIC',provenance_ref:'SERVER-SIDE-WHITELIST-V2'},
    {id:'hypothesis-ranking',label:'Classement d’hypothèses',value:false,status:'VERIFIED_PUBLIC',provenance_ref:'SERVER-SIDE-WHITELIST-V2'},
    {id:'probabilities-produced',label:'Probabilités produites',value:false,status:'VERIFIED_PUBLIC',provenance_ref:'SERVER-SIDE-WHITELIST-V2'},
    {id:'bridge-read-capability',label:'Capacité de lecture bridge',value:'READ_ONLY',status:'VERIFIED_PUBLIC',provenance_ref:'SERVER-SIDE-WHITELIST-V2'},
    {id:'bridge-write-capability',label:'Capacité d’écriture bridge',value:'NONE',status:'VERIFIED_PUBLIC',provenance_ref:'SERVER-SIDE-WHITELIST-V2'},
    {id:'browser-private-credentials',label:'Credentials privés navigateur',value:false,status:'VERIFIED_PUBLIC',provenance_ref:'SERVER-SIDE-WHITELIST-V2'},
    {id:'public-live-active',label:'Publication LIVE active',value:liveActive,status:'VERIFIED_PUBLIC',provenance_ref:'SERVER-SIDE-WHITELIST-V2'},
  );

  const payload={
    identity:{seed_label:'Genesis',root_status:'PRESERVED_AT_SOURCE_VALIDATION',root_version:`GENESIS-003-${a.validated_through}-PUBLIC-PROGRESS-v2`,continuity_policy:'PRIVATE_ROOT_NOT_EXPOSED; PUBLIC_PROJECTION_ONLY'},
    publication_gates:{current_gate:liveActive?'LIVE_READ_ONLY_ACTIVE':'LIVE_READ_ONLY_BRIDGE_READY_NOT_DEPLOYED',recommended_next_step:liveActive?'CONTINUE_SERVER_SIDE_READ_ONLY_SYNC':'AUTHORIZE_CONTROLLED_PUBLIC_READ_ONLY_DEPLOYMENT',gates:[
      {id:'contract-v2',label:'Contrat public v2',status:'PASSED'},{id:'adapter',label:'Genesis Public Adapter',status:'PASSED'},
      {id:'snapshot',label:'Snapshot public figé',status:'PASSED'},{id:'live-read-only',label:'Bridge serveur lecture seule',status:'PASSED'},
    ]},
    metrics,
    evidence:[{id:'SERVER-SIDE-WHITELIST-V2',type:'PUBLIC_ATTESTATION',status:'VERIFIED_PUBLIC',public_ref:'Whitelisted progressive Genesis status projection'}],
    integrity:{status:'VERIFIED_PUBLIC',checks:[
      {id:'live-public-projection-hash',status:'PASSED',public_ref:'PUBLIC-READ-ONLY-SHA256'},
      {id:'live-server-side-only',status:'PASSED',public_ref:'Browser has no private source access'},
      {id:'live-write-capability-none',status:'PASSED',public_ref:'Bridge exposes no write capability'},
      {id:'live-freshness-window',status:'PASSED',public_ref:'Stale source is rejected'},
    ]},
  };
  const digest=digestPayload(payload,input.source_observed_at);
  payload.identity.root_digest=`PUBLIC-READ-ONLY-SHA256:${digest}`;
  payload.evidence.push({id:'LIVE-PUBLIC-PROJECTION-HASH',type:'PUBLIC_HASH',status:'VERIFIED_PUBLIC',public_ref:'Server-side progressive public read-only projection',hash:`sha256:${digest}`});
  const envelope={contract_version:'2.0.0-draft',mode:'LIVE_READ_ONLY',publication_id:'GENESIS-PUBLIC-READ-ONLY-PROGRESSIVE-0002',published_at:new Date(now).toISOString(),source_status:'PUBLIC_READ_ONLY',integrity_status:'VERIFIED_PUBLIC',payload};
  validatePublicV2(envelope); scanSensitive(envelope); return {envelope,sourceAgeSeconds:ageSeconds};
}

async function main() {
  const inputPath=process.argv[2]; if(!inputPath) fail('Usage: bridge-public-progressive.mjs <bridge-input.json>');
  const input=JSON.parse(await readFile(path.resolve(inputPath),'utf8')); const result=buildProgressivePublicEnvelope(input);
  const outDir=path.resolve('.build/genesis-public-read-only-bridge'); await mkdir(outDir,{recursive:true});
  await writeFile(path.join(outDir,'public-read-only-envelope.json'),`${JSON.stringify(result.envelope,null,2)}\n`,'utf8');
  console.log('GENESIS_PROGRESSIVE_PUBLIC_READ_ONLY_BRIDGE_VALID');
  console.log(JSON.stringify({mode:result.envelope.mode,source_status:result.envelope.source_status,integrity_status:result.envelope.integrity_status,validated_through:result.envelope.payload.metrics.find(x=>x.id==='genesis003-validated-through')?.value,public_live_active:result.envelope.payload.metrics.find(x=>x.id==='public-live-active')?.value},null,2));
}
if (process.argv[1]===fileURLToPath(import.meta.url)) main().catch(error=>{console.error(`GENESIS_PROGRESSIVE_PUBLIC_READ_ONLY_BRIDGE_INVALID: ${error.message}`);process.exit(1);});
