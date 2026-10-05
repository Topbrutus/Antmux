#!/usr/bin/env node
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { fileURLToPath } from 'node:url';

import { CodexPlayerAdapter } from './codex-player-adapter.js';

const execFileAsync = promisify(execFile);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROVIDERS = Object.freeze(['CODEX', 'MUSE', 'GROK', 'ANTIGRAVITY']);
const SCHEMA = Object.freeze({
  type: 'object',
  additionalProperties: false,
  required: ['decision', 'move_id', 'note'],
  properties: {
    decision: { type: 'string', enum: ['PLAY', 'PASS'] },
    move_id: { type: ['string', 'null'] },
    note: { type: 'string', maxLength: 400 }
  }
});

function contextFor(provider) {
  const playerId = provider === 'MUSE' ? 'P2' : provider === 'GROK' ? 'P3' : provider === 'ANTIGRAVITY' ? 'P4' : 'P1';
  return Object.freeze({
    playerId,
    occupant: provider,
    role: 'NEUTRAL',
    score: 0,
    round: 1,
    revolution: false,
    hand: Object.freeze([
      Object.freeze({ id: 'SMOKE-CARD-3', rank: '3', label: 'Smoke calculation alpha', metadata: { calculation_id: 'CALC-SMOKE-A', tags: ['DOMAIN_INTEGER'] } }),
      Object.freeze({ id: 'SMOKE-CARD-4', rank: '4', label: 'Smoke calculation beta', metadata: { calculation_id: 'CALC-SMOKE-B', tags: ['DOMAIN_INTEGER'] } })
    ]),
    legalMoves: Object.freeze([
      Object.freeze({ moveId: 'MOVE-SMOKE-ALPHA', cardIds: ['SMOKE-CARD-3'], supportCardIds: [], targetCalculationId: null, rank: '3', count: 1, strength: 0, wouldFinish: false, wouldRevolt: false, wouldCut: false, sameRankSkip: false, target: null }),
      Object.freeze({ moveId: 'MOVE-SMOKE-BETA', cardIds: ['SMOKE-CARD-4'], supportCardIds: [], targetCalculationId: null, rank: '4', count: 1, strength: 1, wouldFinish: false, wouldRevolt: false, wouldCut: false, sameRankSkip: false, target: null })
    ]),
    targetCandidates: Object.freeze([]),
    currentTrick: Object.freeze({ count: 0, rank: null, cards: [], lastPlayerId: null }),
    publicPlayers: Object.freeze([
      Object.freeze({ playerId: 'P1', role: 'NEUTRAL', cardsRemaining: 2 }),
      Object.freeze({ playerId: 'P2', role: 'NEUTRAL', cardsRemaining: 2 }),
      Object.freeze({ playerId: 'P3', role: 'NEUTRAL', cardsRemaining: 2 }),
      Object.freeze({ playerId: 'P4', role: 'NEUTRAL', cardsRemaining: 2 })
    ])
  });
}

function promptFor(provider, context) {
  const legal = context.legalMoves.map(m => ({ moveId: m.moveId, cardIds: m.cardIds, rank: m.rank, count: m.count, strength: m.strength }));
  return [
    `You are ${provider}, a bounded GAMEZEL President-of-Formulas occupant.`,
    'Choose exactly one legal move from LEGAL_MOVES.',
    'Return PLAY with exactly one supplied move_id. Do not PASS because this is an opening trick.',
    'Never invent a card, target, support, calculation, formula, verdict, command, file, credential, or move id.',
    'Do not use tools, shell, filesystem, web, deployment, editing, external requests, or side effects.',
    'Do not expose chain-of-thought. note is only a short public summary.',
    `SEAT=${context.playerId}`,
    `LEGAL_MOVES=${JSON.stringify(legal)}`,
    'Return only structured JSON matching the schema.'
  ].join('\n');
}

function findJsonObjects(text) {
  const out = [];
  const source = String(text || '');
  for (let start = 0; start < source.length; start += 1) {
    if (source[start] !== '{') continue;
    let depth = 0;
    let inString = false;
    let escaped = false;
    for (let i = start; i < source.length; i += 1) {
      const ch = source[i];
      if (inString) {
        if (escaped) escaped = false;
        else if (ch === '\\') escaped = true;
        else if (ch === '"') inString = false;
        continue;
      }
      if (ch === '"') { inString = true; continue; }
      if (ch === '{') depth += 1;
      if (ch === '}') depth -= 1;
      if (depth === 0) {
        try { out.push(JSON.parse(source.slice(start, i + 1))); } catch (_) {}
        break;
      }
    }
  }
  return out;
}

function extractDecision(value, seen = new Set()) {
  if (value === null || value === undefined) return null;
  if (typeof value === 'string') {
    for (const candidate of findJsonObjects(value)) {
      const found = extractDecision(candidate, seen);
      if (found) return found;
    }
    return null;
  }
  if (typeof value !== 'object' || seen.has(value)) return null;
  seen.add(value);
  if (typeof value.decision === 'string' && Object.prototype.hasOwnProperty.call(value, 'move_id')) return value;
  if (Array.isArray(value)) {
    for (const item of value) {
      const found = extractDecision(item, seen);
      if (found) return found;
    }
    return null;
  }
  for (const nested of Object.values(value)) {
    const found = extractDecision(nested, seen);
    if (found) return found;
  }
  return null;
}

function parseJsonl(text) {
  const values = [];
  for (const line of String(text || '').split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    try { values.push(JSON.parse(trimmed)); } catch (_) { values.push(trimmed); }
  }
  return values;
}

function parseProviderDecision(stdout, stderr) {
  const found = extractDecision(parseJsonl(stdout)) || extractDecision(parseJsonl(stderr)) || extractDecision(stdout) || extractDecision(stderr);
  if (!found) throw new Error('NO_STRUCTURED_DECISION');
  return normalize(found);
}

function normalize(raw) {
  const decision = String(raw?.decision || '').trim().toUpperCase();
  const moveId = raw?.move_id ?? raw?.moveId ?? null;
  if (!['PLAY', 'PASS'].includes(decision)) throw new Error('INVALID_DECISION');
  if (decision === 'PLAY' && !moveId) throw new Error('PLAY_REQUIRES_MOVE');
  if (decision === 'PASS' && moveId != null) throw new Error('PASS_MUST_NOT_HAVE_MOVE');
  return { decision, moveId: moveId == null ? null : String(moveId), note: String(raw?.note || '').slice(0, 400) };
}

function classification(err) {
  const text = String(err?.stderr || err?.stdout || err?.message || err || '');
  const code = String(err?.code || err?.name || 'PROVIDER_ERROR').toUpperCase().replace(/[^A-Z0-9_:-]/g, '_').slice(0, 80) || 'PROVIDER_ERROR';
  return {
    code,
    trustedDirectoryError: /trusted directory|skip-git-repo-check/i.test(text),
    authRequired: /not logged in|login required|authentication|unauthorized|401|api.?key.*not configured/i.test(text),
    providerUnavailable: /credit|quota|rate.?limit|429|billing|capacity|timeout|unavailable/i.test(text),
    schemaError: /schema|structured output|output-schema/i.test(text),
    configError: /config|invalid value|failed to parse/i.test(text),
    modelError: /model.*(?:not found|unsupported|unavailable)|unsupported model/i.test(text),
    argumentError: /unexpected argument|unknown option|unrecognized option|invalid argument/i.test(text),
    permissionError: /permission|sandbox|read.?only/i.test(text),
    networkError: /network|connect|dns|tls|certificate/i.test(text)
  };
}

async function runExternal(provider, context) {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), `gamezel-step8-${provider.toLowerCase()}-`));
  const prompt = promptFor(provider, context);
  try {
    if (provider === 'MUSE') {
      const schemaPath = path.join(tmp, 'schema.json');
      fs.writeFileSync(schemaPath, JSON.stringify(SCHEMA));
      const bin = process.env.MUSE_BIN || path.join(os.homedir(), '.local', 'bin', 'muse');
      const { stdout, stderr } = await execFileAsync(bin, [
        'exec', '--json', '--output-schema', schemaPath,
        '--disable-web-tools', '--disable-write', '--disable-shell',
        '--approval-mode', 'never', '--no-session-log', '--max-model-steps', '1',
        '--workspace', tmp, prompt
      ], { timeout: 120000, maxBuffer: 4 * 1024 * 1024, env: process.env });
      return parseProviderDecision(stdout, stderr);
    }
    if (provider === 'GROK') {
      const bin = process.env.GROK_BIN || path.join(os.homedir(), '.grok', 'bin', 'grok');
      const { stdout, stderr } = await execFileAsync(bin, [
        '--single', prompt, '--json-schema', JSON.stringify(SCHEMA),
        '--max-turns', '1', '--no-subagents', '--disable-web-search',
        '--permission-mode', 'plan', '--cwd', tmp
      ], { timeout: 120000, maxBuffer: 4 * 1024 * 1024, env: process.env });
      return parseProviderDecision(stdout, stderr);
    }
    if (provider === 'ANTIGRAVITY') {
      const promptPath = path.join(tmp, 'prompt.txt');
      fs.writeFileSync(promptPath, prompt);
      const python = process.env.ANTIGRAVITY_PYTHON || path.join(os.homedir(), '.local/share/gamezel-antigravity-sdk/venv/bin/python');
      const bridge = process.env.ANTIGRAVITY_PRESIDENT_BRIDGE || path.join(__dirname, 'antigravity-president-agent.py');
      const { stdout, stderr } = await execFileAsync(python, [bridge, '--prompt-file', promptPath], { timeout: 120000, maxBuffer: 4 * 1024 * 1024, env: process.env });
      return parseProviderDecision(stdout, stderr);
    }
    throw new Error('UNSUPPORTED_PROVIDER');
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
}

async function run(provider) {
  const context = contextFor(provider);
  let decision;
  if (provider === 'CODEX') {
    const adapter = new CodexPlayerAdapter({
      bin: process.env.GAMEZEL_CODEX_BIN || path.join(os.homedir(), '.local', 'bin', 'codex'),
      timeoutMs: 120000
    });
    decision = await adapter.decideStrategy(context);
  } else {
    decision = await runExternal(provider, context);
  }
  const allowed = new Set(context.legalMoves.map(m => m.moveId));
  const legal = decision.decision === 'PLAY' && allowed.has(decision.moveId);
  return {
    provider,
    status: legal ? 'PASS' : 'INVALID_DECISION',
    decision: decision.decision,
    moveId: decision.moveId,
    legal,
    trustedDirectoryError: false,
    notePresent: Boolean(String(decision.note || '').trim())
  };
}

const provider = String(process.argv[2] || '').trim().toUpperCase();
if (!PROVIDERS.includes(provider)) {
  console.log(JSON.stringify({ status: 'INVALID_PROVIDER', allowed: PROVIDERS }));
  process.exitCode = 2;
} else {
  try {
    const result = await run(provider);
    console.log(JSON.stringify(result));
    if (result.status !== 'PASS') process.exitCode = 1;
  } catch (err) {
    console.log(JSON.stringify({ provider, status: 'PROVIDER_ERROR', ...classification(err) }));
    process.exitCode = 1;
  }
}
