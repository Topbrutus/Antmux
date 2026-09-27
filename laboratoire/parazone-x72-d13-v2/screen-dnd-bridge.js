(()=>{
"use strict";
const frame=document.querySelector("iframe");
if(!frame)return;
const SCREEN=Number(new URL(frame.getAttribute("src"),location.href).searchParams.get("screen")||0);
const channel=("BroadcastChannel"in window)?new BroadcastChannel("BRUTUS_FRAME_DND_V1"):null;
let active=null,timer=null;
const overlay=document.createElement("div");
overlay.id="brutusFrameDropBridge";
overlay.innerHTML='<div><strong>DÉPOSER ICI</strong><span>SCREEN '+SCREEN+'</span></div>';
const css=document.createElement("style");
css.textContent='#brutusFrameDropBridge{display:none;position:fixed;inset:0;z-index:2147483647;background:#00131dcc;border:2px dashed #00e8ff;box-shadow:inset 0 0 80px #00e8ff33;align-items:center;justify-content:center;color:#dffcff;font:800 18px Consolas;letter-spacing:.08em}#brutusFrameDropBridge.active{display:flex}#brutusFrameDropBridge div{padding:24px 34px;border:1px solid #00e8ff;border-radius:10px;background:#03121fee;box-shadow:0 0 24px #00e8ff55;text-align:center}#brutusFrameDropBridge span{display:block;margin-top:8px;font-size:12px;color:#8fdfff}';
document.head.appendChild(css);document.body.appendChild(overlay);
function clearTimer(){if(timer){clearTimeout(timer);timer=null}}
function hide(){clearTimer();active=null;overlay.classList.remove("active")}
function show(m){if(!m||!m.key||Number(m.sourceScreen)===SCREEN)return;active={key:String(m.key),sourceScreen:Number(m.sourceScreen)||0};overlay.classList.add("active");clearTimer();timer=setTimeout(hide,15000)}
function broadcast(m){try{channel?.postMessage(m)}catch(_){}}
window.addEventListener("message",e=>{
  if(e.origin!==location.origin||e.source!==frame.contentWindow)return;
  const m=e.data||{};
  if(m.type==="BRUTUS_ICON_DRAG_START"){broadcast({type:"START",key:m.key,sourceScreen:Number(m.sourceScreen)||SCREEN})}
  if(m.type==="BRUTUS_ICON_DRAG_END"){broadcast({type:"END",key:m.key,sourceScreen:Number(m.sourceScreen)||SCREEN})}
});
if(channel)channel.onmessage=e=>{
  const m=e.data||{};
  if(m.type==="START")show(m);
  if(m.type==="END"&&(!active||!m.key||m.key===active.key))hide();
};
overlay.addEventListener("dragenter",e=>{if(active)e.preventDefault()});
overlay.addEventListener("dragover",e=>{if(!active)return;e.preventDefault();if(e.dataTransfer)e.dataTransfer.dropEffect="move"});
overlay.addEventListener("drop",e=>{
  if(!active)return;
  e.preventDefault();e.stopPropagation();
  const payload={type:"BRUTUS_ICON_DROP",key:active.key,targetScreen:SCREEN,clientX:e.clientX,clientY:e.clientY,shiftKey:!!e.shiftKey};
  frame.contentWindow?.postMessage(payload,location.origin);
  broadcast({type:"END",key:active.key,sourceScreen:active.sourceScreen});
  hide();
});
})();