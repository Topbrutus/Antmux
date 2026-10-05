#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: apply-provider-cooldown5h.py RUNNER_PATH')

src_path = Path(sys.argv[1])
src = src_path.read_text(encoding='utf-8')

if 'export const PROVIDER_NO_RESPONSE_COOLDOWN_MS = 5 * 60 * 60 * 1000;' in src:
    print('COOLDOWN_PATCH=ALREADY_PRESENT')
    raise SystemExit(0)

marker = """});

export const DECISION_SCHEMA = Object.freeze({
"""
insert = """});

export const PROVIDER_NO_RESPONSE_COOLDOWN_MS = 5 * 60 * 60 * 1000;

function providerCooldownPath(playerId, env = process.env) {
  const stateRoot = env.GAMEZEL_AGENT_STATE_DIR ||
    path.join(os.homedir(), '.gamezel-agent-state');
  fs.mkdirSync(stateRoot, { recursive: true });
  return path.join(stateRoot, `${String(playerId).toLowerCase()}-provider-cooldown.json`);
}

export function readProviderCooldown(playerId, env = process.env) {
  const filePath = providerCooldownPath(playerId, env);
  try {
    const parsed = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    const sleepUntil = Number(parsed?.sleep_until || 0);
    if (!Number.isFinite(sleepUntil) || sleepUntil <= 0) return null;
    return {
      player_id: String(playerId).toUpperCase(),
      reason: 'provider_no_response',
      sleep_until: sleepUntil
    };
  } catch (_) {
    return null;
  }
}

export function startProviderCooldown(playerId, nowMs, env = process.env) {
  const base = Number(nowMs);
  if (!Number.isFinite(base)) throw new Error('Invalid cooldown clock');
  const state = {
    player_id: String(playerId).toUpperCase(),
    reason: 'provider_no_response',
    sleep_until: base + PROVIDER_NO_RESPONSE_COOLDOWN_MS
  };
  const filePath = providerCooldownPath(playerId, env);
  const tmpPath = `${filePath}.${process.pid}.${base}.tmp`;
  fs.writeFileSync(tmpPath, JSON.stringify(state) + '\n', { encoding: 'utf8', mode: 0o600 });
  fs.renameSync(tmpPath, filePath);
  try { fs.chmodSync(filePath, 0o600); } catch (_) {}
  return state;
}

export function clearProviderCooldown(playerId, env = process.env) {
  const filePath = providerCooldownPath(playerId, env);
  try { fs.unlinkSync(filePath); } catch (err) {
    if (err?.code !== 'ENOENT') throw err;
  }
}

function currentTimeMs(options = {}) {
  const raw = typeof options.now === 'function' ? options.now() : Date.now();
  const value = Number(raw);
  return Number.isFinite(value) ? value : Date.now();
}

export const DECISION_SCHEMA = Object.freeze({
"""
if src.count(marker) != 1:
    raise SystemExit(f'profile/schema marker count={src.count(marker)}')
src = src.replace(marker, insert, 1)

old_turn = """  const startingRound = state.round;
  const decision = normalizeDecision(await decide(state));

  const fresh = await cli(['status', '--json']);
  const freshCurrent = fresh.currentTurn || fresh.current_turn;
  if (!fresh.roundActive || fresh.round !== startingRound || freshCurrent?.PLAYER_ID !== playerId) {
    return { action: 'STALE_DECISION_DISCARDED', decision, state: fresh };
  }
"""
new_turn = """  const startingRound = state.round;
  const nowMs = currentTimeMs(options);
  const cooldown = readProviderCooldown(playerId, env);

  if (cooldown && cooldown.sleep_until > nowMs) {
    const fresh = await cli(['status', '--json']);
    const freshCurrent = fresh.currentTurn || fresh.current_turn;
    if (!fresh.roundActive || fresh.round !== startingRound || freshCurrent?.PLAYER_ID !== playerId) {
      return {
        action: 'COOLDOWN_WAIT',
        cooldown_until: cooldown.sleep_until,
        state: fresh
      };
    }
    const result = await cli(['pass', '--json']);
    return {
      action: 'COOLDOWN_PASS',
      cooldown_until: cooldown.sleep_until,
      result
    };
  }

  if (cooldown) clearProviderCooldown(playerId, env);

  let decision;
  try {
    decision = normalizeDecision(await decide(state));
  } catch (_) {
    const sleeping = startProviderCooldown(playerId, nowMs, env);
    const fresh = await cli(['status', '--json']);
    const freshCurrent = fresh.currentTurn || fresh.current_turn;
    if (!fresh.roundActive || fresh.round !== startingRound || freshCurrent?.PLAYER_ID !== playerId) {
      return {
        action: 'NO_RESPONSE_COOLDOWN_STALE',
        cooldown_until: sleeping.sleep_until,
        state: fresh
      };
    }
    const result = await cli(['pass', '--json']);
    return {
      action: 'NO_RESPONSE_COOLDOWN',
      cooldown_until: sleeping.sleep_until,
      result
    };
  }

  clearProviderCooldown(playerId, env);

  const fresh = await cli(['status', '--json']);
  const freshCurrent = fresh.currentTurn || fresh.current_turn;
  if (!fresh.roundActive || fresh.round !== startingRound || freshCurrent?.PLAYER_ID !== playerId) {
    return { action: 'STALE_DECISION_DISCARDED', decision, state: fresh };
  }
"""
if src.count(old_turn) != 1:
    raise SystemExit(f'runTurnOnce marker count={src.count(old_turn)}')
src = src.replace(old_turn, new_turn, 1)

src_path.write_text(src, encoding='utf-8')
print('COOLDOWN_PATCH=APPLIED')
