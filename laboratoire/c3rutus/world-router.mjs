export const GLOBAL_BUBBLE = Object.freeze({
  id: "ANTMUX-UNIVERSE-01",
  type: "GLOBAL_ENVELOPE",
  verso: "VERSO-GLOBAL-01",
  router: "WORLD-ROUTER-01"
});

export const WORLD_FAMILIES = Object.freeze([
  Object.freeze({ id: "MATTER", label: "Matière" }),
  Object.freeze({ id: "INFORMATION", label: "Information" }),
  Object.freeze({ id: "TIME", label: "Temps" }),
  Object.freeze({ id: "MATH", label: "Mathématique" }),
  Object.freeze({ id: "BIO", label: "Vie" }),
  Object.freeze({ id: "ENERGY", label: "Énergie" })
]);

export const WORLD_CATALOG = Object.freeze([
  Object.freeze({
    id: "MATTER/CARBON",
    family: "MATTER",
    label: "Carbone",
    status: "ACTIVE",
    localVerso: "VERSO-LOCAL-CARBON"
  }),
  Object.freeze({
    id: "INFORMATION/CRYPTO",
    family: "INFORMATION",
    label: "Crypto",
    status: "ACTIVE",
    localVerso: "VERSO-LOCAL-CRYPTO"
  }),
  Object.freeze({
    id: "TIME/CLOCK",
    family: "TIME",
    label: "Temps",
    status: "STUB",
    localVerso: "VERSO-LOCAL-TIME"
  }),
  Object.freeze({
    id: "MATH/GEOMETRY",
    family: "MATH",
    label: "Géométrie",
    status: "STUB",
    localVerso: "VERSO-LOCAL-MATH"
  }),
  Object.freeze({
    id: "BIO/CELL",
    family: "BIO",
    label: "Cellule",
    status: "STUB",
    localVerso: "VERSO-LOCAL-BIO"
  }),
  Object.freeze({
    id: "ENERGY/FREQUENCY",
    family: "ENERGY",
    label: "Fréquence",
    status: "STUB",
    localVerso: "VERSO-LOCAL-ENERGY"
  })
]);

export const PORTAL_CONTRACTS = Object.freeze([
  Object.freeze({
    id: "PORTAL-CARBON-CRYPTO-01",
    from: "MATTER/CARBON",
    to: "INFORMATION/CRYPTO",
    via: GLOBAL_BUBBLE.verso,
    transform: "UTF8-CARRIER-V1",
    reversible: true,
    proofMode: "ROUNDTRIP",
    note: "Transport encoding only; this is not encryption or hashing."
  })
]);

export function worldById(id) {
  return WORLD_CATALOG.find(world => world.id === id) ?? null;
}

export function portalBetween(from, to) {
  const direct = PORTAL_CONTRACTS.find(p => p.from === from && p.to === to);
  if (direct) return Object.freeze({ ...direct, direction: "FORWARD" });

  const reverse = PORTAL_CONTRACTS.find(p => p.reversible && p.from === to && p.to === from);
  if (reverse) return Object.freeze({ ...reverse, direction: "REVERSE" });

  return null;
}

export function routeWorld(from, to) {
  const source = worldById(from);
  const destination = worldById(to);

  if (!source || !destination) {
    return Object.freeze({
      open: false,
      reason: "UNKNOWN_WORLD",
      from,
      to,
      path: Object.freeze([])
    });
  }

  if (from === to) {
    return Object.freeze({
      open: true,
      reason: "SAME_WORLD",
      from,
      to,
      path: Object.freeze([from])
    });
  }

  const portal = portalBetween(from, to);
  if (!portal) {
    return Object.freeze({
      open: false,
      reason: "NO_PORTAL_CONTRACT",
      from,
      to,
      path: Object.freeze([from, GLOBAL_BUBBLE.verso, to])
    });
  }

  return Object.freeze({
    open: true,
    reason: "PORTAL_CONTRACT_FOUND",
    from,
    to,
    portal,
    path: Object.freeze([from, GLOBAL_BUBBLE.verso, to])
  });
}

export function encodeCarrier(text) {
  const bytes = new TextEncoder().encode(String(text));
  return Object.freeze({
    type: "UTF8-CARRIER-V1",
    text: String(text),
    bytes: Object.freeze(Array.from(bytes)),
    hex: Array.from(bytes, byte => byte.toString(16).padStart(2, "0")).join(""),
    binary: Array.from(bytes, byte => byte.toString(2).padStart(8, "0")).join(" ")
  });
}

export function decodeCarrier(carrier) {
  if (!carrier || carrier.type !== "UTF8-CARRIER-V1" || !Array.isArray(carrier.bytes)) {
    throw new Error("Invalid UTF8 carrier");
  }
  return new TextDecoder().decode(Uint8Array.from(carrier.bytes));
}

export function transportEnvelope({
  antId,
  from,
  to,
  tick,
  state,
  proofRef,
  echo
}) {
  if (!antId) throw new Error("antId is required");
  if (!Number.isInteger(tick) || tick < 0) throw new Error("tick must be a non-negative integer");

  const route = routeWorld(from, to);
  if (!route.open) {
    return Object.freeze({
      accepted: false,
      route,
      invariant: null
    });
  }

  return Object.freeze({
    accepted: true,
    route,
    invariant: Object.freeze({
      antId,
      tick,
      state: state ?? null,
      proofRef: proofRef ?? null,
      echo: echo ?? null
    })
  });
}
