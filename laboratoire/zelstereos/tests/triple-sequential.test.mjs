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
  const stub=String.raw