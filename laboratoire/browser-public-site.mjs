#!/usr/bin/env node

import { createServer } from 'node:http';
import { mkdir, readFile, stat, writeFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const REPO_ROOT = fileURLToPath(new URL('../', import.meta.url));
const EVIDENCE_DIR = join(REPO_ROOT, '.build', 'antmux-lab-browser-evidence');

const MIME = new Map([
  ['.html', 'text/html; charset=utf-8'],
  ['.css', 'text/css; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'],
  ['.mjs', 'text/javascript; charset=utf-8'],
  ['.json', 'application/json; charset=utf-8'],
  ['.md', 'text/markdown; charset=utf-8']
]);

function fail(message) { throw new Error(message); }
function assert(condition, message) { if (!condition) fail(message); }

async function resolvePublicPath(urlPath) {
  const decoded = decodeURIComponent((urlPath ?? '/').split('?')[0]);
  let relative = decoded.replace(/^\/+/, '');
  if (!relative || relative.endsWith('/')) relative += 'index.html';
  const normalized = normalize(relative);
  if (normalized.startsWith('..') || normalized.includes('/../') || normalized.includes('\\..\\')) {
    fail('Traversal de chemin refusé.');
  }
  let path = join(REPO_ROOT, normalized);
  try {
    const info = await stat(path);
    if (info.isDirectory()) path = join(path, 'index.html');
  } catch {
    // Le serveur retournera 404.
  }
  return path;
}

const server = createServer(async (request, response) => {
  try {
    const filePath = await resolvePublicPath(request.url);
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

async function assertNoOverflow(page, label) {
  const geometry = await page.evaluate(() => ({
    viewportWidth: window.innerWidth,
    scrollWidth: document.documentElement.scrollWidth
  }));
  assert(geometry.scrollWidth <= geometry.viewportWidth + 1,
    `${label}: débordement horizontal (${geometry.scrollWidth} > ${geometry.viewportWidth}).`);
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
    let response = await page.goto(`${base}/`, { waitUntil: 'networkidle' });
    assert(response?.ok(), `${viewportName}: accueil Antmux inaccessible.`);
    assert((await page.title()) === 'Antmux — Générateur de Fourmis', `${viewportName}: titre accueil inattendu.`);

    const labButton = page.locator('a[href="./laboratoire/"]');
    assert(await labButton.isVisible(), `${viewportName}: bouton LABORATOIRE invisible à l'accueil.`);
    assert((await labButton.textContent())?.trim() === 'LABORATOIRE', `${viewportName}: libellé bouton laboratoire inattendu.`);
    await assertNoOverflow(page, `${viewportName}/accueil`);

    await labButton.click();
    await page.waitForLoadState('networkidle');
    assert(new URL(page.url()).pathname === '/laboratoire/', `${viewportName}: navigation laboratoire incorrecte.`);
    assert((await page.title()) === 'Antmux — Laboratoire public', `${viewportName}: titre laboratoire inattendu.`);
    assert((await page.locator('h1').textContent())?.trim() === 'Laboratoire', `${viewportName}: H1 laboratoire absent.`);
    assert(await page.getByText('LAB-004 · DEMO VALIDÉE EN CI', { exact: true }).isVisible(), `${viewportName}: statut LAB-004 absent.`);

    const genesisButton = page.locator('a.primary[href="./genesis/"]').first();
    assert(await genesisButton.isVisible(), `${viewportName}: bouton Genesis invisible dans le laboratoire.`);
    await page.screenshot({ path: join(EVIDENCE_DIR, `${viewportName}-laboratoire.png`), fullPage: true });
    await assertNoOverflow(page, `${viewportName}/laboratoire`);

    await genesisButton.click();
    await page.waitForLoadState('networkidle');
    assert(new URL(page.url()).pathname === '/laboratoire/genesis/', `${viewportName}: navigation Genesis incorrecte.`);
    assert((await page.title()) === 'Genesis Vision Center — DEMO', `${viewportName}: titre Genesis inattendu.`);
    await page.locator('#cockpit').waitFor({ state: 'visible', timeout: 5000 });
    assert((await page.locator('#demoBanner').textContent())?.trim() === 'DEMO / SYNTHETIC DATA', `${viewportName}: bannière DEMO absente.`);
    assert((await page.locator('#mode').textContent())?.trim() === 'DEMO', `${viewportName}: mode Genesis inattendu.`);
    assert((await page.locator('#sourceStatus').textContent())?.trim() === 'SYNTHETIC', `${viewportName}: source Genesis inattendue.`);
    assert(!(await page.locator('#fatal').isVisible()), `${viewportName}: état fatal Genesis visible.`);
    await page.screenshot({ path: join(EVIDENCE_DIR, `${viewportName}-genesis.png`), fullPage: true });
    await assertNoOverflow(page, `${viewportName}/genesis`);

    assert(pageErrors.length === 0, `${viewportName}: erreurs JavaScript: ${pageErrors.join(' | ')}`);
    assert(consoleErrors.length === 0, `${viewportName}: erreurs console: ${consoleErrors.join(' | ')}`);
    assert(!requestedPaths.some(path => path.startsWith('/private/')), `${viewportName}: route privée demandée.`);

    return {
      viewport: viewportName,
      size: viewport,
      home_button_visible: true,
      laboratory_rendered: true,
      genesis_rendered: true,
      genesis_mode: 'DEMO',
      source_status: 'SYNTHETIC',
      private_route_requested: false,
      horizontal_overflow: false,
      browser_console_errors: 0,
      browser_page_errors: 0,
      screenshots: [
        `.build/antmux-lab-browser-evidence/${viewportName}-laboratoire.png`,
        `.build/antmux-lab-browser-evidence/${viewportName}-genesis.png`
      ]
    };
  } finally {
    await context.close();
  }
}

try {
  const address = server.address();
  if (!address || typeof address === 'string') fail('Port HTTP de test indisponible.');
  const base = `http://127.0.0.1:${address.port}`;
  await mkdir(EVIDENCE_DIR, { recursive: true });

  browser = await chromium.launch({ headless: true });
  const results = [
    await verifyViewport(base, 'desktop', { width: 1440, height: 1000 }),
    await verifyViewport(base, 'mobile', { width: 390, height: 844 })
  ];

  const report = {
    ok: true,
    lab: 'LAB-004',
    test: 'ANTMUX_HOME_TO_LAB_TO_GENESIS_REAL_BROWSER',
    browser: 'Chromium',
    browser_version: browser.version(),
    home_button: '/laboratoire/',
    lab_entry: '/laboratoire/',
    genesis_entry: '/laboratoire/genesis/',
    private_genesis_connected: false,
    viewports: results
  };

  await writeFile(join(EVIDENCE_DIR, 'REPORT.json'), `${JSON.stringify(report, null, 2)}\n`, 'utf8');
  console.log('ANTMUX_LAB_PUBLIC_BROWSER_VALID');
  console.log(JSON.stringify(report, null, 2));
} catch (error) {
  console.error('ANTMUX_LAB_PUBLIC_BROWSER_INVALID');
  console.error(error instanceof Error ? error.stack ?? error.message : String(error));
  process.exitCode = 1;
} finally {
  if (browser) await browser.close();
  await new Promise(resolve => server.close(resolve));
}
