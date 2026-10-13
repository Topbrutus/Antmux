# ASTRA CHECKPOINT — Brutus T10 Replay

Date: 2026-10-13

## Position exacte dans Colonne 37

Parcours officiel :

`... T8 Contre-test → T9 Stabilité → T10 Replay → T11 Budget → T12 Candidat ...`

T10 est la vertèbre 17/33. Ce changement ne réordonne pas le parcours.

## Baseline vérifiée avant T10

- dépôt : `Topbrutus/Antmux`
- base Git : `3dfb55ea8377a1edad646db8a7a3635ad39010ec`
- T9 : `LIVE_VALIDATED_SHADOW`
- dashboard POST-T9 SHA-256 : `c8e4e06b74d7028f6db233d21cb630a93f9f8265e287cad58916e43ffdf8a34d`
- T8 module SHA-256 : `a93bd6cd9aaaf0fe832604de9e390e6d69de7dfb8b853e558d8c9955761cce9e`
- T9 module SHA-256 : `c0e0309dfe6d571c1d786010f72bc6f8bf3ccdada1f5fa960ab6f428e3640dd1`
- T8/T9 conservent 0 autorité moteur et 0 promotion de preuve.

## Rôle officiel de T10

T10 répond uniquement à la question :

> Combien de recalculs sont mérités pour une clé admissible ?

T10 **ne lance pas** les recalculs et **ne les planifie pas**. La vertèbre suivante, T11 — Budget, doit arbitrer CPU, mémoire, stockage et temps avant toute future exécution.

La clé suivie reste celle de T9 :

`formula_id + source_value`

Admissibilité :

- T8 doit être `PASS` ;
- T9 doit être `BASELINE` ou `STABLE_REPEAT` ;
- T9 `DRIFT` bloque toute recommandation de replay ;
- T8 `FAIL`/`LIMITED` bloque toute recommandation de replay.

## Politique de mérite Replay

La règle vient du prototype Colonne 37 déjà présent dans `laboratoire/brutus-colonne-37/brutus37.py`, où `CrystalRecord.replay_budget` diminue quand le nombre d'observations augmente.

Règle portée dans T10 :

- observations `1–2` → `8` recalculs mérités ;
- observations `3–4` → `6` ;
- observations `5–8` → `4` ;
- observations `9–16` → `2` ;
- observations `17+` → `1`.

Interprétation : une clé peu observée mérite davantage de relecture potentielle ; une clé déjà répétée et stable en mérite moins.

Cette valeur est une **recommandation opérationnelle**, pas une autorisation de calcul et pas une preuve scientifique.

## Bornage mémoire

- clés par défaut : `32 768`
- plafond dur : `131 072`
- éviction : `LRU`
- compteur `evictions` exposé

## Garde-fous

T10 déclare explicitement :

- `authority = SHADOW_ONLY`
- `source_of_truth = T9_OUTCOME_CALLBACK`
- `requires_t8_pass = true`
- `requires_t9_non_drift = true`
- `executes_replay = false`
- `schedules_replay = false`
- `controls_budget = false`
- `t11_budget_required = true`
- `scientific_proof_claim = false`
- `validation_state_mutated = false`
- `controls_routing = false`
- `controls_scheduling = false`
- `controls_calculation = false`
- `compute_skips = 0`
- `value_mutated = false`
- `proof_promotion = false`

## Tests ciblés

1. seuils exacts de la politique `8/6/4/2/1` ;
2. T8 FAIL/LIMITED → recommandation bloquée ;
3. T9 DRIFT → recommandation bloquée ;
4. clés bornées + éviction LRU ;
5. callback dashboard : delta T8 = delta T9 = delta T10 ;
6. T10 ne lance ni ne schedule de replay ;
7. T8 et T9 inchangés par le patch T10.

## Déploiement gardé

Workflow : `.github/workflows/deploy-brotoculateur-t10-vps.yml`

Séquence appliquée :

1. audit VPS non mutant ;
2. état exact `PRE_T10` exigé ;
3. copie du package live dans un stage ;
4. patch appliqué seulement au stage ;
5. compilation + tests T10 sur cette copie exacte ;
6. save/pause officiel ;
7. backup dashboard/T8/T9/T10/statut/drop-in ;
8. application exacte dashboard + T10 du stage ;
9. restart ;
10. canary live ;
11. rollback automatique disponible ;
12. audit indépendant POST_T10 ;
13. checkpoint GitHub avec hashes et mesures live.

## Validation live VPS — 2026-10-13

### PR et base

- PR T10 : `#292`
- merge commit : `3c2122e99c0422eb279046508c3f8544046ec938`
- mode : `SHADOW_ONLY`

### Audit PRE_T10 non mutant

Workflow : `38382824393`

État observé avant mutation :

- source : `PRE_T10`
- moteur : `RUNNING`
- processed_packets : `113 366`
- cristaux : `1 802 681`
- T8 observations : `617 312`
- T8 FAIL : `0`
- T8 LIMITED : `0`
- T9 observations : `617 312`
- T9 répétitions : `613 867`
- T9 drifts : `0`
- T10 module : absent
- dashboard SHA-256 : `c8e4e06b74d7028f6db233d21cb630a93f9f8265e287cad58916e43ffdf8a34d`
- disque root : `59%`
- audit : `PASS`

### Tests sur copie exacte et canary

Workflow : `38382871423`

Le package live a été copié dans un stage temporaire. T10 a d'abord été appliqué uniquement à cette copie. Avant toute mutation live, les contrôles suivants ont passé :

- dépendance T8/T9 saine : `PASS`
- patch T10 : `PASS`
- politique de référence `8/6/4/2/1` : `PASS`
- gate T8 FAIL/LIMITED : `PASS`
- gate T9 DRIFT : `PASS`
- bornage des clés + LRU : `PASS`
- callback T8 ↔ T9 ↔ T10 : lockstep `17 / 17 / 17`, `PASS`
- suite ciblée T10 : `PASS`
- stage exact live : `PASS`

Hashes du stage exact :

- dashboard POST_T10 SHA-256 : `8b97522a6210f0c6ec2feaa1a3786bd00ffda5362aed9feee2c1966768bd61d4`
- T8 module SHA-256 inchangé : `a93bd6cd9aaaf0fe832604de9e390e6d69de7dfb8b853e558d8c9955761cce9e`
- T9 module SHA-256 inchangé : `c0e0309dfe6d571c1d786010f72bc6f8bf3ccdada1f5fa960ab6f428e3640dd1`
- T10 module SHA-256 : `9fe9b3bbb9a42c790d02e2d85638b2ea11e067750dc1cc5c6812b2c42f40a3be`
- backup : `brotoculateur/backups/t10-20261013T102222Z`

Premier battement canary live :

- état : `RUNNING`
- processed_packets : `2`
- T9 observations : `10`
- T10 observations : `10`
- T10 admissibles : `10`
- delta T9 : `10`
- delta T10 : `10`
- mérite replay courant total : `80`
- distribution de mérite : `8 → 10 clés`
- T10 bloqués par drift T9 : `0`
- disque root : `59%`
- workflow : `PASS`

Le mérite total `80` à ce premier battement signifie `10` clés encore dans le premier palier, chacune conseillée à `8`. Il ne signifie pas que `80` recalculs ont été exécutés : T10 n'exécute et ne planifie aucun replay.

### Audit indépendant POST_T10

Workflow : `38383001548`

Fenêtre runtime observée après redémarrage du service :

- source : `POST_T10`
- moteur : `RUNNING`
- processed_packets : `8 713`
- cristaux : `1 804 097`
- T8 observations : `49 168`
- T8 FAIL : `0`
- T8 LIMITED : `0`
- T9 observations : `49 168`
- T9 répétitions : `48 107`
- T9 drifts : `0`
- T10 mode : `BRUTUS_T10_REPLAY_V1`
- T10 activé : `true`
- T10 observations : `49 168`
- T10 admissibles : `49 168`
- mérite replay courant total : `5 335`
- gates T8 FAIL/LIMITED et T9 DRIFT : vérifiés sans blocage par l'audit
- dashboard SHA-256 : `8b97522a6210f0c6ec2feaa1a3786bd00ffda5362aed9feee2c1966768bd61d4`
- T10 module SHA-256 : `9fe9b3bbb9a42c790d02e2d85638b2ea11e067750dc1cc5c6812b2c42f40a3be`
- disque root : `59%`
- audit : `PASS`

## Interprétation

T10 a démontré le bon fonctionnement opérationnel de sa politique de mérite Replay dans la configuration live observée. Les sorties T8/T9 admissibles sont suivies en lockstep, les drifts T9 sont explicitement interdits, et le mérite décroît selon la règle de référence `8/6/4/2/1`.

La valeur de mérite T10 reste **strictement consultative**. Aucun replay n'est exécuté ou planifié par T10, aucun budget n'est consommé, aucune autorité moteur n'est accordée, aucun `ValidationState` n'est modifié et aucune preuve scientifique n'est promue.

T11 — Budget reste la prochaine porte obligatoire avant toute future décision d'exécution de replay.

## Statut final

`LIVE_VALIDATED_SHADOW` — T10 actif et validé opérationnellement. Prochaine vertèbre officielle : `T11 — Budget`.
