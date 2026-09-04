#!/usr/bin/env node
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  extractProgressiveGenesisStatusC072,
  buildProgressiveBridgeInputC072,
} from './build-public-source-progressive-c072.mjs';

const C073_NEW_KEYS = Object.freeze({
  genesis003_c073: 'VALIDATED_10_OF_10',
  gesis_signal_decode_adapter_contract_frozen: 'true',
  gesis_signal_decode_adapter_contract_id: 'GESIS-SIGNAL-DECODE-ADAPTER-CONTRACT-001',
  gesis_decode_adapter_input_mode: 'C072_EXACT_BYTES_AND_VALIDATED_DESCRIPTOR_IN_MEMORY_ONLY',
  gesis_decode_adapter_arraybuffer_policy: 'COPY_EXACT_BYTES_TO_NEW_ARRAYBUFFER',
  gesis_decode_runtime_dependency: 'true',
  gesis_decode_runtime_identity_required: 'true',
  gesis_decode_cross_runtime_equivalence_proven: 'false',
  gesis_decode_signal_performed: 'false',
  gesis_decode_analysis_performed: 'false',
  gesis_decode_pcm_serialization_policy: 'CHANNEL_MAJOR_FLOAT32_LITTLE_ENDIAN_IEEE754',
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

export function c073ToExactC072Text(found) {
  const copy = new Map(found);
  for (const key of Object.keys(C073_NEW_KEYS)) copy.delete(key);
  copy.set('genesis003_validated_through', 'C072');
  copy.set('next_scientific_action', 'DEFINE_GESIS_SIGNAL_DECODE_ADAPTER_CONTRACT');
  return serialize(copy);
}

function assertExactC073(found) {
  if (found.size !== 95) fail(`Projection C073 attendue sur 95 lignes; reçu ${found.size}.`);
  if (found.get('genesis003_validated_through') !== 'C073') fail('Stage C073 invalide.');
  if (found.get('next_scientific_action') !== 'VERIFY_GESIS_DECODE_ADAPTER_WITH_DETERMINISTIC_WAV_CONTROL') fail('Action C073 invalide.');

  if (
    found.get('execution_bindings_required') !== '11' ||
    found.get('execution_bindings_bound') !== '7' ||
    found.get('execution_bindings_unbound') !== '4' ||
    found.get('execution_bindings_complete') !== 'false'
  ) fail('État historique des bindings exécution C073 invalide.');

  if (
    found.get('kernel_bindings_required') !== '8' ||
    found.get('kernel_bindings_bound') !== '8' ||
    found.get('kernel_bindings_complete') !== 'true'
  ) fail('État noyau hérité invalide.');
  if (found.get('kernel_source_of_truth') !== 'SIGNAL_AND_MEASUREMENT_PROVENANCE') fail('Source de vérité noyau invalide.');
  if (found.get('provider_model_kernel_dependency') !== 'false') fail('Provider/model est redevenu dépendance noyau.');
  if (found.get('prompt_style_kernel_dependency') !== 'false') fail('Prompt/style est redevenu dépendance noyau.');
  if (found.get('real_experiment_execution_authorized') !== 'false') fail('Exécution réelle autorisée par erreur.');

  for (const [key, value] of Object.entries(C073_NEW_KEYS)) {
    if (found.get(key) !== value) fail(`Champ C073 invalide: ${key}`);
  }

  const forbidden = [
    'adapter_contract_spec_digest',
    'runtime_identity_sha256',
    'synthetic_runtime_identity_sha256',
    'handoff_descriptor_sha256',
    'synthetic_handoff_descriptor_sha256',
    'decoded_pcm_sha256',
    'gesis_commit_sha',
    'gesis_decoder_blob_sha',
    'audit_run_id',
    'audited_candidate_sha',
    'closure_sha',
    'interface_spec_digest',
    'signal_sha256',
    'provenance_sha256',
    'ingest_descriptor_sha256',
    'generator_provider',
    'model_name',
    'model_version_or_build',
    'prompt',
    'style',
    'remote_url',
    'file_path',
    'api_key',
    'authorization',
  ];
  for (const key of forbidden) if (found.has(key)) fail(`Clé privée C073 interdite: ${key}`);

  extractProgressiveGenesisStatusC072(c073ToExactC072Text(found));
}

export function extractProgressiveGenesisStatusC073(text) {
  try {
    return extractProgressiveGenesisStatusC072(text);
  } catch {
    const found = parse(text);
    assertExactC073(found);
    return {
      schema: 'GENESIS_PUBLIC_PROGRESSIVE_STATUS_V9_GESIS_DECODE_ADAPTER',
      validatedThrough: 'C073',
      values: Object.freeze(Object.fromEntries(found)),
    };
  }
}

export function buildProgressiveBridgeInputC073(status, options = {}) {
  if (status?.validatedThrough !== 'C073') return buildProgressiveBridgeInputC072(status, options);
  if (status.schema !== 'GENESIS_PUBLIC_PROGRESSIVE_STATUS_V9_GESIS_DECODE_ADAPTER') fail('Statut C073 invalide.');
  const found = new Map(Object.entries(status.values ?? {}));
  assertExactC073(found);
  const baseStatus = extractProgressiveGenesisStatusC072(c073ToExactC072Text(found));
  const base = buildProgressiveBridgeInputC072(baseStatus, options);
  return {
    ...base,
    bridge_input_version: '9.0.0',
    publication_intent: 'SERVER_SIDE_PUBLIC_READ_ONLY_PROGRESSIVE_BRIDGE_C073_GESIS_DECODE_ADAPTER',
    source_attestation: {
      ...base.source_attestation,
      source_state: 'C041_C073_GESIS_DECODE_ADAPTER_COMPLETE_VALIDATED',
      validated_through: 'C073',
      public_status: status.values,
    },
  };
}

export function assertProgressiveBridgeInputC073(input) {
  if (input?.publication_intent !== 'SERVER_SIDE_PUBLIC_READ_ONLY_PROGRESSIVE_BRIDGE_C073_GESIS_DECODE_ADAPTER') return false;
  if (input.bridge_input_version !== '9.0.0') fail('Version C073 invalide.');
  const attestation = input.source_attestation;
  if (
    !attestation ||
    attestation.validated_through !== 'C073' ||
    attestation.source_state !== 'C041_C073_GESIS_DECODE_ADAPTER_COMPLETE_VALIDATED' ||
    attestation.read_capability !== 'READ_ONLY' ||
    attestation.write_capability !== 'NONE'
  ) fail('Attestation C073 invalide.');
  assertExactC073(new Map(Object.entries(attestation.public_status ?? {})));
  return true;
}

async function main() {
  const sourcePath = process.argv[2];
  if (!sourcePath) fail('Usage: build-public-source-progressive-c073.mjs <status.env> [output.json]');
  const outputPath = process.argv[3] ?? '.build/genesis-progressive-live/bridge-input.json';
  const source = await readFile(path.resolve(sourcePath), 'utf8');
  const status = extractProgressiveGenesisStatusC073(source);
  const input = buildProgressiveBridgeInputC073(status, { liveActive: (process.env.GENESIS_PUBLIC_LIVE_ACTIVE ?? '1') === '1' });
  const resolved = path.resolve(outputPath);
  await mkdir(path.dirname(resolved), { recursive: true });
  await writeFile(resolved, `${JSON.stringify(input, null, 2)}\n`, 'utf8');
  console.log('GENESIS_PROGRESSIVE_C073_GESIS_DECODE_ADAPTER_SOURCE_VALID');
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    console.error(`GENESIS_PROGRESSIVE_C073_GESIS_DECODE_ADAPTER_SOURCE_INVALID: ${error.message}`);
    process.exit(1);
  });
}
