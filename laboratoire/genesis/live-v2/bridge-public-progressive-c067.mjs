#!/usr/bin/env node
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { validatePublicV2 } from '../validate-public-v2.mjs';
import { assertProgressiveBridgeInputC067, publicBool, publicNumber, publicValue } from './build-public-source-progressive-c067.mjs';

const STAGES=['C060','C061','C062','C063','C064','C065','C066','C067'];
function fail(message){throw new Error(message);}
function atLeast(stage,min){return STAGES.indexOf(stage)>=STAGES.indexOf(min);}
function stable(value){if(Array.isArray(value))return value.map(stable);if(value&&typeof value==='object')return Object.fromEntries(Object.keys(value).sort().map(k=>[k,stable(value[k])]));return value;}
function digestPayload(payload,observedAt){return createHash('sha256').update(JSON.stringify(stable({observed_at:observedAt,payload})),'utf8').digest('hex');}
function scanSensitive(value,label='$'){
  if(typeof value==='string'){
    const patterns=[[/-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/i,'private key'],[/\bghp_[A-Za-z0-9_]{20,}\b/,'GitHub token'],[/\bgithub_pat_[A-Za-z0-9_]{20,}\b/,'GitHub token'],[/\bsk-[A-Za-z0-9_-]{20,}\b/,'API key'],[/^[A-Za-z]:\\/,'absolute Windows path'],[/^\\\\/,'UNC path'],[/^file:\/\//i,'file URL'],[/https?:\/\/(?:localhost|127\.0\.0\.1)(?::\d+)?(?:\/|$)/i,'local endpoint'],[/https?:\/\/10\.\d+\.\d+\.\d+(?::\d+)?(?:\/|$)/i,'private IP'],[/https?:\/\/192\.168\.\d+\.\d+(?::\d+)?(?:\/|$)/i,'private IP'],[/https?:\/\/172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+(?::\d+)?(?:\/|$)/i,'private IP'],[/Topbrutus\/seedgenesis/i,'direct private repository reference'],[/Topbrutus\/gesis/i,'direct private repository reference'],[/refs\/heads\//i,'private branch reference'],[/public\/live-source/i,'private publication branch reference'],[/public\/live\/status\.env/i,'private publication path reference']];
    for(const[pattern,name]of patterns)if(pattern.test(value))fail(`${label} contient un motif interdit (${name}).`);return;
  }
  if(Array.isArray(value)){value.forEach((item,index)=>scanSensitive(item,`${label}[${index}]`));return;}
  if(value&&typeof value==='object')for(const[key,item]of Object.entries(value))scanSensitive(item,`${label}.${key}`);
}
function metric(id,label,value){return{id,label,value,status:'VERIFIED_PUBLIC',provenance_ref:'SERVER-SIDE-WHITELIST-V3'};}

export function buildProgressivePublicEnvelopeC067(input,options={}){
  assertProgressiveBridgeInputC067(input);scanSensitive(input);
  const observed=Date.parse(input.source_observed_at),now=Date.parse(options.now??input.bridge_received_at);if(Number.isNaN(observed)||Number.isNaN(now))fail('Horodatage bridge invalide.');
  const ageSeconds=Math.floor((now-observed)/1000);if(ageSeconds<0)fail('La source ne peut pas venir du futur.');if(ageSeconds>input.max_age_seconds)fail('Source progressive périmée: fail closed.');
  const stage=input.source_attestation.validated_through,liveActive=input.live_active;
  const metrics=[
    metric('genesis003-validated-through','GENESIS-003 validé jusqu’à',stage),
    metric('genesis003-c041-c060','GENESIS-003 C041–C060','COMPLETE_VALIDATED'),
    metric('selected-experiment-status','État du test sélectionné',publicValue(input,'selected_experiment_status')),
  ];
  if(atLeast(stage,'C061'))metrics.push(
    metric('genesis003-c061','C061 · admissibilité d’exécution',publicValue(input,'genesis003_c061')),
    metric('c061-execution-input','Entrée d’exécution C061',publicValue(input,'c061_execution_input')),
    metric('execution-admissibility','Gate d’exécution',publicValue(input,'execution_admissibility')),
    metric('next-scientific-action','Prochaine action scientifique',publicValue(input,'next_scientific_action')),
  );
  if(atLeast(stage,'C062'))metrics.push(
    metric('genesis003-c062','C062 · spécification réelle',publicValue(input,'genesis003_c062')),
    metric('real-experiment-spec-id','Expérience réelle candidate',publicValue(input,'real_experiment_spec_id')),
    metric('real-experiment-spec-status','État de la spécification',publicValue(input,'real_experiment_spec_status')),
    metric('real-experiment-family','Famille expérimentale',publicValue(input,'real_experiment_family')),
    metric('trial-class','Classe d’essai',publicValue(input,'trial_class')),
    metric('replicates-per-arm','Répétitions par condition',publicNumber(input,'replicates_per_arm')),
    metric('blinded-primary-analysis','Analyse primaire aveugle',publicBool(input,'blinded_primary_analysis')),
    metric('pretargeted-symbolic-search','Recherche symbolique pré-ciblée',publicBool(input,'pretargeted_symbolic_search')),
    metric('real-plan-selection-performed','Plan réel sélectionné',publicBool(input,'real_plan_selection_performed')),
  );
  if(atLeast(stage,'C063'))metrics.push(
    metric('genesis003-c063','C063 · plan réel suivant',publicValue(input,'genesis003_c063')),
    metric('real-next-test-plan-id','Plan réel sélectionné',publicValue(input,'real_next_test_plan_id')),
    metric('real-next-test-plan-status','État du plan réel',publicValue(input,'real_next_test_plan_status')),
    metric('real-next-test-sample-count','Échantillons planifiés',publicNumber(input,'sample_count')),
    metric('execution-bindings-required','Bindings requis',publicNumber(input,'execution_bindings_required')),
    metric('execution-bindings-bound','Bindings prouvés',publicNumber(input,'execution_bindings_bound')),
    metric('execution-bindings-complete','Bindings complets',publicBool(input,'execution_bindings_complete')),
  );
  if(atLeast(stage,'C064'))metrics.push(
    metric('genesis003-c064','C064 · contrat d’exécution réel',publicValue(input,'genesis003_c064')),
    metric('real-execution-contract-id','Contrat d’exécution public',publicValue(input,'real_execution_contract_id')),
    metric('real-execution-contract-status','État du contrat d’exécution',publicValue(input,'real_execution_contract_status')),
    metric('execution-bindings-unbound','Bindings restant à résoudre',publicNumber(input,'execution_bindings_unbound')),
    metric('generator-seed-policy-bound','Politique seed prouvée',publicBool(input,'generator_seed_policy_bound')),
    metric('gesis-primary-profile-compatible','Profil GESIS primaire compatible',publicBool(input,'gesis_primary_profile_compatible')),
    metric('gesis-observed-candidate-recorded','Candidat GESIS observé',publicBool(input,'gesis_observed_candidate_recorded')),
  );
  if(atLeast(stage,'C065'))metrics.push(
    metric('genesis003-c065','C065 · bindings GESIS neutres',publicValue(input,'genesis003_c065')),
    metric('gesis-neutral-path-compatible','Chemin GESIS neutre compatible',publicBool(input,'gesis_neutral_path_compatible')),
    metric('default-az-profile-still-incompatible','Profil A→Z par défaut toujours incompatible',publicBool(input,'default_az_profile_still_incompatible')),
    metric('analysis-decision-rule-bound','Règle de décision liée',publicBool(input,'analysis_decision_rule_bound')),
  );
  if(atLeast(stage,'C066'))metrics.push(
    metric('genesis003-c066','C066 · audit des bindings restants',publicValue(input,'genesis003_c066')),
    metric('binding-dependency-audit','Audit des dépendances de bindings',publicValue(input,'binding_dependency_audit')),
    metric('new-bindings-proven','Nouveaux bindings prouvés par C066',publicNumber(input,'new_bindings_proven')),
    metric('generator-execution-profile-frozen','Profil générateur réel gelé',publicBool(input,'generator_execution_profile_frozen')),
  );
  if(stage==='C067')metrics.push(
    metric('genesis003-c067','C067 · contrôle audio déterministe',publicValue(input,'genesis003_c067')),
    metric('control-generator-profile','Profil générateur de contrôle',publicValue(input,'control_generator_profile')),
    metric('control-generator-deterministic','Contrôle audio déterministe',publicBool(input,'control_generator_deterministic')),
    metric('real-generator-bindings-added','Bindings réels ajoutés par le contrôle',publicNumber(input,'real_generator_bindings_added')),
    metric('real-generator-profile-frozen','Profil générateur expérimental réel gelé',publicBool(input,'real_generator_profile_frozen')),
  );
  metrics.push(
    metric('hypothesis-selection','Hypothèse sélectionnée',false),metric('hypothesis-ranking','Classement d’hypothèses',false),metric('probabilities-produced','Probabilités produites',false),
    metric('bridge-read-capability','Capacité de lecture bridge','READ_ONLY'),metric('bridge-write-capability','Capacité d’écriture bridge','NONE'),metric('browser-private-credentials','Credentials privés navigateur',false),metric('public-live-active','Publication LIVE active',liveActive),
  );
  const payload={
    identity:{seed_label:'Genesis',root_status:'PRESERVED_AT_SOURCE_VALIDATION',root_version:`GENESIS-003-${stage}-PUBLIC-PROGRESS-v3`,continuity_policy:'PRIVATE_ROOT_NOT_EXPOSED; PUBLIC_PROJECTION_ONLY'},
    publication_gates:{current_gate:liveActive?'LIVE_READ_ONLY_ACTIVE':'LIVE_READ_ONLY_BRIDGE_READY_NOT_DEPLOYED',recommended_next_step:liveActive?'CONTINUE_SERVER_SIDE_READ_ONLY_SYNC':'AUTHORIZE_CONTROLLED_PUBLIC_READ_ONLY_DEPLOYMENT',gates:[{id:'contract-v2',label:'Contrat public v2',status:'PASSED'},{id:'adapter',label:'Genesis Public Adapter',status:'PASSED'},{id:'snapshot',label:'Snapshot public figé',status:'PASSED'},{id:'live-read-only',label:'Bridge serveur lecture seule',status:'PASSED'}]},
    metrics,
    evidence:[{id:'SERVER-SIDE-WHITELIST-V3',type:'PUBLIC_ATTESTATION',status:'VERIFIED_PUBLIC',public_ref:'Whitelisted progressive Genesis C060-C067 status projection'}],
    integrity:{status:'VERIFIED_PUBLIC',checks:[{id:'live-public-projection-hash',status:'PASSED',public_ref:'PUBLIC-READ-ONLY-SHA256'},{id:'live-server-side-only',status:'PASSED',public_ref:'Browser has no private source access'},{id:'live-write-capability-none',status:'PASSED',public_ref:'Bridge exposes no write capability'},{id:'live-freshness-window',status:'PASSED',public_ref:'Stale source is rejected'}]},
  };
  const digest=digestPayload(payload,input.source_observed_at);payload.identity.root_digest=`PUBLIC-READ-ONLY-SHA256:${digest}`;payload.evidence.push({id:'LIVE-PUBLIC-PROJECTION-HASH',type:'PUBLIC_HASH',status:'VERIFIED_PUBLIC',public_ref:'Server-side progressive public read-only projection',hash:`sha256:${digest}`});
  const envelope={contract_version:'2.0.0-draft',mode:'LIVE_READ_ONLY',publication_id:'GENESIS-PUBLIC-READ-ONLY-PROGRESSIVE-0003',published_at:new Date(now).toISOString(),source_status:'PUBLIC_READ_ONLY',integrity_status:'VERIFIED_PUBLIC',payload};
  validatePublicV2(envelope);scanSensitive(envelope);return{envelope,sourceAgeSeconds:ageSeconds};
}

async function main(){const inputPath=process.argv[2];if(!inputPath)fail('Usage: bridge-public-progressive-c067.mjs <bridge-input.json>');const input=JSON.parse(await readFile(path.resolve(inputPath),'utf8'));const result=buildProgressivePublicEnvelopeC067(input);const outDir=path.resolve('.build/genesis-public-read-only-bridge');await mkdir(outDir,{recursive:true});await writeFile(path.join(outDir,'public-read-only-envelope.json'),`${JSON.stringify(result.envelope,null,2)}\n`,'utf8');console.log('GENESIS_PROGRESSIVE_C067_PUBLIC_READ_ONLY_BRIDGE_VALID');console.log(JSON.stringify({mode:result.envelope.mode,source_status:result.envelope.source_status,integrity_status:result.envelope.integrity_status,validated_through:result.envelope.payload.metrics.find(x=>x.id==='genesis003-validated-through')?.value,public_live_active:result.envelope.payload.metrics.find(x=>x.id==='public-live-active')?.value},null,2));}
if(process.argv[1]===fileURLToPath(import.meta.url))main().catch(error=>{console.error(`GENESIS_PROGRESSIVE_C067_PUBLIC_READ_ONLY_BRIDGE_INVALID: ${error.message}`);process.exit(1);});
