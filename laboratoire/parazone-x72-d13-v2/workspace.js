(()=>{
"use strict";
const SCREEN=Number(new URLSearchParams(location.search).get("screen")||0);if(SCREEN<1||SCREEN>5)return;
const KEY="BRUTUS_DESKTOP_WORKSPACE_V1",CHAN="BRUTUS_DESKTOP_WORKSPACE_V1",GRID=16,MAGNET_RADIUS=92,ICON_TRANSFER_MIME="application/x-brutus-workspace-icon";let state,surface,icons,channel,z=30,applying=false,magnetGhost=null,windowMenu=null,windowMenuList=null;
const cards=new Map(),orig=new Map(),A=new Set(["ANALYSIS-AMP-01","ANALYSIS-HISTORY-01","TIMEBASE-01","SAMPLER-01","SAMPLER-QUALITY-01","CRACK-METER-01","CRACK-CLASSIFIER-01"]),O=new Set(["PRESET-BANK-01","REFERENCE-CATALOG-01","MICROPHONE-SOURCE-01","SIGNAL-GENERATOR-01"]),C=new Set(["INPUT-TEST-01","CONNECT-T2-01","CONNECT-T3-01","CONNECT-T4-01","CONNECT-T5-01"]);
const snap=v=>Math.round(v/GRID)*GRID,clamp=(v,a,b)=>Math.max(a,Math.min(b,v)),clone=x=>JSON.parse(JSON.stringify(x));
function keyOf(e){return e.dataset.workspaceKey||e.id||""} function labelOf(e,k){const h=e.querySelector(":scope > .panelControlBar > h2");if(h){const c=h.cloneNode(true);c.querySelectorAll(".panelId").forEach(x=>x.remove());if(c.textContent.trim())return c.textContent.trim()}return e.querySelector(":scope > .panelControlBar > .panelControlLabel")?.textContent?.trim()||k}
function home(e,k){if(e.dataset.desktopHome)return +e.dataset.desktopHome;if(e.closest(".layout"))return 1;if(e.closest(".monitorWall")||A.has(k))return 2;if(O.has(k)||/MICROPHONE|GENERATOR|PRESET|REFERENCE/.test(k))return 3;if(C.has(k)||/^CONNECT-T/.test(k))return 4;return 5}
function size(k,e){if(k==="CORE-ENGINE")return[720,560];if(e.classList.contains("monitorPanel"))return[390,235];if(k==="PRESET-BANK-01")return[650,370];if(k==="SIGNAL-GENERATOR-01")return[620,430];if(k==="CONTROL-DIAL-RACK-01")return[720,260];if(k==="MASTER-CONTROLS")return[520,145];if(e.classList.contains("t1Panel"))return[440,230];return[390,260]}
function defaults(){const g={1:[],2:[],3:[],4:[],5:[]},m={};for(const [k,e] of cards)g[home(e,k)].push([k,e]);for(let s=1;s<=5;s++)g[s].sort((a,b)=>a[0].localeCompare(b[0])).forEach(([k,e],i)=>{const d=size(k,e);m[k]={screen:s,x:16+(i%3)*416,y:48+Math.floor(i/3)*288,w:d[0],h:d[1],min:false,ix:16+(i%10)*96,iy:56+Math.floor(i/10)*72,z:10+i}});return{modules:m}}
function normalize(x){if(!x||typeof x!=="object")x={version:1,enabled:false,active:"",live:defaults(),profiles:{}};if(!x.live?.modules)x.live=defaults();if(!x.profiles)x.profiles={};for(const[k,e]of cards)if(!x.live.modules[k]){const s=home(e,k),d=size(k,e),n=Object.values(x.live.modules).filter(v=>v.screen===s).length;x.live.modules[k]={screen:s,x:16+(n%3)*416,y:48+Math.floor(n/3)*288,w:d[0],h:d[1],min:false,ix:16,iy:56,z:10+n}}return x}
function load(){try{state=normalize(JSON.parse(localStorage.getItem(KEY)||"null"))}catch(_){state=normalize(null)}try{localStorage.setItem(KEY,JSON.stringify(state))}catch(_){}} function save(b=true){localStorage.setItem(KEY,JSON.stringify(state));if(b&&channel)channel.postMessage({type:"STATE",state})}
function style(){const s=document.createElement("style");s.textContent='body.brutusDesktopMode{overflow:hidden!important;height:100vh!important}body.brutusDesktopMode .shell{transform:none!important;width:100%!important;max-width:none!important;height:100vh;overflow:hidden}body.brutusDesktopMode .layout,body.brutusDesktopMode .monitorWall,body.brutusDesktopMode .instrumentDeck,body.brutusDesktopMode .controls{display:none!important}.workspaceSurface{display:none;position:relative;height:calc(100vh - 112px);min-height:520px;margin-top:5px;border:1px solid #173e5b;border-radius:9px;background:linear-gradient(#00e8ff0b 1px,transparent 1px),linear-gradient(90deg,#00e8ff0b 1px,transparent 1px),radial-gradient(circle,#07192a,#01050a);background-size:16px 16px,16px 16px,auto;overflow:hidden}.brutusDesktopMode .workspaceSurface{display:block}.workspaceCard{position:absolute!important;display:block!important;margin:0!important;min-width:180px!important;min-height:110px!important;max-width:none!important;max-height:none!important;overflow:auto!important;transform:none!important;box-shadow:0 8px 26px #0009,0 0 14px #00dfff18!important}.workspaceCard>.panelControlBar{cursor:grab;user-select:none}.workspaceCard .panelFoldBtn{display:none!important}.workspaceMinBtn{color:#9eefff!important}.workspaceCloseBtn{color:#ff9a9a!important;border-color:#7a2a32!important;font-size:13px!important;line-height:1!important}.workspaceCloseBtn:hover{color:#fff!important;border-color:#ff3344!important;box-shadow:0 0 9px #ff334455!important}.workspaceClosed{display:none!important}.col:has(>.foldablePanel.workspaceClosed){grid-template-columns:minmax(0,1fr)!important;grid-template-rows:none!important;grid-auto-flow:row!important;grid-auto-rows:minmax(0,1fr)!important;align-content:stretch!important}.workspaceWindowMenu{position:relative;z-index:6200}.workspaceWindowMenuBtn{height:23px;border:1px solid #315f9b;border-radius:5px;background:#071524;color:#a9dcff;padding:0 7px;font:800 8px Consolas;cursor:pointer}.workspaceWindowMenuBtn:hover,.workspaceWindowMenu.open .workspaceWindowMenuBtn{border-color:#00e8ff;color:#fff}.workspaceWindowMenuList{display:none;position:absolute;top:calc(100% + 4px);right:0;min-width:460px;max-width:560px;max-height:55vh;overflow:auto;padding:6px;border:1px solid #315f9b;border-radius:7px;background:#04101bf5;box-shadow:0 10px 28px #000c;z-index:6300}.workspaceWindowMenu.open .workspaceWindowMenuList{display:grid;gap:5px}.workspaceWindowMenuEmpty{padding:7px;color:#617f91;font:8px Consolas}.workspaceWindowRow{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:6px;align-items:center;padding:4px;border:1px solid #173e5b;border-radius:6px;background:#06111d}.workspaceWindowOpen,.workspaceWindowTargets button{min-height:26px;border:1px solid #234d6b;border-radius:5px;background:#071524;color:#bdeeff;font:800 8px Consolas;cursor:pointer}.workspaceWindowOpen{width:100%;text-align:left;padding:5px 7px}.workspaceWindowTargets{display:flex;gap:3px}.workspaceWindowTargets button{width:30px;padding:0;text-align:center}.workspaceWindowTargets button.workspaceHere{width:36px;border-color:#00e8ff;color:#dffcff}.workspaceWindowTargets button.workspaceTargetActive{border-color:#00e99a;color:#8fffd9}.workspaceWindowOpen:hover,.workspaceWindowTargets button:hover{border-color:#00e8ff;color:#fff}.workspaceResize{position:absolute;right:1px;bottom:1px;width:18px;height:18px;z-index:70;cursor:nwse-resize;background:linear-gradient(135deg,transparent 0 45%,#315f9b 46% 58%,transparent 59% 68%,#00e8ff 69% 78%,transparent 79%)}.workspaceToolbar{position:absolute;left:8px;right:8px;top:7px;height:32px;display:flex;align-items:center;gap:5px;padding:4px 6px;border:1px solid #234d6b;border-radius:7px;background:#04101bea;z-index:4000;font:800 8px Consolas;color:#8fcfff}.workspaceToolbar input,.workspaceToolbar select,.workspaceToolbar button,.workspaceModeBtn{height:23px;border:1px solid #315f9b;border-radius:5px;background:#071524;color:#a9dcff;padding:0 7px;font:800 8px Consolas}.brutusDesktopMode .header,.brutusDesktopMode .screenTitleBar{z-index:5000!important}.brutusDesktopMode .screenTitleBar{position:relative!important}.workspaceModeBtn.active{border-color:#00e99a;color:#8fffd9}.workspaceHint{margin-left:auto;color:#5f90ab}.workspaceIcons{position:absolute;inset:44px 0 0;pointer-events:none;z-index:3000}.workspaceIcon{position:absolute;width:88px;height:62px;pointer-events:auto;display:grid;place-items:center;border:1px solid #315f9b;border-radius:8px;background:#06111dea;color:#a8d9ff;box-shadow:0 4px 14px #000a;cursor:grab;user-select:none;padding:4px;text-align:center;font:800 7px Consolas;overflow:hidden}.workspaceIcon:before{content:"▣";display:block;font-size:18px;color:#00e8ff}.workspaceOff{display:none!important}.workspaceDrop{border-color:#ffae42!important;color:#ffd58a!important;box-shadow:0 0 12px #ffae4277!important}.workspaceMagnetGhost{display:none;position:absolute;pointer-events:none;border:1px dashed #00e8ff;border-radius:8px;background:#00e8ff0c;box-shadow:0 0 18px #00e8ff33,inset 0 0 18px #00e8ff14;z-index:2500}.workspaceMagnetGhost.active{display:block}.workspaceMagnetGhost:after{content:attr(data-zone);position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);color:#9eefff;font:800 9px Consolas,monospace;letter-spacing:.08em}.brutusDesktopMode .workspaceCard.engine{padding-top:6px!important}.brutusDesktopMode .workspaceCard.isFolded>:not(.panelControlBar){display:block!important}';document.head.appendChild(s)}
function bounds(m,precise=false){const W=Math.max(220,(surface?.clientWidth||innerWidth)-16),H=Math.max(180,(surface?.clientHeight||innerHeight)-48),q=v=>precise?v:snap(v);m.w=clamp(q(+m.w||390),180,W);m.h=clamp(q(+m.h||260),110,H);m.x=clamp(q(+m.x||16),0,Math.max(0,W-m.w));m.y=clamp(q(+m.y||48),40,Math.max(40,H-m.h));m.ix=clamp(q(+m.ix||16),0,Math.max(0,W-88));m.iy=clamp(q(+m.iy||56),48,Math.max(48,H-62))}
function rawClamp(x,y,w,h){const W=Math.max(220,(surface?.clientWidth||innerWidth)-16),H=Math.max(180,(surface?.clientHeight||innerHeight)-48);return{x:clamp(x,0,Math.max(0,W-w)),y:clamp(y,48,Math.max(48,H-h))}}
function magnetPoints(w,h){const W=Math.max(w+32,surface?.clientWidth||innerWidth),H=Math.max(h+64,surface?.clientHeight||innerHeight),left=16,center=Math.max(16,(W-w)/2),right=Math.max(16,W-w-16),top=48,bottom=Math.max(48,H-h-16);return[{n:1,x:left,y:top},{n:2,x:center,y:top},{n:3,x:right,y:top},{n:4,x:left,y:bottom},{n:5,x:center,y:bottom},{n:6,x:right,y:bottom}].map(a=>({...a,x:snap(a.x),y:snap(a.y)}))}
function magneticPosition(x,y,w,h,shift=false){const raw=rawClamp(x,y,w,h);if(shift)return{...raw,zone:0};let best=null;for(const a of magnetPoints(w,h)){const d=Math.hypot(raw.x-a.x,raw.y-a.y);if(!best||d<best.d)best={...a,d}}if(best&&best.d<=MAGNET_RADIUS)return{x:best.x,y:best.y,zone:best.n};const g=rawClamp(snap(raw.x),snap(raw.y),w,h);return{...g,zone:0}}
function showMagnetGhost(pos,w,h){if(!magnetGhost)return;if(!pos?.zone){magnetGhost.classList.remove("active");return}magnetGhost.style.left=pos.x+"px";magnetGhost.style.top=pos.y+"px";magnetGhost.style.width=w+"px";magnetGhost.style.height=h+"px";magnetGhost.dataset.zone="SNAP "+pos.zone;magnetGhost.classList.add("active")}
function hideMagnetGhost(){magnetGhost?.classList.remove("active")}
function storedWindowInfo(k,m){
  if(!m)return null;
  if(!m.closed&&!m.min)return null;
  const origin=Number(m.closedScreen)||Number(m.screen)||home(cards.get(k),k);
  return{origin,status:m.closed?"FERMÉE":"ICÔNE"};
}
function refreshWindowMenu(){
  if(!windowMenu||!windowMenuList||!state)return;
  const stored=[...cards.entries()]
    .map(([k,e])=>({k,e,m:state.live.modules[k],info:storedWindowInfo(k,state.live.modules[k])}))
    .filter(x=>x.info)
    .sort((a,b)=>a.info.origin-b.info.origin||labelOf(a.e,a.k).localeCompare(labelOf(b.e,b.k)));
  const btn=windowMenu.querySelector(".workspaceWindowMenuBtn");
  if(btn)btn.textContent=stored.length?"FENÊTRES · "+stored.length:"FENÊTRES";
  windowMenuList.innerHTML="";
  const head=document.createElement("div");head.className="workspaceWindowMenuEmpty";head.textContent="MAGASIN GLOBAL · OUVRIR ICI = SCREEN "+SCREEN;windowMenuList.appendChild(head);
  if(!stored.length){const e=document.createElement("div");e.className="workspaceWindowMenuEmpty";e.textContent="AUCUNE FENÊTRE RANGÉE";windowMenuList.appendChild(e);return}
  for(const {k,e,info} of stored){
    const row=document.createElement("div");row.className="workspaceWindowRow";
    const open=document.createElement("button");open.type="button";open.className="workspaceWindowOpen";
    open.textContent="S"+info.origin+" · "+info.status+" · "+labelOf(e,k);
    open.title="Ouvrir "+labelOf(e,k)+" ici sur SCREEN "+SCREEN;
    open.onclick=x=>{x.preventDefault();x.stopPropagation();routeStoredWindow(k,SCREEN);windowMenu.classList.remove("open")};
    const targets=document.createElement("div");targets.className="workspaceWindowTargets";
    const here=document.createElement("button");here.type="button";here.className="workspaceHere";here.textContent="ICI";here.title="Ouvrir sur SCREEN "+SCREEN;
    here.onclick=x=>{x.preventDefault();x.stopPropagation();routeStoredWindow(k,SCREEN);windowMenu.classList.remove("open")};targets.appendChild(here);
    for(let n=1;n<=5;n++){
      const t=document.createElement("button");t.type="button";t.textContent="S"+n;t.title="Envoyer sur SCREEN "+n;
      if(n===Number(info.origin))t.classList.add("workspaceTargetActive");
      t.onclick=x=>{x.preventDefault();x.stopPropagation();routeStoredWindow(k,n);windowMenu.classList.remove("open")};
      targets.appendChild(t);
    }
    row.append(open,targets);windowMenuList.appendChild(row);
  }
}
function syncClosedClasses(){
  for(const [k,e] of cards){const m=state?.live?.modules?.[k];e.classList.toggle("workspaceClosed",!!m?.closed)}
}
function closeCard(k){
  const m=state?.live?.modules?.[k];if(!m)return;
  m.closed=true;m.closedScreen=SCREEN;m.min=false;save();apply();
}
function reopenCard(k){
  const m=state?.live?.modules?.[k];if(!m)return;
  m.closed=false;delete m.closedScreen;m.min=false;bump(m);save();apply();
}
function installCloseButtons(){
  for(const [k,e] of cards){
    const tools=e.querySelector(":scope > .panelControlBar .panelTools");if(!tools||tools.querySelector(".workspaceCloseBtn"))continue;
    const b=document.createElement("button");b.type="button";b.className="workspaceCloseBtn";b.textContent="X";b.title="Fermer cette fenêtre";
    b.addEventListener("click",x=>{x.preventDefault();x.stopPropagation();closeCard(k)});
    tools.appendChild(b);
  }
}
function restoreOriginal(e){const o=orig.get(e);if(!o)return;e.classList.remove("workspaceCard","workspaceOff");["left","top","width","height","zIndex"].forEach(k=>e.style[k]="");e.querySelector(":scope > .workspaceResize")?.remove();e.querySelector(":scope > .panelControlBar .workspaceMinBtn")?.remove();e.classList.toggle("screenHiddenByMode",o.hidden);e.classList.toggle("isFolded",o.folded);e.classList.toggle("panelMinimized",!!o.panelMinimized);const f=e.querySelector(":scope > .panelControlBar .panelFoldBtn");if(f)f.textContent=o.folded?"DÉPLIER":"REPLIER";if(o.next&&o.next.parentNode===o.parent)o.parent.insertBefore(e,o.next);else o.parent.appendChild(e)}
function prep(e,k){if(!e.classList.contains("workspaceCard"))orig.set(e,{parent:e.parentNode,next:e.nextSibling,hidden:e.classList.contains("screenHiddenByMode"),folded:e.classList.contains("isFolded"),panelMinimized:e.classList.contains("panelMinimized")});e.classList.remove("screenHiddenByMode","isFolded","panelMinimized");e.classList.add("workspaceCard");if(e.parentNode!==surface)surface.appendChild(e);const tools=e.querySelector(":scope > .panelControlBar .panelTools");if(tools&&!tools.querySelector(".workspaceMinBtn")){const b=document.createElement("button");b.type="button";b.className="workspaceMinBtn";b.textContent="▁";b.title="Réduire en icône";b.onclick=x=>{x.preventDefault();x.stopPropagation();minimize(k)};tools.insertBefore(b,tools.querySelector(".workspaceCloseBtn"))}if(!e.querySelector(":scope > .workspaceResize")){const r=document.createElement("div");r.className="workspaceResize";r.onpointerdown=x=>resizeStart(x,k);e.appendChild(r)}const bar=e.querySelector(":scope > .panelControlBar");if(bar&&!bar.dataset.desktopDrag){bar.dataset.desktopDrag="1";bar.onpointerdown=x=>{if(!x.target.closest("button,input,select,textarea,a"))dragStart(x,k)}}}
function cardApply(k,e){const m=state.live.modules[k];if(!m)return;if(m.closed||+m.screen!==SCREEN||m.min){e.classList.add("workspaceOff");return}e.classList.remove("workspaceOff");bounds(m,!!m.precise);e.style.left=m.x+"px";e.style.top=m.y+"px";e.style.width=m.w+"px";e.style.height=m.h+"px";e.style.zIndex=m.z||10}
function bump(m){m.z=++z;if(z>800){z=31;m.z=z}}
function dropAt(x,y){const e=document.elementFromPoint(x,y)?.closest?.("[data-screen-open]");return e?+e.dataset.screenOpen:0} function dropHi(x,y){document.querySelectorAll("[data-screen-open]").forEach(b=>b.classList.remove("workspaceDrop"));const n=dropAt(x,y);if(n)document.querySelector('[data-screen-open="'+n+'"]')?.classList.add("workspaceDrop")} function dropClear(){document.querySelectorAll(".workspaceDrop").forEach(b=>b.classList.remove("workspaceDrop"))}
function dragStart(ev,k){if(!state.enabled||ev.button!==0)return;const e=cards.get(k),m=state.live.modules[k];if(!e||!m||m.min)return;ev.preventDefault();bump(m);const sx=ev.clientX,sy=ev.clientY,ox=m.x,oy=m.y,h=ev.currentTarget;try{h.setPointerCapture(ev.pointerId)}catch(_){};const mv=x=>{const pos=magneticPosition(ox+x.clientX-sx,oy+x.clientY-sy,m.w,m.h,x.shiftKey);m.x=pos.x;m.y=pos.y;e.style.left=m.x+"px";e.style.top=m.y+"px";showMagnetGhost(pos,m.w,m.h);dropHi(x.clientX,x.clientY)},up=x=>{try{h.releasePointerCapture?.(x.pointerId)}catch(_){};h.removeEventListener("pointermove",mv);h.removeEventListener("pointerup",up);const t=dropAt(x.clientX,x.clientY);dropClear();hideMagnetGhost();if(t&&t!==SCREEN){m.screen=t;m.x=16;m.y=48;m.precise=false;bump(m)}else{const pos=magneticPosition(m.x,m.y,m.w,m.h,x.shiftKey);m.x=pos.x;m.y=pos.y;m.precise=!!x.shiftKey}save();apply()};h.addEventListener("pointermove",mv);h.addEventListener("pointerup",up)}
function resizeStart(ev,k){if(!state.enabled||ev.button!==0)return;ev.preventDefault();ev.stopPropagation();const e=cards.get(k),m=state.live.modules[k],h=ev.currentTarget,sx=ev.clientX,sy=ev.clientY,ow=m.w,oh=m.h;bump(m);try{h.setPointerCapture(ev.pointerId)}catch(_){};const mv=x=>{m.w=Math.max(180,ow+x.clientX-sx);m.h=Math.max(110,oh+x.clientY-sy);e.style.width=m.w+"px";e.style.height=m.h+"px"},up=x=>{try{h.releasePointerCapture?.(x.pointerId)}catch(_){};h.removeEventListener("pointermove",mv);h.removeEventListener("pointerup",up);if(!x.shiftKey){m.w=snap(m.w);m.h=snap(m.h);m.precise=false}else{m.w=Math.max(180,m.w);m.h=Math.max(110,m.h);m.precise=true};bounds(m,!!m.precise);save();cardApply(k,e);dispatchEvent(new Event("resize"))};h.addEventListener("pointermove",mv);h.addEventListener("pointerup",up)}
function minimize(k){const m=state.live.modules[k];if(!m)return;m.min=true;m.ix=snap(m.x||16);m.iy=snap(m.y||56);bump(m);save();apply()}
function restore(k){const m=state.live.modules[k];if(!m)return;m.min=false;bump(m);save();apply()}
function restoreHere(k){
  const m=state.live.modules[k];if(!m)return;
  m.closed=false;delete m.closedScreen;m.screen=SCREEN;m.min=false;m.x=16;m.y=48;m.precise=false;bump(m);save();apply();
}
function routeStoredWindow(k,targetScreen){
  const m=state.live.modules[k],target=Number(targetScreen);if(!m||target<1||target>5)return;
  state.enabled=true;
  m.closed=false;delete m.closedScreen;m.min=false;m.screen=target;m.x=16;m.y=48;m.precise=false;bump(m);save();apply();
}
function iconTransferPayload(k){const m=state.live.modules[k];return JSON.stringify({type:"BRUTUS_WORKSPACE_ICON",key:k,sourceView:SCREEN,screen:Number(m?.screen)||SCREEN})}
function readIconTransfer(ev){
  let raw="";
  try{raw=ev.dataTransfer?.getData(ICON_TRANSFER_MIME)||ev.dataTransfer?.getData("text/plain")||""}catch(_){}
  try{const d=JSON.parse(raw);if(d?.type==="BRUTUS_WORKSPACE_ICON"&&cards.has(d.key))return d}catch(_){}
  return null;
}
function moveIconLocal(k,clientX,clientY,shift=false){
  const m=state.live.modules[k];if(!m||!surface)return;
  const r=surface.getBoundingClientRect(),p=magneticPosition(clientX-r.left-44,clientY-r.top-31,88,62,shift);
  m.ix=p.x;m.iy=p.y;m.iprecise=!!shift;bump(m);save();apply();
}
function transferPanelTo(k,targetScreen,clientX=null,clientY=null,shift=false){
  const m=state.live.modules[k];if(!m)return;
  m.closed=false;delete m.closedScreen;m.screen=targetScreen;m.min=false;m.precise=!!shift;
  if(targetScreen===SCREEN&&surface&&Number.isFinite(clientX)&&Number.isFinite(clientY)){
    const r=surface.getBoundingClientRect(),p=magneticPosition(clientX-r.left-(Number(m.w)||390)/2,clientY-r.top-(Number(m.h)||260)/2,Number(m.w)||390,Number(m.h)||260,shift);
    m.x=p.x;m.y=p.y;
  }else{m.x=16;m.y=48;m.precise=false}
  bump(m);save();apply();
}
function installIconTransfers(){
  addEventListener("message",e=>{
    if(e.origin!==location.origin||e.source!==parent)return;
    const m=e.data||{};if(m.type!=="BRUTUS_ICON_DROP"||!cards.has(m.key))return;
    transferPanelTo(m.key,SCREEN,Number(m.clientX),Number(m.clientY),!!m.shiftKey);
  });
  document.addEventListener("dragover",e=>{
    const types=[...(e.dataTransfer?.types||[])];
    if(types.includes(ICON_TRANSFER_MIME)||types.includes("text/plain")){e.preventDefault();if(e.dataTransfer)e.dataTransfer.dropEffect="move"}
  },true);
  document.addEventListener("drop",e=>{
    const d=readIconTransfer(e);if(!d)return;
    e.preventDefault();e.stopPropagation();dropClear();hideMagnetGhost();
    const targetButton=e.target.closest?.("[data-screen-open]"),targetScreen=targetButton?Number(targetButton.dataset.screenOpen):SCREEN;
    const m=state.live.modules[d.key];if(!m)return;
    const sameLocalIcon=targetScreen===SCREEN&&Number(d.sourceView)===SCREEN&&Number(m.screen)===SCREEN&&!targetButton;
    if(sameLocalIcon)moveIconLocal(d.key,e.clientX,e.clientY,e.shiftKey);
    else transferPanelTo(d.key,targetScreen,e.clientX,e.clientY,e.shiftKey);
  },true);
}
function iconRender(){
  icons.innerHTML="";
  for(const[k,m]of Object.entries(state.live.modules)){
    if(m.closed||!m.min)continue;
    const c=cards.get(k);if(!c)continue;
    const W=Math.max(220,(surface?.clientWidth||innerWidth)-16),H=Math.max(180,(surface?.clientHeight||innerHeight)-48);
    const ix=clamp(Number(m.ix)||16,0,Math.max(0,W-88)),iy=clamp(Number(m.iy)||56,48,Math.max(48,H-62));
    const i=document.createElement("div");i.className="workspaceIcon";i.draggable=true;i.dataset.panelKey=k;
    i.textContent=(Number(m.screen)===SCREEN?"":"S"+m.screen+" · ")+labelOf(c,k);
    i.title=Number(m.screen)===SCREEN?"Cliquer pour rouvrir · glisser pour déplacer/transférer":"SCREEN "+m.screen+" · cliquer pour amener ici · glisser pour transférer";
    i.style.left=ix+"px";i.style.top=iy+"px";
    let dragged=false;
    const armRemoteDrop=()=>{try{if(parent&&parent!==window)parent.postMessage({type:"BRUTUS_ICON_DRAG_START",key:k,sourceScreen:SCREEN},location.origin)}catch(_){}};
    const disarmRemoteDrop=()=>{try{if(parent&&parent!==window)parent.postMessage({type:"BRUTUS_ICON_DRAG_END",key:k,sourceScreen:SCREEN},location.origin)}catch(_){}};
    i.addEventListener("pointerdown",ev=>{if(ev.button===0)armRemoteDrop()});
    i.addEventListener("dragstart",ev=>{
      dragged=true;if(!ev.dataTransfer)return;
      const payload=iconTransferPayload(k);ev.dataTransfer.effectAllowed="move";
      try{ev.dataTransfer.setData(ICON_TRANSFER_MIME,payload)}catch(_){}
      try{ev.dataTransfer.setData("text/plain",payload)}catch(_){}
      armRemoteDrop();
      i.style.opacity=".55";
    });
    i.addEventListener("dragend",()=>{i.style.opacity="";setTimeout(()=>{dragged=false},0);dropClear();hideMagnetGhost()});
    i.addEventListener("click",e=>{e.preventDefault();e.stopPropagation();if(dragged)return;disarmRemoteDrop();restoreHere(k)});
    icons.appendChild(i);
  }
}
function profiles(){const s=document.querySelector(".workspaceProfiles");if(!s)return;const cur=state.active||s.value;s.innerHTML='<option value="">MODULES SAUVÉS</option>';Object.keys(state.profiles).sort().forEach(n=>{const o=document.createElement("option");o.value=n;o.textContent=n;s.appendChild(o)});if(state.profiles[cur])s.value=cur}
function apply(){if(applying)return;applying=true;document.body.classList.toggle("brutusDesktopMode",!!state.enabled);const b=document.querySelector(".workspaceModeBtn");if(b){b.classList.toggle("active",!!state.enabled);b.textContent=state.enabled?"BUREAU ON":"BUREAU"}if(state.enabled){for(const[k,e]of cards){prep(e,k);cardApply(k,e)}iconRender();profiles()}else{for(const e of cards.values())restoreOriginal(e);icons.innerHTML=""}syncClosedClasses();refreshWindowMenu();dispatchEvent(new Event("resize"));applying=false}
function ui(){const tb=document.getElementById("screenTitleBar");
windowMenu=document.createElement("div");windowMenu.className="workspaceWindowMenu";
const menuBtn=document.createElement("button");menuBtn.type="button";menuBtn.className="workspaceWindowMenuBtn";menuBtn.textContent="FENÊTRES";
windowMenuList=document.createElement("div");windowMenuList.className="workspaceWindowMenuList";
menuBtn.addEventListener("click",e=>{e.preventDefault();e.stopPropagation();windowMenu.classList.toggle("open");refreshWindowMenu()});
windowMenu.addEventListener("pointerdown",e=>e.stopPropagation());windowMenu.append(menuBtn,windowMenuList);tb?.insertBefore(windowMenu,tb.children[1]||null);
document.addEventListener("pointerdown",e=>{if(windowMenu&&!windowMenu.contains(e.target))windowMenu.classList.remove("open")});
const b=document.createElement("button");b.className="workspaceModeBtn";b.type="button";b.textContent="BUREAU";b.onclick=()=>{state.enabled=!state.enabled;save();apply()};tb?.insertBefore(b,tb.children[1]||null);surface=document.createElement("section");surface.className="workspaceSurface";surface.innerHTML='<div class="workspaceToolbar"><span>MODULE</span><input class="workspaceName" maxlength="48" placeholder="ex. TEST-RÉSONANCE"><button class="workspaceSave">ENREGISTRER</button><select class="workspaceProfiles"><option value="">MODULES SAUVÉS</option></select><button class="workspaceLoad">OUVRIR</button><span class="workspaceHint">6 AIMANTS · SNAP 16px · SHIFT = LIBRE · FENÊTRES = ROUTAGE S1–S5</span></div>';icons=document.createElement("div");icons.className="workspaceIcons";surface.appendChild(icons);magnetGhost=document.createElement("div");magnetGhost.className="workspaceMagnetGhost";surface.appendChild(magnetGhost);document.querySelector(".shell")?.appendChild(surface);document.querySelector(".workspaceSave").onclick=()=>{const n=(document.querySelector(".workspaceName").value||"").trim().slice(0,48);if(!n)return;state.profiles[n]={name:n,live:clone(state.live)};state.active=n;save();profiles()};document.querySelector(".workspaceLoad").onclick=()=>{const n=document.querySelector(".workspaceProfiles").value;if(!state.profiles[n])return;state.live=clone(state.profiles[n].live);state.active=n;state.enabled=true;state=normalize(state);save();apply()}}
function init(){document.querySelectorAll(".foldablePanel").forEach(e=>{const k=keyOf(e);if(k&&!cards.has(k))cards.set(k,e)});if(!cards.size)return;for(const[k,e]of cards)e.dataset.desktopHome=String(home(e,k));style();ui();load();installCloseButtons();installIconTransfers();channel="BroadcastChannel"in window?new BroadcastChannel(CHAN):null;if(channel)channel.onmessage=e=>{if(e.data?.type==="STATE"){state=normalize(clone(e.data.state));apply()}};addEventListener("storage",e=>{if(e.key===KEY&&e.newValue){try{state=normalize(JSON.parse(e.newValue));apply()}catch(_){}}});profiles();apply()}
if(document.readyState==="loading")addEventListener("DOMContentLoaded",init,{once:true});else init();
})();