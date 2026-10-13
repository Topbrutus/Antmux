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

## Validation live VPS

PR moteur: #285
Merge commit: `50ab0f95844258f612fa3caed5407e15c6696fa6`

Audit PRE-T7:

- run `38371324609`;
- source `PRE_T7`;
- moteur RUNNING;
- 128 471 paquets traites;
- 175 268 observations T6;
- Papillon 144 shards;
- T7 absent;
- audit PASS.

Canary T7:

- run `38371398857`;
- backup rollback: `/home/rob/brotoculateur/backups/t7-20261013T084519Z`;
- workflow PASS;
- moteur RUNNING;
- 87 paquets T7 = 87 paquets traites;
- 870 tentatives logiques;
- 492 appels physiques de formule;
- 1 262 appels physiques de predicat;
- 68 hits memo Papillon;
- ratio logique / appel physique de formule: 1.768293;
- 0 pouvoir moteur accorde a T7.

Audit independant POST-T7:

- run `38371517373`;
- source `POST_T7`;
- moteur RUNNING;
- 7 490 paquets T7 = 7 490 paquets traites;
- 74 900 tentatives logiques;
- 42 854 appels physiques de formule;
- 7 309 hits memo Papillon;
- 42 544 observations T6;
- Papillon 144 shards;
- 1 742 708 cristaux;
- disque racine 59%;
- environ 49 019 548 KB libres;
- audit PASS.

Interpretation stricte:

T7 mesure une reduction du nombre d'appels physiques de fonctions de formule par rapport au nombre de tentatives logiques observees dans cette configuration. Ce ratio n'est pas un benchmark de temps CPU et ne constitue pas une preuve d'acceleration chronometrique.

Les gardes restent inchanges: aucune selection de formule, aucun controle Papillon, aucun routage, aucun scheduling, aucun compute skip, aucune mutation de valeur et aucune promotion de preuve.
