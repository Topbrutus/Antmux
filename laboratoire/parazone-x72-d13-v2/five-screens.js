const cards=[...document.querySelectorAll(".card")];
const LOGICAL=[
  {n:1,name:"MASTER",url:"screen-1-master.html"},
  {n:2,name:"ANALYSIS",url:"screen-2-analysis.html"},
  {n:3,name:"OPERATOR",url:"screen-3-operator.html"},
  {n:4,name:"CONTROL",url:"screen-4-control.html"},
  {n:5,name:"SETTINGS",url:"screen-5-settings.html"}
];
const LEGACY_PLACEMENT_KEY="BRUTUS_SCREEN_PLACEMENT_V1";
const GEOMETRY_KEY="BRUTUS_SCREEN_GEOMETRY_V1";
const geometryChannel=("BroadcastChannel" in window)?new BroadcastChannel("BRUTUS_SCREEN_GEOMETRY_V1"):null;

function loadWindowGeometry(){
  try{return JSON.parse(localStorage.getItem(GEOMETRY_KEY)||"null")}catch(_){return null}
}
function geometryCount(saved){
  return Object.keys(saved?.windows||{}).filter(k=>{
    const n=Number(k);return Number.isInteger(n)&&n>=1&&n<=5;
  }).length;
}
function formatGeometry(g){
  if(!g)return "NON MÉMORISÉ";
  return "X "+Math.round(Number(g.x)||0)+" · Y "+Math.round(Number(g.y)||0)+" · "+Math.round(Number(g.width)||0)+"×"+Math.round(Number(g.height)||0);
}
function renderSavedGeometry(){
  const saved=loadWindowGeometry();
  const windows=saved?.windows||{};
  const count=geometryCount(saved);
  const mapping=document.getElementById("mapping");
  const status=document.getElementById("placementStatus");
  const info=document.getElementById("physicalList");
  const restore=document.getElementById("restoreCurrentPlacement");

  mapping.innerHTML="";
  for(const x of LOGICAL){
    const cell=document.createElement("div");cell.className="mapCell";
    const title=document.createElement("strong");title.textContent="SCREEN "+x.n+" · "+x.name;
    const value=document.createElement("div");value.textContent=formatGeometry(windows[x.n]);
    cell.append(title,value);mapping.appendChild(cell);
  }

  restore.hidden=count!==5;
  if(count===5){
    const d=saved?.savedAt?new Date(saved.savedAt):null;
    status.textContent="5/5 PAGES LOCALISÉES ET MÉMORISÉES";
    status.classList.remove("warn");
    info.textContent=d?"Dernière sauvegarde : "+d.toLocaleString():"Placement mémorisé.";
  }else if(count>0){
    status.textContent=count+"/5 PAGES MÉMORISÉES · SAUVEGARDE INCOMPLÈTE";
    status.classList.add("warn");
    info.textContent="Relance LOCALISER + SAUVEGARDER avec les cinq pages ouvertes.";
  }else{
    status.textContent="AUCUN PLACEMENT MÉMORISÉ";
    status.classList.remove("warn");
    info.textContent="Place les cinq fenêtres comme tu les veux, puis clique LOCALISER + SAUVEGARDER LES 5.";
  }
}
function captureWindowGeometry(timeoutMs=1200){
  return new Promise(resolve=>{
    if(!geometryChannel)return resolve({});
    const requestId="CAPTURE-"+Date.now()+"-"+Math.random().toString(36).slice(2);
    const found={};
    let done=false;
    const finish=()=>{
      if(done)return;
      done=true;
      geometryChannel.removeEventListener("message",onMessage);
      resolve(found);
    };
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
async function localizeAndSaveFive(){
  const status=document.getElementById("placementStatus");
  if(!geometryChannel){
    status.textContent="LOCALISATION IMPOSSIBLE · BroadcastChannel non disponible";
    status.classList.add("warn");
    return;
  }
  status.textContent="LOCALISATION DES 5 PAGES…";
  status.classList.remove("warn");
  const windows=await captureWindowGeometry();
  const count=Object.keys(windows).length;
  if(count!==5){
    status.textContent=count+"/5 PAGES TROUVÉES · SAUVEGARDE NON MODIFIÉE";
    status.classList.add("warn");
    return;
  }
  localStorage.setItem(GEOMETRY_KEY,JSON.stringify({version:2,savedAt:Date.now(),windows}));
  renderSavedGeometry();
}
function applySavedWindowPlacement(timeoutMs=1400){
  return new Promise(resolve=>{
    const saved=loadWindowGeometry(),windows=saved?.windows||{};
    if(!geometryChannel||geometryCount(saved)!==5)return resolve({requested:0,applied:0});
    const requestId="RESTORE-"+Date.now()+"-"+Math.random().toString(36).slice(2);
    const applied=new Set();
    let done=false;
    const finish=()=>{
      if(done)return;
      done=true;
      geometryChannel.removeEventListener("message",onMessage);
      resolve({requested:5,applied:applied.size});
    };
    const onMessage=e=>{
      const m=e.data||{};
      if(m.type!=="GEOMETRY_APPLIED"||String(m.requestId||"")!==requestId)return;
      const n=Number(m.geometry?.screen);
      if(Number.isInteger(n)&&n>=1&&n<=5)applied.add(n);
      if(applied.size===5)finish();
    };
    geometryChannel.addEventListener("message",onMessage);
    for(const [n,g] of Object.entries(windows)){
      geometryChannel.postMessage({type:"APPLY_GEOMETRY",requestId,targetScreen:Number(n),geometry:g});
    }
    setTimeout(finish,timeoutMs);
  });
}
async function recallSavedPlacement(){
  const status=document.getElementById("placementStatus");
  const saved=loadWindowGeometry();
  if(geometryCount(saved)!==5){
    renderSavedGeometry();
    return;
  }
  status.textContent="RAPPEL DU PLACEMENT MÉMORISÉ…";
  const result=await applySavedWindowPlacement();
  status.textContent="PLACEMENT RAPPELÉ · "+result.applied+"/5 PAGES ONT CONFIRMÉ";
  status.classList.toggle("warn",result.applied!==5);
}
function openScreen(btn){
  const n=Number(btn.dataset.screen),u=btn.dataset.url;
  const saved=loadWindowGeometry(),g=saved?.windows?.[n];
  let features="popup=yes,resizable=yes,scrollbars=yes,width=1280,height=900";
  if(g){
    features="popup=yes,resizable=yes,scrollbars=yes,left="+Math.round(g.x)+",top="+Math.round(g.y)+",width="+Math.round(g.width)+",height="+Math.round(g.height);
  }
  const w=window.open(u,"BRUTUS_SCREEN_"+n,features);
  if(w&&g&&geometryChannel){
    setTimeout(()=>{
      geometryChannel.postMessage({
        type:"APPLY_GEOMETRY",
        requestId:"OPEN-"+Date.now()+"-"+n,
        targetScreen:n,
        geometry:g
      });
    },700);
  }
  return w;
}
function clearPlacement(){
  localStorage.removeItem(GEOMETRY_KEY);
  localStorage.removeItem(LEGACY_PLACEMENT_KEY);
  renderSavedGeometry();
  const status=document.getElementById("placementStatus");
  status.textContent="PLACEMENT EFFACÉ · AUCUNE POSITION MÉMORISÉE";
  status.classList.remove("warn");
}

cards.forEach(b=>b.addEventListener("click",()=>openScreen(b)));
document.getElementById("saveCurrentPlacement").addEventListener("click",localizeAndSaveFive);
document.getElementById("restoreCurrentPlacement").addEventListener("click",recallSavedPlacement);
document.getElementById("resetPlacement").addEventListener("click",clearPlacement);

renderSavedGeometry();
