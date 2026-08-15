'use strict';

const EXPECTED = Object.freeze({
  triforce: 3,
  structuresIndependent: 6,
  structuresVisible: 7,
  poles: 7,
  branches: 7,
  calibrations: 10,
  barriers: 9,
  orientations: 13,
  points: 49,
  polePairs: 21,
  matchingLinks: 147,
  undirectedLinks: 1029,
  directedLinks: 2058,
  matrixZeros: 343,
  matrixCells: 2401,
  cycle7x13: 91,
  cycle3x7x13: 273,
  mesh13x7x7: 637,
  degree: 42,
  lambda: 35,
  mu: 42,
  rho: 142857,
  neoNumerator: 571429,
  neoDenominator: 999999,
});

const gcd = (a, b) => {
  a = Math.abs(a); b = Math.abs(b);
  while (b) [a, b] = [b, a % b];
  return a;
};
const lcm = (...values) => values.reduce((a, b) => Math.abs(a * b) / gcd(a, b));
const choose2 = n => n * (n - 1) / 2;
const phaseIndex = (t, b, o) => (91 * t + 39 * b + 21 * o) % 273;

function graphReport() {
  const groups = 7;
  const perGroup = 7;
  const n = groups * perGroup;
  const adjacency = Array.from({ length: n }, (_, i) =>
    Array.from({ length: n }, (_, j) => Number(i !== j && Math.floor(i / perGroup) !== Math.floor(j / perGroup)))
  );
  const degreeSet = new Set(adjacency.map(row => row.reduce((a, b) => a + b, 0)));
  const ones = adjacency.flat().reduce((a, b) => a + b, 0);
  const zeros = n * n - ones;
  const edges = ones / 2;
  const neighbors = i => new Set(adjacency[i].map((v, j) => v ? j : -1).filter(j => j >= 0));
  const lambda = new Set();
  const mu = new Set();
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      const ni = neighbors(i), nj = neighbors(j);
      let common = 0;
      for (const x of ni) if (nj.has(x)) common++;
      (adjacency[i][j] ? lambda : mu).add(common);
    }
  }
  return { degreeSet: [...degreeSet], ones, zeros, edges, lambda: [...lambda], mu: [...mu] };
}

function verify() {
  const P = EXPECTED.poles;
  const B = EXPECTED.branches;
  const O = EXPECTED.orientations;
  const T = EXPECTED.triforce;

  const phases = new Set();
  for (let t = 0; t < T; t++) {
    for (let b = 0; b < B; b++) {
      for (let o = 0; o < O; o++) phases.add(phaseIndex(t, b, o));
    }
  }

  const graph = graphReport();
  const cycle7 = Array.from({ length: 7 }, (_, i) => (i + 1) * EXPECTED.rho);
  const neoByAverage = cycle7.reduce((sum, x) => sum + x + 1, 0) / 7;

  const checks = [
    ['7 × 7 = 49', P * B, EXPECTED.points],
    ['C(7,2) = 21', choose2(P), EXPECTED.polePairs],
    ['21 × 7 = 147', choose2(P) * B, EXPECTED.matchingLinks],
    ['21 × 7 × 7 = 1029', choose2(P) * B * B, EXPECTED.undirectedLinks],
    ['2 × 1029 = 2058', 2 * EXPECTED.undirectedLinks, EXPECTED.directedLinks],
    ['7³ = 343', P ** 3, EXPECTED.matrixZeros],
    ['7⁴ = 49² = 2401', P ** 4, EXPECTED.matrixCells],
    ['2058 + 343 = 2401', EXPECTED.directedLinks + EXPECTED.matrixZeros, EXPECTED.matrixCells],
    ['ppcm(7,13) = 91', lcm(P, O), EXPECTED.cycle7x13],
    ['ppcm(3,7,13) = 273', lcm(T, P, O), EXPECTED.cycle3x7x13],
    ['13 × 7 × 7 = 637', O * P * B, EXPECTED.mesh13x7x7],
    ['273 phases distinctes', phases.size, 273],
    ['degré du graphe = 42', graph.degreeSet.join(','), '42'],
    ['arêtes du graphe = 1029', graph.edges, 1029],
    ['uns de la matrice = 2058', graph.ones, 2058],
    ['zéros de la matrice = 343', graph.zeros, 343],
    ['lambda = 35', graph.lambda.join(','), '35'],
    ['mu = 42', graph.mu.join(','), '42'],
    ['rho = (10^6−1)/7 = 142857', (10 ** 6 - 1) / 7, EXPECTED.rho],
    ['NEO_num = moyenne des 7 états +1', neoByAverage, EXPECTED.neoNumerator],
    ['C + V = 1', 47 / 50 + 3 / 50, 1],
    ['700 ms / 7 = 100 ms', 700 / 7, 100],
    ['7 s / 7 = 1 s', 7 / 7, 1],
    ['7 min / 7 = 1 min', 7 / 7, 1],
    ['7 h / 7 = 1 h', 7 / 7, 1],
    ['7 jours / 7 = 1 jour', 7 / 7, 1],
    ['7 semaines / 7 = 1 semaine', 7 / 7, 1],
    ['7 ans / 7 = 1 an', 7 / 7, 1],
  ].map(([name, actual, expected]) => ({ name, actual, expected, pass: String(actual) === String(expected) }));

  return {
    engine: 'Antmux Public Verifier',
    version: 1,
    generatedAt: new Date().toISOString(),
    checks,
    pass: checks.every(c => c.pass),
    summary: {
      passed: checks.filter(c => c.pass).length,
      total: checks.length,
      phasesDistinct: phases.size,
      graph,
      cycle7,
      neo: `${EXPECTED.neoNumerator}/${EXPECTED.neoDenominator}`,
    },
    scope: 'Vérification mathématique publique uniquement. Aucune implémentation du serveur dédié Antmux n’est incluse.',
  };
}

function render() {
  const report = verify();
  const tbody = document.querySelector('#checks');
  tbody.innerHTML = report.checks.map(c => `
    <tr class="${c.pass ? 'pass' : 'fail'}">
      <td>${c.pass ? 'PASS' : 'FAIL'}</td>
      <td>${c.name}</td>
      <td><code>${c.actual}</code></td>
      <td><code>${c.expected}</code></td>
    </tr>`).join('');
  document.querySelector('#status').textContent = report.pass ? `VERIFIED · ${report.summary.passed}/${report.summary.total}` : `FAILED · ${report.summary.passed}/${report.summary.total}`;
  document.querySelector('#status').className = report.pass ? 'ok' : 'bad';
  window.__ANTMUX_VERIFICATION_REPORT__ = report;
}

function exportReport() {
  const report = window.__ANTMUX_VERIFICATION_REPORT__ || verify();
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'antmux-verification-report.json';
  a.click();
  URL.revokeObjectURL(url);
}

document.querySelector('#rerun').addEventListener('click', render);
document.querySelector('#export').addEventListener('click', exportReport);
render();
