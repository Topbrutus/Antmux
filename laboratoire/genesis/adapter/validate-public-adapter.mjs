#!/usr/bin/env node
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { adaptPublicCandidate } from './public-adapter.mjs';

const fixturePath = fileURLToPath(new URL('./fixtures/synthetic-private-like.json', import.meta.url));
const evidenceDir = fileURLToPath(new URL('../../../.build/genesis-adapter-evidence/', import.meta.url));
const outputPath = `${evidenceDir}public-adapter-output.json`;

const input = JSON.parse(await readFile(fixturePath, 'utf8'));
const output = adaptPublicCandidate(input);
const serialized = JSON.stringify(output);

const forbidden = [
  'Topbrutus/seedgenesis',
  'C:\\private\\seedgenesis',
  'ghp_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
  'http://127.0.0.1:9999/private',
  'SYNTHETIC PRIVATE-LIKE NOISE'
];
for(const marker of forbidden){
  if(serialized.includes(marker)) throw new Error(`Fuite de frontière détectée: ${marker}`);
}
if(output.integrity_status !== 'VERIFIED_PUBLIC') throw new Error('La sortie Adapter doit être VERIFIED_PUBLIC après validation.');
if(output.mode !== 'DEMO' || output.source_status !== 'SYNTHETIC') throw new Error('La phase Adapter doit rester DEMO/SYNTHETIC.');

await mkdir(evidenceDir, {recursive:true});
await writeFile(outputPath, `${JSON.stringify(output,null,2)}\n`, 'utf8');

console.log('GENESIS_PUBLIC_ADAPTER_VALID');
console.log(JSON.stringify({
  ok:true,
  mode:output.mode,
  source_status:output.source_status,
  integrity_status:output.integrity_status,
  publication_id:output.publication_id,
  private_noise_leaked:false,
  snapshot_enabled:false,
  live_read_only_enabled:false
}, null, 2));
