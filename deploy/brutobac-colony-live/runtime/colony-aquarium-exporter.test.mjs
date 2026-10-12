import test from 'node:test';
import assert from 'node:assert/strict';

import { ColonyAquariumProjector } from './colony-aquarium-exporter.mjs';

function makeState({ antState = 'RECYCLED', generation = 7, cycle = 7 } = {}) {
  return {
    schema: 'BRUTUS-LIVING-COLONY-v0.1',
    queen: { id: 'BRUTUS', role: 'QUEEN', generation, cycle },
    counters: { ant: 12 },
    ants: [
      {
        ant_id: 'ANT-ABCDEF123456',
        generation,
        specialty: 'FRESQUE_SCOUT',
        quest_id: 'QUEST-FRESQUE_SCAN-000012',
        born_at: '2026-10-12T03:00:00Z',
        state: antState,
        recycled_at: antState === 'RECYCLED' ? '2026-10-12T03:00:01Z' : null
      }
    ],
    quests: [
      {
        quest_id: 'QUEST-FRESQUE_SCAN-000012',
        type: 'FRESQUE_SCAN',
        specialty: 'FRESQUE_SCOUT',
        target: 'TABLE:ADD:7:49',
        status: antState === 'RECYCLED' ? 'DONE' : 'RUNNING',
        result_status: antState === 'RECYCLED' ? 'PASS' : null,
        reason: 'CONTINUOUS_FRESQUE_INSPECTION'
      }
    ],
    astra_mailbox: [],
    crystal_watch: {
      levels: { L1: 1000, L4: 5 },
      highest_level: 'L4',
      newest_events: [
        { type: 'CRYSTAL_COUNT_INCREASE', level: 'L4', delta: 1, count: 5, observed_at: '2026-10-12T03:00:00Z' }
      ]
    },
    last_cycle_at: '2026-10-12T03:00:01Z'
  };
}

test('projects real queen, ant identity, quest metadata and crystal watch into aquarium events', () => {
  let now = 1000;
  const projector = new ColonyAquariumProjector({ now: () => now, replayHoldMs: 5000, retentionMs: 5000 });
  const events = projector.ingest(makeState({ antState: 'RECYCLED' }));

  const queen = events.find((e) => e.ant_id === 'QUEEN-BRUTUS');
  assert.equal(queen.role, 'QUEEN');
  assert.equal(queen.position, 'CENTER');
  assert.equal(queen.metadata.queen_generation, 7);

  const born = events.find((e) => e.event_type === 'ANT_BORN' && e.ant_id === 'ANT-ABCDEF123456');
  assert.ok(born);
  assert.equal(born.metadata.quest_id, 'QUEST-FRESQUE_SCAN-000012');
  assert.equal(born.metadata.specialty, 'FRESQUE_SCOUT');
  assert.equal(born.metadata.colony_state, 'RECYCLED');

  const workMove = events.find((e) => e.event_type === 'ANT_MOVE' && e.ant_id === 'ANT-ABCDEF123456' && e.position === 'E:GENESIS-A');
  assert.ok(workMove);
  assert.equal(workMove.role, 'SCOUT');

  const crystal = events.find((e) => e.event_type === 'CRYSTAL_UPDATE' && e.crystal?.crystal_id === 'CRYSTAL-L4');
  assert.ok(crystal);
  assert.equal(crystal.metadata.count, 5);
});

test('time dilation returns a recycled real ant to Queen after visible work interval and later removes it', () => {
  let now = 1000;
  const projector = new ColonyAquariumProjector({ now: () => now, replayHoldMs: 5000, retentionMs: 4000 });
  projector.ingest(makeState({ antState: 'RECYCLED' }));

  now = 6500;
  let events = projector.ingest(makeState({ antState: 'RECYCLED' }));
  const returned = events.find((e) => e.event_type === 'ANT_MOVE' && e.ant_id === 'ANT-ABCDEF123456' && e.position === 'CENTER');
  assert.ok(returned);
  assert.equal(returned.state, 'RETURNING');
  assert.equal(returned.metadata.visualization_mode, 'REAL_QUEST_TIME_DILATED');

  now = 11000;
  events = projector.ingest(makeState({ antState: 'RECYCLED' }));
  const removed = events.find((e) => e.event_type === 'ANT_REMOVED' && e.ant_id === 'ANT-ABCDEF123456');
  assert.ok(removed);
});

test('working ant is projected to its real specialty work zone without waiting for replay delay', () => {
  let now = 1000;
  const projector = new ColonyAquariumProjector({ now: () => now });
  const events = projector.ingest(makeState({ antState: 'WORKING' }));
  const move = events.find((e) => e.event_type === 'ANT_MOVE' && e.ant_id === 'ANT-ABCDEF123456');
  assert.ok(move);
  assert.equal(move.position, 'E:GENESIS-A');
  assert.equal(move.state, 'EXPLORING');
});
