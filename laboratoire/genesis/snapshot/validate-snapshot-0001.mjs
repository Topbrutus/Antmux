#!/usr/bin/env node
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { isDeepStrictEqual } from 'node:util';
import { fileURLToPath } from 'node:url';
import { adaptPublicCandidate } from '../adapter/public-adapter.mjs';
import { validatePublicV2 } from '../validate-public-v2.mjs';

function fail(message){ throw new Error(message); }
function stable(value){
  if(Array.isArray(value)) return value.map(stable);
  if(value&&typeof value==='object') return Object.fromEntries(Object.keys(value).sort().map(k=>[k,stable(value[k])]));
  return value;
}
function metric(output,id){
  const item=output.payload.metrics.find(x=>x.id===id);
  if(!item) fail(`Métrique snapshot manquante: ${id}`);
  return item.value;
}

export function verifySnapshot0001(input, committed){
  const adapted=adaptPublicCandidate(structuredClone(input));
  validatePublicV2(adapted);
  validatePublicV2(committed);
  if(!isDeepStrictEqual(adapted,committed)) fail('Le snapshot commité diverge de la sortie déterministe de l’Adapter.');

  const projection={
    evidence_ledger_auto_promotion:metric(adapted,'evidence-ledger-auto-promotion'),
    genesis003_c041_c060:metric(adapted,'genesis003-c041-c060'),
    hypothesis_selection_performed:metric(adapted,'hypothesis-selection-performed'),
    probabilities_produced:metric(adapted,'probabilities-produced'),
    selected_experiment_status:metric(adapted,'selected-experiment-status'),
    source_closure_audit:metric(adapted,'source-closure-audit')
  };
  const canonical=JSON.stringify(stable(projection));
  const digest=createHash('sha256').update(canonical,'utf8').digest('hex');
  const expectedRoot=`PUBLIC-PROJECTION-SHA256:${digest}`;
  const expectedEvidence=`sha256:${digest}`;
  if(adapted.payload.identity.root_digest!==expectedRoot) fail('Le digest de projection publique ne correspond pas aux faits publiés.');
  const hashEvidence=adapted.payload.evidence.find(x=>x.id==='SNAPSHOT-PROJECTION-HASH');
  if(hashEvidence?.hash!==expectedEvidence) fail('La preuve PUBLIC_HASH ne correspond pas à la projection publique.');

  const payloadKeys=Object.keys(adapted.payload).sort();
  const expectedKeys=['evidence','identity','integrity','metrics','publication_gates'];
  if(!isDeepStrictEqual(payloadKeys,expectedKeys)) fail('SNAPSHOT 0001 doit rester une projection publique minimale.');
  if(adapted.mode!=='SNAPSHOT'||adapted.source_status!=='PUBLIC_SNAPSHOT'||adapted.integrity_status!=='VERIFIED_PUBLIC') fail('Enveloppe SNAPSHOT finale invalide.');
  const live=adapted.payload.publication_gates.gates.find(x=>x.id==='live-read-only');
  if(live?.status!=='PENDING') fail('LIVE_READ_ONLY doit rester PENDING.');
  const text=JSON.stringify(adapted);
  if(/DEMO|SYNTHETIC/.test(text)) fail('Contamination DEMO/SYNTHETIC détectée dans le snapshot réel.');

  return {
    ok:true,
    publication_id:adapted.publication_id,
    mode:adapted.mode,
    source_status:adapted.source_status,
    integrity_status:adapted.integrity_status,
    projection_sha256:digest,
    private_raw_data_copied:false,
    live_read_only_enabled:false
  };
}

async function main(){
  const inputPath=fileURLToPath(new URL('./public-snapshot-0001-input.json',import.meta.url));
  const outputPath=fileURLToPath(new URL('./genesis-public-snapshot-0001.json',import.meta.url));
  try{
    const input=JSON.parse(await readFile(inputPath,'utf8'));
    const output=JSON.parse(await readFile(outputPath,'utf8'));
    const result=verifySnapshot0001(input,output);
    console.log('GENESIS_PUBLIC_SNAPSHOT_0001_VALID');
    console.log(JSON.stringify(result,null,2));
  }catch(error){
    console.error('GENESIS_PUBLIC_SNAPSHOT_0001_INVALID');
    console.error(error instanceof Error?error.message:String(error));
    process.exitCode=1;
  }
}
if(process.argv[1]&&fileURLToPath(import.meta.url)===process.argv[1])await main();
