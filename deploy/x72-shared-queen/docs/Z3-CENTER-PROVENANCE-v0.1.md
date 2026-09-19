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

It also reconstructs the coupled state from:

```text
3 center values + 9 residual side values
```

and requires numerical agreement with the coupled state.

## Floating-point reconstruction rule

The stored source/coupled/summary bodies are hashed exactly.

However, reconstruction from the 3+9 representation involves additional floating-point subtraction/addition, so a mathematically equivalent reconstruction may differ by the final binary floating-point rounding bit.

Therefore the deep 3+9 reconstruction check uses:

```text
absolute tolerance = 1e-10 per complex channel value
```

This is deliberate.

It does not weaken body-hash integrity checks. It only applies to the independently recomputed reconstruction equality test.

## 3+9 information accounting

The center summary contains:

```text
3 values
```

The retained residual state contains:

```text
9 values
```

Total:

```text
3 + 9 = 12 degrees of representation
```

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

## Next safe step

After integrating the adversarial test into the Worker 1 branch:

1. run all Z3 and X72 regressions;
2. benchmark fast center provenance verification versus deep center verification;
3. update PR #59 with measured evidence;
4. keep PR #59 unmerged until explicit authorization;
5. only then design the combined execution frame that chains:
   `Z transform → Euler → Echo_Z → center coupling → 3+9 → provenance`.
