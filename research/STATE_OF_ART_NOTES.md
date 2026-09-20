# State-of-the-art notes — ANTMUX-X72 v0.1

This note separates established techniques from project-specific composition choices.

## 1. Givens rotations — established

Wallace Givens introduced plane/unitary rotations for matrix transformations in the 1950s. The current project uses ordered Givens rotations as known mathematical building blocks.

Reference:
- W. Givens, *Computation of Plain Unitary Rotations Transforming a General Matrix to Triangular Form*, Journal of the Society for Industrial and Applied Mathematics, 6:26–50, 1958. DOI: 10.1137/0106004.

Reliability and floating-point implementation of Givens rotations have also been studied extensively:
- D. Bindel, J. Demmel, W. Kahan, O. Marques, *On computing Givens rotations reliably and efficiently*, ACM Transactions on Mathematical Software, 28:206–238, 2002.

### Positioning for ANTMUX-X72

Do not claim invention of Givens rotations or orthogonal norm preservation.

Candidate project-specific contribution:
- the exact ordered 18-pair routing schedule;
- its 12-channel / four-triad integration;
- the center+residual reconstruction contract;
- its use as one stage of the ANTMUX-X72 runtime.

## 2. Quaternion neural networks — established, but not the current implementation

Quaternion-valued neural methods use quaternion algebra to preserve internal multidimensional relationships.

Reference:
- T. Parcollet et al., *Quaternion Recurrent Neural Networks*, arXiv:1806.04418, 2018.

### Positioning for ANTMUX-X72

The current four-triad representation is **not sufficient** to call the implementation quaternion-valued. Unless Hamilton products / quaternion algebra are explicitly present and tested, use:
- “four-triad 12-channel representation”;
- “multidimensional structured state”.

Do not use “quaternion neural network” as a formal claim.

## 3. Noisy-OR family — established

Noisy-OR and generalizations use multiplicative complement forms to combine multiple causes.

Reference:
- S. Srinivas, *A Generalization of the Noisy-Or Model*, 1993, pp. 208–218.

The current visual mixer:

```text
L_c = 1 - product_i(1 - s_i*w_i,c)
```

has a similar algebraic shape.

### Positioning for ANTMUX-X72

Current use is deterministic and bounded. There is no defined conditional-probability semantics or Bayesian causal interpretation.

Preferred wording:
- “bounded monotonic union”;
- “noisy-OR-like algebraic form”.

## 4. Affective computing — established

Affective computing already contains categorical, dimensional, physiological and multimodal emotion representations.

Reference:
- Y. Wang et al., *A Systematic Review on Affective Computing: Emotion Models, Databases, and Recent Advances*, arXiv:2203.06935, 2022.

### Positioning for ANTMUX-X72

The current twelve labels are visual calibration controls, not validated affect recognition.

Do not claim:
- biological emotion detection;
- clinical interpretation;
- validated animal affect inference.

A future empirical study would need:
- operational definitions;
- measurable signals;
- labelled or independently assessed ground truth;
- preregistered evaluation criteria;
- held-out validation data.

## 5. Novelty question still open

The scientific novelty question is not:

> “Are any ingredients new?”

Several ingredients are established.

The stronger research question is:

> “Is the specific composition — the 12-channel schedule, center/residual contract, source-level +theta/-theta stereo construction, runtime provenance and downstream use — materially distinct from previously published architectures, and does it produce measurable advantages?”

That requires a systematic prior-art search and comparative experiments.

## 6. Search terms for the next literature pass

- ordered Givens rotation networks
- structured orthogonal transforms neural networks
- learnable Givens rotations
- butterfly orthogonal matrices
- bilateral latent representation
- dual-path latent state transformation
- symmetric / antisymmetric feature transforms
- paired phase rotations latent representations
- orthogonal recurrent neural networks
- center-residual decomposition multichannel
- noisy-OR continuous activation fusion
- affective computing continuous state blending

## 7. Evidence hierarchy for future claims

1. mathematical identity / proof;
2. deterministic unit test;
3. adversarial / falsification test;
4. randomized simulation;
5. baseline comparison;
6. external replication;
7. peer review;
8. application-specific empirical validation.

A screenshot, aesthetic resemblance or symbolic analogy is not evidence of mathematical novelty.
