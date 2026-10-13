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

## Tests ciblés prévus

1. seuils exacts de la politique `8/6/4/2/1` ;
2. T8 FAIL/LIMITED → recommandation bloquée ;
3. T9 DRIFT → recommandation bloquée ;
4. clés bornées + éviction LRU ;
5. callback dashboard : delta T8 = delta T9 = delta T10 ;
6. T10 ne lance ni ne schedule de replay ;
7. T8 et T9 inchangés par le patch T10.

## Déploiement prévu

Workflow : `.github/workflows/deploy-brotoculateur-t10-vps.yml`

Séquence :

1. audit VPS non mutant ;
2. exiger état exact `PRE_T10` ;
3. copier le package live dans un stage ;
4. appliquer le patch seulement au stage ;
5. compiler et exécuter les tests T10 sur cette copie exacte ;
6. save/pause officiel ;
7. backup dashboard/T8/T9/T10/statut/drop-in ;
8. appliquer exactement dashboard + T10 du stage ;
9. restart ;
10. canary live ;
11. rollback automatique si dérive ;
12. audit indépendant POST_T10 ;
13. checkpoint GitHub avec hashes et mesures live.

## Statut avant déploiement

`READY_FOR_PR` — T10 n'est pas encore déployé live au moment de cette section.
