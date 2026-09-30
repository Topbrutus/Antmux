import test from "node:test";
import assert from "node:assert/strict";
import vm from "node:vm";
import { readFile } from "node:fs/promises";

const html = await readFile(new URL("../index.html", import.meta.url), "utf8");

function extractFunction(name) {
  const asyncMarker = `async function ${name}(`;
  const syncMarker = `function ${name}(`;
  const asyncStart = html.indexOf(asyncMarker);
  const start = asyncStart !== -1 ? asyncStart : html.indexOf(syncMarker);
  assert.notEqual(start, -1, `${name} not found`);
  const openParen = html.indexOf("(", start);
  let pd=0,q=null,e=false,close=-1;
  for(let i=openParen;i<html.length;i++){
    const ch=html[i];
    if(q){if(e)e=false;else if(ch==="\\")e=true;else if(ch===q)q=null;continue;}
    if(ch==="'"||ch=='"'||ch==="`"){q=ch;continue;}
    if(ch==="(")pd++;
    if(ch===")"){pd--;if(pd===0){close=i;break;}}
  }
  const brace=html.indexOf("{",close);
  let depth=0;q=null;e=false;
  for(let i=brace;i<html.length;i++){
    const ch=html[i];
    if(q){if(e)e=false;else if(ch==="\\")e=true;else if(ch===q)q=null;continue;}
    if(ch==="'"||ch=='"'||ch==="`"){q=ch;continue;}
    if(ch==="{")depth++;
    if(ch==="}"){depth--;if(depth===0)return html.slice(start,i+1);}
  }
  throw new Error(name+" closing brace not found");
}

function loadVerdictCore(){
  const calls=[];
  const context={
    Object,String,Number,Math,
    clamp01:x=>Math.max(0,Math.min(1,Number(x)||0)),
    ZEL_AUDIO_CROSSFADE_SEC:.28,
    scheduleToneAt:(freq,start,dur,gain)=>calls.push({freq,start,dur,gain})
  };
  vm.createContext(context);
  vm.runInContext([
    extractFunction("zelVerdictNormalize"),
    extractFunction("soundVerdictPassAt"),
    extractFunction("soundVerdictFailAt"),
    extractFunction("soundVerdictInconclusiveAt"),
    extractFunction("soundVerdictAt"),
    extractFunction("zelVerdictDelaySec"),
  ].join("\n"),context);
  return {context,calls};
}

test("verdict vocabulary is unambiguous",()=>{
  const {context}=loadVerdictCore();
  assert.equal(context.zelVerdictNormalize("PASS"),"PASS");
  assert.equal(context.zelVerdictNormalize("RÉSISTE"),"PASS");
  assert.equal(context.zelVerdictNormalize("FAIL"),"FAIL");
  assert.equal(context.zelVerdictNormalize("CASSÉE"),"FAIL");
  assert.equal(context.zelVerdictNormalize("DOMAIN"),"DOMAIN");
  assert.equal(context.zelVerdictNormalize("ERROR"),"ERROR");
  assert.equal(context.zelVerdictNormalize("UNKNOWN"),null);
});

test("PASS and FAIL use distinct terminal sound signatures",()=>{
  const pass=loadVerdictCore();
  const passCue=pass.context.soundVerdictAt("PASS",10);
  const fail=loadVerdictCore();
  const failCue=fail.context.soundVerdictAt("FAIL",10);
  assert.deepEqual(passCue,{status:"PASS",cue:"RESISTE"});
  assert.deepEqual(failCue,{status:"FAIL",cue:"CASSEE"});
  assert.deepEqual(pass.calls.map(x=>x.freq),[523.25,659.25,783.99,1046.5]);
  assert.deepEqual(fail.calls.map(x=>x.freq),[329.63,220,146.83,98]);
});

test("DOMAIN and ERROR are inconclusive, never broken",()=>{
  for(const status of ["DOMAIN","ERROR"]){
    const {context,calls}=loadVerdictCore();
    const cue=context.soundVerdictAt(status,5);
    assert.equal(cue.status,status);
    assert.equal(cue.cue,"INCONCLUSIF");
    assert.equal(calls.length,3);
    assert.notDeepEqual(calls.map(x=>x.freq),[329.63,220,146.83,98]);
  }
});

test("verdict is delayed until final stage audio has cleared",()=>{
  const {context}=loadVerdictCore();
  const low=context.zelVerdictDelaySec(3.2,.24);
  const peak=context.zelVerdictDelaySec(3.2,.98);
  assert.ok(low>3.6);
  assert.ok(peak>4.1);
});

test("AI calculation accepts explicit verdict and returns scheduled cue",()=>{
  assert.match(html,/spec\.verdict\?\?spec\.final_status\?\?spec\.stages\?\.\[6\]\?\.verdict/);
  assert.match(html,/status:i===6\?\(verdict\|\|'PASS'\):'RUN'/);
  assert.match(html,/soundVerdictAt\(verdict,audioCtx\.currentTime\+verdictDelaySec\)/);
  assert.match(html,/verdict:verdictCue\?Object\.freeze\(\{\.\.\.verdictCue,delay_sec:verdictDelaySec\}\):null/);
});

test("public API exposes manual verdict audition and version 2.4",()=>{
  assert.match(html,/version:'2\.4'/);
  assert.match(html,/playVerdictSound:\(status\)=>/);
  assert.match(html,/verdictStatus:zelVerdictNormalize/);
});
