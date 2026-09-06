#!/usr/bin/env node
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  extractProgressiveGenesisStatusC074,
  buildProgressiveBridgeInputC074,
} from './build-public-source-progressive-c074.mjs';

const C081_NEW_KEYS = Object.freeze({
  c080_status: 'PREEXECUTION_BLOCKED',
  c080_scientific_decode_count: '0',
  c080_scientific_verdict_issued: 'false',
  c080_prediction_verdict: 'NONE',
  genesis003_c081: 'VALIDATED_MEASURED_INCONCLUSIVE',
  c081_claim_class: 'MEASURED',
  c081_status: 'VALIDATED_MEASURED_INCONCLUSIVE',
  c081_scientific_outcome: 'INCONCLUSIVE_RUNTIME_OR_EXECUTION_NOT_ESTABLISHED',
  c081_hypothesis_status: 'UNRESOLVED_INCONCLUSIVE',
  c081_primary_hypothesis_tested: 'false',
  c081_prediction_verdict: 'NONE',
  c081_prediction_comparison_count: '0',
  c081_planned_scientific_decode_count: '36',
  c081_final_scientific_decode_count: '18',
  c081_firefox_decode_count: '18',
  c081_chrome_decode_count: '0',
  c081_prediction_promotion_performed: 'false',
  c081_post_observation_retry: 'false',
  c082_started: 'false',
});
const POST_C074_KEYS = Object.freeze({
  post_c074_runtime_identity_sample_rate_binding: 'VALIDATED',
  post_c074_claim_class: 'MEASURED',
  post_c074_audio_context_sample_rate_hz: '44100',
  post_c074_same_runtime_repeatability: 'true',
  post_c074_sample_rate_tamper_changes_identity: 'true',
  post_c074_invalid_sample_rates_fail_closed: 'true',
  post_c074_historical_c074_verdict_preserved: 'true',
  post_c074_cross_runtime_decode_equivalence_proven: 'false',
  post_c074_real_experiment_executed: 'false',
  post_c074_experimental_audio_generated: 'false',
  post_c074_external_model_or_api_used: 'false',
  c075_started: 'false',
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

export function c081ToExactC074Text(found) {
  const copy = new Map(found);
  for (const key of Object.keys(POST_C074_KEYS)) copy.delete(key);
  for (const key of Object.keys(C081_NEW_KEYS)) copy.delete(key);
  copy.set('genesis003_validated_through', 'C074');
  copy.set('next_scientific_action', 'BIND_AUDIO_CONTEXT_SAMPLE_RATE_IN_DECODE_RUNTIME_IDENTITY');
  return serialize(copy);
}

function assertExactPostC074Fallback(found) {
  if (found.size !== 121) fail(`Projection post-C074 attendue sur 121 lignes; reçu ${found.size}.`);
  if (found.get('genesis003_validated_through') !== 'C074') fail('Stage post-C074 invalide.');
  if (found.get('next_scientific_action') !== 'DEFINE_C075_SCIENTIFIC_STAGE') fail('Action post-C074 invalide.');
  for (const [key, value] of Object.entries(POST_C074_KEYS)) {
    if (found.get(key) !== value) fail(`Champ post-C074 invalide: ${key}`);
  }
  extractProgressiveGenesisStatusC074(c081ToExactC074Text(found));
}

function assertExactC081(found) {
  if (found.size !== 140) fail(`Projection C081 attendue sur 140 lignes; reçu ${found.size}.`);
  if (found.get('genesis003_validated_through') !== 'C081') fail('Stage C081 invalide.');
  if (found.get('next_scientific_action') !== 'NONE_AUTHORIZED_C082_NOT_STARTED') fail('Action C081 invalide.');
  if (
    found.get('kernel_bindings_required') !== '8' ||
    found.get('kernel_bindings_bound') !== '8' ||
    found.get('kernel_bindings_complete') !== 'true'
  ) fail('État noyau C081 invalide.');
  for (const [key, value] of Object.entries(C081_NEW_KEYS)) {
    if (found.get(key) !== value) fail(`Champ C081 invalide: ${key}`);
  }
  for (const [key, value] of Object.entries(POST_C074_KEYS)) {
    if (found.get(key) !== value) fail(`Champ post-C074 invalide: ${key}`);
  }
  for (const key of ['c081_status', 'c081_scientific_outcome', 'c081_hypothesis_status', 'c081_prediction_verdict']) {
    if (['SUCCESS', 'FAIL', 'CONFIRMED', 'REFUTED', 'null'].includes(found.get(key))) fail(`Verdict C081 interdit: ${key}`);
  }
  if (found.get('c074_verification_verdict') !== 'FAIL_RUNTIME_DECODE_TRANSFORM') fail('Le verdict C074 historique a été modifié.');
  const forbidden = [
    'measurement_record_digest',
    'runtime_identity_sha256',
    'ingest_descriptor_sha256',
    'handoff_descriptor_sha256',
    'decoded_pcm_sha256',
    'receipt_sha256',
    'gesis_commit_sha',
    'gesis_decoder_blob_sha',
    'audit_run_id',
    'gesis_harness_run_id',
    'audited_candidate_sha',
    'closure_sha',
    'artifact_id',
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
  for (const key of forbidden) if (found.has(key)) fail(`Clé privée C081 interdite: ${key}`);
  extractProgressiveGenesisStatusC074(c081ToExactC074Text(found));
}

export function extractProgressiveGenesisStatusC081(text) {
  try {
    return extractProgressiveGenesisStatusC074(text);
  } catch {
    const found = parse(text);
    if (found.size === 121) {
      assertExactPostC074Fallback(found);
      return extractProgressiveGenesisStatusC074(c081ToExactC074Text(found));
    }
    assertExactC081(found);
    return {
      schema: 'GENESIS_PUBLIC_PROGRESSIVE_STATUS_V11_C081_MEASURED_INCONCLUSIVE',
      validatedThrough: 'C081',
      values: Object.freeze(Object.fromEntries(found)),
    };
  }
}

export function buildProgressiveBridgeInputC081(status, options = {}) {
  if (status?.validatedThrough !== 'C081') return buildProgressiveBridgeInputC074(status, options);
  if (status.schema !== 'GENESIS_PUBLIC_PROGRESSIVE_STATUS_V11_C081_MEASURED_INCONCLUSIVE') fail('Statut C081 invalide.');
  const found = new Map(Object.entries(status.values ?? {}));
  assertExactC081(found);
  const baseStatus = extractProgressiveGenesisStatusC074(c081ToExactC074Text(found));
  const base = buildProgressiveBridgeInputC074(baseStatus, options);
  return {
    ...base,
    bridge_input_version: '11.0.0',
    publication_intent: 'SERVER_SIDE_PUBLIC_READ_ONLY_PROGRESSIVE_BRIDGE_C081_MEASURED_INCONCLUSIVE',
    source_attestation: {
      ...base.source_attestation,
      source_state: 'C041_C081_MEASURED_INCONCLUSIVE_PUBLIC_HEALTH_VALIDATED',
      validated_through: 'C081',
      next_scientific_action: 'NONE_AUTHORIZED_C082_NOT_STARTED',
      public_status: status.values,
    },
  };
}

export function assertProgressiveBridgeInputC081(input) {
  if (input?.publication_intent !== 'SERVER_SIDE_PUBLIC_READ_ONLY_PROGRESSIVE_BRIDGE_C081_MEASURED_INCONCLUSIVE') return false;
  if (input.bridge_input_version !== '11.0.0') fail('Version C081 invalide.');
  const attestation = input.source_attestation;
  if (
    !attestation ||
    attestation.validated_through !== 'C081' ||
    attestation.source_state !== 'C041_C081_MEASURED_INCONCLUSIVE_PUBLIC_HEALTH_VALIDATED' ||
    attestation.read_capability !== 'READ_ONLY' ||
    attestation.write_capability !== 'NONE'
  ) fail('Attestation C081 invalide.');
  assertExactC081(new Map(Object.entries(attestation.public_status ?? {})));
  return true;
}

async function main() {
  const sourcePath = process.argv[2];
  if (!sourcePath) fail('Usage: build-public-source-progressive-c081.mjs <status.env> [output.json]');
  const outputPath = process.argv[3] ?? '.build/genesis-progressive-live/bridge-input.json';
  const source = await readFile(path.resolve(sourcePath), 'utf8');
  const status = extractProgressiveGenesisStatusC081(source);
  const input = buildProgressiveBridgeInputC081(status, { liveActive: (process.env.GENESIS_PUBLIC_LIVE_ACTIVE ?? '1') === '1' });
  const resolved = path.resolve(outputPath);
  await mkdir(path.dirname(resolved), { recursive: true });
  await writeFile(resolved, `${JSON.stringify(input, null, 2)}\n`, 'utf8');
  console.log('GENESIS_PROGRESSIVE_C081_MEASURED_INCONCLUSIVE_SOURCE_VALID');
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    console.error(`GENESIS_PROGRESSIVE_C081_MEASURED_INCONCLUSIVE_SOURCE_INVALID: ${error.message}`);
    process.exit(1);
  });
}
