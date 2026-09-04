#!/usr/bin/env node
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { validatePublicV2 } from '../validate-public-v2.mjs';
import { buildProgressivePublicEnvelopeC072 } from './bridge-public-progressive-c072.mjs';
import {
  assertProgressiveBridgeInputC073,
  c073ToExactC072Text,
} from './build-public-source-progressive-c073.mjs';
import {
  extractProgressiveGenesisStatusC072,
  buildProgressiveBridgeInputC072,
} from './build-public-source-progressive-c072.mjs';

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
  return { id, label, value, status: 'VERIFIED_PUBLIC', provenance_ref: 'SERVER-SIDE-WHITELIST-V9-GESIS-DECODE-ADAPTER' };
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
    '20ea3c3d77c8d934db17ae60bb3032b023dff5a6',
    'b6efdff8639264a48d269806ad6507f5e2bee5d9',
    '203f94de2824a1f904a004ce5092f5c5d423b7bd3f7264a7a08f51e7a96830ec',
    'e9bf65407aaf1072601de7c5f68a80255f4ff0a1d947bfad9cc621b13440d204',
    '14aa571228918a7665358a93cb1b0f5da8a711222f48105d3e615b01239a8283',
    '6c8256a5fcb7a11b44f519880eb792f936f44f49',
    '8b97673a2228af397fa949bf5f7921c8cdc54be4',
    '3910ba8431504196c02d3b1550b50fc51166aa8b',
    'e49962faf07627c9ca35cf292ec17336933c95c3',
    'a2d9685f6437ebc3d42fd8bc893e40d649bf817b7c4b2bc37bdc4093c304f28a',
    'dae4c8995ea19d51a4acc354bd97d882e28ba9fdb8217ea7779368562c6cc4eb',
    'e7d9b93be4c5b3df659c9a6805a5371a06035aa00d86dc88ede4dc50d6595eac',
    '24e6eafcb2681b84e1f9debe577db6e2fc2a965456093c7dea09b14b6f4cbe12',
    'generator_provider',
    'model_name',
    'model_version_or_build',
    'runtime_identity_sha256',
    'handoff_descriptor_sha256',
    'decoded_pcm_sha256',
    'gesis_commit_sha',
    'gesis_decoder_blob_sha',
  ];
  for (const token of forbidden) if (text.includes(token)) fail(`Donnée privée interdite: ${token}`);
}

export function buildProgressivePublicEnvelopeC073(input, options = {}) {
  if (input?.publication_intent !== 'SERVER_SIDE_PUBLIC_READ_ONLY_PROGRESSIVE_BRIDGE_C073_GESIS_DECODE_ADAPTER') {
    return buildProgressivePublicEnvelopeC072(input, options);
  }
  assertProgressiveBridgeInputC073(input);
  const found = new Map(Object.entries(input.source_attestation.public_status));
  const c072 = extractProgressiveGenesisStatusC072(c073ToExactC072Text(found));
  const baseInput = buildProgressiveBridgeInputC072(c072, { now: input.bridge_received_at, liveActive: input.live_active });
  baseInput.source_observed_at = input.source_observed_at;
  baseInput.bridge_received_at = input.bridge_received_at;
  baseInput.max_age_seconds = input.max_age_seconds;

  const result = buildProgressivePublicEnvelopeC072(baseInput, options);
  const envelope = structuredClone(result.envelope);
  const metrics = envelope.payload.metrics;

  byId(metrics, 'genesis003-validated-through').value = 'C073';
  byId(metrics, 'next-scientific-action').value = 'VERIFY_GESIS_DECODE_ADAPTER_WITH_DETERMINISTIC_WAV_CONTROL';

  const insertionIndex = metrics.findIndex((entry) => entry.id === 'hypothesis-selection');
  metrics.splice(
    insertionIndex,
    0,
    metric('genesis003-c073', 'C073 · contrat adaptateur décodage GESIS', 'VALIDATED_10_OF_10'),
    metric('gesis-signal-decode-adapter-contract-frozen', 'Contrat adaptateur décodage GESIS gelé', true),
    metric('gesis-signal-decode-adapter-contract-id', 'Contrat adaptateur décodage GESIS', 'GESIS-SIGNAL-DECODE-ADAPTER-CONTRACT-001'),
    metric('gesis-decode-adapter-input-mode', 'Mode entrée adaptateur décodage', 'C072_EXACT_BYTES_AND_VALIDATED_DESCRIPTOR_IN_MEMORY_ONLY'),
    metric('gesis-decode-adapter-arraybuffer-policy', 'Politique ArrayBuffer', 'COPY_EXACT_BYTES_TO_NEW_ARRAYBUFFER'),
    metric('gesis-decode-runtime-dependency', 'Dépendance runtime décodage', true),
    metric('gesis-decode-runtime-identity-required', 'Identité runtime requise', true),
    metric('gesis-decode-cross-runtime-equivalence-proven', 'Équivalence inter-runtime prouvée', false),
    metric('gesis-decode-signal-performed', 'Décodage signal effectué', false),
    metric('gesis-decode-analysis-performed', 'Analyse GESIS effectuée', false),
    metric('gesis-decode-pcm-serialization-policy', 'Politique sérialisation PCM', 'CHANNEL_MAJOR_FLOAT32_LITTLE_ENDIAN_IEEE754'),
  );

  envelope.payload.identity.root_version = 'GENESIS-003-C073-GESIS-DECODE-ADAPTER-PUBLIC-PROGRESS-v9';
  envelope.payload.evidence = envelope.payload.evidence.filter((entry) => entry.id !== 'LIVE-PUBLIC-PROJECTION-HASH');
  envelope.payload.evidence[0] = {
    id: 'SERVER-SIDE-WHITELIST-V9-GESIS-DECODE-ADAPTER',
    type: 'PUBLIC_ATTESTATION',
    status: 'VERIFIED_PUBLIC',
    public_ref: 'Whitelisted C073 GESIS decode adapter status',
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
  envelope.publication_id = 'GENESIS-PUBLIC-READ-ONLY-PROGRESSIVE-0009-GESIS-DECODE-ADAPTER';

  validatePublicV2(envelope);
  scanPrivate(envelope);
  return { envelope, sourceAgeSeconds: result.sourceAgeSeconds };
}

async function main() {
  const inputPath = process.argv[2];
  if (!inputPath) fail('Usage: bridge-public-progressive-c073.mjs <bridge-input.json>');
  const input = JSON.parse(await readFile(path.resolve(inputPath), 'utf8'));
  const result = buildProgressivePublicEnvelopeC073(input);
  const outDir = path.resolve('.build/genesis-public-read-only-bridge');
  await mkdir(outDir, { recursive: true });
  await writeFile(path.join(outDir, 'public-read-only-envelope.json'), `${JSON.stringify(result.envelope, null, 2)}\n`, 'utf8');
  console.log('GENESIS_PROGRESSIVE_C073_GESIS_DECODE_ADAPTER_PUBLIC_BRIDGE_VALID');
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    console.error(`GENESIS_PROGRESSIVE_C073_GESIS_DECODE_ADAPTER_PUBLIC_BRIDGE_INVALID: ${error.message}`);
    process.exit(1);
  });
}
