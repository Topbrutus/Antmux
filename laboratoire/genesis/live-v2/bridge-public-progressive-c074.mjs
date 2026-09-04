#!/usr/bin/env node
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { validatePublicV2 } from '../validate-public-v2.mjs';
import { buildProgressivePublicEnvelopeC073 } from './bridge-public-progressive-c073.mjs';
import {
  assertProgressiveBridgeInputC074,
  c074ToExactC073Text,
} from './build-public-source-progressive-c074.mjs';
import {
  extractProgressiveGenesisStatusC073,
  buildProgressiveBridgeInputC073,
} from './build-public-source-progressive-c073.mjs';

function fail(message) { throw new Error(message); }
function stable(value) {
  if (Array.isArray(value)) return value.map(stable);
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.keys(value).sort().map((key) => [key, stable(value[key])]));
  }
  return value;
}
function digestPayload(payload, observedAt) {
  return createHash('sha256').update(JSON.stringify(stable({ observed_at: observedAt, payload })), 'utf8').digest('hex');
}
function metric(id, label, value) {
  return { id, label, value, status: 'VERIFIED_PUBLIC', provenance_ref: 'SERVER-SIDE-WHITELIST-V10-C074-MEASURED-RUNTIME-TRANSFORM' };
}
function byId(metrics, id) {
  const found = metrics.find((entry) => entry.id === id);
  if (!found) fail(`Metric manquante: ${id}`);
  return found;
}
function scanPrivate(value) {
  const text = JSON.stringify(value);
  const forbidden = [
    'Topbrutus/seedgenesis',
    'Topbrutus/gesis',
    '84582b2a7c53c7c51d4b7a18ac6650365135e8e1',
    'e4db07078b95e743c57a8ac322958d636087f8ad',
    'c6532a7806de59c78268cc0e36e5cd48906031ed',
    'e5865c110509d98c80bf88ee9f73282ddb608185e39cde1e49c84e3786706858',
    'c1d6aeb247e61e5fbc5575bf251c8331c6bdfe4784b68065a3d6ad50b9ffe7bc',
    '07a53c7ed515c93ea16aa4e78b46222404e3614bd171d1eca662d0c3a945a66d',
    '50b8e3153a4f6d8b8ec5660a3d8e06106f132be367ca8bf279524a6fce7e29e8',
    '33db943f9eb42fd277084f4f945ae7e4d7a088ca7fd008847b1a73f0206734a9',
    '6bf952c076f93e57d45e8305d696c54c8907b76e513e076924ae8bac5db679de',
    'c4df37399dca258ce61f568b71bcabb4d01c069d3ae94409094412f65fbf977a',
    '6c8256a5fcb7a11b44f519880eb792f936f44f49',
    '8b97673a2228af397fa949bf5f7921c8cdc54be4',
    'measurement_record_digest',
    'runtime_identity_sha256',
    'ingest_descriptor_sha256',
    'handoff_descriptor_sha256',
    'decoded_pcm_sha256',
    'naive_reference_pcm_sha256',
    'receipt_sha256',
    'gesis_commit_sha',
    'gesis_decoder_blob_sha',
    'generator_provider',
    'model_name',
    'model_version_or_build',
  ];
  for (const token of forbidden) if (text.includes(token)) fail(`Donnée privée interdite: ${token}`);
}

export function buildProgressivePublicEnvelopeC074(input, options = {}) {
  if (input?.publication_intent !== 'SERVER_SIDE_PUBLIC_READ_ONLY_PROGRESSIVE_BRIDGE_C074_MEASURED_RUNTIME_TRANSFORM') {
    return buildProgressivePublicEnvelopeC073(input, options);
  }
  assertProgressiveBridgeInputC074(input);
  const found = new Map(Object.entries(input.source_attestation.public_status));
  const c073 = extractProgressiveGenesisStatusC073(c074ToExactC073Text(found));
  const baseInput = buildProgressiveBridgeInputC073(c073, { now: input.bridge_received_at, liveActive: input.live_active });
  baseInput.source_observed_at = input.source_observed_at;
  baseInput.bridge_received_at = input.bridge_received_at;
  baseInput.max_age_seconds = input.max_age_seconds;

  const result = buildProgressivePublicEnvelopeC073(baseInput, options);
  const envelope = structuredClone(result.envelope);
  const metrics = envelope.payload.metrics;

  byId(metrics, 'genesis003-validated-through').value = 'C074';
  byId(metrics, 'next-scientific-action').value = 'BIND_AUDIO_CONTEXT_SAMPLE_RATE_IN_DECODE_RUNTIME_IDENTITY';

  const insertionIndex = metrics.findIndex((entry) => entry.id === 'hypothesis-selection');
  metrics.splice(
    insertionIndex,
    0,
    metric('genesis003-c074', 'C074 · vérification runtime de décodage', 'VALIDATED_10_OF_10'),
    metric('c074-claim-class', 'Classe épistémique C074', 'MEASURED'),
    metric('c074-control-wav-verified', 'Contrôle WAV C067 vérifié', true),
    metric('c074-control-encoded-sample-rate-hz', 'Fréquence encodée du contrôle (Hz)', 48000),
    metric('c074-runtime-audio-context-sample-rate-hz', 'AudioContext runtime mesuré (Hz)', 44100),
    metric('c074-decoded-sample-rate-hz', 'Fréquence décodée mesurée (Hz)', 44100),
    metric('c074-decoded-frame-length', 'Longueur décodée mesurée (frames)', 44099),
    metric('c074-repeated-decode-receipt-match', 'Receipts répétés identiques dans le même runtime', true),
    metric('c074-verification-verdict', 'Verdict vérification C074', 'FAIL_RUNTIME_DECODE_TRANSFORM'),
    metric('c074-finding', 'Constat C074', 'AUDIO_CONTEXT_SAMPLE_RATE_TRANSFORM_DETECTED'),
    metric('c074-cross-runtime-decode-equivalence-proven', 'Équivalence décodage inter-runtime prouvée', false),
    metric('c074-real-experiment-executed', 'Expérience réelle exécutée', false),
    metric('c074-experimental-audio-generated', 'Audio expérimental généré', false),
    metric('c074-external-model-or-api-used', 'Modèle/API externe utilisé pour C074', false),
  );

  envelope.payload.identity.root_version = 'GENESIS-003-C074-MEASURED-RUNTIME-TRANSFORM-PUBLIC-PROGRESS-v10';
  envelope.payload.evidence = envelope.payload.evidence.filter((entry) => entry.id !== 'LIVE-PUBLIC-PROJECTION-HASH');
  envelope.payload.evidence[0] = {
    id: 'SERVER-SIDE-WHITELIST-V10-C074-MEASURED-RUNTIME-TRANSFORM',
    type: 'PUBLIC_ATTESTATION',
    status: 'VERIFIED_PUBLIC',
    public_ref: 'Whitelisted C074 measured runtime-transform status',
  };
  const digest = digestPayload(envelope.payload, input.source_observed_at);
  envelope.payload.identity.root_digest = `PUBLIC-READ-ONLY-SHA256:${digest}`;
  envelope.payload.evidence.push({
    id: 'LIVE-PUBLIC-PROJECTION-HASH',
    type: 'PUBLIC_HASH',
    status: 'VERIFIED_PUBLIC',
    public_ref: 'Server-side progressive public read-only projection',
    hash: `sha256:${digest}`,
  });
  envelope.publication_id = 'GENESIS-PUBLIC-READ-ONLY-PROGRESSIVE-0010-C074-MEASURED-RUNTIME-TRANSFORM';

  validatePublicV2(envelope);
  scanPrivate(envelope);
  return { envelope, sourceAgeSeconds: result.sourceAgeSeconds };
}

async function main() {
  const inputPath = process.argv[2];
  if (!inputPath) fail('Usage: bridge-public-progressive-c074.mjs <bridge-input.json>');
  const input = JSON.parse(await readFile(path.resolve(inputPath), 'utf8'));
  const result = buildProgressivePublicEnvelopeC074(input);
  const outDir = path.resolve('.build/genesis-public-read-only-bridge');
  await mkdir(outDir, { recursive: true });
  await writeFile(path.join(outDir, 'public-read-only-envelope.json'), `${JSON.stringify(result.envelope, null, 2)}\n`, 'utf8');
  console.log('GENESIS_PROGRESSIVE_C074_MEASURED_RUNTIME_TRANSFORM_PUBLIC_BRIDGE_VALID');
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    console.error(`GENESIS_PROGRESSIVE_C074_MEASURED_RUNTIME_TRANSFORM_PUBLIC_BRIDGE_INVALID: ${error.message}`);
    process.exit(1);
  });
}
