# Z3 Center Provenance v0.1

Status: CANDIDATE / PRE-INTEGRATION  
Layer: reversible center coupling + 3+9 decomposition  
Authority: read-only provenance/audit layer

## Purpose

This contract seals the center-coupling stage of the 13-node candidate system.

It links:

```text
source 4×3 transformed state
→ reversible 12×12 center coupling
→ coupled 12-channel state
→ 3-value center summary + 9 residual side values
```

without changing X72 ternary semantics or Queen authority.

## Sealed objects

The frame records hashes for:

```text
source_state_h256
coupling_h256
coupled_state_h256
summary_h256
center_series_h256
residual_series_h256[3]
source_z3_echo_provenance_h256 (optional)
provenance_h256
```

The coupling seal includes:

```text
schedule_version
ordered schedule
theta
12×12 matrix
```

Current schedule version:

```text
Z3-MIRROR-RING-SCHEDULE-v0.1
```

## Fast verification

Fast verification validates:

1. center-provenance schema;
2. schedule version;
3. canonical frame hash;
4. source-state hash;
5. coupled-state hash;
6. center-summary hash;
7. three residual-series hashes;
8. coupling theta/matrix consistency;
9. coupling hash;
10. optional upstream Z3 Echo provenance hash syntax.

Fast verification does not call:

```text
coupling.apply(source)
CenterSummary3WithResidual.decompose(coupled)
```

Therefore it checks integrity/coherence of the already-sealed center chain without semantic recomputation.

## Deep verification

Deep verification first performs fast verification.

It then recomputes:

```text
expected_coupled = coupling.apply(source)
expected_summary = decompose(expected_coupled)
```

and verifies that both agree with the sealed coupled state and summary.

It also reconstructs a numerical approximation of the coupled state from:

```text
3 center values + 9 residual side values
```

and requires agreement with the coupled state under the declared reconstruction tolerance.

## Floating-point reconstruction rule

The stored source/coupled/summary bodies are hashed exactly.

However, the 3+9 transform is only algebraically invertible. In binary64, mean/residual formation can be ill-conditioned and can round away low-order information. The error is not limited to the final bit and can depend strongly on dynamic range.

For example, distinct quartets such as `(1e16,0,0,0)` and `(1e16,0,0,1)` can produce the same stored center/residual values. Therefore the 3+9 representation is not the exact provenance authority.

The current deep 3+9 reconstruction check uses:

```text
absolute tolerance = 1e-10 per complex channel value
```

This threshold is an acceptance budget for the derived numerical representation, not a proof of bit-exact invertibility. Exact provenance remains anchored by the separately sealed coupled 12-channel state body/hash.

## 3+9 information accounting

The center summary contains:

```text
3 values
```

The retained residual state contains:

```text
9 values
```

Total, in exact arithmetic:

```text
3 + 9 = 12 algebraic degrees of representation
```

This count does not imply a one-to-one binary64 encoding at all scales. The coupled 12-channel state remains authoritative for exact hashing and audit.

The fourth residual is derived from the first three because the center is defined as the four-triad mean:

```text
r3 = -(r0 + r1 + r2)
```

A center-only 12→3 map remains many-to-one.

The test suite includes an explicit counterexample where two different 12-channel states have the same 3-value center.

## Security boundary

All current seals use unkeyed SHA-256.

They provide:

- deterministic integrity references;
- tamper/inconsistency detection against an existing sealed chain;
- reproducible provenance linkage.

They do not provide:

- producer authentication;
- authorization;
- signatures;
- non-repudiation.

A new independently created self-consistent chain can be hashed by any producer.

## Relation to prior Z3 provenance

The center provenance frame may carry:

```text
source_z3_echo_provenance_h256
```

This allows the chain to be linked conceptually as:

```text
X72 candidate/echo
→ Z3 Echo provenance
→ Z3 center provenance
```

The field is a reference only.

The center layer does not reinterpret the meaning of the upstream X72 or Z3 hashes.

## Acceptance evidence

Worker 1 center-provenance acceptance:

```text
15/15 PASS
```

Covered:

- schema/version;
- fast verify;
- deep verify;
- deterministic sealing;
- source/coupling/coupled/summary hash traceability;
- upstream hash preservation;
- three residual hashes;
- source tamper rejection;
- coupled-state tamper rejection;
- summary tamper rejection;
- frame metadata tamper rejection;
- malformed upstream hash rejection;
- explicit fast-vs-deep semantic distinction;
- self-consistent wrong derivation caught by deep verification;
- JSON serialization.

Worker 2 center-provenance adversarial battery:

```text
11/11 PASS
```

Covered:

- resealed metadata tampering;
- wrong source;
- wrong coupled state;
- wrong 3+9 summary;
- proof that fast verify does not recompute;
- deep recomputation;
- theta/matrix mismatch;
- unkeyed-chain security boundary;
- frozen schedule version;
- repeated deterministic seals;
- stable JSON output.

## Existing semantics remain unchanged

This layer does not modify:

```text
Echo ∈ {-1,0,+1}
Provenance ∈ {-1,0,+1}
```

and does not convert logical ternary states into numerical gains or center values.

It remains read-only.

No Queen mutation, action execution, or production deployment is introduced.

## Measured center-provenance benchmark — 2026-09-19

Method:

```text
clock = time.perf_counter_ns
calls per repetition = 100
repetitions = 5
summary = median wall time per call
sizes = 8, 32, 128 coefficients per triad
```

Measured results:

```text
8 coefficients / triad, 96 complex channel values:
seal        918.701 us/call
fast verify 6917.128 us/call
deep verify 15209.783 us/call
deep vs fast overhead +119.89%

32 coefficients / triad, 384 complex channel values:
seal        2839.595 us/call
fast verify 9127.581 us/call
deep verify 21033.159 us/call
deep vs fast overhead +130.44%

128 coefficients / triad, 1536 complex channel values:
seal        11421.317 us/call
fast verify 16870.884 us/call
deep verify 47078.221 us/call
deep vs fast overhead +179.05%
```

Interpretation:

- fast center verification still hashes the sealed source, coupled, center and residual bodies;
- it does not rerun `coupling.apply(source)` or the center decomposition;
- deep verification adds those semantic recomputations;
- these measurements show deep verification is materially more expensive for the measured synthetic sizes;
- this is not a whole-system speedup claim.

Source report:

`reports/Z3-CENTER-PROVENANCE-BENCHMARK-2026-09-19.json`

## Independent numerical hardening evidence — 2026-09-19

A dedicated regression battery now covers the edge cases discovered during independent falsification:

```text
test_z3_codex_audit_regressions.py
14/14 PASS
```

It includes:

- finite `1e308` center means without naive-sum overflow;
- preservation of equal smallest subnormals in the center mean;
- large-cancellation reconstruction;
- rejection of a noncanonical theta-zero shear;
- rejection of complex norm-changing matrices as spatial rotations;
- copying caller-owned mutable rotation/sample storage;
- rejection of destructive whole and partial complex underflow;
- scaled complex division/multiplication when the representable result would otherwise overflow intermediate arithmetic;
- the known binary64 3+9 collision boundary;
- explicit v0.1 routing invariant subspaces;
- explicit distinction between direct full-turn parameter closure and repeated quarter-turn composition.

The coupled 12-channel body/hash remains the exact provenance authority. The 3+9 representation remains a derived numerical view with an explicit binary64 limitation.

## Next safe step

1. commit the audited numerical hardening and its regression evidence atomically;
2. commit the benchmark script/report and this measured evidence;
3. push only `worker1/z3-echo-pipeline-v0.1`;
4. update PR #59 with the new head, limits, tests and benchmark;
5. wait for CI and keep PR #59 draft/unmerged;
6. only after the branch is green, decide whether v0.2 should connect the y and x/z routing components before designing the combined execution frame:
   `Z transform → Euler → Echo_Z → center coupling → 3+9 → provenance`.
