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
    };
  }
  const keys = [...found.keys()].sort().join(',');
  fail(`Statut Genesis non autorisé par le contrat progressif; keys=${keys}.`);
}

export function buildProgressiveBridgeInput(status, options = {}) {
  if (status?.schema !== 'GENESIS_PUBLIC_PROGRESSIVE_STATUS_V2') fail('Statut progressif invalide.');
  if (!['C060', 'C061'].includes(status.validatedThrough)) fail('validatedThrough non autorisé.');

  const now = new Date(options.now ?? Date.now());
  if (Number.isNaN(now.getTime())) fail('Horodatage invalide.');
  const liveActive = options.liveActive !== false;

  return {
    bridge_input_version: '2.0.0',
    publication_intent: 'SERVER_SIDE_PUBLIC_READ_ONLY_PROGRESSIVE_BRIDGE',
    bridge_received_at: now.toISOString(),
    source_observed_at: now.toISOString(),
    max_age_seconds: 300,
    source_attestation: {
      source_kind: 'PRIVATE_GENESIS_PUBLIC_PROJECTION',
      source_identity: 'OPAQUE_PUBLIC_ATTESTATION',
      source_state: status.validatedThrough === 'C061' ? 'C041_C061_COMPLETE_VALIDATED' : 'C041_C060_COMPLETE_VALIDATED',
      validated_through: status.validatedThrough,
      c061_status: status.c061Status,
      c061_execution_input: status.c061ExecutionInput,
      execution_admissibility: status.executionAdmissibility,
      next_scientific_action: status.nextScientificAction,
      selected_experiment_status: status.selectedExperimentStatus,
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
    private_identifiers_projected: false,
  }, null, 2));
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    console.error(`GENESIS_PROGRESSIVE_PRIVATE_SOURCE_INVALID: ${error.message}`);
    process.exit(1);
  });
}
