# ASTRA CHECKPOINT — Brutus L2 Seuil

Date: 2026-10-13

Position officielle : `L1 Score cristal → L2 Seuil → L3 Press`.

Le prototype fondateur laissait `threshold: None`. Aucune source inspectée ne fournit de seuil scientifique officiel.

L2 v1 utilise donc une référence d'ingénierie configurable, par défaut `75.0/100`, soit trois quarts de l'échelle normalisée L1. Ce seuil n'est pas scientifiquement calibré.

Sorties :
- `AT_OR_ABOVE_ENGINEERING_REFERENCE`
- `BELOW_ENGINEERING_REFERENCE`

L2 n'accepte ni ne rejette un candidat, ne modifie aucun ValidationState, ne canonise rien et ne promeut aucune preuve.

## Code

PR #300, merge `7db4371e0d4b835fb5c25ab61732c8c943219a5f`.

L2 module SHA-256 : `912b662ee544a76f5b7db6f37d265ba0bb748f8b3d5a32287df93d2b12c0b898`.

Dashboard POST-L2 SHA-256 : `fea396adeba7611f0c5a1fddf67088646e484eeb25d7e2bffbffe4474adeea65`.

## PRE_L2

Workflow `38388481325` PASS.

- source PRE_L2
- moteur RUNNING
- cristaux 1,838,270
- L1 observations 418,454
- score moyen L1 98.533146
- L2 absent
- disque 60%

## Canary

Workflow `38388547433` PASS.

Tests exact-copy : frontière 75, au-dessus/en-dessous, garde-fous, bornes de configuration et lockstep T8→L2 PASS.

Premier live :
- L1 = 549
- L2 = 549
- compared = 549
- threshold = 75.0
- at_or_above = 438
- below = 111
- margin_average = 8.076372

Backup : `brotoculateur/backups/l2-20261013T111202Z`.

## POST_L2 indépendant

Workflow `38388606079` PASS.

- source POST_L2
- moteur RUNNING
- cristaux 1,838,912
- L1 observations 17,788
- score moyen L1 97.545195
- L2 observations 17,788
- compared 17,788
- at_or_above 17,353
- below 435
- disque 60%

Statut final : `LIVE_VALIDATED_SHADOW`.

Important : le seuil 75 est une référence d'ingénierie v1, configurable et explicitement non calibrée scientifiquement. Il ne signifie ni preuve, ni acceptation scientifique, ni canonisation.

Prochaine vertèbre : `L3 — Press`.
