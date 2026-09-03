#!/usr/bin/env node
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const LEGACY_EXPECTED = Object.freeze({
  science_baseline: 'GREEN',
  genesis003_c041_c060: 'COMPLETE_VALIDATED',
  experiment_selection_performed: 'true',
  selected_experiment_status: 'PLANNED_NOT_EXECUTED',
  hypothesis_selection_performed: 'false',
  hypothesis_ranking_produced: 'false',
  uncertainty_promotion_performed: 'false',
  probabilities_produced: 'false',
  evidence_ledger_auto_promotion: 'false',
  GENESIS_AUDIT_FAILED: '0',
});

const C061_EXPECTED = Object.freeze({
  ...LEGACY_EXPECTED,
  genesis003_validated_through: 'C061',
  genesis003_c061: 'VALIDATED_10_OF_10',
  c061_execution_input: 'SYNTHETIC_C060_FIXTURE',
  execution_admissibility: 'BLOCKED_SYNTHETIC_SELECTION',
  next_scientific_action: 'AWAIT_REAL_EXPERIMENT_SPEC',
});

const C062_EXPECTED = Object.freeze({
  ...C061_EXPECTED,
  genesis003_validated_through: 'C062',
  next_scientific_action: 'BUILD_REAL_NEXT_TEST_PLAN',
  genesis003_c062: 'VALIDATED_10_OF_10',
  real_experiment_spec_id: 'REAL-EXPERIMENT-SPEC-001',
  real_experiment_spec_status: 'FROZEN_CANDIDATE_NOT_SELECTED',
  real_experiment_family: 'BLIND_MULTILINGUAL_GESIS_COMPARISON',
  trial_class: 'PILOT_COMPARATIVE_NOT_CONFIRMATORY',
  replicates_per_arm: '3',
  blinded_primary_analysis: 'true',
  pretargeted_symbolic_search: 'false',
  real_plan_selection_performed: 'false',
});

function fail(message) { throw new Error(message); }

function parseExactStatus(text) {
  if (typeof text !== 'string' || text.length === 0) fail('Source Genesis absente.');
  const found = new Map();
  for (const raw of text.split(/\r?\n/)) {
    if (!raw) continue;
    const match = raw.match(/^([A-Za-z0-9_]+)=(.*)$/);
    if (!match) fail(`Ligne de statut invalide: ${raw}.`);
    const [, key, value] = match;
    if (found.has(key)) fail(`Clé dupliquée: ${key}.`);
    found.set(key, value);
  }
  return found;
}

function matchesExact(found, expected) {
  const expectedKeys = Object.keys(expected);
  if (found.size !== expectedKeys.length) return false;
  return expectedKeys.every((key) => found.get(key) === expected[key]);
}

function emptyC062Fields() {
  return {
    c062Status: 'NOT_APPLICABLE',
    realExperimentSpecId: 'NOT_APPLICABLE',
    realExperimentSpecStatus: 'NOT_APPLICABLE',
    realExperimentFamily: 'NOT_APPLICABLE',
    trialClass: 'NOT_APPLICABLE',
    replicatesPerArm: null,
    blindedPrimaryAnalysis: null,
    pretargetedSymbolicSearch: null,
    realPlanSelectionPerformed: null,
  };
}

export function extractProgressiveGenesisStatus(text) {
  const found = parseExactStatus(text);
  if (matchesExact(found, LEGACY_EXPECTED)) {
    return {
      schema: 'GENESIS_PUBLIC_PROGRESSIVE_STATUS_V2',
      validatedThrough: 'C060',
      c061Status: 'NOT_APPLICABLE',
      c061ExecutionInput: 'NOT_APPLICABLE',
      executionAdmissibility: 'NOT_APPLICABLE',
      nextScientificAction: 'AWAIT_EXPLICIT_NEW_PHASE',
      selectedExperimentStatus: found.get('selected_experiment_status'),
      ...emptyC062Fields(),
    };
  }
  if (matchesExact(found, C061_EXPECTED)) {
    return {
      schema: 'GENESIS_PUBLIC_PROGRESSIVE_STATUS_V2',
      validatedThrough: 'C061',
      c061Status: found.get('genesis003_c061'),
      c061ExecutionInput: found.get('c061_execution_input'),
      executionAdmissibility: found.get('execution_admissibility'),
      nextScientificAction: found.get('next_scientific_action'),
      selectedExperimentStatus: found.get('selected_experiment_status'),
      ...emptyC062Fields(),
    };
  }
  if (matchesExact(found, C062_EXPECTED)) {
    return {
      schema: 'GENESIS_PUBLIC_PROGRESSIVE_STATUS_V2',
      validatedThrough: 'C062',
      c061Status: found.get('genesis003_c061'),
      c061ExecutionInput: found.get('c061_execution_input'),
      executionAdmissibility: found.get('execution_admissibility'),
      nextScientificAction: found.get('next_scientific_action'),
      selectedExperimentStatus: found.get('selected_experiment_status'),
      c062Status: found.get('genesis003_c062'),
      realExperimentSpecId: found.get('real_experiment_spec_id'),
      realExperimentSpecStatus: found.get('real_experiment_spec_status'),
      realExperimentFamily: found.get('real_experiment_family'),
      trialClass: found.get('trial_class'),
      replicatesPerArm: Number(found.get('replicates_per_arm')),
      blindedPrimaryAnalysis: found.get('blinded_primary_analysis') === 'true',
      pretargetedSymbolicSearch: found.get('pretargeted_symbolic_search') === 'true',
      realPlanSelectionPerformed: found.get('real_plan_selection_performed') === 'true',
    };
  }
  const keys = [...found.keys()].sort().join(',');
  fail(`Statut Genesis non autorisé par le contrat progressif; keys=${keys}.`);
}

export function buildProgressiveBridgeInput(status, options = {}) {
  if (status?.schema !== 'GENESIS_PUBLIC_PROGRESSIVE_STATUS_V2') fail('Statut progressif invalide.');
  if (!['C060', 'C061', 'C062'].includes(status.validatedThrough)) fail('validatedThrough non autorisé.');

  const now = new Date(options.now ?? Date.now());
  if (Number.isNaN(now.getTime())) fail('Horodatage invalide.');
  const liveActive = options.liveActive !== false;
  const state = {
    C060: 'C041_C060_COMPLETE_VALIDATED',
    C061: 'C041_C061_COMPLETE_VALIDATED',
    C062: 'C041_C062_COMPLETE_VALIDATED',
  }[status.validatedThrough];

  return {
    bridge_input_version: '2.0.0',
    publication_intent: 'SERVER_SIDE_PUBLIC_READ_ONLY_PROGRESSIVE_BRIDGE',
    bridge_received_at: now.toISOString(),
    source_observed_at: now.toISOString(),
    max_age_seconds: 300,
    source_attestation: {
      source_kind: 'PRIVATE_GENESIS_PUBLIC_PROJECTION',
      source_identity: 'OPAQUE_PUBLIC_ATTESTATION',
      source_state: state,
      validated_through: status.validatedThrough,
      c061_status: status.c061Status,
      c061_execution_input: status.c061ExecutionInput,
      execution_admissibility: status.executionAdmissibility,
      next_scientific_action: status.nextScientificAction,
      selected_experiment_status: status.selectedExperimentStatus,
      c062_status: status.c062Status,
      real_experiment_spec_id: status.realExperimentSpecId,
      real_experiment_spec_status: status.realExperimentSpecStatus,
      real_experiment_family: status.realExperimentFamily,
      trial_class: status.trialClass,
      replicates_per_arm: status.replicatesPerArm,
      blinded_primary_analysis: status.blindedPrimaryAnalysis,
      pretargeted_symbolic_search: status.pretargetedSymbolicSearch,
      real_plan_selection_performed: status.realPlanSelectionPerformed,
      read_capability: 'READ_ONLY',
      write_capability: 'NONE',
      adapter_only: true,
    },
    transport: {
      server_side_pull: true,
      public_endpoint_only: true,
      fail_closed: true,
      snapshot_fallback_available: true,
      browser_credentials_present: false,
      private_browser_request: false,
    },
    live_active: liveActive,
  };
}

async function main() {
  const sourcePath = process.argv[2];
  if (!sourcePath) fail('Usage: build-public-source-progressive.mjs <status.env> [output.json]');
  const outputPath = process.argv[3] ?? '.build/genesis-progressive-live/bridge-input.json';
  const source = await readFile(path.resolve(sourcePath), 'utf8');
  const status = extractProgressiveGenesisStatus(source);
  const liveFlag = process.env.GENESIS_PUBLIC_LIVE_ACTIVE ?? '1';
  if (!['0', '1'].includes(liveFlag)) fail('GENESIS_PUBLIC_LIVE_ACTIVE doit être 0 ou 1.');
  const input = buildProgressiveBridgeInput(status, { liveActive: liveFlag === '1' });
  const resolved = path.resolve(outputPath);
  await mkdir(path.dirname(resolved), { recursive: true });
  await writeFile(resolved, `${JSON.stringify(input, null, 2)}\n`, 'utf8');
  console.log('GENESIS_PROGRESSIVE_PRIVATE_SOURCE_VALID');
  console.log(JSON.stringify({
    validated_through: input.source_attestation.validated_through,
    execution_admissibility: input.source_attestation.execution_admissibility,
    next_scientific_action: input.source_attestation.next_scientific_action,
    real_experiment_spec_status: input.source_attestation.real_experiment_spec_status,
    private_identifiers_projected: false,
  }, null, 2));
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    console.error(`GENESIS_PROGRESSIVE_PRIVATE_SOURCE_INVALID: ${error.message}`);
    process.exit(1);
  });
}
