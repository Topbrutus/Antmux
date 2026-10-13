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

## Déploiement prévu

Séquence proof-first :

1. audit VPS non mutant ;
2. exiger état exact `PRE_T12` ;
3. copier le package live dans un stage ;
4. appliquer T12 seulement au stage ;
5. compiler et exécuter les tests sur cette copie exacte ;
6. save/pause ;
7. backup dashboard/T8/T9/T10/T11/T12/statut/drop-in ;
8. appliquer exactement dashboard + T12 du stage ;
9. restart ;
10. canary live ;
11. rollback automatique si dérive ;
12. audit indépendant POST_T12 ;
13. checkpoint GitHub avec hashes et mesures live.

## Statut avant déploiement

`READY_FOR_PR` — T12 n'est pas encore déployé live au moment de cette section.
