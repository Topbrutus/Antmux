(()=>{
"use strict";

const KEY="BRUTUS_GLOBAL_FONT_V1";
const CHANNEL_NAME="BRUTUS_GLOBAL_FONT_V1";
const MIN=0.80,MAX=1.80,STEP=0.10;
const TYPO_SELECTOR="button,span,div,p,h1,h2,h3,h4,label,input,select,textarea,pre,td,th,strong,em,small,a";
const MODULE_SELECTOR=".foldablePanel,.panel,.engine,.t1Panel,.dialRack,.freqAutomation,.audioOutputPanel,.controlLaunchBar,.workspaceSurface,.workspaceWindowMenu,.workspaceToolbar,.workspaceIcons,.workspaceIcon,.panelMiniOverlay,.panelMiniIcon";
let channel=null;
let scale=1;

const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const round2=v=>Math.round(v*100)/100;

function load(){
  try{
    const raw=JSON.parse(localStorage.getItem(KEY)||"null");
    if(raw&&typeof raw==="object")scale=round2(clamp(Number(raw.scale)||1,MIN,MAX));
  }catch(_){}
}
function save(broadcast=true){
  try{localStorage.setItem(KEY,JSON.stringify({version:1,scale,updatedAt:Date.now()}))}catch(_){}
  if(broadcast&&channel)channel.postMessage({type:"FONT_SCALE",scale});
}
function isModuleElement(el){
  return !!el.closest?.(MODULE_SELECTOR);
}
function collect(root=document){
  const all=root===document
    ?[...document.querySelectorAll(TYPO_SELECTOR)]
    :[
      ...(root.matches?.(TYPO_SELECTOR)?[root]:[]),
      ...((root.querySelectorAll&&root.querySelectorAll(TYPO_SELECTOR))||[])
    ];
  return all.filter(el=>{
    if(isModuleElement(el))return false;
    if(el.closest?.("script,style,svg,canvas"))return false;
    const fs=Number.parseFloat(getComputedStyle(el).fontSize);
    return Number.isFinite(fs)&&fs>0;
  });
}
function apply(root=document){
  for(const el of collect(root)){
    if(!el.dataset.brutusGlobalFontBasePx){
      const current=Number.parseFloat(getComputedStyle(el).fontSize);
      if(Number.isFinite(current)&&current>0)el.dataset.brutusGlobalFontBasePx=String(current/(Number(el.dataset.brutusGlobalFontApplied)||1));
    }
    const base=Number(el.dataset.brutusGlobalFontBasePx);
    if(!Number.isFinite(base)||base<=0)continue;
    el.style.fontSize=(base*scale).toFixed(2)+"px";
    el.dataset.brutusGlobalFontApplied=String(scale);
  }
  updateReadout();
}
function updateReadout(){
  const r=document.getElementById("globalFontReadout");
  if(r)r.textContent=Math.round(scale*100)+"%";
}
function setScale(next,broadcast=true){
  scale=round2(clamp(Number(next)||1,MIN,MAX));
  apply(document);
  save(broadcast);
}
function bindControls(){
  const minus=document.getElementById("globalFontMinus");
  const plus=document.getElementById("globalFontPlus");
  if(minus&&!minus.dataset.fontBound){
    minus.dataset.fontBound="1";
    minus.addEventListener("click",e=>{e.preventDefault();e.stopPropagation();setScale(scale-STEP)});
  }
  if(plus&&!plus.dataset.fontBound){
    plus.dataset.fontBound="1";
    plus.addEventListener("click",e=>{e.preventDefault();e.stopPropagation();setScale(scale+STEP)});
  }
  updateReadout();
}
function installSync(){
  if("BroadcastChannel" in window){
    channel=new BroadcastChannel(CHANNEL_NAME);
    channel.onmessage=e=>{
      const m=e.data||{};
      if(m.type!=="FONT_SCALE")return;
      scale=round2(clamp(Number(m.scale)||1,MIN,MAX));
      apply(document);
    };
  }
  addEventListener("storage",e=>{
    if(e.key!==KEY||!e.newValue)return;
    try{
      const m=JSON.parse(e.newValue);
      scale=round2(clamp(Number(m.scale)||1,MIN,MAX));
      apply(document);
    }catch(_){}
  });
}
function installObserver(){
  const observer=new MutationObserver(mutations=>{
    for(const mutation of mutations){
      for(const node of mutation.addedNodes){
        if(node.nodeType===1&&!isModuleElement(node))apply(node);
      }
    }
  });
  observer.observe(document.body,{childList:true,subtree:true});
}
function init(){
  load();
  bindControls();
  installSync();
  apply(document);
  installObserver();
  dispatchEvent(new CustomEvent("BRUTUS_GLOBAL_FONT_READY",{detail:{scale}}));
}
if(document.readyState==="loading")addEventListener("DOMContentLoaded",init,{once:true});else init();
})();