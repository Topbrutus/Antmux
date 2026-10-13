# ASTRA CHECKPOINT — Brutus L4 Canon

Date: 2026-10-13

Position officielle : `L3 Press → L4 Canon → L5 Placement`.

## Contrat source

Le prototype `laboratoire/brutus-colonne-37/brutus37.py` représente :

- `L3_PRESS` par `{ "dust_key": z_stamp.z_id }` ;
- `L4_CANON` par `{ "canonical_z": z_stamp.z_id }` ;
- `L5_PLACEMENT` immédiatement après.

L4 v1 respecte cette séparation : il enregistre comme identité canonique **technique** exactement le Z-ID de sortie déjà existant après une pression L3 réussie.

Formule de contrat :

`canonical_z = out.z_id`

L4 ne crée aucune nouvelle identité. Il ne transforme pas un Z-ID en preuve scientifique, ne modifie aucun `ValidationState`, n'accepte/rejette aucun candidat et ne promeut aucune preuve.

Les deux côtés de la référence L2 restent admissibles au canon technique lorsque L3 les a pressés.

## Garde-fous

- `authority = SHADOW_ONLY`
- `canonical_z_is_output_z_id = true`
- `creates_new_identity = false`
- `records_both_l3_reference_sides = true`
- `technical_identity_canon = true`
- `scientific_canon_claim = false`
- `canonicalizes_scientific_proof = false`
- `l5_placement_input = true`
- aucun score ajouté
- aucun nouveau seuil
- aucun accept/reject
- aucune mutation ValidationState
- aucun routage/scheduling/calcul
- aucun replay exécuté
- aucune promotion de preuve

## Code

PR #304 — merge `78230829724625dd5e51a7907ec2abd930b8957c`.

Correction du garde-fou d'audit : PR #305 — merge `9d6f6653779f8569ffd3eafdbe39031a07342011`.

L4 module SHA-256 :

`9f8ff4d83cec6721eefe0a04bfd333861d47e7e10b17a85dec2dcaf1b9dc336d`

Dashboard POST-L4 SHA-256 :

`4476ae0d83542226a1c37ab1b069a11a59d106f8e8ee0807b697ddc9e0f67bb0`

## Première tentative PRE_L4 — garde-fou utile

Workflow `38390133247` : `FAIL` avant toute mutation VPS.

Le workflow avait imposé à tort :

`L3 pressed == L3 observations`

La longue fenêtre L3 réelle montrait qu'une partie des observations était bloquée pour Z-ID manquant. Le workflow a donc correctement refusé d'aller plus loin.

Aucun outil L4 n'a été staged vers le moteur et aucune mutation live n'a eu lieu pendant ce run.

La correction PR #305 a remplacé l'invariant trop strict par la comptabilité exacte :

`L3 observations = pressed + blocked_l2_other + blocked_missing_z`

et, après L4 :

`L4 observations = L3 observations`

`L4 canonical_records = L3 pressed`

`L4 blocked_l3_other = L3 blocked_l2_other + L3 blocked_missing_z`

`L4 unique_canonical_z = L3 unique_dust_keys`

## PRE_L4 corrigé

Workflow `38390357147` : `PASS`.

- source : `PRE_L4`
- moteur : `RUNNING`
- processed_packets : `52 876`
- cristaux : `1 850 685`
- L3 observations : `303 189`
- L3 pressées : `155 726`
- L3 bloquées L2 : `0`
- L3 bloquées Z-ID manquant : `147 463`
- L3 dust_keys uniques : `1 352`
- L4 absent
- disque root : `60%`

Interprétation : les observations non pressées provenaient du Z-ID manquant, pas d'un rejet L2. L4 ne doit pas inventer un canon pour ces observations.

## Canary exact-copy

Workflow `38390416416` : `PASS`.

Avant mutation live, le package VPS a été copié dans un stage exact et les tests suivants ont passé :

- `canonical_z == output.z_id` : PASS
- même Z sur les deux côtés L3 → même `canonical_z` : PASS
- Z-ID absent → blocage : PASS
- résultat L3 invalide → blocage : PASS
- aucun canon scientifique / aucune promotion de preuve : PASS
- callback T8→L4 lockstep `17/17/17/17/17/17/17/17/17` : PASS
- répétitions du même résultat : `17 canonical_records`, `1 canonical_z unique`
- côtés contrôlés : `16 AT_OR_ABOVE`, `1 BELOW`

Hashes stage :

- L4 : `9f8ff4d83cec6721eefe0a04bfd333861d47e7e10b17a85dec2dcaf1b9dc336d`
- dashboard POST-L4 : `4476ae0d83542226a1c37ab1b069a11a59d106f8e8ee0807b697ddc9e0f67bb0`

Backup :

`brotoculateur/backups/l4-20261013T112823Z`

Premier battement live :

- moteur : `RUNNING`
- L3 observations : `290`
- L3 pressées : `290`
- L3 bloquées L2 : `0`
- L4 observations : `290`
- L4 canonical_records : `290`
- L4 bloquées L3 : `0`
- canonical_z uniques : `49`
- côté `AT_OR_ABOVE_REFERENCE` : `214`
- côté `BELOW_REFERENCE` : `76`
- canary : `PASS`

## POST_L4 indépendant

Workflow `38390480672` : `PASS`.

- source : `POST_L4`
- moteur : `RUNNING`
- processed_packets : `3 601`
- cristaux : `1 851 507`
- L3 observations : `19 729`
- L3 pressées : `19 729`
- L3 bloquées L2 : `0`
- L3 Z-ID manquant : `0`
- L3 dust_keys uniques : `242`
- L4 observations : `19 729`
- L4 canonical_records : `19 729`
- L4 bloquées L3 : `0`
- L4 Z-ID manquant : `0`
- L4 canonical_z uniques : `242`
- disque root : `60%`
- audit : `PASS`

## Interprétation

L4 est validé comme **canon technique d'identité Z**, pas comme canon scientifique.

Un `canonical_z` signifie ici : « identité Z de sortie déjà existante, pressée avec succès par L3 et enregistrée comme référence canonique technique pour la suite de la colonne ».

Il ne signifie pas : preuve scientifique, relation mathématique démontrée, validation institutionnelle, vérité canonique universelle ou promotion automatique de cristal.

Le premier échec PRE_L4 fait partie de la preuve : le garde-fou a bloqué une hypothèse trop stricte avant toute mutation, puis l'invariant a été corrigé pour refléter la réalité mesurée du pipeline.

## Statut final

`LIVE_VALIDATED_SHADOW` — L4 actif et validé opérationnellement.

Prochaine vertèbre officielle : `L5 — Placement`.
