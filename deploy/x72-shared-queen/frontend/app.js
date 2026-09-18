(() => {
  "use strict";

  const THEME = {
    bg:"#05070C", panel:"#0A0F18", grid:"#172333", text:"#F2F5F8", muted:"#8795A8",
    gold:"#F6B94A", gold2:"#FFDF8A", cyan:"#39D8FF", blue:"#4B7CFF", magenta:"#E65BFF",
    violet:"#8B5CFF", green:"#5CFFB1", warning:"#FFB84C", error:"#FF557A", white:"#FFFFFF"
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
    runtimeBadge:$("runtimeBadge")
  };
  const ctx = els.canvas.getContext("2d");
  let lastState = null;
  let connected = false;
  let socket = null;

  function api(path){ return new URL(path, window.location.href).toString(); }
  function wsUrl(){
    const url = new URL("./ws", window.location.href);
    url.protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return url.toString();
  }
  function clamp(v,a=0,b=1){ return Math.max(a, Math.min(b, v)); }
  function fmt(v,n=3){ return Number(v || 0).toFixed(n); }

  async function postJson(path, body){
    const response = await fetch(api(path), {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body: body ? JSON.stringify(body) : "{}"
    });
    const json = await response.json().catch(()=>({detail:"Réponse non JSON"}));
    if(!response.ok) throw new Error(json.detail || `HTTP ${response.status}`);
    return json;
  }

  function updateDom(state){
    if(!state) return;
    els.mode.textContent = state.queen_mode;
    els.tick.textContent = state.tick_count;
    els.dt.textContent = `${fmt(state.dt_sim,6)}s`;
    els.rexec.textContent = `${fmt(state.r_exec,1)}/s`;
    els.frt.textContent = `${fmt(state.f_rt,3)}×`;
    els.activity.textContent = fmt(state.activity_level);
    els.memory.textContent = fmt(state.memory_level);
    els.crystal.textContent = fmt(state.crystallization_level);
    els.repair.textContent = fmt(state.repair_level);
    els.integrity.textContent = state.integrity_match ? "MATCH" : "MISMATCH";
    els.integrity.className = state.integrity_match ? "ok" : "bad";
    els.events.textContent = state.event_count;
    els.generation.textContent = state.generation;
    els.eventBus.innerHTML = (state.recent_events || []).slice().reverse().map(label => `<p>${label}</p>`).join("");
    els.proofBox.textContent = [
      `SOURCE: ${state.source}`,
      `ENTITY: ${state.entity_id}`,
      `WHOLE_H256: ${state.whole_h256}`,
      `BASE36_50: ${state.b36_view}`,
      `PROTECTED_H256: ${state.protected_h256}`,
      `REFERENCE_H256: ${state.reference_h256}`,
      `REPAIR: ${state.repair_verdict} — ${state.repair_reason}`
    ].join("\n");
    els.referenceCheck.textContent = `RÉFÉRENCE H256 : ${state.integrity_match ? "MATCH" : "MISMATCH"}`;
    els.status.textContent = connected ? "QUEEN SERVER CONNECTED — état partagé serveur." : "CORE DISCONNECTED";
    els.status.className = connected ? "status" : "status bad";
    els.reportVerdict.textContent = state.repair_verdict || "INVALID";
    els.runtimeBadge.textContent = connected ? "QUEEN SERVER V0.2 — SHARED" : "CORE DISCONNECTED";
  }

  function drawGear(cx, cy, radius, teeth, phase, color){
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(phase);
    ctx.beginPath();
    for(let i=0; i<teeth*2; i++){
      const r = i % 2 ? radius * 0.86 : radius;
      const a = i * Math.PI / teeth;
      ctx.lineTo(Math.cos(a)*r, Math.sin(a)*r);
    }
    ctx.closePath();
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(0,0,radius*0.28,0,Math.PI*2);
    ctx.stroke();
    ctx.restore();
  }

  function draw(state){
    const dpr = window.devicePixelRatio || 1;
    const rect = els.canvas.getBoundingClientRect();
    els.canvas.width = Math.max(1, Math.floor(rect.width*dpr));
    els.canvas.height = Math.max(1, Math.floor(rect.height*dpr));
    ctx.setTransform(dpr,0,0,dpr,0,0);
    const w = rect.width;
    const h = rect.height;
    ctx.clearRect(0,0,w,h);
    ctx.fillStyle = THEME.bg;
    ctx.fillRect(0,0,w,h);
    const cx = w/2, cy = h/2;
    const size = Math.min(w,h);
    const tick = state ? state.tick_count : 0;

    ctx.strokeStyle = THEME.grid;
    ctx.lineWidth = 1;
    for(let r=0.16; r<=0.48; r+=0.08){
      ctx.beginPath();
      ctx.arc(cx,cy,size*r,0,Math.PI*2);
      ctx.stroke();
    }

    const synapses = state ? state.synapses : [];
    const points = synapses.map((s,i)=>{
      const a = -Math.PI/2 + i * Math.PI*2 / 7;
      const r = size*0.34;
      return {x:cx+Math.cos(a)*r, y:cy+Math.sin(a)*r, s};
    });
    ctx.strokeStyle = state && state.integrity_match ? "rgba(57,216,255,.45)" : "rgba(255,85,122,.55)";
    ctx.lineWidth = 2;
    (state ? state.relations : []).forEach(([a,b])=>{
      const p = points[a], q = points[b];
      if(!p || !q) return;
      ctx.beginPath();
      ctx.moveTo(p.x,p.y);
      ctx.lineTo(q.x,q.y);
      ctx.stroke();
    });

    points.forEach(({x,y,s})=>{
      const active = !!s.enabled;
      ctx.beginPath();
      ctx.arc(x,y,12 + 10*clamp(s.activity),0,Math.PI*2);
      ctx.fillStyle = active ? THEME.cyan : THEME.error;
      ctx.globalAlpha = active ? 0.82 : 0.92;
      ctx.fill();
      ctx.globalAlpha = 1;
      ctx.strokeStyle = THEME.gold;
      ctx.stroke();
      ctx.fillStyle = THEME.text;
      ctx.font = "12px system-ui";
      ctx.textAlign = "center";
      ctx.fillText(s.synapse_id, x, y+4);
    });

    drawGear(cx, cy, size*0.12, 36, tick*0.01, THEME.gold);
    drawGear(cx-size*0.2, cy+size*0.2, size*0.08, 28, -tick*0.014, THEME.violet);
    drawGear(cx+size*0.22, cy-size*0.18, size*0.06, 20, tick*0.018, THEME.green);

    const rings = [
      [state?.activity_level || 0, THEME.cyan, size*0.43],
      [state?.memory_level || 0, THEME.magenta, size*0.46],
      [state?.crystallization_level || 0, THEME.green, size*0.49]
    ];
    rings.forEach(([value,color,r])=>{
      ctx.beginPath();
      ctx.arc(cx,cy,r,-Math.PI/2,-Math.PI/2+Math.PI*2*clamp(value));
      ctx.strokeStyle = color;
      ctx.lineWidth = 5;
      ctx.stroke();
    });

    if(!connected){
      ctx.fillStyle = "rgba(5,7,12,.72)";
      ctx.fillRect(0,0,w,h);
      ctx.fillStyle = THEME.error;
      ctx.font = "700 24px system-ui";
      ctx.textAlign = "center";
      ctx.fillText("CORE DISCONNECTED", cx, cy);
    }
  }

  function connect(){
    socket = new WebSocket(wsUrl());
    socket.addEventListener("open", ()=>{ connected = true; });
    socket.addEventListener("message", event=>{
      lastState = JSON.parse(event.data);
      connected = true;
      updateDom(lastState);
      draw(lastState);
    });
    socket.addEventListener("close", ()=>{
      connected = false;
      updateDom(lastState);
      draw(lastState);
      setTimeout(connect, 1500);
    });
    socket.addEventListener("error", ()=>{
      connected = false;
      updateDom(lastState);
      draw(lastState);
      try { socket.close(); } catch {}
    });
  }

  els.pauseBtn.disabled = true;
  els.pauseBtn.textContent = "SERVEUR";
  els.resetBtn.disabled = true;
  els.resetBtn.textContent = "ADMIN";
  els.faultBtn.addEventListener("click", async ()=>{
    try { await postJson("./api/fault", {synapse_id:"RANDOM"}); }
    catch(error){ els.status.textContent = String(error.message || error); }
  });
  els.repairBtn.addEventListener("click", async ()=>{
    try { await postJson("./api/repair"); }
    catch(error){ els.status.textContent = String(error.message || error); }
  });
  els.snapshotBtn.addEventListener("click", ()=>{
    if(!lastState) return;
    const blob = new Blob([JSON.stringify(lastState,null,2)], {type:"application/json"});
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `antmux-x72-shared-${lastState.tick_count}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  });
  window.addEventListener("resize", ()=>draw(lastState));
  connect();
})();

