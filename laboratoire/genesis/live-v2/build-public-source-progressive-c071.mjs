#!/usr/bin/env node
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  extractProgressiveGenesisStatusC070,
  buildProgressiveBridgeInputC070,
} from './build-public-source-progressive-c070.mjs';

const C071_NEW_KEYS = Object.freeze({
  genesis003_c071: 'VALIDATED_10_OF_10',
  kernel_signal_contract_frozen: 'true',
  kernel_source_of_truth: 'SIGNAL_AND_MEASUREMENT_PROVENANCE',
  kernel_bindings_required: '8',
  kernel_bindings_bound: '8',
  kernel_bindings_complete: 'true',
  external_generation_metadata_required_by_kernel: 'false',
  prompt_style_kernel_dependency: 'false',
  real_experiment_execution_authorized: 'false',
  historical_execution_contract_policy: 'IMMUTABLE_HISTORY_NOT_KERNEL_SOURCE_OF_TRUTH',
});

function fail(message) { throw new Error(message); }
function parse(text) {
  const found = new Map();
  for (const raw of text.split(/\r?\n/)) {
    if (!raw) continue;
    const match = raw.match(/^([A-Za-z0-9_]+)=(.*)$/);
    if (!match) fail(`Ligne invalide: ${raw}`);
    if (found.has(match[1])) fail(`Clé dupliquée: ${match[1]}`);
    found.set(match[1], match[2]);
  }
  return found;
}
function serialize(found) {
  return `${[...found].map(([key, value]) => `${key}=${value}`).join('\n')}\n`;
}

export function c071ToExactC070Text(found) {
  const copy = new Map(found);
  for (const key of Object.keys(C071_NEW_KEYS)) copy.delete(key);
  copy.set('genesis003_validated_through', 'C070');
  copy.set('next_scientific_action', 'FREEZE_REMAINING_GENERATION_IO_BINDINGS');
  return serialize(copy);
}

function assertExactC071(found) {
  if (found.size !== 73) fail(`Projection C071 attendue sur 73 lignes; reçu ${found.size}.`);
  if (found.get('genesis003_validated_through') !== 'C071') fail('Stage C071 invalide.');
  if (found.get('next_scientific_action') !== 'DEFINE_KERNEL_NEUTRAL_SIGNAL_INGEST_INTERFACE') fail('Action C071 invalide.');

  // Historical real-execution contract remains historical and incomplete.
  if (
    found.get('execution_bindings_required') !== '11' ||
    found.get('execution_bindings_bound') !== '7' ||
    found.get('execution_bindings_unbound') !== '4' ||
    found.get('execution_bindings_complete') !== 'false'
  ) fail('État historique des bindings exécution C071 invalide.');

  if (found.get('analysis_decision_rule_bound') !== 'true') fail('Règle C070 héritée non liée.');
  if (found.get('measurement_qc_rule_frozen') !== 'true') fail('Règle QC C070 héritée non gelée.');
  if (found.get('provider_model_kernel_dependency') !== 'false') fail('Provider/model est redevenu dépendance noyau.');

  for (const [key, value] of Object.entries(C071_NEW_KEYS)) {
    if (found.get(key) !== value) fail(`Champ C071 invalide: ${key}`);
  }

  const forbidden = [
    'kernel_contract_digest',
    'signal_sha256',
    'gesis_commit',
    'gesis_analyzer_blob',
    'gesis_configuration_sha256',
    'analysis_decision_rule_sha256',
    'measurement_digest_sha256',
    'audit_run_id',
    'generator_provider',
    'model_name',
    'model_version_or_build',
  ];
  for (const key of forbidden) if (found.has(key)) fail(`Clé privée C071 interdite: ${key}`);

  extractProgressiveGenesisStatusC070(c071ToExactC070Text(found));
}

export function extractProgressiveGenesisStatusC071(text) {
  try {
    return extractProgressiveGenesisStatusC070(text);
  } catch {
    const found = parse(text);
    assertExactC071(found);
    return {
      schema: 'GENESIS_PUBLIC_PROGRESSIVE_STATUS_V7_KERNEL_SIGNAL_CONTRACT',
      validatedThrough: 'C071',
      values: Object.freeze(Object.fromEntries(found)),
    };
  }
}

export function buildProgressiveBridgeInputC071(status, options = {}) {
  if (status?.validatedThrough !== 'C071') return buildProgressiveBridgeInputC070(status, options);
  if (status.schema !== 'GENESIS_PUBLIC_PROGRESSIVE_STATUS_V7_KERNEL_SIGNAL_CONTRACT') fail('Statut C071 invalide.');
  const found = new Map(Object.entries(status.values ?? {}));
  assertExactC071(found);
  const baseStatus = extractProgressiveGenesisStatusC070(c071ToExactC070Text(found));
  const base = buildProgressiveBridgeInputC070(baseStatus, options);
  return {
    ...base,
    bridge_input_version: '7.0.0',
    publication_intent: 'SERVER_SIDE_PUBLIC_READ_ONLY_PROGRESSIVE_BRIDGE_C071_KERNEL_SIGNAL_CONTRACT',
    source_attestation: {
      ...base.source_attestation,
      source_state: 'C041_C071_KERNEL_SIGNAL_CONTRACT_COMPLETE_VALIDATED',
      validated_through: 'C071',
      public_status: status.values,
    },
  };
}

export function assertProgressiveBridgeInputC071(input) {
  if (input?.publication_intent !== 'SERVER_SIDE_PUBLIC_READ_ONLY_PROGRESSIVE_BRIDGE_C071_KERNEL_SIGNAL_CONTRACT') return false;
  if (input.bridge_input_version !== '7.0.0') fail('Version C071 invalide.');
  const attestation = input.source_attestation;
  if (
    !attestation ||
    attestation.validated_through !== 'C071' ||
    attestation.source_state !== 'C041_C071_KERNEL_SIGNAL_CONTRACT_COMPLETE_VALIDATED' ||
    attestation.read_capability !== 'READ_ONLY' ||
    attestation.write_capability !== 'NONE'
  ) fail('Attestation C071 invalide.');
  assertExactC071(new Map(Object.entries(attestation.public_status ?? {})));
  return true;
}

async function main() {
  const sourcePath = process.argv[2];
  if (!sourcePath) fail('Usage: build-public-source-progressive-c071.mjs <status.env> [output.json]');
  const outputPath = process.argv[3] ?? '.build/genesis-progressive-live/bridge-input.json';
  const source = await readFile(path.resolve(sourcePath), 'utf8');
  const status = extractProgressiveGenesisStatusC071(source);
  const input = buildProgressiveBridgeInputC071(status, { liveActive: (process.env.GENESIS_PUBLIC_LIVE_ACTIVE ?? '1') === '1' });
  const resolved = path.resolve(outputPath);
  await mkdir(path.dirname(resolved), { recursive: true });
  await writeFile(resolved, `${JSON.stringify(input, null, 2)}\n`, 'utf8');
  console.log('GENESIS_PROGRESSIVE_C071_KERNEL_SIGNAL_SOURCE_VALID');
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    console.error(`GENESIS_PROGRESSIVE_C071_KERNEL_SIGNAL_SOURCE_INVALID: ${error.message}`);
    process.exit(1);
  });
}
