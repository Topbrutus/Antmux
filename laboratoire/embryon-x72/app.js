(() => {
  "use strict";

  const LIVE_PATH = "./live/public-read-only.json";
  const SYNAPSE_COUNT = 7;
  const CX = 320;
  const CY = 320;
  const RADIUS = 215;

  const els = {
    sourceBadge: document.getElementById("sourceBadge"),
    connectionBadge: document.getElementById("connectionBadge"),
    queenMode: document.getElementById("queenMode"),
    eventCount: document.getElementById("eventCount"),
    eventLog: document.getElementById("eventLog"),
    relationLayer: document.getElementById("relationLayer"),
    synapseLayer: document.getElementById("synapseLayer"),
    pulseLayer: document.getElementById("pulseLayer"),
    phasePetals: document.getElementById("phasePetals"),
    hashValue: document.getElementById("hashValue"),
    b36Value: document.getElementById("b36Value"),
    mDt: document.getElementById("mDt"),
    mExec: document.getElementById("mExec"),
    mFps: document.getElementById("mFps"),
    mTick: document.getElementById("mTick"),
    mGen: document.getElementById("mGen"),
    mActive: document.getElementById("mActive"),
    gActivity: document.getElementById("gActivity"),
    gMemory: document.getElementById("gMemory"),
    gCrystal: document.getElementById("gCrystal"),
    gRepair: document.getElementById("gRepair"),
    gError: document.getElementById("gError"),
    vActivity: document.getElementById("vActivity"),
    vMemory: document.getElementById("vMemory"),
    vCrystal: document.getElementById("vCrystal"),
    vRepair: document.getElementById("vRepair"),
    vError: document.getElementById("vError"),
    faultBtn: document.getElementById("faultBtn"),
    repairBtn: document.getElementById("repairBtn"),
    pauseBtn: document.getElementById("pauseBtn"),
    resetBtn: document.getElementById("resetBtn")
  };

  const points = Array.from({ length: SYNAPSE_COUNT }, (_, i) => {
    const angle = (-90 + i * (360 / SYNAPSE_COUNT)) * Math.PI / 180;
    return {
      x: CX + Math.cos(angle) * RADIUS,
      y: CY + Math.sin(angle) * RADIUS
    };
  });

  const baseSynapses = () => Array.from({ length: SYNAPSE_COUNT }, (_, i) => ({
    id: `S${i + 1}`,
    active: true,
    activity: 0.28 + i * 0.035,
    memory: 0.36 + (i % 3) * 0.07,
    crystal: 0.20 + (i % 4) * 0.045,
    repair: 0
  }));

  let state = {
    source: "DEMO",
    mode: "STABLE",
    dtSim: 1 / 60,
    rExec: 1,
    fRt: 60,
    tick: 0,
    generation: 0,
    eventCount: 0,
    activity: 0.35,
    memory: 0.46,
    crystal: 0.28,
    repair: 0,
    error: 0,
    synapses: baseSynapses()
  };

  let paused = false;
  let repairing = false;
  let faultIndex = null;
  let phase = 0;
  let lastHashTick = -1;
  let liveConnected = false;
  let rafId = 0;
  let timerId = 0;
  let liveTimerId = 0;

  function svg(tag, attrs = {}) {
    const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, String(value)));
    return node;
  }

  function buildClock() {
    els.relationLayer.replaceChildren();
    els.synapseLayer.replaceChildren();
    els.phasePetals.replaceChildren();

    for (let i = 0; i < SYNAPSE_COUNT; i += 1) {
      const a = points[i];
      const b = points[(i + 1) % SYNAPSE_COUNT];

      els.relationLayer.appendChild(svg("line", {
        id: `ring-link-${i}`,
        x1: a.x, y1: a.y, x2: b.x, y2: b.y
      }));

      els.relationLayer.appendChild(svg("line", {
        id: `core-link-${i}`,
        x1: CX, y1: CY, x2: a.x, y2: a.y
      }));

      const midAngle = (-90 + i * (360 / SYNAPSE_COUNT) + 180 / SYNAPSE_COUNT) * Math.PI / 180;
      const px = CX + Math.cos(midAngle) * 165;
      const py = CY + Math.sin(midAngle) * 165;
      const path = svg("path", {
        d: `M ${CX} ${CY} Q ${px} ${py} ${a.x} ${a.y}`
      });
      els.phasePetals.appendChild(path);

      const group = svg("g", {
        id: `synapse-${i}`,
        class: "synapse",
        transform: `translate(${a.x} ${a.y})`
      });
      group.appendChild(svg("circle", { cx: 0, cy: 0, r: 32 }));

      const label = svg("text", { x: 0, y: -2, "text-anchor": "middle" });
      label.textContent = `S${i + 1}`;
      group.appendChild(label);

      const value = svg("text", { x: 0, y: 15, "text-anchor": "middle", class: "value" });
      value.textContent = "0.00";
      group.appendChild(value);

      els.synapseLayer.appendChild(group);
    }
  }

  function addEvent(type, detail = "") {
    state.eventCount += 1;
    const item = document.createElement("li");
    const time = new Date().toLocaleTimeString("fr-CA", { hour12: false });
    const strong = document.createElement("strong");
    strong.textContent = type;
    item.append(time + " · ", strong);
    if (detail) item.append(" · " + detail);
    els.eventLog.prepend(item);
    while (els.eventLog.children.length > 40) {
      els.eventLog.removeChild(els.eventLog.lastChild);
    }
    els.eventCount.textContent = String(state.eventCount);
  }

  function clamp01(value) {
    return Math.max(0, Math.min(1, Number(value) || 0));
  }

  function updateDemoState() {
    if (paused || liveConnected) return;

    state.tick += 1;
    phase += 0.065;

    const wave = (Math.sin(phase) + 1) / 2;
    state.activity = 0.28 + wave * 0.24;
    state.memory = clamp01(state.memory + 0.00055);
    state.crystal = clamp01(state.crystal + 0.00032);

    state.synapses.forEach((syn, i) => {
      const localWave = (Math.sin(phase + i * 0.9) + 1) / 2;
      if (syn.active) {
        syn.activity = 0.18 + localWave * 0.58;
        syn.memory = clamp01(syn.memory + 0.00035);
        syn.crystal = clamp01(syn.crystal + 0.0002);
      } else {
        syn.activity = 0;
      }
    });

    if (repairing && faultIndex !== null) {
      state.mode = "AUTO_REPAIR";
      state.repair = clamp01(state.repair + 0.035);
      state.error = clamp01(1 - state.repair);
      state.synapses[faultIndex].repair = state.repair;

      if (state.repair >= 1) {
        state.synapses[faultIndex].active = true;
        state.synapses[faultIndex].repair = 0;
        addEvent("REPAIR_COMPLETED", state.synapses[faultIndex].id);
        addEvent("STATE_STABILIZED", "7/7 synapses actives");
        faultIndex = null;
        repairing = false;
        state.mode = "STABLE";
        state.repair = 0;
        state.error = 0;
      }
    }

    render();
  }

  function render() {
    const activeCount = state.synapses.filter(s => s.active).length;

    els.queenMode.textContent = state.mode;
    els.mDt.textContent = `${Number(state.dtSim).toFixed(4)} s`;
    els.mExec.textContent = `${Number(state.rExec).toFixed(2)}×`;
    els.mFps.textContent = `${Math.round(Number(state.fRt))} Hz`;
    els.mTick.textContent = String(state.tick);
    els.mGen.textContent = String(state.generation);
    els.mActive.textContent = `${activeCount} / ${SYNAPSE_COUNT}`;

    const fields = [
      ["activity", els.gActivity, els.vActivity],
      ["memory", els.gMemory, els.vMemory],
      ["crystal", els.gCrystal, els.vCrystal],
      ["repair", els.gRepair, els.vRepair],
      ["error", els.gError, els.vError]
    ];
    fields.forEach(([key, meter, value]) => {
      const v = clamp01(state[key]);
      meter.value = v;
      value.textContent = v.toFixed(2);
    });

    state.synapses.forEach((syn, i) => {
      const group = document.getElementById(`synapse-${i}`);
      if (!group) return;
      group.setAttribute("class", `synapse${!syn.active ? " fault" : ""}${syn.repair > 0 ? " repair" : ""}`);
      const value = group.querySelector(".value");
      if (value) value.textContent = clamp01(syn.activity).toFixed(2);

      const ringLine = document.getElementById(`ring-link-${i}`);
      const coreLine = document.getElementById(`core-link-${i}`);
      const opacity = syn.active ? 0.2 + clamp01(syn.activity) * 0.72 : 0.08;
      if (ringLine) ringLine.style.opacity = String(opacity);
      if (coreLine) coreLine.style.opacity = String(opacity);
    });

    const petalsRotation = (state.tick * 0.22 * Math.max(0.2, Number(state.rExec))) % 360;
    els.phasePetals.setAttribute("transform", `rotate(${petalsRotation} ${CX} ${CY})`);

    renderPulse();

    if (state.tick - lastHashTick >= 4 || lastHashTick < 0) {
      lastHashTick = state.tick;
      updateHashes();
    }
  }

  function renderPulse() {
    els.pulseLayer.replaceChildren();
    if (faultIndex === null) return;
    const p = points[faultIndex];
    const radius = 39 + Math.sin(phase * 2) * 5;
    const circle = svg("circle", {
      class: "pulse",
      cx: p.x,
      cy: p.y,
      r: radius
    });
    circle.style.stroke = repairing ? "var(--orange)" : "var(--red)";
    els.pulseLayer.appendChild(circle);
  }

  function canonicalVisualState() {
    return {
      source: state.source,
      mode: state.mode,
      dtSim: Number(state.dtSim.toFixed(6)),
      rExec: Number(state.rExec.toFixed(6)),
      fRt: Number(state.fRt.toFixed(3)),
      tick: Number(state.tick),
      generation: Number(state.generation),
      activity: Number(state.activity.toFixed(6)),
      memory: Number(state.memory.toFixed(6)),
      crystal: Number(state.crystal.toFixed(6)),
      repair: Number(state.repair.toFixed(6)),
      error: Number(state.error.toFixed(6)),
      synapses: state.synapses.map(s => ({
        id: s.id,
        active: Boolean(s.active),
        activity: Number(clamp01(s.activity).toFixed(6)),
        memory: Number(clamp01(s.memory).toFixed(6)),
        crystal: Number(clamp01(s.crystal).toFixed(6)),
        repair: Number(clamp01(s.repair).toFixed(6))
      }))
    };
  }

  async function updateHashes() {
    if (!window.crypto || !window.crypto.subtle) {
      els.hashValue.textContent = "Web Crypto indisponible";
      els.b36Value.textContent = "indisponible";
      return;
    }
    try {
      const encoded = new TextEncoder().encode(JSON.stringify(canonicalVisualState()));
      const digest = await crypto.subtle.digest("SHA-256", encoded);
      const bytes = Array.from(new Uint8Array(digest));
      const hex = bytes.map(b => b.toString(16).padStart(2, "0")).join("");
      const base36 = BigInt("0x" + hex).toString(36).toUpperCase().padStart(50, "0");
      els.hashValue.textContent = hex;
      els.b36Value.textContent = base36;
    } catch {
      els.hashValue.textContent = "Erreur de calcul";
      els.b36Value.textContent = "Erreur";
    }
  }

  function injectFault() {
    if (liveConnected || faultIndex !== null) return;
    faultIndex = 2;
    const syn = state.synapses[faultIndex];
    syn.active = false;
    syn.activity = 0;
    state.mode = "FAULT";
    state.error = 0.82;
    state.repair = 0;
    repairing = false;
    addEvent("FAULT_DETECTED", syn.id);
    render();
  }

  function startRepair() {
    if (liveConnected || faultIndex === null || repairing) return;
    repairing = true;
    state.mode = "AUTO_REPAIR";
    state.repair = 0.02;
    addEvent("REPAIR_STARTED", state.synapses[faultIndex].id);
    render();
  }

  function resetDemo() {
    if (liveConnected) return;
    state = {
      source: "DEMO",
      mode: "STABLE",
      dtSim: 1 / 60,
      rExec: 1,
      fRt: 60,
      tick: 0,
      generation: 0,
      eventCount: 0,
      activity: 0.35,
      memory: 0.46,
      crystal: 0.28,
      repair: 0,
      error: 0,
      synapses: baseSynapses()
    };
    faultIndex = null;
    repairing = false;
    phase = 0;
    els.eventLog.replaceChildren();
    addEvent("DEMO_RESET", "état déterministe initial");
    render();
  }

  function setLiveMode(payload) {
    const incoming = payload && payload.visual_state ? payload.visual_state : payload;
    if (!incoming || !Array.isArray(incoming.synapses) || incoming.synapses.length !== SYNAPSE_COUNT) {
      return false;
    }

    state = {
      source: "LIVE_READ_ONLY",
      mode: String(incoming.mode || "UNKNOWN"),
      dtSim: Number(incoming.dt_sim ?? incoming.dtSim ?? 0),
      rExec: Number(incoming.r_exec ?? incoming.rExec ?? 0),
      fRt: Number(incoming.f_rt ?? incoming.fRt ?? 0),
      tick: Number(incoming.tick ?? 0),
      generation: Number(incoming.generation ?? 0),
      eventCount: Number(incoming.event_count ?? state.eventCount ?? 0),
      activity: clamp01(incoming.activity),
      memory: clamp01(incoming.memory),
      crystal: clamp01(incoming.crystallization ?? incoming.crystal),
      repair: clamp01(incoming.repair),
      error: clamp01(incoming.error),
      synapses: incoming.synapses.map((s, i) => ({
        id: String(s.id || `S${i + 1}`),
        active: Boolean(s.active),
        activity: clamp01(s.activity),
        memory: clamp01(s.memory),
        crystal: clamp01(s.crystallization ?? s.crystal),
        repair: clamp01(s.repair)
      }))
    };

    liveConnected = true;
    faultIndex = null;
    repairing = false;
    els.sourceBadge.textContent = "LIVE READ-ONLY TELEMETRY";
    els.sourceBadge.className = "badge live";
    els.connectionBadge.textContent = "LIVE CORE : CONNECTÉ";
    els.connectionBadge.className = "badge live";
    els.faultBtn.disabled = true;
    els.repairBtn.disabled = true;
    render();
    return true;
  }

  async function pollLive() {
    try {
      const response = await fetch(LIVE_PATH, { cache: "no-store" });
      if (!response.ok) throw new Error("not live");
      const payload = await response.json();
      if (payload.mode && payload.mode !== "LIVE_READ_ONLY" && !payload.visual_state) {
        throw new Error("invalid public mode");
      }
      setLiveMode(payload);
    } catch {
      if (!liveConnected) {
        els.sourceBadge.textContent = "DEMO TELEMETRY — NOT CORE";
        els.sourceBadge.className = "badge demo";
        els.connectionBadge.textContent = "LIVE CORE : NON CONNECTÉ";
        els.connectionBadge.className = "badge dim";
      }
    }
  }

  function animate() {
    if (!paused && !liveConnected) {
      const core = document.getElementById("core");
      if (core) {
        const scale = 1 + Math.sin(phase * 1.5) * 0.012;
        core.setAttribute("transform", `translate(${CX * (1 - scale)} ${CY * (1 - scale)}) scale(${scale})`);
      }
    }
    rafId = requestAnimationFrame(animate);
  }

  els.faultBtn.addEventListener("click", injectFault);
  els.repairBtn.addEventListener("click", startRepair);
  els.pauseBtn.addEventListener("click", () => {
    paused = !paused;
    els.pauseBtn.textContent = paused ? "Reprendre" : "Pause";
    addEvent(paused ? "VISUAL_PAUSED" : "VISUAL_RESUMED");
  });
  els.resetBtn.addEventListener("click", resetDemo);

  buildClock();
  addEvent("QUEEN_BORN", "7 synapses internes");
  addEvent("STATE_STABLE", "DEMO / VisualState");
  render();

  timerId = window.setInterval(updateDemoState, 250);
  liveTimerId = window.setInterval(pollLive, 2000);
  pollLive();
  animate();

  window.addEventListener("pagehide", () => {
    clearInterval(timerId);
    clearInterval(liveTimerId);
    cancelAnimationFrame(rafId);
  }, { once: true });
})();
