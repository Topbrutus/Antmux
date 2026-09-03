#!/usr/bin/env node
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

const EXPECTED_CONTRACT = '2.0.0-draft';
const TOP_LEVEL = new Set(['contract_version','mode','publication_id','published_at','source_status','integrity_status','payload']);
const PAYLOAD = new Set(['identity','continuity','metacognition','pipeline','training_field','observatory','publication_gates','metrics','evidence','integrity']);
const PIPELINE_STATUSES = new Set(['PENDING','RUNNING_PUBLIC','PASSED','FAILED','REJECTED','NOT_APPLICABLE']);
const CHECK_STATUSES = new Set(['PASSED','FAILED','NOT_RUN','NOT_APPLICABLE']);
const SEMANTIC_CLASSES = new Set(['MEASURED','DERIVED','INTERPRETED','HYPOTHESIS','UNKNOWN']);
const INTEGRITY_STATUSES = new Set(['NOT_APPLICABLE','UNVERIFIED','VERIFIED_PUBLIC','FAILED_PUBLIC_CHECK']);

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

export function validatePublicV2(data){
  obj(data,'$');allowed(data,TOP_LEVEL,'$');required(data,TOP_LEVEL,'$');
  if(data.contract_version!==EXPECTED_CONTRACT)fail(`contract_version doit être ${EXPECTED_CONTRACT}.`);
  if(data.mode!=='DEMO')fail('Le validateur v2 canonique attend mode=DEMO.');
  if(data.source_status!=='SYNTHETIC')fail('Le snapshot canonique v2 doit rester SYNTHETIC.');
  if(!INTEGRITY_STATUSES.has(data.integrity_status))fail('integrity_status invalide.');
  str(data.publication_id,'$.publication_id');str(data.published_at,'$.published_at');if(Number.isNaN(Date.parse(data.published_at)))fail('$.published_at invalide.');
  obj(data.payload,'$.payload');allowed(data.payload,PAYLOAD,'$.payload');
  identity(data.payload.identity);continuity(data.payload.continuity);meta(data.payload.metacognition);pipeline(data.payload.pipeline);observations(data.payload.training_field);observatory(data.payload.observatory);gates(data.payload.publication_gates);metrics(data.payload.metrics);evidence(data.payload.evidence);integrity(data.payload.integrity);
  scan(data);
  return {ok:true,contract_version:data.contract_version,mode:data.mode,publication_id:data.publication_id};
}

async function main(){
  const defaultPath=fileURLToPath(new URL('./demo/genesis-demo-v2.json',import.meta.url));const target=process.argv[2]??defaultPath;
  try{const data=JSON.parse(await readFile(target,'utf8'));const result=validatePublicV2(data);console.log('GENESIS_PUBLIC_V2_VALID');console.log(JSON.stringify(result,null,2))}
  catch(error){console.error('GENESIS_PUBLIC_V2_INVALID');console.error(error instanceof Error?error.message:String(error));process.exitCode=1}
}
if(process.argv[1]&&fileURLToPath(import.meta.url)===process.argv[1])await main();
