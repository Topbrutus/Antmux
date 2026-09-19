# Z3 Provenance / Hash Contract v0.1

Status: CANDIDATE / PRE-INTEGRATION  
Layer: Z3EchoPipeline-v0.1  
Authority: read-only mathematical/provenance layer

## Purpose

The provenance contract seals the transformed-domain state without changing X72 authority or ternary semantics.

It records:

- the exact finite Z coefficient series used as source;
- the exact echoed finite Z coefficient series;
- the exact transfer parameters;
- optional upstream X72 candidate and echo hashes;
- one deterministic provenance hash over the frame.

## Hash schemas

```text
ANTMUX-Z3-FINITE-Z-SERIES-H256-v0.1
ANTMUX-Z3-ECHO-TRANSFER-H256-v0.1
ANTMUX-Z3-ECHO-PROVENANCE-v0.1
```

All hashes are SHA-256 lowercase hexadecimal strings.

## Canonical numerical representation

Floating-point values are hashed by their exact Python binary64 hexadecimal representation.

Examples are conceptually equivalent to:

```text
float_value.hex()
complex -> { real_hex, imag_hex }
```

This avoids decimal formatting ambiguity in the canonical hash input.

Positive and negative zero are normalized to one canonical zero representation before hashing.

Non-finite values are rejected.

## Series seal

A finite transformed series is sealed from:

```text
representation = FINITE_Z_COEFFICIENTS
samples[n][channel] = complex coefficient
```

For each triad:

```text
[x[n], y[n], z[n]]
```

The series hash covers every coefficient in order.

Changing one coefficient changes the expected series hash.

## Transfer seal

The transfer seal covers:

```text
gain G
delay d
rotation matrix R
rotation source
Euler order, when known
Euler Z-Y-Z angles, when supplied
```

Mathematical transfer:

```text
E(z) = G z^(-d) R X(z)
```

The exact rotation matrix is always hashed.

If Euler angles are supplied, they must reproduce the stored matrix under the explicit order:

```text
R = Rz(alpha) Ry(beta) Rz(gamma)
```

Otherwise the seal uses:

```text
rotation_source = EXPLICIT_MATRIX3
euler_order = null
euler_angles = null
```

The implementation never invents Euler angles that were not supplied.

## Topology seal

The v0.1 provenance frame fixes:

```text
triad_count = 4
channels_per_triad = 3
total_node_count = 13
```

This is the project topology:

```text
1 center + 4 × 3 peripheral positions = 13
```

A topology mismatch invalidates verification.

## Optional upstream X72 chain

The frame may carry:

```text
source_x72_candidate_h256
source_x72_echo_h256
```

These fields are optional.

When present, each must be a valid lowercase 64-character SHA-256 hexadecimal value.

The provenance layer preserves these references. It does not reinterpret their semantics.

## Fast verification

Fast verification checks:

1. frame schema and representation;
2. 13-node topology constants;
3. provenance frame canonical hash;
4. source series hash;
5. echoed series hash;
6. transfer parameter hash;
7. rotation metadata coherence;
8. optional upstream X72 hash syntax.

Fast verification intentionally does **not** rerun:

```text
transfer.apply(source)
```

Therefore the fast path verifies integrity/coherence of the sealed chain without repeating the transformed-domain calculation.

## Deep verification

Deep verification first runs the fast checks.

It then recomputes:

```text
expected_echoed = transfer.apply(source)
```

and requires:

```text
H(expected_echoed) = echoed_series_h256
```

Deep verification is the semantic derivation check.

Use it for:

- tests;
- audits;
- checkpoint validation;
- suspicious or externally supplied frames.

Do not force it into every hot-path verification unless measurement justifies the cost.

## Security boundary

SHA-256 in this contract is unkeyed.

Therefore it provides:

- deterministic integrity sealing;
- tamper/inconsistency detection against an existing sealed chain;
- reproducible provenance references.

It does **not** provide:

- producer authentication;
- identity proof;
- non-repudiation;
- authorization.

A party capable of creating an entirely new self-consistent chain can also compute new valid SHA-256 hashes.

This limitation is explicit and must remain documented.

## Fast vs deep example

A source, transfer, and echoed series may be sealed into a self-consistent frame.

Fast verification can establish:

```text
source body matches source hash
echoed body matches echoed hash
transfer parameters match transfer hash
frame matches provenance hash
```

Only deep verification establishes:

```text
echoed == transfer(source)
```

for the supplied mathematical derivation.

## X72 semantics remain unchanged

This provenance layer does not change:

```text
Echo ∈ {-1,0,+1}
Provenance ∈ {-1,0,+1}
3×3 = 9 states
```

Existing rules remain:

- +1 requires explicit positive confirmation;
- 0 means unknown / indeterminate / silence / timeout;
- -1 requires explicit negative confirmation;
- silence is not negative;
- correlation is not proof;
- candidate is not action.

The numerical Z3 transfer gain `G` remains separate from X72 `echo_state`.

## No authority expansion

The provenance layer is read-only.

It does not:

- mutate Queen Server state;
- execute actions;
- provide mutation transport;
- create a local Queen;
- deploy to production;
- authenticate external producers.

## Acceptance requirements

v0.1 should retain:

```text
deterministic seal
signed-zero normalization
Euler metadata validation
source coefficient tamper rejection
echoed coefficient tamper rejection
frame metadata tamper rejection
malformed upstream hash rejection
fast path without transfer recomputation
deep semantic derivation verification
JSON serializable frame
```

Existing X72 acceptance must remain green.

## Current test evidence

Worker 1 provenance acceptance:

```text
16/16 PASS
```

Worker 2 provenance adversarial battery:

```text
9/9 PASS
```

These results establish implementation/test evidence for the current branch only.

They do not establish physical novelty or producer authenticity.

## Measured provenance benchmark — 2026-09-19

Method:

```text
clock = time.perf_counter_ns
calls per repetition = 200
repetitions = 5
summary = median wall time per call
series sizes = 8, 32, 128 triad coefficients
```

Measured results:

```text
8 triads / 24 scalar coefficients:
seal        162.656 us/call
fast verify 172.985 us/call
deep verify 312.3535 us/call
deep vs fast overhead +80.57%

32 triads / 96 scalar coefficients:
seal        384.724 us/call
fast verify 391.48 us/call
deep verify 851.1115 us/call
deep vs fast overhead +117.41%

128 triads / 384 scalar coefficients:
seal        1337.182 us/call
fast verify 1311.39 us/call
deep verify 2871.755 us/call
deep vs fast overhead +118.99%
```

Interpretation:

- fast verification still hashes the supplied source and echoed coefficient bodies;
- it does not recompute `transfer.apply(source)`;
- deep verification adds the semantic transfer recomputation;
- current measurements show deep verification is materially more expensive than fast verification for these synthetic series sizes;
- this is not a whole-system speedup claim.

Source report:

`reports/Z3-PROVENANCE-BENCHMARK-2026-09-19.json`

## Next measured step

1. rerun complete Z3 + X72 regressions after the provenance/adversarial merge;
2. keep PR #59 unmerged until explicit review/authorization;
3. after correctness remains green, design the next center-coupling brick;
4. do not claim invertibility for any future 12→3 center compression without preserved side information or proof.
