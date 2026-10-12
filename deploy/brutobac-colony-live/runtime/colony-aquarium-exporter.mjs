#!/usr/bin/env node
import { mkdir, rename, writeFile } from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';

const EVENT_SCHEMA = 'BRUTUS-AQUARIUM-EVENT-v1';
const EXPORT_SCHEMA = 'BRUTOBAC-COLONY-PROJECTION-v0.1';

const SPECIALTY_VISUAL = Object.freeze({
  ARCHIVIST_COMPACTOR: { role: 'CARRIER', node: 'W:GENESIS-B', workState: 'TRANSPORTING' },
  FRESQUE_SCOUT: { role: 'SCOUT', node: 'E:GENESIS-A', workState: 'EXPLORING' },
  CALCULATOR: { role: 'RESONATOR', node: 'E:GENESIS-B', workState: 'RESONATING' },
  CRYSTAL_INSPECTOR: { role: 'HARVESTER', node: 'W:GENESIS-C', workState: 'HARVESTING' },
  COUNTER_TESTER: { role: 'QUEEN_GUARD', node: 'W:GENESIS-A', workState: 'EXPLORING' },
  PROVENANCE_AUDITOR: { role: 'ARCHITECT', node: 'E:GENESIS-C', workState: 'EXPLORING' },
  ASTRA_LIAISON: { role: 'SYNAPSE', node: 'E:OUTPUT', workState: 'RETURNING' }
});

function clampInt(value, fallback, min, max) {
  const n = Number(value);
  if (!Number.isInteger(n)) return fallback;
  return Math.max(min, Math.min(max, n));
}

function visualFor(specialty) {
  return SPECIALTY_VISUAL[String(specialty || '').toUpperCase()] || {
    role: 'SYNAPSE', node: 'W:GENESIS-C', workState: 'EXPLORING'
  };
}

function safeQuestMap(quests) {
  return new Map((Array.isArray(quests) ? quests : []).map((q) => [q?.quest_id, q]));
}

function crystalNode(level) {
  const n = Number(String(level || '').replace(/^L/i, ''));
  if (n >= 5) return 'CENTER';
  if (n === 4) return 'E:GENESIS-B';
  if (n === 3) return 'W:GENESIS-B';
  if (n === 2) return 'W:GENESIS-C';
  return 'W:START';
}

export class ColonyAquariumProjector {
  constructor({ now = () => Date.now(), replayHoldMs = 5500, retentionMs = 14000, maxEvents = 320 } = {}) {
    this.now = now;
    this.replayHoldMs = replayHoldMs;
    this.retentionMs = retentionMs;
    this.maxEvents = maxEvents;
    this.tick = Math.max(1, Math.floor(this.now()));
    this.events = [];
    this.antTracks = new Map();
    this.lastQueenSignature = null;
    this.seenCrystalEvents = new Set();
    this.lastStatusAt = 0;
  }

  nextTick() {
    this.tick += 1;
    return this.tick;
  }

  push(event) {
    this.events.push({ schema: EVENT_SCHEMA, ...event, tick: event.tick ?? this.nextTick() });
    if (this.events.length > this.maxEvents) this.events.splice(0, this.events.length - this.maxEvents);
  }

  emitStatus(connected, details = {}) {
    const now = this.now();
    if (connected && now - this.lastStatusAt < 1500) return;
    this.lastStatusAt = now;
    this.push({
      event_type: 'SYSTEM_STATUS',
      metadata: {
        connection_status: connected ? 'CONNECTED' : 'DISCONNECTED',
        connection_source: 'POLLING',
        source: 'BRUTUS_LIVING_COLONY_8812',
        authority: 'BRUTUS_QUEEN',
        bridge_mode: 'READ_ONLY',
        visualization_mode: 'REAL_QUEST_TIME_DILATED',
        ...details
      }
    });
  }

  emitQueen(state) {
    const queen = state?.queen || {};
    const signature = `${queen.generation ?? 0}:${queen.cycle ?? 0}:${state?.last_cycle_at ?? ''}`;
    if (signature === this.lastQueenSignature) return;
    this.lastQueenSignature = signature;
    const active = (state?.ants || []).filter((a) => ['BORN', 'WORKING', 'RETURNED_TO_QUEEN'].includes(a?.state)).length;
    this.push({
      event_type: this.events.some((e) => e.ant_id === 'QUEEN-BRUTUS') ? 'ANT_STATE' : 'ANT_BORN',
      ant_id: 'QUEEN-BRUTUS',
      role: 'QUEEN',
      state: 'RESONATING',
      position: 'CENTER',
      state_version: Math.max(1, Number(queen.generation || queen.cycle || 1)),
      pedigree: {
        lineage: 'BRUTUS-LIVING-COLONY',
        generation: Math.max(1, Number(queen.generation || 1)),
        queen_hash: 'BRUTUS',
        birth_tick: 1
      },
      metadata: {
        source: 'BRUTUS_LIVING_COLONY_8812',
        authority_mode: 'READ_ONLY_MIRROR',
        queen_generation: Number(queen.generation || 0),
        queen_cycle: Number(queen.cycle || 0),
        active_ants: active,
        total_ants_born: Number(state?.counters?.ant || 0),
        queued_quests: (state?.quests || []).filter((q) => q?.status === 'QUEUED').length,
        running_quests: (state?.quests || []).filter((q) => q?.status === 'RUNNING').length,
        astra_letters: Number(state?.astra_mailbox?.length || 0),
        visualization_mode: 'AUTHORITY_STATE'
      }
    });
  }

  emitAntBorn(ant, quest, firstSeenState) {
    const visual = visualFor(ant?.specialty);
    const track = {
      antId: ant.ant_id,
      specialty: ant.specialty || 'UNKNOWN',
      questId: ant.quest_id || null,
      version: 1,
      phase: 'BORN',
      firstSeenAt: this.now(),
      lastRawState: null,
      taskNode: visual.node,
      returnedAt: null,
      removed: false
    };
    this.antTracks.set(ant.ant_id, track);
    this.push({
      event_type: 'ANT_BORN',
      ant_id: ant.ant_id,
      role: visual.role,
      state: 'SINGING_TO_MEET',
      position: 'CENTER',
      state_version: track.version,
      pedigree: {
        lineage: `BRUTUS-${track.specialty}`,
        generation: Math.max(1, Number(ant?.generation || 1)),
        queen_hash: 'BRUTUS',
        birth_tick: this.tick
      },
      metadata: this.antMetadata(ant, quest, firstSeenState)
    });
    return track;
  }

  antMetadata(ant, quest, rawState) {
    return {
      source: 'BRUTUS_LIVING_COLONY_8812',
      authority_mode: 'READ_ONLY_MIRROR',
      specialty: ant?.specialty || null,
      quest_id: ant?.quest_id || null,
      quest_type: quest?.type || null,
      quest_status: quest?.status || null,
      result_status: quest?.result_status || null,
      colony_state: rawState || ant?.state || null,
      target: quest?.target || null,
      reason: quest?.reason || null,
      born_at: ant?.born_at || null,
      recycled_at: ant?.recycled_at || null,
      visualization_mode: 'REAL_QUEST_TIME_DILATED'
    };
  }

  moveAntToTask(track, ant, quest) {
    if (track.phase === 'WORK') return;
    const visual = visualFor(ant?.specialty);
    track.version += 1;
    track.phase = 'WORK';
    this.push({
      event_type: 'ANT_MOVE',
      ant_id: ant.ant_id,
      role: visual.role,
      state: visual.workState,
      position: visual.node,
      previous_position: 'CENTER',
      state_version: track.version,
      last_move_tick: this.tick,
      metadata: this.antMetadata(ant, quest, ant?.state)
    });
  }

  returnAntToQueen(track, ant, quest) {
    if (track.phase === 'RETURNED' || track.removed) return;
    track.version += 1;
    track.phase = 'RETURNED';
    track.returnedAt = this.now();
    this.push({
      event_type: 'ANT_MOVE',
      ant_id: ant.ant_id,
      role: visualFor(ant?.specialty).role,
      state: 'RETURNING',
      position: 'CENTER',
      previous_position: track.taskNode,
      state_version: track.version,
      last_move_tick: this.tick,
      metadata: this.antMetadata(ant, quest, ant?.state)
    });
  }

  removeAnt(track, ant, quest) {
    if (track.removed) return;
    track.version += 1;
    track.removed = true;
    this.push({
      event_type: 'ANT_REMOVED',
      ant_id: ant.ant_id,
      state_version: track.version,
      metadata: this.antMetadata(ant, quest, ant?.state)
    });
  }

  emitCrystals(state) {
    for (const event of state?.crystal_watch?.newest_events || []) {
      const key = `${event.type}:${event.level}:${event.count}:${event.observed_at}`;
      if (this.seenCrystalEvents.has(key)) continue;
      this.seenCrystalEvents.add(key);
      if (this.seenCrystalEvents.size > 500) {
        this.seenCrystalEvents = new Set([...this.seenCrystalEvents].slice(-250));
      }
      this.push({
        event_type: 'CRYSTAL_UPDATE',
        crystal: {
          crystal_id: `CRYSTAL-${String(event.level || 'L?').toUpperCase()}`,
          material_id: `LEVEL-${String(event.level || 'L?').toUpperCase()}`,
          material_h256: '0'.repeat(64),
          type: Number(String(event.level || '').replace(/^L/i, '')) >= 5 ? 'DEEP_CELESTIAL_CORE' : 'OCEANIC_CRYSTAL',
          state: event.type === 'NEW_HIGHEST_LEVEL' ? 'OVERCHARGED' : 'RESONATING',
          node_id: crystalNode(event.level),
          purity: 100,
          energy: Number(event.delta || 0)
        },
        metadata: {
          source: 'BRUTUS_CRYSTAL_WATCH',
          level: event.level,
          count: Number(event.count || 0),
          delta: Number(event.delta || 0),
          event_kind: event.type,
          observed_at_utc: event.observed_at || null
        }
      });
    }
  }

  ingest(rawPayload) {
    const state = rawPayload?.colony || rawPayload;
    if (!state || state?.schema !== 'BRUTUS-LIVING-COLONY-v0.1') {
      throw new Error('COLONY_STATE_SCHEMA_MISMATCH');
    }
    this.emitStatus(true, { queen_generation: state?.queen?.generation ?? null, queen_cycle: state?.queen?.cycle ?? null });
    this.emitQueen(state);
    this.emitCrystals(state);

    const quests = safeQuestMap(state.quests);
    const ants = Array.isArray(state.ants) ? state.ants : [];
    const recent = ants.slice(-160);
    const currentIds = new Set();

    for (const ant of recent) {
      if (!ant?.ant_id) continue;
      currentIds.add(ant.ant_id);
      const quest = quests.get(ant.quest_id) || null;
      let track = this.antTracks.get(ant.ant_id);
      if (!track) track = this.emitAntBorn(ant, quest, ant.state);

      if (ant.state === 'WORKING') {
        this.moveAntToTask(track, ant, quest);
      } else if (ant.state === 'RETURNED_TO_QUEEN') {
        this.moveAntToTask(track, ant, quest);
        this.returnAntToQueen(track, ant, quest);
      } else if (ant.state === 'RECYCLED') {
        if (track.phase === 'BORN') this.moveAntToTask(track, ant, quest);
        const age = this.now() - track.firstSeenAt;
        if (age >= this.replayHoldMs) this.returnAntToQueen(track, ant, quest);
        if (track.returnedAt !== null && this.now() - track.returnedAt >= this.retentionMs) this.removeAnt(track, ant, quest);
      }
      track.lastRawState = ant.state;
    }

    for (const [antId, track] of this.antTracks) {
      if (track.removed && this.now() - (track.returnedAt || track.firstSeenAt) > this.retentionMs * 2) {
        this.antTracks.delete(antId);
      }
    }

    return this.snapshot();
  }

  disconnected(error) {
    this.emitStatus(false, { error: String(error?.message || error).slice(0, 400) });
    return this.snapshot();
  }

  snapshot() {
    return this.events.slice();
  }
}

async function atomicJsonWrite(filePath, value) {
  await mkdir(path.dirname(filePath), { recursive: true });
  const tmp = `${filePath}.tmp-${process.pid}-${Date.now()}`;
  await writeFile(tmp, `${JSON.stringify(value)}\n`, 'utf8');
  await rename(tmp, filePath);
}

export async function runExporter({
  sourceUrl = process.env.BRUTOBAC_COLONY_STATE_URL || 'http://127.0.0.1:8812/api/state',
  outputPath = process.env.BRUTOBAC_PUBLIC_EVENTS_PATH || '/var/www/antmux.com/public_html/brutus/brutobac/live-events.json',
  pollMs = clampInt(process.env.BRUTOBAC_COLONY_POLL_MS, 250, 100, 5000),
  signal = null,
  fetchImpl = fetch,
  projector = new ColonyAquariumProjector()
} = {}) {
  const controller = signal || new AbortController();
  let stopped = false;
  const stop = () => { stopped = true; };
  if (controller?.signal) controller.signal.addEventListener('abort', stop, { once: true });

  while (!stopped) {
    const started = Date.now();
    try {
      const response = await fetchImpl(sourceUrl, { headers: { Accept: 'application/json' }, cache: 'no-store' });
      if (!response.ok) throw new Error(`COLONY_HTTP_${response.status}`);
      const payload = await response.json();
      await atomicJsonWrite(outputPath, projector.ingest(payload));
    } catch (error) {
      await atomicJsonWrite(outputPath, projector.disconnected(error));
    }
    const remaining = Math.max(20, pollMs - (Date.now() - started));
    await new Promise((resolve) => setTimeout(resolve, remaining));
  }
}

async function main() {
  const abort = new AbortController();
  process.on('SIGTERM', () => abort.abort());
  process.on('SIGINT', () => abort.abort());
  process.stdout.write(`${JSON.stringify({ schema: EXPORT_SCHEMA, status: 'STARTING' })}\n`);
  await runExporter({ signal: abort });
}

if (import.meta.url === `file://${process.argv[1]?.replaceAll('\\', '/')}` || process.argv[1]?.endsWith('colony-aquarium-exporter.mjs')) {
  main().catch((error) => {
    process.stderr.write(`${error?.stack || error}\n`);
    process.exit(1);
  });
}

export { EVENT_SCHEMA, EXPORT_SCHEMA, SPECIALTY_VISUAL };
