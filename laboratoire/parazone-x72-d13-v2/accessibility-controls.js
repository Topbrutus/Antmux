(()=>{
"use strict";

const SCREEN=Number(new URLSearchParams(location.search).get("screen")||0);
const KEY="BRUTUS_ACCESSIBILITY_V1";
const CHANNEL_NAME="BRUTUS_ACCESSIBILITY_V1";
const TEXT_MIN=0.80,TEXT_MAX=2.00,TEXT_STEP=0.10;
const ZOOM_MIN=0.75,ZOOM_MAX=1.50,ZOOM_STEP=0.05;
let channel=null;
let state={textScale:1,screen1Zoom:1};

function clamp(v,min,max){return Math.max(min,Math.min(max,v))}
function round2(v){return Math.round(v*100)/100}
function load(){
  try{
    const raw=JSON.parse(localStorage.getItem(KEY)||"null");
    if(raw&&typeof raw==="object"){
      state.textScale=clamp(Number(raw.textScale)||1,TEXT_MIN,TEXT_MAX);
      state.screen1Zoom=clamp(Number(raw.screen1Zoom)||1,ZOOM_MIN,ZOOM_MAX);
    }
  }catch(_){}
}
function save(broadcast=true){
  try{localStorage.setItem(KEY,JSON.stringify(state))}catch(_){}
  if(broadcast&&channel)channel.postMessage({type:"ACCESSIBILITY_STATE",state:{...state}});
}
function setGlobals(){
  window.BRUTUS_GLOBAL_TEXT_SCALE=state.textScale;
  window.BRUTUS_SCREEN1_ZOOM_FACTOR=state.screen1Zoom;
}
function textTargets(root=document){
  const selector="button,span,div,p,h1,h2,h3,label,input,select,textarea,pre,td,th,strong,em,small,a";
  const all=root===document?[...document.querySelectorAll(selector)]:[
    ...(root.matches?.(selector)?[root]:[]),
    ...root.querySelectorAll?.(selector)||[]
  ];
  return all.filter(el=>{
    if(el.closest("script,style,svg,canvas"))return false;
    const cs=getComputedStyle(el);
    return cs.display!=="none"&&Number.parseFloat(cs.fontSize)>0;
  });
}
function panelAdjustedBase(el){
  const base=Number(el.dataset.brutusBaseFontPx);
  if(!Number.isFinite(base)||base<=0)return null;
  const panel=el.closest(".foldablePanel");
  const panelScale=panel?Number(panel.dataset.textScale)||1:1;
  return base*panelScale;
}
function applyTextScale(){
  // Global font scaling moved to font-controls.js so modules keep independent typography.
}
function refreshZoom(){
  window.BRUTUS_SCREEN1_ZOOM_FACTOR=state.screen1Zoom;
  if(SCREEN===1&&typeof window.autoFitFiveScreen==="function")window.autoFitFiveScreen();
}
function updateReadouts(){
  const text=document.getElementById("globalTextReadout");
  const zoom=document.getElementById("screenZoomReadout");
  if(text)text.textContent=Math.round(state.textScale*100)+"%";
  if(zoom)zoom.textContent=Math.round(state.screen1Zoom*100)+"%";
}
function setTextScale(value,broadcast=true){
  state.textScale=round2(clamp(Number(value)||1,TEXT_MIN,TEXT_MAX));
  window.BRUTUS_GLOBAL_TEXT_SCALE=state.textScale;
  applyTextScale(document);
  updateReadouts();
  save(broadcast);
}
function setZoom(value,broadcast=true){
  state.screen1Zoom=round2(clamp(Number(value)||1,ZOOM_MIN,ZOOM_MAX));
  refreshZoom();
  updateReadouts();
  save(broadcast);
}
function button(label,title,handler){
  const b=document.createElement("button");
  b.type="button";
  b.className="screenAccessBtn";
  b.textContent=label;
  b.title=title;
  b.addEventListener("click",e=>{e.preventDefault();e.stopPropagation();handler()});
  return b;
}
function group(label,id,minus,plus){
  const g=document.createElement("span");
  g.className="screenAccessGroup";
  const name=document.createElement("span");
  name.className="screenAccessLabel";
  name.textContent=label;
  const readout=document.createElement("span");
  readout.id=id;
  readout.className="screenAccessReadout";
  g.append(name,minus,readout,plus);
  return g;
}
function installStyles(){
  const s=document.createElement("style");
  s.textContent=`
.screenTitleBar{gap:14px!important}
.screenStatusGroup{display:flex;align-items:center;gap:12px;white-space:nowrap}
.screenStatusDivider{display:inline-block;margin:0 3px;color:#315f9b}
#screenFitBadge{display:inline-block;min-width:64px;text-align:center;padding:0 7px;white-space:nowrap}
.screenAccessibilityControls{display:flex;align-items:center;gap:12px;flex-wrap:nowrap}
.screenAccessGroup{display:flex;align-items:center;gap:6px;padding:3px 7px;border:1px solid #234d6b;border-radius:6px;background:#04101b}
.screenAccessLabel{color:#6f9bb7;font:800 7px Consolas,monospace;letter-spacing:.08em}
.screenAccessBtn{width:28px;height:25px;padding:0;border:1px solid #315f9b;border-radius:5px;background:#071524;color:#c6efff;font:900 15px/1 Consolas,monospace;cursor:pointer}
.screenAccessBtn:hover{border-color:#00e8ff;color:#fff;box-shadow:0 0 8px #00e8ff33}
.screenAccessReadout{display:inline-block;min-width:58px;padding:0 8px;text-align:center;color:#dffcff;font:800 9px Consolas,monospace;white-space:nowrap}
@media(max-width:1050px){.screenAccessibilityControls{gap:6px}.screenAccessGroup{gap:4px;padding:3px 5px}.screenAccessReadout{min-width:52px;padding:0 5px}}
`;
  document.head.appendChild(s);
}
function installControls(){
  const host=document.getElementById("screenAccessibilityControls");
  if(!host||SCREEN!==1)return;
  host.hidden=false;
  host.innerHTML="";
  const zoomMinus=button("−","Zoom out SCREEN 1",()=>setZoom(state.screen1Zoom-ZOOM_STEP));
  const zoomPlus=button("+","Zoom in SCREEN 1",()=>setZoom(state.screen1Zoom+ZOOM_STEP));
  host.append(group("ZOOM","screenZoomReadout",zoomMinus,zoomPlus));
  updateReadouts();
}
function installSync(){
  if("BroadcastChannel" in window){
    channel=new BroadcastChannel(CHANNEL_NAME);
    channel.onmessage=e=>{
      const m=e.data||{};
      if(m.type!=="ACCESSIBILITY_STATE"||!m.state)return;
      state.textScale=round2(clamp(Number(m.state.textScale)||1,TEXT_MIN,TEXT_MAX));
      state.screen1Zoom=round2(clamp(Number(m.state.screen1Zoom)||1,ZOOM_MIN,ZOOM_MAX));
      setGlobals();
      applyTextScale(document);
      refreshZoom();
      updateReadouts();
    };
  }
  addEventListener("storage",e=>{
    if(e.key!==KEY||!e.newValue)return;
    try{
      const m=JSON.parse(e.newValue);
      state.textScale=round2(clamp(Number(m.textScale)||1,TEXT_MIN,TEXT_MAX));
      state.screen1Zoom=round2(clamp(Number(m.screen1Zoom)||1,ZOOM_MIN,ZOOM_MAX));
      setGlobals();
      applyTextScale(document);
      refreshZoom();
      updateReadouts();
    }catch(_){}
  });
}
function installObserver(){
  const observer=new MutationObserver(mutations=>{
    for(const mutation of mutations){
      for(const node of mutation.addedNodes){
        if(node.nodeType===1)applyTextScale(node);
      }
    }
  });
  observer.observe(document.body,{childList:true,subtree:true});
}
function init(){
  load();
  setGlobals();
  installStyles();
  installControls();
  installSync();
  applyTextScale(document);
  installObserver();
  refreshZoom();
  dispatchEvent(new CustomEvent("BRUTUS_ACCESSIBILITY_READY",{detail:{screen:SCREEN,textScale:state.textScale,screen1Zoom:state.screen1Zoom}}));
}
if(document.readyState==="loading")addEventListener("DOMContentLoaded",init,{once:true});else init();
})();
