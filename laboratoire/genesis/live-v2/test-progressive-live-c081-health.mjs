#!/usr/bin/env node
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import {
  extractProgressiveGenesisStatusC081,
  buildProgressiveBridgeInputC081,
  c081ToExactC074Text,
} from './build-public-source-progressive-c081.mjs';
import { extractProgressiveGenesisStatusC074 } from './build-public-source-progressive-c074.mjs';
import { buildProgressivePublicEnvelopeC081 } from './bridge-public-progressive-c081.mjs';

const prior = spawnSync(process.execPath, ['laboratoire/genesis/live-v2/test-progressive-live-c074-runtime-transform.mjs'], { encoding: 'utf8' });
assert.equal(prior.status, 0, prior.stderr || prior.stdout);
const priorPath = '/tmp/antmux-c074-cli-status.env';
assert.equal(existsSync(priorPath), true);
const C074 = readFileSync(priorPath, 'utf8');

function c081() {
  return C074
    .replace('genesis003_validated_through=C074', 'genesis003_validated_through=C081')
    .replace('next_scientific_action=BIND_AUDIO_CONTEXT_SAMPLE_RATE_IN_DECODE_RUNTIME_IDENTITY', 'next_scientific_action=NONE_AUTHORIZED_C082_NOT_STARTED') +
`post_c074_runtime_identity_sample_rate_binding=VALIDATED
post_c074_claim_class=MEASURED
post_c074_audio_context_sample_rate_hz=44100
post_c074_same_runtime_repeatability=true
post_c074_sample_rate_tamper_changes_identity=true
post_c074_invalid_sample_rates_fail_closed=true
post_c074_historical_c074_verdict_preserved=true
post_c074_cross_runtime_decode_equivalence_proven=false
post_c074_real_experiment_executed=false
post_c074_experimental_audio_generated=false
post_c074_external_model_or_api_used=false
c075_started=false
c080_status=PREEXECUTION_BLOCKED
c080_scientific_decode_count=0
c080_scientific_verdict_issued=false
c080_prediction_verdict=NONE
genesis003_c081=VALIDATED_MEASURED_INCONCLUSIVE
c081_claim_class=MEASURED
c081_status=VALIDATED_MEASURED_INCONCLUSIVE
c081_scientific_outcome=INCONCLUSIVE_RUNTIME_OR_EXECUTION_NOT_ESTABLISHED
c081_hypothesis_status=UNRESOLVED_INCONCLUSIVE
c081_primary_hypothesis_tested=false
c081_prediction_verdict=NONE
c081_prediction_comparison_count=0
c081_planned_scientific_decode_count=36
c081_final_scientific_decode_count=18
c081_firefox_decode_count=18
c081_chrome_decode_count=0
c081_prediction_promotion_performed=false
c081_post_observation_retry=false
c082_started=false
`;
}

const status = extractProgressiveGenesisStatusC081(c081());
assert.equal(status.validatedThrough, 'C081');
assert.equal(Object.keys(status.values).length, 140);
console.log('PASS C081-LIVE-01 exact 140-line V0.1 C081 projection accepted');

const postC074Status = extractProgressiveGenesisStatusC081(
  C074.replace('next_scientific_action=BIND_AUDIO_CONTEXT_SAMPLE_RATE_IN_DECODE_RUNTIME_IDENTITY', 'next_scientific_action=DEFINE_C075_SCIENTIFIC_STAGE') +
`post_c074_runtime_identity_sample_rate_binding=VALIDATED
post_c074_claim_class=MEASURED
post_c074_audio_context_sample_rate_hz=44100
post_c074_same_runtime_repeatability=true
post_c074_sample_rate_tamper_changes_identity=true
post_c074_invalid_sample_rates_fail_closed=true
post_c074_historical_c074_verdict_preserved=true
post_c074_cross_runtime_decode_equivalence_proven=false
post_c074_real_experiment_executed=false
post_c074_experimental_audio_generated=false
post_c074_external_model_or_api_used=false
c075_started=false
`
);
assert.equal(postC074Status.validatedThrough, 'C074');
console.log('PASS C081-LIVE-01B post-C074 121-line source remains accepted as C074 fallback');

const input = buildProgressiveBridgeInputC081(status, { now: '2026-09-06T14:00:00Z', liveActive: true });
assert.equal(input.max_age_seconds, 300);
assert.equal(input.transport.snapshot_fallback_available, true);
assert.equal(input.transport.browser_credentials_present, false);
assert.equal(input.transport.private_browser_request, false);
const envelope = buildProgressivePublicEnvelopeC081(input, { now: '2026-09-06T14:00:00Z' }).envelope;
const metrics = Object.fromEntries(envelope.payload.metrics.map((entry) => [entry.id, entry.value]));
assert.equal(envelope.mode, 'LIVE_READ_ONLY');
assert.equal(envelope.source_status, 'PUBLIC_READ_ONLY');
assert.equal(envelope.integrity_status, 'VERIFIED_PUBLIC');
assert.equal(envelope.payload.publication_gates.current_gate, 'LIVE_READ_ONLY_ACTIVE');
assert.equal(metrics['bridge-write-capability'], 'NONE');
assert.equal(metrics['browser-private-credentials'], false);
assert.equal(metrics['public-live-active'], true);
console.log('PASS C081-LIVE-02 public envelope remains read-only and live-active');

assert.equal(metrics['genesis003-validated-through'], 'C081');
assert.equal(metrics['kernel-bindings-required'], 8);
assert.equal(metrics['kernel-bindings-bound'], 8);
assert.equal(metrics['kernel-bindings-complete'], true);
assert.equal(metrics['c080-status'], 'PREEXECUTION_BLOCKED');
assert.equal(metrics['c080-scientific-decode-count'], 0);
assert.equal(metrics['c080-scientific-verdict-issued'], false);
assert.equal(metrics['c081-status'], 'VALIDATED_MEASURED_INCONCLUSIVE');
assert.equal(metrics['c081-firefox-decode-count'], 18);
assert.equal(metrics['c081-chrome-decode-count'], 0);
assert.equal(metrics['c081-primary-hypothesis-tested'], false);
assert.equal(metrics['c081-prediction-verdict'], 'NONE');
assert.equal(metrics['c081-prediction-comparison-count'], 0);
assert.equal(metrics['c082-started'], false);
console.log('PASS C081-LIVE-03 V0.1 C081 health fields are observable');

const c074 = c081ToExactC074Text(new Map(Object.entries(status.values)));
const trustedC074 = extractProgressiveGenesisStatusC074(c074);
assert.equal(trustedC074.validatedThrough, 'C074');
assert.equal(Object.keys(trustedC074.values).length, 109);
assert.equal(c074, C074);
console.log('PASS C081-LIVE-04 C081 reduces byte-exactly to trusted C074');

for (const [from, to] of [
  ['c081_status=VALIDATED_MEASURED_INCONCLUSIVE', 'c081_status=SUCCESS'],
  ['c081_prediction_verdict=NONE', 'c081_prediction_verdict=FAIL'],
  ['c081_prediction_comparison_count=0', 'c081_prediction_comparison_count=1'],
  ['c081_primary_hypothesis_tested=false', 'c081_primary_hypothesis_tested=true'],
  ['c081_chrome_decode_count=0', 'c081_chrome_decode_count=18'],
  ['c082_started=false', 'c082_started=true'],
]) assert.throws(() => extractProgressiveGenesisStatusC081(c081().replace(from, to)));
console.log('PASS C081-LIVE-05 altered C081 verdict/count/gate claims fail closed');

for (const extra of [
  'measurement_record_digest=private',
  'runtime_identity_sha256=private',
  'decoded_pcm_sha256=private',
  'gesis_commit_sha=private',
  'gesis_decoder_blob_sha=private',
  'artifact_id=private',
  'model_name=private',
]) assert.throws(() => extractProgressiveGenesisStatusC081(c081() + `${extra}\n`));
console.log('PASS C081-LIVE-06 private C081 evidence fields are rejected');

const serialized = JSON.stringify(envelope);
for (const token of [
  'Topbrutus/seedgenesis',
  'Topbrutus/gesis',
  'f521f05f62cb9d4d1d512b8b4e605f448855fd87',
  'c57babd2efd9f662022fc4861812be38431bee52',
  '34019513883',
  '9984436148',
  '9984536984',
  '28613fa64093b3b4e5ae729da6672240ac677dd822704de3b88eb714333dab62',
  '538905fd24f3a8f226381d78078ab08d6e9af4bc260db44b5f0e503d0698f1eb',
]) assert.equal(serialized.includes(token), false);
console.log('PASS C081-LIVE-07 public envelope contains no private C081 identifiers');

const cliStatus = '/tmp/antmux-c081-cli-status.env';
const cliInput = '/tmp/antmux-c081-cli-input.json';
writeFileSync(cliStatus, c081(), 'utf8');
const buildCli = spawnSync(process.execPath, ['laboratoire/genesis/live-v2/build-public-source-progressive-c081.mjs', cliStatus, cliInput], {
  encoding: 'utf8',
  env: { ...process.env, GENESIS_PUBLIC_LIVE_ACTIVE: '1' },
});
assert.equal(buildCli.status, 0, buildCli.stderr || buildCli.stdout);
assert.equal(existsSync(cliInput), true);
const bridgeCli = spawnSync(process.execPath, ['laboratoire/genesis/live-v2/bridge-public-progressive-c081.mjs', cliInput], { encoding: 'utf8' });
assert.equal(bridgeCli.status, 0, bridgeCli.stderr || bridgeCli.stdout);
const cliEnvelope = JSON.parse(readFileSync('.build/genesis-public-read-only-bridge/public-read-only-envelope.json', 'utf8'));
assert.equal(cliEnvelope.payload.metrics.find((entry) => entry.id === 'genesis003-validated-through')?.value, 'C081');
assert.equal(cliEnvelope.payload.metrics.find((entry) => entry.id === 'c081-prediction-verdict')?.value, 'NONE');
assert.equal(cliEnvelope.payload.metrics.find((entry) => entry.id === 'c082-started')?.value, false);
assert.equal(cliEnvelope.mode, 'LIVE_READ_ONLY');
console.log('PASS C081-LIVE-08 C081 runtime CLI smoke');
console.log('GENESIS_PROGRESSIVE_LIVE_C081_HEALTH_TESTS=9/9');
console.log('C081_RUNTIME_CLI_SMOKE=PASS');
