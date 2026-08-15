const CANON = Object.freeze({
  version: 'ANTMUX-CORTEX-1',
  triforce: 3,
  poles: 7,
  branches: 7,
  orientations: 13,
  cycle: 273,
  matrix: 2401,
  mesh: 637,
  rho: 142857,
  neoNumerator: 571429,
  neoDenominator: 999999,
  memory: '9/10',
  coherence: '47/50',
  respiration: '3/50',
});

const ROLES = [
  ['Fourmi', 'mémoire · stigmergie · routage'],
  ['Abeille', 'quorum · agrégation · consensus'],
  ['Scarabée', 'transport · transformation · robustesse'],
  ['Papillon', 'exploration · représentation · mutation'],
  ['Mante', 'sélection · précision · inhibition'],
  ['Libellule', 'observation · anomalies · réaction'],
  ['Termite', 'construction · distribution · persistance'],
];

const WORLDS = new Map([
  [6, 'Carbone'], [7, 'Azote'], [8, 'Oxygène'], [9, 'Fluor'], [10, 'Néon'],
  [20, 'Calcium'], [26, 'Fer'], [29, 'Cuivre'], [30, 'Zinc'], [35, 'Brome'], [36, 'Krypton'],
]);

const mod = (n, m) => ((n % m) + m) % m;

function clockPhases(epochMs) {
  const d = new Date(epochMs);
  return [
    mod(Math.floor(epochMs / 100), 7),
    mod(Math.floor(epochMs / 1000), 7),
    mod(Math.floor(epochMs / 60_000), 7),
    mod(Math.floor(epochMs / 3_600_000), 7),
    mod(Math.floor(epochMs / 86_400_000), 7),
    mod(Math.floor(epochMs / 604_800_000), 7),
    mod(d.getUTCFullYear() - 1970, 7),
  ];
}

function base7Code(phases) {
  return phases.reduce((sum, value, index) => sum + value * (7 ** index), 0);
}

function deriveTime(epochMs) {
  const bucket = Math.floor(epochMs / 100) * 100;
  const phases = clockPhases(bucket);
  const code7 = base7Code(phases);
  const triforce = mod(code7, 3);
  const branch = mod(code7, 7);
  const orientation = mod(code7, 13);
  const phase = mod(91 * triforce + 39 * branch + 21 * orientation, 273);
  return {
    epochMs: bucket,
    utc: new Date(bucket).toISOString(),
    phases,
    code7,
    triforce,
    branch,
    orientation,
    phase,
    pole: mod(phase, 7),
    address: mod(code7, 2401),
  };
}

async function sha256(text) {
  const data = new TextEncoder().encode(text);
  const digest = await crypto.subtle.digest('SHA-256', data);
  return [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2, '0')).join('');
}

async function resolveGitHubIdentity(value) {
  const raw = String(value || '').trim();
  if (!raw) throw new Error('Entre un identifiant GitHub ou un numéro GitHub.');

  if (/^\d+$/.test(raw)) {
    return { id: raw, login: `github-id-${raw}`, verified: false, source: 'declared-id' };
  }

  try {
    const response = await fetch(`https://api.github.com/users/${encodeURIComponent(raw)}`, {
      headers: { Accept: 'application/vnd.github+json' },
    });
    if (!response.ok) throw new Error(`GitHub HTTP ${response.status}`);
    const user = await response.json();
    return {
      id: String(user.id),
      login: user.login,
      verified: true,
      source: 'github-public-api',
      avatar: user.avatar_url,
      profile: user.html_url,
    };
  } catch (error) {
    return { id: `unverified:${raw}`, login: raw, verified: false, source: 'offline-fallback' };
  }
}

function runWorker(roleIndex, payload) {
  return new Promise((resolve, reject) => {
    const worker = new Worker('./antmux-worker.js');
    const timeout = setTimeout(() => {
      worker.terminate();
      reject(new Error(`Worker ${roleIndex} timeout`));
    }, 8000);

    worker.onmessage = (event) => {
      clearTimeout(timeout);
      worker.terminate();
      resolve(event.data);
    };
    worker.onerror = (event) => {
      clearTimeout(timeout);
      worker.terminate();
      reject(new Error(event.message || `Worker ${roleIndex} error`));
    };
    worker.postMessage({ ...payload, roleIndex });
  });
}

async function runSevenWorkers(payload) {
  const results = await Promise.all(ROLES.map((_, index) => runWorker(index, payload)));
  const total = results.reduce((sum, result) => sum + result.raw, 0);
  return results.map(result => ({
    ...result,
    weight: result.raw / total,
  }));
}

function worldName(z) {
  return WORLDS.get(z) || `Monde Z-${z}`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

class AntmuxCortexBox extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.artifact = null;
  }

  connectedCallback() {
    this.render();
    this.bind();
  }

  $(selector) {
    return this.shadowRoot.querySelector(selector);
  }

  render() {
    this.shadowRoot.innerHTML = `
      <style>
        :host{display:block;min-height:100vh;color:#edf7ff;background:radial-gradient(circle at 50% 0,#183449 0,#0a1118 34%,#05080c 76%);font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}
        *{box-sizing:border-box}
        .wrap{width:min(1460px,96vw);margin:0 auto;padding:28px 0 60px}
        .hero{display:flex;justify-content:space-between;align-items:flex-end;gap:18px;margin-bottom:20px}
        .eyebrow{font:800 11px ui-monospace,monospace;letter-spacing:.18em;text-transform:uppercase;color:#72dcff}
        h1{font-size:clamp(36px,6vw,78px);letter-spacing:-.055em;line-height:.92;margin:7px 0 10px}
        h2{margin:5px 0 14px;font-size:24px}
        p{line-height:1.55}.muted{color:#8ca4b7}.small{font-size:12px}.gold{color:#f1ce82}.ok{color:#92e6b2}.warn{color:#ffd27a}
        .badge{border:1px solid #32586e;color:#a5ccdf;border-radius:999px;padding:9px 12px;font:700 11px ui-monospace,monospace;white-space:nowrap}
        .pipeline{display:grid;grid-template-columns:1fr 72px 1.25fr 72px 1fr;gap:10px;align-items:stretch}
        .card{background:linear-gradient(180deg,rgba(14,24,34,.97),rgba(7,12,18,.98));border:1px solid #213a4c;border-radius:22px;padding:18px;box-shadow:0 22px 70px rgba(0,0,0,.25)}
        .arrow{display:grid;place-items:center;color:#e2b562;font-size:38px;font-weight:900}
        label{display:block;margin:12px 0 6px;color:#9cb8c9;font-size:12px;font-weight:750;text-transform:uppercase;letter-spacing:.08em}
        input,textarea,button{font:inherit}
        input,textarea{width:100%;background:#071018;color:#eaf7ff;border:1px solid #315268;border-radius:12px;padding:11px 12px;outline:none}
        textarea{min-height:210px;resize:vertical;font:13px/1.55 ui-monospace,monospace}
        input:focus,textarea:focus{border-color:#72dcff;box-shadow:0 0 0 3px rgba(114,220,255,.08)}
        .row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
        .row>*{flex:1}.row .fixed{flex:0 0 auto}
        button{cursor:pointer;border:1px solid #31576e;background:#102230;color:#ecf8ff;border-radius:12px;padding:11px 14px;font-weight:800}
        button:hover{border-color:#72dcff}button.primary{background:#e2b562;color:#181108;border-color:#f3d38d}button:disabled{opacity:.45;cursor:not-allowed}
        .core{position:relative;overflow:hidden}.core:before{content:'';position:absolute;inset:-30%;background:conic-gradient(from 0deg,transparent,#173d54,transparent,#6b552a,transparent);opacity:.18;animation:spin 15s linear infinite;pointer-events:none}@keyframes spin{to{transform:rotate(360deg)}}
        .core>*{position:relative}
        .core-ring{width:190px;aspect-ratio:1;border:1px solid #4d6c7e;border-radius:50%;margin:10px auto;display:grid;place-items:center;box-shadow:inset 0 0 40px #0b1a24,0 0 40px rgba(98,205,255,.08)}
        .core-ring strong{font:900 38px ui-monospace,monospace;color:#f2d18b}.core-ring span{display:block;text-align:center;color:#7f9cad;font:700 10px ui-monospace,monospace;letter-spacing:.12em}
        .workers{display:grid;gap:7px;margin-top:14px}.worker{display:grid;grid-template-columns:90px 1fr 48px;align-items:center;gap:8px}.track{height:7px;border-radius:999px;background:#10202a;overflow:hidden}.fill{height:100%;background:linear-gradient(90deg,#72dcff,#e2b562)}.pct{text-align:right;font:700 11px ui-monospace,monospace;color:#c8dce8}
        .output{min-height:100%}.proof{background:#050a0e;border:1px solid #1b303e;border-radius:12px;padding:10px;font:11px/1.5 ui-monospace,monospace;word-break:break-all;color:#90b6ca;margin-top:10px}
        .metrics{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}.metric{background:#08131b;border:1px solid #193242;border-radius:12px;padding:9px}.metric span{display:block;color:#708fa3;font-size:10px;text-transform:uppercase;letter-spacing:.08em}.metric strong{display:block;margin-top:4px;font:800 15px ui-monospace,monospace}
        .flow{margin-top:16px;border:1px solid #1d3545;border-radius:18px;padding:14px;background:#071018}.flowline{overflow:auto;white-space:nowrap;font:700 12px ui-monospace,monospace;color:#9dc1d4}.node{display:inline-block;border:1px solid #294b60;border-radius:999px;padding:7px 10px;margin:3px;background:#0a161f}.flowarrow{color:#e2b562;margin:0 3px}
        .actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}.actions a{color:#72dcff;text-decoration:none;font-weight:750;padding:10px 0}
        .status{min-height:20px;margin-top:8px;color:#8fa9bb;font:12px ui-monospace,monospace}
        @media(max-width:1050px){.pipeline{grid-template-columns:1fr}.arrow{transform:rotate(90deg);height:45px}.hero{align-items:flex-start;flex-direction:column}}
      </style>
      <main class="wrap">
        <header class="hero">
          <div>
            <div class="eyebrow">ANTMUX · ARTIFACT BOX · SEVEN WORKERS</div>
            <h1>IN → CORTEX → OUT</h1>
            <p class="muted">Branche une identité GitHub, injecte du contenu, choisis un monde atomique, puis laisse le Cortex produire un artefact Antmux déterministe et vérifiable.</p>
          </div>
          <div class="badge">CLIENT-SIDE · WEB WORKERS · SHA-256</div>
        </header>

        <section class="pipeline">
          <article class="card">
            <div class="eyebrow">GENERATOR IN</div>
            <h2>Entrée</h2>
            <label for="github">GitHub · nom ou numéro</label>
            <input id="github" placeholder="Topbrutus ou 206796334" autocomplete="off" />
            <div class="row">
              <div>
                <label for="world">Monde atomique Z</label>
                <input id="world" type="number" min="1" max="118" value="7" />
              </div>
              <div>
                <label for="epoch">Temps UTC · millisecondes</label>
                <input id="epoch" type="number" step="100" />
              </div>
            </div>
            <label for="content">Contenu à traverser</label>
            <textarea id="content" placeholder="Texte, paramètres, instruction, fragment de données…"></textarea>
            <div class="actions">
              <button id="now">Temps Terre maintenant</button>
              <button id="run" class="primary">Brancher et calculer</button>
            </div>
            <div id="identity" class="status">Aucune identité branchée.</div>
          </article>

          <div class="arrow">→</div>

          <article class="card core">
            <div class="eyebrow">CORTEX ANTMUX</div>
            <h2>Boîte de calcul</h2>
            <div class="core-ring"><div><span>PHASE CANONIQUE</span><strong id="phase">—</strong><span>SUR DEUX CENT SOIXANTE-TREIZE</span></div></div>
            <div class="metrics">
              <div class="metric"><span>Code base sept</span><strong id="code7">—</strong></div>
              <div class="metric"><span>Adresse</span><strong id="address">—</strong></div>
              <div class="metric"><span>Orientation</span><strong id="orientation">—</strong></div>
              <div class="metric"><span>Pôle</span><strong id="pole">—</strong></div>
            </div>
            <div class="workers" id="workers"></div>
            <div class="status" id="core-status">Les sept travailleurs attendent une entrée.</div>
          </article>

          <div class="arrow">→</div>

          <article class="card output">
            <div class="eyebrow">GENERATOR OUT</div>
            <h2>Artefact</h2>
            <div class="metrics">
              <div class="metric"><span>Monde</span><strong id="world-name">—</strong></div>
              <div class="metric"><span>GitHub ID</span><strong id="github-id">—</strong></div>
            </div>
            <label>Signature atomique Antmux</label>
            <div id="atomic" class="proof">—</div>
            <label>Empreinte d'entrée</label>
            <div id="input-hash" class="proof">—</div>
            <label>Preuve d'artefact</label>
            <div id="proof" class="proof">—</div>
            <div class="actions">
              <button id="export" disabled>Exporter JSON</button>
              <button id="copy" disabled>Copier la preuve</button>
              <a href="./clock.html">Ouvrir l'horloge vivante →</a>
            </div>
            <p class="small muted">La “signature atomique” est une signature algorithmique Antmux dérivée du monde Z. Ce n'est pas une propriété physique secrète de l'atome réel.</p>
          </article>
        </section>

        <section class="flow">
          <div class="eyebrow">LOI D'ATTACHEMENT</div>
          <div class="flowline">
            <span class="node">GitHub ID</span><span class="flowarrow">+</span>
            <span class="node">contenu SHA-256</span><span class="flowarrow">+</span>
            <span class="node">temps Terre / 100 ms</span><span class="flowarrow">+</span>
            <span class="node">monde Z</span><span class="flowarrow">→</span>
            <span class="node">graine Cortex</span><span class="flowarrow">→</span>
            <span class="node">sept Web Workers</span><span class="flowarrow">→</span>
            <span class="node">phase 273</span><span class="flowarrow">→</span>
            <span class="node">adresse 2401</span><span class="flowarrow">→</span>
            <span class="node">signature monde</span><span class="flowarrow">→</span>
            <span class="node">preuve SHA-256</span>
          </div>
        </section>
      </main>
    `;
  }

  bind() {
    this.$('#epoch').value = String(Math.floor(Date.now() / 100) * 100);
    this.$('#now').addEventListener('click', () => {
      this.$('#epoch').value = String(Math.floor(Date.now() / 100) * 100);
    });
    this.$('#run').addEventListener('click', () => this.run());
    this.$('#export').addEventListener('click', () => this.exportArtifact());
    this.$('#copy').addEventListener('click', async () => {
      if (!this.artifact) return;
      await navigator.clipboard.writeText(this.artifact.proofHash);
      this.$('#core-status').textContent = 'Preuve copiée.';
    });
  }

  async run() {
    const runButton = this.$('#run');
    runButton.disabled = true;
    this.$('#core-status').textContent = 'Le Cortex résout l’identité et prépare les sept travailleurs…';

    try {
      const github = await resolveGitHubIdentity(this.$('#github').value);
      const z = Math.max(1, Math.min(118, Number(this.$('#world').value || 7)));
      const content = this.$('#content').value;
      const requestedEpoch = Number(this.$('#epoch').value || Date.now());
      const time = deriveTime(requestedEpoch);

      this.$('#identity').innerHTML = github.verified
        ? `<span class="ok">GitHub vérifié : ${escapeHtml(github.login)} · ID ${escapeHtml(github.id)}</span>`
        : `<span class="warn">Identité déclarée : ${escapeHtml(github.login)} · ${escapeHtml(github.id)}</span>`;

      const inputHash = await sha256(content);
      const seedMaterial = JSON.stringify({
        version: CANON.version,
        githubId: github.id,
        githubLogin: github.login,
        worldZ: z,
        epochMs: time.epochMs,
        contentHash: inputHash,
        phases: time.phases,
        phase: time.phase,
        neo: `${CANON.neoNumerator}/${CANON.neoDenominator}`,
      });
      const cortexSeed = await sha256(seedMaterial);

      this.$('#core-status').textContent = 'Sept travailleurs calculent en parallèle…';
      const workers = await runSevenWorkers({
        seed: cortexSeed,
        worldZ: z,
        timePhase: time.phase,
      });

      const workerVector = workers.map(w => `${w.roleIndex}:${w.phaseOffset}:${w.address}:${w.lane}:${w.raw}`).join('|');
      const atomicSignature = await sha256(`ANTMUX|ATOM|Z${z}|${cortexSeed}|${workerVector}`);

      const artifactBase = {
        schema: 'antmux.artifact.v1',
        generatedAtUtc: new Date().toISOString(),
        identity: github,
        input: {
          worldZ: z,
          worldName: worldName(z),
          contentBytes: new TextEncoder().encode(content).length,
          contentHash: inputHash,
        },
        earthTime: time,
        cortex: {
          seedHash: cortexSeed,
          neo: `${CANON.neoNumerator}/${CANON.neoDenominator}`,
          canon: CANON,
          workers,
        },
        output: {
          atomicSignature,
        },
      };
      const proofHash = await sha256(JSON.stringify(artifactBase));
      this.artifact = { ...artifactBase, proofHash };

      this.paint(time, workers, github, z, inputHash, atomicSignature, proofHash);
      this.$('#core-status').innerHTML = '<span class="ok">Artefact calculé. Les sept travailleurs sont alignés sur la même graine.</span>';
      this.$('#export').disabled = false;
      this.$('#copy').disabled = false;
    } catch (error) {
      this.$('#core-status').innerHTML = `<span class="warn">Erreur : ${escapeHtml(error.message)}</span>`;
    } finally {
      runButton.disabled = false;
    }
  }

  paint(time, workers, github, z, inputHash, atomicSignature, proofHash) {
    this.$('#phase').textContent = String(time.phase);
    this.$('#code7').textContent = String(time.code7);
    this.$('#address').textContent = String(time.address);
    this.$('#orientation').textContent = `${time.orientation + 1}/13`;
    this.$('#pole').textContent = `${time.pole + 1}/7`;
    this.$('#world-name').textContent = `${worldName(z)} · Z${z}`;
    this.$('#github-id').textContent = String(github.id);
    this.$('#atomic').textContent = atomicSignature;
    this.$('#input-hash').textContent = inputHash;
    this.$('#proof').textContent = proofHash;
    this.$('#workers').innerHTML = workers.map((worker, index) => `
      <div class="worker" title="${escapeHtml(ROLES[index][1])}">
        <strong>${escapeHtml(worker.role)}</strong>
        <div class="track"><div class="fill" style="width:${(worker.weight * 100).toFixed(3)}%"></div></div>
        <span class="pct">${(worker.weight * 100).toFixed(1)}%</span>
      </div>`).join('');
  }

  exportArtifact() {
    if (!this.artifact) return;
    const blob = new Blob([JSON.stringify(this.artifact, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    const id = String(this.artifact.identity.id).replace(/[^a-zA-Z0-9_-]/g, '_');
    anchor.href = url;
    anchor.download = `antmux-artifact-${id}-z${this.artifact.input.worldZ}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  }
}

customElements.define('antmux-cortex-box', AntmuxCortexBox);
