#!/usr/bin/env node
import { cp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const REPO_ROOT=fileURLToPath(new URL('../',import.meta.url));
const OUT=join(REPO_ROOT,'.build','antmux-laboratoire-public');
const FILES=[
  'index.html','styles.css','app.js',
  'laboratoire/index.html','laboratoire/README.md',
  'laboratoire/data/MEASUREMENT-CONTRACT.md','laboratoire/data/G1-SOURCES.md',
  'laboratoire/genesis/index.html','laboratoire/genesis/README.md',
  'laboratoire/genesis/PUBLIC-CONTRACT-v1.md','laboratoire/genesis/PUBLIC-CONTRACT-v2.md',
  'laboratoire/genesis/demo/genesis-demo-v1.json','laboratoire/genesis/demo/genesis-demo-v2.json',
  'laboratoire/genesis/snapshot/genesis-public-snapshot-0001.json'
];
async function sha256(path){return createHash('sha256').update(await readFile(path)).digest('hex')}
await rm(OUT,{recursive:true,force:true});await mkdir(OUT,{recursive:true});
const manifestFiles=[];
for(const relative of FILES){const source=join(REPO_ROOT,relative);const target=join(OUT,relative);await mkdir(dirname(target),{recursive:true});await cp(source,target);manifestFiles.push({path:relative,sha256:await sha256(source)})}
const manifest={bundle:'antmux-laboratoire-public',lab:'LAB-004',release_kind:'OVERLAY',deploy_target_hint:'/',home_button:'/laboratoire/',lab_entry:'/laboratoire/',genesis_entry:'/laboratoire/genesis/',genesis_contract_version:'2.0.0-draft',genesis_mode:'SNAPSHOT',source_status:'PUBLIC_SNAPSHOT',publication_id:'GENESIS-PUBLIC-SNAPSHOT-0001',integrity_status:'VERIFIED_PUBLIC',live_read_only:'PENDING',private_genesis_connected:false,generator_modified:false,destructive_deploy_required:false,files:manifestFiles};
await writeFile(join(OUT,'MANIFEST.json'),`${JSON.stringify(manifest,null,2)}\n`,'utf8');
console.log('ANTMUX_LAB_PUBLIC_OVERLAY_READY');console.log(JSON.stringify(manifest,null,2));
