import {
  GLOBAL_BUBBLE,
  decodeCarrier,
  encodeCarrier,
  transportEnvelope
} from "./world-router.mjs";

export const ROUNDTRIP_EVENTS = Object.freeze([
  "BIRTH",
  "DEPART",
  "VERSO_GLOBAL_FORWARD",
  "TRANSFORM_OUTBOUND",
  "ARRIVE",
  "DEPART_RETURN",
  "VERSO_GLOBAL_RETURN",
  "RECONSTRUCT",
  "RETURN"
]);

function freezePayload(payload = {}) {
  return Object.freeze({ ...payload });
}

function traceRecord({ seq, event, world, antId, tick, state, proofRef, echo, payload }) {
  return Object.freeze({
    seq,
    event,
    world,
    antId,
    tick,
    state,
    proofRef,
    echo,
    payload: freezePayload(payload)
  });
}

function sameInvariant(envelope, expected) {
  if (!envelope?.accepted || !envelope.invariant) return false;
  const invariant = envelope.invariant;
  return (
    invariant.antId === expected.antId &&
    invariant.tick === expected.tick &&
    invariant.state === expected.state &&
    invariant.proofRef === expected.proofRef &&
    invariant.echo === expected.echo
  );
}

export function runWorldRoundtrip({
  experimentId = "WORLD-ROUNDTRIP-0001",
  antId = "ANT-0001",
  startWorld = "MATTER/CARBON",
  transitWorld = "INFORMATION/CRYPTO",
  tick = 42,
  state = "ACTIVE",
  value = "C",
  proofRef = "PROOF-WORLD-ROUNDTRIP-0001",
  echo = "ECHO-WORLD-ROUNDTRIP-0001"
} = {}) {
  if (!experimentId) throw new Error("experimentId is required");
  if (!antId) throw new Error("antId is required");
  if (!Number.isInteger(tick) || tick < 0) {
    throw new Error("tick must be a non-negative integer");
  }

  const expectedInvariant = Object.freeze({
    antId,
    tick,
    state,
    proofRef,
    echo
  });

  const forward = transportEnvelope({
    antId,
    from: startWorld,
    to: transitWorld,
    tick,
    state,
    proofRef,
    echo
  });

  const outboundCarrier = encodeCarrier(value);

  const reverse = transportEnvelope({
    antId,
    from: transitWorld,
    to: startWorld,
    tick,
    state,
    proofRef,
    echo
  });

  const returnedValue = decodeCarrier(outboundCarrier);
  const traceRef =
    `TRACE://${experimentId}/${antId}/T${String(tick).padStart(8, "0")}`;

  const trace = Object.freeze([
    traceRecord({
      seq: 1,
      event: "BIRTH",
      world: startWorld,
      antId,
      tick,
      state,
      proofRef,
      echo,
      payload: { value: String(value) }
    }),
    traceRecord({
      seq: 2,
      event: "DEPART",
      world: startWorld,
      antId,
      tick,
      state,
      proofRef,
      echo,
      payload: { to: transitWorld }
    }),
    traceRecord({
      seq: 3,
      event: "VERSO_GLOBAL_FORWARD",
      world: GLOBAL_BUBBLE.verso,
      antId,
      tick,
      state,
      proofRef,
      echo,
      payload: { routeOpen: forward.accepted }
    }),
    traceRecord({
      seq: 4,
      event: "TRANSFORM_OUTBOUND",
      world: GLOBAL_BUBBLE.verso,
      antId,
      tick,
      state,
      proofRef,
      echo,
      payload: {
        transform: outboundCarrier.type,
        hex: outboundCarrier.hex,
        binary: outboundCarrier.binary
      }
    }),
    traceRecord({
      seq: 5,
      event: "ARRIVE",
      world: transitWorld,
      antId,
      tick,
      state,
      proofRef,
      echo,
      payload: { carrierType: outboundCarrier.type }
    }),
    traceRecord({
      seq: 6,
      event: "DEPART_RETURN",
      world: transitWorld,
      antId,
      tick,
      state,
      proofRef,
      echo,
      payload: { to: startWorld }
    }),
    traceRecord({
      seq: 7,
      event: "VERSO_GLOBAL_RETURN",
      world: GLOBAL_BUBBLE.verso,
      antId,
      tick,
      state,
      proofRef,
      echo,
      payload: { routeOpen: reverse.accepted }
    }),
    traceRecord({
      seq: 8,
      event: "RECONSTRUCT",
      world: GLOBAL_BUBBLE.verso,
      antId,
      tick,
      state,
      proofRef,
      echo,
      payload: { value: returnedValue }
    }),
    traceRecord({
      seq: 9,
      event: "RETURN",
      world: startWorld,
      antId,
      tick,
      state,
      proofRef,
      echo,
      payload: { value: returnedValue }
    })
  ]);

  const actualEvents = trace.map(entry => entry.event);
  const contractForward = forward.route?.portal ?? null;
  const contractReverse = reverse.route?.portal ?? null;

  const checks = Object.freeze({
    forwardRouteOpen: forward.accepted === true,
    reverseRouteOpen: reverse.accepted === true,
    forwardInvariantMatch: sameInvariant(forward, expectedInvariant),
    reverseInvariantMatch: sameInvariant(reverse, expectedInvariant),
    samePortalContract:
      contractForward?.id === "PORTAL-CARBON-CRYPTO-01" &&
      contractReverse?.id === "PORTAL-CARBON-CRYPTO-01",
    reversibleContract:
      contractForward?.reversible === true &&
      contractReverse?.reversible === true,
    transformMatch:
      contractForward?.transform === outboundCarrier.type &&
      contractReverse?.transform === outboundCarrier.type,
    proofModeRoundtrip:
      contractForward?.proofMode === "ROUNDTRIP" &&
      contractReverse?.proofMode === "ROUNDTRIP",
    dataMatch: returnedValue === String(value),
    historyComplete:
      actualEvents.length === ROUNDTRIP_EVENTS.length &&
      actualEvents.every((event, index) => event === ROUNDTRIP_EVENTS[index])
  });

  const verdict = Object.values(checks).every(Boolean) ? "PASS" : "FAIL";

  return Object.freeze({
    experimentId,
    traceRef,
    ant: expectedInvariant,
    startWorld,
    transitWorld,
    input: String(value),
    carrier: outboundCarrier,
    returnedValue,
    forward,
    reverse,
    trace,
    proof: Object.freeze({
      mode: "ROUNDTRIP",
      verdict,
      checks
    })
  });
}
