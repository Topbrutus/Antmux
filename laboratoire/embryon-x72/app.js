(() => {
  "use strict";

  const THEME = {
    bg:"#05070C", panel:"#0A0F18", panel2:"#0D1420", grid:"#172333",
    text:"#F2F5F8", muted:"#8795A8", gold:"#F6B94A", gold2:"#FFDF8A",
    cyan:"#39D8FF", blue:"#4B7CFF", magenta:"#E65BFF", violet:"#8B5CFF",
    green:"#5CFFB1", warning:"#FFB84C", error:"#FF557A", white:"#FFFFFF"
  };
  const CANON_SCHEMA = "ANTMUX-X72-CANON-v1";
  const CORE_SCHEMA = "ANTMUX-X72-QUEEN-CORE-v0.2";
  const PROTECTED_SCHEMA = "ANTMUX-X72-PROTECTED-STATE-v1";
  const BASE36_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  const EXPECTED_REFERENCE = "49e75d92d8fde33f402c3b60482bc5dcf13c12f09bd8c07c7937961d42ceaff9";

  const $ = id => document.getElementById(id);
  const els = {
    canvas:$("lifeClock"), mode:$("mode"), tick:$("tick"), dt:$("dt"), rexec:$("rexec"),
    frt:$("frt"), activity:$("activity"), memory:$("memory"), crystal:$("crystal"),
    repair:$("repair"), integrity:$("integrity"), events:$("events"), generation:$("generation"),
    eventBus:$("eventBus"), proofBox:$("proofBox"), status:$("status"),
    pauseBtn:$("pauseBtn"), faultBtn:$("faultBtn"), repairBtn:$("repairBtn"),
    resetBtn:$("resetBtn"), snapshotBtn:$("snapshotBtn"), referenceCheck:$("referenceCheck"),
    reportFault:$("reportFault"), reportSteps:$("reportSteps"), reportVerdict:$("reportVerdict")
  };
  const ctx = els.canvas.getContext("2d");

  function clamp(v,a=0,b=1){ return Math.max(a,Math.min(b,v)); }
  function avg(arr, key){ return arr.reduce((s,x)=>s+x[key],0)/arr.length; }

  function stableStringify(value){
    if (value === null || typeof value !== "object") return JSON.stringify(value);
    if (Array.isArray(value)) return "[" + value.map(stableStringify).join(",") + "]";
    const keys = Object.keys(value).sort();
    return "{" + keys.map(k => JSON.stringify(k)+":"+stableStringify(value[k])).join(",") + "}";
  }

  function canonicalBytes(obj){
    return new TextEncoder().encode(stableStringify({canon_schema:CANON_SCHEMA,payload:obj}));
  }

  async function sha256Hex(bytes){
    const digest = await crypto.subtle.digest("SHA-256", bytes);
    return [...new Uint8Array(digest)].map(b=>b.toString(16).padStart(2,"0")).join("");
  }

  function hexToBase36_50(hex){
    let n = BigInt("0x"+hex);
    if (n === 0n) return "0".padStart(50,"0");
    let out = "";
    while(n>0n){
      const r = Number(n % 36n);
      out = BASE36_ALPHABET[r] + out;
      n /= 36n;
    }
    return out.padStart(50,"0");
  }

  class EventBus {
    constructor(entityId){
      this.entityId = entityId;
      this.nextId = 1;
      this.events = [];
    }
    emit(tick,eventType,payload={}){
      this.events.push({event_id:this.nextId++,tick,event_type:eventType,entity_id:this.entityId,payload});
      this.events = this.events.slice(-512);
    }
    get count(){ return this.events.length; }
    recentLabels(n=10){
      return this.events.slice(-n).map(e=>{
        const keys = Object.keys(e.payload||{});
        return e.event_type + (keys.length ? ":"+String(e.payload[keys[0]]) : "");
      });
    }
  }

  class QueenCore {
    constructor(seed=72){
      this.seed = seed|0;
      this.entityId = `QUEEN-X72-${String(this.seed).padStart(4,"0")}`;
      this.queenEpoch = 0;
      this.generation = 0;
      this.mode = "SLEEP";
      this.tick = 0;
      this.simTime = 0;
      this.dtSim = 1/240;
      this.relations = [[0,1],[1,2],[2,3],[3,4],[4,5],[5,6],[6,0],[0,3],[2,5],[1,4]];
      const roles = ["INPUT","MEMORY","RELATION","CHOICE","TEMPORAL","REPAIR","AUDIT"];
      this.synapses = roles.map((role,i)=>({
        synapse_id:`S${i+1}`, role, integrity:1000, enabled:true, generation:0,
        activity:0.08+0.03*i, memory:0.07+0.02*i, crystal:0.04+0.015*i, repair_progress:0
      }));
      this.bus = new EventBus(this.entityId);
      this.bus.emit(this.tick,"SEED_LOADED",{seed:this.seed});
      this.bus.emit(this.tick,"QUEEN_BORN",{entity_id:this.entityId});
      this.protectedReference = structuredClone(this.protectedProjection());
      this.integrityMatch = true;
      this.lastRepairReport = {
        verdict:"INVALID", reason:"Aucune réparation exécutée.", changed_synapses:[],
        before_protected_h256:"", after_protected_h256:"", reference_protected_h256:"",
        whole_state_h256:""
      };
    }
    protectedProjection(){
      return {
        schema:PROTECTED_SCHEMA,
        entity_id:this.entityId,
        queen_epoch:this.queenEpoch,
        relations:this.relations.map(x=>[...x]),
        synapses:this.synapses.map(s=>({
          synapse_id:s.synapse_id, role:s.role, integrity:s.integrity,
          enabled:s.enabled, generation:s.generation
        }))
      };
    }
    protectedEqualsReference(){
      return stableStringify(this.protectedProjection()) === stableStringify(this.protectedReference);
    }
    wholeStateProjection(){
      return {
        schema:CORE_SCHEMA, seed:this.seed, entity_id:this.entityId, queen_epoch:this.queenEpoch,
        generation:this.generation, mode:this.mode, tick:this.tick,
        sim_time_us:Math.round(this.simTime*1_000_000),
        relations:this.relations.map(x=>[...x]),
        synapses:this.synapses.map(s=>({
          synapse_id:s.synapse_id, role:s.role, integrity:s.integrity, enabled:s.enabled,
          generation:s.generation, activity_u:Math.round(s.activity*1_000_000),
          memory_u:Math.round(s.memory*1_000_000), crystal_u:Math.round(s.crystal*1_000_000),
          repair_u:Math.round(s.repair_progress*1_000_000)
        }))
      };
    }
    modeForTick(){
      if (!this.protectedEqualsReference()) {
        return this.synapses.some(s=>s.repair_progress>0) ? "AUTO_REPAIR" : "FAULT";
      }
      const phase = this.tick % 1800;
      if (phase < 260) return "SLEEP";
      if (phase < 420) return "EVENT";
      if (phase < 760) return "BURST";
      return "STABLE";
    }
    step(){
      this.tick += 1;
      this.simTime += this.dtSim;
      this.mode = this.modeForTick();
      const gain = {SLEEP:.16,EVENT:.56,BURST:.88,STABLE:.38,FAULT:.22,AUTO_REPAIR:.70}[this.mode];
      this.synapses.forEach((s,i)=>{
        const p = this.simTime*(1.5+i*.11)+i*.9;
        const oscillation = .5+.5*Math.sin(p);
        let target = gain*(.55+.45*oscillation);
        if (!s.enabled || s.integrity<=0) target=0;
        s.activity += (target-s.activity)*.055;
        s.activity = clamp(s.activity);
        if (s.enabled && s.activity>.48) s.memory += .00020*s.activity;
        s.memory -= .000015*Math.max(0,s.memory-.08);
        s.memory = clamp(s.memory,0,.92);
        if (s.memory>.18) s.crystal += .000075*s.memory;
        s.crystal -= .000005*Math.max(0,s.crystal-.05);
        s.crystal = clamp(s.crystal,0,.90);
      });
      if (this.tick%360===0) this.bus.emit(this.tick,"MODE",{mode:this.mode});
      if (this.tick%7200===0){
        this.generation += 1;
        this.bus.emit(this.tick,"GENERATION_ADVANCED",{generation:this.generation});
      }
    }
    injectFault(sid=null){
      if (!this.protectedEqualsReference()) throw new Error("Une panne protégée existe déjà.");
      let idx;
      if (sid){
        idx = this.synapses.findIndex(s=>s.synapse_id===sid);
        if (idx<0) throw new Error("Synapse inconnue: "+sid);
      } else {
        idx = (Math.floor(this.tick/17)+3)%this.synapses.length;
      }
      const s = this.synapses[idx];
      s.enabled=false; s.integrity=0; s.repair_progress=0;
      this.mode="FAULT";
      this.integrityMatch=false;
      this.bus.emit(this.tick,"FAULT_DETECTED",{synapse_id:s.synapse_id});
      return s.synapse_id;
    }
    reset(){
      return new QueenCore(this.seed);
    }
  }

  class RepairEngine {
    constructor(core){
      this.core=core; this.active=false; this.progress=0; this.targets=[];
    }
    diagnose(){
      const ref = Object.fromEntries(this.core.protectedReference.synapses.map(x=>[x.synapse_id,x]));
      return this.core.synapses.filter(s=>{
        const r=ref[s.synapse_id];
        return !r || s.role!==r.role || s.integrity!==r.integrity || s.enabled!==r.enabled || s.generation!==r.generation;
      }).map(s=>s.synapse_id);
    }
    begin(){
      if (this.core.protectedEqualsReference()){
        const r={verdict:"INVALID",reason:"Aucune divergence protégée à réparer.",changed_synapses:[]};
        this.core.lastRepairReport={...this.core.lastRepairReport,...r};
        this.core.bus.emit(this.core.tick,"REPAIR_INVALID",{reason:r.reason});
        return r;
      }
      this.targets=this.diagnose();
      if (!this.targets.length){
        const r={verdict:"FAIL",reason:"Hash protégé divergent mais aucune synapse réparable identifiée.",changed_synapses:[]};
        this.core.lastRepairReport={...this.core.lastRepairReport,...r};
        this.core.bus.emit(this.core.tick,"REPAIR_FAILED",{reason:r.reason});
        return r;
      }
      this.active=true; this.progress=0; this.core.mode="AUTO_REPAIR";
      this.core.bus.emit(this.core.tick,"REPAIR_STARTED",{targets:this.targets.join(",")});
      this.core.synapses.forEach(s=>{ if(this.targets.includes(s.synapse_id)) s.repair_progress=.001; });
      return {verdict:"INVALID",reason:"Réparation en cours.",changed_synapses:[...this.targets]};
    }
    step(){
      if(!this.active) return null;
      this.progress=Math.min(1,this.progress+.0075);
      this.core.synapses.forEach(s=>{ if(this.targets.includes(s.synapse_id)) s.repair_progress=this.progress; });
      if(this.progress<1) return null;
      const ref=Object.fromEntries(this.core.protectedReference.synapses.map(x=>[x.synapse_id,x]));
      const changed=[];
      this.core.synapses.forEach(s=>{
        if(!this.targets.includes(s.synapse_id)) return;
        const r=ref[s.synapse_id];
        s.role=r.role; s.integrity=r.integrity; s.enabled=r.enabled; s.generation=r.generation; s.repair_progress=0;
        changed.push(s.synapse_id);
      });
      this.active=false; this.progress=0;
      const pass=this.core.protectedEqualsReference();
      const verdict=pass?"PASS":"FAIL";
      const reason=pass ? "Hash protégé restauré exactement sur la référence autorisée." : "Le hash protégé ne ferme pas sur la référence après restauration.";
      this.core.mode=pass?"STABLE":"FAULT";
      this.core.integrityMatch=pass;
      this.core.bus.emit(this.core.tick,pass?"REPAIR_COMPLETED":"REPAIR_FAILED",{verdict,targets:changed.join(",")});
      this.core.bus.emit(this.core.tick,"STATE_CANONICALIZED",{});
      this.core.bus.emit(this.core.tick,"STATE_HASHED",{});
      const report={verdict,reason,changed_synapses:changed};
      this.core.lastRepairReport={...this.core.lastRepairReport,...report};
      this.targets=[];
      return report;
    }
  }

  let core = new QueenCore(72);
  let repair = new RepairEngine(core);
  let running = true;
  let accumulator = 0;
  let lastFrame = performance.now();
  let windowStart = lastFrame;
  let windowTicks = 0;
  let rExec = 0;
  let fRt = 0;
  let phase = 0;
  let stars = [];
  let hashCache = {whole:"calcul…",b36:"calcul…",protected:"calcul…",reference:"calcul…"};
  let hashBusy=false;
  let hashFrame=0;

  function resizeCanvas(){
    const dpr=Math.max(1,Math.min(2,window.devicePixelRatio||1));
    const rect=els.canvas.getBoundingClientRect();
    const w=Math.max(320,Math.floor(rect.width));
    const h=Math.max(320,Math.floor(rect.height));
    if(els.canvas.width!==Math.floor(w*dpr)||els.canvas.height!==Math.floor(h*dpr)){
      els.canvas.width=Math.floor(w*dpr); els.canvas.height=Math.floor(h*dpr);
      ctx.setTransform(dpr,0,0,dpr,0,0);
      els.canvas._cssW=w; els.canvas._cssH=h;
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
      const x=cx+Math.cos(a)*rr, y=cy+Math.sin(a)*rr;
      if(i===0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
    }
    ctx.closePath(); ctx.strokeStyle=color; ctx.lineWidth=width; ctx.stroke();
  }

  function drawMeter(cx,cy,radius,value,color){
    ctx.beginPath(); ctx.arc(cx,cy,radius,0,Math.PI*2); ctx.strokeStyle=THEME.grid; ctx.lineWidth=2; ctx.stroke();
    ctx.beginPath(); ctx.arc(cx,cy,radius,-Math.PI/2,-Math.PI/2+Math.PI*2*clamp(value)); ctx.strokeStyle=color; ctx.lineWidth=5; ctx.stroke();
  }

  function draw(){
    resizeCanvas();
    const w=els.canvas._cssW,h=els.canvas._cssH;
    ctx.clearRect(0,0,w,h); ctx.fillStyle=THEME.bg; ctx.fillRect(0,0,w,h);
    const cx=w*.5, cy=h*.5, r=Math.min(w,h)*.34;

    ctx.strokeStyle=THEME.grid; ctx.lineWidth=1;
    for(let x=0;x<=w+40;x+=40){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,h);ctx.stroke();}
    for(let y=0;y<=h+40;y+=40){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke();}

    if(!stars.length){
      const rnd=seededRandom((Math.floor(w)*100003+Math.floor(h))>>>0);
      const count=Math.max(40,Math.floor(w*h/18000));
      stars=Array.from({length:count},()=>[rnd()*w,rnd()*h,rnd()<.8?1:2]);
    }
    ctx.fillStyle=THEME.muted;
    stars.forEach(([x,y,rr])=>{ctx.beginPath();ctx.arc(x,y,rr,0,Math.PI*2);ctx.fill();});

    core.relations.forEach(([a,b])=>{
      const [x1,y1]=nodePos(a,cx,cy,r), [x2,y2]=nodePos(b,cx,cy,r);
      const intensity=(core.synapses[a].activity+core.synapses[b].activity)/2;
      let color=intensity>.45?THEME.cyan:THEME.blue;
      if(!(core.synapses[a].enabled&&core.synapses[b].enabled)) color=THEME.error;
      ctx.strokeStyle=color; ctx.lineWidth=1+3*intensity;
      ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke();
      if(intensity>.25&&core.synapses[a].enabled&&core.synapses[b].enabled){
        const q=((core.tick*.011)+a*.19+b*.07)%1;
        const px=x1+(x2-x1)*q, py=y1+(y2-y1)*q, pr=2+3*intensity;
        ctx.fillStyle=THEME.gold2;ctx.beginPath();ctx.arc(px,py,pr,0,Math.PI*2);ctx.fill();
      }
    });

    const activity=avg(core.synapses,"activity"), memory=avg(core.synapses,"memory"), crystal=avg(core.synapses,"crystal");
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
      ctx.closePath();ctx.strokeStyle=i%3?THEME.gold2:THEME.cyan;ctx.lineWidth=1;ctx.stroke();
    }

    core.synapses.forEach((syn,i)=>{
      const [x,y]=nodePos(i,cx,cy,r);
      const pulse=1+.18*Math.sin(phase*8+i), rr=(12+16*syn.activity)*pulse;
      let color=!syn.enabled||syn.integrity<=0?THEME.error:(syn.repair_progress>0?THEME.warning:(syn.crystal>.20?THEME.gold2:THEME.cyan));
      ctx.strokeStyle=THEME.grid;ctx.lineWidth=2;ctx.beginPath();ctx.arc(x,y,rr*1.7,0,Math.PI*2);ctx.stroke();
      ctx.fillStyle=THEME.panel2;ctx.strokeStyle=color;ctx.lineWidth=3;ctx.beginPath();ctx.arc(x,y,rr,0,Math.PI*2);ctx.fill();ctx.stroke();
      const inn=Math.max(3,rr*syn.activity*.65);ctx.fillStyle=color;ctx.beginPath();ctx.arc(x,y,inn,0,Math.PI*2);ctx.fill();
      ctx.fillStyle=THEME.text;ctx.font="bold 11px Consolas";ctx.textAlign="center";
      ctx.fillText(`${syn.synapse_id}  A:${syn.activity.toFixed(2)}  I:${(syn.integrity/1000).toFixed(2)}`,x,y+rr+15);
    });

    const modeColor={SLEEP:THEME.blue,EVENT:THEME.gold,BURST:THEME.magenta,STABLE:THEME.green,FAULT:THEME.error,AUTO_REPAIR:THEME.warning}[core.mode]||THEME.white;
    const coreR=r*(.17+.035*Math.sin(phase*4));
    ctx.strokeStyle=THEME.grid;ctx.lineWidth=3;ctx.beginPath();ctx.arc(cx,cy,coreR*1.5,0,Math.PI*2);ctx.stroke();
    ctx.fillStyle=THEME.panel;ctx.strokeStyle=modeColor;ctx.lineWidth=4;ctx.beginPath();ctx.arc(cx,cy,coreR,0,Math.PI*2);ctx.fill();ctx.stroke();
    ctx.fillStyle=THEME.gold2;ctx.font=`bold ${Math.max(28,Math.floor(coreR*.72))}px Georgia`;ctx.textAlign="center";ctx.fillText("∞",cx,cy-4);
    ctx.fillStyle=modeColor;ctx.font="bold 12px Consolas";ctx.fillText(core.mode,cx,cy+coreR*.55);

    ctx.fillStyle=THEME.gold2;ctx.font="bold 18px Georgia";ctx.fillText("HORLOGE DE LA VIE — REINE",cx,cy-r*1.23);
    ctx.fillStyle=THEME.text;ctx.font="bold 12px Consolas";ctx.fillText(`TICK ${core.tick.toLocaleString("fr-CA")}  •  GEN ${core.generation}  •  SYNAPSES ${core.synapses.filter(s=>s.enabled).length}/7  •  REPAIR ${core.lastRepairReport.verdict}`,cx,cy+r*1.24);
    ctx.textAlign="left";ctx.fillStyle=core.protectedEqualsReference()?THEME.green:THEME.error;ctx.font="bold 10px Consolas";
    ctx.fillText(`WHOLE H256 ${hashCache.whole.slice(0,18)}…   PROTECTED ${core.protectedEqualsReference()?"MATCH":"MISMATCH"}`,16,h-14);
  }

  async function refreshHashes(){
    if(hashBusy) return;
    hashBusy=true;
    try{
      const protectedHex=await sha256Hex(canonicalBytes(core.protectedProjection()));
      const referenceHex=await sha256Hex(canonicalBytes(core.protectedReference));
      const wholeHex=await sha256Hex(canonicalBytes(core.wholeStateProjection()));
      hashCache={protected:protectedHex,reference:referenceHex,whole:wholeHex,b36:hexToBase36_50(wholeHex)};
      core.integrityMatch=protectedHex===referenceHex;
      core.lastRepairReport.reference_protected_h256=referenceHex;
      core.lastRepairReport.after_protected_h256=protectedHex;
      core.lastRepairReport.whole_state_h256=wholeHex;
      els.referenceCheck.textContent=`RÉFÉRENCE H256 : ${referenceHex===EXPECTED_REFERENCE?"MATCH V0.2":"MISMATCH"}`;
      els.referenceCheck.className=referenceHex===EXPECTED_REFERENCE?"ok":"bad";
    }catch(e){
      els.referenceCheck.textContent="RÉFÉRENCE H256 : erreur de calcul";
      els.referenceCheck.className="bad";
    }finally{ hashBusy=false; }
  }

  function refreshPanels(){
    const activity=avg(core.synapses,"activity"),memory=avg(core.synapses,"memory"),crystal=avg(core.synapses,"crystal");
    els.mode.textContent=core.mode;
    els.tick.textContent=core.tick.toLocaleString("fr-CA");
    els.dt.textContent=core.dtSim.toFixed(6)+"s";
    els.rexec.textContent=rExec.toFixed(1)+"/s";
    els.frt.textContent=fRt.toFixed(3)+"×";
    els.activity.textContent=activity.toFixed(3);
    els.memory.textContent=memory.toFixed(3);
    els.crystal.textContent=crystal.toFixed(3);
    els.repair.textContent=repair.progress.toFixed(3);
    const match=core.protectedEqualsReference();
    els.integrity.textContent=match?"MATCH":"MISMATCH";
    els.integrity.className=match?"ok":"bad";
    els.events.textContent=core.bus.count.toLocaleString("fr-CA");
    els.generation.textContent=String(core.generation);

    els.eventBus.replaceChildren(...core.bus.events.slice(-12).reverse().map(e=>{
      const div=document.createElement("div");
      const payload=Object.keys(e.payload||{}).length?" · "+JSON.stringify(e.payload):"";
      div.textContent=`• [${e.tick}] ${e.event_type}${payload}`;
      return div;
    }));

    let proof="ID  ROLE      ACT   MEM   CRYS  INTEG  STATE\n";
    proof+="────────────────────────────────────────────────\n";
    core.synapses.forEach(s=>{
      proof += `${s.synapse_id.padEnd(3)} ${s.role.padEnd(9)} ${s.activity.toFixed(3)} ${s.memory.toFixed(3)} ${s.crystal.toFixed(3)} ${String(s.integrity).padStart(4)}  ${s.enabled?"ON":"FAULT"}\n`;
    });
    proof += `\nWHOLE H256\n${hashCache.whole}\n\nB36_50\n${hashCache.b36}\n\nPROTECTED CURRENT\n${hashCache.protected}\n\nPROTECTED REFERENCE\n${hashCache.reference}\n\nVERDICT: ${core.lastRepairReport.verdict}\n${core.lastRepairReport.reason}\n`;
    els.proofBox.textContent=proof;
  }

  function tickFrame(now){
    const elapsed=Math.min(.1,Math.max(0,(now-lastFrame)/1000));
    lastFrame=now;
    if(running){
      accumulator+=elapsed;
      let steps=0;
      while(accumulator>=core.dtSim && steps<64){
        core.step();
        const report=repair.step();
        if(report) els.status.textContent=`${report.verdict}: ${report.reason}`;
        accumulator-=core.dtSim;
        steps++;windowTicks++;
      }
    }
    const win=(now-windowStart)/1000;
    if(win>=.5){
      rExec=windowTicks/win;
      fRt=(windowTicks*core.dtSim)/win;
      windowTicks=0;windowStart=now;
    }
    phase += .012+.045*avg(core.synapses,"activity");
    draw();refreshPanels();
    hashFrame++;
    if(hashFrame%30===0) refreshHashes();
    requestAnimationFrame(tickFrame);
  }

  els.pauseBtn.addEventListener("click",()=>{
    running=!running;els.pauseBtn.textContent=running?"PAUSE":"REPRENDRE";
  });
  els.faultBtn.addEventListener("click",()=>{
    try{
      const sid=core.injectFault();
      els.status.textContent=`PANNE injectée dans ${sid}. Le hash protégé diverge maintenant de la référence.`;
      refreshHashes();
    }catch(e){els.status.textContent="Injection refusée : "+e.message;}
  });
  els.repairBtn.addEventListener("click",()=>{
    const report=repair.begin();
    els.status.textContent=repair.active?"Réparation réelle démarrée : restauration depuis référence autorisée + fermeture H256.":`${report.verdict}: ${report.reason}`;
  });
  els.resetBtn.addEventListener("click",()=>{
    core=new QueenCore(72);repair=new RepairEngine(core);accumulator=0;phase=0;
    els.status.textContent="CORE réinitialisé depuis la graine déterministe.";
    refreshHashes();
  });
  els.snapshotBtn.addEventListener("click",async()=>{
    await refreshHashes();
    const payload={
      visual_state:{
        source:"QUEEN_CORE_V0.2_WEB_PORT",tick_count:core.tick,sim_time:core.simTime,dt_sim:core.dtSim,
        r_exec:rExec,f_rt:fRt,event_count:core.bus.count,queen_mode:core.mode,generation:core.generation,
        active_synapses:core.synapses.filter(s=>s.enabled).length,repair_level:repair.progress,
        crystallization_level:avg(core.synapses,"crystal"),memory_level:avg(core.synapses,"memory"),
        error_level:core.protectedEqualsReference()?0:1,activity_level:avg(core.synapses,"activity"),
        whole_h256:hashCache.whole,b36_view:hashCache.b36,protected_h256:hashCache.protected,
        reference_h256:hashCache.reference,integrity_match:core.protectedEqualsReference(),
        repair_verdict:core.lastRepairReport.verdict,repair_reason:core.lastRepairReport.reason,
        synapses:core.synapses,relations:core.relations,recent_events:core.bus.recentLabels(10)
      },
      protected_projection:core.protectedProjection(),
      reference_protected_h256:hashCache.reference,
      events:core.bus.events,
      last_repair_report:core.lastRepairReport
    };
    const blob=new Blob([JSON.stringify(payload,null,2)],{type:"application/json"});
    const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download=`antmux_core_tick_${core.tick}.json`;a.click();
    setTimeout(()=>URL.revokeObjectURL(a.href),1000);
    core.bus.emit(core.tick,"SNAPSHOT_SAVED",{path:a.download});
    els.status.textContent="Snapshot JSON généré.";
  });

  async function loadReport(){
    try{
      const r=await fetch("./core/ANTMUX_X72_CORE_V02_TEST_REPORT.json",{cache:"no-store"});
      if(!r.ok) throw new Error();
      const data=await r.json();
      els.reportFault.textContent=data.synapse_fault||"—";
      els.reportSteps.textContent=String(data.repair_steps??"—");
      els.reportVerdict.textContent=data.verdict||"—";
      els.reportVerdict.className=data.verdict==="PASS"?"ok":"bad";
    }catch{ els.reportVerdict.textContent="INDISPONIBLE";els.reportVerdict.className="bad"; }
  }

  window.addEventListener("resize",()=>{stars=[];});
  loadReport();
  refreshHashes();
  requestAnimationFrame(tickFrame);
})();
