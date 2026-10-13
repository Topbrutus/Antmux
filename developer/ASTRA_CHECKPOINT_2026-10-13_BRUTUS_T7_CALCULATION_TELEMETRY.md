# ASTRA CHECKPOINT — BRUTUS T7 CALCULATION TELEMETRY

Date: 2026-10-13
Stage: T7 — Calcul
Mode: SHADOW_ONLY

## Definition

T7 mesure le travail de calcul reel au niveau des paquets effectivement traites par `ExperimentRunner.step()`.

Il ne doit pas etre force en correspondance 1:1 avec C2/T6, car C2/T6 observent des structures creees alors que T7 observe les paquets executes.

Invariant principal:

`T7.packet_observations == processed_packets`

Pour chaque paquet, T7 comptabilise:

- tentatives logiques de formules;
- tentatives natives hors Papillon;
- appels physiques de predicat;
- appels physiques de fonction de formule;
- evaluations Papillon;
- hits/misses du cache Papillon;
- sorties non triviales emises.

## Papillon

`Papillon144.telemetry_counters()` est une lecture pure des compteurs internes. Elle ne scanne pas les shards et ne modifie aucun cache.

T7 compare un snapshot avant/apres le traitement d'un paquet pour obtenir les deltas Papillon.

## Garde-fous

- `authority = SHADOW_ONLY`
- `controls_formula_selection = false`
- `controls_papillon = false`
- `controls_routing = false`
- `controls_scheduling = false`
- `compute_skips = 0`
- `value_mutated = false`
- `proof_promotion = false`
- `timing_claim = false`
- `performance_speedup_claim = false`

T7 ne mesure pas encore le temps CPU et ne revendique aucune acceleration chronometrique.

## Validation locale

Copie exacte POST-T6 utilisee.

Resultats:

- `T7_PAPILLON_TELEMETRY_PURE=PASS`
- `T7_CHAIN=PASS 120 1200 681 102`
- 120 paquets executes;
- 1200 tentatives logiques;
- 681 appels physiques de formule;
- 102 hits memo Papillon;
- `T7_ROLLOVER=PASS 40 60`;
- `T7_CALCULATION=PASS`;
- `T7_PYCOMPILE=PASS`;
- YAML workflow valide;
- patch idempotent.

## Hashes POST-T7 attendus Linux

- papillon_engine.py: `87045c18db95871f4cc9521bdfae1c7c4175dcf0a09ef33a8f7e35c5879fa50a`
- t6_papillon.py: `6c58c96cd46de6f10851e443b5882ffdd2c505c82f907b325cae250e1ffd0792`
- t7_calculation.py: `5d6ce094a5b9238994182d56b1740555633f4c49983a40e4abceb0a7495303fd`
- orchestrator.py: `cf4978cb315f817abf2283f41630c322a80ccbb94c75662eac8b4a87c7a05d63`
- dashboard.py: `e9bf39bfd632a2945bd976373a3e749d28140ca26160c7faeb07297cbf5af690`

## Deploiement

Le workflow `deploy-brotoculateur-t7-vps.yml` impose:

1. audit exact POST-T6;
2. test du patch sur une copie du live avant pause;
3. save + pause;
4. backup rollback;
5. mutation exacte;
6. restart;
7. verification `packet_observations == processed_packets`;
8. reconciliation logique = native + Papillon;
9. conflits de comptabilite a zero;
10. aucun pouvoir moteur accorde a T7.
