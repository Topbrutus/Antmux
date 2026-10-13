# ASTRA CHECKPOINT — Brutus S1 Aggregator

Date: 2026-10-13

Position officielle : `L5 Placement → S1 Agrégateur → S2 Index lignée`.

## Contrat source

Le prototype `laboratoire/brutus-colonne-37/brutus37.py` représente S1_AGGREGATOR par :

`aggregate_z = z_stamp.z_id`

S1 v1 respecte ce contrat : une observation L5 HOT valide est agrégée sous l'identité Z déjà existante. Les répétitions du même Z augmentent sa multiplicité. Des Z distincts ne sont jamais fusionnés.

Formule opérationnelle :

`aggregate_z = out.z_id`

`aggregate_count[aggregate_z] += 1`

L'agrégation est donc un comptage de multiplicité par identité Z stable, pas une création d'identité ni une fusion scientifique.

## Garde-fous

- `authority = SHADOW_ONLY`
- `aggregate_z_is_output_z_id = true`
- `aggregate_z_is_l5_canonical_z = true`
- `merges_distinct_z = false`
- `creates_new_identity = false`
- `counts_multiplicity_only = true`
- `preserves_hot_placement = true`
- `preserves_both_reference_sides = true`
- `s2_lineage_index_input = true`
- aucun score ajouté
- aucun nouveau seuil
- aucun accept/reject
- aucune mutation ValidationState
- aucun routage/scheduling/calcul
- aucune réservation de ressources
- aucun replay exécuté
- aucune promotion de preuve

## Code

PR #309 — merge `3e4dda986b0d3205b41d14c0b620689e0e68f61d`.

S1 module SHA-256 :

`7c08763dc64d7ce7122885b6afc1bc63b9f43a8f90699f5286bf4a6042afe357`

Dashboard POST-S1 SHA-256 :

`7f68744ad3458e77b9b8be74722943f3457318ad58a4c23bf23b793a67d13f6b`

## PRE_S1 non mutant

Workflow `38392974315` : `PASS`.

- source : `PRE_S1`
- moteur : `RUNNING`
- processed_packets : `58 425`
- cristaux : `1 866 188`
- L5 observations : `336 616`
- L5 placements : `155 611`
- L5 bloquées L4 : `181 005`
- L5 bloquées Z-ID : `0`
- L5 Z placés uniques : `1 278`
- S1 absent
- disque root : `60%`

La baseline valide la comptabilité à préserver :

`S1 observations = L5 observations`

`S1 aggregated = L5 placed`

`S1 blocked_l5_other = L5 blocked_l4_other + L5 blocked_missing_z`

`S1 unique_aggregate_z = L5 unique_placed_z`

## Canary exact-copy

Workflow `38393033949` : `PASS`.

Avant mutation live, le package VPS a été copié dans un stage exact et les tests suivants ont passé :

- répétition du même Z → multiplicité correcte : PASS
- Z distincts jamais fusionnés : PASS
- résultat L5 invalide → blocage : PASS
- Z-ID absent → blocage : PASS
- aucune fausse autorité / aucune promotion de preuve : PASS
- callback T8→S1 lockstep `17/17/17/17/17/17/17/17/17/17/17` : PASS
- même Z répété 17 fois → `1 aggregate_z`, multiplicité `17`
- côtés contrôlés : `16 AT_OR_ABOVE`, `1 BELOW`

Hashes stage :

- S1 : `7c08763dc64d7ce7122885b6afc1bc63b9f43a8f90699f5286bf4a6042afe357`
- dashboard POST-S1 : `7f68744ad3458e77b9b8be74722943f3457318ad58a4c23bf23b793a67d13f6b`

Backup :

`brotoculateur/backups/s1-20261013T115057Z`

Premier battement live :

- moteur : `RUNNING`
- L5 observations : `318`
- L5 placements : `318`
- S1 observations : `318`
- S1 agrégations : `318`
- Z agrégés uniques : `51`
- Z agrégés répétés : `29`
- multiplicité max : `30`
- côté `AT_OR_ABOVE_REFERENCE` : `236`
- côté `BELOW_REFERENCE` : `82`
- canary : `PASS`

## POST_S1 indépendant

Workflow `38393103926` : `PASS`.

- source : `POST_S1`
- moteur : `RUNNING`
- processed_packets : `3 405`
- cristaux : `1 866 910`
- L5 observations : `18 589`
- L5 placements : `18 589`
- L5 bloquées L4 : `0`
- L5 bloquées Z-ID : `0`
- L5 Z placés uniques : `242`
- S1 observations : `18 589`
- S1 agrégations : `18 589`
- S1 Z agrégés uniques : `242`
- S1 Z agrégés répétés : `188`
- multiplicité max observée : `2 673`
- disque root : `60%`
- audit : `PASS`

## Interprétation

S1 est validé comme **agrégateur de multiplicité par identité Z**.

Un `aggregate_z` signifie ici : « l'identité Z technique déjà placée HOT par L5, utilisée comme clé stable pour compter combien d'observations de cette même identité sont revenues ».

La multiplicité max `2 673` signifie qu'au moins une identité Z a été observée 2 673 fois dans la fenêtre runtime POST_S1. Ce nombre n'est pas un score scientifique, une preuve, une importance, une priorité ou une fusion de 2 673 objets différents.

S1 ne fusionne jamais deux Z distincts. Il ne modifie ni l'identité, ni la valeur, ni le statut scientifique. Il prépare seulement la matière agrégée pour S2 Index lignée.

## Statut final

`LIVE_VALIDATED_SHADOW` — S1 actif et validé opérationnellement.

Prochaine vertèbre officielle : `S2 — Index lignée`.
