import { validatePublicV2 } from '../validate-public-v2.mjs';

const PAYLOAD_KEYS = new Set([
  'identity','continuity','metacognition','pipeline','training_field',
  'observatory','publication_gates','metrics','evidence','integrity'
]);

const FIELDS = {
  identity: ['seed_label','root_status','root_version','root_digest','continuity_policy'],
  continuity: ['cycle','previous_checkpoint_ref','current_checkpoint_ref','parent_link_status','root_identity_status','accepted_candidates','rejected_candidates','return_status'],
  metacognition: ['status','competing_hypotheses','uncertainty','next_test','rationale','c041_c060_status'],
  observatory: ['label','mode','fft_status','latest_export_ref','peak_count','episode_count','block_score_status','scientific_rule']
};

function fail(message){ throw new Error(message); }
function obj(value,path){ if(!value || typeof value!=='object' || Array.isArray(value)) fail(`${path} doit être un objet.`); }
function assertAllowedKeys(value, allowed, path){
  obj(value,path);
  for(const key of Object.keys(value)) if(!allowed.has(key)) fail(`${path}.${key} n'est pas autorisé par l'Adapter.`);
}
function clone(value){ return structuredClone(value); }
function strictObject(value, fields, path){
  const allowed = new Set(fields);
  assertAllowedKeys(value, allowed, path);
  const out = {};
  for(const key of fields) if(key in value) out[key] = clone(value[key]);
  return out;
}
function strictArray(value, fields, path){
  if(!Array.isArray(value)) fail(`${path} doit être une liste.`);
  return value.map((item,index)=>strictObject(item,fields,`${path}[${index}]`));
}

function buildPayload(source){
  assertAllowedKeys(source,PAYLOAD_KEYS,'$.public_payload');
  const out = {};

  for(const category of ['identity','continuity','metacognition','observatory']){
    if(category in source) out[category] = strictObject(source[category],FIELDS[category],`$.public_payload.${category}`);
  }

  if('pipeline' in source){
    assertAllowedKeys(source.pipeline,new Set(['steps']),'$.public_payload.pipeline');
    out.pipeline = {steps: strictArray(source.pipeline.steps,['id','label','status'],'$.public_payload.pipeline.steps')};
  }

  if('training_field' in source){
    assertAllowedKeys(source.training_field,new Set(['label','purpose','observations']),'$.public_payload.training_field');
    out.training_field = {
      ...(source.training_field.label!==undefined ? {label:clone(source.training_field.label)} : {}),
      ...(source.training_field.purpose!==undefined ? {purpose:clone(source.training_field.purpose)} : {}),
      observations: strictArray(source.training_field.observations,['id','label','value','unit','semantic_class','status','provenance_ref'],'$.public_payload.training_field.observations')
    };
  }

  if('publication_gates' in source){
    assertAllowedKeys(source.publication_gates,new Set(['current_gate','recommended_next_step','gates']),'$.public_payload.publication_gates');
    out.publication_gates = {
      ...(source.publication_gates.current_gate!==undefined ? {current_gate:clone(source.publication_gates.current_gate)} : {}),
      ...(source.publication_gates.recommended_next_step!==undefined ? {recommended_next_step:clone(source.publication_gates.recommended_next_step)} : {}),
      gates: strictArray(source.publication_gates.gates,['id','label','status'],'$.public_payload.publication_gates.gates')
    };
  }

  if('metrics' in source) out.metrics = strictArray(source.metrics,['id','label','value','unit','status','provenance_ref'],'$.public_payload.metrics');
  if('evidence' in source) out.evidence = strictArray(source.evidence,['id','type','status','public_ref','hash'],'$.public_payload.evidence');

  if('integrity' in source){
    assertAllowedKeys(source.integrity,new Set(['status','checks']),'$.public_payload.integrity');
    out.integrity = {
      ...(source.integrity.status!==undefined ? {status:clone(source.integrity.status)} : {}),
      checks: strictArray(source.integrity.checks,['id','status','public_ref'],'$.public_payload.integrity.checks')
    };
  }

  return out;
}

export function adaptPublicCandidate(input){
  obj(input,'$');
  if(input.adapter_input_version!=='1.0.0-test') fail('adapter_input_version doit être 1.0.0-test.');
  if(input.publication_intent!=='EXPLICIT_PUBLICATION_CANDIDATE') fail('publication_intent explicite obligatoire.');
  if(input.mode!=='DEMO' && input.mode!=='SNAPSHOT') fail('VALIDATE_PUBLIC_ADAPTER accepte uniquement mode=DEMO ou SNAPSHOT.');
  if(input.source_status!=='SYNTHETIC' && input.source_status!=='PUBLIC_SNAPSHOT') fail('VALIDATE_PUBLIC_ADAPTER accepte uniquement source_status=SYNTHETIC ou PUBLIC_SNAPSHOT.');
  obj(input.public_payload,'$.public_payload');

  const output = {
    contract_version: '2.0.0-draft',
    mode: clone(input.mode),
    publication_id: clone(input.publication_id),
    published_at: clone(input.published_at),
    source_status: clone(input.source_status),
    integrity_status: 'UNVERIFIED',
    payload: buildPayload(input.public_payload)
  };

  validatePublicV2(output);
  output.integrity_status = 'VERIFIED_PUBLIC';
  validatePublicV2(output);
  return output;
}
