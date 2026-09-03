#!/usr/bin/env node
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT=fileURLToPath(new URL('./',import.meta.url));
const EXPECTED_BANNER='DEMO / SYNTHETIC DATA';
const EXPECTED_DATA_PATH='./demo/genesis-demo-v2.json';
const EXPECTED_CONTRACT='2.0.0-draft';
const MIME=new Map([['.html','text/html; charset=utf-8'],['.json','application/json; charset=utf-8'],['.md','text/markdown; charset=utf-8'],['.mjs','text/javascript; charset=utf-8']]);
function fail(m){throw new Error(m)}
function resolvePath(urlPath){const decoded=decodeURIComponent((urlPath??'/').split('?')[0]);const rel=decoded==='/'?'index.html':decoded.replace(/^\/+/,'');const norm=normalize(rel);if(norm.startsWith('..')||norm.includes('/../')||norm.includes('\\..\\'))fail('Traversal refusé.');return join(ROOT,norm)}
const server=createServer(async(req,res)=>{try{const f=resolvePath(req.url);const body=await readFile(f);res.statusCode=200;res.setHeader('content-type',MIME.get(extname(f))??'application/octet-stream');res.setHeader('cache-control','no-store');res.end(body)}catch{res.statusCode=404;res.end('Not Found')}})
await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve)});
try{
  const address=server.address();if(!address||typeof address==='string')fail('Port indisponible.');const base=`http://127.0.0.1:${address.port}`;
  const indexResponse=await fetch(`${base}/`);if(!indexResponse.ok)fail(`index inaccessible ${indexResponse.status}`);const html=await indexResponse.text();
  for(const marker of ['<title>Genesis Vision Center — DEMO</title>',EXPECTED_BANNER,`const DATA_PATH='./demo/genesis-demo-v2.json'`,`const EXPECTED_CONTRACT='2.0.0-draft'`,'DO NOT DISPLAY AS GENESIS DATA','ROOT / identité','GENESIS-002 / continuité','GENESIS-003 / prochaine question',"Pyramide / terrain d'entraînement",'GESIS / observatoire'])if(!html.includes(marker))fail(`Marqueur cockpit absent: ${marker}`);
  if(!html.includes('href="/generator/"'))fail('Lien vers le générateur Antmux absent.');
  const dataResponse=await fetch(`${base}/demo/genesis-demo-v2.json`);if(!dataResponse.ok)fail(`snapshot v2 inaccessible ${dataResponse.status}`);const data=await dataResponse.json();if(data.contract_version!==EXPECTED_CONTRACT)fail('Contrat JSON inattendu.');if(data.mode!=='DEMO'||data.source_status!=='SYNTHETIC')fail('Le snapshot v2 doit rester DEMO/SYNTHETIC.');if(data.payload?.observatory?.scientific_rule!=='MESURE != INTERPRÉTATION')fail('Règle MESURE != INTERPRÉTATION absente.');
  const privateResponse=await fetch(`${base}/private/genesis-state.json`);if(privateResponse.status!==404)fail('Une route privée fictive ne doit pas être servie.');
  console.log('GENESIS_COCKPIT_SMOKE_VALID');console.log(JSON.stringify({ok:true,contract:data.contract_version,mode:data.mode,source_status:data.source_status,publication_id:data.publication_id,private_route_status:privateResponse.status},null,2));
}catch(e){console.error('GENESIS_COCKPIT_SMOKE_INVALID');console.error(e instanceof Error?e.message:String(e));process.exitCode=1}
finally{await new Promise(resolve=>server.close(resolve))}
