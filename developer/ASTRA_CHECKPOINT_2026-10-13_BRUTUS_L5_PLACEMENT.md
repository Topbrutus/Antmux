# ASTRA CHECKPOINT — Brutus L5 Placement

Date: 2026-10-13

Position officielle : `L4 Canon → L5 Placement → S1 Agrégateur`.

## Contrat source

Le prototype `laboratoire/brutus-colonne-37/brutus37.py` représente L5_PLACEMENT par le littéral :

`HOT`

L5 v1 respecte cette source sans inventer WARM/COLD ni de signification physique.

Après un canon technique L4 valide :

`placement = HOT`

Le même `canonical_z` est conservé. L5 ne crée aucune nouvelle identité.

`HOT` est une **classe logique de placement**. Ce n'est ni une température physique, ni une priorité CPU, ni un niveau de stockage, ni un niveau de preuve.

Les observations L4 bloquées restent bloquées et ne reçoivent aucun placement artificiel.

## Garde-fous

- `authority = SHADOW_ONLY`
- `prototype_placement_literal = HOT`
- `hot_is_logical_class = true`
- `physical_temperature_claim = false`
- `priority_claim = false`
- `storage_tier_claim = false`
- `canonical_z_is_output_z_id = true`
- `creates_new_identity = false`
- `places_both_l4_reference_sides = true`
- `s1_aggregator_input = true`
- aucun score ajouté
- aucun nouveau seuil
- aucun accept/reject
- aucune mutation ValidationState
- aucun routage/scheduling/calcul
- aucune réservation de ressources
- aucun replay exécuté
- aucune promotion de preuve

## Code

PR #307 — merge `920134ebb13a3321dd90aeac2a134ce54340b113`.

L5 module SHA-256 :

`cd1d0fa824ddf753c5471d7c8c2d04211f364a3b411ae55a57dc25a653e0e55d`

Dashboard POST-L5 SHA-256 :

`f2854516dcff8ff606870c101f6517fda091bf24fb3d9273d4891c59c2533192`

## PRE_L5 non mutant

Workflow `38391698945` : `PASS`.

- source : `PRE_L5`
- moteur : `RUNNING`
- processed_packets : `63 670`
- cristaux : `1 858 731`
- L4 observations : `366 555`
- L4 canonical_records : `158 620`
- L4 bloquées L3 : `207 935`
- L4 bloquées Z-ID : `0`
- L4 canonical_z uniques : `1 378`
- L5 absent
- disque root : `60%`

La baseline montre pourquoi L5 doit séparer observation et placement : toutes les observations L4 ne sont pas canoniques. Le contrat appliqué est :

`L5 observations = L4 observations`

`L5 placed = L4 canonical_records`

`L5 blocked_l4_other = L4 blocked_l3_other + L4 blocked_missing_z`

`L5 unique_placed_z = L4 unique_canonical_z`

## Canary exact-copy

Workflow `38391769464` : `PASS`.

Avant mutation live, le package VPS a été copié dans un stage exact et les tests suivants ont passé :

- littéral `HOT` : PASS
- même Z sur les deux côtés L4 → même identité placée : PASS
- résultat L4 invalide → blocage : PASS
- Z-ID absent → blocage : PASS
- aucune fausse revendication thermique/prioritaire/stockage : PASS
- aucune promotion de preuve : PASS
- callback T8→L5 lockstep `17/17/17/17/17/17/17/17/17/17` : PASS
- répétitions du même résultat : `17 placements`, `1 Z unique`
- côtés contrôlés : `16 AT_OR_ABOVE`, `1 BELOW`

Hashes stage :

- L5 : `cd1d0fa824ddf753c5471d7c8c2d04211f364a3b411ae55a57dc25a653e0e55d`
- dashboard POST-L5 : `f2854516dcff8ff606870c101f6517fda091bf24fb3d9273d4891c59c2533192`

Backup :

`brotoculateur/backups/l5-20261013T114005Z`

Premier battement live :

- moteur : `RUNNING`
- L4 observations : `302`
- L4 canonical_records : `302`
- L5 observations : `302`
- L5 placements : `302`
- Z placés uniques : `51`
- placement_classes : `HOT=302`
- côté `AT_OR_ABOVE_REFERENCE` : `220`
- côté `BELOW_REFERENCE` : `82`
- canary : `PASS`

## POST_L5 indépendant

Workflow `38391850771` : `PASS`.

- source : `POST_L5`
- moteur : `RUNNING`
- processed_packets : `3 931`
- cristaux : `1 859 631`
- L4 observations : `21 840`
- L4 canonical_records : `21 840`
- L4 bloquées L3 : `0`
- L4 bloquées Z-ID : `0`
- L4 canonical_z uniques : `292`
- L5 observations : `21 840`
- L5 placements : `21 840`
- L5 Z placés uniques : `292`
- disque root : `60%`
- audit : `PASS`

L'audit vérifie aussi que `HOT` reste une classe logique seulement, qu'aucune identité n'est créée, que S1 Agrégateur est le prochain consommateur et qu'aucune promotion de preuve n'a lieu.

## Interprétation

L5 est validé comme **placement logique HOT** des canons techniques L4 admissibles.

Un placement `HOT` signifie ici : « ce canonical_z technique est placé dans la classe logique HOT prévue par le prototype pour être transmis à S1 Agrégateur ».

Il ne signifie pas : matière chaude, priorité machine, mémoire hot-tier, importance scientifique, acceptation, preuve, canon scientifique ou vérité universelle.

La grande fenêtre PRE_L5 contenait `207 935` observations L4 bloquées. Le garde-fou L5 les laisse explicitement hors placement. Le canary et le POST, après redémarrage, ont observé une fenêtre où toutes les sorties L4 étaient canoniques et donc toutes placées HOT.

## Statut final

`LIVE_VALIDATED_SHADOW` — L5 actif et validé opérationnellement.

Prochaine vertèbre officielle : `S1 — Agrégateur`.
