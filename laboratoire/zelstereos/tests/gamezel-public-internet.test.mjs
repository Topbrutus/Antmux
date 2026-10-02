import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve('laboratoire/zelstereos');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');

const voices = {
  P1: 'VOICE_P1_ASTRA_PLAY.mp3',
  P2: 'VOICE_P2_MUSE_PLAY.mp3',
  P3: 'VOICE_P3_GROK_PLAY.mp3',
  P4: 'VOICE_P4_ANTIGRAVITY_PLAY.mp3'
};

test('GAMEZEL public Internet bridge keeps four canonical PLAY voices on RECTO', () => {
  for (const [playerId, file] of Object.entries(voices)) {
    const full = path.join(root, 'assets', 'sfx', file);
    assert.ok(fs.existsSync(full), `${playerId} voice file missing`);
    assert.ok(fs.statSync(full).size > 512, `${playerId} voice file empty`);
    assert.match(html, new RegExp(`${playerId}:'${file.replace('.', '\\.')}'`));
  }
});
test('GAMEZEL public draw WebSocket event is handled separately from numeric state', () => {
  assert.match(html, /s\.type==='GAMEZEL_PUBLIC_DRAW'/);
  assert.match(html, /s\.transport_replay!==true/);
  assert.match(html, /gamezelPlayPublicDraw\(s\)\.catch/);
  assert.match(html, /GAMEZEL · /);
});

test('legacy public SFX bank remains exactly 36 top-level SFX mp3 files', () => {
  const sfxRoot = path.join(root, 'assets', 'sfx');
  const count = fs.readdirSync(sfxRoot)
    .filter(name => /^SFX\d+.*\.mp3$/i.test(name))
    .length;
  assert.equal(count, 36);
});
