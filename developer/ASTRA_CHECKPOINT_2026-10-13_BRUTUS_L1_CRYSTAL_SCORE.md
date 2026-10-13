# ASTRA CHECKPOINT — Brutus L1 Score cristal

Date: 2026-10-13

Position officielle : `T12 Candidat → L1 Score cristal → L2 Seuil`.

Le prototype fondateur laissait `score: None` à L1 et `threshold: None` à L2. L1 v1 utilise donc un score d'ingénierie transparent, pas un score scientifique.

Formule : `100 * mean(countertest, stability, replay_maturity, budget_fulfillment)`.

Poids : 0.25 chacun.

- countertest : T8 PASS = 1.0
- stability : T9 BASELINE = 0.5 ; STABLE_REPEAT = 1.0
- replay_maturity : `(8 - T10_requested_replays) / 7`
- budget_fulfillment : `T11_advised / T11_requested`

Garde-fous : SHADOW_ONLY, score 0–100, aucun seuil, aucun accept/reject, aucune canonisation, aucune promotion de preuve, aucune autorité calcul/routage/scheduling/replay. L2 reste la prochaine couche de seuil.

## Code

PR #298, merge `0b2bb52c957d221609f25b9a5197223e13694c3c`.

L1 module SHA-256 : `2f5d674410d284e0e274a2ef347666d3cd18aa4a0235a4cc5fdabcb37469bca4`.

Dashboard POST-L1 SHA-256 : `b0f450f62bd6096fe4481fb1bed5a9072a866d117e4b772d91ab8663f0485749`.

## PRE_L1

Workflow `38387119073` PASS.

- source PRE_L1
- moteur RUNNING
- cristaux 1,829,131
- T12 observations 276,197
- L1 absent
- disque 60%

## Canary

Workflow `38387186498` PASS.

Tests exact-copy : formule, upstream gates, aucun seuil/promotion, lockstep T8→L1 PASS.

Premier live :
- T12 = 186
- L1 = 186
- scored = 186
- moyenne = 76.881720
- min = 62.5
- max = 89.285714
- composantes moyennes : countertest 1.0, stability 0.860215, replay_maturity 0.215054, budget_fulfillment 1.0

Backup : `brotoculateur/backups/l1-20261013T110020Z`.

## POST_L1 indépendant

Workflow `38387286728` PASS.

- source POST_L1
- moteur RUNNING
- cristaux 1,830,120
- T12 observations 27,064
- L1 observations 27,064
- scored 27,064
- moyenne 97.385562
- min 62.5
- max 100.0
- disque 60%

Statut final : `LIVE_VALIDATED_SHADOW`.

Prochaine vertèbre : `L2 — Seuil`.
