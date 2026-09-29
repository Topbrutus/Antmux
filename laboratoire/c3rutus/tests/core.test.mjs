import test from "node:test";
import assert from "node:assert/strict";
import { PERIODIC_TABLE } from "../periodic-table.mjs";
import { LIFE_CLOCK, lifeClockSample } from "../life-clock.mjs";
import {
  C3,
  buildLocalProjections,
  c3Result,
  echoAddress,
  elementForTick,
  invertPolarity,
  lcm,
  snakeNext,
  triangleForProjection
} from "../core.mjs";
import {
  GLOBAL_BUBBLE,
  WORLD_CATALOG,
  decodeCarrier,
  encodeCarrier,
  routeWorld,
  transportEnvelope
} from "../world-router.mjs";

test("canonical constants are stable", () => {
  assert.equal(C3.zBase, 7);
  assert.equal(C3.negZBase, 6);
  assert.equal(C3.envelope, 13);
  assert.equal(C3.commonLattice, 42);
  assert.equal(C3.midBase, 6.5);
  assert.equal(C3.recto, 555);
  assert.equal(C3.projectionCount, 9);
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

test("nine local projections share one canonical periodic table", () => {
  const projections = buildLocalProjections(PERIODIC_TABLE, "MATTER/CARBON");
  assert.equal(projections.length, 9);
  assert.equal(projections[0].elements, PERIODIC_TABLE);
  assert.equal(projections[8].elements, PERIODIC_TABLE);
  assert.equal(projections[0].worldAddress, "MATTER/CARBON");
  assert.equal(triangleForProjection(1), 1);
  assert.equal(triangleForProjection(4), 2);
  assert.equal(triangleForProjection(9), 3);
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
    echoAddress("MATTER/CARBON", 7, 6, 42),
    "ECHO://C3RUTUS/MATTER/CARBON/P07/E006/T00000042/Z7-NZ6-VERSO-LOCAL"
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


test("global bubble contains distinct worlds and a global Verso", () => {
  assert.equal(GLOBAL_BUBBLE.verso, "VERSO-GLOBAL-01");
  assert.ok(WORLD_CATALOG.some(w => w.id === "MATTER/CARBON"));
  assert.ok(WORLD_CATALOG.some(w => w.id === "INFORMATION/CRYPTO"));
});

test("Carbon to Crypto requires the explicit global portal", () => {
  const route = routeWorld("MATTER/CARBON", "INFORMATION/CRYPTO");
  assert.equal(route.open, true);
  assert.deepEqual(route.path, [
    "MATTER/CARBON",
    "VERSO-GLOBAL-01",
    "INFORMATION/CRYPTO"
  ]);
  assert.equal(route.portal.transform, "UTF8-CARRIER-V1");
  assert.equal(route.portal.proofMode, "ROUNDTRIP");
});

test("undefined inter-world routes stay closed", () => {
  const route = routeWorld("MATTER/CARBON", "BIO/CELL");
  assert.equal(route.open, false);
  assert.equal(route.reason, "NO_PORTAL_CONTRACT");
});

test("carrier preserves Carbon symbol by roundtrip", () => {
  const carrier = encodeCarrier("C");
  assert.equal(carrier.hex, "43");
  assert.equal(carrier.binary, "01000011");
  assert.equal(decodeCarrier(carrier), "C");
});

test("ant transport preserves identity invariants across global Verso", () => {
  const envelope = transportEnvelope({
    antId: "ANT-0001",
    from: "MATTER/CARBON",
    to: "INFORMATION/CRYPTO",
    tick: 42,
    state: "ACTIVE",
    proofRef: "PROOF-42",
    echo: "ECHO-42"
  });
  assert.equal(envelope.accepted, true);
  assert.equal(envelope.invariant.antId, "ANT-0001");
  assert.equal(envelope.invariant.tick, 42);
});
