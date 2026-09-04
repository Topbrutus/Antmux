#!/usr/bin/env node
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  extractProgressiveGenesisStatusC073,
  buildProgressiveBridgeInputC073,
} from './build-public-source-progressive-c073.mjs';

const C074_NEW_KEYS = Object.freeze({
  genesis003_c074: 'VALIDATED_10_OF_10',
  c074_claim_class: 'MEASURED',
  c074_control_wav_verified: 'true',
  c074_control_encoded_sample_rate_hz: '48000',
  c074_runtime_audio_context_sample_rate_hz: '44100',
  c074_decoded_sample_rate_hz: '44100',
  c074_decoded_frame_length: '44099',
  c074_repeated_decode_receipt_match: 'true',
  c074_verification_verdict: 'FAIL_RUNTIME_DECODE_TRANSFORM',
  c074_finding: 'AUDIO_CONTEXT_SAMPLE_RATE_TRANSFORM_DETECTED',
  c074_cross_runtime_decode_equivalence_proven: 'false',
  c074_real_experiment_executed: 'false',
  c074_experimental_audio_generated: 'false',
  c074_external_model_or_api_used: 'false',
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

export function c074ToExactC073Text(found) {
  const copy = new Map(found);
  for (const key of Object.keys(C074_NEW_KEYS)) copy.delete(key);
  copy.set('genesis003_validated_through', 'C073');
  copy.set('next_scientific_action', 'VERIFY_GESIS_DECODE_ADAPTER_WITH_DETERMINISTIC_WAV_CONTROL');
  return serialize(copy);
}

function assertExactC074(found) {
  if (found.size !== 109) fail(`Projection C074 attendue sur 109 lignes; reçu ${found.size}.`);
  if (found.get('genesis003_validated_through') !== 'C074') fail('Stage C074 invalide.');
  if (found.get('next_scientific_action') !== 'BIND_AUDIO_CONTEXT_SAMPLE_RATE_IN_DECODE_RUNTIME_IDENTITY') fail('Action C074 invalide.');

  if (
    found.get('execution_bindings_required') !== '11' ||
    found.get('execution_bindings_bound') !== '7' ||
    found.get('execution_bindings_unbound') !== '4' ||
    found.get('execution_bindings_complete') !== 'false'
  ) fail('État historique des bindings exécution C074 invalide.');

  if (
    found.get('kernel_bindings_required') !== '8' ||
    found.get('kernel_bindings_bound') !== '8' ||
    found.get('kernel_bindings_complete') !== 'true'
  ) fail('État noyau hérité invalide.');
  if (found.get('kernel_source_of_truth') !== 'SIGNAL_AND_MEASUREMENT_PROVENANCE') fail('Source de vérité noyau invalide.');
  if (found.get('provider_model_kernel_dependency') !== 'false') fail('Provider/model est redevenu dépendance noyau.');
  if (found.get('prompt_style_kernel_dependency') !== 'false') fail('Prompt/style est redevenu dépendance noyau.');
  if (found.get('real_experiment_execution_authorized') !== 'false') fail('Exécution réelle autorisée par erreur.');

  for (const [key, value] of Object.entries(C074_NEW_KEYS)) {
    if (found.get(key) !== value) fail(`Champ C074 invalide: ${key}`);
  }

  if (found.get('c074_verification_verdict') === 'PASS_EXACT_REFERENCE') fail('Le verdict négatif C074 a été réécrit en succès.');
  if (found.get('c074_claim_class') !== 'MEASURED') fail('Classe épistémique C074 invalide.');

  const forbidden = [
    'measurement_record_digest',
    'runtime_identity_sha256',
    'ingest_descriptor_sha256',
    'handoff_descriptor_sha256',
    'decoded_pcm_sha256',
    'naive_reference_pcm_sha256',
    'receipt_sha256',
    'gesis_commit_sha',
    'gesis_decoder_blob_sha',
    'audit_run_id',
    'gesis_harness_run_id',
    'audited_candidate_sha',
    'closure_sha',
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
  for (const key of forbidden) if (found.has(key)) fail(`Clé privée C074 interdite: ${key}`);

  extractProgressiveGenesisStatusC073(c074ToExactC073Text(found));
}

export function extractProgressiveGenesisStatusC074(text) {
  try {
    return extractProgressiveGenesisStatusC073(text);
  } catch {
    const found = parse(text);
    assertExactC074(found);
    return {
      schema: 'GENESIS_PUBLIC_PROGRESSIVE_STATUS_V10_C074_MEASURED_RUNTIME_TRANSFORM',
      validatedThrough: 'C074',
      values: Object.freeze(Object.fromEntries(found)),
    };
  }
}

export function buildProgressiveBridgeInputC074(status, options = {}) {
  if (status?.validatedThrough !== 'C074') return buildProgressiveBridgeInputC073(status, options);
  if (status.schema !== 'GENESIS_PUBLIC_PROGRESSIVE_STATUS_V10_C074_MEASURED_RUNTIME_TRANSFORM') fail('Statut C074 invalide.');
  const found = new Map(Object.entries(status.values ?? {}));
  assertExactC074(found);
  const baseStatus = extractProgressiveGenesisStatusC073(c074ToExactC073Text(found));
  const base = buildProgressiveBridgeInputC073(baseStatus, options);
  return {
    ...base,
    bridge_input_version: '10.0.0',
    publication_intent: 'SERVER_SIDE_PUBLIC_READ_ONLY_PROGRESSIVE_BRIDGE_C074_MEASURED_RUNTIME_TRANSFORM',
    source_attestation: {
      ...base.source_attestation,
      source_state: 'C041_C074_MEASURED_RUNTIME_TRANSFORM_COMPLETE_VALIDATED',
      validated_through: 'C074',
      public_status: status.values,
    },
  };
}

export function assertProgressiveBridgeInputC074(input) {
  if (input?.publication_intent !== 'SERVER_SIDE_PUBLIC_READ_ONLY_PROGRESSIVE_BRIDGE_C074_MEASURED_RUNTIME_TRANSFORM') return false;
  if (input.bridge_input_version !== '10.0.0') fail('Version C074 invalide.');
  const attestation = input.source_attestation;
  if (
    !attestation ||
    attestation.validated_through !== 'C074' ||
    attestation.source_state !== 'C041_C074_MEASURED_RUNTIME_TRANSFORM_COMPLETE_VALIDATED' ||
    attestation.read_capability !== 'READ_ONLY' ||
    attestation.write_capability !== 'NONE'
  ) fail('Attestation C074 invalide.');
  assertExactC074(new Map(Object.entries(attestation.public_status ?? {})));
  return true;
}

async function main() {
  const sourcePath = process.argv[2];
  if (!sourcePath) fail('Usage: build-public-source-progressive-c074.mjs <status.env> [output.json]');
  const outputPath = process.argv[3] ?? '.build/genesis-progressive-live/bridge-input.json';
  const source = await readFile(path.resolve(sourcePath), 'utf8');
  const status = extractProgressiveGenesisStatusC074(source);
  const input = buildProgressiveBridgeInputC074(status, { liveActive: (process.env.GENESIS_PUBLIC_LIVE_ACTIVE ?? '1') === '1' });
  const resolved = path.resolve(outputPath);
  await mkdir(path.dirname(resolved), { recursive: true });
  await writeFile(resolved, `${JSON.stringify(input, null, 2)}\n`, 'utf8');
  console.log('GENESIS_PROGRESSIVE_C074_MEASURED_RUNTIME_TRANSFORM_SOURCE_VALID');
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    console.error(`GENESIS_PROGRESSIVE_C074_MEASURED_RUNTIME_TRANSFORM_SOURCE_INVALID: ${error.message}`);
    process.exit(1);
  });
}
