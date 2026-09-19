# Z3 Center Coupling v0.1

Status: CANDIDATE / PRE-INTEGRATION  
System interpretation: one 13-node system shown in mirrored form  
Authority: read-only mathematical layer

## 1. Purpose

This layer connects the four transformed triads into one reversible 12-channel state before any 3-value center summary is taken.

The design goal is:

```text
4 triads × 3 channels = 12 transformed channels
                  ↓
        reversible center coupling
                  ↓
             12 channels
                  ↓
        3-value center summary
             + 9 residuals
                  ↓
        exact reconstruction
```

The center does not silently destroy nine degrees of freedom.

## 2. One system, not two systems

The mirrored drawing is treated as one system.

```text
1 center + 4 × 3 peripheral positions = 13 nodes
```

The left/right appearance is a presentation and routing symmetry.

No implementation claim is made that there are two independent 13-node systems.

## 3. Twelve-channel representation

At one finite-Z coefficient index, the four triads are flattened as:

```text
v =
[T0.x, T0.y, T0.z,
 T1.x, T1.y, T1.z,
 T2.x, T2.y, T2.z,
 T3.x, T3.y, T3.z]^T
```

Therefore:

```text
v ∈ C^12
```

Complex values are allowed because the Z-domain representation may be complex.

## 4. Reversible 12→12 center coupling

The center coupling is a real orthogonal 12×12 matrix:

```text
C(theta) ∈ R^(12×12)
```

Applied coefficient-wise:

```text
v_c = C(theta) v
```

The matrix is constructed as an ordered product of Givens plane rotations.

Each Givens rotation has:

```text
G(i,j,theta)^T G(i,j,theta) = I
det(G(i,j,theta)) = +1
```

Therefore the full product is orthogonal and reversible:

```text
C(theta)^T C(theta) = I
C(theta)^(-1) = C(theta)^T
```

Reconstruction:

```text
v = C(theta)^T v_c
```

## 5. Candidate routing schedule v0.1

The current schedule is a project candidate, not a physical law.

It first couples six mirrored channel positions:

```text
(0,11)
(1,10)
(2,9)
(3,8)
(4,7)
(5,6)
```

Then it couples the same channel position around the four triads:

```text
x-ring:
(0,3) (3,6) (6,9) (9,0)

y-ring:
(1,4) (4,7) (7,10) (10,1)

z-ring:
(2,5) (5,8) (8,11) (11,2)
```

This is why the implementation can be described as combining:

```text
mirror coupling + four-triad ring coupling
```

The exact order is part of the v0.1 contract because the overlapping rotations are generally non-commutative.

## 6. Full-turn closure

For:

```text
theta = 2πk
```

each Givens rotation returns to identity.

Therefore:

```text
C(2πk) = I
```

within numerical tolerance.

This gives the requested multiple-of-360-degree closure as a mathematical property of the candidate coupling.

## 7. Norm preservation

Because the coupling is orthogonal:

```text
||C(theta)v||_2 = ||v||_2
```

for the 12-channel coefficient vector.

This is a mathematical conservation of Euclidean norm under the coordinate mixing.

It is not a claim about physical energy unless a later physical model defines and validates that interpretation.

## 8. Three-value center summary

After reversible 12→12 coupling, the current center summary is defined channel-wise as the mean of the four triads.

For channel `c ∈ {x,y,z}`:

```text
s_c = (T0_c + T1_c + T2_c + T3_c) / 4
```

The center therefore carries:

```text
s = [s_x, s_y, s_z]^T
```

which is exactly three values.

## 9. Why 12→3 alone cannot be inverted

A bare map from twelve independent values to three values is many-to-one in general.

The test suite explicitly demonstrates that two different 12-channel states can have the same 3-value center mean.

Therefore:

```text
CENTER_3_ONLY != PERFECT_RECONSTRUCTION
```

No code or documentation may claim otherwise.

## 10. The 3 + 9 decomposition

To retain all twelve degrees of freedom, the implementation stores three residual triads for the first three groups.

For group `g ∈ {0,1,2}` and channel `c`:

```text
r_g,c = T_g,c - s_c
```

This gives:

```text
3 center values
+
3 residual groups × 3 channels
=
3 + 9
=
12 values
```

The fourth residual is not stored because it is constrained by the mean:

```text
r_3,c = -(r_0,c + r_1,c + r_2,c)
```

Reconstruction:

```text
T_0,c = s_c + r_0,c
T_1,c = s_c + r_1,c
T_2,c = s_c + r_2,c
T_3,c = s_c - r_0,c - r_1,c - r_2,c
```

Thus:

```text
3 center + 9 residual = exact 12-value representation
```

subject only to ordinary floating-point numerical tolerance.

## 11. Relation to the user's "two bodies together"

The current mathematical implementation interprets the two mirrored visual bodies as one coupled state.

The reversible center matrix mixes mirror positions and then links corresponding x/y/z positions across all four triads.

The center summary then exposes one 3-vector while the nine residual degrees remain available for exact reconstruction.

This is a project architecture interpretation of the drawing.

It is not evidence that an external physical system has the same topology.

## 12. Relation to Z-transform / Euler / Echo_Z

The intended composition is now:

```text
raw triad sequences
→ finite Z representation
→ per-triad Euler Z-Y-Z rotation
→ transformed-domain Echo transfer
→ 12-channel reversible center coupling
→ 3-value center summary + 9 residual side state
→ provenance sealing
```

The exact final execution order remains a candidate integration question and should be benchmarked/tested before runtime integration.

## 13. Existing X72 semantics remain frozen

The center layer does not change:

```text
Echo ∈ {-1,0,+1}
Provenance ∈ {-1,0,+1}
3×3 = 9 states
```

It also does not reinterpret:

- silence;
- timeout;
- explicit negative;
- correlation;
- decision candidate;
- Queen authority.

Numerical center values remain separate from X72 ternary evidence states.

## 14. Acceptance evidence

Worker 1 center acceptance:

```text
14/14 PASS
```

Covered:

- exact 12-channel accounting;
- orthogonality;
- 12→12 round trip;
- coefficient-count preservation;
- norm preservation;
- source immutability;
- 360-degree closure;
- nontrivial channel mixing;
- 3+9 exact reconstruction;
- center mean;
- derived fourth residual;
- proof-by-test that center-only is not reconstruction;
- zero-angle identity;
- complex-coefficient support.

Worker 2 adversarial battery:

```text
15/15 PASS
```

Covered:

- invalid angle rejection;
- adversarial angles;
- repeated full turns;
- order sensitivity;
- propagation beyond one mirror pair;
- same-center / different-state counterexample;
- residual disambiguation;
- malformed state rejection;
- theta/matrix mismatch rejection;
- deterministic matrix construction.

## 15. Explicit limits

The current implementation does not prove:

- physical significance of the routing schedule;
- optimality of the center matrix;
- that the mean is the best possible center observable;
- that 3 center values alone contain all information;
- producer authenticity;
- physical novelty.

The exact mathematical statements tested above are the only current claims.

## 16. Next safe brick

Extend the existing Z3 provenance contract so it can seal:

```text
source 12-channel state hash
center coupling schedule/version
theta
12×12 coupling matrix hash
coupled 12-channel state hash
3-value center summary hash
9-value residual side-state hash
```

Then deep verification should recompute:

```text
source
→ center coupling
→ 3+9 decomposition
```

and compare every sealed result.

No merge to main until explicit authorization.
