import test from "node:test";
import assert from "node:assert/strict";
import { ROUNDTRIP_EVENTS, runWorldRoundtrip } from "../roundtrip.mjs";

test("WORLD-ROUNDTRIP-0001 completes Carbon -> Crypto -> Carbon", () => {
  const result = runWorldRoundtrip();

  assert.equal(result.experimentId, "WORLD-ROUNDTRIP-0001");
  assert.equal(result.ant.antId, "ANT-0001");
  assert.equal(result.startWorld, "MATTER/CARBON");
  assert.equal(result.transitWorld, "INFORMATION/CRYPTO");

  assert.equal(result.input, "C");
  assert.equal(result.carrier.type, "UTF8-CARRIER-V1");
  assert.equal(result.carrier.hex, "43");
  assert.equal(result.carrier.binary, "01000011");
  assert.equal(result.returnedValue, "C");

  assert.equal(result.forward.accepted, true);
  assert.equal(result.reverse.accepted, true);
  assert.equal(result.proof.verdict, "PASS");
  assert.ok(Object.values(result.proof.checks).every(Boolean));
});

test("roundtrip preserves the ant identity invariants", () => {
  const result = runWorldRoundtrip({
    antId: "ANT-0099",
    tick: 273,
    state: "CARRYING",
    proofRef: "PROOF-0099",
    echo: "ECHO-0099",
    value: "Carbon"
  });

  assert.equal(result.ant.antId, "ANT-0099");
  assert.equal(result.ant.tick, 273);
  assert.equal(result.ant.state, "CARRYING");
  assert.equal(result.ant.proofRef, "PROOF-0099");
  assert.equal(result.ant.echo, "ECHO-0099");

  assert.deepEqual(result.forward.invariant, result.ant);
  assert.deepEqual(result.reverse.invariant, result.ant);
  assert.equal(result.returnedValue, "Carbon");
  assert.equal(result.proof.verdict, "PASS");
});

test("roundtrip trace is complete, ordered and immutable", () => {
  const result = runWorldRoundtrip();

  assert.equal(result.trace.length, 9);
  assert.deepEqual(result.trace.map(entry => entry.event), ROUNDTRIP_EVENTS);
  assert.deepEqual(result.trace.map(entry => entry.seq), [1,2,3,4,5,6,7,8,9]);
  assert.equal(Object.isFrozen(result.trace), true);
  assert.equal(result.trace.every(Object.isFrozen), true);
  assert.equal(result.trace.every(entry => Object.isFrozen(entry.payload)), true);
  assert.match(result.traceRef, /^TRACE:\/\/WORLD-ROUNDTRIP-0001\/ANT-0001\/T00000042$/);
});

test("roundtrip proof fails when no portal contract exists", () => {
  const result = runWorldRoundtrip({
    transitWorld: "BIO/CELL"
  });

  assert.equal(result.forward.accepted, false);
  assert.equal(result.reverse.accepted, false);
  assert.equal(result.proof.checks.forwardRouteOpen, false);
  assert.equal(result.proof.checks.reverseRouteOpen, false);
  assert.equal(result.proof.verdict, "FAIL");
});
