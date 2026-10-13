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

## Déploiement prévu

Workflow : `.github/workflows/deploy-brotoculateur-t11-vps.yml`

Séquence :

1. audit VPS non mutant ;
2. exiger état exact `PRE_T11` ;
3. copier le package live dans un stage ;
4. appliquer T11 seulement au stage ;
5. compiler et exécuter les tests sur cette copie exacte ;
6. save/pause ;
7. backup dashboard/T8/T9/T10/T11/statut/drop-in ;
8. appliquer exactement dashboard + T11 du stage ;
9. restart ;
10. canary live ;
11. rollback automatique si dérive ;
12. audit indépendant POST_T11 ;
13. checkpoint GitHub avec hashes et mesures live.

## Statut avant déploiement

`READY_FOR_PR` — T11 n'est pas encore déployé live au moment de cette section.
