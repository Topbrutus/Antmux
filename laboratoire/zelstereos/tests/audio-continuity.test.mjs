import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const html = await readFile(new URL("../index.html", import.meta.url), "utf8");

test("audio continuity uses a non-zero crossfade window", () => {
  const m = html.match(/const ZEL_AUDIO_CROSSFADE_SEC=([0-9.]+);/);
  assert.ok(m, "crossfade constant missing");
  const seconds = Number(m[1]);
  assert.ok(seconds >= 0.15 && seconds <= 0.5, "crossfade should remain a short overlap");
});

test("SFX envelope fades in and out instead of hard-cutting", () => {
  assert.match(html, /const fadeIn=Math\.min\(\.10,dur\*\.24\),fadeOut=Math\.min\(\.24,dur\*\.34\)/);
  assert.match(html, /linearRampToValueAtTime\(gain\*soundVolume,start\+fadeIn\)/);
  assert.match(html, /exponentialRampToValueAtTime\(\.0001,start\+dur\)/);
});

test("motor duration extends through the stage boundary", () => {
  assert.match(html, /const dur=Math\.max\(baseDur,Math\.min\(5\.0,\(Number\(stageDt\)\|\|\.65\)\+ZEL_AUDIO_CROSSFADE_SEC\)\)/);
});

test("every live stage schedules a continuity bridge", () => {
  assert.match(html, /const bridgeDt=Math\.max\(stageDt,sonicDt\)\+ZEL_AUDIO_CROSSFADE_SEC/);
  assert.match(html, /scheduleContinuityBridgeAt\(liveStageFreq\[stageIndex\]\|\|82,base,bridgeDt,stageIndex,complexity\)/);
});

test("continuity bridge itself crossfades under the next stage", () => {
  assert.match(html, /function scheduleContinuityBridgeAt\(/);
  assert.match(html, /g\.gain\.setValueAtTime\(level,start\+Math\.max\(\.12,d-ZEL_AUDIO_CROSSFADE_SEC\)\)/);
  assert.match(html, /g\.gain\.exponentialRampToValueAtTime\(\.0001,start\+d\)/);
});
