import test from "node:test";
import assert from "node:assert/strict";
import vm from "node:vm";
import { readFile } from "node:fs/promises";

const html=await readFile(new URL("../index.html",import.meta.url),"utf8");

function extractFunction(name){
  const markers=["async function "+name+"(","function "+name+"("];
  let start=-1;
  for(const marker of markers){start=html.indexOf(marker);if(start!==-1)break;}
  assert.notEqual(start,-1,name+" not found");
  const open=html.indexOf("(",start);
  let pd=0,quote=null,esc=false,close=-1;
  for(let i=open;i<html.length;i++){
    const ch=html[i];
    if(quote){if(esc)esc=false;else if(ch==="\\")esc=true;else if(ch===quote)quote=null;continue;}
    if(ch==="\'"||ch==='"'){quote=ch;continue;}
    if(ch==="(")pd++;
    if(ch===")"&&--pd===0){close=i;break;}
  }
  const brace=html.indexOf("{",close);
  let depth=0;quote=null;esc=false;
  for(let i=brace;i<html.length;i++){
    const ch=html[i];
    if(quote){if(esc)esc=false;else if(ch==="\\")esc=true;else if(ch===quote)quote=null;continue;}
    if(ch==="\'"||ch==='"'){quote=ch;continue;}
    if(ch==="{")depth++;
    if(ch==="}"&&--depth===0)return html.slice(start,i+1);
  }
  throw new Error(name+" closing brace not found");
}

function makeContext(){
  const ctx={console,Object,Array,String,Number,Math,JSON,BigInt,TypeError,RangeError,Error,Promise,Date};
  vm.createContext(ctx);
  const prelude=[
    "const ZEL_RADIX_BASES=Object.freeze(Array.from({length:12},(_,i)=>i+2));",
    "function zelEvolutionExactInt(value){",
    "  if(typeof value===\'bigint\')return value;",
    "  if(typeof value===\'number\'&&Number.isSafeInteger(value))return BigInt(value);",
    "  if(typeof value===\'string\'&&/^[+-]?\\d+$/.test(value.trim()))return BigInt(value.trim());",
    "  throw new RangeError(\'exact integer required\');",
    "}"
  ].join("\n");
  const names=["zelRadixAssertBase","zelRadixDigitValue","zelRadixEncodeExact","zelRadixDecodeExact","zelRadixBraid","zelRadixBraidAudioStages","zelRadixBraidAudioPasses"];
  vm.runInContext(prelude+"\n"+names.map(extractFunction).join("\n"),ctx);
  return ctx;
}

test("ZX radix braid uses exactly bases 2 through 13 and creates 144 unique paths",()=>{
  const ctx=makeContext();
  const r=ctx.zelRadixBraid(255);
  assert.deepEqual(Array.from(r.bases),[2,3,4,5,6,7,8,9,10,11,12,13]);
  assert.equal(r.source_lanes,12);
  assert.equal(r.path_count,144);
  assert.equal(r.source_passed,12);
  assert.equal(r.passed_paths,144);
  assert.equal(r.failed_paths,0);
  assert.equal(r.ok,true);
  const ids=r.lanes.flatMap(l=>Array.from(l.paths,p=>p.path_id));
  assert.equal(new Set(ids).size,144);
  assert.equal(r.lanes[0].representation,"11111111");
  assert.equal(r.lanes.at(-1).representation,"168");
});

test("every base-to-base path reconstructs huge positive and negative integers exactly",()=>{
  const ctx=makeContext();
  for(const input of ["0","1","-273","90071992547409931234567890123456789","-99999999999999999999999999999999999999"]){
    const r=ctx.zelRadixBraid(input);
    assert.equal(r.root,input.replace(/^\+/,""));
    assert.equal(r.ok,true);
    assert.equal(r.passed_paths,144);
    assert.ok(r.lanes.every(l=>l.paths.every(p=>p.canonical===r.root&&p.ok===true)));
  }
});

test("radix decoder rejects digits that do not belong to the selected base",()=>{
  const ctx=makeContext();
  assert.throws(()=>ctx.zelRadixDecodeExact("2",2),/invalid for base 2/);
  assert.throws(()=>ctx.zelRadixDecodeExact("D",13),/invalid for base 13/);
  assert.throws(()=>ctx.zelRadixDecodeExact("",10),/representation required/);
  assert.throws(()=>ctx.zelRadixEncodeExact(7,14),/2 through 13/);
});

test("radix sonic trace exposes 12 audible base lanes, 144 braid paths, invariant and return",()=>{
  const ctx=makeContext();
  const r=ctx.zelRadixBraid(47);
  const stages=ctx.zelRadixBraidAudioStages(r);
  assert.equal(stages.length,16);
  assert.match(stages[0].label,/ENTREE ZX/);
  for(let i=0;i<12;i++)assert.match(stages[i+1].label,new RegExp("BASE "+(i+2)));
  assert.match(stages[13].label,/144 chemins/);
  assert.equal(stages[14].exact,"144/144");
  assert.equal(stages[14].status,"PASS");
  assert.equal(stages[15].exact,"47");
  assert.equal(stages[15].status,"PASS");
});


test("radix audio is partitioned into two legal seven-stage waves",()=>{
  const ctx=makeContext();
  const r=ctx.zelRadixBraid(47);
  const bundle=ctx.zelRadixBraidAudioPasses(r);
  assert.equal(bundle.passes.length,2);
  assert.deepEqual(Array.from(bundle.passes,p=>p.length),[7,7]);
  assert.match(bundle.passes[0][0].label,/ENTREE ZX/);
  assert.match(bundle.passes[0][1].label,/BASE 2/);
  assert.match(bundle.passes[0][6].label,/BASE 7/);
  assert.match(bundle.passes[1][0].label,/BASE 8/);
  assert.match(bundle.passes[1][5].label,/BASE 13/);
  assert.match(bundle.passes[1][6].label,/144\/144/);
  assert.equal(bundle.passes[1][6].status,"PASS");
});
