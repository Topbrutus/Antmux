#!/usr/bin/env node
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

const EXPECTED_CONTRACT = '2.0.0-draft';
const TOP_LEVEL = new Set(['contract_version','mode','publication_id','published_at','source_status','integrity_status','payload']);
const PAYLOAD = new Set(['identity','continuity','metacognition','pipeline','training_field','observatory','publication_gates','metrics','evidence','integrity']);
const SNAPSHOT_REQUIRED = ['identity','publication_gates','metrics','evidence','integrity'];
const LIVE_REQUIRED = ['identity','publication_gates','metrics','evidence','integrity'];
const PIPELINE_STATUSES = new Set(['PENDING','RUNNING_PUBLIC','PASSED','FAILED','REJECTED','NOT_APPLICABLE']);
const CHECK_STATUSES = new Set(['PASSED','FAILED','NOT_RUN','NOT_APPLICABLE']);
const SEMANTIC_CLASSES = new Set(['MEASURED','DERIVED','INTERPRETED','HYPOTHESIS','UNKNOWN']);
const INTEGRITY_STATUSES = new Set(['NOT_APPLICABLE','UNVERIFIED','VERIFIED_PUBLIC','FAILED_PUBLIC_CHECK']);
const COMPLETE_CYCLE_IDS = [
  'demo-step-source',
  'demo-step-descent',
  'demo-step-zero',
  'demo-step-formation',
  'demo-step-exploration',
  'demo-step-validation',
  'demo-step-return'
];

function fail(m){throw new Error(m)}
function obj(v,p){if(!v||typeof v!=='object'||Array.isArray(v))fail(`${p} doit être un objet.`)}
function str(v,p){if(typeof v!=='string'||v.length===0)fail(`${p} doit être une chaîne non vide.`)}
function int(v,p){if(!Number.isInteger(v)||v<0)fail(`${p} doit être un entier >= 0.`)}
function allowed(o,set,p){for(const k of Object.keys(o))if(!set.has(k))fail(`${p}.${k} n'est pas autorisé.`)}
function required(o,keys,p){for(const k of keys)if(!(k in o))fail(`${p}.${k} est obligatoire.`)}
function primitive(v,p){const t=typeof v;if(!['string','number','boolean'].includes(t)||(t==='number'&&!Number.isFinite(v)))fail(`${p} doit être une valeur publique primitive finie.`)}

function sensitive(v,p){
  if(typeof v!=='string')return;
  const patterns=[
    [/-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/i,'clé privée'],
    [/\bghp_[A-Za-z0-9_]{20,}\b/,'token GitHub'],
    [/\bgithub_pat_[A-Za-z0-9_]{20,}\b/,'token GitHub'],
    [/\bsk-[A-Za-z0-9_-]{20,}\b/,'clé API'],
    [/^[A-Za-z]:\\/,'chemin Windows absolu'],
    [/^\\\\/,'chemin UNC'],
    [/^file:\/\//i,'file URL'],
    [/https?:\/\/(?:localhost|127\.0\.0\.1)(?::\d+)?(?:\/|$)/i,'endpoint local'],
    [/https?:\/\/10\.\d+\.\d+\.\d+(?::\d+)?(?:\/|$)/i,'IP privée'],
    [/https?:\/\/192\.168\.\d+\.\d+(?::\d+)?(?:\/|$)/i,'IP privée'],
    [/https?:\/\/172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+(?::\d+)?(?:\/|$)/i,'IP privée']
  ];
  for(const [re,label] of patterns)if(re.test(v))fail(`${p} contient un motif interdit (${label}).`);
}
function scan(v,p='$'){
  if(typeof v==='string'){sensitive(v,p);return}
  if(Array.isArray(v)){v.forEach((x,i)=>scan(x,`${p}[${i}]`));return}
  if(v&&typeof v==='object')for(const [k,x] of Object.entries(v))scan(x,`${p}.${k}`);
}

function identity(v){
  obj(v,'$.payload.identity');const a=new Set(['seed_label','root_status','root_version','root_digest','continuity_policy']);
  allowed(v,a,'$.payload.identity');required(v,a,'$.payload.identity');for(const k of a)str(v[k],`$.payload.identity.${k}`);
}
function continuity(v){
  obj(v,'$.payload.continuity');const a=new Set(['cycle','previous_checkpoint_ref','current_checkpoint_ref','parent_link_status','root_identity_status','accepted_candidates','rejected_candidates','return_status']);
  allowed(v,a,'$.payload.continuity');required(v,a,'$.payload.continuity');int(v.cycle,'$.payload.continuity.cycle');int(v.accepted_candidates,'$.payload.continuity.accepted_candidates');int(v.rejected_candidates,'$.payload.continuity.rejected_candidates');
  for(const k of ['previous_checkpoint_ref','current_checkpoint_ref','parent_link_status','root_identity_status','return_status'])str(v[k],`$.payload.continuity.${k}`);
}
function meta(v){
  obj(v,'$.payload.metacognition');const a=new Set(['status','competing_hypotheses','uncertainty','next_test','rationale','c041_c060_status']);
  allowed(v,a,'$.payload.metacognition');required(v,a,'$.payload.metacognition');int(v.competing_hypotheses,'$.payload.metacognition.competing_hypotheses');
  for(const k of ['status','uncertainty','next_test','rationale','c041_c060_status'])str(v[k],`$.payload.metacognition.${k}`);
}
function pipeline(v){
  obj(v,'$.payload.pipeline');allowed(v,new Set(['steps']),'$.payload.pipeline');required(v,['steps'],'$.payload.pipeline');if(!Array.isArray(v.steps))fail('$.payload.pipeline.steps doit être une liste.');
  v.steps.forEach((s,i)=>{const p=`$.payload.pipeline.steps[${i}]`;obj(s,p);allowed(s,new Set(['id','label','status']),p);required(s,['id','label','status'],p);str(s.id,`${p}.id`);str(s.label,`${p}.label`);if(!PIPELINE_STATUSES.has(s.status))fail(`${p}.status invalide.`)});
}
function observations(v){
  obj(v,'$.payload.training_field');allowed(v,new Set(['label','purpose','observations']),'$.payload.training_field');required(v,['label','purpose','observations'],'$.payload.training_field');str(v.label,'$.payload.training_field.label');str(v.purpose,'$.payload.training_field.purpose');
  if(!Array.isArray(v.observations))fail('$.payload.training_field.observations doit être une liste.');
  v.observations.forEach((x,i)=>{const p=`$.payload.training_field.observations[${i}]`;obj(x,p);const a=new Set(['id','label','value','unit','semantic_class','status','provenance_ref']);allowed(x,a,p);required(x,['id','label','value','semantic_class','status','provenance_ref'],p);str(x.id,`${p}.id`);str(x.label,`${p}.label`);primitive(x.value,`${p}.value`);if(x.unit!==null&&'unit'in x)str(x.unit,`${p}.unit`);if(!SEMANTIC_CLASSES.has(x.semantic_class))fail(`${p}.semantic_class invalide.`);str(x.status,`${p}.status`);str(x.provenance_ref,`${p}.provenance_ref`)});
}
function observatory(v){
  obj(v,'$.payload.observatory');const a=new Set(['label','mode','fft_status','latest_export_ref','peak_count','episode_count','block_score_status','scientific_rule']);allowed(v,a,'$.payload.observatory');required(v,a,'$.payload.observatory');
  for(const k of ['label','mode','fft_status','latest_export_ref','block_score_status','scientific_rule'])str(v[k],`$.payload.observatory.${k}`);int(v.peak_count,'$.payload.observatory.peak_count');int(v.episode_count,'$.payload.observatory.episode_count');
  if(v.scientific_rule!=='MESURE != INTERPRÉTATION')fail('$.payload.observatory.scientific_rule doit préserver MESURE != INTERPRÉTATION.');
}
function gates(v){
  obj(v,'$.payload.publication_gates');allowed(v,new Set(['current_gate','recommended_next_step','gates']),'$.payload.publication_gates');required(v,['current_gate','recommended_next_step','gates'],'$.payload.publication_gates');str(v.current_gate,'$.payload.publication_gates.current_gate');str(v.recommended_next_step,'$.payload.publication_gates.recommended_next_step');
  if(!Array.isArray(v.gates))fail('$.payload.publication_gates.gates doit être une liste.');
  v.gates.forEach((g,i)=>{const p=`$.payload.publication_gates.gates[${i}]`;obj(g,p);allowed(g,new Set(['id','label','status']),p);required(g,['id','label','status'],p);str(g.id,`${p}.id`);str(g.label,`${p}.label`);if(!PIPELINE_STATUSES.has(g.status))fail(`${p}.status invalide.`)});
}
function metrics(v){
  if(!Array.isArray(v))fail('$.payload.metrics doit être une liste.');v.forEach((x,i)=>{const p=`$.payload.metrics[${i}]`;obj(x,p);const a=new Set(['id','label','value','unit','status','provenance_ref']);allowed(x,a,p);required(x,['id','label','value','status','provenance_ref'],p);str(x.id,`${p}.id`);str(x.label,`${p}.label`);primitive(x.value,`${p}.value`);if('unit'in x&&x.unit!==null)str(x.unit,`${p}.unit`);str(x.status,`${p}.status`);str(x.provenance_ref,`${p}.provenance_ref`)});
}
function evidence(v){
  if(!Array.isArray(v))fail('$.payload.evidence doit être une liste.');v.forEach((x,i)=>{const p=`$.payload.evidence[${i}]`;obj(x,p);const a=new Set(['id','type','status','public_ref','hash']);allowed(x,a,p);required(x,['id','type','status','public_ref'],p);str(x.id,`${p}.id`);str(x.type,`${p}.type`);str(x.status,`${p}.status`);str(x.public_ref,`${p}.public_ref`);if('hash'in x)str(x.hash,`${p}.hash`)});
}
function integrity(v){
  obj(v,'$.payload.integrity');allowed(v,new Set(['status','checks']),'$.payload.integrity');required(v,['status','checks'],'$.payload.integrity');str(v.status,'$.payload.integrity.status');if(!Array.isArray(v.checks))fail('$.payload.integrity.checks doit être une liste.');
  v.checks.forEach((x,i)=>{const p=`$.payload.integrity.checks[${i}]`;obj(x,p);allowed(x,new Set(['id','status','public_ref']),p);required(x,['id','status','public_ref'],p);str(x.id,`${p}.id`);if(!CHECK_STATUSES.has(x.status))fail(`${p}.status invalide.`);str(x.public_ref,`${p}.public_ref`)});
}

function validatePayload(data){
  const p=data.payload;
  if(data.mode==='DEMO') required(p,PAYLOAD,'$.payload');
  else if(data.mode==='SNAPSHOT') required(p,SNAPSHOT_REQUIRED,'$.payload');
  else required(p,LIVE_REQUIRED,'$.payload');
  if('identity'in p)identity(p.identity);
  if('continuity'in p)continuity(p.continuity);
  if('metacognition'in p)meta(p.metacognition);
  if('pipeline'in p)pipeline(p.pipeline);
  if('training_field'in p)observations(p.training_field);
  if('observatory'in p)observatory(p.observatory);
  if('publication_gates'in p)gates(p.publication_gates);
  if('metrics'in p)metrics(p.metrics);
  if('evidence'in p)evidence(p.evidence);
  if('integrity'in p)integrity(p.integrity);
}

function completeDemoCycle(data){
  const p=data.payload;
  const steps=p.pipeline.steps;
  if(steps.length!==COMPLETE_CYCLE_IDS.length)fail('Le pipeline DEMO complet doit contenir exactement 7 étapes.');
  COMPLETE_CYCLE_IDS.forEach((id,i)=>{if(steps[i]?.id!==id)fail(`Ordre du pipeline invalide à l'étape ${i+1}.`);if(steps[i]?.status!=='PASSED')fail(`Le cycle DEMO complet exige PASSED à l'étape ${i+1}.`)});
  if(p.metacognition.status!=='DEMO_CYCLE_COMPLETE')fail('GENESIS-003 DEMO doit déclarer DEMO_CYCLE_COMPLETE.');
  if(p.metacognition.c041_c060_status!=='COMPLETE_VALIDATED_DEMO')fail('C041-C060 DEMO doit être COMPLETE_VALIDATED_DEMO.');
  if(p.metacognition.competing_hypotheses<2)fail('L’exploration DEMO exige au moins deux hypothèses concurrentes.');
  if(p.continuity.parent_link_status!=='PASSED')fail('Le retour SOURCE exige un lien parent PASSED.');
  if(p.continuity.root_identity_status!=='PASSED')fail('Le retour SOURCE exige une identité ROOT PASSED.');
  if(p.continuity.return_status!=='PASSED')fail('Le retour SOURCE exige return_status=PASSED.');
  if(p.continuity.previous_checkpoint_ref===p.continuity.current_checkpoint_ref)fail('Le checkpoint courant doit avancer sans perdre le lien parent.');
  if((p.continuity.accepted_candidates+p.continuity.rejected_candidates)<1)fail('La validation DEMO doit conserver au moins un verdict accepté ou rejeté.');
  const evidenceIds=new Set(p.evidence.map(x=>x.id));
  if(!evidenceIds.has('DEMO-CYCLE-5-6-7'))fail('La preuve publique synthétique DEMO-CYCLE-5-6-7 est obligatoire.');
  const cycleCheck=p.integrity.checks.find(x=>x.id==='demo-check-cycle-5-6-7');
  if(!cycleCheck||cycleCheck.status!=='PASSED')fail('Le contrôle d’intégrité du cycle 5-6-7 doit être PASSED.');
}

function validateSnapshot(data){
  const p=data.payload;
  if(data.publication_id.startsWith('DEMO-'))fail('Un SNAPSHOT public réel ne peut pas utiliser un publication_id DEMO.');
  if(!p.identity.root_digest.startsWith('PUBLIC-PROJECTION-SHA256:'))fail('Le SNAPSHOT doit exposer uniquement un digest de projection publique.');
  if(/DEMO/i.test(p.identity.root_status)||/DEMO/i.test(p.identity.root_version))fail('Le SNAPSHOT ne doit pas réutiliser une identité DEMO.');
  if(p.integrity.status!==data.integrity_status)fail('Les statuts d’intégrité SNAPSHOT doivent être cohérents.');
  if(!['UNVERIFIED','VERIFIED_PUBLIC'].includes(data.integrity_status))fail('Un SNAPSHOT doit être UNVERIFIED ou VERIFIED_PUBLIC pendant sa construction/validation.');

  const gateMap=new Map(p.publication_gates.gates.map(g=>[g.id,g.status]));
  for(const id of ['contract-v2','adapter','snapshot','live-read-only'])if(!gateMap.has(id))fail(`Gate SNAPSHOT manquante: ${id}.`);
  for(const id of ['contract-v2','adapter','snapshot'])if(gateMap.get(id)!=='PASSED')fail(`Gate ${id} doit être PASSED pour un SNAPSHOT.`);
  if(gateMap.get('live-read-only')==='PASSED')fail('LIVE_READ_ONLY doit rester bloqué pendant la publication SNAPSHOT.');
  if(p.publication_gates.current_gate!=='LIVE_READ_ONLY_PENDING')fail('current_gate doit être LIVE_READ_ONLY_PENDING après le premier SNAPSHOT.');

  if(p.metrics.some(x=>x.status==='SYNTHETIC'))fail('Un SNAPSHOT réel ne doit pas publier de métrique SYNTHETIC.');
  if(p.training_field?.observations?.some(x=>x.status==='SYNTHETIC'))fail('Un SNAPSHOT réel ne doit pas publier d’observation SYNTHETIC.');
  if(p.observatory?.mode==='DEMO')fail('Un SNAPSHOT réel ne doit pas déclarer observatory.mode=DEMO.');

  const hashEvidence=p.evidence.find(x=>x.type==='PUBLIC_HASH'&&typeof x.hash==='string'&&/^sha256:[0-9a-f]{64}$/.test(x.hash));
  if(!hashEvidence)fail('Le SNAPSHOT exige une preuve PUBLIC_HASH sha256.');
  const hashCheck=p.integrity.checks.find(x=>x.id==='snapshot-public-projection-hash');
  if(!hashCheck||hashCheck.status!=='PASSED')fail('Le contrôle snapshot-public-projection-hash doit être PASSED.');
  const privacyCheck=p.integrity.checks.find(x=>x.id==='snapshot-private-raw-data-not-copied');
  if(!privacyCheck||privacyCheck.status!=='PASSED')fail('Le contrôle snapshot-private-raw-data-not-copied doit être PASSED.');
}

function validateLiveReadOnly(data){
  const p=data.payload;
  if(data.publication_id.startsWith('DEMO-'))fail('LIVE_READ_ONLY public ne peut pas utiliser un publication_id DEMO.');
  if(!p.identity.root_digest.startsWith('PUBLIC-READ-ONLY-SHA256:'))fail('LIVE_READ_ONLY doit exposer uniquement un digest public read-only.');
  if(p.integrity.status!==data.integrity_status)fail('Les statuts d’intégrité LIVE_READ_ONLY doivent être cohérents.');
  if(data.integrity_status!=='VERIFIED_PUBLIC')fail('LIVE_READ_ONLY exige integrity_status=VERIFIED_PUBLIC.');

  const gateMap=new Map(p.publication_gates.gates.map(g=>[g.id,g.status]));
  for(const id of ['contract-v2','adapter','snapshot','live-read-only'])if(!gateMap.has(id))fail(`Gate LIVE_READ_ONLY manquante: ${id}.`);
  for(const id of ['contract-v2','adapter','snapshot','live-read-only'])if(gateMap.get(id)!=='PASSED')fail(`Gate ${id} doit être PASSED pour LIVE_READ_ONLY.`);

  const activeMetric=p.metrics.find(x=>x.id==='public-live-active');
  if(!activeMetric||typeof activeMetric.value!=='boolean'||activeMetric.status!=='VERIFIED_PUBLIC')fail('La métrique public-live-active doit être booléenne et VERIFIED_PUBLIC.');
  const currentGate=p.publication_gates.current_gate;
  const nextStep=p.publication_gates.recommended_next_step;
  if(currentGate==='LIVE_READ_ONLY_BRIDGE_READY_NOT_DEPLOYED'){
    if(activeMetric.value!==false)fail('READY_NOT_DEPLOYED exige public-live-active=false.');
    if(nextStep!=='AUTHORIZE_CONTROLLED_PUBLIC_READ_ONLY_DEPLOYMENT')fail('READY_NOT_DEPLOYED exige l’étape d’autorisation de déploiement.');
  }else if(currentGate==='LIVE_READ_ONLY_ACTIVE'){
    if(activeMetric.value!==true)fail('LIVE_READ_ONLY_ACTIVE exige public-live-active=true.');
    if(nextStep!=='CONTINUE_SERVER_SIDE_READ_ONLY_SYNC')fail('LIVE_READ_ONLY_ACTIVE exige la poursuite du sync server-side read-only.');
  }else{
    fail('current_gate LIVE_READ_ONLY invalide.');
  }

  const hashEvidence=p.evidence.find(x=>x.id==='LIVE-PUBLIC-PROJECTION-HASH'&&x.type==='PUBLIC_HASH'&&typeof x.hash==='string'&&/^sha256:[0-9a-f]{64}$/.test(x.hash));
  if(!hashEvidence)fail('LIVE_READ_ONLY exige une preuve LIVE-PUBLIC-PROJECTION-HASH sha256.');
  for(const id of ['live-public-projection-hash','live-server-side-only','live-write-capability-none','live-freshness-window']){
    const check=p.integrity.checks.find(x=>x.id===id);
    if(!check||check.status!=='PASSED')fail(`Le contrôle ${id} doit être PASSED.`);
  }
  const writeMetric=p.metrics.find(x=>x.id==='bridge-write-capability');
  if(writeMetric?.value!=='NONE'||writeMetric?.status!=='VERIFIED_PUBLIC')fail('La métrique bridge-write-capability doit rester NONE/VERIFIED_PUBLIC.');
  const browserMetric=p.metrics.find(x=>x.id==='browser-private-credentials');
  if(browserMetric?.value!==false||browserMetric?.status!=='VERIFIED_PUBLIC')fail('La métrique browser-private-credentials doit rester false/VERIFIED_PUBLIC.');
}

export function validatePublicV2(data){
  obj(data,'$');allowed(data,TOP_LEVEL,'$');required(data,TOP_LEVEL,'$');
  if(data.contract_version!==EXPECTED_CONTRACT)fail(`contract_version doit être ${EXPECTED_CONTRACT}.`);
  if(data.mode!=='DEMO'&&data.mode!=='SNAPSHOT'&&data.mode!=='LIVE_READ_ONLY')fail('Le contrat v2 accepte uniquement DEMO, SNAPSHOT ou LIVE_READ_ONLY.');
  if(data.mode==='DEMO'&&data.source_status!=='SYNTHETIC')fail('DEMO exige source_status=SYNTHETIC.');
  if(data.mode==='SNAPSHOT'&&data.source_status!=='PUBLIC_SNAPSHOT')fail('SNAPSHOT exige source_status=PUBLIC_SNAPSHOT.');
  if(data.mode==='LIVE_READ_ONLY'&&data.source_status!=='PUBLIC_READ_ONLY')fail('LIVE_READ_ONLY exige source_status=PUBLIC_READ_ONLY.');
  if(!INTEGRITY_STATUSES.has(data.integrity_status))fail('integrity_status invalide.');
  str(data.publication_id,'$.publication_id');str(data.published_at,'$.published_at');if(Number.isNaN(Date.parse(data.published_at)))fail('$.published_at invalide.');
  obj(data.payload,'$.payload');allowed(data.payload,PAYLOAD,'$.payload');
  validatePayload(data);
  if(data.mode==='DEMO')completeDemoCycle(data);
  else if(data.mode==='SNAPSHOT')validateSnapshot(data);
  else validateLiveReadOnly(data);
  scan(data);
  return data.mode==='DEMO'
    ? {ok:true,contract_version:data.contract_version,mode:data.mode,publication_id:data.publication_id,cycle_5_6_7:'PASSED'}
    : data.mode==='SNAPSHOT'
      ? {ok:true,contract_version:data.contract_version,mode:data.mode,publication_id:data.publication_id,snapshot_gate:'PASSED'}
      : {ok:true,contract_version:data.contract_version,mode:data.mode,publication_id:data.publication_id,live_read_only_bridge:data.payload.publication_gates.current_gate==='LIVE_READ_ONLY_ACTIVE'?'PASSED_ACTIVE':'PASSED_NOT_DEPLOYED'};
}

async function main(){
  const defaultPath=fileURLToPath(new URL('./demo/genesis-demo-v2.json',import.meta.url));const target=process.argv[2]??defaultPath;
  try{const data=JSON.parse(await readFile(target,'utf8'));const result=validatePublicV2(data);console.log('GENESIS_PUBLIC_V2_VALID');console.log(JSON.stringify(result,null,2))}
  catch(error){console.error('GENESIS_PUBLIC_V2_INVALID');console.error(error instanceof Error?error.message:String(error));process.exitCode=1}
}
if(process.argv[1]&&fileURLToPath(import.meta.url)===process.argv[1])await main();
