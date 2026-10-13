# ASTRA CHECKPOINT — Brutus T9 Stability

Date: 2026-10-13

## Position exacte dans Colonne 37

Parcours officiel :

`... T7 Calcul → T8 Contre-test → T9 Stabilité → T10 Replay ...`

T9 est la vertèbre 16/33. Ce changement ne réordonne pas le parcours.

## Baseline vérifiée avant T9

- dépôt : `Topbrutus/Antmux`
- base Git : `e2b3e2f7784bd3febebb60b52914ffa57f764136`
- T8 : `LIVE_VALIDATED_SHADOW`
- dashboard POST-T8 SHA-256 : `8a294e39869babd68ff7c5456afbbd5d740ca44aec360e60a0f5bd8a1335e94e`
- T8 module SHA-256 : `a93bd6cd9aaaf0fe832604de9e390e6d69de7dfb8b853e558d8c9955761cce9e`
- T8 conserve 0 autorité moteur et 0 promotion de preuve.

## Rôle de T9

T9 mesure uniquement la stabilité sous répétition des sorties déjà acceptées `PASS` par T8.

Clé de répétition :

`formula_id + source_value`

Signature sémantique comparée :

`output_value + validation_state`

Comportement :

1. première sortie T8 PASS pour une clé : `BASELINE` ;
2. même clé + même signature : `STABLE_REPEAT` ;
3. même clé + signature différente : `DRIFT` ;
4. T8 `FAIL` ou `LIMITED` : observation enregistrée comme amont non admissible, jamais transformée en stabilité.

T9 ne refait pas le contre-test T8 et ne remplace pas T8.

## Mesure principale

`stability_rate = stable_repeats / repeat_observations`

Cette mesure est opérationnelle. Elle ne constitue pas une preuve scientifique générale.

## Bornage mémoire

- baselines par défaut : `32 768`
- plafond dur : `131 072`
- éviction : `LRU` — baseline la moins récemment utilisée
- `eviction_policy = LRU` et compteur `evictions` exposés dans le statut

Le bornage évite qu'une vertèbre shadow accumule une mémoire non bornée.

## Garde-fous

T9 déclare explicitement :

- `authority = SHADOW_ONLY`
- `source_of_truth = T8_PASS_CALLBACK`
- `requires_t8_pass = true`
- `scientific_proof_claim = false`
- `validation_state_mutated = false`
- `controls_routing = false`
- `controls_scheduling = false`
- `controls_calculation = false`
- `compute_skips = 0`
- `value_mutated = false`
- `proof_promotion = false`

T9 ne doit pas écrire `ValidationState`, sélectionner une formule, modifier le Papillon, router, scheduler, sauter un calcul ou promouvoir une preuve.

## Tests ciblés prévus

1. répétitions identiques → `STABLE_REPEAT` ;
2. corruption de la sortie répétée → `DRIFT` ;
3. T8 FAIL/LIMITED → non admissible à la stabilité ;
4. baselines bornées avec éviction LRU mesurée ;
5. callback dashboard : delta T8 = delta T9 ;
6. T8 inchangé par le patch T9.

## Déploiement prévu

Workflow : `.github/workflows/deploy-brotoculateur-t9-vps.yml`

Séquence :

1. audit VPS non mutant ;
2. exiger état exact `PRE_T9` ;
3. copier le package live dans un stage ;
4. appliquer le patch seulement au stage ;
5. compiler et exécuter les tests T9 sur cette copie exacte ;
6. save/pause officiel ;
7. backup dashboard/T8/T9/statut/drop-in ;
8. appliquer exactement les fichiers du stage ;
9. restart ;
10. canary live ;
11. rollback automatique si dérive ;
12. audit indépendant POST_T9 ;
13. checkpoint GitHub avec hashes et mesures live.

Le canary exige :

- T8 reste activé et `SHADOW_ONLY` ;
- delta T9 = delta T8 ;
- `upstream_fail = 0` ;
- `upstream_limited = 0` ;
- `drifts = 0` ;
- si des répétitions sont observées, `stability_rate = 1.0` ;
- aucun worker error ;
- aucune autorité moteur T9.

## Statut avant déploiement

READY_FOR_PR — T9 n'est pas encore déployé live au moment de cette section.

## Validation live VPS — 2026-10-13

### PR et base

- PR T9 : `#290`
- merge commit : `556096940b5fd56b6581f6ea5f49183434286959`
- mode : `SHADOW_ONLY`

### Audit PRE_T9 non mutant

Workflow : `38381245471`

État observé avant mutation :

- source : `PRE_T9`
- moteur : `RUNNING`
- processed_packets : `276 997`
- cristaux : `1 789 636`
- T8 observations : `1 596 187`
- T8 PASS : `1 596 187`
- T8 FAIL : `0`
- T8 LIMITED : `0`
- T9 module : absent
- dashboard SHA-256 : `8a294e39869babd68ff7c5456afbbd5d740ca44aec360e60a0f5bd8a1335e94e`
- disque root : `59%`
- audit : `PASS`

### Tests sur copie exacte et canary

Workflow : `38381319702`

Le package live a d'abord été copié dans un stage temporaire. T9 a été appliqué uniquement à cette copie, puis les tests suivants ont passé avant mutation live :

- répétition identique : `PASS`, stabilité `1.0`
- dérive volontaire de sortie : `DRIFT` détecté
- gate T8 FAIL/LIMITED : `PASS`
- bornage baseline + LRU : `PASS`
- callback T8 ↔ T9 : lockstep `PASS`
- suite ciblée T9 : `PASS`

Hashes du stage exact :

- dashboard POST_T9 SHA-256 : `c8e4e06b74d7028f6db233d21cb630a93f9f8265e287cad58916e43ffdf8a34d`
- T8 module SHA-256 inchangé : `a93bd6cd9aaaf0fe832604de9e390e6d69de7dfb8b853e558d8c9955761cce9e`
- T9 module SHA-256 : `c0e0309dfe6d571c1d786010f72bc6f8bf3ccdada1f5fa960ab6f428e3640dd1`
- backup : `brotoculateur/backups/t9-20261013T100852Z`

Premier battement canary live :

- état : `RUNNING`
- delta T8 : `5`
- delta T9 : `5`
- observations T9 : `5`
- baselines : `5`
- répétitions : `0`
- drifts : `0`
- disque root : `59%`
- workflow : `PASS`

À ce premier battement, `stability_rate = 0.0` parce qu'aucune répétition n'avait encore été observée ; il ne s'agissait donc pas d'une mesure négative de stabilité.

### Audit indépendant POST_T9

Workflow : `38381409128`

État observé :

- source : `POST_T9`
- moteur : `RUNNING`
- processed_packets : `5 508`
- cristaux : `1 790 467`
- T8 observations : `30 966`
- T8 PASS : `30 966`
- T8 FAIL : `0`
- T8 LIMITED : `0`
- T9 observations : `30 966`
- T9 répétitions : `30 393`
- T9 répétitions stables : `30 393`
- T9 drifts : `0`
- stabilité observée sur répétitions : `30 393 / 30 393 = 1.0`
- dashboard SHA-256 : `c8e4e06b74d7028f6db233d21cb630a93f9f8265e287cad58916e43ffdf8a34d`
- T9 module SHA-256 : `c0e0309dfe6d571c1d786010f72bc6f8bf3ccdada1f5fa960ab6f428e3640dd1`
- disque root : `59%`
- audit : `PASS`

## Interprétation

T9 a démontré le bon fonctionnement opérationnel de sa mesure de stabilité sous répétition dans la configuration live observée : les `30 393` répétitions admissibles ont reproduit la même signature sémantique et aucun drift n'a été observé dans cette fenêtre.

Cela ne constitue pas une preuve scientifique générale de stabilité universelle. T9 reste une vertèbre de télémétrie `SHADOW_ONLY`, sans autorité moteur, sans mutation de `ValidationState`, sans routage, sans scheduling, sans compute skip et sans promotion de preuve.

## Statut final

`LIVE_VALIDATED_SHADOW` — T9 actif et validé opérationnellement. Prochaine vertèbre officielle : `T10 — Replay`.
