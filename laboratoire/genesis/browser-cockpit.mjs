#!/usr/bin/env node
import { createServer } from 'node:http';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const ROOT=fileURLToPath(new URL('./',import.meta.url));
const REPO_ROOT=fileURLToPath(new URL('../../',import.meta.url));
const EVIDENCE_DIR=join(REPO_ROOT,'.build','genesis-browser-evidence');
const SNAPSHOT=JSON.parse(await readFile(join(ROOT,'snapshot','genesis-public-snapshot-0001.json'),'utf8'));
const MIME=new Map([['.html','text/html; charset=utf-8'],['.json','application/json; charset=utf-8'],['.md','text/markdown; charset=utf-8'],['.mjs','text/javascript; charset=utf-8']]);
function fail(m){throw new Error(m)}
function assert(v,m){if(!v)fail(m)}
function resolvePath(urlPath){const decoded=decodeURIComponent((urlPath??'/').split('?')[0]);const rel=decoded==='/'?'index.html':decoded.replace(/^\/+/, '');const norm=normalize(rel);if(norm.startsWith('..')||norm.includes('/../')||norm.includes('\\..\\'))fail('Traversal refusé.');return join(ROOT,norm)}
const server=createServer(async(req,res)=>{try{const body=await readFile(resolvePath(req.url));res.statusCode=200;res.setHeader('content-type',MIME.get(extname(resolvePath(req.url)))??'application/octet-stream');res.setHeader('cache-control','no-store');res.end(body)}catch{res.statusCode=404;res.end('Not Found')}});
await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve)});
let browser;
async function txt(page,s){return (await page.locator(s).textContent())?.trim()??''}
async function verify(base,name,viewport){
  const context=await browser.newContext({viewport,deviceScaleFactor:1});const page=await context.newPage();const errors=[],requests=[],responses=[];
  page.on('console',m=>{if(m.type()==='error')errors.push(`console:${m.text()}`)});page.on('pageerror',e=>errors.push(`page:${e.message}`));
  page.on('request',r=>{const u=new URL(r.url());if(u.origin===base)requests.push(u.pathname)});page.on('response',r=>{const u=new URL(r.url());if(u.origin===base)responses.push({path:u.pathname,status:r.status()})});
  try{
    const response=await page.goto(`${base}/`,{waitUntil:'networkidle'});assert(response?.ok(),`${name}: index`);
    assert((await page.title())==='Genesis Vision Center — LIVE / SNAPSHOT',`${name}: title`);
    await page.locator('#cockpit').waitFor({state:'visible',timeout:5000});
    assert((await txt(page,'#dataBanner'))==='SNAPSHOT FALLBACK / PUBLIC DATA',`${name}: banner`);
    assert((await txt(page,'#mode'))==='SNAPSHOT',`${name}: mode`);assert((await txt(page,'#sourceStatus'))==='PUBLIC_SNAPSHOT',`${name}: source`);assert((await txt(page,'#integrityStatus'))==='VERIFIED_PUBLIC',`${name}: integrity`);assert((await txt(page,'#liveReadOnly'))==='PENDING',`${name}: live gate`);
    assert((await txt(page,'#rootDigest'))===SNAPSHOT.payload.identity.root_digest,`${name}: digest`);
    assert((await txt(page,'#viewEyebrow')).includes('Snapshot fallback'),`${name}: fallback label`);
    const live=responses.find(x=>x.path==='/live/public-read-only.json');const snap=responses.find(x=>x.path==='/snapshot/genesis-public-snapshot-0001.json');assert(live?.status===404,`${name}: LIVE must be absent before activation`);assert(snap?.status===200,`${name}: snapshot`);
    assert(requests.includes('/live/public-read-only.json')&&requests.includes('/snapshot/genesis-public-snapshot-0001.json'),`${name}: fallback request chain`);assert(!requests.some(x=>x.startsWith('/private/')),`${name}: private request`);assert(errors.length===0,`${name}: ${errors.join('|')}`);assert(!(await page.locator('#fatal').isVisible()),`${name}: fatal`);
    const geo=await page.evaluate(()=>({w:innerWidth,sw:document.documentElement.scrollWidth}));assert(geo.sw<=geo.w+1,`${name}: overflow`);
    await page.screenshot({path:join(EVIDENCE_DIR,`${name}.png`),fullPage:true});return {viewport:name,live_status:live.status,snapshot_status:snap.status,requested_paths:[...new Set(requests)],errors:0,overflow:false};
  }finally{await context.close()}
}
try{
  const a=server.address();if(!a||typeof a==='string')fail('Port indisponible');const base=`http://127.0.0.1:${a.port}`;await mkdir(EVIDENCE_DIR,{recursive:true});browser=await chromium.launch({headless:true});const viewports=[await verify(base,'desktop',{width:1440,height:1100}),await verify(base,'mobile',{width:390,height:844})];const report={ok:true,test:'GENESIS_LIVE_CAPABLE_SNAPSHOT_FALLBACK_BROWSER',browser:'Chromium',browser_version:browser.version(),display_mode:'SNAPSHOT_FALLBACK',contract:'2.0.0-draft',snapshot_publication:'GENESIS-PUBLIC-SNAPSHOT-0001',live_endpoint_predeployed:false,snapshot_fallback_verified:true,private_genesis_connected:false,generator_modified:false,viewports};await writeFile(join(EVIDENCE_DIR,'REPORT.json'),`${JSON.stringify(report,null,2)}\n`);console.log('GENESIS_COCKPIT_BROWSER_VALID');console.log(JSON.stringify(report,null,2));
}catch(e){console.error('GENESIS_COCKPIT_BROWSER_INVALID');console.error(e instanceof Error?e.stack??e.message:String(e));process.exitCode=1}
finally{if(browser)await browser.close();await new Promise(resolve=>server.close(resolve))}
