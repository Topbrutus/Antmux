#!/usr/bin/env node
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import {
  extractProgressiveGenesisStatusC074,
  buildProgressiveBridgeInputC074,
  c074ToExactC073Text,
} from './build-public-source-progressive-c074.mjs';
import { extractProgressiveGenesisStatusC073 } from './build-public-source-progressive-c073.mjs';
import { buildProgressivePublicEnvelopeC074 } from './bridge-public-progressive-c074.mjs';

const prior = spawnSync(process.execPath, ['laboratoire/genesis/live-v2/test-progressive-live-c073-decode-adapter.mjs'], { encoding: 'utf8' });
assert.equal(prior.status, 0, prior.stderr || prior.stdout);
const priorPath = '/tmp/antmux-c073-cli-status.env';
assert.equal(existsSync(priorPath), true);
const C073 = readFileSync(priorPath, 'utf8');

function c074() {
  return C073
    .replace('genesis003_validated_through=C073', 'genesis003_validated_through=C074')
    .replace('next_scientific_action=VERIFY_GESIS_DECODE_ADAPTER_WITH_DETERMINISTIC_WAV_CONTROL', 'next_scientific_action=BIND_AUDIO_CONTEXT_SAMPLE_RATE_IN_DECODE_RUNTIME_IDENTITY') +
`genesis003_c074=VALIDATED_10_OF_10
c074_claim_class=MEASURED
c074_control_wav_verified=true
c074_control_encoded_sample_rate_hz=48000
c074_runtime_audio_context_sample_rate_hz=44100
c074_decoded_sample_rate_hz=44100
c074_decoded_frame_length=44099
c074_repeated_decode_receipt_match=true
c074_verification_verdict=FAIL_RUNTIME_DECODE_TRANSFORM
c074_finding=AUDIO_CONTEXT_SAMPLE_RATE_TRANSFORM_DETECTED
c074_cross_runtime_decode_equivalence_proven=false
c074_real_experiment_executed=false
c074_experimental_audio_generated=false
c074_external_model_or_api_used=false
`;
}

const status = extractProgressiveGenesisStatusC074(c074());
assert.equal(status.validatedThrough, 'C074');
assert.equal(Object.keys(status.values).length, 109);
console.log('PASS C074-LIVE-01 exact 109-line C074 measured projection accepted');

const input = buildProgressiveBridgeInputC074(status, { now: '2026-09-04T23:50:00Z', liveActive: true });
const envelope = buildProgressivePublicEnvelopeC074(input, { now: '2026-09-04T23:50:00Z' }).envelope;
const metrics = Object.fromEntries(envelope.payload.metrics.map((entry) => [entry.id, entry.value]));
assert.equal(metrics['genesis003-validated-through'], 'C074');
assert.equal(metrics['next-scientific-action'], 'BIND_AUDIO_CONTEXT_SAMPLE_RATE_IN_DECODE_RUNTIME_IDENTITY');
assert.equal(metrics['bridge-write-capability'], 'NONE');
assert.equal(envelope.mode, 'LIVE_READ_ONLY');
assert.equal(envelope.source_status, 'PUBLIC_READ_ONLY');
assert.equal(envelope.integrity_status, 'VERIFIED_PUBLIC');
console.log('PASS C074-LIVE-02 C074 public envelope remains exact read-only');

assert.equal(metrics['execution-bindings-required'], 11);
assert.equal(metrics['execution-bindings-bound'], 7);
assert.equal(metrics['execution-bindings-unbound'], 4);
assert.equal(metrics['execution-bindings-complete'], false);
assert.equal(metrics['kernel-bindings-required'], 8);
assert.equal(metrics['kernel-bindings-bound'], 8);
assert.equal(metrics['kernel-bindings-complete'], true);
assert.equal(metrics['gesis-decode-runtime-dependency'], true);
assert.equal(metrics['gesis-decode-runtime-identity-required'], true);
console.log('PASS C074-LIVE-03 inherited execution, kernel and C073 adapter states remain intact');

assert.equal(metrics['genesis003-c074'], 'VALIDATED_10_OF_10');
assert.equal(metrics['c074-claim-class'], 'MEASURED');
assert.equal(metrics['c074-control-wav-verified'], true);
assert.equal(metrics['c074-control-encoded-sample-rate-hz'], 48000);
assert.equal(metrics['c074-runtime-audio-context-sample-rate-hz'], 44100);
assert.equal(metrics['c074-decoded-sample-rate-hz'], 44100);
assert.equal(metrics['c074-decoded-frame-length'], 44099);
assert.equal(metrics['c074-repeated-decode-receipt-match'], true);
assert.equal(metrics['c074-verification-verdict'], 'FAIL_RUNTIME_DECODE_TRANSFORM');
assert.equal(metrics['c074-finding'], 'AUDIO_CONTEXT_SAMPLE_RATE_TRANSFORM_DETECTED');
assert.equal(metrics['c074-cross-runtime-decode-equivalence-proven'], false);
console.log('PASS C074-LIVE-04 measured negative finding is explicit and preserved');

const c073 = c074ToExactC073Text(new Map(Object.entries(status.values)));
const trustedC073 = extractProgressiveGenesisStatusC073(c073);
assert.equal(trustedC073.validatedThrough, 'C073');
assert.equal(Object.keys(trustedC073.values).length, 95);
assert.equal(c073, C073);
console.log('PASS C074-LIVE-05 C074 reduces byte-exactly to trusted C073');

for (const [from, to] of [
  ['c074_claim_class=MEASURED', 'c074_claim_class=HYPOTHESIS'],
  ['c074_runtime_audio_context_sample_rate_hz=44100', 'c074_runtime_audio_context_sample_rate_hz=48000'],
  ['c074_verification_verdict=FAIL_RUNTIME_DECODE_TRANSFORM', 'c074_verification_verdict=PASS_EXACT_REFERENCE'],
  ['c074_finding=AUDIO_CONTEXT_SAMPLE_RATE_TRANSFORM_DETECTED', 'c074_finding=NONE'],
  ['c074_cross_runtime_decode_equivalence_proven=false', 'c074_cross_runtime_decode_equivalence_proven=true'],
]) assert.throws(() => extractProgressiveGenesisStatusC074(c074().replace(from, to)));
console.log('PASS C074-LIVE-06 altered epistemic/runtime claims fail closed');

for (const extra of [
  'measurement_record_digest=private',
  'runtime_identity_sha256=private',
  'ingest_descriptor_sha256=private',
  'handoff_descriptor_sha256=private',
  'decoded_pcm_sha256=private',
  'naive_reference_pcm_sha256=private',
  'receipt_sha256=private',
  'gesis_commit_sha=private',
  'gesis_decoder_blob_sha=private',
  'model_name=private',
]) assert.throws(() => extractProgressiveGenesisStatusC074(c074() + `${extra}\n`));
console.log('PASS C074-LIVE-07 private measurement/model evidence fields are rejected');

const serialized = JSON.stringify(envelope);
for (const token of [
  'Topbrutus/seedgenesis',
  'Topbrutus/gesis',
  '84582b2a7c53c7c51d4b7a18ac6650365135e8e1',
  'e4db07078b95e743c57a8ac322958d636087f8ad',
  'c6532a7806de59c78268cc0e36e5cd48906031ed',
  'e5865c110509d98c80bf88ee9f73282ddb608185e39cde1e49c84e3786706858',
  'c1d6aeb247e61e5fbc5575bf251c8331c6bdfe4784b68065a3d6ad50b9ffe7bc',
  '33db943f9eb42fd277084f4f945ae7e4d7a088ca7fd008847b1a73f0206734a9',
  '6bf952c076f93e57d45e8305d696c54c8907b76e513e076924ae8bac5db679de',
  'c4df37399dca258ce61f568b71bcabb4d01c069d3ae94409094412f65fbf977a',
]) assert.equal(serialized.includes(token), false);
console.log('PASS C074-LIVE-08 public envelope contains no private C074/GESIS evidence identifiers');

assert.equal(metrics['provider-model-kernel-dependency'], false);
assert.equal(metrics['prompt-style-kernel-dependency'], false);
assert.equal(metrics['real-experiment-execution-authorized'], false);
assert.equal(metrics['c074-real-experiment-executed'], false);
assert.equal(metrics['c074-experimental-audio-generated'], false);
assert.equal(metrics['c074-external-model-or-api-used'], false);
assert.notEqual(metrics['c074-verification-verdict'], 'PASS_EXACT_REFERENCE');
console.log('PASS C074-LIVE-09 safety semantics and negative verdict remain fail-closed');

const cliStatus = '/tmp/antmux-c074-cli-status.env';
const cliInput = '/tmp/antmux-c074-cli-input.json';
writeFileSync(cliStatus, c074(), 'utf8');
const buildCli = spawnSync(process.execPath, ['laboratoire/genesis/live-v2/build-public-source-progressive-c074.mjs', cliStatus, cliInput], {
  encoding: 'utf8',
  env: { ...process.env, GENESIS_PUBLIC_LIVE_ACTIVE: '1' },
});
assert.equal(buildCli.status, 0, buildCli.stderr || buildCli.stdout);
assert.equal(existsSync(cliInput), true);
const bridgeCli = spawnSync(process.execPath, ['laboratoire/genesis/live-v2/bridge-public-progressive-c074.mjs', cliInput], { encoding: 'utf8' });
assert.equal(bridgeCli.status, 0, bridgeCli.stderr || bridgeCli.stdout);
const cliEnvelope = JSON.parse(readFileSync('.build/genesis-public-read-only-bridge/public-read-only-envelope.json', 'utf8'));
assert.equal(cliEnvelope.payload.metrics.find((entry) => entry.id === 'genesis003-validated-through')?.value, 'C074');
assert.equal(cliEnvelope.payload.metrics.find((entry) => entry.id === 'c074-verification-verdict')?.value, 'FAIL_RUNTIME_DECODE_TRANSFORM');
assert.equal(cliEnvelope.payload.metrics.find((entry) => entry.id === 'bridge-write-capability')?.value, 'NONE');
assert.equal(cliEnvelope.mode, 'LIVE_READ_ONLY');
console.log('PASS C074-LIVE-10 C074 runtime CLI smoke');
console.log('GENESIS_PROGRESSIVE_LIVE_C074_MEASURED_RUNTIME_TRANSFORM_TESTS=10/10');
console.log('C074_RUNTIME_CLI_SMOKE=PASS');
