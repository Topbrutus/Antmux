const CANON = Object.freeze({
  triforce: 3,
  structuresIndependent: 6,
  structuresTotal: 7,
  poles: 7,
  branches: 7,
  barriers: 9,
  calibrations: 10,
  orientations: 13,
  points: 49,
  cyclePoleOrientation: 91,
  cycle: 273,
  mesh: 637,
  links: 1029,
  directedLinks: 2058,
  matrix: 2401,
  rho: 142857,
  neoNumerator: 571429,
  neoDenominator: 999999,
  memory: 9 / 10,
  coherence: 47 / 50,
  respiration: 3 / 50,
});

const INSECTS = Object.freeze([
  ['Fourmi', 'mémoire · stigmergie · routage'],
  ['Abeille', 'quorum · agrégation · consensus'],
  ['Scarabée', 'transport · transformation · robustesse'],
  ['Papillon', 'exploration · représentation · mutation'],
  ['Mante', 'sélection · précision · inhibition'],
  ['Libellule', 'observation · anomalie · réaction'],
  ['Termite', 'construction · distribution · persistance'],
]);

const MS = Object.freeze({
  hundred: 100,
  second: 1000,
  minute: 60_000,
  hour: 3_600_000,
  day: 86_400_000,
  week: 604_800_000,
});

const mod = (n, m) => ((n % m) + m) % m;

function phaseIndex(t, b, o) {
  return mod(91 * t + 39 * b + 21 * o, CANON.cycle);
}

function clockPhases(epochMs) {
  const d = new Date(epochMs);
  return [
    mod(Math.floor(epochMs / MS.hundred), 7),
    mod(Math.floor(epochMs / MS.second), 7),
    mod(Math.floor(epochMs / MS.minute), 7),
    mod(Math.floor(epochMs / MS.hour), 7),
    mod(Math.floor(epochMs / MS.day), 7),
    mod(Math.floor(epochMs / MS.week), 7),
    mod(d.getUTCFullYear() - 1970, 7),
  ];
}

function base7Code(phases) {
  return phases.reduce((sum, value, index) => sum + value * (7 ** index), 0);
}

function insectWeights(phase) {
  const raw = INSECTS.map((_, i) => {
    const wave = Math.sin((2 * Math.PI * (phase + i * 39)) / CANON.cycle);
    return CANON.respiration + CANON.coherence * ((wave + 1) / 2);
  });
  const total = raw.reduce((a, b) => a + b, 0);
  const out = raw.map(v => v / total);
  const firstSix = out.slice(0, 6);
  out[6] = Math.max(0, 1 - firstSix.reduce((a, b) => a + b, 0));
  return out;
}

function derive(epochMs) {
  const bucket = Math.floor(epochMs / 100) * 100;
  const phases = clockPhases(bucket);
  const code7 = base7Code(phases);
  const triforce = mod(code7, 3);
  const branch = mod(code7, 7);
  const orientation = mod(code7, 13);
  const phase = phaseIndex(triforce, branch, orientation);
  const pole = mod(phase, 7);
  const address = mod(code7, CANON.matrix);
  const theta = (2 * Math.PI * phase) / CANON.cycle;
  const lemniscate = [Math.sin(theta), 0.5 * Math.sin(2 * theta)];
  const weights = insectWeights(phase);
  return {
    epochMs: bucket,
    utc: new Date(bucket).toISOString(),
    local: new Date(bucket).toLocaleString(),
    phases,
    code7,
    triforce,
    branch,
    orientation,
    phase,
    pole,
    address,
    lemniscate,
    weights,
    canon: CANON,
  };
}

async function sha256(text) {
  const data = new TextEncoder().encode(text);
  const digest = await crypto.subtle.digest('SHA-256', data);
  return [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2, '0')).join('');
}

function snapshotPayload(state) {
  return {
    epochMs: state.epochMs,
    phases: state.phases,
    code7: state.code7,
    triforce: state.triforce,
    branch: state.branch,
    orientation: state.orientation,
    phase: state.phase,
    pole: state.pole,
    address: state.address,
    weights: state.weights.map(v => Number(v.toFixed(12))),
    canon: state.canon,
  };
}

class AntmuxWorldGenerator extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.live = true;
    this.epochMs = Date.now();
    this.current = null;
    this.capture = null;
    this.timer = null;
  }

  connectedCallback() {
    this.renderShell();
    this.bind();
    this.tick();
    this.timer = setInterval(() => this.tick(), 100);
  }

  disconnectedCallback() {
    if (this.timer) clearInterval(this.timer);
  }

  $(selector) {
    return this.shadowRoot.querySelector(selector);
  }

  renderShell() {
    this.shadowRoot.innerHTML = `
      <style>
        :host{display:block;min-height:100vh;background:
          radial-gradient(circle at 50% 0%,#153149 0,#0a1119 36%,#070b10 70%);color:#eef6ff}
        *{box-sizing:border-box}
        .wrap{width:min(1420px,96vw);margin:0 auto;padding:28px 0 56px}
        .hero{display:flex;justify-content:space-between;align-items:flex-end;gap:20px;margin-bottom:20px}
        .eyebrow{font:700 12px/1.2 ui-monospace,monospace;letter-spacing:.18em;color:#78d9ff;text-transform:uppercase}
        h1{margin:6px 0 0;font-size:clamp(34px,6vw,74px);line-height:.95;letter-spacing:-.045em}
        .sub{max-width:720px;color:#9fb5c6;margin:10px 0 0;line-height:1.55}
        .badge{border:1px solid #315a73;border-radius:999px;padding:9px 12px;color:#a9cde2;font:700 12px ui-monospace,monospace;white-space:nowrap}
        .grid{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(320px,.8fr);gap:16px}
        .card{background:linear-gradient(180deg,rgba(15,25,35,.96),rgba(8,13,19,.97));border:1px solid #20384b;border-radius:22px;padding:18px;box-shadow:0 24px 80px rgba(0,0,0,.28)}
        .wide{grid-column:1/-1}
        .row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
        button,input{font:inherit}
        button{border:1px solid #315b75;background:#112231;color:#e9f7ff;border-radius:12px;padding:10px 14px;cursor:pointer;font-weight:750}
        button:hover{border-color:#78d9ff}
        button.primary{background:#e2b562;color:#17110a;border-color:#f3d38d}
        button.danger{background:#25161a;border-color:#6c3440}
        input{width:230px;background:#090f16;border:1px solid #31536b;color:#eaf7ff;border-radius:10px;padding:9px 10px}
        .clock{font:700 clamp(24px,4vw,52px)/1 ui-monospace,monospace;margin:8px 0;color:#f7e8bf}
        .muted{color:#819aad;font-size:13px}
        .metrics{display:grid;grid-template-columns:repeat(6,minmax(90px,1fr));gap:8px;margin-top:14px}
        .metric{background:#09131c;border:1px solid #1c3344;border-radius:14px;padding:10px}
        .metric span{display:block;font-size:11px;color:#7896aa;text-transform:uppercase;letter-spacing:.08em}
        .metric strong{display:block;margin-top:4px;font:700 18px ui-monospace,monospace;color:#eaf7ff}
        .clocks{display:grid;grid-template-columns:repeat(7,1fr);gap:8px;margin-top:14px}
        .clockcell{padding:11px 8px;border:1px solid #24445a;background:#0a151e;border-radius:14px;text-align:center;position:relative;overflow:hidden}
        .clockcell::after{content:'';position:absolute;left:0;bottom:0;height:3px;width:var(--p);background:#6ed7ff}
        .clockcell strong{display:block;font:800 24px ui-monospace,monospace;color:#f4d792}
        .clockcell small{color:#7895a8}
        .dependency{display:flex;align-items:center;gap:8px;overflow:auto;padding:8px 0 2px;white-space:nowrap;font:700 12px ui-monospace,monospace;color:#8dbbd5}
        .node{border:1px solid #274a60;border-radius:999px;padding:7px 10px;background:#0a151d}
        .arrow{color:#e2b562}
        .mainviz{display:grid;grid-template-columns:minmax(320px,1fr) minmax(280px,.75fr);gap:14px;align-items:center}
        .viz{min-height:520px;display:grid;place-items:center;background:radial-gradient(circle,#0e1e2a 0,#081018 58%,#06090d 100%);border:1px solid #1e3647;border-radius:18px;overflow:hidden}
        svg{width:100%;height:auto;max-height:520px}
        .functions{display:grid;gap:9px}
        .frow{display:grid;grid-template-columns:92px 1fr 54px;gap:8px;align-items:center}
        .track{height:8px;background:#101f2a;border-radius:999px;overflow:hidden}
        .fill{height:100%;background:linear-gradient(90deg,#6ed7ff,#e0b462)}
        .value{text-align:right;font:700 12px ui-monospace,monospace;color:#cbddea}
        .formula{font:12px/1.55 ui-monospace,monospace;white-space:pre-wrap;background:#060a0e;border:1px solid #182d3c;border-radius:14px;padding:12px;color:#a9cfe5;margin-top:12px}
        .snapshot{word-break:break-all;font:11px/1.45 ui-monospace,monospace;color:#80a6bc;background:#070c11;border:1px solid #1b3140;padding:10px;border-radius:12px}
        .ok{color:#93e6b1}.warn{color:#ffd27a}
        @media(max-width:920px){.grid,.mainviz{grid-template-columns:1fr}.metrics{grid-template-columns:repeat(3,1fr)}.clocks{grid-template-columns:repeat(2,1fr)}.wide{grid-column:auto}.hero{align-items:flex-start;flex-direction:column}.viz{min-height:360px}}
      </style>
      <div class="wrap">
        <header class="hero">
          <div>
            <div class="eyebrow">ANTMUX · WEB COMPONENT · HORLOGE TERRE</div>
            <h1>Lecteur temporel synthétique</h1>
            <p class="sub">Une seule source dynamique. L'heure UTC de la Terre alimente sept phases liées, puis la Triforce, la branche, l'orientation, la phase deux cent soixante-treize, le pôle et les sept fonctions internes.</p>
          </div>
          <div class="badge">AUCUN REACT · AUCUN BACKEND · ÉTAT DÉRIVÉ</div>
        </header>

        <section class="grid">
          <article class="card wide">
            <div class="row" style="justify-content:space-between">
              <div>
                <div class="eyebrow">SOURCE CANONIQUE</div>
                <div id="utc" class="clock">—</div>
                <div id="local" class="muted">—</div>
              </div>
              <div class="row">
                <button id="live" class="primary">Pause</button>
                <button id="step100">+ 100 ms</button>
                <button id="step1s">+ 1 s</button>
                <input id="epoch" type="number" step="100" aria-label="Epoch Unix en millisecondes" />
                <button id="apply">Appliquer</button>
              </div>
            </div>
            <div id="clocks" class="clocks"></div>
            <div class="dependency">
              <span class="node">UTC ms</span><span class="arrow">→</span>
              <span class="node">sept phases</span><span class="arrow">→</span>
              <span class="node">code base sept</span><span class="arrow">→</span>
              <span class="node">T · B · O</span><span class="arrow">→</span>
              <span class="node">phase 273</span><span class="arrow">→</span>
              <span class="node">pôle</span><span class="arrow">→</span>
              <span class="node">sept insectes</span><span class="arrow">→</span>
              <span class="node">emblème</span>
            </div>
          </article>

          <article class="card">
            <div class="eyebrow">ÉTAT LIÉ</div>
            <div class="metrics">
              <div class="metric"><span>Code₇</span><strong id="code7">—</strong></div>
              <div class="metric"><span>Triforce</span><strong id="tri">—</strong></div>
              <div class="metric"><span>Branche</span><strong id="branch">—</strong></div>
              <div class="metric"><span>Orientation</span><strong id="orientation">—</strong></div>
              <div class="metric"><span>Phase</span><strong id="phase">—</strong></div>
              <div class="metric"><span>Pôle</span><strong id="pole">—</strong></div>
            </div>
            <div class="metrics" style="grid-template-columns:repeat(3,1fr)">
              <div class="metric"><span>Adresse</span><strong id="address">—</strong></div>
              <div class="metric"><span>NEO</span><strong>571429/999999</strong></div>
              <div class="metric"><span>Matrice</span><strong>2401</strong></div>
            </div>
            <div class="formula">700 ms / 7 = 100 ms
7 s / 7 = 1 s
7 min / 7 = 1 min
7 h / 7 = 1 h
7 jours / 7 = 1 jour
7 semaines / 7 = 1 semaine
7 années / 7 = 1 année

r = (91T + 39B + 21O) mod 273
M = 9/10 · C = 47/50 · V = 3/50 · C + V = 1</div>
          </article>

          <article class="card">
            <div class="eyebrow">SEPT FONCTIONS INTERNES</div>
            <div id="functions" class="functions"></div>
          </article>

          <article class="card wide mainviz">
            <div id="viz" class="viz"></div>
            <div>
              <div class="eyebrow">CAPTURE / RÉINCARNATION</div>
              <h2 style="margin:.35rem 0 1rem">Premier état reproductible</h2>
              <div class="row">
                <button id="capture" class="primary">Capturer</button>
                <button id="reincarnate">Réincarner</button>
                <button id="export">Exporter JSON</button>
              </div>
              <p class="muted">La capture fige le quantum de cent millisecondes. Réincarner recalcule tout depuis cette seule valeur et compare l'empreinte.</p>
              <div style="margin-top:12px" class="muted">État</div>
              <div id="captureStatus" class="snapshot">Aucune capture.</div>
              <div style="margin-top:12px" class="muted">Empreinte SHA-256</div>
              <div id="fingerprint" class="snapshot">—</div>
            </div>
          </article>
        </section>
      </div>`;
  }

  bind() {
    this.$('#live').addEventListener('click', () => {
      this.live = !this.live;
      if (!this.live) this.epochMs = this.current?.epochMs ?? Date.now();
      this.$('#live').textContent = this.live ? 'Pause' : 'Reprendre';
      this.$('#live').classList.toggle('primary', this.live);
      this.tick(true);
    });

    this.$('#step100').addEventListener('click', () => {
      this.live = false;
      this.$('#live').textContent = 'Reprendre';
      this.epochMs = (this.current?.epochMs ?? this.epochMs) + 100;
      this.tick(true);
    });

    this.$('#step1s').addEventListener('click', () => {
      this.live = false;
      this.$('#live').textContent = 'Reprendre';
      this.epochMs = (this.current?.epochMs ?? this.epochMs) + 1000;
      this.tick(true);
    });

    this.$('#apply').addEventListener('click', () => {
      const value = Number(this.$('#epoch').value);
      if (Number.isFinite(value)) {
        this.live = false;
        this.$('#live').textContent = 'Reprendre';
        this.epochMs = Math.floor(value / 100) * 100;
        this.tick(true);
      }
    });

    this.$('#capture').addEventListener('click', () => this.captureState());
    this.$('#reincarnate').addEventListener('click', () => this.reincarnate());
    this.$('#export').addEventListener('click', () => this.exportJson());
  }

  tick(force = false) {
    const now = this.live ? Date.now() : this.epochMs;
    const bucket = Math.floor(now / 100) * 100;
    if (!force && this.current?.epochMs === bucket) return;
    this.epochMs = bucket;
    this.current = derive(bucket);
    this.renderState();
  }

  renderState() {
    const s = this.current;
    this.$('#utc').textContent = s.utc.replace('T', ' ').replace('Z', ' UTC');
    this.$('#local').textContent = `Local navigateur : ${s.local}`;
    this.$('#epoch').value = String(s.epochMs);
    this.$('#code7').textContent = s.code7;
    this.$('#tri').textContent = `${s.triforce + 1}/3`;
    this.$('#branch').textContent = `${s.branch + 1}/7`;
    this.$('#orientation').textContent = `${s.orientation + 1}/13`;
    this.$('#phase').textContent = `${s.phase}/272`;
    this.$('#pole').textContent = `${s.pole + 1}/7`;
    this.$('#address').textContent = `${s.address}/2400`;

    const labels = ['700 ms', '7 s', '7 min', '7 h', '7 jours', '7 semaines', '7 années'];
    this.$('#clocks').innerHTML = s.phases.map((value, i) => `
      <div class="clockcell" style="--p:${((value + 1) / 7) * 100}%">
        <small>${labels[i]}</small>
        <strong>${value}</strong>
        <small>sur 0…6</small>
      </div>`).join('');

    this.$('#functions').innerHTML = s.weights.map((w, i) => `
      <div class="frow" title="${INSECTS[i][1]}">
        <strong>${INSECTS[i][0]}</strong>
        <div class="track"><div class="fill" style="width:${(w * 100).toFixed(3)}%"></div></div>
        <div class="value">${(w * 100).toFixed(2)}%</div>
      </div>`).join('');

    this.$('#viz').innerHTML = this.svg(s);
  }

  svg(s) {
    const size = 620, cx = 310, cy = 310, outer = 250, starRing = 205, ray = 38;
    let ticks = '', stars = '', links = '';

    for (let o = 0; o < 13; o++) {
      const a = -Math.PI / 2 + (2 * Math.PI * o) / 13;
      const x1 = cx + outer * Math.cos(a), y1 = cy + outer * Math.sin(a);
      const x2 = cx + (outer + 17) * Math.cos(a), y2 = cy + (outer + 17) * Math.sin(a);
      const active = o === s.orientation;
      ticks += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${active ? '#f3d38d' : '#34566b'}" stroke-width="${active ? 4 : 1.3}"/>`;
    }

    const centers = [];
    for (let p = 0; p < 7; p++) {
      const a = -Math.PI / 2 + (2 * Math.PI * p) / 7;
      centers.push([cx + starRing * Math.cos(a), cy + starRing * Math.sin(a)]);
    }

    for (let p = 0; p < 7; p++) {
      const [x, y] = centers[p];
      const [nx, ny] = centers[(p + 1) % 7];
      links += `<line x1="${x}" y1="${y}" x2="${nx}" y2="${ny}" stroke="#23475c" stroke-width="1.3"/>`;
      let rays = '';
      for (let b = 0; b < 7; b++) {
        const a = -Math.PI / 2 + (2 * Math.PI * b) / 7;
        const tx = x + ray * Math.cos(a), ty = y + ray * Math.sin(a);
        const active = p === s.pole && b === s.branch;
        rays += `<line x1="${x}" y1="${y}" x2="${tx}" y2="${ty}" stroke="${active ? '#f3d38d' : '#68d7ff'}" stroke-width="${active ? 4 : 1.5}"/>`;
      }
      stars += `${rays}<circle cx="${x}" cy="${y}" r="${p === s.pole ? 8 : 5}" fill="${p === s.pole ? '#f3d38d' : '#68d7ff'}"/>`;
    }

    const t = (2 * Math.PI * s.phase) / 273;
    const lx = cx + 105 * Math.sin(t);
    const ly = cy + 100 * 0.5 * Math.sin(2 * t);
    const infinity = `<path d="M180 310 C180 225 265 225 310 310 C355 395 440 395 440 310 C440 225 355 225 310 310 C265 395 180 395 180 310" fill="none" stroke="#d8a956" stroke-width="4" opacity=".9"/>
      <circle cx="${lx}" cy="${ly}" r="8" fill="#fff0b6" stroke="#d8a956" stroke-width="3"/>`;

    return `<svg viewBox="0 0 ${size} ${size}" aria-label="Emblème temporel Antmux">
      <circle cx="${cx}" cy="${cy}" r="278" fill="none" stroke="#1e3545"/>
      ${ticks}${links}${stars}${infinity}
      <circle cx="${cx}" cy="${cy}" r="86" fill="#070c11" stroke="#d8a956" stroke-width="2"/>
      <text x="${cx}" y="${cy - 16}" text-anchor="middle" fill="#f7e8bf" font-size="20" font-family="ui-monospace,monospace">r ${s.phase} / 273</text>
      <text x="${cx}" y="${cy + 12}" text-anchor="middle" fill="#82b6d3" font-size="14" font-family="ui-monospace,monospace">code₇ ${s.code7}</text>
      <text x="${cx}" y="${cy + 36}" text-anchor="middle" fill="#82b6d3" font-size="12" font-family="ui-monospace,monospace">adresse ${s.address} / 2400</text>
    </svg>`;
  }

  async captureState() {
    const payload = snapshotPayload(this.current);
    const fingerprint = await sha256(JSON.stringify(payload));
    this.capture = { payload, fingerprint };
    this.$('#fingerprint').textContent = fingerprint;
    this.$('#captureStatus').innerHTML = `<span class="ok">CAPTURE OK</span> · ${payload.epochMs} · phase ${payload.phase} · code₇ ${payload.code7}`;
  }

  async reincarnate() {
    if (!this.capture) {
      this.$('#captureStatus').innerHTML = '<span class="warn">Capture requise avant réincarnation.</span>';
      return;
    }
    const rebuilt = derive(this.capture.payload.epochMs);
    const fp = await sha256(JSON.stringify(snapshotPayload(rebuilt)));
    const ok = fp === this.capture.fingerprint;
    this.$('#captureStatus').innerHTML = ok
      ? `<span class="ok">RÉINCARNATION IDENTIQUE ✓</span> · phase ${rebuilt.phase} · code₇ ${rebuilt.code7}`
      : `<span class="warn">ÉCART DÉTECTÉ ✕</span>`;
    this.$('#fingerprint').textContent = fp;
  }

  exportJson() {
    const payload = this.capture?.payload ?? snapshotPayload(this.current);
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `antmux-time-${payload.epochMs}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }
}

customElements.define('antmux-world-generator', AntmuxWorldGenerator);
