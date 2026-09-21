# ANTMUX X72 — Timing correction v0.2.1

Status: corrective release candidate.

## Exact cadence basis

The v0.2.1 engine target is derived from the canonical base-7 address-space size:

```text
7^4 = 2401
2401 / 10 s = 240.1 Hz
dt_sim = 10 / 2401 s
```

This replaces the approximate 240 Hz engine target used by v0.2.0.

## Compatibility rule

v0.2.1 changes the real engine cadence only. Historical tick-domain contracts remain unchanged in this corrective release:

- relation/Z3 sampling interval: 60 ticks;
- mode event interval: 360 ticks;
- Z3 runtime frame event interval: 240 ticks;
- generation interval: 7200 ticks.

Therefore v0.2.0 remains reproducible as the published historical version, while v0.2.1 records the cadence correction explicitly instead of rewriting history.
