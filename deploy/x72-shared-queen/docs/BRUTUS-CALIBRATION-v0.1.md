# ANTMUX X72 — Brutus calibration and 2401 synchronization v0.1

Status: **CANDIDATE / OBSERVATION ONLY**

This experiment does not alter Queen authority, protected state, the 240.1 Hz
target, or the historical logical tick contracts. It measures them.

## 1. Brutus calibration candidate

The target engine cadence is

```text
7^4 = 2401
2401 / 10 s = 240.1 Hz
```

For an observed execution cadence `f_measured`, define the candidate
calibration factor

```text
K_B = 240.1 / f_measured
```

Interpretation is deliberately limited:

- `K_B = 1`: measured cadence equals target cadence;
- `K_B > 1`: measured execution is below target;
- `K_B < 1`: measured execution is above target.

`K_B` is not accepted as a stable constant until a long-enough observation
shows that it remains reproducible rather than following scheduler jitter.

## 2. Exact logical synchronization with the 2401 cycle

The current runtime clocks are:

```text
base-7 cycle       2401 ticks
relation sample      60 ticks
Z3 sample            60 ticks
Z3 frame            240 ticks
MODE event          360 ticks
mode cycle         1800 ticks
generation         7200 ticks
```

Because `2401 = 7^4` shares no prime factor with 60, 240, 360, 1800 or 7200,
their exact common boundaries are determined by the least common multiple.

| Boundary | Common ticks | Exact time at 240.1 Hz |
| --- | ---: | ---: |
| 2401 + relation/Z3 sample | 144060 | 600 s = 10 min |
| 2401 + Z3 frame | 576240 | 2400 s = 40 min |
| 2401 + MODE event | 864360 | 3600 s = 1 h |
| 2401 + mode cycle | 4321800 | 18000 s = 5 h |
| 2401 + generation | 17287200 | 72000 s = 20 h |
| all listed clocks | 17287200 | 72000 s = 20 h |

Therefore the one-hour experiment contains observable exact boundaries:

- every 10 minutes: 2401 + relation sample + Z3 sample;
- at the 40-minute boundary: 2401 + Z3 sample + Z3 frame;
- at the 60-minute boundary: 2401 + Z3 sample + MODE event.

The generation boundary joins the complete synchronization only every 20 hours.

## 3. Meaning of simultaneous

“Simultaneous” here means **same logical Queen tick**.

Inside one `QueenCore.step()`, the tick is incremented once and the runtime
operations are then evaluated sequentially by the CPU using that same tick
value. This is deterministic logical simultaneity; it is not a claim that all
machine instructions execute at the same physical nanosecond.

## 4. One-hour falsification test

The candidate is useful only if observation agrees with the contract.

At the end of the one-hour test, record:

- public software version;
- start/end tick and wall elapsed time;
- measured execution Hz;
- `K_B`;
- correction and frequency error in ppm;
- integrity status;
- whether the expected 2401 synchronization boundaries were crossed.

If `K_B` varies materially with observation window or system load, treat it as
scheduler calibration telemetry rather than a stable system constant.
