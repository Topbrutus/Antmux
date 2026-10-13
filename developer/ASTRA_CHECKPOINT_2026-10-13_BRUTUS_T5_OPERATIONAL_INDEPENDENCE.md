# ASTRA CHECKPOINT — BRUTUS T5 OPERATIONAL INDEPENDENCE

Date: 2026-10-13
Stage: T5 — Indépendance opérationnelle
Mode: SHADOW_ONLY

## Définition

T5 ne transforme jamais une convergence T4 en preuve scientifique.

La chaîne est volontairement stricte:

- T2 = doublon exact C2;
- T3 = voisinage sémantique;
- T4 = plusieurs C2 distincts convergent vers une même cible Z;
- T5 = qualification de diversité de lignée sur une cible déjà convergente T4.

T5 lit uniquement un résumé public et borné de T4: `target_summary(z_id)`.

## Loi T5

Pour une cible T4 convergente (`distinct_c2 >= 2`):

- 0 axe diversifié: `CONVERGENT_SAME_LINEAGE`;
- 1 axe: `DIVERSE_1_AXIS`;
- 2 axes: `DIVERSE_2_AXES_REVIEW`;
- 3 axes: `INDEPENDENCE_CANDIDATE`.

Les trois axes sont:

1. au moins 2 familles T1;
2. au moins 2 origines Z;
3. au moins 2 parents Z.

Seul le niveau 3 axes porte le nom `INDEPENDENCE_CANDIDATE`.
Même ce niveau reste un candidat opérationnel à contre-tester, jamais une preuve scientifique.

## Garde-fous

- `scientific_independence_claim = false`
- `operational_candidate_only = true`
- `authority = SHADOW_ONLY`
- `deduplication_applied = false`
- `packets_collapsed = 0`
- `controls_routing = false`
- `controls_scheduling = false`
- `compute_skips = 0`
- `value_mutated = false`
- `proof_promotion = false`

Un doublon exact ne crée jamais un nouveau candidat T5.
Une cible à seulement deux axes reste en revue et n'est pas promue.

## Mémoire

T5 ne recopie pas les structures T4.

Il conserve seulement une signature compacte de cible et son niveau maximal observé.
La limite par défaut est `BROTO_T5_MAX_TARGETS=16384`.
T4 reste la source de vérité pour les comptes C2/familles/origines/parents.

## Validation locale

Copie bit-identique POST-T4 utilisée.

Résultats:

- `T5_THREE_AXIS=PASS`
- `T5_TWO_AXIS_REVIEW=PASS`
- `T5_CHAIN=PASS`
- `T5_ROLLOVER=PASS`
- `T5_INDEPENDENCE=PASS`

Chaîne naturelle locale:

- 550 observations C2→T5 synchronisées;
- niveaux cibles: 36 NOT_CONVERGENT, 15 CONVERGENT_SAME_LINEAGE, 2 DIVERSE_1_AXIS, 10 DIVERSE_2_AXES_REVIEW, 0 INDEPENDENCE_CANDIDATE;
- après rollover: 693 observations;
- 0 conflit T4.

Le test synthétique séparé prouve qu'une cible convergente avec 2 familles + 2 origines + 2 parents atteint bien `INDEPENDENCE_CANDIDATE`, puis qu'un doublon exact ultérieur ne crée pas un deuxième candidat.

## Hashes POST-T5 attendus Linux

- t4_convergence.py: `228333cc7153a390f45b93ca3f79a43065ba0697a36b54034a67b623c21387c8`
- t5_independence.py: `22d71b4d3d52093ee10aa78a5ea0f620abc4c5c06e5bddfe6ddf09b9a638a3c6`
- orchestrator.py: `461a18418bf2abc0c4f434287e5783d1e29bfaf67d9837d9e388b8a6f1b8fb7c`
- dashboard.py: `dc7d1fe9212a30f40371381b8abfcca91d5ea490227859a4759412d72ca59c10`

## Déploiement

Le workflow `deploy-brotoculateur-t5-vps.yml` impose:

1. audit exact POST-T4;
2. vérification C2→T4 1:1;
3. test du patch sur une copie exacte du live avant pause;
4. save + pause;
5. backup rollback de orchestrator/dashboard/T4/T5/drop-in;
6. mutation exacte;
7. restart;
8. preuve live T4=T5 en observations;
9. conflits T4 à zéro;
10. aucun pouvoir moteur accordé à T5.
