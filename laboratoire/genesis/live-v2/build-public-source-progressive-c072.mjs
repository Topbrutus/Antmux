#!/usr/bin/env node
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  extractProgressiveGenesisStatusC071,
  buildProgressiveBridgeInputC071,
} from './build-public-source-progressive-c071.mjs';

const C072_NEW_KEYS = Object.freeze({
  genesis003_c072: 'VALIDATED_10_OF_10',
  kernel_signal_ingest_interface_frozen: 'true',
  kernel_signal_ingest_interface_id: 'KERNEL-SIGNAL-INGEST-INTERFACE-001',
  kernel_ingest_input_mode: 'EXACT_BYTES_IN_MEMORY_ONLY',
  kernel_ingest_required_fields: '5',
  kernel_ingest_unknown_fields_allowed: 'false',
  kernel_ingest_content_addressed: 'true',
  kernel_ingest_provenance_addressed: 'true',
  kernel_ingest_transport_dependency: 'false',
  kernel_ingest_signal_decode_performed: 'false',
  kernel_ingest_gesis_execution_performed: 'false',
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

export function c072ToExactC071Text(found) {
  const copy = new Map(found);
  for (const key of Object.keys(C072_NEW_KEYS)) copy.delete(key);
  copy.set('genesis003_validated_through', 'C071');
  copy.set('next_scientific_action', 'DEFINE_KERNEL_NEUTRAL_SIGNAL_INGEST_INTERFACE');
  return serialize(copy);
}

function assertExactC072(found) {
  if (found.size !== 84) fail(`Projection C072 attendue sur 84 lignes; reçu ${found.size}.`);
  if (found.get('genesis003_validated_through') !== 'C072') fail('Stage C072 invalide.');
  if (found.get('next_scientific_action') !== 'DEFINE_GESIS_SIGNAL_DECODE_ADAPTER_CONTRACT') fail('Action C072 invalide.');

  if (
    found.get('execution_bindings_required') !== '11' ||
    found.get('execution_bindings_bound') !== '7' ||
    found.get('execution_bindings_unbound') !== '4' ||
    found.get('execution_bindings_complete') !== 'false'
  ) fail('État historique des bindings exécution C072 invalide.');

  if (
    found.get('kernel_bindings_required') !== '8' ||
    found.get('kernel_bindings_bound') !== '8' ||
    found.get('kernel_bindings_complete') !== 'true'
  ) fail('État noyau C071 hérité invalide.');
  if (found.get('kernel_source_of_truth') !== 'SIGNAL_AND_MEASUREMENT_PROVENANCE') fail('Source de vérité noyau invalide.');
  if (found.get('provider_model_kernel_dependency') !== 'false') fail('Provider/model est redevenu dépendance noyau.');
  if (found.get('prompt_style_kernel_dependency') !== 'false') fail('Prompt/style est redevenu dépendance noyau.');
  if (found.get('real_experiment_execution_authorized') !== 'false') fail('Exécution réelle autorisée par erreur.');

  for (const [key, value] of Object.entries(C072_NEW_KEYS)) {
    if (found.get(key) !== value) fail(`Champ C072 invalide: ${key}`);
  }

  const forbidden = [
    'interface_spec_digest',
    'synthetic_fixture_signal_sha256',
    'synthetic_fixture_provenance_sha256',
    'synthetic_fixture_ingest_descriptor_sha256',
    'signal_sha256',
    'provenance_sha256',
    'ingest_descriptor_sha256',
    'audit_run_id',
    'audited_candidate_sha',
    'closure_sha',
    'gesis_commit',
    'gesis_analyzer_blob',
    'generator_provider',
    'model_name',
    'model_version_or_build',
  ];
  for (const key of forbidden) if (found.has(key)) fail(`Clé privée C072 interdite: ${key}`);

  extractProgressiveGenesisStatusC071(c072ToExactC071Text(found));
}

export function extractProgressiveGenesisStatusC072(text) {
  try {
    return extractProgressiveGenesisStatusC071(text);
  } catch {
    const found = parse(text);
    assertExactC072(found);
    return {
      schema: 'GENESIS_PUBLIC_PROGRESSIVE_STATUS_V8_KERNEL_SIGNAL_INGEST',
      validatedThrough: 'C072',
      values: Object.freeze(Object.fromEntries(found)),
    };
  }
}

export function buildProgressiveBridgeInputC072(status, options = {}) {
  if (status?.validatedThrough !== 'C072') return buildProgressiveBridgeInputC071(status, options);
  if (status.schema !== 'GENESIS_PUBLIC_PROGRESSIVE_STATUS_V8_KERNEL_SIGNAL_INGEST') fail('Statut C072 invalide.');
  const found = new Map(Object.entries(status.values ?? {}));
  assertExactC072(found);
  const baseStatus = extractProgressiveGenesisStatusC071(c072ToExactC071Text(found));
  const base = buildProgressiveBridgeInputC071(baseStatus, options);
  return {
    ...base,
    bridge_input_version: '8.0.0',
    publication_intent: 'SERVER_SIDE_PUBLIC_READ_ONLY_PROGRESSIVE_BRIDGE_C072_KERNEL_SIGNAL_INGEST',
    source_attestation: {
      ...base.source_attestation,
      source_state: 'C041_C072_KERNEL_SIGNAL_INGEST_COMPLETE_VALIDATED',
      validated_through: 'C072',
      public_status: status.values,
    },
  };
}

export function assertProgressiveBridgeInputC072(input) {
  if (input?.publication_intent !== 'SERVER_SIDE_PUBLIC_READ_ONLY_PROGRESSIVE_BRIDGE_C072_KERNEL_SIGNAL_INGEST') return false;
  if (input.bridge_input_version !== '8.0.0') fail('Version C072 invalide.');
  const attestation = input.source_attestation;
  if (
    !attestation ||
    attestation.validated_through !== 'C072' ||
    attestation.source_state !== 'C041_C072_KERNEL_SIGNAL_INGEST_COMPLETE_VALIDATED' ||
    attestation.read_capability !== 'READ_ONLY' ||
    attestation.write_capability !== 'NONE'
  ) fail('Attestation C072 invalide.');
  assertExactC072(new Map(Object.entries(attestation.public_status ?? {})));
  return true;
}

async function main() {
  const sourcePath = process.argv[2];
  if (!sourcePath) fail('Usage: build-public-source-progressive-c072.mjs <status.env> [output.json]');
  const outputPath = process.argv[3] ?? '.build/genesis-progressive-live/bridge-input.json';
  const source = await readFile(path.resolve(sourcePath), 'utf8');
  const status = extractProgressiveGenesisStatusC072(source);
  const input = buildProgressiveBridgeInputC072(status, { liveActive: (process.env.GENESIS_PUBLIC_LIVE_ACTIVE ?? '1') === '1' });
  const resolved = path.resolve(outputPath);
  await mkdir(path.dirname(resolved), { recursive: true });
  await writeFile(resolved, `${JSON.stringify(input, null, 2)}\n`, 'utf8');
  console.log('GENESIS_PROGRESSIVE_C072_KERNEL_SIGNAL_INGEST_SOURCE_VALID');
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    console.error(`GENESIS_PROGRESSIVE_C072_KERNEL_SIGNAL_INGEST_SOURCE_INVALID: ${error.message}`);
    process.exit(1);
  });
}
