# ASTRA CHECKPOINT — BRUTUS T6 PAPILLON AFFINITY

Date: 2026-10-13
Stage: T6 — Papillon
Mode: SHADOW_ONLY

## Definition

T6 relie les sorties T5 au Papillon144 réel sans lui donner de pouvoir moteur.

- T5 fournit le niveau opérationnel de convergence/indépendance candidate.
- Papillon144 fournit son index exact 0..143.
- T6 projette chaque observation sur ce shard et mesure la distribution.

T6 ne crée pas une géométrie 144 parallèle. Il appelle la même fonction d'index que le cache Papillon live via une nouvelle méthode publique pure `shard_index(formula_id, value)`.

## Affinités T6

- `NOT_CONVERGENT` -> `PAPILLON_BASELINE_OBSERVE`
- `CONVERGENT_SAME_LINEAGE` -> `PAPILLON_CONVERGENT_OBSERVE`
- `DIVERSE_1_AXIS` -> `PAPILLON_LOW_REVIEW`
- `DIVERSE_2_AXES_REVIEW` -> `PAPILLON_MEDIUM_REVIEW`
- `INDEPENDENCE_CANDIDATE` -> `PAPILLON_HIGH_REVIEW`

Ces affinités sont des étiquettes d'observation uniquement.

## Garde-fous

- `authority = SHADOW_ONLY`
- `papillon_cache_mutated = false`
- `papillon_policy_changed = false`
- `actual_papillon_routes_applied = 0`
- `controls_papillon = false`
- `controls_routing = false`
- `controls_scheduling = false`
- `compute_skips = 0`
- `value_mutated = false`
- `proof_promotion = false`
- `scientific_claim = false`

## Validation locale

Copie exacte POST-T5 utilisée.

Résultats:

- `T6_PUBLIC_INDEX_PURE=PASS`
- `T6_READ_ONLY=PASS`
- `T6_CHAIN=PASS`
- `T6_ROLLOVER=PASS`
- `T6_PAPILLON=PASS`

Test de pureté:

- `Papillon144.status()` avant appel T6 = après appel T6 exactement;
- aucune évaluation, hit, miss, insertion ou éviction ajoutée par T6.

Échantillon de chaîne:

- 550 observations C2->T6;
- 66 shards Papillon touchés;
- affinités: 72 baseline, 135 convergent-observe, 48 low-review, 295 medium-review, 0 high-review;
- après rollover: 664 observations;
- T6 tier counts = T5 tier observation counts exactement.

## Hashes POST-T6 attendus Linux

- papillon_engine.py: `c66cd7530d06e88c08857b9a1b3a42748296a06f542d7a0bbee0ad7ce0ccc101`
- t5_independence.py inchangé: `22d71b4d3d52093ee10aa78a5ea0f620abc4c5c06e5bddfe6ddf09b9a638a3c6`
- t6_papillon.py: `6c58c96cd46de6f10851e443b5882ffdd2c505c82f907b325cae250e1ffd0792`
- orchestrator.py: `de777c45a46b06476a44affbacf3fc9237dec0be380dd9cd767e979fa437bd56`
- dashboard.py: `52ca5d46a25c3e444eca03b38f0c9647c113741c4eafcc1f027559c370533dbd`

## Déploiement

Le workflow `deploy-brotoculateur-t6-vps.yml` impose:

1. audit exact POST-T5;
2. Papillon live à 144 shards et mode exact selective memo;
3. test du patch sur copie du live avant pause;
4. save + pause;
5. backup rollback;
6. mutation exacte;
7. restart;
8. T5=T6 en observations;
9. 144 shards confirmés;
10. zéro route Papillon appliquée par T6.

T6 est une mesure de distribution/affinité. Ce n'est ni une preuve scientifique ni une autorité de routage.