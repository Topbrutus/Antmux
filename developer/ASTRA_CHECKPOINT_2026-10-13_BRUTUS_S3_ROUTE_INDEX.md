# ASTRA CHECKPOINT — Brutus S3 Index route

Date: 2026-10-13

Position officielle : `S2 Index lignée → S3 Index route → S4 Index formule`.

## Contrat source

Le prototype `laboratoire/brutus-colonne-37/brutus37.py` place S3 après S2 et mesure `route_signature` à S3.

La vitrine du prototype décrit S3 ainsi :

`Indexe les parcours Papillon.`

Le runtime live possède déjà la fonction exacte de shard Papillon144, exposée en lecture par `Papillon144.shard_index(formula_id, value)` et déjà utilisée par T6.

Pour éviter de créer un deuxième routeur ou un deuxième calcul de route concurrent, S3 live v1 réutilise cette source de vérité et le `branch_path` déjà émis par le packet :

`route_ref = P{papillon_shard:03d}|{branch_path}`

avec :

- `papillon_shard = Papillon144.shard_index(formula_id, source.value)`
- `branch_path = out.branch_path`
- `source.branch_path == out.branch_path` exigé; sinon S3 bloque au lieu d'inventer une route.

Cette adaptation n'essaie volontairement pas de reproduire un nouveau `Pxxx/Vxx` indépendant du Papillon live. Elle indexe les parcours effectivement observables par les primitives déjà présentes dans le runtime.

## Garde-fous

- `authority = SHADOW_ONLY`
- `prototype_measurement_route_signature = true`
- `indexes_papillon_paths = true`
- `uses_existing_papillon_shard_function = true`
- `creates_parallel_router = false`
- `chooses_route = false`
- `applies_route = false`
- `actual_routes_applied = 0`
- `infers_hidden_path = false`
- `z_identity_preserved = true`
- `lineage_mutated = false`
- `formula_index_authority = false`
- `s4_formula_index_input = true`
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

PR #313 — merge :

`ba301f365c0d8524d5e670b24ea298b89a4e3c84`

S3 module SHA-256 :

`35b76679778254e179dcb2df8b2415aa9634319dbc511408eb23bf544f4b9ca3`

Dashboard POST-S3 SHA-256 :

`b39265fedc454b0187d7ec3a2d2e29dba2840716590db52960b89b6300e3e3ea`

## PRE_S3 non mutant

Workflow `38395654075` : `PASS`.

- source : `PRE_S3`
- moteur : `RUNNING`
- processed_packets : `80 555`
- cristaux : `1 882 361`
- T6 shards touchés : `144`
- S2 observations : `463 284`
- S2 indexées : `160 349`
- S2 bloquées S1 : `302 935`
- S2 bloquées Z-ID : `0`
- S2 enfants Z uniques : `1 379`
- S3 absent
- disque root : `60%`

Comptabilité attendue :

`S3 observations = S2 observations`

`S3 indexed = S2 indexed`

`S3 blocked = S2 blocked`

`S3 unique_z_indexed = S2 unique_child_z`

## Canary exact-copy

Workflow `38395714786` : `PASS`.

Avant mutation live, le package VPS a été copié dans un stage exact. Tests exécutés :

- lecture du shard Papillon exact et déterministe : `PASS`
  - exemple contrôlé : shard `20`, route_ref `P020|ROOT/A`
- état Papillon avant/après lecture inchangé : `PASS`
- même Z observé par deux chemins différents → deux route_refs distincts : `PASS`
  - `P051|ROOT/A`
  - `P051|ROOT/B`
- blocage des entrées S2 non indexées : `PASS`
- blocage si Papillon indisponible : `PASS`
- blocage si `branch_path` dérive entre source et sortie : `PASS`
- aucune autorité de routage : `PASS`
- callback T8→S3 lockstep `17` sur chacun des 13 modules : `PASS`
- sur ces 17 répétitions contrôlées : une route unique, multiplicité `17`
- `S3_ROUTE_INDEX=PASS`
- `S3_EXACT_LIVE_STAGE=PASS`

Backup :

`brotoculateur/backups/s3-20261013T121341Z`

Premier battement live :

- moteur : `RUNNING`
- S2 observations : `217`
- S2 indexées : `217`
- S3 observations : `217`
- S3 indexées : `217`
- routes uniques : `179`
- shards Papillon touchés : `51`
- branch_paths uniques : `19`
- Z uniques indexés : `39`
- Z multi-route : `27`
- routes contenant plusieurs Z : `8`
- multiplicité max route_ref : `3`
- canary : `PASS`

## POST_S3 indépendant

Workflow `38395793825` : `PASS`.

- source : `POST_S3`
- dashboard SHA : `b39265fedc454b0187d7ec3a2d2e29dba2840716590db52960b89b6300e3e3ea`
- S3 SHA : `35b76679778254e179dcb2df8b2415aa9634319dbc511408eb23bf544f4b9ca3`
- moteur : `RUNNING`
- processed_packets : `3 133`
- cristaux : `1 883 005`
- T6 shards touchés dans son propre résumé courant : `126`
- S2 observations : `17 155`
- S2 indexées : `17 155`
- S2 blocages : `0`
- S2 enfants Z uniques : `234`
- S3 observations : `17 155`
- S3 indexées : `17 155`
- routes uniques : `4 695`
- shards Papillon touchés par S3 : `138`
- Z multi-route : `184`
- multiplicité max route_ref : `56`
- disque root : `60%`
- audit : `PASS`

### Note T6 / S3

`T6_SHARDS=126` et `S3_SHARDS_TOUCHED=138` ne sont pas censés être égaux.

T6 et S3 sont deux projections de télémétrie distinctes, à des points différents du parcours et avec leurs propres fenêtres/compteurs. Le contrat S3 exige uniquement que chaque route S3 utilise la fonction exacte `Papillon144.shard_index` et reste dans l'intervalle `0..143`; il n'exige pas l'égalité des compteurs agrégés T6 et S3.

## Interprétation

Dans la fenêtre POST_S3, S3 a indexé `17 155` observations en `4 695` route_refs distincts et a touché `138/144` shards Papillon.

`184` identités Z ont été observées par plus d'un route_ref. Cela décrit une diversité de parcours observée pour la même identité Z technique. Ce n'est pas une preuve scientifique, un score de valeur, une priorité, ni une commande de routage.

La multiplicité maximale `56` signifie qu'un même route_ref a été observé 56 fois dans cette fenêtre. Elle ne signifie ni importance ni niveau de preuve.

S3 ne modifie pas S2, la lignée Z, le Papillon, les formules, la valeur ou l'état de validation.

## Trace d'hygiène dépôt

Avant la création de la branche S3, un fichier vide `_noop` a été créé accidentellement sur `main`, puis supprimé immédiatement avant tout travail S3 ou toute mutation VPS :

- ajout accidentel : `99c9484fabfc7d7c9d4acd27e2252b9fc34f69c0`
- retrait : `72fadce071f30865483d689776f4924c705e0bd5`

Après retrait, l'arbre Git est revenu au même tree SHA que le checkpoint S2 (`eb929968f6367be7211a3695746b0b6a757ea33f`). Aucun fichier moteur ni état live n'a été modifié par cet incident. La branche S3 a ensuite été créée depuis le HEAD nettoyé.

## Statut final

`LIVE_VALIDATED_SHADOW` — S3 actif et validé opérationnellement comme index read-only des parcours Papillon observés.

Prochaine vertèbre officielle : `S4 — Index formule`.
