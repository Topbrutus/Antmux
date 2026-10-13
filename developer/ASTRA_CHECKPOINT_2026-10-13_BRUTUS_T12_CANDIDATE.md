# ASTRA CHECKPOINT — Brutus T12 Candidate

Date: 2026-10-13

## Position exacte dans Colonne 37

Parcours officiel :

`... T10 Replay → T11 Budget → T12 Candidat → L1 Score cristal → L2 Seuil ...`

T12 est la vertèbre 19/33. Ce changement ne réordonne pas le parcours.

## Source disponible

Le prototype fondateur `laboratoire/brutus-colonne-37/brutus37.py` définit explicitement `T12_CANDIDATE` immédiatement avant `L1_CRYSTAL_SCORE`, et sa mesure prototype est simplement `{candidate: true}`.

Aucune source inspectée ne définit pour T12 :

- un score ;
- un seuil ;
- une règle de preuve ;
- une règle de nouveauté scientifique ;
- une règle de canonisation ;
- une règle d'acceptation/rejet fondée sur le budget.

T12 v1 refuse donc d'inventer ces règles.

## Rôle T12 v1

T12 matérialise une **fiche candidat technique pré-score** lorsque T11 émet une sortie Budget reconnue.

Pour chaque candidat, il conserve :

- un identifiant déterministe `CAND-...` basé sur `formula_id + source.value + out.value` ;
- la classe Budget T11 : `FULL`, `PARTIAL` ou `ZERO` ;
- le nombre de replays demandé par T10 via T11 ;
- le nombre de replays conseillé par T11 ;
- la formule ;
- une clé source pseudonymisée ;
- le statut de matérialisation du candidat.

L'identifiant candidat est un identifiant technique T12. Il n'est pas déclaré équivalent à C2 et ne constitue pas une identité scientifique.

## Traitement des classes Budget

- `BUDGET_FULL_N` → `CANDIDATE_RECORDED_FULL_BUDGET`
- `BUDGET_PARTIAL_M_OF_N` → `CANDIDATE_RECORDED_PARTIAL_BUDGET`
- `BUDGET_ZERO_OF_N` → `CANDIDATE_RECORDED_ZERO_BUDGET`

Un budget zéro ne supprime pas silencieusement le candidat : T11 est un arbitre opérationnel de budget, pas un seuil scientifique. La classe `ZERO` est donc transmise à L1 comme contexte.

Une sortie T11 inconnue ou upstream-bloquée n'est pas matérialisée comme candidat et devient `BLOCKED_T11_OTHER`.

## Frontière avec L1 et L2

T12 ne score rien et n'applique aucun seuil.

- T12 = formation de la fiche candidat ;
- L1 = prochain instrument officiel autorisé à commencer un score cristal ;
- L2 = seuil, séparé de T12.

Cette séparation empêche T12 de devenir silencieusement une porte de promotion.

## Garde-fous

T12 déclare explicitement :

- `authority = SHADOW_ONLY`
- `source_of_truth = T11_BUDGET_OUTCOME_CALLBACK`
- `candidate_definition = TECHNICAL_PRE_SCORE_RECORD`
- `candidate_key_scope = FORMULA_SOURCE_OUTPUT_ONLY`
- `candidate_key_is_c2_fingerprint = false`
- `candidate_key_is_scientific_identity = false`
- `records_zero_budget_candidates = true`
- `l1_crystal_score_input = true`
- `assigns_score = false`
- `applies_threshold = false`
- `scientific_candidate_claim = false`
- `scientific_proof_claim = false`
- `validation_state_mutated = false`
- `canonizes = false`
- `promotes_proof = false`
- `controls_routing = false`
- `controls_scheduling = false`
- `controls_calculation = false`
- `reserves_resources = false`
- `executes_replay = false`
- `schedules_replay = false`
- `compute_skips = 0`
- `value_mutated = false`
- `proof_promotion = false`

## Tests ciblés

1. FULL/PARTIAL/ZERO produisent une fiche candidat ;
2. le même couple formule/source/sortie garde le même candidate_id même si le budget change ;
3. une sortie T11 inconnue est bloquée sans candidat ;
4. budget ZERO est conservé comme candidat avec contexte ;
5. T12 n'assigne aucun score ni seuil ;
6. aucune revendication scientifique ;
7. callback dashboard : delta T8 = T9 = T10 = T11 = T12 ;
8. aucune mutation de valeur, routage, scheduling, calcul, validation ou preuve.

## Déploiement gardé appliqué

Workflow : `.github/workflows/deploy-brotoculateur-t12-vps.yml`

Runner VPS versionné : `deploy/vps-t12/run_t12_vps.sh`

Séquence appliquée :

1. audit VPS non mutant ;
2. état exact `PRE_T12` exigé ;
3. copie du package live dans un stage ;
4. T12 appliqué seulement au stage ;
5. compilation et tests sur cette copie exacte ;
6. save/pause ;
7. backup dashboard/T8/T9/T10/T11/T12/statut/drop-in ;
8. application exacte dashboard + T12 du stage ;
9. restart ;
10. canary live ;
11. rollback automatique disponible ;
12. audit indépendant POST_T12 ;
13. checkpoint GitHub avec hashes et mesures live.

## Validation live VPS — 2026-10-13

### PR et base

- PR T12 : `#296`
- merge commit : `94774e878a9d5bbba57af55d2f4ad448854a177d`
- mode : `SHADOW_ONLY`
- T12 module SHA-256 : `582566a439ce1fdb9665237a81398f52476e4a85b715ee855d310ed7d407a4f9`

### Audit PRE_T12 non mutant

Workflow : `38386139502`

État observé :

- source : `PRE_T12`
- moteur : `RUNNING`
- processed_packets : `78 926`
- cristaux : `1 823 046`
- T8 observations : `454 510`
- T8 FAIL : `0`
- T8 LIMITED : `0`
- T9 observations : `454 510`
- T9 drifts : `0`
- T10 observations : `454 510`
- T11 observations : `454 510`
- T11 demande normalisée : `615 308`
- T11 conseil normalisé : `615 308`
- T11 coupé : `0`
- T12 module : absent
- dashboard PRE_T12 SHA-256 : `9991bbb5513101ea66d22411dfe7da8e1ba79ebc2d1bea668ef07acec3546021`
- disque root : `60%`
- audit : `PASS`

### Tests sur copie exacte et canary

Workflow : `38386214548`

Avant mutation live :

- dépendances T8/T9/T10/T11 saines : `PASS`
- patch T12 : `PASS`
- classes FULL/PARTIAL/ZERO : `PASS`
- candidate_id stable lorsque le budget change : `PASS`
- gate T11 inconnue : `PASS`
- aucune promotion/score/seuil : `PASS`
- callback T8↔T9↔T10↔T11↔T12 : `17 / 17 / 17 / 17 / 17`, `PASS`
- suite ciblée T12 : `PASS`
- stage exact live : `PASS`

Hashes du stage exact :

- dashboard POST_T12 SHA-256 : `6f717f1af70e0ccc5da67221cced408106a95100c185ed17afecd06d47eff1f0`
- T12 module SHA-256 : `582566a439ce1fdb9665237a81398f52476e4a85b715ee855d310ed7d407a4f9`
- backup : `brotoculateur/backups/t12-20261013T105141Z`

Premier battement canary live :

- état : `RUNNING`
- processed_packets : `84`
- T11 observations : `488`
- T12 observations : `488`
- candidats enregistrés : `488`
- candidate_id uniques : `111`
- bloqués T11 : `0`
- classes Budget : `FULL = 488`
- delta T11 : `488`
- delta T12 : `488`
- disque root : `60%`
- workflow : `PASS`

Le nombre `488` représente des observations candidates techniques pré-score. Il ne représente ni 488 preuves scientifiques, ni 488 cristaux canonisés, ni 488 promotions de ValidationState.

### Audit indépendant POST_T12

Workflow : `38386301767`

Fenêtre runtime observée après redémarrage :

- source : `POST_T12`
- moteur : `RUNNING`
- processed_packets : `4 638`
- cristaux : `1 823 917`
- T8 observations : `25 904`
- T8 FAIL : `0`
- T8 LIMITED : `0`
- T9 observations : `25 904`
- T9 drifts : `0`
- T10 observations : `25 904`
- T11 observations : `25 904`
- T11 demande normalisée : `43 264`
- T11 conseil normalisé : `43 264`
- T11 coupé : `0`
- T12 mode : `BRUTUS_T12_CANDIDATE_V1`
- T12 activé : `true`
- T12 observations : `25 904`
- candidats enregistrés : `25 904`
- candidate_id uniques : `731`
- bloqués T11 : `0`
- dashboard SHA-256 : `6f717f1af70e0ccc5da67221cced408106a95100c185ed17afecd06d47eff1f0`
- T12 module SHA-256 : `582566a439ce1fdb9665237a81398f52476e4a85b715ee855d310ed7d407a4f9`
- disque root : `60%`
- audit : `PASS`

L'audit indépendant confirme le lockstep complet jusqu'à T12 et l'absence de dérive upstream. T12 reste une couche de matérialisation pré-score seulement : pas de score, pas de seuil, pas de revendication scientifique, pas de canonisation, pas de contrôle de calcul et pas de promotion de preuve.

## Interprétation

T12 fonctionne maintenant comme la frontière explicite entre les couches d'observation/contre-test/budget et les futures couches de classement. Il produit une population de candidats techniques observables sans leur attribuer de valeur scientifique.

Le nombre de `candidate_id` uniques est inférieur au nombre d'observations parce qu'un même candidat technique peut être observé plusieurs fois. Ce comportement est volontaire : l'identité est déterministe sur formule/source/sortie, tandis que les observations restent comptées séparément.

Le budget ZERO reste enregistrable par conception et par test. Cela évite de transformer silencieusement une contrainte opérationnelle de ressources en rejet scientifique.

## Statut final

`LIVE_VALIDATED_SHADOW` — T12 actif et validé opérationnellement comme matérialiseur de candidats techniques pré-score. Prochaine vertèbre officielle : `L1 — Score cristal`.
