(()=>{
"use strict";
const SCREEN=Number(new URLSearchParams(location.search).get("screen")||0);if(SCREEN<1||SCREEN>5)return;
const KEY="BRUTUS_DESKTOP_WORKSPACE_V2",LEGACY_KEY="BRUTUS_DESKTOP_WORKSPACE_V1",CHAN="BRUTUS_DESKTOP_WORKSPACE_V2",GRID=16,MAGNET_RADIUS=92,ICON_TRANSFER_MIME="application/x-brutus-workspace-icon";let state,surface,icons,channel,z=30,applying=false,magnetGhost=null,windowMenu=null,windowMenuList=null;
const FONT_KEY="BRUTUS_GLOBAL_FONT_V1",FONT_CHAN="BRUTUS_GLOBAL_FONT_V1",FONT_MIN=.80,FONT_MAX=1.80,FONT_STEP=.10;let fontScale=1,fontChannel=null;
const SCREEN_ZOOM_KEY="BRUTUS_SCREEN1_ZOOM_V1",LEGACY_ACCESS_KEY="BRUTUS_ACCESSIBILITY_V1",SCREEN_ZOOM_MIN=.75,SCREEN_ZOOM_MAX=1.50,SCREEN_ZOOM_STEP=.05;let screenZoom=1;
const cards=new Map(),orig=new Map(),LEGACY_A=new Set(["ANALYSIS-AMP-01","ANALYSIS-HISTORY-01","TIMEBASE-01","SAMPLER-01","SAMPLER-QUALITY-01","CRACK-METER-01","CRACK-CLASSIFIER-01"]),LEGACY_O=new Set(["PRESET-BANK-01","REFERENCE-CATALOG-01","MICROPHONE-SOURCE-01","SIGNAL-GENERATOR-01"]),LEGACY_C=new Set(["INPUT-TEST-01","CONNECT-T2-01","CONNECT-T3-01","CONNECT-T4-01","CONNECT-T5-01"]);
const SCREEN_GROUP_NAMES={1:"LABORATOIRE",2:"EXTENSION 1",3:"EXTENSION 2",4:"EXTENSION 3",5:"EXTENSION 4"};
const snap=v=>Math.round(v/GRID)*GRID,clamp=(v,a,b)=>Math.max(a,Math.min(b,v)),clone=x=>JSON.parse(JSON.stringify(x));
function fontClamp(v){return Math.max(FONT_MIN,Math.min(FONT_MAX,Number(v)||1))}
function loadFontScale(){try{const x=JSON.parse(localStorage.getItem(FONT_KEY)||"null");fontScale=fontClamp(x?.scale)}catch(_){fontScale=1}}
function fontTargetElements(){
  const selector="button,span,div,p,h1,h2,h3,h4,label,input,select,textarea,pre,td,th,strong,em,small,a";
  return [...document.querySelectorAll(selector)].filter(el=>{
    if(el.closest("script,style,svg,canvas"))return false;
    const n=Number.parseFloat(getComputedStyle(el).fontSize);
    return Number.isFinite(n)&&n>0;
  });
}
function moduleZoomForText(el){
  const panel=el.closest(".foldablePanel");
  if(!panel||el.closest(".panelControlBar"))return 1;
  return Math.max(.50,Math.min(2.00,Number(panel.dataset.moduleZoom)||1));
}
function applyGlobalFont(){
  for(const el of fontTargetElements()){
    if(!el.dataset.brutusGlobalFontBasePx){
      const now=Number.parseFloat(getComputedStyle(el).fontSize);
      if(Number.isFinite(now)&&now>0)el.dataset.brutusGlobalFontBasePx=String(now);
    }
    const base=Number(el.dataset.brutusGlobalFontBasePx);
    const moduleZoom=moduleZoomForText(el);
    if(Number.isFinite(base)&&base>0)el.style.fontSize=(base*fontScale/moduleZoom).toFixed(2)+"px";
  }
  const r=document.getElementById("globalFontReadout");if(r)r.textContent=Math.round(fontScale*100)+"%";
}
function saveFontScale(broadcast=true){
  try{localStorage.setItem(FONT_KEY,JSON.stringify({version:2,scale:fontScale,updatedAt:Date.now()}))}catch(_){}
  if(broadcast&&fontChannel)fontChannel.postMessage({type:"FONT_SCALE",scale:fontScale});
}
function setGlobalFont(next,broadcast=true){fontScale=Math.round(fontClamp(next)*100)/100;applyGlobalFont();saveFontScale(broadcast)}
function initGlobalFont(){
  loadFontScale();
  const minus=document.getElementById("globalFontMinus"),plus=document.getElementById("globalFontPlus");
  if(minus&&!minus.dataset.fontBound){minus.dataset.fontBound="1";minus.onclick=e=>{e.preventDefault();e.stopPropagation();setGlobalFont(fontScale-FONT_STEP)}}
  if(plus&&!plus.dataset.fontBound){plus.dataset.fontBound="1";plus.onclick=e=>{e.preventDefault();e.stopPropagation();setGlobalFont(fontScale+FONT_STEP)}}
  if("BroadcastChannel" in window){
    fontChannel=new BroadcastChannel(FONT_CHAN);
    fontChannel.onmessage=e=>{if(e.data?.type==="FONT_SCALE"){fontScale=Math.round(fontClamp(e.data.scale)*100)/100;applyGlobalFont()}};
  }
  addEventListener("storage",e=>{if(e.key===FONT_KEY&&e.newValue){try{const x=JSON.parse(e.newValue);fontScale=Math.round(fontClamp(x.scale)*100)/100;applyGlobalFont()}catch(_){}}});
  addEventListener("BRUTUS_MODULE_ZOOM_CHANGED",()=>applyGlobalFont());
  applyGlobalFont();
}
function screenZoomClamp(v){return Math.max(SCREEN_ZOOM_MIN,Math.min(SCREEN_ZOOM_MAX,Number(v)||1))}
function loadScreenZoom(){
  try{
    const cur=JSON.parse(localStorage.getItem(SCREEN_ZOOM_KEY)||"null");
    if(cur&&Number(cur.scale))screenZoom=screenZoomClamp(cur.scale);
    else{
      const legacy=JSON.parse(localStorage.getItem(LEGACY_ACCESS_KEY)||"null");
      screenZoom=screenZoomClamp(legacy?.screen1Zoom||1);
    }
  }catch(_){screenZoom=1}
}
function saveScreenZoom(){
  try{localStorage.setItem(SCREEN_ZOOM_KEY,JSON.stringify({version:1,scale:screenZoom,updatedAt:Date.now()}))}catch(_){}
}
function applyScreenZoom(){
  if(SCREEN!==1)return;
  window.BRUTUS_SCREEN1_ZOOM_FACTOR=screenZoom;
  const r=document.getElementById("screenZoomReadout");if(r)r.textContent=Math.round(screenZoom*100)+"%";
  requestAnimationFrame(()=>dispatchEvent(new Event("resize")));
}
function setScreenZoom(next){
  screenZoom=Math.round(screenZoomClamp(next)*100)/100;
  saveScreenZoom();
  applyScreenZoom();
}
function initScreenZoom(){
  const host=document.getElementById("screenAccessibilityControls");
  if(!host||SCREEN!==1)return;
  loadScreenZoom();
  host.hidden=false;
  host.innerHTML='<span class="screenAccessGroup"><span class="screenAccessLabel">ZOOM</span><button id="screenZoomMinus" class="screenAccessBtn" type="button" data-local-control="1" title="Réduire le zoom de SCREEN 1">−</button><span id="screenZoomReadout" class="screenAccessReadout">100%</span><button id="screenZoomPlus" class="screenAccessBtn" type="button" data-local-control="1" title="Agrandir le zoom de SCREEN 1">+</button></span>';
  const minus=document.getElementById("screenZoomMinus"),plus=document.getElementById("screenZoomPlus");
  minus.onclick=e=>{e.preventDefault();e.stopPropagation();setScreenZoom(screenZoom-SCREEN_ZOOM_STEP)};
  plus.onclick=e=>{e.preventDefault();e.stopPropagation();setScreenZoom(screenZoom+SCREEN_ZOOM_STEP)};
  applyScreenZoom();
}
function keyOf(e){return e.dataset.workspaceKey||e.id||""} function labelOf(e,k){const h=e.querySelector(":scope > .panelControlBar > h2");if(h){const c=h.cloneNode(true);c.querySelectorAll(".panelId").forEach(x=>x.remove());if(c.textContent.trim())return c.textContent.trim()}return e.querySelector(":scope > .panelControlBar > .panelControlLabel")?.textContent?.trim()||k}
function legacyHome(e,k){if(e.closest(".layout"))return 1;if(e.closest(".monitorWall")||LEGACY_A.has(k))return 2;if(LEGACY_O.has(k)||/MICROPHONE|GENERATOR|PRESET|REFERENCE/.test(k))return 3;if(LEGACY_C.has(k)||/^CONNECT-T/.test(k))return 4;return 5}
function home(){return 1}
const WORKSPACE_MODEL="LAB_EXTENSIONS_V1";
function migrateLegacyLive(live){
  if(!live?.modules)return live;
  for(const[k,e]of cards){
    const m=live.modules[k];if(!m)continue;
    const oldHome=legacyHome(e,k);
    if(Number(m.screen)===oldHome){
      m.screen=1;
      if(Number(m.closedScreen)===oldHome)m.closedScreen=1;
    }
  }
  return live;
}
function size(k,e){if(k==="CORE-ENGINE")return[720,560];if(e.classList.contains("monitorPanel"))return[390,235];if(k==="PRESET-BANK-01")return[650,370];if(k==="SIGNAL-GENERATOR-01")return[620,430];if(k==="CONTROL-DIAL-RACK-01")return[720,260];if(k==="MASTER-CONTROLS")return[520,145];if(e.classList.contains("t1Panel"))return[440,230];return[390,260]}
function defaults(){const g={1:[],2:[],3:[],4:[],5:[]},m={};for(const [k,e] of cards)g[home(e,k)].push([k,e]);for(let s=1;s<=5;s++)g[s].sort((a,b)=>a[0].localeCompare(b[0])).forEach(([k,e],i)=>{const d=size(k,e);m[k]={screen:s,closed:true,closedScreen:s,x:16+(i%3)*416,y:48+Math.floor(i/3)*288,w:d[0],h:d[1],min:false,ix:16+(i%10)*96,iy:56+Math.floor(i/10)*72,z:10+i}});return{modules:m}}
function normalize(x){
  if(!x||typeof x!=="object")x={version:3,workspaceModel:WORKSPACE_MODEL,enabled:true,active:"",live:defaults(),profiles:{}};
  const needsMigration=Number(x.version)<3||x.workspaceModel!==WORKSPACE_MODEL;
  x.enabled=true;if(!x.live?.modules)x.live=defaults();if(!x.profiles)x.profiles={};
  if(needsMigration)migrateLegacyLive(x.live);
  for(const profile of Object.values(x.profiles)){
    if(!profile||typeof profile!=="object")continue;
    if(profile.workspaceModel!==WORKSPACE_MODEL)migrateLegacyLive(profile.live);
    profile.version=3;profile.workspaceModel=WORKSPACE_MODEL;
  }
  x.version=3;x.workspaceModel=WORKSPACE_MODEL;
  for(const[k,e]of cards)if(!x.live.modules[k]){const s=1,d=size(k,e),n=Object.values(x.live.modules).filter(v=>v.screen===s).length;x.live.modules[k]={screen:s,closed:true,closedScreen:s,x:16+(n%3)*416,y:48+Math.floor(n/3)*288,w:d[0],h:d[1],min:false,ix:16,iy:56,z:10+n}}
  return x
}
function load(){try{state=normalize(JSON.parse(localStorage.getItem(KEY)||"null"))}catch(_){state=normalize(null)}try{localStorage.setItem(KEY,JSON.stringify(state))}catch(_){}} function save(b=true){localStorage.setItem(KEY,JSON.stringify(state));if(b&&channel)channel.postMessage({type:"STATE",state})}
function style(){const s=document.createElement("style");s.textContent='body.brutusDesktopMode{overflow:hidden!important;height:100vh!important}body.brutusDesktopMode .shell{transform:none!important;width:100%!important;max-width:none!important;height:100vh;overflow:hidden}body.brutusDesktopMode .layout,body.brutusDesktopMode .monitorWall,body.brutusDesktopMode .instrumentDeck,body.brutusDesktopMode .controls{display:none!important}.workspaceSurface{display:none;position:relative;height:calc(100vh - 112px);min-height:520px;margin-top:5px;border:1px solid #173e5b;border-radius:9px;background:linear-gradient(#00e8ff0b 1px,transparent 1px),linear-gradient(90deg,#00e8ff0b 1px,transparent 1px),radial-gradient(circle,#07192a,#01050a);background-size:16px 16px,16px 16px,auto;overflow:hidden}.brutusDesktopMode .workspaceSurface{display:block}.workspaceCard{position:absolute!important;display:block!important;margin:0!important;min-width:180px!important;min-height:110px!important;max-width:none!important;max-height:none!important;overflow:auto!important;transform:none!important;box-shadow:0 8px 26px #0009,0 0 14px #00dfff18!important}.workspaceCard>.panelControlBar{cursor:grab;user-select:none}.workspaceCard .panelFoldBtn{display:none!important}.workspaceMinBtn{color:#9eefff!important}.workspaceCloseBtn{color:#ff9a9a!important;border-color:#7a2a32!important;font-size:13px!important;line-height:1!important}.workspaceCloseBtn:hover{color:#fff!important;border-color:#ff3344!important;box-shadow:0 0 9px #ff334455!important}.workspaceClosed{display:none!important}.col:has(>.foldablePanel.workspaceClosed){grid-template-columns:minmax(0,1fr)!important;grid-template-rows:none!important;grid-auto-flow:row!important;grid-auto-rows:minmax(0,1fr)!important;align-content:stretch!important}.workspaceWindowMenu{position:relative;z-index:6200}.workspaceWindowMenuBtn{height:23px;border:1px solid #315f9b;border-radius:5px;background:#071524;color:#a9dcff;padding:0 7px;font:800 8px Consolas;cursor:pointer}.workspaceWindowMenuBtn:hover,.workspaceWindowMenu.open .workspaceWindowMenuBtn{border-color:#00e8ff;color:#fff}.workspaceWindowMenuList{display:none;position:absolute;top:calc(100% + 4px);right:0;min-width:460px;max-width:560px;max-height:55vh;overflow:auto;padding:6px;border:1px solid #315f9b;border-radius:7px;background:#04101bf5;box-shadow:0 10px 28px #000c;z-index:6300}.workspaceWindowMenu.open .workspaceWindowMenuList{display:grid;gap:5px}.workspaceWindowMenuEmpty{padding:7px;color:#617f91;font:8px Consolas}.workspaceWindowRow{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:6px;align-items:center;padding:4px;border:1px solid #173e5b;border-radius:6px;background:#06111d}.workspaceWindowOpen,.workspaceWindowTargets button{min-height:26px;border:1px solid #234d6b;border-radius:5px;background:#071524;color:#bdeeff;font:800 8px Consolas;cursor:pointer}.workspaceWindowOpen{width:100%;text-align:left;padding:5px 7px}.workspaceWindowTargets{display:flex;gap:3px}.workspaceWindowTargets button{width:30px;padding:0;text-align:center}.workspaceWindowTargets button.workspaceHere{width:36px;border-color:#00e8ff;color:#dffcff}.workspaceWindowTargets button.workspaceTargetActive{border-color:#00e99a;color:#8fffd9}.workspaceWindowOpen:hover,.workspaceWindowTargets button:hover{border-color:#00e8ff;color:#fff}.workspaceResize{position:absolute;right:1px;bottom:1px;width:18px;height:18px;z-index:70;cursor:nwse-resize;background:linear-gradient(135deg,transparent 0 45%,#315f9b 46% 58%,transparent 59% 68%,#00e8ff 69% 78%,transparent 79%)}.workspaceToolbar{position:absolute;left:8px;right:8px;top:7px;height:32px;display:flex;align-items:center;gap:5px;padding:4px 6px;border:1px solid #234d6b;border-radius:7px;background:#04101bea;z-index:4000;font:800 8px Consolas;color:#8fcfff}.workspaceToolbar input,.workspaceToolbar select,.workspaceToolbar button,.workspaceModeBtn{height:23px;border:1px solid #315f9b;border-radius:5px;background:#071524;color:#a9dcff;padding:0 7px;font:800 8px Consolas}.brutusDesktopMode .header,.brutusDesktopMode .screenTitleBar{z-index:5000!important}.brutusDesktopMode .screenTitleBar{position:relative!important}.workspaceModeBtn.active{border-color:#00e99a;color:#8fffd9}.workspaceHint{margin-left:auto;color:#5f90ab}.workspaceIcons{position:absolute;inset:44px 0 0;pointer-events:none;z-index:3000}.workspaceIcon{position:absolute;width:88px;height:62px;pointer-events:auto;display:grid;place-items:center;border:1px solid #315f9b;border-radius:8px;background:#06111dea;color:#a8d9ff;box-shadow:0 4px 14px #000a;cursor:grab;user-select:none;padding:4px;text-align:center;font:800 7px Consolas;overflow:hidden}.workspaceIcon:before{content:"▣";display:block;font-size:18px;color:#00e8ff}.workspaceOff{display:none!important}.workspaceDrop{border-color:#ffae42!important;color:#ffd58a!important;box-shadow:0 0 12px #ffae4277!important}.workspaceMagnetGhost{display:none;position:absolute;pointer-events:none;border:1px dashed #00e8ff;border-radius:8px;background:#00e8ff0c;box-shadow:0 0 18px #00e8ff33,inset 0 0 18px #00e8ff14;z-index:2500}.workspaceMagnetGhost.active{display:block}.workspaceMagnetGhost:after{content:attr(data-zone);position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);color:#9eefff;font:800 9px Consolas,monospace;letter-spacing:.08em}.brutusDesktopMode .workspaceCard.engine{padding-top:6px!important}.brutusDesktopMode .workspaceCard.isFolded>:not(.panelControlBar){display:block!important}';document.head.appendChild(s)}
function bounds(m,precise=false){const W=Math.max(220,(surface?.clientWidth||innerWidth)-16),H=Math.max(180,(surface?.clientHeight||innerHeight)-48),q=v=>precise?v:snap(v);m.w=clamp(q(+m.w||390),180,W);m.h=clamp(q(+m.h||260),110,H);m.x=clamp(q(+m.x||16),0,Math.max(0,W-m.w));m.y=clamp(q(+m.y||48),40,Math.max(40,H-m.h));m.ix=clamp(q(+m.ix||16),0,Math.max(0,W-88));m.iy=clamp(q(+m.iy||56),48,Math.max(48,H-62))}
function rawClamp(x,y,w,h){const W=Math.max(220,(surface?.clientWidth||innerWidth)-16),H=Math.max(180,(surface?.clientHeight||innerHeight)-48);return{x:clamp(x,0,Math.max(0,W-w)),y:clamp(y,48,Math.max(48,H-h))}}
function magnetPoints(w,h){const W=Math.max(w+32,surface?.clientWidth||innerWidth),H=Math.max(h+64,surface?.clientHeight||innerHeight),left=16,center=Math.max(16,(W-w)/2),right=Math.max(16,W-w-16),top=48,bottom=Math.max(48,H-h-16);return[{n:1,x:left,y:top},{n:2,x:center,y:top},{n:3,x:right,y:top},{n:4,x:left,y:bottom},{n:5,x:center,y:bottom},{n:6,x:right,y:bottom}].map(a=>({...a,x:snap(a.x),y:snap(a.y)}))}
function magneticPosition(x,y,w,h,shift=false){const raw=rawClamp(x,y,w,h);if(shift)return{...raw,zone:0};let best=null;for(const a of magnetPoints(w,h)){const d=Math.hypot(raw.x-a.x,raw.y-a.y);if(!best||d<best.d)best={...a,d}}if(best&&best.d<=MAGNET_RADIUS)return{x:best.x,y:best.y,zone:best.n};const g=rawClamp(snap(raw.x),snap(raw.y),w,h);return{...g,zone:0}}
function showMagnetGhost(pos,w,h){if(!magnetGhost)return;if(!pos?.zone){magnetGhost.classList.remove("active");return}magnetGhost.style.left=pos.x+"px";magnetGhost.style.top=pos.y+"px";magnetGhost.style.width=w+"px";magnetGhost.style.height=h+"px";magnetGhost.dataset.zone="SNAP "+pos.zone;magnetGhost.classList.add("active")}
function hideMagnetGhost(){magnetGhost?.classList.remove("active")}
function panelIsLocallyHidden(e){
  return !!e&&(e.classList.contains("panelClosed")||e.classList.contains("panelMinimized")||e.dataset.closed==="1"||e.dataset.minimized==="1");
}
function windowIsHiddenHere(e,m){
  return !!m&&(!!m.closed||!!m.min||Number(m.screen)!==SCREEN||panelIsLocallyHidden(e));
}
function windowDirectoryInfo(k,m,e){
  if(!m)return null;
  const origin=Number(m.closedScreen)||Number(m.screen)||home(e||cards.get(k),k);
  const localClosed=!!e&&(e.classList.contains("panelClosed")||e.dataset.closed==="1");
  const localMin=!!e&&(e.classList.contains("panelMinimized")||e.dataset.minimized==="1");
  const status=(m.closed||localClosed)?"FERMÉE":((m.min||localMin)?"ICÔNE":"AUTRE ÉCRAN");
  return{origin,status};
}
function reconcilePanelHiddenState(){
  if(!state?.live?.modules)return;
  let changed=false;
  for(const [k,e] of cards){
    const m=state.live.modules[k];if(!m)continue;
    const localClosed=e.classList.contains("panelClosed")||e.dataset.closed==="1";
    const localMin=e.classList.contains("panelMinimized")||e.dataset.minimized==="1";
    if(localClosed&&!m.closed){
      m.closed=true;m.closedScreen=Number(m.screen)||home(e,k);m.min=false;changed=true;
    }else if(localMin&&!m.closed&&!m.min){
      m.min=true;changed=true;
    }
  }
  if(changed)save(false);
}
function refreshWindowMenu(){
  if(!windowMenu||!windowMenuList||!state)return;
  const directory=[...cards.entries()]
    .map(([k,e])=>({k,e,m:state.live.modules[k],info:windowDirectoryInfo(k,state.live.modules[k],e)}))
    .filter(x=>x.info&&windowIsHiddenHere(x.e,x.m))
    .sort((a,b)=>a.info.origin-b.info.origin||labelOf(a.e,a.k).localeCompare(labelOf(b.e,b.k)));
  const btn=windowMenu.querySelector(".workspaceWindowMenuBtn");
  if(btn)btn.textContent=directory.length?"MODULE · "+directory.length:"MODULE";
  windowMenuList.innerHTML="";
  const head=document.createElement("div");head.className="workspaceWindowMenuEmpty";head.textContent="MODULES CACHÉS · CLIQUER POUR OUVRIR ICI · SCREEN "+SCREEN;windowMenuList.appendChild(head);
  if(!directory.length){const e=document.createElement("div");e.className="workspaceWindowMenuEmpty";e.textContent="AUCUN MODULE CACHÉ";windowMenuList.appendChild(e);applyGlobalFont();return}
  let lastOrigin=0;
  for(const {k,e,info} of directory){
    if(info.origin!==lastOrigin){const group=document.createElement("div");group.className="workspaceWindowMenuEmpty";group.textContent="SCREEN "+info.origin+" · "+(SCREEN_GROUP_NAMES[info.origin]||"");windowMenuList.appendChild(group);lastOrigin=info.origin}
    const row=document.createElement("div");row.className="workspaceWindowRow";
    const open=document.createElement("button");open.type="button";open.className="workspaceWindowOpen";
    open.textContent="S"+info.origin+" · "+info.status+" · "+labelOf(e,k);
    open.title="Amener "+labelOf(e,k)+" ici sur SCREEN "+SCREEN;
    open.onclick=x=>{x.preventDefault();x.stopPropagation();routeWindow(k,SCREEN);windowMenu.classList.remove("open")};
    const targets=document.createElement("div");targets.className="workspaceWindowTargets";
    const here=document.createElement("button");here.type="button";here.className="workspaceHere";here.textContent="ICI";here.title="Ouvrir sur SCREEN "+SCREEN;
    here.onclick=x=>{x.preventDefault();x.stopPropagation();routeWindow(k,SCREEN);windowMenu.classList.remove("open")};targets.appendChild(here);
    for(let n=1;n<=5;n++){
      const t=document.createElement("button");t.type="button";t.textContent="S"+n;t.title="Envoyer sur SCREEN "+n;
      if(n===Number(info.origin))t.classList.add("workspaceTargetActive");
      t.onclick=x=>{x.preventDefault();x.stopPropagation();routeWindow(k,n);windowMenu.classList.remove("open")};
      targets.appendChild(t);
    }
    row.append(open,targets);windowMenuList.appendChild(row);
  }
  applyGlobalFont();
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
function ensurePanelTools(e,k){
  let bar=e.querySelector(":scope > .panelControlBar");
  if(!bar){
    bar=document.createElement("div");bar.className="panelControlBar";
    const label=document.createElement("div");label.className="panelControlLabel";label.textContent=labelOf(e,k)||k;
    bar.appendChild(label);e.prepend(bar);
  }
  let tools=bar.querySelector(":scope > .panelTools");
  if(!tools){tools=document.createElement("div");tools.className="panelTools";bar.appendChild(tools)}
  return tools;
}
function ensureCloseButton(k,e){
  const tools=ensurePanelTools(e,k);
  let b=tools.querySelector(".workspaceCloseBtn");
  if(b)return b;
  b=tools.querySelector(".panelCloseBtn");
  if(b){b.classList.add("workspaceCloseBtn");return b}
  b=document.createElement("button");b.type="button";b.className="workspaceCloseBtn";b.textContent="X";b.title="Fermer et ranger cette fenêtre";
  b.setAttribute("aria-label","Fermer et ranger "+labelOf(e,k));
  b.addEventListener("click",x=>{x.preventDefault();x.stopPropagation();closeCard(k)});
  tools.appendChild(b);
  return b;
}
function installCloseButtons(){for(const [k,e] of cards)ensureCloseButton(k,e)}
function restoreOriginal(e){const o=orig.get(e);if(!o)return;e.classList.remove("workspaceCard","workspaceOff");["left","top","width","height","zIndex"].forEach(k=>e.style[k]="");e.querySelector(":scope > .workspaceResize")?.remove();e.querySelector(":scope > .panelControlBar .workspaceMinBtn")?.remove();e.classList.toggle("screenHiddenByMode",o.hidden);e.classList.toggle("isFolded",o.folded);e.classList.toggle("panelMinimized",!!o.panelMinimized);const f=e.querySelector(":scope > .panelControlBar .panelFoldBtn");if(f)f.textContent=o.folded?"DÉPLIER":"REPLIER";if(o.next&&o.next.parentNode===o.parent)o.parent.insertBefore(e,o.next);else o.parent.appendChild(e)}
function prep(e,k){if(!e.classList.contains("workspaceCard"))orig.set(e,{parent:e.parentNode,next:e.nextSibling,hidden:e.classList.contains("screenHiddenByMode"),folded:e.classList.contains("isFolded"),panelMinimized:e.classList.contains("panelMinimized")});e.classList.remove("screenHiddenByMode","isFolded","panelMinimized");e.classList.add("workspaceCard");if(e.parentNode!==surface)surface.appendChild(e);const tools=ensurePanelTools(e,k);const close=ensureCloseButton(k,e);if(!tools.querySelector(".workspaceMinBtn")){const b=document.createElement("button");b.type="button";b.className="workspaceMinBtn";b.textContent="▁";b.title="Réduire en icône";b.onclick=x=>{x.preventDefault();x.stopPropagation();minimize(k)};tools.insertBefore(b,close)}if(!e.querySelector(":scope > .workspaceResize")){const r=document.createElement("div");r.className="workspaceResize";r.onpointerdown=x=>resizeStart(x,k);e.appendChild(r)}const bar=e.querySelector(":scope > .panelControlBar");if(bar&&!bar.dataset.desktopDrag){bar.dataset.desktopDrag="1";bar.onpointerdown=x=>{if(!x.target.closest("button,input,select,textarea,a"))dragStart(x,k)}}}
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
  dispatchEvent(new CustomEvent("BRUTUS_PANEL_REOPENED",{detail:{key:k,screen:SCREEN}}));
}
function routeWindow(k,targetScreen){
  const m=state.live.modules[k],target=Number(targetScreen);if(!m||target<1||target>5)return;
  state.enabled=true;
  m.closed=false;delete m.closedScreen;m.min=false;m.screen=target;m.x=16;m.y=48;m.precise=false;bump(m);save();apply();
  dispatchEvent(new CustomEvent("BRUTUS_PANEL_REOPENED",{detail:{key:k,screen:target}}));
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
  dispatchEvent(new CustomEvent("BRUTUS_PANEL_REOPENED",{detail:{key:k,screen:targetScreen}}));
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
function closeAllWindows(){
  if(!state?.live?.modules)return;
  for(const [k,m] of Object.entries(state.live.modules)){
    m.closed=true;m.closedScreen=Number(m.screen)||home(cards.get(k),k);m.min=false;
  }
  state.enabled=true;save();apply();
}
function profiles(){const s=document.querySelector(".workspaceProfiles");if(!s)return;const cur=state.active||s.value;s.innerHTML='<option value="">MODULES SAUVÉS</option>';Object.keys(state.profiles).sort().forEach(n=>{const o=document.createElement("option");o.value=n;o.textContent=n;s.appendChild(o)});if(state.profiles[cur])s.value=cur}
function apply(){if(applying)return;applying=true;state.enabled=true;document.body.classList.add("brutusDesktopMode");const b=document.querySelector(".workspaceModeBtn");if(b){b.classList.add("active");b.textContent="RANGER TOUT"}for(const[k,e]of cards){prep(e,k);cardApply(k,e)}iconRender();profiles();syncClosedClasses();refreshWindowMenu();applyGlobalFont();dispatchEvent(new Event("resize"));applying=false}
function ui(){const tb=document.getElementById("screenTitleBar");
windowMenu=document.getElementById("workspaceModuleMenu");
let menuBtn=document.getElementById("workspaceModuleButton");
windowMenuList=document.getElementById("workspaceModuleList");
if(!windowMenu||!menuBtn||!windowMenuList){
  windowMenu=document.createElement("div");windowMenu.className="workspaceWindowMenu";
  menuBtn=document.createElement("button");menuBtn.type="button";menuBtn.className="screenLaunchBtn workspaceWindowMenuBtn";menuBtn.textContent="MODULE";menuBtn.title="Afficher les fenêtres et programmes cachés";
  windowMenuList=document.createElement("div");windowMenuList.className="workspaceWindowMenuList";
  windowMenu.append(menuBtn,windowMenuList);tb?.insertBefore(windowMenu,tb.children[1]||null);
}
menuBtn.addEventListener("click",e=>{e.preventDefault();e.stopPropagation();windowMenu.classList.toggle("open");refreshWindowMenu()});
windowMenu.addEventListener("pointerdown",e=>e.stopPropagation());
document.addEventListener("pointerdown",e=>{if(windowMenu&&!windowMenu.contains(e.target))windowMenu.classList.remove("open")});
const b=document.createElement("button");b.className="workspaceModeBtn active";b.type="button";b.textContent="RANGER TOUT";b.title="Fermer et ranger toutes les fenêtres";b.onclick=()=>closeAllWindows();tb?.insertBefore(b,tb.children[1]||null);surface=document.createElement("section");surface.className="workspaceSurface";surface.innerHTML='<div class="workspaceToolbar"><span>MODULE</span><input class="workspaceName" maxlength="48" placeholder="ex. TEST-RÉSONANCE"><button class="workspaceSave">ENREGISTRER</button><select class="workspaceProfiles"><option value="">MODULES SAUVÉS</option></select><button class="workspaceLoad">OUVRIR</button><span class="workspaceHint">6 AIMANTS · SNAP 16px · SHIFT = LIBRE · S1 = LABO · S2–S5 = EXTENSIONS</span></div>';icons=document.createElement("div");icons.className="workspaceIcons";surface.appendChild(icons);magnetGhost=document.createElement("div");magnetGhost.className="workspaceMagnetGhost";surface.appendChild(magnetGhost);document.querySelector(".shell")?.appendChild(surface);document.querySelector(".workspaceSave").onclick=()=>{const n=(document.querySelector(".workspaceName").value||"").trim().slice(0,48);if(!n)return;state.profiles[n]={name:n,version:3,workspaceModel:WORKSPACE_MODEL,live:clone(state.live)};state.active=n;save();profiles()};document.querySelector(".workspaceLoad").onclick=()=>{const n=document.querySelector(".workspaceProfiles").value;if(!state.profiles[n])return;state.live=clone(state.profiles[n].live);state.active=n;state.enabled=true;state=normalize(state);save();apply()}}
function init(){document.querySelectorAll(".foldablePanel").forEach(e=>{const k=keyOf(e);if(k&&!cards.has(k))cards.set(k,e)});if(!cards.size){initGlobalFont();initScreenZoom();document.documentElement.classList.remove("brutusWorkspaceBoot");return}for(const[k,e]of cards)e.dataset.desktopHome=String(home(e,k));style();ui();load();reconcilePanelHiddenState();installCloseButtons();installIconTransfers();addEventListener("BRUTUS_PANEL_CLOSE_REQUEST",e=>{const k=String(e.detail?.key||"");if(cards.has(k))closeCard(k)});channel="BroadcastChannel"in window?new BroadcastChannel(CHAN):null;if(channel)channel.onmessage=e=>{if(e.data?.type==="STATE"){state=normalize(clone(e.data.state));reconcilePanelHiddenState();apply()}};addEventListener("storage",e=>{if(e.key===KEY&&e.newValue){try{state=normalize(JSON.parse(e.newValue));reconcilePanelHiddenState();apply()}catch(_){}}});profiles();apply();initGlobalFont();initScreenZoom();document.documentElement.classList.remove("brutusWorkspaceBoot");dispatchEvent(new CustomEvent("BRUTUS_WORKSPACE_READY",{detail:{screen:SCREEN,module_count:cards.size}}))}
if(document.readyState==="loading")addEventListener("DOMContentLoaded",init,{once:true});else init();
})();