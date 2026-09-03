#!/usr/bin/env node
import { createServer } from 'node:http';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const ROOT=fileURLToPath(new URL('./',import.meta.url));
const REPO_ROOT=fileURLToPath(new URL('../../',import.meta.url));
const EVIDENCE_DIR=join(REPO_ROOT,'.build','genesis-browser-evidence');
const DATA=JSON.parse(await readFile(join(ROOT,'demo','genesis-demo-v2.json'),'utf8'));
const EXPECTED={title:'Genesis Vision Center — DEMO',banner:'DEMO / SYNTHETIC DATA',contract:'2.0.0-draft',mode:'DEMO',source:'SYNTHETIC',publication:DATA.publication_id};
const MIME=new Map([['.html','text/html; charset=utf-8'],['.json','application/json; charset=utf-8'],['.md','text/markdown; charset=utf-8'],['.mjs','text/javascript; charset=utf-8']]);

function fail(m){throw new Error(m)} function assert(c,m){if(!c)fail(m)}
function resolvePath(urlPath){const decoded=decodeURIComponent((urlPath??'/').split('?')[0]);const rel=decoded==='/'?'index.html':decoded.replace(/^\/+/,'');const norm=normalize(rel);if(norm.startsWith('..')||norm.includes('/../')||norm.includes('\\..\\'))fail('Traversal refusé.');return join(ROOT,norm)}
const server=createServer(async(req,res)=>{try{const f=resolvePath(req.url);const body=await readFile(f);res.statusCode=200;res.setHeader('content-type',MIME.get(extname(f))??'application/octet-stream');res.setHeader('cache-control','no-store');res.end(body)}catch{res.statusCode=404;res.end('Not Found')}})
await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve)});
let browserInstance;

async function text(page,s){return (await page.locator(s).textContent())?.trim()??''}
async function verify(base,name,viewport){
  const context=await browserInstance.newContext({viewport,deviceScaleFactor:1});const page=await context.newPage();const consoleErrors=[],pageErrors=[],requests=[];
  page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text())});page.on('pageerror',e=>pageErrors.push(e.message));page.on('request',r=>{const u=new URL(r.url());if(u.origin===base)requests.push(u.pathname)});
  try{
    const response=await page.goto(`${base}/`,{waitUntil:'networkidle'});assert(response?.ok(),`${name}: index HTTP invalide`);
    assert((await page.title())===EXPECTED.title,`${name}: titre inattendu`);
    await page.locator('#cockpit').waitFor({state:'visible',timeout:5000});
    assert(await page.locator('#demoBanner').isVisible(),`${name}: bannière absente`);assert((await text(page,'#demoBanner'))===EXPECTED.banner,`${name}: bannière incorrecte`);assert((await text(page,'#contractVersion'))===EXPECTED.contract,`${name}: contrat incorrect`);assert((await text(page,'#mode'))===EXPECTED.mode,`${name}: mode incorrect`);assert((await text(page,'#sourceStatus'))===EXPECTED.source,`${name}: source incorrect`);assert((await text(page,'#publicationId'))===EXPECTED.publication,`${name}: publication incorrecte`);
    for(const selector of ['#rootStatus','#cycle','#nextTest','#trainingObservations','#scientificRule','#publicationGates','#returnStatus']) assert(await page.locator(selector).count()===1,`${name}: section ${selector} absente`);
    assert((await text(page,'#scientificRule'))==='MESURE != INTERPRÉTATION',`${name}: règle scientifique affaiblie`);
    assert((await text(page,'#nextTest'))===DATA.payload.metacognition.next_test,`${name}: prochain test DEMO incorrect`);
    assert((await text(page,'#returnStatus'))==='PASSED',`${name}: retour SOURCE non fermé`);
    const cycleNodes=await page.locator('#genesisCycle .node').count();assert(cycleNodes===(DATA.payload.pipeline.steps.length),`${name}: cycle incomplet`);
    const cycleStatuses=(await page.locator('#genesisCycle .node .badge').allTextContents()).map(v=>v.trim());assert(cycleStatuses.length===7,`${name}: statuts cycle incomplets`);assert(cycleStatuses.every(v=>v==='PASSED'),`${name}: le cycle 1→7 n'est pas entièrement PASSED`);assert(cycleStatuses.slice(4).every(v=>v==='PASSED'),`${name}: DEMO 5→6→7 non fermé`);
    const observationCount=await page.locator('#trainingObservations .item').count();assert(observationCount===DATA.payload.training_field.observations.length,`${name}: observations incomplètes`);const gateCount=await page.locator('#publicationGates .item').count();assert(gateCount===DATA.payload.publication_gates.gates.length,`${name}: gates incomplets`);
    const fatalVisible=await page.locator('#fatal').isVisible();assert(!fatalVisible,`${name}: verrou fatal visible`);const geo=await page.evaluate(()=>({w:innerWidth,sw:document.documentElement.scrollWidth,hidden:document.getElementById('cockpit')?.hidden??true}));assert(!geo.hidden,`${name}: cockpit hidden`);assert(geo.sw<=geo.w+1,`${name}: débordement horizontal`);assert(consoleErrors.length===0,`${name}: console.error ${consoleErrors.join('|')}`);assert(pageErrors.length===0,`${name}: pageerror ${pageErrors.join('|')}`);assert(!requests.some(p=>p.startsWith('/private/')),`${name}: requête privée détectée`);
    await page.screenshot({path:join(EVIDENCE_DIR,`${name}.png`),fullPage:true});return {viewport:name,size:viewport,rendered:true,cycle_nodes:cycleNodes,cycle_statuses:cycleStatuses,cycle_5_6_7_passed:cycleStatuses.slice(4).every(v=>v==='PASSED'),training_observations:observationCount,publication_gates:gateCount,requested_paths:[...new Set(requests)],horizontal_overflow:false,browser_console_errors:0,browser_page_errors:0};
  }finally{await context.close()}
}
try{
  const address=server.address();if(!address||typeof address==='string')fail('Port de test indisponible');const base=`http://127.0.0.1:${address.port}`;await mkdir(EVIDENCE_DIR,{recursive:true});browserInstance=await chromium.launch({headless:true});const version=browserInstance.version();const viewports=[await verify(base,'desktop',{width:1440,height:1100}),await verify(base,'mobile',{width:390,height:844})];const report={ok:true,lab:'LAB-004',test:'GENESIS_VISION_CENTER_V2_BROWSER',browser:'Chromium',browser_version:version,contract:EXPECTED.contract,mode:EXPECTED.mode,source_status:EXPECTED.source,publication_id:EXPECTED.publication,cycle_5_6_7:'PASSED',private_genesis_connected:false,generator_modified:false,viewports};await writeFile(join(EVIDENCE_DIR,'REPORT.json'),`${JSON.stringify(report,null,2)}\n`,'utf8');console.log('GENESIS_COCKPIT_BROWSER_VALID');console.log(JSON.stringify(report,null,2));
}catch(e){console.error('GENESIS_COCKPIT_BROWSER_INVALID');console.error(e instanceof Error?e.stack??e.message:String(e));process.exitCode=1}
finally{if(browserInstance)await browserInstance.close();await new Promise(resolve=>server.close(resolve))}
