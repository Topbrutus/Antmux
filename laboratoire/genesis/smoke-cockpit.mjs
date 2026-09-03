#!/usr/bin/env node
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT=fileURLToPath(new URL('./',import.meta.url));
const EXPECTED_TITLE='<title>Genesis Vision Center — LIVE / SNAPSHOT</title>';
const EXPECTED_BANNER='PUBLIC READ-ONLY';
const EXPECTED_LIVE_PATH='./live/public-read-only.json';
const EXPECTED_SNAPSHOT_PATH='./snapshot/genesis-public-snapshot-0001.json';
const EXPECTED_CONTRACT='2.0.0-draft';
const MIME=new Map([['.html','text/html; charset=utf-8'],['.json','application/json; charset=utf-8'],['.md','text/markdown; charset=utf-8'],['.mjs','text/javascript; charset=utf-8']]);
function fail(m){throw new Error(m)}
function resolvePath(urlPath){const decoded=decodeURIComponent((urlPath??'/').split('?')[0]);const rel=decoded==='/'?'index.html':decoded.replace(/^\/+/,'');const norm=normalize(rel);if(norm.startsWith('..')||norm.includes('/../')||norm.includes('\\..\\'))fail('Traversal refusé.');return join(ROOT,norm)}
const server=createServer(async(req,res)=>{try{const f=resolvePath(req.url);const body=await readFile(f);res.statusCode=200;res.setHeader('content-type',MIME.get(extname(f))??'application/octet-stream');res.setHeader('cache-control','no-store');res.end(body)}catch{res.statusCode=404;res.end('Not Found')}})
await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve)});
try{
  const address=server.address();if(!address||typeof address==='string')fail('Port indisponible.');const base=`http://127.0.0.1:${address.port}`;
  const indexResponse=await fetch(`${base}/`);if(!indexResponse.ok)fail(`index inaccessible ${indexResponse.status}`);const html=await indexResponse.text();
  for(const marker of [EXPECTED_TITLE,EXPECTED_BANNER,`const LIVE_PATH='${EXPECTED_LIVE_PATH}'`,`const SNAPSHOT_PATH='${EXPECTED_SNAPSHOT_PATH}'`,`const EXPECTED_CONTRACT='2.0.0-draft'`,'DO NOT DISPLAY AS GENESIS DATA','ROOT / identité','GENESIS-002 / continuité','GENESIS-003 / prochaine question',"Pyramide / terrain d'entraînement",'GESIS / observatoire','LIVE_READ_ONLY_ACTIVE','public-live-active'])if(!html.includes(marker))fail(`Marqueur cockpit absent: ${marker}`);
  if(html.includes('href="/generator/"'))fail('Le cockpit Genesis ne doit pas pointer vers /generator/.');
  if(html.includes('Topbrutus/seedgenesis')||html.includes('git@github.com:Topbrutus/seedgenesis.git'))fail('Le cockpit ne doit contenir aucune référence vers la source privée.');

  const liveResponse=await fetch(`${base}/live/public-read-only.json`);
  if(liveResponse.status!==404)fail(`Le LIVE ne doit pas être prépublié dans le bundle statique avant activation: ${liveResponse.status}`);

  const dataResponse=await fetch(`${base}/snapshot/genesis-public-snapshot-0001.json`);if(!dataResponse.ok)fail(`snapshot 0001 inaccessible ${dataResponse.status}`);const data=await dataResponse.json();if(data.contract_version!==EXPECTED_CONTRACT)fail('Contrat JSON inattendu.');if(data.mode!=='SNAPSHOT'||data.source_status!=='PUBLIC_SNAPSHOT'||data.integrity_status!=='VERIFIED_PUBLIC')fail('Le snapshot doit rester SNAPSHOT/PUBLIC_SNAPSHOT/VERIFIED_PUBLIC.');if(data.publication_id!=='GENESIS-PUBLIC-SNAPSHOT-0001')fail('publication_id snapshot inattendu.');const live=data.payload?.publication_gates?.gates?.find(g=>g.id==='live-read-only');if(live?.status!=='PENDING')fail('Le snapshot fallback doit conserver LIVE_READ_ONLY=PENDING.');
  const privateResponse=await fetch(`${base}/private/genesis-state.json`);if(privateResponse.status!==404)fail('Une route privée fictive ne doit pas être servie.');
  console.log('GENESIS_COCKPIT_SMOKE_VALID');console.log(JSON.stringify({ok:true,contract:data.contract_version,predeploy_live_status:liveResponse.status,fallback_mode:data.mode,fallback_source_status:data.source_status,fallback_publication_id:data.publication_id,fallback_integrity_status:data.integrity_status,fallback_live_gate:live.status,private_route_status:privateResponse.status},null,2));
}catch(e){console.error('GENESIS_COCKPIT_SMOKE_INVALID');console.error(e instanceof Error?e.message:String(e));process.exitCode=1}
finally{await new Promise(resolve=>server.close(resolve))}
