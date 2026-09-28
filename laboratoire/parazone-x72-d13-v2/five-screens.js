const cards=[...document.querySelectorAll(".card")];
const LOGICAL=[
  {n:1,name:"MASTER",url:"screen-1-master.html"},
  {n:2,name:"ANALYSIS",url:"screen-2-analysis.html"},
  {n:3,name:"OPERATOR",url:"screen-3-operator.html"},
  {n:4,name:"CONTROL",url:"screen-4-control.html"},
  {n:5,name:"SETTINGS",url:"screen-5-settings.html"}
];
const PLACEMENT_KEY="BRUTUS_SCREEN_PLACEMENT_V1";
const GEOMETRY_KEY="BRUTUS_SCREEN_GEOMETRY_V1";
const geometryChannel=("BroadcastChannel"in window)?new BroadcastChannel("BRUTUS_SCREEN_GEOMETRY_V1"):null;
let physicalScreens=[];
let screenDetailsHandle=null;
function screenSignature(s){return [s.left,s.top,s.width,s.height].join(":")}
function plainScreen(s,i){
  return {id:screenSignature(s),index:i,label:s.label||("MONITEUR "+(i+1)),
    left:s.left,top:s.top,width:s.width,height:s.height,
    availLeft:Number.isFinite(s.availLeft)?s.availLeft:s.left,
    availTop:Number.isFinite(s.availTop)?s.availTop:s.top,
    availWidth:Number.isFinite(s.availWidth)?s.availWidth:s.width,
    availHeight:Number.isFinite(s.availHeight)?s.availHeight:s.height,
    isPrimary:!!s.isPrimary,isInternal:!!s.isInternal};
}
function fallbackScreen(){
  return plainScreen({left:window.screenX||0,top:window.screenY||0,width:screen.width,height:screen.height,
    availLeft:screen.availLeft||0,availTop:screen.availTop||0,
    availWidth:screen.availWidth||screen.width,availHeight:screen.availHeight||screen.height,
    isPrimary:true,label:"MONITEUR COURANT"},0);
}
function loadPlacement(){
  try{return JSON.parse(localStorage.getItem(PLACEMENT_KEY)||"{}")}catch(_){return {}}
}
function savePlacement(){
  const map={};
  document.querySelectorAll("select[data-logical]").forEach(sel=>map[sel.dataset.logical]=sel.value);
  localStorage.setItem(PLACEMENT_KEY,JSON.stringify(map));
}
function loadWindowGeometry(){
  try{return JSON.parse(localStorage.getItem(GEOMETRY_KEY)||"null")}catch(_){return null}
}
function geometryCount(saved){
  return Object.keys(saved?.windows||{}).filter(k=>Number(k)>=1&&Number(k)<=5).length;
}
function captureWindowGeometry(timeoutMs=900){
  return new Promise(resolve=>{
    if(!geometryChannel)return resolve({});
    const requestId="CAPTURE-"+Date.now()+"-"+Math.random().toString(36).slice(2);
    const found={};let done=false;
    const finish=()=>{if(done)return;done=true;geometryChannel.removeEventListener("message",onMessage);resolve(found)};
    const onMessage=e=>{
      const m=e.data||{};
      if(m.type!=="GEOMETRY"||String(m.requestId||"")!==requestId)return;
      const g=m.geometry||{},n=Number(g.screen);
      if(!Number.isInteger(n)||n<1||n>5)return;
      found[n]={
        x:Number(g.x)||0,
        y:Number(g.y)||0,
        width:Math.max(320,Number(g.width)||1280),
        height:Math.max(240,Number(g.height)||900)
      };
      if(Object.keys(found).length===5)finish();
    };
    geometryChannel.addEventListener("message",onMessage);
    geometryChannel.postMessage({type:"CAPTURE_REQUEST",requestId});
    setTimeout(finish,timeoutMs);
  });
}
async function saveCurrentWindowPlacement(){
  const status=document.getElementById("placementStatus");
  if(!geometryChannel){
    status.textContent="SAUVEGARDE IMPOSSIBLE · BroadcastChannel non disponible";
    status.classList.add("warn");
    return;
  }
  status.textContent="LECTURE DE LA POSITION DES 5 FENÊTRES…";
  const windows=await captureWindowGeometry();
  const count=Object.keys(windows).length;
  if(!count){
    status.textContent="AUCUNE FENÊTRE BRUTUS N'A RÉPONDU · laisse les fenêtres ouvertes puis réessaie";
    status.classList.add("warn");
    return;
  }
  const saved={version:1,savedAt:Date.now(),windows};
  localStorage.setItem(GEOMETRY_KEY,JSON.stringify(saved));
  status.textContent="PLACEMENT MANUEL SAUVEGARDÉ · "+count+"/5 FENÊTRES";
  status.classList.toggle("warn",count<5);
}
function applySavedWindowPlacement(timeoutMs=1100){
  return new Promise(resolve=>{
    const saved=loadWindowGeometry(),windows=saved?.windows||{};
    if(!geometryChannel||!Object.keys(windows).length)return resolve({requested:0,applied:0});
    const requestId="RESTORE-"+Date.now()+"-"+Math.random().toString(36).slice(2);
    const applied=new Set();let done=false;
    const finish=()=>{if(done)return;done=true;geometryChannel.removeEventListener("message",onMessage);resolve({requested:Object.keys(windows).length,applied:applied.size})};
    const onMessage=e=>{
      const m=e.data||{};
      if(m.type!=="GEOMETRY_APPLIED"||String(m.requestId||"")!==requestId)return;
      const n=Number(m.geometry?.screen);
      if(Number.isInteger(n)&&n>=1&&n<=5)applied.add(n);
      if(applied.size>=Object.keys(windows).length)finish();
    };
    geometryChannel.addEventListener("message",onMessage);
    for(const [n,g] of Object.entries(windows)){
      geometryChannel.postMessage({type:"APPLY_GEOMETRY",requestId,targetScreen:Number(n),geometry:g});
    }
    setTimeout(finish,timeoutMs);
  });
}
async function restoreCurrentWindowPlacement(){
  const status=document.getElementById("placementStatus");
  const saved=loadWindowGeometry(),count=geometryCount(saved);
  if(!count){
    status.textContent="AUCUN PLACEMENT MANUEL SAUVEGARDÉ";
    status.classList.add("warn");
    return;
  }
  status.textContent="REPLACEMENT DES FENÊTRES…";
  const result=await applySavedWindowPlacement();
  status.textContent="PLACEMENT RESTAURÉ · "+result.applied+"/"+result.requested+" FENÊTRES ONT CONFIRMÉ";
  status.classList.toggle("warn",result.applied<result.requested);
}
function sortedScreens(items){
  return [...items].sort((a,b)=>(a.left-b.left)||(a.top-b.top)||(a.index-b.index));
}
function defaultMapping(){
  const ordered=sortedScreens(physicalScreens),map={};
  LOGICAL.forEach((x,i)=>{
    if(ordered.length)map[x.n]=ordered[Math.min(i,ordered.length-1)].id;
  });
  return map;
}
function renderMapping(){
  const saved=loadPlacement(),defaults=defaultMapping();
  const mapping=document.getElementById("mapping");
  mapping.innerHTML="";
  LOGICAL.forEach(x=>{
    const cell=document.createElement("div");cell.className="mapCell";
    const title=document.createElement("strong");title.textContent="BRUTUS "+x.n+" · "+x.name;
    const select=document.createElement("select");select.dataset.logical=String(x.n);
    physicalScreens.forEach(s=>{
      const o=document.createElement("option");o.value=s.id;
      o.textContent=(s.isPrimary?"★ ":"")+s.label+" · "+s.width+"×"+s.height+" @ "+s.left+","+s.top;
      select.appendChild(o);
    });
    select.value=physicalScreens.some(s=>s.id===saved[x.n])?saved[x.n]:(defaults[x.n]||"");
    select.addEventListener("change",savePlacement);
    cell.append(title,select);mapping.appendChild(cell);
  });
  savePlacement();
  document.getElementById("physicalList").innerHTML=physicalScreens.map((s,i)=>
    "<b>"+(i+1)+". "+s.label+"</b> · "+s.width+"×"+s.height+" · position "+s.left+","+s.top+(s.isPrimary?" · PRIMARY":"")
  ).join("<br>")||"Aucun moniteur détaillé détecté.";
}
async function detectPhysicalScreens(){
  const status=document.getElementById("placementStatus");
  try{
    if("getScreenDetails" in window){
      screenDetailsHandle=await window.getScreenDetails();
      physicalScreens=screenDetailsHandle.screens.map(plainScreen);
      status.textContent=physicalScreens.length+" MONITEUR(S) DÉTECTÉ(S) · WINDOW MANAGEMENT ACTIVE";
      status.classList.remove("warn");
      if(screenDetailsHandle&&screenDetailsHandle.addEventListener){
        screenDetailsHandle.addEventListener("screenschange",()=>{
          physicalScreens=screenDetailsHandle.screens.map(plainScreen);renderMapping();
        });
      }
    }else{
      physicalScreens=[fallbackScreen()];
      status.textContent="API MULTI-ÉCRANS NON DISPONIBLE · MODE MANUEL / MONITEUR COURANT";
      status.classList.add("warn");
    }
  }catch(err){
    physicalScreens=[fallbackScreen()];
    status.textContent="ACCÈS MULTI-ÉCRANS NON ACCORDÉ · MODE MANUEL · "+(err&&err.name?err.name:"ERROR");
    status.classList.add("warn");
  }
  renderMapping();
  return physicalScreens;
}
function openScreen(btn,features){
  const n=btn.dataset.screen,u=btn.dataset.url;
  return window.open(u,"BRUTUS_SCREEN_"+n,features||"popup=yes,width=1280,height=900,resizable=yes,scrollbars=yes");
}
async function autoPlaceFive(){
  const status=document.getElementById("placementStatus");
  const placeholders={};
  LOGICAL.forEach(x=>{
    placeholders[x.n]=window.open("about:blank","BRUTUS_SCREEN_"+x.n,
      "popup=yes,width=640,height=480,resizable=yes,scrollbars=yes");
  });
  await detectPhysicalScreens();
  const saved=loadPlacement(),defaults=defaultMapping();
  let opened=0;
  for(const x of [LOGICAL[2],LOGICAL[0],LOGICAL[1],LOGICAL[3],LOGICAL[4]]){
    const targetId=saved[x.n]||defaults[x.n];
    const physical=physicalScreens.find(s=>s.id===targetId)||physicalScreens[0];
    const w=placeholders[x.n];
    if(!w)continue;
    try{
      if(physical){
        w.moveTo(physical.availLeft,physical.availTop);
        w.resizeTo(Math.max(640,physical.availWidth),Math.max(480,physical.availHeight));
      }
      w.location.replace(x.url);opened++;
    }catch(_){
      try{w.location=x.url;opened++}catch(__){}
    }
  }
  if(opened<5){
    status.textContent="POP-UPS PARTIELLEMENT BLOQUÉS · "+opened+"/5 OUVERTS · autoriser les pop-ups puis recommencer";
    status.classList.add("warn");
  }else if(physicalScreens.length<5){
    status.textContent="5 FENÊTRES OUVERTES · "+physicalScreens.length+" MONITEUR(S) DÉTECTÉ(S) · placement manuel possible";
    status.classList.add("warn");
  }else{
    status.textContent="5/5 OUVERTS ET PLACÉS · MAPPING MÉMORISÉ";
    status.classList.remove("warn");
  }
}
cards.forEach(b=>b.addEventListener("click",()=>openScreen(b)));
document.getElementById("detectScreens").addEventListener("click",detectPhysicalScreens);
document.getElementById("autoPlace").addEventListener("click",autoPlaceFive);
document.getElementById("openOperator").addEventListener("click",()=>
  openScreen(document.querySelector('[data-screen="3"]')));
document.getElementById("openAll").addEventListener("click",()=>{
  [3,1,2,4,5].forEach(n=>openScreen(document.querySelector('[data-screen="'+n+'"]')));
});
document.getElementById("saveCurrentPlacement").addEventListener("click",saveCurrentWindowPlacement);
document.getElementById("restoreCurrentPlacement").addEventListener("click",restoreCurrentWindowPlacement);
document.getElementById("resetPlacement").addEventListener("click",()=>{
  localStorage.removeItem(PLACEMENT_KEY);
  localStorage.removeItem(GEOMETRY_KEY);
  renderMapping();
  document.getElementById("placementStatus").textContent="PLACEMENTS MÉMORISÉS EFFACÉS";
});
physicalScreens=[fallbackScreen()];
renderMapping();
const savedGeometry=loadWindowGeometry();
if(geometryCount(savedGeometry)){
  document.getElementById("placementStatus").textContent="PLACEMENT MANUEL SAUVEGARDÉ · "+geometryCount(savedGeometry)+"/5 FENÊTRES";
}
