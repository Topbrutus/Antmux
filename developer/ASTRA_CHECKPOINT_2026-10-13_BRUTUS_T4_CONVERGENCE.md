# ASTRA CHECKPOINT — BRUTUS T4 CONVERGENCE

Date: 2026-10-13
Stage: T4 — Convergence
Mode: SHADOW_ONLY

## Definition

T4 ne compte pas un doublon exact comme une convergence.

- T2 = meme C2 qui revient.
- T3 = C2 distinct mais voisin semantiquement.
- T4 = plusieurs C2 distincts qui aboutissent a la meme cible Z canonique.

La cle de cible est le `z_id`, qui represente la valeur canonique estampillee par le Cortex Z.
Les C2 sont conserves sous forme de signatures compactes bornees par cible.

## Garde-fous

- `exact_duplicate_counts_as_convergence = false`
- `hash_distance_used = false`
- `scientific_convergence_claim = false`
- `deduplication_applied = false`
- `packets_collapsed = 0`
- `controls_routing = false`
- `controls_scheduling = false`
- `compute_skips = 0`
- `value_mutated = false`
- `proof_promotion = false`

T4 reste une mesure operationnelle. Une convergence T4 n'est pas une preuve scientifique.

## Mesures T4

T4 suit notamment:

- observations totales;
- cibles Z suivies;
- structures C2 distinctes par cible;
- evenements de convergence structurelle;
- cibles devenues convergentes;
- convergences inter-familles T1;
- convergences multi-origines Z;
- convergences multi-parents Z;
- distribution des convergences par classe T3;
- conflits de coherence avec T2/T3;
- pression de capacite.

## Bornes memoire

- `BROTO_T4_MAX_TARGETS`, defaut 16 384;
- `BROTO_T4_SIGS_PER_TARGET`, defaut 16;
- historique recent: 37 evenements.

Quand une cible atteint sa limite de signatures, T4 compte la pression de capacite sans inventer un conflit T2/T3.

## Validation locale

Copie exacte POST-T3 utilisee.

Resultats:

- `T4_SEMANTICS=PASS`
- `T4_CAPACITY_GUARD=PASS`
- `T4_CHAIN=PASS`
- `T4_ROLLOVER=PASS`
- `T4_CONVERGENCE=PASS`

Echantillon local de chaine:

- 550 observations;
- 63 cibles Z suivies;
- 214 convergences structurelles;
- qualificateurs T3 de convergence: 203 NEAR, 10 ADJACENT, 1 DISTANT;
- 0 conflit T2;
- 0 conflit T3.

## Hashes POST-T4 attendus Linux

- t4_convergence.py: `736f19b2b2bf25b65d7fa32e17576c3dac3125fb8bf3cb063bb00e6629482ed5`
- orchestrator.py: `1ee7c8e61d538f4d8c5617179a64bc3b15e8c3084ea096a909fa4343afbf737e`
- dashboard.py: `0d2a7f64fe8082186060210891ded1fc12ddeef01daacfbaff496f9e63d41cc6`
- t3_neighborhood.py reste: `f4144e566508d6bd0e17279690d3ff9edd72e85a93d5a0d8dead2beeab1310d6`

## Deploiement

Le workflow `deploy-brotoculateur-t4-vps.yml` impose:

1. audit exact POST-T3;
2. test du patch sur une copie du live avant pause;
3. save + pause;
4. backup rollback;
5. mutation exacte;
6. restart;
7. verification T3=T4 en observations;
8. conflits T2/T3 a zero;
9. aucun pouvoir moteur accorde a T4.
