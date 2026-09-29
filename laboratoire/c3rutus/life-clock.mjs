export const LIFE_CLOCK = Object.freeze({
  exactText: "240.10000000005764801000001384128720100332329305696089",
  nominalText: "240.1",
  dustText: "0.00000000005764801000001384128720100332329305696089",
  exactHz: Number("240.10000000005764801000001384128720100332329305696089"),
  cycleLCM: 546
});

export function lifeClockSample(elapsedMs) {
  if (!Number.isFinite(elapsedMs) || elapsedMs < 0) {
    throw new Error("elapsedMs must be a non-negative finite number");
  }

  const seconds = elapsedMs / 1000;
  const exactTicks = seconds * LIFE_CLOCK.exactHz;
  const beat = Math.floor(exactTicks);
  const fraction = exactTicks - beat;

  return Object.freeze({
    seconds,
    beat,
    fraction,
    actionTick: Math.floor(seconds),
    phase546: beat % LIFE_CLOCK.cycleLCM,
    r6: beat % 6,
    r7: beat % 7,
    r13: beat % 13
  });
}

export function lifeClockAt(nowMs, startedAtMs) {
  return lifeClockSample(Math.max(0, nowMs - startedAtMs));
}
