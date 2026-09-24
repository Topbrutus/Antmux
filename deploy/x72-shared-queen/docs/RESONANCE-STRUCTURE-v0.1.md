# X72 — Instrumented Resonance Structure v0.1

## Final architecture

One architecture only:

```
QUEEN / WHEEL
     |
     | read-only state observation
     v
RESONANCE BRIDGE
     |
     v
INDEPENDENT RESONANCE STRUCTURE
```

Queen remains independent. The resonance structure remains independent. The
bridge is strictly read-only: it exposes a copied state view and no command or
mutation surface.

## Scientific labels

- HYPOTHESIS: route or interpretation being tested.
- MEASURED: value obtained from an ingested signal or sensor.
- CALCULATED: value derived mathematically.
- UNKNOWN: not established.
- NOT_RUN: test not executed.
- SYNTHETIC: deterministic software verification only.

No software result is presented as proof of a physical, biological, medical,
particle-physics or consciousness mechanism.

## Route A

Route A is encoded as the current candidate graph:

```
BOTTOM
  |
  v
MAUVE_A1
  |\
  | +--> YELLOW
  | +--> RED_1 --> GREEN_1 --> A2
  | |       \
  | |        -> RED_2 -> BLUE -> C3
  | +--> GROUND_ECHO
```

Structured return:

```
C3 -> YELLOW_RETURN -> BOTTOM
C3 -> MAUVE_RETURN  -> MAUVE_A1
C3 -> BOTTOM_RETURN -> BOTTOM
GROUND_ECHO -> MAUVE_A1
```

Accumulation labels:

- first: `MAUVE_A1`
- second: `A2`
- third: `C3`

The `RED_1 / GREEN_1` pair is stored as a forward/reversed mirror pair.

## Principal measurement channels

```
REF
C1
C2
C3
C4
C5
C6
C7
```

REF is the injected reference. Every C-channel is compared to REF.

## Route A sensors

```
BOTTOM
MAUVE_A1
YELLOW
RED_1
GREEN_1
GROUND_ECHO
A2
RED_2
BLUE
C3
YELLOW_RETURN
MAUVE_RETURN
BOTTOM_RETURN
```

Each Route A sensor records count, mean, RMS, peak and last value. Additional
observation-only sensors can be added later without changing QueenCore.

## Signal markers and tests

The subsystem generates or accepts:

1. fixed sine;
2. short impulse;
3. chirp / sweep;
4. 0.1 Hz breathing envelope;
5. synchronous seven-zone excitation;
6. ascending phase progression;
7. descending phase progression.

Breathing envelope:

```
B(t) = (1 + sin(2*pi*fB*t)) / 2
fB = 0.1 Hz
```

Zone signal form:

```
x_i(t) = A_i * B(t) * sin(2*pi*f_i*t + phi_i)
```

## Measurements

For each C-zone:

- RMS amplitude;
- peak amplitude;
- dominant frequency / FFT;
- gain relative to REF;
- delay relative to REF;
- phase delta relative to REF;
- windowed magnitude-squared coherence estimate;
- transfer bandwidth using a -3 dB threshold.

Adjacent links `C1<->C2` through `C6<->C7` are also analyzed for gain,
phase, delay, coherence and bandwidth.

Stereo views:

```
SUM  = L + R
DIFF = L - R
```

SUM and DIFF are calculated views, not extra physical sensors.

## JSONL journal

Each completed analysis can be appended to a JSONL journal. Records preserve the
test type, input parameters, REF metrics, C1-C7 measurements, adjacent-link
measurements, Route A sensor state, research constants and evidence labels.

## Preserved calculated references

These values remain available as references and are never forced into results:

```
7^4 = 2401
lcm(3,7,13) = 273
13*7*7 = 637
3*(6+1)*7*7*9*10*13 = 1 203 930
R(t,b,o) = (91t + 39b + 21o) mod 273
Theta = 2*pi*R/273
2.852/7 = 0.407428571428...
```

Usage label:

```
REFERENCE_ONLY_DO_NOT_FORCE
```

## Read-only bridge contract

`ResonanceWheelBridge` imports no Queen or Noyau implementation.

Its contract is deliberately narrow:

- optional wheel state reader;
- state is deep-copied before return;
- no command sink;
- no mutation method;
- no write path;
- structure may run with no wheel attached;
- Queen may run with no resonance structure attached.

The integration tests compare Queen hashes before and after bridge reads and
structure execution. They must remain identical when Queen itself is not
stepped.

## Eight-screen instrumentation layout

1. Route A graph, direction and accumulation nodes;
2. REF + C1 waveform, FFT and test marker;
3. C2 + C3 amplitude, gain, delay and bandwidth;
4. C4 coherence, phase and upper/lower interaction;
5. C5 resonance spectrum and harmonics;
6. C6 + C7 phase, delay and output;
7. adjacent-link gain/coherence/bandwidth and L/R SUM/DIFF;
8. JSONL journal, anomalies, evidence labels and run status.

## Validation commands

```
python3 deploy/x72-shared-queen/tests/test_resonance_structure.py
python3 deploy/x72-shared-queen/tests/test_resonance_bridge.py
python3 deploy/x72-shared-queen/tests/test_resonance_queen_integration.py
python3 deploy/x72-shared-queen/tests/run_resonance_protocol.py --report /tmp/x72-resonance-report.json
```

The hardware stage remains separate. Real sensor data should enter through
REF/C1-C7 and Route A sensor ingestion without modifying QueenCore.
