# ASTRA CHECKPOINT — Brutus L3 Press

Date: 2026-10-13

Position officielle : `L2 Seuil → L3 Press → L4 Canon`.

## Contrat source

Le prototype `laboratoire/brutus-colonne-37/brutus37.py` représente :

- `L2_THRESHOLD` par `{ "threshold": None }` ;
- `L3_PRESS` par `{ "dust_key": z_stamp.z_id }` ;
- `L4_CANON` par `{ "canonical_z": z_stamp.z_id }`.

L3 v1 respecte cette séparation : il ne crée pas un nouveau score ni une nouvelle identité. Il presse l'identité Z déjà présente sur la sortie en utilisant exactement `dust_key = out.z_id`.

Les deux côtés L2 restent pressables car L2 n'est pas une règle d'acceptation/rejet. L3 conserve seulement la relation au seuil d'ingénierie.

Un paquet sans Z-ID est bloqué au lieu de recevoir une identité inventée.

L3 ne canonise rien : L4 Canon reste la prochaine vertèbre.

## Garde-fous

- `authority = SHADOW_ONLY`
- `dust_key_is_output_z_id = true`
- `creates_new_identity = false`
- `presses_both_l2_reference_sides = true`
- `l4_canon_input = true`
- `canonizes = false`
- aucun score ajouté
- aucun nouveau seuil
- aucun accept/reject
- aucune mutation ValidationState
- aucun routage/scheduling/calcul
- aucun replay exécuté
- aucune promotion de preuve

## Code

PR #302, merge `062fde3f05b41b666ca77efca4c24f6c07e40970`.

L3 module SHA-256 : `373f2bf054ec595e72c1012228b3a39ec0279e9a2c8cefa9d7122c7e113fb42d`.

Dashboard POST-L3 SHA-256 : `b00131bb87a21ffb55baec337e809fcdf39c03d3498d63f1690beda43541ef84`.

## PRE_L3

Workflow `38389409683` PASS.

- source : `PRE_L3`
- moteur : `RUNNING`
- processed_packets : `45 992`
- cristaux : `1 844 061`
- L2 observations : `265 061`
- L2 au-dessus/égal : `260 939`
- L2 en dessous : `4 122`
- L3 absent
- disque root : `60%`

## Canary exact-copy

Workflow `38389456939` PASS.

Tests sur copie exacte :

- `dust_key == output.z_id` : PASS
- même Z sur les deux côtés L2 → même dust_key : PASS
- Z-ID absent → blocage : PASS
- résultat L2 invalide → blocage : PASS
- aucun canon/proof promotion : PASS
- callback T8→L3 lockstep `17/17/17/17/17/17/17/17` : PASS
- répétitions du même résultat : `17 pressions`, `1 dust_key unique`
- côtés contrôlés : `16 AT_OR_ABOVE`, `1 BELOW`

Hashes stage :

- L3 : `373f2bf054ec595e72c1012228b3a39ec0279e9a2c8cefa9d7122c7e113fb42d`
- dashboard POST-L3 : `b00131bb87a21ffb55baec337e809fcdf39c03d3498d63f1690beda43541ef84`

Backup : `brotoculateur/backups/l3-20261013T112001Z`.

Premier battement live :

- moteur : `RUNNING`
- L2 observations : `217`
- L3 observations : `217`
- L3 pressed : `217`
- dust_keys uniques : `39`
- côté `AT_OR_ABOVE_REFERENCE` : `158`
- côté `BELOW_REFERENCE` : `59`
- blocage L2 : `0`
- Z-ID manquant : `0`
- canary : `PASS`

## POST_L3 indépendant

Workflow `38389525502` PASS.

- source : `POST_L3`
- moteur : `RUNNING`
- processed_packets : `3 428`
- cristaux : `1 844 758`
- L2 observations : `18 726`
- L2 au-dessus/égal : `18 298`
- L2 en dessous : `428`
- L3 observations : `18 726`
- L3 pressed : `18 726`
- dust_keys uniques : `233`
- blocage L2 : `0`
- Z-ID manquant : `0`
- disque root : `60%`
- audit : `PASS`

## Interprétation

L3 est validé comme **presse d'identité Z**, pas comme seconde couche de score ou de décision. Une observation située sous la référence L2 reste pressable et conserve son Z-ID ; cela évite de transformer le seuil d'ingénierie en règle de rejet implicite.

Le nombre de `dust_keys uniques` mesure les identités Z distinctes observées dans la fenêtre runtime L3. Il ne constitue ni un nombre de preuves, ni un nombre de canons.

## Statut final

`LIVE_VALIDATED_SHADOW` — L3 actif et validé opérationnellement.

Prochaine vertèbre officielle : `L4 — Canon`.
