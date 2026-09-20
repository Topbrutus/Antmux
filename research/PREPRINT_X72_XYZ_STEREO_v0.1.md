# ANTMUX-X72: A Reproducible 12-Channel Orthogonal Coupling and Bilateral Stereo-Z Architecture

**Version:** 0.1  
**Author:** Topbrutus  
**Date:** 2026-09-20  
**Status:** Technical preprint draft / candidate architecture  
**Repository:** https://github.com/Topbrutus/Antmux

## Abstract

This technical preprint documents the current mathematical and software state of ANTMUX-X72. The system extracts four triads from a 72-dimensional runtime state, yielding a 12-channel representation. A candidate 12×12 orthogonal coupling is constructed as an ordered product of Givens plane rotations. The coupled state supports a three-value center summary together with nine residual values, preserving twelve algebraic degrees of freedom while explicitly acknowledging floating-point reconstruction error.

A bilateral stereo layer then evaluates the same pre-stereo Z state through two synchronized source calculations with opposite scalar phase angles, +theta and -theta. The visible eye renderer does not rotate or mirror the rendered image; the left/right distinction exists in the numerical path. The implementation additionally contains a bounded visual-state combination law for twelve tunable controls and four native light channels.

The contribution claimed here is the documented project architecture, routing schedule, integration choices, implementation and reproducibility package. This document does **not** claim that Givens rotations, bilateral averaging, noisy-OR-like bounded unions, quaternion methods, or affective computing are themselves new. It also does not claim a biological or physical law of life.

## 1. Problem statement

The project investigates whether a compact, reversible and inspectable state transformation can support:

1. a structured 12-channel representation derived from four triads;
2. reversible channel mixing with explicit mathematical invariants;
3. a compact center representation without falsely claiming that 12 independent values can be reconstructed from only 3;
4. synchronized left/right numerical paths computed from the same source state;
5. a stable visual interface whose geometry does not fabricate the left/right distinction;
6. reproducible tests separating proven implementation properties from semantic hypotheses.

The central engineering requirement is that a visually evocative interface must remain downstream from the mathematical state and must not redefine the mathematics.

## 2. Representation

At a finite Z coefficient index, the current four transformed triads are flattened as

```text
v =
[T0.x, T0.y, T0.z,
 T1.x, T1.y, T1.z,
 T2.x, T2.y, T2.z,
 T3.x, T3.y, T3.z]^T
```

so that

```text
v ∈ C^12
```

The implementation currently groups the project state into four triads of three channels. The labels used by the visual layer are project semantics; the mathematical layer is the 12-channel vector itself.
## 3. Orthogonal center coupling

The candidate center coupling is a real orthogonal matrix

```text
C(theta) ∈ R^(12×12)
```

applied coefficient-wise:

```text
v_c = C(theta) v
```

Each factor is a Givens plane rotation. Therefore, in exact arithmetic,

```text
C(theta)^T C(theta) = I
C(theta)^(-1) = C(theta)^T
```

and reconstruction is

```text
v = C(theta)^T v_c
```

The current ordered routing schedule is:

```text
(0,11) (1,10) (2,9) (3,8) (4,7) (5,6)
(0,3)  (3,6)  (6,9) (9,0)
(1,4)  (4,7)  (7,10) (10,1)
(2,5)  (5,8)  (8,11) (11,2)
```

The order is part of the v0.1 contract because overlapping rotations are generally non-commutative.

### 3.1 Verified mathematical properties

The test suite verifies numerically that the implemented matrix is orthogonal within tolerance, preserves the Euclidean norm within tolerance, reconstructs the source through the transpose, and closes to the identity for direct construction at integer full turns within floating-point tolerance.

The implementation does **not** claim the stronger group identity

```text
C(a+b) = C(a)C(b)
```

for this ordered overlapping schedule. In general that identity does not hold.

## 4. Center summary and residuals

For channel c in {x,y,z}, the center summary is

```text
s_c = (T0_c + T1_c + T2_c + T3_c) / 4
```

giving

```text
s = [s_x, s_y, s_z]^T
```

A 12-to-3 map alone is many-to-one and is **not** a reversible encoding. The current implementation therefore retains nine residual values:

```text
r_g,c = T_g,c - s_c     for g ∈ {0,1,2}
```

with the fourth residual constrained by

```text
r_3,c = -(r_0,c + r_1,c + r_2,c)
```

Thus, in exact arithmetic,

```text
3 center values + 9 residual values = 12 algebraic degrees of freedom
```

Binary64 reconstruction is measured and is not claimed to be bit-exact for every finite input.
## 5. Stereo-Z at the source

The current stereo rule is calculated before rendering. A single pre-stereo Z state enters two synchronized calculations on the same runtime frame:

```text
left  / G : Z_G = C(+theta) Z
right / D : Z_D = C(-theta) Z
```

The two branches share the same source state and the same tick, while the scalar phase sign is opposite.

A bilateral output may be formed component-wise:

```text
B_i = (G_i + D_i) / 2
```

or vectorially:

```text
B = (Z_G + Z_D) / 2
```

Importantly, the renderer is constrained by:

```text
visible_rotation_left  = 0
visible_rotation_right = 0
mirror_left            = false
mirror_right           = false
```

The opposite direction belongs to the numerical calculation, not to a rotated or mirrored image.

## 6. Phase convention

The current runtime phase convention is

```text
theta(t) = 2*pi*((t mod 7200)/7200)
```

with one nominal cycle per 7200 ticks.

### Terminology note

In public-facing material the project has sometimes used the phrase **“angle d'Euler”**. For academic precision, the current implementation should be described as a **scalar phase angle used to parameterize an ordered product of Givens rotations**. It is not presently the classical three-angle Euler parameterization of a 3-D rigid rotation.

## 7. Visual-state combination

The visual layer exposes twelve continuous state controls. For one output channel c, simultaneous state contributions are combined by

```text
L_c = 1 - product_i(1 - s_i*w_i,c)
```

with

```text
s_i ∈ [0,1]
w_i,c ∈ [0,1]
```

which guarantees

```text
0 <= L_c <= 1
```

for valid inputs.

This law is used as a bounded monotonic union. Its algebraic form is related to noisy-OR constructions, but the current project does **not** assign a probabilistic causal interpretation to the weights. The twelve labels are calibration semantics, not validated measurements of human or animal emotion.
## 8. Implementation boundary

The mathematical and runtime layers are separated from the renderer.

**Mathematical/runtime path:**
- four triads / twelve channels;
- ordered Givens coupling;
- center plus residual decomposition;
- synchronized stereo source;
- provenance and checkpoint verification.

**Visual-only path:**
- four light channels (yellow/orange, blue/turquoise, mauve, rose);
- red/gray/reflection/stripe overlays;
- twelve tunable state controls;
- stable eye rendering without visual rotation or mirror.

The visual controls are observation/calibration tools and do not mutate the protected Queen state.

## 9. Reproducibility evidence at baseline HEAD

Baseline source HEAD tested for this draft:

```text
8e05e2b85a16f311ebe832d6c201bd901c66f61f
```

Verified locally on 2026-09-20:

```text
Z3 center coupling                 14/14 PASS
Z3 center coupling adversarial     15/15 PASS
Stereo Source                      10/10 PASS
Z3 runtime bridge                  10/10 PASS
Eye Render                         12/12 PASS
CAT Mode UI                        22/22 PASS
```

The reproducibility commands are documented in `research/REPRODUCIBILITY.md`.

## 10. Related work and positioning

### 10.1 Givens rotations

Givens rotations are established numerical-linear-algebra tools. Wallace Givens described unitary plane rotations for matrix transformations in 1958. Later numerical work studied reliable and efficient computation of these rotations.

ANTMUX-X72 does not claim invention of Givens rotations. The project-specific element is the particular ordered 12-channel routing schedule and its integration into the runtime architecture.

### 10.2 Quaternion-valued neural methods

Quaternion neural networks are an established field for representing internally related multidimensional features. The current ANTMUX-X72 implementation should **not** be described as a quaternion neural network unless quaternion algebra and quaternion products are explicitly implemented and tested. The present four-triad Z structure is compared to that literature only as related multidimensional representation work.

### 10.3 Noisy-OR-like bounded combination

The formula used by the visual-state mixer has the same multiplicative complement shape that appears in noisy-OR models. The current implementation uses it as a bounded deterministic mixer. It does not currently define probabilities, conditional independence, or a causal Bayesian network.

### 10.4 Affective computing

Affective computing contains categorical and dimensional emotion models and a large literature on multimodal recognition. The twelve labels in ANTMUX-X72 are currently tunable interface states. They are not validated affect-recognition outputs and should not be presented as biological measurements without a separate empirical study.
## 11. Limitations

1. The 12-channel routing graph in v0.1 has two connected components; it is reversible but does not provide full 12-way mixing.
2. Binary64 reconstruction is approximate rather than universally bit-exact.
3. The stereo +theta/-theta construction is an engineering architecture; no biological hemispheric equivalence is claimed.
4. The bilateral mean is a chosen aggregation operator, not a demonstrated optimal estimator.
5. The twelve visual-state labels and weights are candidates awaiting empirical calibration.
6. No physical-energy conservation claim follows from Euclidean norm preservation alone.
7. No claim of novelty over all prior literature has yet been established by a systematic prior-art search.

## 12. Falsifiable next experiments

The next scientific stage should test:

1. numerical reconstruction error as a function of scale, phase and coefficient distribution;
2. norm error across large randomized and adversarial test sets;
3. sensitivity to ordering of the 18 Givens rotations;
4. comparison of the current routing schedule with alternative fully connected schedules;
5. stereo-source divergence as a function of theta;
6. whether bilateral aggregation provides measurable benefit for a defined downstream task;
7. whether the 12-state visual mapping can be tied to externally measurable signals without circular calibration.

A candidate interpretation should be rejected or revised when these tests contradict it.

## 13. Conclusion

ANTMUX-X72 currently provides a reproducible software implementation of a 12-channel orthogonal coupling, an algebraically complete center-plus-residual representation, and a synchronized bilateral stereo-Z calculation with stable rendering. The strongest present claims are implementation and numerical properties verified by tests. Semantic, affective, biological and physical interpretations remain explicitly separated as hypotheses.

## References

[1] W. Givens. *Computation of Plain Unitary Rotations Transforming a General Matrix to Triangular Form*. Journal of the Society for Industrial and Applied Mathematics, 6:26–50, 1958. DOI: 10.1137/0106004.

[2] D. Bindel, J. Demmel, W. Kahan, O. Marques. *On computing Givens rotations reliably and efficiently*. ACM Transactions on Mathematical Software, 28:206–238, 2002.

[3] T. Parcollet, M. Ravanelli, M. Morchid, G. Linarès, C. Trabelsi, R. Mori, Y. Bengio. *Quaternion Recurrent Neural Networks*. arXiv:1806.04418, 2018.

[4] S. Srinivas. *A Generalization of the Noisy-Or Model*. 1993, pp. 208–218.

[5] Y. Wang et al. *A Systematic Review on Affective Computing: Emotion Models, Databases, and Recent Advances*. arXiv:2203.06935, 2022.

## Acknowledgement

Development, calculation checks, documentation assistance and testing support were performed with AI assistance, including ChatGPT/OpenAI. Scientific claims in this document are limited to what the source code, tests and cited literature presently support.
