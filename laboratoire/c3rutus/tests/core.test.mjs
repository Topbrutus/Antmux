import test from "node:test";
import assert from "node:assert/strict";
import { PERIODIC_TABLE } from "../periodic-table.mjs";
import { LIFE_CLOCK, lifeClockSample } from "../life-clock.mjs";
import {
  C3,
  buildWorlds,
  c3Result,
  echoAddress,
  elementForTick,
  invertPolarity,
  lcm,
  snakeNext,
  triangleForWorld
} from "../core.mjs";

test("canonical constants are stable", () => {
  assert.equal(C3.zBase, 7);
  assert.equal(C3.negZBase, 6);
  assert.equal(C3.envelope, 13);
  assert.equal(C3.commonLattice, 42);
  assert.equal(C3.midBase, 6.5);
  assert.equal(C3.recto, 555);
  assert.equal(PERIODIC_TABLE.length, 118);
  assert.equal(lcm(C3.zBase, C3.negZBase), 42);
});

test("C3 pair rule closes the trinity", () => {
  assert.equal(c3Result(2, 3), 1);
  assert.equal(c3Result(3, 1), 2);
  assert.equal(c3Result(1, 2), 3);
});

test("double inversion returns to origin", () => {
  assert.equal(invertPolarity(invertPolarity(1)), 1);
  assert.equal(invertPolarity(invertPolarity(-1)), -1);
});

test("nine worlds share one canonical periodic table", () => {
  const worlds = buildWorlds(PERIODIC_TABLE);
  assert.equal(worlds.length, 9);
  assert.equal(worlds[0].elements, PERIODIC_TABLE);
  assert.equal(worlds[8].elements, PERIODIC_TABLE);
  assert.equal(triangleForWorld(1), 1);
  assert.equal(triangleForWorld(4), 2);
  assert.equal(triangleForWorld(9), 3);
});

test("snake route visits all worlds exactly once before closing", () => {
  const seen = [];
  let world = C3.snakeRoute[0];
  for (let i = 0; i < 9; i += 1) {
    seen.push(world);
    world = snakeNext(world);
  }
  assert.equal(new Set(seen).size, 9);
  assert.equal(world, C3.snakeRoute[0]);
});

test("element progression wraps deterministically", () => {
  assert.equal(elementForTick(1, 0, PERIODIC_TABLE).symbol, "H");
  assert.equal(elementForTick(1, 117, PERIODIC_TABLE).symbol, "Og");
  assert.equal(elementForTick(1, 118, PERIODIC_TABLE).symbol, "H");
});

test("ECHO address is deterministic", () => {
  assert.equal(
    echoAddress(7, 6, 42),
    "ECHO://C3RUTUS/W07/E006/T00000042/Z7-NZ6-VERSO"
  );
});


test("Life Clock keeps the 240.1+dust reference and derives deterministic residues", () => {
  assert.equal(LIFE_CLOCK.nominalText, "240.1");
  assert.equal(
    LIFE_CLOCK.exactText,
    "240.10000000005764801000001384128720100332329305696089"
  );
  const s = lifeClockSample(1000);
  assert.equal(s.beat, 240);
  assert.equal(s.actionTick, 1);
  assert.equal(s.r6, 0);
  assert.equal(s.r7, 2);
  assert.equal(s.r13, 6);
  assert.equal(s.phase546, 240);
});
