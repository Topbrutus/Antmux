import fs from "node:fs";
import vm from "node:vm";
import crypto from "node:crypto";
import assert from "node:assert/strict";

globalThis.window=globalThis;
globalThis.crypto=crypto.webcrypto;
globalThis.CustomEvent=class CustomEvent{
  constructor(type,options={}){this.type=type;this.detail=options.detail}
};
const emitted=[];
globalThis.dispatchEvent=event=>{emitted.push(event);return true};
const store=new Map();
globalThis.localStorage={
  getItem:key=>store.has(key)?store.get(key):null,
  setItem:(key,value)=>store.set(key,String(value))
};

const calls=[];
let state={desktop_enabled:false};
const ctl={
  ready:()=>true,
  snapshot:()=>({schema:"TEST-WORKSPACE",...state}),
  list:()=>[{key:"CORE-ENGINE",screen:1}],
  desktop:enabled=>{calls.push(["desktop",enabled]);state.desktop_enabled=enabled;return ctl.snapshot()},
  open:(key,screen)=>{calls.push(["open",key,screen]);return{key,screen:screen??1}},
  close:key=>{calls.push(["close",key]);return{key,closed:true}},
  minimize:key=>{calls.push(["minimize",key]);return{key,minimized:true}},
  route:(key,screen)=>{calls.push(["route",key,screen]);return{key,screen}},
  place:(key,spec)=>{calls.push(["place",key,spec]);return{key,...spec}}
};
Object.defineProperty(globalThis,"BRUTUS_WORKSPACE_CONTROL",{value:ctl});

const source=fs.readFileSync(new URL("../verso-door.js",import.meta.url),"utf8");
vm.runInThisContext(source,{filename:"verso-door.js"});
assert.equal(BRUTUS_VERSO.version,"1.0");
assert.equal(BRUTUS_VERSO.ready(),true);

const card={
  schema:"ANTMUX-BRUTUS-VERSO-MISSION-v1",
  mission_id:"TEST-001",
  issued_by:"ASTRA",
  commands:[
    {action:"DESKTOP_SET",enabled:true},
    {action:"WINDOW_ROUTE",window:"CORE-ENGINE",screen:3},
    {action:"WINDOW_PLACE",window:"CORE-ENGINE",screen:3,x:16,y:48,w:720,h:560},
    {action:"STATE_SNAPSHOT"}
  ]
};
const receipt=await BRUTUS_VERSO.execute(card);
assert.equal(receipt.ok,true);
assert.equal(receipt.executed_count,4);
assert.match(receipt.mission_h256,/^[0-9a-f]{64}$/);
assert.match(receipt.receipt_h256,/^[0-9a-f]{64}$/);
assert.deepEqual(calls[0],["desktop",true]);
assert.deepEqual(calls[1],["route","CORE-ENGINE",3]);
assert.equal(calls[2][0],"place");
assert.equal(calls[2][2].screen,3);
assert.equal(JSON.parse(store.get("BRUTUS_VERSO_AUDIT_V1")).length,1);
assert.ok(emitted.some(event=>event.type==="BRUTUS_VERSO_RECEIPT"));

const rejected=await BRUTUS_VERSO.execute({
  schema:"ANTMUX-BRUTUS-VERSO-MISSION-v1",
  mission_id:"TEST-REJECT",
  commands:[{action:"EVAL_ARBITRARY_CODE",code:"nope"}]
});
assert.equal(rejected.ok,false);
assert.match(rejected.results[0].error,/unsupported action/);
assert.equal(calls.length,3);

console.log("BRUTUS_VERSO_MISSION_TEST=PASS");
