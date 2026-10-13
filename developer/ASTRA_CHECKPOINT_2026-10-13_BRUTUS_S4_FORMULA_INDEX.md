# ASTRA CHECKPOINT — Brutus S4 Index formule

Date: 2026-10-13

Position officielle : `S3 Index route → S4 Index formule → S5 Index rapide`.

## Contrat source

Le prototype `laboratoire/brutus-colonne-37/brutus37.py` place S4 immédiatement après S3 et utilise `z_stamp.formula_id` comme mesure de `S4_FORMULA_INDEX`.

La vitrine du prototype décrit S4 ainsi :

`Indexe les résultats par formule.`

Le runtime live transmet déjà le `formula_id` exact au callback de résultat et conserve la trace opérationnelle dans `formula_chain`. La relation de lignée déjà vérifiée par T8 impose :

`out.formula_chain == source.formula_chain + (formula_id,)`

S4 v1 ne fabrique donc aucun nouvel identifiant de formule. Il indexe seulement la formule exacte déjà exécutée vers l'identité Z existante du résultat :

`formula_id → output_z_id`

et maintient aussi la vue inverse :

`output_z_id → formules observées`

Une même formule peut produire plusieurs Z distincts. Un même Z peut être atteint par plusieurs formules distinctes. S4 conserve ces relations sans fusionner, classer ou promouvoir les formules.

## Garde de cohérence formule

S4 exige que la formule reçue par le callback corresponde à la dernière formule réellement inscrite dans `out.formula_chain`.

Si :

`terminal(out.formula_chain) != formula_id`

alors S4 retourne `BLOCKED_FORMULA_CHAIN_MISMATCH` et n'indexe pas l'association.

Cette garde empêche une association formule↔résultat d'être inventée par télémétrie.

## Garde-fous

- `authority = SHADOW_ONLY`
- `source_of_truth = S3_INDEXED_RESULT_PLUS_EXACT_CALLBACK_FORMULA_ID_PLUS_EXISTING_OUTPUT_Z_ID`
- `index_definition = EXACT_FORMULA_ID_TO_EXISTING_OUTPUT_Z_ID`
- `prototype_measurement_formula_id = true`
- `indexes_results_by_formula = true`
- `uses_callback_formula_id = true`
- `requires_formula_chain_terminal_match = true`
- `creates_formula = false`
- `executes_formula = false`
- `selects_formula = false`
- `ranks_formula = false`
- `assigns_formula_score = false`
- `merges_distinct_formulas = false`
- `formula_registry_mutated = false`
- `route_index_mutated = false`
- `z_identity_preserved = true`
- `s5_fast_index_input = true`
- aucune mutation ValidationState
- aucun contrôle du routage
- aucun contrôle du scheduling
- aucun contrôle du calcul
- aucune réservation de ressources
- aucun replay exécuté ou planifié
- aucun compute skip
- aucune mutation de valeur
- aucune promotion de preuve
- aucune revendication de preuve scientifique

## Code

PR #315 — merge :

`de14497f8fb3f7dca79348d40b5c8d04cf399aa9`

S4 module SHA-256 :

`3c9431bbdf7fc0be33d1eae38455d1584ec87b250b4fe09e0bc849cbc117ebc9`

Dashboard POST-S4 SHA-256 :

`5161995d53af3bbefa39aec6fd6a69b6aaa7af10d1295eef5d61fc133cb15f5e`

S3 module conservé :

`35b76679778254e179dcb2df8b2415aa9634319dbc511408eb23bf544f4b9ca3`

## PRE_S4 non mutant

Workflow `38397251681` : `PASS`.

- source : `PRE_S4`
- dashboard SHA : `b39265fedc454b0187d7ec3a2d2e29dba2840716590db52960b89b6300e3e3ea`
- S4 : absent
- moteur : `RUNNING`
- processed_packets : `66 814`
- cristaux : `1 890 658`
- S3 observations : `384 393`
- S3 indexées : `150 586`
- S3 bloquées par S2 : `233 807`
- S3 bloquées Z-ID : `0`
- S3 bloquées branch_path : `0`
- S3 bloquées Papillon : `0`
- S3 path drift : `0`
- S3 Z uniques : `1 300`
- disque root : `60%`
- `S4_AUDIT_ONLY=PASS`

Comptabilité attendue après activation :

`S4 observations = S3 observations`

`S4 indexed = S3 indexed`

`S4 blocked = S3 blocked`

`S4 unique_result_z = S3 unique_z_indexed`

## Canary exact-copy

Workflow `38397315239` : `PASS`.

Avant mutation live, le package VPS a été copié dans un stage exact puis patché sous garde des SHA PRE.

Tests exécutés :

- couple formule→résultat exact répété : `PASS`
  - exemple Z : `Z-016f078a8f71cbe65181c1ca6ae3fe63`
  - multiplicité contrôlée : `3`
- une formule vers plusieurs résultats Z : `PASS`
  - `PLUS1` observé vers deux Z distincts
- un même Z atteint par plusieurs formules : `PASS`
  - `PLUS1 : 10 → 11`
  - `HALF_EVEN : 22 → 11`
  - même Z technique : `Z-016f078a8f71cbe65181c1ca6ae3fe63`
  - formules conservées séparément : `HALF_EVEN`, `PLUS1`
- blocage des entrées S3 non indexées : `PASS`
- blocage `formula_id` manquant : `PASS`
- blocage Z-ID manquant : `PASS`
- blocage callback/formula_chain incohérent : `PASS`
- aucune autorité de formule : `PASS`
- callback T8→S4 lockstep `17` sur chacun des 14 modules : `PASS`
- sur ces 17 répétitions contrôlées :
  - formules uniques : `1`
  - Z résultat unique : `1`
  - multiplicité du couple : `17`
- `S4_FORMULA_INDEX=PASS`
- `S4_EXACT_LIVE_STAGE=PASS`

Backup :

`brotoculateur/backups/s4-20261013T122650Z`

Premier battement live :

- moteur : `RUNNING`
- S3 observations : `243`
- S3 indexées : `243`
- S4 observations : `243`
- S4 indexées : `243`
- formules uniques : `8`
- Z résultats uniques : `44`
- couples formule↔Z uniques : `64`
- formules multi-résultat : `8`
- Z multi-formule : `12`
- multiplicité max d'un couple formule↔Z : `17`
- `S4_LIVE_VERIFY=PASS`
- `S4_WORKFLOW=PASS`

## POST_S4 indépendant

Workflow `38397388987` : `PASS`.

- source : `POST_S4`
- dashboard SHA : `5161995d53af3bbefa39aec6fd6a69b6aaa7af10d1295eef5d61fc133cb15f5e`
- S4 SHA : `3c9431bbdf7fc0be33d1eae38455d1584ec87b250b4fe09e0bc849cbc117ebc9`
- moteur : `RUNNING`
- processed_packets : `3 183`
- cristaux : `1 891 349`
- S3 observations : `17 482`
- S3 indexées : `17 482`
- S3 blocages : `0`
- S3 Z uniques : `255`
- S4 observations : `17 482`
- S4 indexées : `17 482`
- formules uniques : `8`
- Z résultats uniques : `255`
- couples formule↔Z uniques : `376`
- formules multi-résultat : `8`
- Z multi-formule : `60`
- multiplicité max formule↔Z : `1 038`
- disque root : `60%`
- `S4_AUDIT_ONLY=PASS`

## Interprétation

Dans la fenêtre POST_S4, S4 a observé exactement les `17 482` résultats que S3 avait indexés. Il n'y a aucun écart entre les compteurs S3 et S4 dans cette fenêtre.

Les `8` formules uniques sont les identifiants de formules effectivement observés dans cette fenêtre. Ce nombre ne signifie ni « huit meilleures formules », ni huit découvertes, ni huit preuves.

Les `255` Z résultats uniques correspondent exactement aux `255` Z uniques exposés par S3 dans la même fenêtre.

Les `376` couples formule↔Z représentent des associations distinctes réellement observées entre une formule exacte et une identité Z résultat existante.

Les `8` formules multi-résultat signifient que chacune des huit formules observées a produit plus d'une identité Z au cours de la fenêtre. Cela n'est pas un score de qualité.

Les `60` Z multi-formule signifient que 60 identités Z ont été atteintes par plus d'une formule exacte. Cela décrit une convergence opérationnelle de résultats au niveau de l'index. Cela ne constitue pas une preuve d'indépendance, de nouveauté scientifique ou de validité mathématique supérieure.

La multiplicité maximale `1 038` signifie qu'un même couple `(formula_id, Z-ID)` a été observé 1 038 fois. Cette fréquence n'est ni une importance, ni un rang, ni un score, ni une preuve.

S4 ne modifie aucune formule, aucun registre de formules, aucun résultat Z, aucune route S3, aucune valeur ou aucun état de validation.

## Statut final

`LIVE_VALIDATED_SHADOW` — S4 actif et validé opérationnellement comme index read-only des résultats par formule exacte.

Prochaine vertèbre officielle : `S5 — Index rapide`.
