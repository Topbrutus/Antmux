'use strict';

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
});

const INSECTS = [
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

const els = {
  name: document.querySelector('#ant-name'), status: document.querySelector('#status'),
  phase: document.querySelector('#phase'), pole: document.querySelector('#pole'),
  orientation: document.querySelector('#orientation'), emblem: document.querySelector('#emblem'),
  functions: document.querySelector('#functions'), fingerprint: document.querySelector('#fingerprint'),
  generate: document.querySelector('#generate'), reincarnate: document.querySelector('#reincarnate'),
  export: document.querySelector('#export'), world: document.querySelector('#world'),
  worldOutput: document.querySelector('#world-output'),
};

let current = null;
let generation = Number(localStorage.getItem('antmux.generation') || '0');

function positiveWave(phase, i) {
  const x = Math.sin((2 * Math.PI * (phase + i * 39)) / CANON.cycle);
  return 0.06 + 0.94 * ((x + 1) / 2);
}

function normalizedWeights(phase) {
  const raw = INSECTS.map((_, i) => positiveWave(phase, i));
  const sum = raw.reduce((a, b) => a + b, 0);
  return raw.map(v => v / sum);
}

function phaseIndex(triforce, branch, orientation) {
  return (91 * triforce + 39 * branch + 21 * orientation) % CANON.cycle;
}

function buildAnt(n) {
  const triforce = n % CANON.triforce;
  const branch = n % CANON.branches;
  const orientation = n % CANON.orientations;
  const phase = phaseIndex(triforce, branch, orientation);
  const pole = phase % CANON.poles;
  const weights = normalizedWeights(phase);
  return {
    generation: n,
    name: `ANT-${String(n).padStart(6, '0')}`,
    seed: `${CANON.neoNumerator}:${CANON.cycle}:${n}`,
    triforce, branch, orientation, phase, pole, weights,
    canon: CANON,
  };
}

async function sha256(text) {
  const bytes = new TextEncoder().encode(text);
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  return [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2, '0')).join('');
}

function svgEmblem(ant) {
  const size = 440, cx = 220, cy = 220;
  const ring = 165, local = 35;
  let edges = '', stars = '', ticks = '';

  for (let o = 0; o < CANON.orientations; o++) {
    const a = -Math.PI / 2 + 2 * Math.PI * o / CANON.orientations;
    const x1 = cx + 188 * Math.cos(a), y1 = cy + 188 * Math.sin(a);
    const x2 = cx + 202 * Math.cos(a), y2 = cy + 202 * Math.sin(a);
    const active = o === ant.orientation;
    ticks += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${active ? '#ffdc8c' : '#47627b'}" stroke-width="${active ? 3 : 1}"/>`;
  }

  const centers = [];
  for (let p = 0; p < CANON.poles; p++) {
    const a = -Math.PI / 2 + 2 * Math.PI * p / CANON.poles;
    centers.push([cx + ring * Math.cos(a), cy + ring * Math.sin(a)]);
  }
  for (let p = 0; p < CANON.poles; p++) {
    const [x, y] = centers[p];
    const [nx, ny] = centers[(p + 1) % CANON.poles];
    edges += `<line x1="${x}" y1="${y}" x2="${nx}" y2="${ny}" stroke="#244c66" stroke-width="1" opacity=".75"/>`;
    let rays = '';
    for (let b = 0; b < CANON.branches; b++) {
      const a = -Math.PI / 2 + 2 * Math.PI * b / CANON.branches;
      const tx = x + local * Math.cos(a), ty = y + local * Math.sin(a);
      rays += `<line x1="${x}" y1="${y}" x2="${tx}" y2="${ty}" stroke="${p === ant.pole ? '#ffdc8c' : '#6ed7ff'}" stroke-width="${p === ant.pole ? 2.4 : 1.2}"/>`;
    }
    stars += `${rays}<circle cx="${x}" cy="${y}" r="5" fill="${p === ant.pole ? '#ffdc8c' : '#6ed7ff'}"/>`;
  }

  const infinity = `<path d="M125 220 C125 155 190 155 220 220 C250 285 315 285 315 220 C315 155 250 155 220 220 C190 285 125 285 125 220" fill="none" stroke="#e0b462" stroke-width="3" opacity=".9"/>`;
  return `<svg viewBox="0 0 ${size} ${size}" role="img" aria-label="Heptaflux de ${ant.name}">
    <circle cx="${cx}" cy="${cy}" r="205" fill="none" stroke="#253647" stroke-width="1"/>
    ${ticks}${edges}${stars}${infinity}
    <circle cx="${cx}" cy="${cy}" r="72" fill="#080b10" stroke="#e0b462" stroke-width="1.5"/>
    <text x="${cx}" y="${cy-4}" fill="#f5e3bd" text-anchor="middle" font-size="16" font-family="monospace">${ant.name}</text>
    <text x="${cx}" y="${cy+19}" fill="#7fa9c5" text-anchor="middle" font-size="12" font-family="monospace">φ ${ant.phase} / 273</text>
  </svg>`;
}

async function render(ant) {
  current = ant;
  els.name.textContent = ant.name;
  els.phase.textContent = ant.phase;
  els.pole.textContent = ant.pole + 1;
  els.orientation.textContent = `${ant.orientation + 1}/13`;
  els.emblem.innerHTML = svgEmblem(ant);

  els.functions.innerHTML = ant.weights.map((w, i) => `
    <div class="function-row" title="${INSECTS[i][1]}">
      <strong>${INSECTS[i][0]}</strong>
      <div class="track"><div class="fill" style="width:${(w * 100).toFixed(2)}%"></div></div>
      <span class="value">${(w * 100).toFixed(1)}%</span>
    </div>`).join('');

  els.status.textContent = 'CALCUL';
  const fp = await sha256(JSON.stringify(ant));
  ant.fingerprint = fp;
  els.fingerprint.textContent = fp;
  els.status.textContent = 'VÉRIFIÉE';
}

async function newAnt() {
  generation += 1;
  localStorage.setItem('antmux.generation', String(generation));
  await render(buildAnt(generation));
}

async function reincarnate() {
  if (!current) return;
  const rebuilt = buildAnt(current.generation);
  const oldFingerprint = current.fingerprint;
  await render(rebuilt);
  els.status.textContent = rebuilt.fingerprint === oldFingerprint ? 'RÉINCARNÉE ✓' : 'ÉCART ✕';
}

function exportJson() {
  if (!current) return;
  const blob = new Blob([JSON.stringify(current, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = `${current.name.toLowerCase()}.json`; a.click();
  URL.revokeObjectURL(url);
}

function renderWorld() {
  const z = Math.max(1, Math.min(118, Number(els.world.value || 7)));
  const known = WORLDS.get(z);
  els.worldOutput.innerHTML = `<strong>Z = ${z}${known ? ` · ${known}` : ''}</strong><br><span>Monde paramétrique ${z}. Les propriétés physiques réelles doivent être chargées depuis une source scientifique avant simulation.</span>`;
}

els.generate.addEventListener('click', newAnt);
els.reincarnate.addEventListener('click', reincarnate);
els.export.addEventListener('click', exportJson);
els.world.addEventListener('input', renderWorld);
renderWorld();

if (generation === 0) generation = 1;
render(buildAnt(generation));
