(() => {
  "use strict";

  const THEME = {
    bg:"#05070C", panel:"#0A0F18", panel2:"#0D1420", grid:"#172333",
    text:"#F2F5F8", muted:"#8795A8", gold:"#F6B94A", gold2:"#FFDF8A",
    cyan:"#39D8FF", blue:"#4B7CFF", magenta:"#E65BFF", violet:"#8B5CFF",
    green:"#5CFFB1", warning:"#FFB84C", error:"#FF557A", white:"#FFFFFF"
  };

  const $ = id => document.getElementById(id);
  const els = {
    canvas:$("lifeClock"), mode:$("mode"), tick:$("tick"), dt:$("dt"), rexec:$("rexec"),
    frt:$("frt"), activity:$("activity"), memory:$("memory"), crystal:$("crystal"),
    repair:$("repair"), integrity:$("integrity"), events:$("events"), generation:$("generation"),
    eventBus:$("eventBus"), proofBox:$("proofBox"), status:$("status"),
    pauseBtn:$("pauseBtn"), faultBtn:$("faultBtn"), repairBtn:$("repairBtn"),
    resetBtn:$("resetBtn"), snapshotBtn:$("snapshotBtn"), referenceCheck:$("referenceCheck"),
    reportFault:$("reportFault"), reportSteps:$("reportSteps"), reportVerdict:$("reportVerdict"),
    z3Topology:$("z3Topology"), z3History:$("z3History"), z3Center:$("z3Center"),
    z3Theta:$("z3Theta"), z3Verify:$("z3Verify"), z3Hash:$("z3Hash"),
    runtimeBadge:$("runtimeBadge")
  };

  const ctx = els.canvas.getContext("2d");
  let lastState = null;
  let previousState = null;
  let connected = false;
  let socket = null;
  let reconnectTimer = null;
  let lastMessageAt = 0;
  let messageIntervalMs = 250;
  let stars = [];

  function api(path){ return new URL(path, window.location.href).toString(); }
  function wsUrl(){
    const url = new URL("./ws", window.location.href);
    url.protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return url.toString();
  }
  function clamp(v,a=0,b=1){ return Math.max(a,Math.min(b,Number(v)||0)); }
  function fmt(v,n=3){ return Number(v || 0).toFixed(n); }
  function lerp(a,b,t){ return Number(a||0)+(Number(b||0)-Number(a||0))*t; }
  function phaseFromState(state, scale=0.01){
    return state ? Number(state._visualTick ?? state.tick_count ?? 0) * scale : 0;
  }

  function interpolateVisualState(previous,current,alpha){
    if(!current) return null;
    if(!previous) return current;
    const out={...current};
    out._visualTick=lerp(previous.tick_count,current.tick_count,alpha);
    for(const field of ["activity_level","memory_level","crystallization_level","repair_level","error_level"]){
      out[field]=lerp(previous[field],current[field],alpha);
    }
    const previousById=new Map((previous.synapses||[]).map(s=>[s.synapse_id,s]));
    out.synapses=(current.synapses||[]).map(s=>{
      const before=previousById.get(s.synapse_id);
      if(!before) return s;
      return {
        ...s,
        activity:lerp(before.activity,s.activity,alpha),
        memory:lerp(before.memory,s.memory,alpha),
        crystal:lerp(before.crystal,s.crystal,alpha),
        repair_progress:lerp(before.repair_progress,s.repair_progress,alpha)
      };
    });
    return out;
  }

  function visualStateForFrame(now){
    if(!lastState) return null;
    if(!connected || !previousState) return lastState;
    const interval=Math.max(80,Math.min(1000,messageIntervalMs||250));
    const alpha=Math.max(0,Math.min(1,(now-lastMessageAt)/interval));
    return interpolateVisualState(previousState,lastState,alpha);
  }

  function repairDisplay(state){
    const raw=String(state?.repair_verdict||"").toUpperCase();
    if(state?.queen_mode==="AUTO_REPAIR") return {label:"REPAIRING",detail:"RÉPARATION EN COURS",ok:true};
    if(!state?.integrity_match) return {label:raw==="INVALID"?"FAULT ACTIVE":(raw||"FAULT"),detail:"PANNE ACTIVE",ok:false};
    if(raw==="INVALID") return {label:"READY",detail:"AUCUNE PANNE",ok:true};
    if(raw==="PASS") return {label:"PASS",detail:"RÉPARATION VÉRIFIÉE",ok:true};
    if(raw==="FAIL") return {label:"FAIL",detail:"RÉPARATION ÉCHOUÉE",ok:false};
    return {label:raw||"READY",detail:"AUCUNE PANNE",ok:true};
  }

  async function postJson(path, body){
    const response = await fetch(api(path), {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:body ? JSON.stringify(body) : "{}"
    });
    const json = await response.json().catch(()=>({detail:"Réponse non JSON"}));
    if(!response.ok) throw new Error(json.detail || `HTTP ${response.status}`);
    return json;
  }

  function setStatus(text, bad=false){
    els.status.textContent = text;
    els.status.className = bad ? "status bad" : "status";
  }

  function resizeCanvas(){
    const dpr=Math.max(1,Math.min(2,window.devicePixelRatio||1));
    const rect=els.canvas.getBoundingClientRect();
    const w=Math.max(320,Math.floor(rect.width));
    const h=Math.max(320,Math.floor(rect.height));
    if(els.canvas.width!==Math.floor(w*dpr)||els.canvas.height!==Math.floor(h*dpr)){
      els.canvas.width=Math.floor(w*dpr);
      els.canvas.height=Math.floor(h*dpr);
      ctx.setTransform(dpr,0,0,dpr,0,0);
      els.canvas._cssW=w;
      els.canvas._cssH=h;
      stars=[];
    }
  }

  function seededRandom(seed){
    let t=seed>>>0;
    return ()=>{
      t += 0x6D2B79F5;
      let r=Math.imul(t^(t>>>15),1|t);
      r ^= r + Math.imul(r^(r>>>7),61|r);
      return ((r^(r>>>14))>>>0)/4294967296;
    };
  }

  function nodePos(i,cx,cy,r){
    const a=-Math.PI/2+i*Math.PI*2/7;
    return [cx+Math.cos(a)*r*.76,cy+Math.sin(a)*r*.76];
  }

  function drawGear(cx,cy,radius,teeth,angle,color,width=2){
    ctx.beginPath();
    for(let i=0;i<teeth*2;i++){
      const a=angle+i*Math.PI/teeth;
      const rr=radius*(i%2===0?1:.90);
      const x=cx+Math.cos(a)*rr;
      const y=cy+Math.sin(a)*rr;
      if(i===0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
    }
    ctx.closePath();
    ctx.strokeStyle=color;
    ctx.lineWidth=width;
    ctx.stroke();
  }

  function drawMeter(cx,cy,radius,value,color){
    ctx.beginPath();
    ctx.arc(cx,cy,radius,0,Math.PI*2);
    ctx.strokeStyle=THEME.grid;
    ctx.lineWidth=2;
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(cx,cy,radius,-Math.PI/2,-Math.PI/2+Math.PI*2*clamp(value));
    ctx.strokeStyle=color;
    ctx.lineWidth=5;
    ctx.stroke();
  }

  function draw(state){
    resizeCanvas();
    const w=els.canvas._cssW,h=els.canvas._cssH;
    ctx.clearRect(0,0,w,h);
    ctx.fillStyle=THEME.bg;
    ctx.fillRect(0,0,w,h);

    const cx=w*.5, cy=h*.5, r=Math.min(w,h)*.34;
    const phase=phaseFromState(state,.012);
    const visualTick=state ? Number(state._visualTick ?? state.tick_count ?? 0) : 0;
    const synapses=state?.synapses || [];
    const relations=state?.relations || [];

    ctx.strokeStyle=THEME.grid;
    ctx.lineWidth=1;
    for(let x=0;x<=w+40;x+=40){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,h);ctx.stroke();}
    for(let y=0;y<=h+40;y+=40){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke();}

    if(!stars.length){
      const rnd=seededRandom((Math.floor(w)*100003+Math.floor(h))>>>0);
      const count=Math.max(40,Math.floor(w*h/18000));
      stars=Array.from({length:count},()=>[rnd()*w,rnd()*h,rnd()<.8?1:2]);
    }
    ctx.fillStyle=THEME.muted;
    stars.forEach(([x,y,rr])=>{ctx.beginPath();ctx.arc(x,y,rr,0,Math.PI*2);ctx.fill();});

    relations.forEach(([a,b])=>{
      const sa=synapses[a], sb=synapses[b];
      if(!sa||!sb) return;
      const [x1,y1]=nodePos(a,cx,cy,r), [x2,y2]=nodePos(b,cx,cy,r);
      const intensity=(Number(sa.activity||0)+Number(sb.activity||0))/2;
      let color=intensity>.45?THEME.cyan:THEME.blue;
      if(!(sa.enabled&&sb.enabled)) color=THEME.error;
      ctx.strokeStyle=color;
      ctx.lineWidth=1+3*clamp(intensity);
      ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke();

      if(intensity>.25&&sa.enabled&&sb.enabled){
        const q=((visualTick*.011)+a*.19+b*.07)%1;
        const px=x1+(x2-x1)*q, py=y1+(y2-y1)*q;
        ctx.fillStyle=THEME.gold2;
        ctx.beginPath();
        ctx.arc(px,py,2+3*clamp(intensity),0,Math.PI*2);
        ctx.fill();
      }
    });

    const activity=clamp(state?.activity_level);
    const memory=clamp(state?.memory_level);
    const crystal=clamp(state?.crystallization_level);
    const speed=.15+.85*activity;

    drawGear(cx,cy,r*1.02,36,phase*speed,THEME.gold,2);
    drawGear(cx,cy,r*.84,28,-phase*1.25*speed,THEME.cyan,2);
    drawGear(cx,cy,r*.60,20,phase*1.8*speed,THEME.violet,2);
    drawMeter(cx,cy,r*1.12,crystal,THEME.gold);
    drawMeter(cx,cy,r*.72,memory,THEME.cyan);
    drawMeter(cx,cy,r*.48,activity,THEME.magenta);

    const diamondCount=Math.floor(8+crystal*64);
    const rnd=seededRandom(1307);
    for(let i=0;i<diamondCount;i++){
      const a=rnd()*Math.PI*2, rr=r*(.28+rnd()*.58);
      const x=cx+Math.cos(a)*rr,y=cy+Math.sin(a)*rr;
      const size=2+9*crystal*(.35+rnd()*.65), rot=a+phase*.08;
      ctx.beginPath();
      for(let k=0;k<4;k++){
        const aa=rot+k*Math.PI/2, mul=k%2===0?1:.45;
        const px=x+Math.cos(aa)*size*mul,py=y+Math.sin(aa)*size*mul;
        if(k===0)ctx.moveTo(px,py);else ctx.lineTo(px,py);
      }
      ctx.closePath();
      ctx.strokeStyle=i%3?THEME.gold2:THEME.cyan;
      ctx.lineWidth=1;
      ctx.stroke();
    }

    synapses.forEach((syn,i)=>{
      const [x,y]=nodePos(i,cx,cy,r);
      const pulse=1+.18*Math.sin(phase*8+i);
      const rr=(12+16*clamp(syn.activity))*pulse;
      const integrity=(Number(syn.integrity||0)/1000);
      let color=!syn.enabled||integrity<=0?THEME.error:
        (Number(syn.repair_progress||0)>0?THEME.warning:
          (Number(syn.crystal||0)>.20?THEME.gold2:THEME.cyan));

      ctx.strokeStyle=THEME.grid;
      ctx.lineWidth=2;
      ctx.beginPath();ctx.arc(x,y,rr*1.7,0,Math.PI*2);ctx.stroke();

      ctx.fillStyle=THEME.panel2;
      ctx.strokeStyle=color;
      ctx.lineWidth=3;
      ctx.beginPath();ctx.arc(x,y,rr,0,Math.PI*2);ctx.fill();ctx.stroke();

      const inn=Math.max(3,rr*clamp(syn.activity)*.65);
      ctx.fillStyle=color;
      ctx.beginPath();ctx.arc(x,y,inn,0,Math.PI*2);ctx.fill();

      ctx.fillStyle=THEME.text;
      ctx.font="bold 11px Consolas";
      ctx.textAlign="center";
      ctx.fillText(`${syn.synapse_id}  A:${fmt(syn.activity,2)}  I:${fmt(integrity,2)}`,x,y+rr+15);
    });

    const mode=state?.queen_mode || "DISCONNECTED";
    const modeColor={
      SLEEP:THEME.blue,EVENT:THEME.gold,BURST:THEME.magenta,STABLE:THEME.green,
      FAULT:THEME.error,AUTO_REPAIR:THEME.warning,DISCONNECTED:THEME.error
    }[mode]||THEME.white;
    const coreR=r*(.17+.035*Math.sin(phase*4));

    ctx.strokeStyle=THEME.grid;
    ctx.lineWidth=3;
    ctx.beginPath();ctx.arc(cx,cy,coreR*1.5,0,Math.PI*2);ctx.stroke();

    ctx.fillStyle=THEME.panel;
    ctx.strokeStyle=modeColor;
    ctx.lineWidth=4;
    ctx.beginPath();ctx.arc(cx,cy,coreR,0,Math.PI*2);ctx.fill();ctx.stroke();

    ctx.fillStyle=THEME.gold2;
    ctx.font=`bold ${Math.max(28,Math.floor(coreR*.72))}px Georgia`;
    ctx.textAlign="center";
    ctx.fillText("∞",cx,cy-4);
    ctx.fillStyle=modeColor;
    ctx.font="bold 12px Consolas";
    ctx.fillText(mode,cx,cy+coreR*.55);

    ctx.fillStyle=THEME.gold2;
    ctx.font="bold 18px Georgia";
    ctx.fillText("HORLOGE DE LA VIE — REINE",cx,cy-r*1.23);
    ctx.fillStyle=THEME.text;
    ctx.font="bold 12px Consolas";
    const repairUi=repairDisplay(state);
    ctx.fillText(
      `TICK ${Number(state?.tick_count||0).toLocaleString("fr-CA")}  •  GEN ${state?.generation ?? "—"}  •  SYNAPSES ${state?.active_synapses ?? 0}/7  •  REPAIR ${repairUi.label}`,
      cx,cy+r*1.24
    );

    ctx.textAlign="left";
    ctx.fillStyle=state?.integrity_match?THEME.green:THEME.error;
    ctx.font="bold 10px Consolas";
    const whole=String(state?.whole_h256||"—");
    ctx.fillText(`WHOLE H256 ${whole.slice(0,18)}…   PROTECTED ${state?.integrity_match?"MATCH":"MISMATCH"}`,16,h-14);

    if(!connected){
      ctx.fillStyle="rgba(5,7,12,.72)";
      ctx.fillRect(0,0,w,h);
      ctx.fillStyle=THEME.error;
      ctx.font="700 24px system-ui";
      ctx.textAlign="center";
      ctx.fillText("CORE DISCONNECTED",cx,cy);
      ctx.font="500 12px system-ui";
      ctx.fillText("Dernier VisualState gelé — aucun tick local.",cx,cy+26);
    }
  }

  function updateDom(state){
    if(!state) return;
    els.mode.textContent=state.queen_mode;
    els.tick.textContent=Number(state.tick_count||0).toLocaleString("fr-CA");
    els.dt.textContent=`${fmt(state.dt_sim,6)}s`;
    els.rexec.textContent=`${fmt(state.r_exec,1)}/s`;
    els.frt.textContent=`${fmt(state.f_rt,3)}×`;
    els.activity.textContent=fmt(state.activity_level);
    els.memory.textContent=fmt(state.memory_level);
    els.crystal.textContent=fmt(state.crystallization_level);
    els.repair.textContent=fmt(state.repair_level);
    els.integrity.textContent=state.integrity_match?"MATCH":"MISMATCH";
    els.integrity.className=state.integrity_match?"ok":"bad";
    els.events.textContent=Number(state.event_count||0).toLocaleString("fr-CA");
    els.generation.textContent=String(state.generation ?? "—");

    const z3=state.z3_runtime||null;
    const z3Latest=z3?.latest||null;
    if(z3){
      const topology=z3.topology||{};
      els.z3Topology.textContent=`${topology.total_nodes||13} NODES / ${topology.peripheral_channels||12} CH`;
      els.z3History.textContent=`${z3.history_count||0} / ${z3.history_size||32}`;
    }else{
      els.z3Topology.textContent="NON CONNECTÉ";
      els.z3History.textContent="0 / 32";
    }
    if(z3Latest){
      const c=Array.isArray(z3Latest.center)?z3Latest.center:[0,0,0];
      els.z3Center.textContent=`[${c.map(v=>fmt(v,3)).join(", ")}]`;
      els.z3Theta.textContent=`${fmt(z3Latest.theta,4)} rad`;
      els.z3Verify.textContent=z3Latest.fast_verified?"PASS":"FAIL";
      els.z3Verify.className=z3Latest.fast_verified?"ok":"bad";
      els.z3Hash.textContent=String(z3Latest.center_provenance_h256||"—").slice(0,12);
    }else{
      els.z3Center.textContent="EN ATTENTE";
      els.z3Theta.textContent="—";
      els.z3Verify.textContent="EN ATTENTE";
      els.z3Verify.className="";
      els.z3Hash.textContent="—";
    }

    els.eventBus.replaceChildren(...(state.recent_events||[]).slice().reverse().map(label=>{
      const div=document.createElement("div");
      div.textContent=`• ${label}`;
      return div;
    }));

    let proof="ID  ROLE      ACT   MEM   CRYS  INTEG  STATE\n";
    proof+="────────────────────────────────────────────────\n";
    (state.synapses||[]).forEach(s=>{
      proof += `${String(s.synapse_id).padEnd(3)} ${String(s.role).padEnd(9)} ${fmt(s.activity)} ${fmt(s.memory)} ${fmt(s.crystal)} ${String(s.integrity).padStart(4)}  ${s.enabled?"ON":"FAULT"}\n`;
    });
    const repairUi=repairDisplay(state);
    proof += `\nWHOLE H256\n${state.whole_h256||"—"}\n\nB36_50\n${state.b36_view||"—"}\n\nPROTECTED CURRENT\n${state.protected_h256||"—"}\n\nPROTECTED REFERENCE\n${state.reference_h256||"—"}\n\nÉTAT INTERFACE: ${repairUi.label} / ${repairUi.detail}\nVERDICT SERVEUR: ${state.repair_verdict||"—"}\n${state.repair_reason||""}\n`;
    els.proofBox.textContent=proof;

    els.referenceCheck.textContent=`RÉFÉRENCE H256 : ${state.integrity_match?"MATCH":"MISMATCH"}`;
    els.referenceCheck.className=state.integrity_match?"ok":"bad";
    els.reportVerdict.textContent=repairUi.label;
    els.reportVerdict.className=repairUi.ok?"ok":"bad";
    els.reportSteps.textContent=repairUi.detail||"SERVER";
    const activeFaults=(state.synapses||[])
      .filter(s=>!s.enabled||Number(s.integrity)<=0)
      .map(s=>s.synapse_id);
    const repaired=Array.isArray(state.repair_changed_synapses)
      ? state.repair_changed_synapses
      : [];
    els.reportFault.textContent=activeFaults.length
      ? activeFaults.join(", ")
      : (repaired.length ? repaired.join(", ") : "—");

    if(connected){
      setStatus("QUEEN SERVER CONNECTED — VisualState partagé, serveur autoritaire.");
      els.runtimeBadge.textContent="QUEEN SERVER V0.2 — SHARED LIVE";
    }else{
      setStatus("CORE DISCONNECTED — dernière télémétrie gelée; aucun tick local.",true);
      els.runtimeBadge.textContent="CORE DISCONNECTED";
    }
  }

  function scheduleReconnect(){
    if(reconnectTimer) return;
    reconnectTimer=setTimeout(()=>{
      reconnectTimer=null;
      connect();
    },1500);
  }

  function connect(){
    try{
      socket=new WebSocket(wsUrl());
    }catch{
      connected=false;
      updateDom(lastState);
      draw(lastState);
      scheduleReconnect();
      return;
    }

    socket.addEventListener("message",event=>{
      try{
        const incoming=JSON.parse(event.data);
        if(!incoming || incoming.source!=="QUEEN_SERVER_V0_2") throw new Error("source inattendue");
        const now=performance.now();
        if(lastMessageAt>0){
          const observed=Math.max(80,Math.min(1000,now-lastMessageAt));
          messageIntervalMs=messageIntervalMs*.7+observed*.3;
        }
        previousState=lastState;
        lastState=incoming;
        lastMessageAt=now;
        connected=true;
        updateDom(lastState);
      }catch{
        connected=false;
        previousState=null;
        lastMessageAt=0;
        updateDom(lastState);
      }
    });

    socket.addEventListener("close",()=>{
      connected=false;
      previousState=null;
      lastMessageAt=0;
      updateDom(lastState);
      scheduleReconnect();
    });

    socket.addEventListener("error",()=>{
      connected=false;
      previousState=null;
      lastMessageAt=0;
      updateDom(lastState);
      try{socket.close();}catch{}
    });
  }

  els.pauseBtn.disabled=true;
  els.pauseBtn.textContent="SERVEUR";
  els.resetBtn.disabled=true;
  els.resetBtn.textContent="ADMIN";

  els.faultBtn.addEventListener("click",async()=>{
    try{
      const result=await postJson("./api/fault",{synapse_id:"RANDOM"});
      els.reportFault.textContent=result.fault||"RANDOM";
      setStatus(`PANNE SERVEUR injectée: ${result.fault||"RANDOM"} — propagation WebSocket en cours.`);
    }catch(error){
      setStatus(String(error.message||error),true);
    }
  });

  els.repairBtn.addEventListener("click",async()=>{
    try{
      const result=await postJson("./api/repair");
      const verdict=result?.report?.verdict||"—";
      setStatus(`RÉPARATION SERVEUR: ${verdict}. Validation H256 diffusée par WebSocket.`,verdict==="FAIL");
    }catch(error){
      setStatus(String(error.message||error),true);
    }
  });

  els.snapshotBtn.addEventListener("click",()=>{
    if(!lastState) return;
    const blob=new Blob([JSON.stringify({visual_state:lastState},null,2)],{type:"application/json"});
    const a=document.createElement("a");
    a.href=URL.createObjectURL(blob);
    a.download=`antmux-x72-server-visualstate-${lastState.tick_count}.json`;
    a.click();
    setTimeout(()=>URL.revokeObjectURL(a.href),1000);
  });

  window.addEventListener("resize",()=>{
    stars=[];
  });

  function animationLoop(now){
    draw(connected?visualStateForFrame(now):lastState);
    requestAnimationFrame(animationLoop);
  }

  connected=false;
  updateDom(lastState);
  draw(lastState);
  requestAnimationFrame(animationLoop);
  connect();
})();
