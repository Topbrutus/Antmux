#!/usr/bin/env node
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { validatePublicV2 } from '../validate-public-v2.mjs';
import { buildProgressivePublicEnvelopeC071 } from './bridge-public-progressive-c071.mjs';
import {
  assertProgressiveBridgeInputC072,
  c072ToExactC071Text,
} from './build-public-source-progressive-c072.mjs';
import {
  extractProgressiveGenesisStatusC071,
  buildProgressiveBridgeInputC071,
} from './build-public-source-progressive-c071.mjs';

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
  return { id, label, value, status: 'VERIFIED_PUBLIC', provenance_ref: 'SERVER-SIDE-WHITELIST-V8-KERNEL-SIGNAL-INGEST' };
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
    '3910ba8431504196c02d3b1550b50fc51166aa8b',
    'e49962faf07627c9ca35cf292ec17336933c95c3',
    'a2d9685f6437ebc3d42fd8bc893e40d649bf817b7c4b2bc37bdc4093c304f28a',
    'dae4c8995ea19d51a4acc354bd97d882e28ba9fdb8217ea7779368562c6cc4eb',
    'e7d9b93be4c5b3df659c9a6805a5371a06035aa00d86dc88ede4dc50d6595eac',
    '24e6eafcb2681b84e1f9debe577db6e2fc2a965456093c7dea09b14b6f4cbe12',
    '6c8256a5fcb7a11b44f519880eb792f936f44f49',
    '1a5886e1105ae781d3ce32ba77cb741420cc8c14',
  ];
  for (const token of forbidden) if (text.includes(token)) fail(`Donnée privée interdite: ${token}`);
}

export function buildProgressivePublicEnvelopeC072(input, options = {}) {
  if (input?.publication_intent !== 'SERVER_SIDE_PUBLIC_READ_ONLY_PROGRESSIVE_BRIDGE_C072_KERNEL_SIGNAL_INGEST') {
    return buildProgressivePublicEnvelopeC071(input, options);
  }
  assertProgressiveBridgeInputC072(input);
  const found = new Map(Object.entries(input.source_attestation.public_status));
  const c071 = extractProgressiveGenesisStatusC071(c072ToExactC071Text(found));
  const baseInput = buildProgressiveBridgeInputC071(c071, { now: input.bridge_received_at, liveActive: input.live_active });
  baseInput.source_observed_at = input.source_observed_at;
  baseInput.bridge_received_at = input.bridge_received_at;
  baseInput.max_age_seconds = input.max_age_seconds;

  const result = buildProgressivePublicEnvelopeC071(baseInput, options);
  const envelope = structuredClone(result.envelope);
  const metrics = envelope.payload.metrics;

  byId(metrics, 'genesis003-validated-through').value = 'C072';
  byId(metrics, 'next-scientific-action').value = 'DEFINE_GESIS_SIGNAL_DECODE_ADAPTER_CONTRACT';

  const insertionIndex = metrics.findIndex((entry) => entry.id === 'hypothesis-selection');
  metrics.splice(
    insertionIndex,
    0,
    metric('genesis003-c072', 'C072 · interface ingestion signal', 'VALIDATED_10_OF_10'),
    metric('kernel-signal-ingest-interface-frozen', 'Interface ingestion noyau gelée', true),
    metric('kernel-signal-ingest-interface-id', 'Interface ingestion noyau', 'KERNEL-SIGNAL-INGEST-INTERFACE-001'),
    metric('kernel-ingest-input-mode', 'Mode entrée ingestion', 'EXACT_BYTES_IN_MEMORY_ONLY'),
    metric('kernel-ingest-required-fields', 'Champs ingestion requis', 5),
    metric('kernel-ingest-unknown-fields-allowed', 'Champs inconnus ingestion permis', false),
    metric('kernel-ingest-content-addressed', 'Ingestion adressée par contenu', true),
    metric('kernel-ingest-provenance-addressed', 'Ingestion adressée par provenance', true),
    metric('kernel-ingest-transport-dependency', 'Dépendance transport ingestion', false),
    metric('kernel-ingest-signal-decode-performed', 'Décodage signal effectué', false),
    metric('kernel-ingest-gesis-execution-performed', 'Exécution GESIS effectuée', false),
  );

  envelope.payload.identity.root_version = 'GENESIS-003-C072-KERNEL-SIGNAL-INGEST-PUBLIC-PROGRESS-v8';
  envelope.payload.evidence = envelope.payload.evidence.filter((entry) => entry.id !== 'LIVE-PUBLIC-PROJECTION-HASH');
  envelope.payload.evidence[0] = {
    id: 'SERVER-SIDE-WHITELIST-V8-KERNEL-SIGNAL-INGEST',
    type: 'PUBLIC_ATTESTATION',
    status: 'VERIFIED_PUBLIC',
    public_ref: 'Whitelisted C072 kernel signal ingest status',
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
  envelope.publication_id = 'GENESIS-PUBLIC-READ-ONLY-PROGRESSIVE-0008-KERNEL-SIGNAL-INGEST';

  validatePublicV2(envelope);
  scanPrivate(envelope);
  return { envelope, sourceAgeSeconds: result.sourceAgeSeconds };
}

async function main() {
  const inputPath = process.argv[2];
  if (!inputPath) fail('Usage: bridge-public-progressive-c072.mjs <bridge-input.json>');
  const input = JSON.parse(await readFile(path.resolve(inputPath), 'utf8'));
  const result = buildProgressivePublicEnvelopeC072(input);
  const outDir = path.resolve('.build/genesis-public-read-only-bridge');
  await mkdir(outDir, { recursive: true });
  await writeFile(path.join(outDir, 'public-read-only-envelope.json'), `${JSON.stringify(result.envelope, null, 2)}\n`, 'utf8');
  console.log('GENESIS_PROGRESSIVE_C072_KERNEL_SIGNAL_INGEST_PUBLIC_BRIDGE_VALID');
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    console.error(`GENESIS_PROGRESSIVE_C072_KERNEL_SIGNAL_INGEST_PUBLIC_BRIDGE_INVALID: ${error.message}`);
    process.exit(1);
  });
}
