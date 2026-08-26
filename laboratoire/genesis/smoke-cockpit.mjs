#!/usr/bin/env node

import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = fileURLToPath(new URL('./', import.meta.url));
const EXPECTED_BANNER = 'DEMO / SYNTHETIC DATA';
const EXPECTED_DEMO_PATH = './demo/genesis-demo-v1.json';
const EXPECTED_CONTRACT = '1.0.0-draft';

const MIME = new Map([
  ['.html', 'text/html; charset=utf-8'],
  ['.json', 'application/json; charset=utf-8'],
  ['.md', 'text/markdown; charset=utf-8'],
  ['.mjs', 'text/javascript; charset=utf-8']
]);

function fail(message) {
  throw new Error(message);
}

function resolvePublicPath(urlPath) {
  const decoded = decodeURIComponent(urlPath.split('?')[0]);
  const relative = decoded === '/' ? 'index.html' : decoded.replace(/^\/+/, '');
  const normalized = normalize(relative);

  if (normalized.startsWith('..') || normalized.includes('/../') || normalized.includes('\\..\\')) {
    fail('Traversal de chemin refusé.');
  }

  return join(ROOT, normalized);
}

const server = createServer(async (request, response) => {
  try {
    const filePath = resolvePublicPath(request.url ?? '/');
    const body = await readFile(filePath);
    response.statusCode = 200;
    response.setHeader('content-type', MIME.get(extname(filePath)) ?? 'application/octet-stream');
    response.setHeader('cache-control', 'no-store');
    response.end(body);
  } catch {
    response.statusCode = 404;
    response.end('Not Found');
  }
});

await new Promise((resolve, reject) => {
  server.once('error', reject);
  server.listen(0, '127.0.0.1', resolve);
});

try {
  const address = server.address();
  if (!address || typeof address === 'string') fail('Port HTTP de test indisponible.');

  const base = `http://127.0.0.1:${address.port}`;

  const indexResponse = await fetch(`${base}/`);
  if (!indexResponse.ok) fail(`index.html inaccessible (${indexResponse.status}).`);

  const html = await indexResponse.text();
  if (!html.includes('<title>Genesis Vision Center — DEMO</title>')) {
    fail('Titre du cockpit DEMO absent.');
  }
  if (!html.includes(EXPECTED_BANNER)) {
    fail('Bannière DEMO / SYNTHETIC DATA absente du HTML.');
  }
  if (!html.includes(`const DEMO_PATH = '${EXPECTED_DEMO_PATH}'`)) {
    fail('Le cockpit ne référence pas le snapshot DEMO canonique attendu.');
  }
  if (!html.includes(`const EXPECTED_CONTRACT = '${EXPECTED_CONTRACT}'`)) {
    fail('Le cockpit ne verrouille pas la version de contrat attendue.');
  }
  if (!html.includes('DO NOT DISPLAY AS GENESIS DATA')) {
    fail('Le verrou visuel de refus est absent.');
  }

  const demoResponse = await fetch(`${base}/demo/genesis-demo-v1.json`);
  if (!demoResponse.ok) fail(`Snapshot DEMO inaccessible (${demoResponse.status}).`);

  const demo = await demoResponse.json();
  if (demo.contract_version !== EXPECTED_CONTRACT) fail('Contrat JSON inattendu.');
  if (demo.mode !== 'DEMO') fail('Le snapshot servi n’est pas en mode DEMO.');
  if (demo.source_status !== 'SYNTHETIC') fail('Le snapshot servi n’est pas synthétique.');
  if (demo.publication_id !== 'DEMO-GENESIS-0001') fail('Publication DEMO inattendue.');

  const missingResponse = await fetch(`${base}/private/genesis-state.json`);
  if (missingResponse.status !== 404) {
    fail('Une route privée fictive ne doit pas être servie.');
  }

  console.log('GENESIS_COCKPIT_SMOKE_VALID');
  console.log(JSON.stringify({
    ok: true,
    served_index: true,
    served_demo: true,
    mode: demo.mode,
    source_status: demo.source_status,
    publication_id: demo.publication_id,
    private_route_status: missingResponse.status
  }, null, 2));
} catch (error) {
  console.error('GENESIS_COCKPIT_SMOKE_INVALID');
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
} finally {
  await new Promise((resolve) => server.close(resolve));
}
