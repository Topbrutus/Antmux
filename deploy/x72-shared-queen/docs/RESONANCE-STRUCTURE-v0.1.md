# X72 — Instrumented Resonance Structure v0.1

## Mission

Build the new structure as an autonomous experimental subsystem.

It is not the wheel engine.

```
ROUE EXISTANTE
      |
      | controlled interface
      v
RESONANCE BRIDGE
      |
      v
INDEPENDENT RESONANCE STRUCTURE
```

Both sides must work independently.

## Scientific labels

- HYPOTHESIS: route or interpretation being tested.
- MEASURED: value obtained from a sensor or ingested signal.
- CALCULATED: value derived mathematically from measured or configured data.
- UNKNOWN: not established.
- NOT_RUN: test not executed.
- SYNTHETIC: deterministic software verification only.

No software result is presented as proof of a physical, biological, medical,
particle-physics or consciousness mechanism.

## Route A — current Brutus test order

The current route is encoded exactly as a candidate graph.

```
BOTTOM
  |
  v
MAUVE_A1   <- first accumulation
  |\
  | +--> YELLOW
  | +--> RED_1 --> GREEN_1 --> A2
  | |       \                 second accumulation
  | |        -> RED_2 -> BLUE -> C3
  | |                           third accumulation
  | +--> GROUND_ECHO -----------+
  |
  +--------------------------------
```

Structured return from C3:

```
C3 -> YELLOW_RETURN -> BOTTOM
C3 -> MAUVE_RETURN  -> MAUVE_A1
C3 -> BOTTOM_RETURN -> BOTTOM
GROUND_ECHO -> MAUVE_A1
```

The RED_1 / GREEN_1 pair is stored as a mirror pair with forward/reversed
orientation metadata.

## Eight principal measurement channels

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

REF is the actual injected signal reference. Every C-channel is compared to REF.

Additional Route A sensors exist at every candidate node:

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

There is intentionally no upper limit imposed by the architecture on future
observation-only sensor channels.

## Signal markers

The subsystem generates or accepts:

1. fixed sine;
2. short impulse;
3. chirp / sweep;
4. 0.1 Hz breathing envelope;
5. synchronous seven-zone excitation;
6. ascending phase progression;
7. descending phase progression.

The breathing envelope is:

```
B(t) = (1 + sin(2*pi*fB*t)) / 2
fB = 0.1 Hz
```

A zone signal may be represented as:

```
x_i(t) = A_i * B(t) * sin(2*pi*f_i*t + phi_i)
```

## Measurements

For each C-zone the analyzer calculates:

- RMS amplitude;
- peak amplitude;
- dominant frequency;
- gain relative to REF;
- delay relative to REF;
- phase delta relative to REF;
- windowed magnitude-squared coherence estimate;
- transfer bandwidth using the -3 dB threshold.

Adjacent-zone analysis can therefore be performed with the same signal arrays.

Stereo utilities preserve the protocol distinction:

```
SUM  = L + R
DIFF = L - R
```

SUM and DIFF are calculated views, not extra physical sensors.

## Preserved research constants

These stay available as references and are never forced into results:

```
7^4 = 2401
lcm(3,7,13) = 273
13*7*7 = 637
3*(6+1)*7*7*9*10*13 = 1 203 930
R(t,b,o) = (91t + 39b + 21o) mod 273
Theta = 2*pi*R/273
2.852/7 = 0.407428571428...
```

## Bridge

`ResonanceWheelBridge` has no Queen/Noyau import.

Default behavior is read-only:

- wheel state is copied before it is returned;
- no mutation is sent by default;
- only an explicit command gate can deliver a whitelisted command;
- arbitrary commands are rejected.

Whitelisted test commands:

```
SET_TEST_SIGNAL
CLEAR_TEST_SIGNAL
MARK_TEST
```

## Architecture A versus B

Architecture A is the previous pump candidate mounted inside Queen step.
That mount has been removed and kept only for standalone replay.

Architecture B is this independent resonance structure plus bridge.

The protocol runner compares the two architectures at software level and emits
a JSON report.

## Eight-screen instrumentation layout

A practical display split for the user's eight screens:

1. global Route A graph, direction and accumulation nodes;
2. REF + C1 raw waveform, FFT and input markers;
3. C2 + C3 amplitude, delay and bandwidth;
4. C4 coherence, phase and upper/lower interaction;
5. C5 resonance spectrum and harmonics;
6. C6 + C7 phase, delay, output and saturation indicators;
7. pairwise gain/coherence/bandwidth matrix and L/R SUM/DIFF;
8. experiment journal, anomalies, comparison A/B and evidence labels.

## Test command

```
python3 deploy/x72-shared-queen/tests/test_chakra_pump.py
python3 deploy/x72-shared-queen/tests/test_resonance_structure.py
python3 deploy/x72-shared-queen/tests/test_resonance_bridge.py
python3 deploy/x72-shared-queen/tests/run_resonance_protocol.py --report /tmp/x72-resonance-report.json
```

The real hardware stage is deliberately separate. Real sensor data should enter
through REF/C1..C7 and Route A sensor ingestion without changing QueenCore.
