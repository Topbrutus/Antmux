import { spawn } from 'node:child_process';
import fs from 'node:fs';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

export const CODEX_SAFE_STRATEGIES = Object.freeze([
  'USE_ROLE_DEFAULT',
  'CONNECT',
  'FORMULA_COMPARE',
  'FORMULA_COUNTERTEST'
]);

const OUTPUT_SCHEMA = Object.freeze({
  type: 'object',
  properties: {
    strategy: { type: 'string', enum: [...CODEX_SAFE_STRATEGIES] },
    target_formula_id: { type: ['string', 'null'] },
    note: { type: 'string', maxLength: 600 }
  },
  required: ['strategy', 'target_formula_id', 'note'],
  additionalProperties: false
});

export const CODEX_PRESIDENT_OUTPUT_SCHEMA = Object.freeze({
  type: 'object',
  additionalProperties: false,
  required: ['decision', 'move_id', 'note'],
  properties: {
    decision: { type: 'string', enum: ['PLAY', 'PASS'] },
    move_id: { type: ['string', 'null'] },
    note: { type: 'string', maxLength: 400 }
  }
});

function resolveCodexBin(explicit) {
  if (explicit) return explicit;
  const local = path.join(os.homedir(), '.local', 'bin', 'codex');
  if (fs.existsSync(local)) return local;
  return 'codex';
}

function boundedText(value, max = 24000) {
  const text = JSON.stringify(value ?? null);
  return text.length > max ? text.slice(0, max) : text;
}

function runProcess(bin, args, options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(bin, args, {
      cwd: options.cwd || process.cwd(),
      env: options.env || process.env,
      stdio: ['ignore', 'pipe', 'pipe'],
      windowsHide: true
    });

    let stdout = '';
    let stderr = '';
    const maxOutput = Number(options.maxOutput || 1024 * 1024);
    const timer = setTimeout(() => {
      child.kill('SIGTERM');
      const err = new Error('CODEX provider timeout');
      err.code = 'PROVIDER_UNAVAILABLE';
      reject(err);
    }, Number(options.timeoutMs || 90000));

    child.stdout.on('data', chunk => {
      if (stdout.length < maxOutput) stdout += String(chunk);
    });
    child.stderr.on('data', chunk => {
      if (stderr.length < maxOutput) stderr += String(chunk);
    });
    child.on('error', err => {
      clearTimeout(timer);
      const wrapped = new Error(`CODEX adapter not ready: ${err.message}`);
      wrapped.code = 'CODEX_NOT_READY';
      reject(wrapped);
    });
    child.on('close', code => {
      clearTimeout(timer);
      if (code !== 0) {
        const detail = (stderr || stdout || `exit ${code}`).trim().slice(0, 1200);
        const authRequired = /(not logged in|login required|authentication|required.*login|unauthorized|401)/i.test(detail);
        const quotaUnavailable = /(credit|credits|quota|rate.?limit|429|billing|resource[_ -]?exhausted|capacity|temporar(?:y|ily).?unavailable|timeout)/i.test(detail);
        const err = new Error(
          authRequired
            ? `CODEX authentication required: ${detail}`
            : quotaUnavailable
              ? `CODEX provider unavailable: ${detail}`
              : `CODEX adapter failed: ${detail}`
        );
        err.code = authRequired
          ? 'CODEX_AUTH_REQUIRED'
          : quotaUnavailable
            ? 'PROVIDER_UNAVAILABLE'
            : 'CODEX_NOT_READY';
        reject(err);
        return;
      }
      resolve({ stdout, stderr, code });
    });
  });
}

function codexExecArgs({ prompt, schemaPath, outputPath, model }) {
  const args = [
    'exec',
    '--skip-git-repo-check',
    '--ephemeral',
    '--ignore-user-config',
    '--ignore-rules',
    '--sandbox', 'read-only',
    '--config', 'approval_policy="never"',
    '--config', 'web_search="disabled"',
    '--output-schema', schemaPath,
    '-o', outputPath
  ];
  if (model) args.push('--model', model);
  args.push(prompt);
  return args;
}

function presidentPrompt(context = {}) {
  const legalMoves = Array.isArray(context.legalMoves) ? context.legalMoves : [];
  const compactMoves = legalMoves.map(move => ({
    moveId: move.moveId,
    cardIds: move.cardIds,
    supportCardIds: move.supportCardIds,
    targetCalculationId: move.targetCalculationId,
    rank: move.rank,
    count: move.count,
    strength: move.strength,
    wouldFinish: Boolean(move.wouldFinish),
    wouldRevolt: Boolean(move.wouldRevolt),
    wouldCut: Boolean(move.wouldCut),
    sameRankSkip: Boolean(move.sameRankSkip),
    target: move.target || null
  }));

  return [
    'You are CODEX acting only as a bounded strategic occupant inside GAMEZEL President of Formulas.',
    'You have no authority to create cards, targets, support cards, files, commands, deployments, credentials, or scientific verdicts.',
    'Choose exactly PLAY or PASS.',
    'For PLAY, move_id MUST be exactly one moveId from LEGAL_MOVES.',
    'For PASS, move_id MUST be null. PASS is useful only when a trick is already active.',
    'Do not use shell, filesystem, web, external tools, deployment, editing, or repository inspection.',
    'Reason only from the supplied bounded game context.',
    '',
    `SEAT=${String(context.playerId || '')}`,
    `OCCUPANT=${String(context.occupant || 'CODEX')}`,
    `ROLE=${String(context.role || '')}`,
    `ROUND=${Number(context.round || 0)}`,
    `REVOLUTION=${Boolean(context.revolution)}`,
    `CURRENT_TRICK=${boundedText(context.currentTrick, 4000)}`,
    `OWN_HAND=${boundedText(context.hand, 8000)}`,
    `PUBLIC_PLAYERS=${boundedText(context.publicPlayers, 6000)}`,
    `LEGAL_MOVES=${boundedText(compactMoves, 16000)}`,
    '',
    'Return only the structured decision required by the output schema.'
  ].join('\n');
}

export class CodexPlayerAdapter {
  constructor(options = {}) {
    this.bin = resolveCodexBin(options.bin || process.env.GAMEZEL_CODEX_BIN);
    this.workdir = options.workdir || process.env.GAMEZEL_CODEX_WORKDIR || process.cwd();
    this.timeoutMs = Number(options.timeoutMs || process.env.GAMEZEL_CODEX_TIMEOUT_MS || 90000);
    this.model = options.model || process.env.GAMEZEL_CODEX_MODEL || null;
    this.processRunner = options.processRunner || runProcess;
  }

  getStatus() {
    const absolute = path.isAbsolute(this.bin);
    return {
      provider: 'CODEX',
      configured: absolute ? fs.existsSync(this.bin) : true,
      binary: absolute ? this.bin : 'PATH:codex',
      workdir: this.workdir,
      mode: 'ISOLATED_READ_ONLY_DECISION_ADAPTER',
      strategies: [...CODEX_SAFE_STRATEGIES],
      presidentContract: 'PLAY_PASS_MOVE_ID',
      skipGitRepoCheck: true,
      ephemeral: true,
      isolatedTempCwd: true
    };
  }

  async decide(context = {}) {
    const tmp = await mkdtemp(path.join(os.tmpdir(), 'gamezel-codex-'));
    const schemaPath = path.join(tmp, 'decision.schema.json');
    const outputPath = path.join(tmp, 'decision.json');

    try {
      await writeFile(schemaPath, JSON.stringify(OUTPUT_SCHEMA), 'utf8');
      const formulaIds = Array.from(new Set(
        (context.formulas || []).map(f => String(f?.FORMULA_ID || f?.formula_id || '').trim()).filter(Boolean)
      ));
      const prompt = [
        'You are CODEX acting as a bounded GAMEZEL player occupant.',
        'You are NOT allowed to edit files, run deployment actions, alter credentials, or bypass GAMEZEL authority.',
        'Choose exactly one safe strategy from the supplied schema.',
        'If choosing a formula strategy, target_formula_id must be one of the formula ids supplied below; otherwise use null.',
        'Prefer USE_ROLE_DEFAULT when the seat role already matches the useful next action.',
        '',
        `SEAT=${String(context.playerId || '')}`,
        `ROLE=${String(context.role || '')}`,
        `GAME=${Number(context.gameNumber || 0)}`,
        `FORMULA_IDS=${JSON.stringify(formulaIds)}`,
        `BASE_CARD=${boundedText(context.baseCard, 8000)}`,
        `GAME_STATE=${boundedText(context.gameState, 8000)}`,
        '',
        'Return only the structured decision required by the output schema.'
      ].join('\n');
      const args = codexExecArgs({ prompt, schemaPath, outputPath, model: this.model });
      await this.processRunner(this.bin, args, { cwd: tmp, timeoutMs: this.timeoutMs });
      const parsed = JSON.parse(await readFile(outputPath, 'utf8'));
      if (!CODEX_SAFE_STRATEGIES.includes(parsed.strategy)) throw new Error('CODEX returned an unsupported GAMEZEL strategy');
      if (parsed.target_formula_id !== null && !formulaIds.includes(String(parsed.target_formula_id))) {
        throw new Error('CODEX returned a formula outside the supplied GAMEZEL set');
      }
      return { provider: 'CODEX', strategy: parsed.strategy, targetFormulaId: parsed.target_formula_id, note: String(parsed.note || '').slice(0, 600) };
    } catch (err) {
      if (err?.code) throw err;
      const wrapped = new Error(`CODEX adapter failed: ${err?.message || err}`);
      wrapped.code = 'CODEX_NOT_READY';
      throw wrapped;
    } finally {
      await rm(tmp, { recursive: true, force: true }).catch(() => {});
    }
  }

  async decideStrategy(context = {}) {
    const tmp = await mkdtemp(path.join(os.tmpdir(), 'gamezel-codex-president-'));
    const schemaPath = path.join(tmp, 'decision.schema.json');
    const outputPath = path.join(tmp, 'decision.json');
    try {
      await writeFile(schemaPath, JSON.stringify(CODEX_PRESIDENT_OUTPUT_SCHEMA), 'utf8');
      const prompt = presidentPrompt(context);
      const args = codexExecArgs({ prompt, schemaPath, outputPath, model: this.model });
      await this.processRunner(this.bin, args, { cwd: tmp, timeoutMs: this.timeoutMs });
      const parsed = JSON.parse(await readFile(outputPath, 'utf8'));
      const decision = String(parsed?.decision || '').trim().toUpperCase();
      if (!['PLAY', 'PASS'].includes(decision)) throw new Error('CODEX returned an invalid President decision');
      const moveId = parsed?.move_id === null || parsed?.move_id === undefined ? null : String(parsed.move_id).trim();
      if (decision === 'PLAY' && !moveId) throw new Error('CODEX PLAY decision requires move_id');
      if (decision === 'PASS' && moveId) throw new Error('CODEX PASS decision must not include move_id');
      return { decision, moveId, note: String(parsed?.note || '').slice(0, 400) };
    } catch (err) {
      if (err?.code) throw err;
      const wrapped = new Error(`CODEX President adapter failed: ${err?.message || err}`);
      wrapped.code = 'CODEX_NOT_READY';
      throw wrapped;
    } finally {
      await rm(tmp, { recursive: true, force: true }).catch(() => {});
    }
  }
}

export const defaultCodexPlayerAdapter = new CodexPlayerAdapter();
