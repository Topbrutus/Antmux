#!/usr/bin/env node
import { extractProgressiveGenesisStatus, buildProgressiveBridgeInput } from './build-public-source-progressive.mjs';
import { buildProgressivePublicEnvelope } from './bridge-public-progressive.mjs';

const LEGACY = `science_baseline=GREEN\ngenesis003_c041_c060=COMPLETE_VALIDATED\nexperiment_selection_performed=true\nselected_experiment_status=PLANNED_NOT_EXECUTED\nhypothesis_selection_performed=false\nhypothesis_ranking_produced=false\nuncertainty_promotion_performed=false\nprobabilities_produced=false\nevidence_ledger_auto_promotion=false\nGENESIS_AUDIT_FAILED=0\n`;
const C061 = `${LEGACY}genesis003_validated_through=C061\ngenesis003_c061=VALIDATED_10_OF_10\nc061_execution_input=SYNTHETIC_C060_FIXTURE\nexecution_admissibility=BLOCKED_SYNTHETIC_SELECTION\nnext_scientific_action=AWAIT_REAL_EXPERIMENT_SPEC\n`;

function assert(condition, message) { if (!condition) throw new Error(message); }
function rejected(fn) { try { fn(); return false; } catch { return true; } }
function clone(value) { return structuredClone(value); }
function metric(envelope, id) { return envelope.payload.metrics.find((x) => x.id === id); }

const tests = [
  ['PV2-01', 'legacy C060 status remains accepted and live', () => {
    const status = extractProgressiveGenesisStatus(LEGACY);
    assert(status.validatedThrough === 'C060', 'legacy stage');
    const input = buildProgressiveBridgeInput(status, { now: '2026-09-03T22:00:00Z', liveActive: true });
    const { envelope } = buildProgressivePublicEnvelope(input, { now: '2026-09-03T22:00:00Z' });
    assert(envelope.mode === 'LIVE_READ_ONLY', 'mode');
    assert(metric(envelope, 'genesis003-validated-through')?.value === 'C060', 'C060 metric');
    assert(metric(envelope, 'public-live-active')?.value === true, 'live metric');
  }],
  ['PV2-02', 'C061 status is accepted only with the exact blocked synthetic boundary', () => {
    const status = extractProgressiveGenesisStatus(C061);
    assert(status.validatedThrough === 'C061', 'C061 stage');
    assert(status.executionAdmissibility === 'BLOCKED_SYNTHETIC_SELECTION', 'C061 gate');
    assert(status.nextScientificAction === 'AWAIT_REAL_EXPERIMENT_SPEC', 'C061 next action');
  }],
  ['PV2-03', 'C061 public envelope exposes progression without claiming execution', () => {
    const status = extractProgressiveGenesisStatus(C061);
    const input = buildProgressiveBridgeInput(status, { now: '2026-09-03T22:00:00Z', liveActive: true });
    const { envelope } = buildProgressivePublicEnvelope(input, { now: '2026-09-03T22:00:00Z' });
    assert(metric(envelope, 'genesis003-validated-through')?.value === 'C061', 'stage missing');
    assert(metric(envelope, 'genesis003-c061')?.value === 'VALIDATED_10_OF_10', 'C061 missing');
    assert(metric(envelope, 'execution-admissibility')?.value === 'BLOCKED_SYNTHETIC_SELECTION', 'gate missing');
    assert(metric(envelope, 'next-scientific-action')?.value === 'AWAIT_REAL_EXPERIMENT_SPEC', 'next action missing');
    assert(metric(envelope, 'selected-experiment-status')?.value === 'PLANNED_NOT_EXECUTED', 'execution state changed');
  }],
  ['PV2-04', 'unknown extra private/source field is rejected fail-closed', () => {
    assert(rejected(() => extractProgressiveGenesisStatus(`${C061}branch=secret\n`)), 'unknown key accepted');
  }],
  ['PV2-05', 'partial or malformed C061 state is rejected', () => {
    const bad = C061.replace('genesis003_c061=VALIDATED_10_OF_10\n', '');
    assert(rejected(() => extractProgressiveGenesisStatus(bad)), 'partial C061 accepted');
  }],
  ['PV2-06', 'C061 cannot silently become executable', () => {
    const bad = C061.replace('BLOCKED_SYNTHETIC_SELECTION', 'READY_NOT_EXECUTED');
    assert(rejected(() => extractProgressiveGenesisStatus(bad)), 'unexpected READY accepted');
  }],
  ['PV2-07', 'stale progressive source is rejected by bridge', () => {
    const status = extractProgressiveGenesisStatus(C061);
    const input = buildProgressiveBridgeInput(status, { now: '2026-09-03T22:00:00Z', liveActive: true });
    assert(rejected(() => buildProgressivePublicEnvelope(input, { now: '2026-09-03T22:10:01Z' })), 'stale source accepted');
  }],
  ['PV2-08', 'ready-not-deployed mode remains internally consistent', () => {
    const status = extractProgressiveGenesisStatus(C061);
    const input = buildProgressiveBridgeInput(status, { now: '2026-09-03T22:00:00Z', liveActive: false });
    const { envelope } = buildProgressivePublicEnvelope(input, { now: '2026-09-03T22:00:00Z' });
    assert(envelope.payload.publication_gates.current_gate === 'LIVE_READ_ONLY_BRIDGE_READY_NOT_DEPLOYED', 'ready gate');
    assert(metric(envelope, 'public-live-active')?.value === false, 'ready metric');
  }],
  ['PV2-09', 'write capability and browser credentials remain locked down', () => {
    const status = extractProgressiveGenesisStatus(C061);
    const input = buildProgressiveBridgeInput(status, { now: '2026-09-03T22:00:00Z', liveActive: true });
    const { envelope } = buildProgressivePublicEnvelope(input, { now: '2026-09-03T22:00:00Z' });
    assert(metric(envelope, 'bridge-write-capability')?.value === 'NONE', 'write capability');
    assert(metric(envelope, 'browser-private-credentials')?.value === false, 'browser credentials');
  }],
  ['PV2-10', 'public envelope contains no private repo branch path or file URL', () => {
    const status = extractProgressiveGenesisStatus(C061);
    const input = buildProgressiveBridgeInput(status, { now: '2026-09-03T22:00:00Z', liveActive: true });
    const { envelope } = buildProgressivePublicEnvelope(input, { now: '2026-09-03T22:00:00Z' });
    const text = JSON.stringify(envelope);
    for (const forbidden of ['Topbrutus/seedgenesis','public/live-source','public/live/status.env','file:///','refs/heads/']) {
      assert(!text.includes(forbidden), `leak: ${forbidden}`);
    }
  }],
];

let failed = 0;
for (const [id, name, fn] of tests) {
  try { fn(); console.log(`PASS ${id} — ${name}`); }
  catch (error) { failed += 1; console.error(`FAIL ${id} — ${name} — ${error instanceof Error ? error.message : String(error)}`); }
}
console.log(`GENESIS_PROGRESSIVE_LIVE_TESTS_PASSED=${tests.length - failed}/${tests.length}`);
console.log(`GENESIS_PROGRESSIVE_LIVE_TESTS_FAILED=${failed}`);
if (failed) process.exit(1);
