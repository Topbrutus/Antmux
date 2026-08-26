#!/usr/bin/env node

import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

const EXPECTED_CONTRACT = '1.0.0-draft';

const TOP_LEVEL_KEYS = new Set([
  'contract_version',
  'mode',
  'publication_id',
  'published_at',
  'source_status',
  'integrity_status',
  'payload'
]);

const PAYLOAD_KEYS = new Set([
  'experiment',
  'continuity',
  'pipeline',
  'metrics',
  'evidence',
  'integrity'
]);

const PIPELINE_STATUSES = new Set([
  'PENDING',
  'RUNNING_PUBLIC',
  'PASSED',
  'FAILED',
  'REJECTED',
  'NOT_APPLICABLE'
]);

const INTEGRITY_STATUSES = new Set([
  'NOT_APPLICABLE',
  'UNVERIFIED',
  'VERIFIED_PUBLIC',
  'FAILED_PUBLIC_CHECK'
]);

const CHECK_STATUSES = new Set([
  'PASSED',
  'FAILED',
  'NOT_RUN',
  'NOT_APPLICABLE'
]);

function fail(message) {
  throw new Error(message);
}

function assertObject(value, path) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    fail(`${path} doit être un objet.`);
  }
}

function assertString(value, path) {
  if (typeof value !== 'string' || value.length === 0) {
    fail(`${path} doit être une chaîne non vide.`);
  }
}

function assertAllowedKeys(object, allowedKeys, path) {
  for (const key of Object.keys(object)) {
    if (!allowedKeys.has(key)) {
      fail(`${path}.${key} n'est pas autorisé par la liste blanche.`);
    }
  }
}

function assertRequiredKeys(object, requiredKeys, path) {
  for (const key of requiredKeys) {
    if (!(key in object)) {
      fail(`${path}.${key} est obligatoire.`);
    }
  }
}

function validateNoSensitiveString(value, path) {
  if (typeof value !== 'string') return;

  const patterns = [
    { re: /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/i, label: 'clé privée' },
    { re: /\bghp_[A-Za-z0-9_]{20,}\b/, label: 'token GitHub classique' },
    { re: /\bgithub_pat_[A-Za-z0-9_]{20,}\b/, label: 'token GitHub finement scoped' },
    { re: /\bsk-[A-Za-z0-9_-]{20,}\b/, label: 'clé API potentielle' },
    { re: /^[A-Za-z]:\\/, label: 'chemin absolu Windows privé' },
    { re: /^\\\\/, label: 'chemin UNC privé' },
    { re: /^file:\/\//i, label: 'URL file:// privée' },
    { re: /https?:\/\/(?:localhost|127\.0\.0\.1)(?::\d+)?(?:\/|$)/i, label: 'endpoint local privé' },
    { re: /https?:\/\/10\.\d+\.\d+\.\d+(?::\d+)?(?:\/|$)/i, label: 'IP privée 10/8' },
    { re: /https?:\/\/192\.168\.\d+\.\d+(?::\d+)?(?:\/|$)/i, label: 'IP privée 192.168/16' },
    { re: /https?:\/\/172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+(?::\d+)?(?:\/|$)/i, label: 'IP privée 172.16/12' }
  ];

  for (const { re, label } of patterns) {
    if (re.test(value)) {
      fail(`${path} contient un motif interdit (${label}).`);
    }
  }
}

function scanStrings(value, path = '$') {
  if (typeof value === 'string') {
    validateNoSensitiveString(value, path);
    return;
  }

  if (Array.isArray(value)) {
    value.forEach((item, index) => scanStrings(item, `${path}[${index}]`));
    return;
  }

  if (value && typeof value === 'object') {
    for (const [key, child] of Object.entries(value)) {
      scanStrings(child, `${path}.${key}`);
    }
  }
}

function validateExperiment(experiment) {
  assertObject(experiment, '$.payload.experiment');
  const allowed = new Set(['public_experiment_id', 'label', 'status', 'generation']);
  assertAllowedKeys(experiment, allowed, '$.payload.experiment');
  assertRequiredKeys(experiment, ['public_experiment_id', 'label', 'status'], '$.payload.experiment');
  assertString(experiment.public_experiment_id, '$.payload.experiment.public_experiment_id');
  assertString(experiment.label, '$.payload.experiment.label');
  assertString(experiment.status, '$.payload.experiment.status');
  if ('generation' in experiment && !Number.isInteger(experiment.generation)) {
    fail('$.payload.experiment.generation doit être un entier lorsqu’il est présent.');
  }
}

function validateContinuity(continuity) {
  assertObject(continuity, '$.payload.continuity');
  const allowed = new Set(['stage', 'origin_ref', 'previous_publication_ref', 'return_status']);
  assertAllowedKeys(continuity, allowed, '$.payload.continuity');
  for (const key of Object.keys(continuity)) {
    assertString(continuity[key], `$.payload.continuity.${key}`);
  }
}

function validatePipeline(pipeline) {
  assertObject(pipeline, '$.payload.pipeline');
  assertAllowedKeys(pipeline, new Set(['steps']), '$.payload.pipeline');
  assertRequiredKeys(pipeline, ['steps'], '$.payload.pipeline');
  if (!Array.isArray(pipeline.steps)) fail('$.payload.pipeline.steps doit être une liste.');

  pipeline.steps.forEach((step, index) => {
    const path = `$.payload.pipeline.steps[${index}]`;
    assertObject(step, path);
    assertAllowedKeys(step, new Set(['id', 'label', 'status']), path);
    assertRequiredKeys(step, ['id', 'label', 'status'], path);
    assertString(step.id, `${path}.id`);
    assertString(step.label, `${path}.label`);
    if (!PIPELINE_STATUSES.has(step.status)) {
      fail(`${path}.status contient un statut non autorisé.`);
    }
  });
}

function validateMetrics(metrics) {
  if (!Array.isArray(metrics)) fail('$.payload.metrics doit être une liste.');

  metrics.forEach((metric, index) => {
    const path = `$.payload.metrics[${index}]`;
    assertObject(metric, path);
    const allowed = new Set(['id', 'label', 'value', 'unit', 'status', 'provenance_ref']);
    assertAllowedKeys(metric, allowed, path);
    assertRequiredKeys(metric, ['id', 'label', 'value', 'status', 'provenance_ref'], path);
    assertString(metric.id, `${path}.id`);
    assertString(metric.label, `${path}.label`);
    assertString(metric.status, `${path}.status`);
    assertString(metric.provenance_ref, `${path}.provenance_ref`);
    if ('unit' in metric && metric.unit !== null) assertString(metric.unit, `${path}.unit`);

    const type = typeof metric.value;
    if (!['string', 'number', 'boolean'].includes(type) || (type === 'number' && !Number.isFinite(metric.value))) {
      fail(`${path}.value doit être une chaîne, un booléen ou un nombre fini.`);
    }
  });
}

function validateEvidence(evidence) {
  if (!Array.isArray(evidence)) fail('$.payload.evidence doit être une liste.');

  evidence.forEach((item, index) => {
    const path = `$.payload.evidence[${index}]`;
    assertObject(item, path);
    const allowed = new Set(['id', 'type', 'status', 'public_ref', 'hash']);
    assertAllowedKeys(item, allowed, path);
    assertRequiredKeys(item, ['id', 'type', 'status', 'public_ref'], path);
    assertString(item.id, `${path}.id`);
    assertString(item.type, `${path}.type`);
    assertString(item.status, `${path}.status`);
    assertString(item.public_ref, `${path}.public_ref`);
    if ('hash' in item) assertString(item.hash, `${path}.hash`);
  });
}

function validateIntegrity(integrity) {
  assertObject(integrity, '$.payload.integrity');
  assertAllowedKeys(integrity, new Set(['status', 'checks']), '$.payload.integrity');
  assertRequiredKeys(integrity, ['status', 'checks'], '$.payload.integrity');
  assertString(integrity.status, '$.payload.integrity.status');
  if (!Array.isArray(integrity.checks)) fail('$.payload.integrity.checks doit être une liste.');

  integrity.checks.forEach((check, index) => {
    const path = `$.payload.integrity.checks[${index}]`;
    assertObject(check, path);
    assertAllowedKeys(check, new Set(['id', 'status', 'public_ref']), path);
    assertRequiredKeys(check, ['id', 'status', 'public_ref'], path);
    assertString(check.id, `${path}.id`);
    if (!CHECK_STATUSES.has(check.status)) fail(`${path}.status contient un statut non autorisé.`);
    assertString(check.public_ref, `${path}.public_ref`);
  });
}

export function validateDemo(data) {
  assertObject(data, '$');
  assertAllowedKeys(data, TOP_LEVEL_KEYS, '$');
  assertRequiredKeys(data, TOP_LEVEL_KEYS, '$');

  if (data.contract_version !== EXPECTED_CONTRACT) {
    fail(`contract_version doit être ${EXPECTED_CONTRACT}.`);
  }
  if (data.mode !== 'DEMO') fail('mode doit être DEMO pour ce validateur.');
  if (data.source_status !== 'SYNTHETIC') fail('source_status doit être SYNTHETIC en mode DEMO.');
  if (!INTEGRITY_STATUSES.has(data.integrity_status)) fail('integrity_status n’est pas autorisé.');

  assertString(data.publication_id, '$.publication_id');
  assertString(data.published_at, '$.published_at');
  if (Number.isNaN(Date.parse(data.published_at))) fail('$.published_at doit être une date/heure valide.');

  assertObject(data.payload, '$.payload');
  assertAllowedKeys(data.payload, PAYLOAD_KEYS, '$.payload');

  if ('experiment' in data.payload) validateExperiment(data.payload.experiment);
  if ('continuity' in data.payload) validateContinuity(data.payload.continuity);
  if ('pipeline' in data.payload) validatePipeline(data.payload.pipeline);
  if ('metrics' in data.payload) validateMetrics(data.payload.metrics);
  if ('evidence' in data.payload) validateEvidence(data.payload.evidence);
  if ('integrity' in data.payload) validateIntegrity(data.payload.integrity);

  scanStrings(data);

  return {
    ok: true,
    contract_version: data.contract_version,
    mode: data.mode,
    publication_id: data.publication_id
  };
}

async function main() {
  const defaultPath = fileURLToPath(new URL('./demo/genesis-demo-v1.json', import.meta.url));
  const targetPath = process.argv[2] ?? defaultPath;

  try {
    const raw = await readFile(targetPath, 'utf8');
    const data = JSON.parse(raw);
    const result = validateDemo(data);
    console.log('GENESIS_DEMO_VALID');
    console.log(JSON.stringify(result, null, 2));
  } catch (error) {
    console.error('GENESIS_DEMO_INVALID');
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  }
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  await main();
}
