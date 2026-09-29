export const C3 = Object.freeze({
  name: "BoucleTrinitaireC3",
  zBase: 7,
  negZBase: 6,
  envelope: 13,
  commonLattice: 42,
  midBase: 6.5,
  polarityZero: 0,
  recto: 555,
  projectionCount: 9,
  elementCount: 118,
  snakeRoute: Object.freeze([2, 3, 1, 5, 6, 4, 8, 9, 7])
});

export function gcd(a, b) {
  a = Math.abs(Math.trunc(a));
  b = Math.abs(Math.trunc(b));
  while (b !== 0) [a, b] = [b, a % b];
  return a;
}

export function lcm(a, b) {
  if (!a || !b) return 0;
  return Math.abs(a * b) / gcd(a, b);
}

export function c3Result(a, b) {
  const values = [a, b].map(Number);
  if (values.some(v => ![1, 2, 3].includes(v)) || values[0] === values[1]) {
    throw new Error("C3 expects two distinct local positions from {1,2,3}");
  }
  return 6 - values[0] - values[1];
}

export function triangleForProjection(projectionId) {
  assertProjection(projectionId);
  return Math.floor((projectionId - 1) / 3) + 1;
}

export function localPosition(projectionId) {
  assertProjection(projectionId);
  return ((projectionId - 1) % 3) + 1;
}

export function snakeNext(projectionId) {
  assertProjection(projectionId);
  const route = C3.snakeRoute;
  const index = route.indexOf(projectionId);
  return route[(index + 1) % route.length];
}

export function invertPolarity(value) {
  if (value !== 1 && value !== -1) throw new Error("Polarity must be +1 or -1");
  return -value;
}

export function zLatticeIndex(sector) {
  if (!Number.isInteger(sector) || sector < 0 || sector >= C3.zBase) {
    throw new Error("Z sector must be 0..6");
  }
  return sector * (C3.commonLattice / C3.zBase);
}

export function negZLatticeIndex(sector) {
  if (!Number.isInteger(sector) || sector < 0 || sector >= C3.negZBase) {
    throw new Error("-Z sector must be 0..5");
  }
  return sector * (C3.commonLattice / C3.negZBase);
}

export function elementForTick(projectionId, tick, elements) {
  assertProjection(projectionId);
  if (!Number.isInteger(tick) || tick < 0) throw new Error("Tick must be a non-negative integer");
  if (!Array.isArray(elements) || elements.length !== C3.elementCount) {
    throw new Error("Expected the canonical 118-element table");
  }
  const index = (tick + projectionId - 1) % elements.length;
  return elements[index];
}

export function echoAddress(worldAddress, projectionId, atomicNumber, tick) {
  if (!worldAddress || typeof worldAddress !== "string") throw new Error("worldAddress is required");
  assertProjection(projectionId);
  if (!Number.isInteger(atomicNumber) || atomicNumber < 1 || atomicNumber > C3.elementCount) {
    throw new Error("Atomic number must be 1..118");
  }
  if (!Number.isInteger(tick) || tick < 0) throw new Error("Tick must be a non-negative integer");

  return [
    "ECHO://C3RUTUS",
    worldAddress,
    `P${String(projectionId).padStart(2, "0")}`,
    `E${String(atomicNumber).padStart(3, "0")}`,
    `T${String(tick).padStart(8, "0")}`,
    "Z7-NZ6-VERSO-LOCAL"
  ].join("/");
}

export function buildLocalProjections(elements, worldAddress = "MATTER/CARBON") {
  if (!Array.isArray(elements) || elements.length !== C3.elementCount) {
    throw new Error("Expected the canonical 118-element table");
  }

  return Object.freeze(Array.from({ length: C3.projectionCount }, (_, index) => {
    const id = index + 1;
    return Object.freeze({
      id,
      worldAddress,
      triangle: triangleForProjection(id),
      localPosition: localPosition(id),
      zBase: C3.zBase,
      negZBase: C3.negZBase,
      envelope: C3.envelope,
      elements
    });
  }));
}

function assertProjection(projectionId) {
  if (!Number.isInteger(projectionId) || projectionId < 1 || projectionId > C3.projectionCount) {
    throw new Error("Projection id must be 1..9");
  }
}
