(()=>{
"use strict";
const SCHEMA="ANTMUX-BRUTUS-VERSO-MISSION-v1";
const RECEIPT_SCHEMA="ANTMUX-BRUTUS-VERSO-RECEIPT-v1";
const AUDIT_KEY="BRUTUS_VERSO_AUDIT_V1";
const MAX_COMMANDS=64;
const ACTIONS=Object.freeze([
  "STATE_SNAPSHOT",
  "WINDOW_LIST",
  "DESKTOP_SET",
  "WINDOW_OPEN",
  "WINDOW_CLOSE",
  "WINDOW_MINIMIZE",
  "WINDOW_ROUTE",
  "WINDOW_PLACE"
]);
const clone=value=>JSON.parse(JSON.stringify(value));
function control(){
  const ctl=window.BRUTUS_WORKSPACE_CONTROL;
  if(!ctl||typeof ctl.ready!=="function"||!ctl.ready())throw new Error("BRUTUS_VERSO_WORKSPACE_NOT_READY");
  return ctl;
}
function finite(value,name){
  const n=Number(value);
  if(!Number.isFinite(n))throw new TypeError(name+" must be finite");
  return n;
}
function screen(value){
  const n=Number(value);
  if(!Number.isInteger(n)||n<1||n>5)throw new RangeError("screen must be 1..5");
  return n;
}
function cardObject(input){
  const card=typeof input==="string"?JSON.parse(input):clone(input);
  if(!card||typeof card!=="object"||Array.isArray(card))throw new TypeError("mission card object required");
  if(card.schema!==SCHEMA)throw new Error("unsupported mission schema");
  if(typeof card.mission_id!=="string"||!card.mission_id.trim())throw new TypeError("mission_id required");
  if(!Array.isArray(card.commands)||card.commands.length<1||card.commands.length>MAX_COMMANDS)throw new RangeError("commands must contain 1.."+MAX_COMMANDS+" items");
  return card;
}
function commandResult(command,index){
  if(!command||typeof command!=="object"||Array.isArray(command))throw new TypeError("command "+index+" must be an object");
  const action=String(command.action||"").toUpperCase();
  if(!ACTIONS.includes(action))throw new Error("unsupported action:"+action);
  const ctl=control();
  switch(action){
    case "STATE_SNAPSHOT":
      return {action,ok:true,state:ctl.snapshot()};
    case "WINDOW_LIST":
      return {action,ok:true,windows:ctl.list()};
    case "DESKTOP_SET":
      return {action,ok:true,state:ctl.desktop(!!command.enabled)};
    case "WINDOW_OPEN":
      return {action,ok:true,window:ctl.open(String(command.window||""),command.screen===undefined?undefined:screen(command.screen))};
    case "WINDOW_CLOSE":
      return {action,ok:true,window:ctl.close(String(command.window||""))};
    case "WINDOW_MINIMIZE":
      return {action,ok:true,window:ctl.minimize(String(command.window||""))};
    case "WINDOW_ROUTE":
      return {action,ok:true,window:ctl.route(String(command.window||""),screen(command.screen))};
    case "WINDOW_PLACE":{
      const spec={};
      if(command.screen!==undefined)spec.screen=screen(command.screen);
      for(const k of ["x","y","w","h"])if(command[k]!==undefined)spec[k]=finite(command[k],k);
      spec.precise=!!command.precise;
      return {action,ok:true,window:ctl.place(String(command.window||""),spec)};
    }
    default:
      throw new Error("unsupported action:"+action);
  }
}
async function digest(value){
  const bytes=new TextEncoder().encode(JSON.stringify(value));
  const hash=await crypto.subtle.digest("SHA-256",bytes);
  return [...new Uint8Array(hash)].map(x=>x.toString(16).padStart(2,"0")).join("");
}
function audit(receipt){
  try{
    const rows=JSON.parse(localStorage.getItem(AUDIT_KEY)||"[]");
    const next=Array.isArray(rows)?rows:[];
    next.push(receipt);
    localStorage.setItem(AUDIT_KEY,JSON.stringify(next.slice(-100)));
  }catch(_){}
}
async function execute(input){
  const card=cardObject(input);
  const startedAt=Date.now();
  const results=[];
  let ok=true;
  for(let i=0;i<card.commands.length;i++){
    try{
      results.push(commandResult(card.commands[i],i));
    }catch(err){
      ok=false;
      results.push({
        action:String(card.commands[i]?.action||"UNKNOWN").toUpperCase(),
        ok:false,
        error:String(err?.message||err)
      });
      if(card.stop_on_error!==false)break;
    }
  }
  const receipt={
    schema:RECEIPT_SCHEMA,
    mission_id:card.mission_id,
    issued_by:String(card.issued_by||"UNSPECIFIED").slice(0,80),
    ok,
    started_at:startedAt,
    completed_at:Date.now(),
    command_count:card.commands.length,
    executed_count:results.length,
    results,
    final_state:control().snapshot()
  };
  receipt.mission_h256=await digest(card);
  receipt.receipt_h256=await digest(receipt);
  audit(receipt);
  dispatchEvent(new CustomEvent("BRUTUS_VERSO_RECEIPT",{detail:clone(receipt)}));
  return clone(receipt);
}
function example(){
  return {
    schema:SCHEMA,
    mission_id:"MISSION-"+Date.now(),
    issued_by:"ASTRA",
    stop_on_error:true,
    commands:[
      {action:"DESKTOP_SET",enabled:true},
      {action:"WINDOW_ROUTE",window:"CORE-ENGINE",screen:3},
      {action:"STATE_SNAPSHOT"}
    ]
  };
}
const api=Object.freeze({
  version:"1.0",
  schema:SCHEMA,
  receipt_schema:RECEIPT_SCHEMA,
  actions:ACTIONS,
  ready:()=>!!window.BRUTUS_WORKSPACE_CONTROL?.ready?.(),
  execute,
  snapshot:()=>control().snapshot(),
  example
});
Object.defineProperty(window,"BRUTUS_VERSO",{value:api,writable:false,configurable:false,enumerable:false});
dispatchEvent(new CustomEvent("BRUTUS_VERSO_READY",{detail:{version:api.version,schema:SCHEMA}}));
})();
