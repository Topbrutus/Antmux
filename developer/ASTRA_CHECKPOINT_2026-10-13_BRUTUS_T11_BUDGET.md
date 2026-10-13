# ASTRA CHECKPOINT — Brutus T11 Budget

Date: 2026-10-13

## Position exacte dans Colonne 37

Parcours officiel :

`... T9 Stabilité → T10 Replay → T11 Budget → T12 Candidat → L1 Score cristal ...`

T11 est la vertèbre 18/33. Ce changement ne réordonne pas le parcours.

## Ce que les sources établissent — et ce qu'elles n'établissent pas

Le parcours officiel définit T11 comme la vertèbre **Budget**. Les traces de conception disponibles précisent son rôle : arbitrer CPU, mémoire, stockage et temps après T10 Replay et avant T12 Candidat.

Aucune source inspectée ne fournit cependant de seuils numériques physiques, de coût réel d'un replay en CPU/mémoire/stockage/temps, ni de formule officielle cachée pour convertir ces ressources en nombre de replays.

T11 v1 refuse donc d'inventer cette calibration.

## Baseline vérifiée avant T11

- dépôt : `Topbrutus/Antmux`
- base Git : `5d2b75057f5be3f96ca72eb83ccde5d5910c43c9`
- T10 : `LIVE_VALIDATED_SHADOW`
- dashboard POST-T10 SHA-256 : `8b97522a6210f0c6ec2feaa1a3786bd00ffda5362aed9feee2c1966768bd61d4`
- T8 module SHA-256 : `a93bd6cd9aaaf0fe832604de9e390e6d69de7dfb8b853e558d8c9955761cce9e`
- T9 module SHA-256 : `c0e0309dfe6d571c1d786010f72bc6f8bf3ccdada1f5fa960ab6f428e3640dd1`
- T10 module SHA-256 : `9fe9b3bbb9a42c790d02e2d85638b2ea11e067750dc1cc5c6812b2c42f40a3be`
- T10 ne réserve, n'exécute et ne planifie aucun replay.

## Rôle T11 v1

T11 reçoit chaque résultat de mérite T10 :

- `REPLAY_8`
- `REPLAY_6`
- `REPLAY_4`
- `REPLAY_2`
- `REPLAY_1`

Il intersecte cette demande avec quatre plafonds de politique normalisés :

- `cpu`
- `memory`
- `storage`
- `time`

Formule déterministe :

`normalized_capacity = min(cpu_slots, memory_slots, storage_slots, time_slots)`

puis :

`advised_replays = min(T10_requested_replays, normalized_capacity)`

Les plafonds sont des **NORMALIZED_REPLAY_POLICY_SLOTS**. Ils ne prétendent pas être des cœurs CPU, octets, blocs disque ou millisecondes.

## Profil v1 neutre

Le profil initial est :

- CPU = `8`
- mémoire = `8`
- stockage = `8`
- temps = `8`

Pourquoi `8` : T10 ne demande jamais plus de 8 replays. Le profil v1 est donc volontairement neutre afin que l'ajout de T11 ne réduise pas silencieusement le mérite T10 avant calibration physique.

Ce choix ne signifie pas que la machine peut exécuter 8 replays physiquement. T11 déclare explicitement :

- `physical_calibration = false`
- `physical_units_claimed = false`
- `execution_eligible = false`

## Résultats d'arbitrage

Pour chaque observation admissible, T11 produit uniquement une recommandation :

- `BUDGET_FULL_N`
- `BUDGET_PARTIAL_M_OF_N`
- `BUDGET_ZERO_OF_N`

Une sortie T10 qui n'est pas un `REPLAY_N` reconnu devient `BLOCKED_T10_OTHER`.

## Mesures exposées

- observations
- observations admissibles
- demandes T10 totales
- replays conseillés totaux
- replays coupés par budget
- admissions pleines / partielles / zéro
- distribution demandes / conseils
- goulots par axe
- plafonds actifs
- recent 37
- compteurs par formule

## Garde-fous

T11 déclare explicitement :

- `authority = SHADOW_ONLY`
- `source_of_truth = T10_REPLAY_OUTCOME_CALLBACK`
- `slot_units = NORMALIZED_REPLAY_POLICY_SLOTS`
- `physical_calibration = false`
- `physical_units_claimed = false`
- `candidate_advisory_only = true`
- `t12_candidate_input = true`
- `execution_eligible = false`
- `reserves_resources = false`
- `executes_replay = false`
- `schedules_replay = false`
- `scientific_proof_claim = false`
- `validation_state_mutated = false`
- `controls_routing = false`
- `controls_scheduling = false`
- `controls_calculation = false`
- `compute_skips = 0`
- `value_mutated = false`
- `proof_promotion = false`

## Tests ciblés

1. profil neutre 8/8/8/8 conserve tous les mérites T10 ;
2. un goulot coupe correctement une demande ;
3. un axe à zéro donne zéro replay conseillé ;
4. un résultat T10 non Replay est bloqué ;
5. plafonds bornés entre 0 et 8 ;
6. aucune fausse unité physique ;
7. callback dashboard : delta T8 = delta T9 = delta T10 = delta T11 ;
8. aucune exécution, réservation, planification ou promotion de preuve.

## Déploiement gardé appliqué

Workflow : `.github/workflows/deploy-brotoculateur-t11-vps.yml`

Séquence appliquée :

1. audit VPS non mutant ;
2. état exact `PRE_T11` exigé ;
3. copie du package live dans un stage ;
4. T11 appliqué seulement au stage ;
5. compilation et tests sur cette copie exacte ;
6. save/pause ;
7. backup dashboard/T8/T9/T10/T11/statut/drop-in ;
8. application exacte dashboard + T11 du stage ;
9. restart ;
10. canary live ;
11. rollback automatique disponible ;
12. audit indépendant POST_T11 ;
13. checkpoint GitHub avec hashes et mesures live.

## Validation live VPS — 2026-10-13

### PR et base

- PR T11 : `#294`
- merge commit : `b1eb66e679a61be0a9462a902f4b95ba3369f955`
- mode : `SHADOW_ONLY`

### Audit PRE_T11 non mutant

Workflow : `38384513608`

État observé avant mutation :

- source : `PRE_T11`
- moteur : `RUNNING`
- processed_packets : `85 378`
- cristaux : `1 813 347`
- T8 observations : `493 178`
- T8 FAIL : `0`
- T8 LIMITED : `0`
- T9 observations : `493 178`
- T9 drifts : `0`
- T10 observations : `493 178`
- T10 admissibles : `493 178`
- mérite T10 courant total : `26 921`
- T11 module : absent
- dashboard SHA-256 : `8b97522a6210f0c6ec2feaa1a3786bd00ffda5362aed9feee2c1966768bd61d4`
- disque root : `59%`
- audit : `PASS`

### Tests sur copie exacte et canary

Workflow : `38384559732`

Le package live a été copié dans un stage temporaire. T11 a d'abord été appliqué uniquement à cette copie. Avant toute mutation live, les contrôles suivants ont passé :

- dépendance T8/T9/T10 saine : `PASS`
- patch T11 : `PASS`
- profil neutre 8/8/8/8 : `PASS`
- test goulot : `REPLAY_8 → BUDGET_PARTIAL_1_OF_8`, 1 conseillé, 7 coupés, goulot `time` : `PASS`
- budget zéro : `PASS`
- gate T10 non-Replay : `PASS`
- bornage des slots : `PASS`
- callback T8 ↔ T9 ↔ T10 ↔ T11 : lockstep `17 / 17 / 17 / 17`, `PASS`
- suite ciblée T11 : `PASS`
- stage exact live : `PASS`

Hashes du stage exact :

- dashboard POST_T11 SHA-256 : `9991bbb5513101ea66d22411dfe7da8e1ba79ebc2d1bea668ef07acec3546021`
- T8 module SHA-256 inchangé : `a93bd6cd9aaaf0fe832604de9e390e6d69de7dfb8b853e558d8c9955761cce9e`
- T9 module SHA-256 inchangé : `c0e0309dfe6d571c1d786010f72bc6f8bf3ccdada1f5fa960ab6f428e3640dd1`
- T10 module SHA-256 inchangé : `9fe9b3bbb9a42c790d02e2d85638b2ea11e067750dc1cc5c6812b2c42f40a3be`
- T11 module SHA-256 : `559824ead9ed8f824955e10cbe4d3826da4eb4673a43a64125cf46e01985221d`
- backup : `brotoculateur/backups/t11-20261013T103703Z`

Premier battement canary live :

- état : `RUNNING`
- processed_packets : `1`
- T10 observations : `5`
- T11 observations : `5`
- T11 admissibles : `5`
- demande normalisée totale : `40`
- conseil normalisé total : `40`
- coupé par budget : `0`
- slots : `cpu=8`, `memory=8`, `storage=8`, `time=8`
- delta T10 : `5`
- delta T11 : `5`
- disque root : `59%`
- workflow : `PASS`

La demande/conseil `40` signifie ici cinq événements T10 au premier palier `REPLAY_8`. Ce nombre est un agrégat consultatif de slots normalisés ; ce ne sont ni 40 recalculs exécutés, ni une réservation physique de ressources.

### Audit indépendant POST_T11

Workflow : `38384634172`

Fenêtre runtime observée après redémarrage du service :

- source : `POST_T11`
- moteur : `RUNNING`
- processed_packets : `4 461`
- cristaux : `1 814 095`
- T8 observations : `24 845`
- T8 FAIL : `0`
- T8 LIMITED : `0`
- T9 observations : `24 845`
- T9 drifts : `0`
- T10 observations : `24 845`
- T10 admissibles : `24 845`
- mérite T10 courant total : `2 843`
- T11 mode : `BRUTUS_T11_BUDGET_V1`
- T11 activé : `true`
- T11 observations : `24 845`
- demande normalisée cumulée : `40 043`
- conseil normalisé cumulé : `40 043`
- coupé par budget : `0`
- profil de slots : `8/8/8/8`
- capacité normalisée : `8`
- dashboard SHA-256 : `9991bbb5513101ea66d22411dfe7da8e1ba79ebc2d1bea668ef07acec3546021`
- T11 module SHA-256 : `559824ead9ed8f824955e10cbe4d3826da4eb4673a43a64125cf46e01985221d`
- disque root : `59%`
- audit : `PASS`

L'audit a également vérifié que T11 reste `SHADOW_ONLY`, qu'il reçoit ses observations depuis T10, que les unités sont des slots de politique normalisés, que `physical_calibration=false`, `physical_units_claimed=false`, `execution_eligible=false`, `reserves_resources=false`, `executes_replay=false`, `schedules_replay=false`, que la sortie est uniquement consultative pour T12 et qu'aucune promotion de preuve n'a lieu.

## Interprétation

T11 a démontré le bon fonctionnement opérationnel de l'arbitre Budget **normalisé** dans la configuration live observée. Le profil neutre 8/8/8/8 laisse passer entièrement le mérite T10, tandis que les tests contrôlés prouvent que des plafonds plus bas coupent correctement une demande et identifient le goulot.

Cette validation ne constitue **pas** une calibration physique CPU/mémoire/stockage/temps. Le dépôt ne fournit pas encore de mesure de coût réel permettant d'associer un slot à des cœurs, des octets ou des millisecondes. T11 v1 n'invente donc aucune équivalence.

Le total `40 043` est un agrégat de demandes/conseils normalisés par observation durant la fenêtre POST_T11. Il ne doit pas être confondu avec le mérite T10 courant `2 843`, qui est un agrégat courant par clé, ni avec un nombre de replays réellement exécutés. T11 ne réserve aucune ressource et n'exécute rien.

## Statut final

`LIVE_VALIDATED_SHADOW` — T11 actif et validé opérationnellement comme arbitre de politique normalisé. Prochaine vertèbre officielle : `T12 — Candidat`.
