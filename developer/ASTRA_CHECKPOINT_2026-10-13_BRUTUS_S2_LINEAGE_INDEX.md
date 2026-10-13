# ASTRA CHECKPOINT — Brutus S2 Lineage Index

Date: 2026-10-13

Position officielle : `S1 Agrégateur → S2 Index lignée → S3 Index route`.

## Contrat source

Le prototype `laboratoire/brutus-colonne-37/brutus37.py` représente S2_LINEAGE_INDEX par :

`parent_z = z_stamp.parent_z`

Le runtime Z-stamp expose déjà les champs observés :

- `z_id`
- `z_parent_id`
- `z_origin_id`

S2 v1 indexe uniquement ces références déjà émises.

Pour chaque agrégat S1 valide :

- `child_z = out.z_id`
- `parent_z = out.z_parent_id`
- `origin_z = out.z_origin_id`
- index direct `child_z → parent_z`
- index inverse observé `parent_z → child_z`
- index `child_z → origin_z`

S2 ne reconstruit pas d'ancêtres transitifs et n'invente jamais un parent ou une origine manquante.

## Garde-fous

- `authority = SHADOW_ONLY`
- `prototype_measurement_parent_z = true`
- `indexes_direct_parent_only = true`
- `indexes_reverse_observed_children = true`
- `indexes_observed_origin = true`
- `infers_transitive_ancestry = false`
- `infers_missing_parent = false`
- `infers_missing_origin = false`
- `aggregate_z_identity_preserved = true`
- `creates_new_identity = false`
- `merges_distinct_z = false`
- `route_index_authority = false`
- `formula_index_authority = false`
- `s3_route_index_input = true`
- aucune mutation ValidationState
- aucun routage/scheduling/calcul
- aucune réservation de ressources
- aucun replay exécuté
- aucune promotion de preuve

## Code

PR #311 — merge `6818b4384d12b135519f2615ea1360f563b3df01`.

S2 module SHA-256 :

`6fbfc62780fcacdd1b79a7feb83cdda8a56985a8ba7ba033b6835cd08b4885b6`

Dashboard POST-S2 SHA-256 :

`71ab037d40892a4b815f5676e8deaa539583717f8f9df2cf7ce19befca9e914b`

## PRE_S2 non mutant

Workflow `38393939733` : `PASS`.

- source : `PRE_S2`
- moteur : `RUNNING`
- processed_packets : `48 793`
- cristaux : `1 872 361`
- S1 observations : `280 381`
- S1 agrégations : `163 179`
- S1 bloquées L5 : `117 202`
- S1 bloquées Z-ID : `0`
- S1 Z agrégés uniques : `1 395`
- S2 absent
- disque root : `60%`

Comptabilité attendue :

`S2 observations = S1 observations`

`S2 indexed = S1 aggregated`

`S2 blocked = S1 blocked`

`S2 unique_child_z = S1 unique_aggregate_z`

## Canary exact-copy

Workflow `38393993831` : `PASS`.

Avant mutation live, le package VPS a été copié dans un stage exact et les tests suivants ont passé :

- répétition de la même arête parent→enfant : multiplicité correcte : PASS
- même enfant Z observé depuis plusieurs parents directs : PASS
- plusieurs origines observées pour un même enfant test contrôlé : PASS
- racine sans parent inventé : PASS
- entrée S1 bloquée et Z-ID manquant : PASS
- aucune ancestry transitive inventée : PASS
- aucune autorité S3/S4 : PASS
- callback T8→S2 lockstep `17/17/17/17/17/17/17/17/17/17/17/17` : PASS
- même relation répétée 17 fois → `1` arête directe, multiplicité `17`

Hashes stage :

- S2 : `6fbfc62780fcacdd1b79a7feb83cdda8a56985a8ba7ba033b6835cd08b4885b6`
- dashboard POST-S2 : `71ab037d40892a4b815f5676e8deaa539583717f8f9df2cf7ce19befca9e914b`

Backup :

`brotoculateur/backups/s2-20261013T115914Z`

Premier battement live :

- moteur : `RUNNING`
- S1 observations : `284`
- S1 agrégations : `284`
- S2 observations : `284`
- S2 indexées : `284`
- enfants Z uniques : `49`
- parents Z uniques : `13`
- origines Z uniques : `1`
- arêtes directes parent→enfant : `74`
- enfants Z multi-parent : `13`
- enfants Z multi-origine : `0`
- multiplicité max d'une arête : `12`
- canary : `PASS`

## POST_S2 indépendant

Workflow `38394069257` : `PASS`.

- source : `POST_S2`
- moteur : `RUNNING`
- processed_packets : `5 005`
- cristaux : `1 873 292`
- S1 observations : `28 107`
- S1 agrégations : `28 107`
- S1 bloquées : `0`
- S1 Z agrégés uniques : `423`
- S2 observations : `28 107`
- S2 indexées : `28 107`
- arêtes directes parent→enfant : `765`
- enfants Z multi-parent : `89`
- enfants Z multi-origine : `0`
- multiplicité max d'une arête : `1 716`
- disque root : `60%`
- audit : `PASS`

## Interprétation

S2 est validé comme **index de lignée Z directe observée**.

Le fait que `89` enfants Z aient plusieurs parents observés dans la fenêtre POST_S2 signifie que la même identité Z technique a été atteinte depuis plus d'un parent direct observé. C'est une mesure de convergence de lignée dans ce runtime, pas une preuve scientifique et pas une ancestry reconstruite.

La multiplicité max `1 716` signifie qu'une même relation directe parent→enfant a été observée 1 716 fois dans cette fenêtre. Ce nombre n'est ni un score, ni une importance, ni un niveau de preuve.

S2 n'infère pas les grands-parents. Il ne transforme pas `z_origin_id`, les routes ou les formules en lignée cachée. Les routes restent réservées à S3 et l'index formule à S4.

## Statut final

`LIVE_VALIDATED_SHADOW` — S2 actif et validé opérationnellement.

Prochaine vertèbre officielle : `S3 — Index route`.
