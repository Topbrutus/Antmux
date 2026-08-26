#!/usr/bin/env node

import { createServer } from 'node:http';
import { mkdir, readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const ROOT = fileURLToPath(new URL('./', import.meta.url));
const REPO_ROOT = fileURLToPath(new URL('../../', import.meta.url));
const EVIDENCE_DIR = join(REPO_ROOT, '.build', 'genesis-browser-evidence');
const DEMO = JSON.parse(await readFile(join(ROOT, 'demo', 'genesis-demo-v1.json'), 'utf8'));

const EXPECTED = Object.freeze({
  title: 'Genesis Vision Center — DEMO',
  banner: 'DEMO / SYNTHETIC DATA',
  contract: '1.0.0-draft',
  mode: 'DEMO',
  sourceStatus: 'SYNTHETIC',
  publicationId: 'DEMO-GENESIS-0001'
});

const MIME = new Map([
  ['.html', 'text/html; charset=utf-8'],
  ['.json', 'application/json; charset=utf-8'],
  ['.md', 'text/markdown; charset=utf-8'],
  ['.mjs', 'text/javascript; charset=utf-8']
]);

function fail(message) {
  throw new Error(message);
}

function assert(condition, message) {
  if (!condition) fail(message);
}

function resolvePublicPath(urlPath) {
  const decoded = decodeURIComponent((urlPath ?? '/').split('?')[0]);
  const relative = decoded === '/' ? 'index.html' : decoded.replace(/^\/+/, '');
  const normalized = normalize(relative);

  if (normalized.startsWith('..') || normalized.includes('/../') || normalized.includes('\\..\\')) {
    fail('Traversal de chemin refusé.');
  }

  return join(ROOT, normalized);
}

const server = createServer(async (request, response) => {
  try {
    const filePath = resolvePublicPath(request.url);
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

let browser;

async function textOf(page, selector) {
  const value = await page.locator(selector).textContent();
  return value?.trim() ?? '';
}

async function verifyViewport(base, viewportName, viewport) {
  const context = await browser.newContext({ viewport, deviceScaleFactor: 1 });
  const page = await context.newPage();
  const consoleErrors = [];
  const pageErrors = [];
  const requestedPaths = [];

  page.on('console', message => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  page.on('pageerror', error => pageErrors.push(error.message));
  page.on('request', request => {
    const url = new URL(request.url());
    if (url.origin === base) requestedPaths.push(url.pathname);
  });

  try {
    const response = await page.goto(`${base}/`, { waitUntil: 'networkidle' });
    assert(response?.ok(), `${viewportName}: index HTTP invalide (${response?.status() ?? 'aucune réponse'}).`);
    assert((await page.title()) === EXPECTED.title, `${viewportName}: titre navigateur inattendu.`);

    await page.locator('#cockpit').waitFor({ state: 'visible', timeout: 5000 });

    assert(await page.locator('#demoBanner').isVisible(), `${viewportName}: bannière DEMO invisible.`);
    assert((await textOf(page, '#demoBanner')) === EXPECTED.banner, `${viewportName}: texte de bannière DEMO inattendu.`);
    assert((await textOf(page, '#contractVersion')) === EXPECTED.contract, `${viewportName}: contrat rendu inattendu.`);
    assert((await textOf(page, '#mode')) === EXPECTED.mode, `${viewportName}: mode rendu inattendu.`);
    assert((await textOf(page, '#sourceStatus')) === EXPECTED.sourceStatus, `${viewportName}: source_status rendu inattendu.`);
    assert((await textOf(page, '#publicationId')) === EXPECTED.publicationId, `${viewportName}: publication rendue inattendue.`);

    const fatalVisible = await page.locator('#fatal').isVisible();
    const fatalText = await textOf(page, '#fatal');
    assert(!fatalVisible, `${viewportName}: l'état fatal est visible: ${fatalText}`);
    assert(!fatalText.includes('DO NOT DISPLAY AS GENESIS DATA'), `${viewportName}: le verrou fatal a été déclenché.`);

    const pipelineCount = await page.locator('#pipeline .step').count();
    const metricCount = await page.locator('#metrics .metric').count();
    const checkCount = await page.locator('#checks .check').count();
    const evidenceCount = await page.locator('#evidence .check').count();

    assert(pipelineCount === (DEMO.payload?.pipeline?.steps?.length ?? 0), `${viewportName}: nombre d'étapes pipeline rendu incorrect.`);
    assert(metricCount === (DEMO.payload?.metrics?.length ?? 0), `${viewportName}: nombre de métriques rendu incorrect.`);
    assert(checkCount === (DEMO.payload?.integrity?.checks?.length ?? 0), `${viewportName}: nombre de contrôles rendu incorrect.`);
    assert(evidenceCount === (DEMO.payload?.evidence?.length ?? 0), `${viewportName}: nombre de preuves rendu incorrect.`);

    const geometry = await page.evaluate(() => {
      const banner = document.getElementById('demoBanner');
      const cockpit = document.getElementById('cockpit');
      const bannerRect = banner?.getBoundingClientRect();
      const cockpitRect = cockpit?.getBoundingClientRect();
      return {
        viewportWidth: window.innerWidth,
        scrollWidth: document.documentElement.scrollWidth,
        bannerWidth: bannerRect?.width ?? 0,
        bannerHeight: bannerRect?.height ?? 0,
        cockpitWidth: cockpitRect?.width ?? 0,
        cockpitHeight: cockpitRect?.height ?? 0,
        cockpitHidden: cockpit?.hidden ?? true,
        bannerDisplay: banner ? getComputedStyle(banner).display : 'none',
        cockpitDisplay: cockpit ? getComputedStyle(cockpit).display : 'none'
      };
    });

    assert(!geometry.cockpitHidden, `${viewportName}: cockpit encore hidden après rendu.`);
    assert(geometry.bannerDisplay !== 'none' && geometry.bannerWidth > 0 && geometry.bannerHeight > 0, `${viewportName}: bannière sans boîte visuelle.`);
    assert(geometry.cockpitDisplay !== 'none' && geometry.cockpitWidth > 0 && geometry.cockpitHeight > 0, `${viewportName}: cockpit sans boîte visuelle.`);
    assert(geometry.scrollWidth <= geometry.viewportWidth + 1, `${viewportName}: débordement horizontal (${geometry.scrollWidth} > ${geometry.viewportWidth}).`);

    assert(pageErrors.length === 0, `${viewportName}: erreur JavaScript navigateur: ${pageErrors.join(' | ')}`);
    assert(consoleErrors.length === 0, `${viewportName}: console.error navigateur: ${consoleErrors.join(' | ')}`);
    assert(!requestedPaths.some(path => path.startsWith('/private/')), `${viewportName}: requête privée détectée.`);

    const screenshotPath = join(EVIDENCE_DIR, `${viewportName}.png`);
    await page.screenshot({ path: screenshotPath, fullPage: true });

    return {
      viewport: viewportName,
      size: viewport,
      rendered: true,
      screenshot: `.build/genesis-browser-evidence/${viewportName}.png`,
      pipeline_count: pipelineCount,
      metric_count: metricCount,
      check_count: checkCount,
      evidence_count: evidenceCount,
      requested_paths: [...new Set(requestedPaths)],
      horizontal_overflow: false,
      browser_console_errors: 0,
      browser_page_errors: 0
    };
  } finally {
    await context.close();
  }
}

try {
  const address = server.address();
  if (!address || typeof address === 'string') fail('Port HTTP de test navigateur indisponible.');

  const base = `http://127.0.0.1:${address.port}`;
  await mkdir(EVIDENCE_DIR, { recursive: true });

  browser = await chromium.launch({ headless: true });
  const browserVersion = browser.version();

  const results = [];
  results.push(await verifyViewport(base, 'desktop', { width: 1440, height: 1000 }));
  results.push(await verifyViewport(base, 'mobile', { width: 390, height: 844 }));

  const report = {
    ok: true,
    lab: 'LAB-004',
    test: 'GENESIS_COCKPIT_REAL_BROWSER_RENDER',
    browser: 'Chromium',
    browser_version: browserVersion,
    mode: EXPECTED.mode,
    source_status: EXPECTED.sourceStatus,
    publication_id: EXPECTED.publicationId,
    private_genesis_connected: false,
    viewports: results
  };

  const { writeFile } = await import('node:fs/promises');
  await writeFile(join(EVIDENCE_DIR, 'REPORT.json'), `${JSON.stringify(report, null, 2)}\n`, 'utf8');

  console.log('GENESIS_COCKPIT_BROWSER_VALID');
  console.log(JSON.stringify(report, null, 2));
} catch (error) {
  console.error('GENESIS_COCKPIT_BROWSER_INVALID');
  console.error(error instanceof Error ? error.stack ?? error.message : String(error));
  process.exitCode = 1;
} finally {
  if (browser) await browser.close();
  await new Promise(resolve => server.close(resolve));
}
