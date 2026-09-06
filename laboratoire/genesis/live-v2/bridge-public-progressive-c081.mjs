#!/usr/bin/env node
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { validatePublicV2 } from '../validate-public-v2.mjs';
import { buildProgressivePublicEnvelopeC074 } from './bridge-public-progressive-c074.mjs';
import {
  assertProgressiveBridgeInputC081,
  c081ToExactC074Text,
} from './build-public-source-progressive-c081.mjs';
import {
  extractProgressiveGenesisStatusC074,
  buildProgressiveBridgeInputC074,
} from './build-public-source-progressive-c074.mjs';

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
  return { id, label, value, status: 'VERIFIED_PUBLIC', provenance_ref: 'SERVER-SIDE-WHITELIST-V11-C081-MEASURED-INCONCLUSIVE' };
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
    'f521f05f62cb9d4d1d512b8b4e605f448855fd87',
    'c57babd2efd9f662022fc4861812be38431bee52',
    '34019513883',
    '9984436148',
    '9984536984',
    '28613fa64093b3b4e5ae729da6672240ac677dd822704de3b88eb714333dab62',
    '538905fd24f3a8f226381d78078ab08d6e9af4bc260db44b5f0e503d0698f1eb',
    'measurement_record_digest',
    'runtime_identity_sha256',
    'ingest_descriptor_sha256',
    'handoff_descriptor_sha256',
    'decoded_pcm_sha256',
    'receipt_sha256',
    'gesis_commit_sha',
    'gesis_decoder_blob_sha',
    'artifact_id',
    'generator_provider',
    'model_name',
    'model_version_or_build',
  ];
  for (const token of forbidden) if (text.includes(token)) fail(`Donnée privée interdite: ${token}`);
}

export function buildProgressivePublicEnvelopeC081(input, options = {}) {
  if (input?.publication_intent !== 'SERVER_SIDE_PUBLIC_READ_ONLY_PROGRESSIVE_BRIDGE_C081_MEASURED_INCONCLUSIVE') {
    return buildProgressivePublicEnvelopeC074(input, options);
  }
  assertProgressiveBridgeInputC081(input);
  const found = new Map(Object.entries(input.source_attestation.public_status));
  const c074 = extractProgressiveGenesisStatusC074(c081ToExactC074Text(found));
  const baseInput = buildProgressiveBridgeInputC074(c074, { now: input.bridge_received_at, liveActive: input.live_active });
  baseInput.source_observed_at = input.source_observed_at;
  baseInput.bridge_received_at = input.bridge_received_at;
  baseInput.max_age_seconds = input.max_age_seconds;

  const result = buildProgressivePublicEnvelopeC074(baseInput, options);
  const envelope = structuredClone(result.envelope);
  const metrics = envelope.payload.metrics;

  byId(metrics, 'genesis003-validated-through').value = 'C081';
  byId(metrics, 'next-scientific-action').value = 'NONE_AUTHORIZED_C082_NOT_STARTED';

  const insertionIndex = metrics.findIndex((entry) => entry.id === 'hypothesis-selection');
  metrics.splice(
    insertionIndex,
    0,
    metric('c080-status', 'C080 · état', 'PREEXECUTION_BLOCKED'),
    metric('c080-scientific-decode-count', 'C080 · decodes scientifiques', 0),
    metric('c080-scientific-verdict-issued', 'C080 · verdict scientifique émis', false),
    metric('c080-prediction-verdict', 'C080 · verdict prédiction', 'NONE'),
    metric('genesis003-c081', 'C081 · clôture mesurée inconclusive', 'VALIDATED_MEASURED_INCONCLUSIVE'),
    metric('c081-claim-class', 'Classe épistémique C081', 'MEASURED'),
    metric('c081-status', 'Statut C081', 'VALIDATED_MEASURED_INCONCLUSIVE'),
    metric('c081-scientific-outcome', 'Issue scientifique C081', 'INCONCLUSIVE_RUNTIME_OR_EXECUTION_NOT_ESTABLISHED'),
    metric('c081-hypothesis-status', 'Hypothèse C081', 'UNRESOLVED_INCONCLUSIVE'),
    metric('c081-primary-hypothesis-tested', 'Hypothèse primaire testée', false),
    metric('c081-prediction-verdict', 'Verdict prédiction C081', 'NONE'),
    metric('c081-prediction-comparison-count', 'Comparaisons de prédiction C081', 0),
    metric('c081-planned-scientific-decode-count', 'Decodes scientifiques planifiés C081', 36),
    metric('c081-final-scientific-decode-count', 'Decodes scientifiques réalisés C081', 18),
    metric('c081-firefox-decode-count', 'Decodes Firefox C081', 18),
    metric('c081-chrome-decode-count', 'Decodes Chrome C081', 0),
    metric('c081-prediction-promotion-performed', 'Promotion en verdict prédictif', false),
    metric('c081-post-observation-retry', 'Relance post-observation', false),
    metric('c082-started', 'C082 démarré', false),
  );

  envelope.payload.identity.root_version = 'GENESIS-003-C081-MEASURED-INCONCLUSIVE-PUBLIC-PROGRESS-v11';
  envelope.payload.evidence = envelope.payload.evidence.filter((entry) => entry.id !== 'LIVE-PUBLIC-PROJECTION-HASH');
  envelope.payload.evidence[0] = {
    id: 'SERVER-SIDE-WHITELIST-V11-C081-MEASURED-INCONCLUSIVE',
    type: 'PUBLIC_ATTESTATION',
    status: 'VERIFIED_PUBLIC',
    public_ref: 'Whitelisted C081 measured inconclusive public health status',
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
  envelope.publication_id = 'GENESIS-PUBLIC-READ-ONLY-PROGRESSIVE-0011-C081-MEASURED-INCONCLUSIVE';

  validatePublicV2(envelope);
  scanPrivate(envelope);
  return { envelope, sourceAgeSeconds: result.sourceAgeSeconds };
}

async function main() {
  const inputPath = process.argv[2];
  if (!inputPath) fail('Usage: bridge-public-progressive-c081.mjs <bridge-input.json>');
  const input = JSON.parse(await readFile(path.resolve(inputPath), 'utf8'));
  const result = buildProgressivePublicEnvelopeC081(input);
  const outDir = path.resolve('.build/genesis-public-read-only-bridge');
  await mkdir(outDir, { recursive: true });
  await writeFile(path.join(outDir, 'public-read-only-envelope.json'), `${JSON.stringify(result.envelope, null, 2)}\n`, 'utf8');
  console.log('GENESIS_PROGRESSIVE_C081_MEASURED_INCONCLUSIVE_PUBLIC_BRIDGE_VALID');
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    console.error(`GENESIS_PROGRESSIVE_C081_MEASURED_INCONCLUSIVE_PUBLIC_BRIDGE_INVALID: ${error.message}`);
    process.exit(1);
  });
}
