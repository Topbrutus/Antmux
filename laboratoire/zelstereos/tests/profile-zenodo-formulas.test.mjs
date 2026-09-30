import test from "node:test";
import assert from "node:assert/strict";
import vm from "node:vm";
import { readFile } from "node:fs/promises";

const html = await readFile(new URL("../index.html", import.meta.url), "utf8");

function extractFunction(name) {
  const markers=["async function "+name+"(","function "+name+"("];
  let start=-1;
  for(const marker of markers){
    start=html.indexOf(marker);
    if(start!==-1)break;
  }
  assert.notEqual(start,-1,name+" not found");
  const openParen=html.indexOf("(",start);
  let paren=0,quote=null,escaped=false,close=-1;
  for(let i=openParen;i<html.length;i++){
    const ch=html[i];
    if(quote){
      if(escaped)escaped=false;
      else if(ch==="\\")escaped=true;
      else if(ch===quote)quote=null;
      continue;
    }
    if(ch==="'"||ch==='"'){quote=ch;continue;}
    if(ch==="(")paren++;
    if(ch===")"){
      paren--;
      if(paren===0){close=i;break;}
    }
  }
  assert.notEqual(close,-1,name+" parameter list not closed");
  const brace=html.indexOf("{",close);
  let depth=0;
  quote=null;
  escaped=false;
  for(let i=brace;i<html.length;i++){
    const ch=html[i];
    if(quote){
      if(escaped)escaped=false;
      else if(ch==="\\")escaped=true;
      else if(ch===quote)quote=null;
      continue;
    }
    if(ch==="'"||ch==='"'){quote=ch;continue;}
    if(ch==="{")depth++;
    if(ch==="}"){
      depth--;
      if(depth===0)return html.slice(start,i+1);
    }
  }
  throw new Error(name+" closing brace not found");
}

function makeContext(){
  const ctx={console,Map,Set,Object,Array,String,Number,Math,JSON,BigInt,TypeError,RangeError,Error,Promise,Date,performance,setTimeout,clearTimeout};
  vm.createContext(ctx);
  const prelude="const ZEL_FORMULA_WAVE_MAX=2000; const ZEL_FORMULA_STATUSES=Object.freeze(['PASS','FAIL','DOMAIN','ERROR']); const zelFormulaBanks=new Map(); let zelProfileBankReady=null;";
  const names=[
    "zelFormulaSafeValue",
    "zelFormulaSummary",
    "zelFormulaNormalizeVerification",
    "zelFormulaQualifyOne",
    "zelFormulaQualifyDefinitions",
    "zelFormulaRegisterBank",
    "zelProfileZenodoAudit",
    "zelProfileGcd",
    "zelProfileFrac",
    "zelProfileAdd",
    "zelProfileSub",
    "zelProfileMul",
    "zelProfileDiv",
    "zelProfileAbs",
    "zelProfileCmp",
    "zelProfileFracText",
    "zelProfileFracValue",
    "zelProfilePositive",
    "zelProfileNonNegative",
    "zelProfileOffsetCore",
    "zelProfilePellRank",
    "zelProfileFormulaDefinitions",
    "zelRegisterProfileFormulaBank"
  ];
  vm.runInContext(prelude+names.map(extractFunction).join("\n"),ctx);
  return ctx;
}

test("profile audit excludes Boson and accounts for all 13 public profile records",()=>{
  const ctx=makeContext();
  const audit=ctx.zelProfileZenodoAudit();
  assert.equal(audit.length,13);
  const boson=audit.find(x=>x.record===22970584);
  assert.equal(boson.status,"EXCLUDED_USER_REQUEST");
  assert.equal(boson.reason,"BOSON_DE_BRUTUS");
  assert.equal(audit.filter(x=>x.status==="NON_FORMULA_ARCHITECTURE").length,1);
});

test("profile bank contains 12 executable definitions and no Boson provenance",async()=>{
  const ctx=makeContext();
  const defs=ctx.zelProfileFormulaDefinitions();
  assert.equal(defs.length,12);
  assert.equal(defs.some(x=>/22970584|boson/i.test(x.provenance_ref+x.name+x.normalized_formula)),false);
  const ready=await ctx.zelRegisterProfileFormulaBank();
  assert.equal(ready.status,"VERIFIED");
  assert.equal(ready.count,12);
  assert.equal(ready.rejected,0);
});

test("published 240.1 Hz coefficient and 1 fs construction remain exact",()=>{
  const ctx=makeContext();
  const defs=ctx.zelProfileFormulaDefinitions();
  const coeff=defs.find(x=>x.formula_id==="GSP-ZENODO-002").evaluate({delta_t:"1e-15"}).value;
  assert.equal(coeff.coefficient.exact,"5764801/100");
  const onefs=defs.find(x=>x.formula_id==="GSP-ZENODO-011").evaluate().value;
  assert.equal(onefs.delta_t.exact,"1/1000000000000000");
  assert.ok(Math.abs(onefs.f.decimal-240.10000000005765)<1e-12);
  assert.ok(onefs.delta_f.decimal>5.7648e-11&&onefs.delta_f.decimal<5.764802e-11);
  assert.ok(onefs.scaled_residual.decimal>1.38412e-7&&onefs.scaled_residual.decimal<1.38414e-7);
});

test("offset, correction and drift publication relations are internally consistent",()=>{
  const ctx=makeContext();
  const defs=ctx.zelProfileFormulaDefinitions();
  const f0="240.1";
  const one=defs.find(x=>x.formula_id==="GSP-ZENODO-011").evaluate().value;
  const offset=defs.find(x=>x.formula_id==="GSP-ZENODO-001").evaluate({f0:f0,f_obs:one.f.exact,target_dt:"1e-15",tolerance:"0"}).value;
  assert.equal(offset.pass,true);
  assert.equal(offset.residual_t.exact,"0");

  const f3=ctx.zelProfileDiv(ctx.zelProfileFrac(f0),ctx.zelProfileSub(1,ctx.zelProfileMul(ctx.zelProfileFrac(f0),ctx.zelProfileFrac("3e-15"))));
  const corr=defs.find(x=>x.formula_id==="GSP-ZENODO-010").evaluate({f0:f0,f_obs:ctx.zelProfileFracText(f3),target_dt:"1e-15",gain:".5"}).value;
  assert.equal(corr.residual_initial.exact,"1/500000000000000");
  assert.equal(corr.residual_final.exact,"1/1000000000000000");

  const f2=ctx.zelProfileDiv(ctx.zelProfileFrac(f0),ctx.zelProfileSub(1,ctx.zelProfileMul(ctx.zelProfileFrac(f0),ctx.zelProfileFrac("2e-15"))));
  const drift=defs.find(x=>x.formula_id==="GSP-ZENODO-012").evaluate({f0:f0,f1:one.f.exact,f2:ctx.zelProfileFracText(f2),t1:"0",t2:"10"}).value;
  assert.equal(drift.simplification_exact,true);
  assert.equal(drift.period_drift.exact,"1/10000000000000000");
});

test("Pell family and atlas formulas reproduce published anchors",()=>{
  const ctx=makeContext();
  const defs=ctx.zelProfileFormulaDefinitions();
  const sq=defs.find(x=>x.formula_id==="GSP-ZENODO-004").evaluate({k:3}).value;
  assert.equal(sq.rank,"1764");
  assert.equal(sq.root,"42");
  assert.equal(sq.square_check,true);
  const atlas=defs.find(x=>x.formula_id==="GSP-ZENODO-007");
  assert.equal(atlas.evaluate({m:"13",max_steps:100}).value.rank,7);
  assert.equal(atlas.evaluate({m:"73",max_steps:100}).value.rank,36);
});

test("failure mode, candidate gate, connected spectrum and X72 relations execute",()=>{
  const ctx=makeContext();
  const defs=ctx.zelProfileFormulaDefinitions();

  const failure=defs.find(x=>x.formula_id==="GSP-ZENODO-005").evaluate({
    residuals:["0","2e-18","3e-18","2.5e-18",".5e-18"],
    tolerance:"1e-18",
    k_min:3
  }).value;
  assert.equal(failure.K,3);
  assert.equal(failure.reproduced,true);
  assert.equal(failure.signature,"POSITIVE");

  const gate=defs.find(x=>x.formula_id==="GSP-ZENODO-006").evaluate({
    candidate:"3.0001",
    reference:"3",
    tolerance:".001"
  }).value;
  assert.equal(gate.decision,"SURVIVES_TEST");

  const connected=defs.find(x=>x.formula_id==="GSP-ZENODO-003").evaluate({
    samples:[[1,1],[1,-1],[-1,1],[-1,-1]],
    u:.1
  }).value;
  assert.ok(Math.abs(connected.K_Q)<1e-12);

  const daat=defs.find(x=>x.formula_id==="GSP-ZENODO-008").evaluate({
    G:[1,2,-3],
    D:[5,-2,7]
  }).value;
  assert.deepEqual(Array.from(daat.G_reconstructed),[1,2,-3]);
  assert.deepEqual(Array.from(daat.D_reconstructed),[5,-2,7]);

  const paths=defs.find(x=>x.formula_id==="GSP-ZENODO-009").evaluate().value;
  assert.equal(paths.ordered_paths,"479001600");
});
