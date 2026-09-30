import test from "node:test";
import assert from "node:assert/strict";
import vm from "node:vm";
import { readFile } from "node:fs/promises";

const html=await readFile(new URL("../index.html",import.meta.url),"utf8");

function extractFunction(name){
  const markers=["async function "+name+"(","function "+name+"("];
  let start=-1;
  for(const marker of markers){
    start=html.indexOf(marker);
    if(start!==-1)break;
  }
  assert.notEqual(start,-1,name+" not found");
  const open=html.indexOf("(",start);
  let pd=0,quote=null,esc=false,close=-1;
  for(let i=open;i<html.length;i++){
    const ch=html[i];
    if(quote){
      if(esc)esc=false;
      else if(ch==="\\")esc=true;
      else if(ch===quote)quote=null;
      continue;
    }
    if(ch==="'"||ch==='"'){quote=ch;continue;}
    if(ch==="(")pd++;
    if(ch===")"){
      pd--;
      if(pd===0){close=i;break;}
    }
  }
  const brace=html.indexOf("{",close);
  let depth=0;
  quote=null;
  esc=false;
  for(let i=brace;i<html.length;i++){
    const ch=html[i];
    if(quote){
      if(esc)esc=false;
      else if(ch==="\\")esc=true;
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
  const order=[];
  const ctx={
    console,Object,Array,String,Number,Math,JSON,BigInt,TypeError,RangeError,Error,Promise,Date,
    setTimeout,clearTimeout,
    aiPresentationHoldUntil:0,
    ZEL_TRIPLE_SLOT_IDS:Object.freeze(["A","B","C"]),
    zelTripleRunCounter:0,
    zelTripleWorker:null,
    zelTripleSlots:["A","B","C"].map((id,index)=>({
      slot:index+1,instance_id:"Z-"+id,status:"EMPTY",input:null,queued_at:null,started_at:null,
      completed_at:null,cascade_id:null,result:null,error:null
    })),
    order
  };
  vm.createContext(ctx);
  const stub=[
    "function zelEvolutionExactInt(value){",
    "  if(typeof value==='bigint')return value;",
    "  if(typeof value==='number'&&Number.isSafeInteger(value))return BigInt(value);",
    "  if(typeof value==='string'&&/^[+-]?\\d+$/.test(value.trim()))return BigInt(value.trim());",
    "  throw new RangeError('exact integer required');",
    "}",
    "async function zelEvolutionRunAudioTest(spec){",
    "  order.push('START:'+spec.input);",
    "  await new Promise(r=>setTimeout(r,5));",
    "  order.push('END:'+spec.input);",
    "  return {",
    "    ok:true,",
    "    cascade:{",
    "      status:'PASS',",
    "      actual_outputs:[9,108,1296],",
    "      total_formula_evaluations:1413,",
    "      zenodo_formula_evaluations:16956,",
    "      invariant_guards:{total:{checked:5301}},",
    "      total_calculation_events:23670,",
    "      inverse_verification:{ok:true,verified:1296},",
    "      final_nodes:Array.from({length:1296},()=>({}))",
    "    },",
    "    audio:{verdict:{cue:'RESISTE'}}",
    "  };",
    "}"
  ].join("\n");
  const names=[
    "zelTripleSequentialSnapshot",
    "zelTripleSequentialReset",
    "zelTripleSequentialWaitForAudioClear",
    "zelTripleSequentialPump",
    "zelTripleSequentialSubmit",
    "zelTripleSequentialWait",
    "zelTripleSequentialRun"
  ];
  vm.runInContext(stub+"\n"+names.map(extractFunction).join("\n"),ctx);
  return ctx;
}

test("three Z Stereo slots run strictly one after another with no overlap",async()=>{
  const ctx=makeContext();
  const final=await ctx.zelTripleSequentialRun([101,202,303]);
  assert.equal(final.capacity,3);
  assert.equal(final.completed,3);
  assert.equal(final.busy,false);
  assert.deepEqual(Array.from(final.slots,x=>x.instance_id),["Z-A","Z-B","Z-C"]);
  assert.deepEqual(Array.from(final.slots,x=>x.status),["PASS","PASS","PASS"]);
  assert.deepEqual(Array.from(final.slots,x=>x.input),["101","202","303"]);
  assert.deepEqual(Array.from(ctx.order),[
    "START:101","END:101",
    "START:202","END:202",
    "START:303","END:303"
  ]);
  assert.ok(final.slots.every(x=>x.result.verdict==="RESISTE"));
  assert.ok(final.slots.every(x=>x.result.zenodo_formula_evaluations===16956));
});

test("first number can start before second and third are known",async()=>{
  const ctx=makeContext();
  const first=ctx.zelTripleSequentialSubmit("11");
  assert.equal(first.filled,1);
  await new Promise(r=>setTimeout(r,1));
  const middle=ctx.zelTripleSequentialSnapshot();
  assert.equal(["RUNNING","PASS"].includes(middle.slots[0].status),true);
  assert.equal(middle.slots[1].status,"EMPTY");
  assert.equal(middle.slots[2].status,"EMPTY");
  ctx.zelTripleSequentialSubmit("22");
  ctx.zelTripleSequentialSubmit("33");
  const final=await ctx.zelTripleSequentialWait();
  assert.deepEqual(Array.from(final.slots,x=>x.status),["PASS","PASS","PASS"]);
  assert.deepEqual(Array.from(ctx.order),[
    "START:11","END:11",
    "START:22","END:22",
    "START:33","END:33"
  ]);
});

test("queue is capped at exactly three inputs and reset is blocked while busy",async()=>{
  const ctx=makeContext();
  ctx.zelTripleSequentialSubmit(1);
  ctx.zelTripleSequentialSubmit(2);
  ctx.zelTripleSequentialSubmit(3);
  assert.throws(()=>ctx.zelTripleSequentialSubmit(4),/TRIPLE_Z_QUEUE_FULL/);
  assert.throws(()=>ctx.zelTripleSequentialReset(),/TRIPLE_Z_BUSY/);
  await ctx.zelTripleSequentialWait();
  const reset=ctx.zelTripleSequentialReset();
  assert.equal(reset.filled,0);
  assert.deepEqual(Array.from(reset.slots,x=>x.status),["EMPTY","EMPTY","EMPTY"]);
});
