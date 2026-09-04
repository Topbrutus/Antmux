#!/usr/bin/env node
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { validatePublicV2 } from '../validate-public-v2.mjs';
import { buildProgressivePublicEnvelopeC070 } from './bridge-public-progressive-c070.mjs';
import {
  assertProgressiveBridgeInputC071,
  c071ToExactC070Text,
} from './build-public-source-progressive-c071.mjs';
import {
  extractProgressiveGenesisStatusC070,
  buildProgressiveBridgeInputC070,
} from './build-public-source-progressive-c070.mjs';

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
  return { id, label, value, status: 'VERIFIED_PUBLIC', provenance_ref: 'SERVER-SIDE-WHITELIST-V7-KERNEL-SIGNAL-CONTRACT' };
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
    'generator_provider',
    'model_name',
    'model_version_or_build',
    'a5acd442d9a851496c9f3bdc706b6f408e4fd92a03cff83c663b85e6b583a0e4',
    '932c41a38dc8cce2e7cccee436f26a200d269c058e69e5de9ec09105013407aa',
    '6c8256a5fcb7a11b44f519880eb792f936f44f49',
    '8b97673a2228af397fa949bf5f7921c8cdc54be4',
    '707c17bd150f2313f5b649a4da053820f6320f0412ed9957aa6582495c8e5c91',
    'd737d3fa761ccc7112d84387d34a24a3bf8aff5bdb8469e3a436f9b3793ab056',
    '6ca8caa0b84e685c86d2552d27ae87517e6b8a285857ca1da047aabf5ffc63d7',
    '1a5886e1105ae781d3ce32ba77cb741420cc8c14',
  ];
  for (const token of forbidden) if (text.includes(token)) fail(`Donnée privée interdite: ${token}`);
}

export function buildProgressivePublicEnvelopeC071(input, options = {}) {
  if (input?.publication_intent !== 'SERVER_SIDE_PUBLIC_READ_ONLY_PROGRESSIVE_BRIDGE_C071_KERNEL_SIGNAL_CONTRACT') {
    return buildProgressivePublicEnvelopeC070(input, options);
  }
  assertProgressiveBridgeInputC071(input);
  const found = new Map(Object.entries(input.source_attestation.public_status));
  const c070 = extractProgressiveGenesisStatusC070(c071ToExactC070Text(found));
  const baseInput = buildProgressiveBridgeInputC070(c070, { now: input.bridge_received_at, liveActive: input.live_active });
  baseInput.source_observed_at = input.source_observed_at;
  baseInput.bridge_received_at = input.bridge_received_at;
  baseInput.max_age_seconds = input.max_age_seconds;

  const result = buildProgressivePublicEnvelopeC070(baseInput, options);
  const envelope = structuredClone(result.envelope);
  const metrics = envelope.payload.metrics;

  byId(metrics, 'genesis003-validated-through').value = 'C071';
  byId(metrics, 'next-scientific-action').value = 'DEFINE_KERNEL_NEUTRAL_SIGNAL_INGEST_INTERFACE';

  const insertionIndex = metrics.findIndex((entry) => entry.id === 'hypothesis-selection');
  metrics.splice(
    insertionIndex,
    0,
    metric('genesis003-c071', 'C071 · contrat noyau signal', 'VALIDATED_10_OF_10'),
    metric('kernel-signal-contract-frozen', 'Contrat noyau signal gelé', true),
    metric('kernel-source-of-truth', 'Source de vérité noyau', 'SIGNAL_AND_MEASUREMENT_PROVENANCE'),
    metric('kernel-bindings-required', 'Bindings noyau requis', 8),
    metric('kernel-bindings-bound', 'Bindings noyau liés', 8),
    metric('kernel-bindings-complete', 'Bindings noyau complets', true),
    metric('external-generation-metadata-required-by-kernel', 'Métadonnées générateur requises par noyau', false),
    metric('prompt-style-kernel-dependency', 'Prompt/style dépendance noyau', false),
    metric('real-experiment-execution-authorized', 'Exécution expérience réelle autorisée', false),
    metric('historical-execution-contract-policy', 'Contrat exécution historique', 'IMMUTABLE_HISTORY_NOT_KERNEL_SOURCE_OF_TRUTH'),
  );

  envelope.payload.identity.root_version = 'GENESIS-003-C071-KERNEL-SIGNAL-CONTRACT-PUBLIC-PROGRESS-v7';
  envelope.payload.evidence = envelope.payload.evidence.filter((entry) => entry.id !== 'LIVE-PUBLIC-PROJECTION-HASH');
  envelope.payload.evidence[0] = {
    id: 'SERVER-SIDE-WHITELIST-V7-KERNEL-SIGNAL-CONTRACT',
    type: 'PUBLIC_ATTESTATION',
    status: 'VERIFIED_PUBLIC',
    public_ref: 'Whitelisted C071 kernel-neutral signal provenance status',
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
  envelope.publication_id = 'GENESIS-PUBLIC-READ-ONLY-PROGRESSIVE-0007-KERNEL-SIGNAL-CONTRACT';

  validatePublicV2(envelope);
  scanPrivate(envelope);
  return { envelope, sourceAgeSeconds: result.sourceAgeSeconds };
}

async function main() {
  const inputPath = process.argv[2];
  if (!inputPath) fail('Usage: bridge-public-progressive-c071.mjs <bridge-input.json>');
  const input = JSON.parse(await readFile(path.resolve(inputPath), 'utf8'));
  const result = buildProgressivePublicEnvelopeC071(input);
  const outDir = path.resolve('.build/genesis-public-read-only-bridge');
  await mkdir(outDir, { recursive: true });
  await writeFile(path.join(outDir, 'public-read-only-envelope.json'), `${JSON.stringify(result.envelope, null, 2)}\n`, 'utf8');
  console.log('GENESIS_PROGRESSIVE_C071_KERNEL_SIGNAL_PUBLIC_BRIDGE_VALID');
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    console.error(`GENESIS_PROGRESSIVE_C071_KERNEL_SIGNAL_PUBLIC_BRIDGE_INVALID: ${error.message}`);
    process.exit(1);
  });
}
