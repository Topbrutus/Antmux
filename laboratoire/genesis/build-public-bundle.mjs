#!/usr/bin/env node
import { cp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT=fileURLToPath(new URL('./',import.meta.url));
const OUT=fileURLToPath(new URL('../../.build/genesis-vision-center-snapshot/',import.meta.url));
const FILES=['index.html','snapshot/genesis-public-snapshot-0001.json','demo/genesis-demo-v1.json','demo/genesis-demo-v2.json','PUBLIC-CONTRACT-v2.md','README.md'];
async function sha256(path){return createHash('sha256').update(await readFile(path)).digest('hex')}
await rm(OUT,{recursive:true,force:true});await mkdir(OUT,{recursive:true});
const manifestFiles=[];
for(const relative of FILES){const source=join(ROOT,relative);const target=join(OUT,relative);await mkdir(dirname(target),{recursive:true});await cp(source,target);manifestFiles.push({path:relative,sha256:await sha256(source)})}
const manifest={bundle:'genesis-vision-center-snapshot',version:3,lab:'LAB-004',contract_version:'2.0.0-draft',mode:'SNAPSHOT',source_status:'PUBLIC_SNAPSHOT',publication_id:'GENESIS-PUBLIC-SNAPSHOT-0001',integrity_status:'VERIFIED_PUBLIC',live_read_only:'PENDING',private_genesis_connected:false,generator_modified:false,deploy_target_hint:'/laboratoire/genesis/',files:manifestFiles};
await writeFile(join(OUT,'MANIFEST.json'),`${JSON.stringify(manifest,null,2)}\n`,'utf8');
console.log('GENESIS_PUBLIC_BUNDLE_READY');console.log(JSON.stringify(manifest,null,2));
