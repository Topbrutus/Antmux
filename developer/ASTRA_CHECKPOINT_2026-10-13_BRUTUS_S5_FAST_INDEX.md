# ASTRA CHECKPOINT — Brutus S5 Index rapide

Date: 2026-10-13

Position officielle : `S4 Index formule → S5 Index rapide → Co1 Archive`.

## Contrat source

Le prototype `laboratoire/brutus-colonne-37/brutus37.py` représente S5 par `bucket37` et l'ancien `FastLibrary37` utilise 37 voies déterministes pour accélérer l'accès tout en conservant la clé d'identité complète.

Le runtime live possède déjà deux primitives validées :

- `c2_fingerprint(out)` : empreinte structurelle C2 canonique complète;
- `C3Library37.bucket_for(fingerprint)` : partition déterministe 37 voies de C3.

S5 v1 réutilise exactement ces primitives :

`fp = c2_fingerprint(out)`

`bucket37 = C3Library37.bucket_for(fp)`

La clé d'identité de lookup reste l'empreinte C2 complète. `bucket37` n'est qu'un accélérateur d'accès.

S5 indexe, dans la voie 37 correspondante, les couples observés `(formula_id, z_id)` pour une empreinte C2 exacte.

## Frontières et garde-fous

- `authority = SHADOW_ONLY`
- `prototype_measurement_bucket37 = true`
- `uses_existing_c2_fingerprint = true`
- `uses_exact_c3_bucket_function = true`
- `full_c2_fingerprint_is_identity = true`
- `bucket37_is_routing_only = true`
- `query_before_compute = false`
- `compute_skips = 0`
- `persistent = false`
- capacité bornée; aucun évincement silencieux
- `BLOCKED_CAPACITY` plutôt qu'une suppression lorsqu'une limite est atteinte
- `creates_formula = false`
- `executes_formula = false`
- `selects_formula = false`
- `ranks_formula = false`
- `formula_registry_mutated = false`
- `s4_formula_index_mutated = false`
- `z_identity_preserved = true`
- `co1_archive_input = true`
- aucune mutation ValidationState
- aucun contrôle du routage, scheduling ou calcul
- aucune réservation de ressources
- aucun replay exécuté ou planifié
- aucune mutation de valeur
- aucune promotion de preuve
- aucune revendication de preuve scientifique

S5 ne remplace pas C3. C3 reste la bibliothèque d'empreintes C2; S5 réutilise sa partition 37 comme index d'accès de fin de chaîne pour les résultats déjà admis par S4.

## Code

PR #317 — merge :

`495da3f277f6c85fcf2f08d95ee2cfc4789a89ab`

S5 module SHA-256 :

`de885d1f4748d236a0050cbea87560cf26fc74a08a95a8a02b119241ce6b0334`

Dashboard POST-S5 SHA-256 :

`82b57cca014d6eee3d9e039e6f483317f248caddef8d21b37cbf226ce27903af`

Upstream conservé :

- S4 : `3c9431bbdf7fc0be33d1eae38455d1584ec87b250b4fe09e0bc849cbc117ebc9`
- C3 : `b7970583e688488d0f9fd8a90838d9163d00b08b7e6afedd499434e79a06c434`

## PRE_S5 non mutant

Workflow `38398633100` : `PASS`.

- source : `PRE_S5`
- dashboard : `5161995d53af3bbefa39aec6fd6a69b6aaa7af10d1295eef5d61fc133cb15f5e`
- S5 : absent
- moteur : `RUNNING`
- processed_packets : `56 323`
- cristaux : `1 897 777`
- C3 bucket_count : `37`
- S4 observations : `326 002`
- S4 indexées : `190 059`
- S4 bloquées S3 : `135 943`
- S4 missing formula : `0`
- S4 missing Z : `0`
- S4 formula mismatch : `0`
- S4 Z résultats uniques : `1 429`
- disque root : `60%`
- `S5_AUDIT_ONLY=PASS`

Comptabilité attendue :

`S5 observations = S4 observations`

`S5 indexed = S4 indexed`

`S5 blocked_s4_other = total blockers S4`

`S5 unique_z_indexed = S4 unique_result_z`

## Canary exact-copy

Workflow `38398700755` : `PASS`.

Avant mutation live, le package VPS a été copié et patché dans un stage exact sous garde des SHA.

Tests :

- C2 exact + bucket C3 exact + lookup : `PASS`
  - exemple bucket : `34`
  - empreinte : `C2-6b0913f869e0e10f9ee7a6abc52c392ec0b84405ee26c8744fa293ac3234c47e`
  - Z : `Z-f812c59b0901cb3ed4c3edd77b3f759c`
- même Z atteint par plusieurs formules/structures conservé : `PASS`
  - Z : `Z-016f078a8f71cbe65181c1ca6ae3fe63`
  - deux empreintes C2 distinctes routées vers buckets `28` et `34`
- gardes d'entrée : `PASS`
- capacité contrôlée : `37` acceptées / `12` rejetées sur limite test `37`
- aucune autorité d'exécution : `PASS`
- callback T8→S5 lockstep : `17` observations sur chacun des 15 modules : `PASS`
- `S5_FAST_INDEX=PASS`
- `S5_EXACT_LIVE_STAGE=PASS`

Backup :

`brotoculateur/backups/s5-20261013T123803Z`

Premier battement live :

- moteur : `RUNNING`
- S4 observations : `278`
- S4 indexées : `278`
- S5 observations : `278`
- S5 indexées : `278`
- buckets occupés : `36/37`
- empreintes C2 uniques : `182`
- entrées rapides uniques : `182`
- Z uniques : `49`
- Z multi-bucket : `23`
- multiplicité max d'une entrée rapide : `6`
- `S5_LIVE_VERIFY=PASS`
- `S5_WORKFLOW=PASS`

## POST_S5 indépendant

Workflow `38398781264` : `PASS`.

- source : `POST_S5`
- dashboard : `82b57cca014d6eee3d9e039e6f483317f248caddef8d21b37cbf226ce27903af`
- S5 : `de885d1f4748d236a0050cbea87560cf26fc74a08a95a8a02b119241ce6b0334`
- moteur : `RUNNING`
- processed_packets : `3 221`
- cristaux : `1 898 468`
- C3 bucket_count : `37`
- S4 observations : `17 553`
- S4 indexées : `17 553`
- tous les blockers S4 : `0`
- S4 Z résultats uniques : `248`
- S5 observations : `17 553`
- S5 indexées : `17 553`
- buckets occupés : `37/37`
- empreintes C2 uniques : `4 379`
- entrées rapides uniques : `4 379`
- Z uniques : `248`
- capacity_rejections : `0`
- multiplicité max d'une entrée rapide : `21`
- disque root : `60%`
- `S5_AUDIT_ONLY=PASS`

## Interprétation

Dans la fenêtre POST_S5, les `17 553` observations S4 ont toutes été vues par S5 et les `17 553` résultats S4 valides ont tous été indexés.

Les `4 379` empreintes C2 uniques décrivent des états structurels exacts déjà calculés. Elles ne sont pas 4 379 découvertes scientifiques.

Les `248` Z uniques correspondent exactement aux `248` Z résultats uniques de S4 dans la même fenêtre. S5 n'a donc ni perdu ni créé une identité Z.

Les `37/37` buckets occupés signifient que la partition d'accès 37 voies a été entièrement utilisée dans cette fenêtre. Cela ne constitue pas une propriété mathématique universelle du système.

La multiplicité maximale `21` signifie qu'une même entrée rapide exacte `(C2, formula_id, z_id)` a été observée 21 fois dans cette fenêtre. Ce nombre n'est ni un score, ni un rang, ni un niveau de preuve.

Le premier battement live avait observé `23` Z multi-bucket. Cela est possible parce qu'un même Z technique peut être atteint sous plusieurs structures C2 exactes distinctes. Les buckets indexent les empreintes C2, pas l'identité Z elle-même.

S5 reste non persistant en v1 et n'effectue aucun lookup avant calcul. La persistance/archivage appartient à la couche suivante et ne doit pas être attribuée rétroactivement à S5.

## Statut final

`LIVE_VALIDATED_SHADOW` — S5 actif et validé comme index rapide read-only 37 voies basé sur les primitives C2/C3 existantes.

Les 29 premières vertèbres de la Colonne 37 sont maintenant complétées.

Prochaine vertèbre officielle : `Co1 — Archive`.
