# Reproducibility — ANTMUX-X72 v0.2

**Baseline tested:** `197b450`  
**Date:** 2026-09-20

## Scope

This protocol verifies the current software claims used by the technical preprint:

- orthogonality and reversibility of the 12-channel center coupling;
- preservation of the Euclidean norm within numerical tolerance;
- algebraic completeness of the 3+9 center/residual representation;
- adversarial checks on invalid angles, order sensitivity and non-invertibility of center-only 12→3;
- synchronized left/right Stereo Source from one Z input;
- reversible Da'at center/differential reconstruction and link invariants;
- evidence-ledger isolation;
- Hopscotch route invariance and full-cycle traces;
- bounded oscillator radius identity;
- coupled-field accounting invariants;
- C12 graph metric invariants;
- bounded path-capacity sampler and exact 12! route count;
- no visual eye rotation or mirror;
- runtime checkpoint reconstruction;
- visual/experimental layer isolation from authoritative Queen state.

It does **not** validate biological, psychological or physical interpretations.

## Requirements

- Python 3
- Node.js for frontend syntax and emotion-map tests
- repository checkout at the target commit

The runtime test modules are self-contained in `deploy/x72-shared-queen`.

## Core commands

From repository root on Windows PowerShell:

```powershell
$T = ".\deploy\x72-shared-queen\tests"

python "$T\test_z3_center_coupling.py"
python "$T\test_z3_center_coupling_adversarial.py"
python "$T\test_stereo_source.py"
python "$T\test_z3_runtime_bridge.py"
python "$T\test_eye_render.py"
python "$T\test_cat_mode_ui.py"
python "$T\test_daat_gate.py"
python "$T\test_daat_gate_sweep.py"
python "$T\test_daat_link.py"
python "$T\test_daat_link_sweep.py"
python "$T\test_daat_evidence.py"
python "$T\test_hopscotch_paths.py"
python "$T\test_hopscotch_sweep.py"
python "$T\test_oscillator_modes.py"
python "$T\test_oscillator_sweep.py"
python "$T\test_coupled_field.py"
python "$T\test_coupled_field_sweep.py"
python "$T\test_graph_geometry.py"
python "$T\test_graph_geometry_sweep.py"
python "$T\test_path_capacity.py"
python "$T\test_path_capacity_sweep.py"
python "$T\test_long_run_homeostasis.py"

node --check ".\laboratoire\embryon-x72\app.js"
node --check ".\laboratoire\embryon-x72\cat_mode.js"
node --check ".\laboratoire\embryon-x72\emotion_map.js"
node "$T\test_emotion_map.js"
```

## Expected baseline results

Observed on 2026-09-20:

```text
Z3 center coupling                 14/14 PASS
Z3 center coupling adversarial     15/15 PASS
Stereo Source                      10/10 PASS
Z3 runtime bridge                  10/10 PASS
Eye Render                         12/12 PASS
CAT Mode UI                        22/22 PASS
Extended reproducibility runner    22/22 test programs PASS
```

Any future release intended for scientific citation should rerun these tests and preserve the resulting logs.

## Claims tied to tests

### Orthogonality

The center coupling test checks:

```text
C(theta)^T C(theta) ≈ I
```

within floating-point tolerance.

### Norm preservation

The test checks:

```text
||C(theta)v||_2 ≈ ||v||_2
```

This is Euclidean norm preservation under an orthogonal transformation. It is **not** a physical-energy claim.

### Center representation

The tests explicitly demonstrate:

```text
CENTER_3_ONLY != PERFECT_RECONSTRUCTION
```

and verify the 3+9 residual representation.

### Stereo Source

The test verifies:

```text
left  = C(+theta)Z
right = C(-theta)Z
```

on the same source frame, together with:

```text
visible_rotation = false
mirror_x         = false
negative_eye     = false
```

### Checkpoint determinism

The runtime tests restore from checkpoint and verify the protected whole-state hash and derived stereo projection.

## Recommended release evidence

For each citable release, archive:

1. Git commit SHA;
2. exact source archive;
3. test output;
4. Python and Node versions;
5. operating system;
6. preprint version;
7. `CITATION.cff`;
8. DOI once assigned.

## Falsification policy

A failure in an invariant test is treated as evidence against the corresponding implementation claim. A semantic interpretation is not promoted to a demonstrated claim merely because the code runs or produces a visually compelling output.
