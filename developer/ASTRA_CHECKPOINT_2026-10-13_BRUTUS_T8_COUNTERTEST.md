# ASTRA CHECKPOINT — BRUTUS T8 CONTRE-TEST — 2026-10-13

## Position
T8 = Contre-test, après T7 Calcul dans le parcours officiel Brutus Colonne 37.

## Mode
- schema: `BRUTUS_T8_COUNTERTEST_V1`
- authority: `SHADOW_ONLY`
- aucune mutation de `ValidationState`
- `COUNTERTESTED` n'est pas écrit par T8 v1
- aucune promotion de preuve
- aucun routage, scheduling ou compute skip

## Source observée
T8 consomme le callback réel des résultats de formule déjà envoyé à Brutomagique :
`formula_id + source TracePacket + output TracePacket`.

## Contre-tests
Chaque sortie vérifie :
1. lignée parent/depth/branch/formula_chain ;
2. lignée Z (`z_id`, `z_parent_id`, `z_origin_id`) ;
3. état EXACT pour les 10 formules actuelles ;
4. relation indépendante par formule.

Relations courantes :
- PLUS1 : `y-x=1`
- DOUBLE : `y` pair et `y/2=x`
- SQUARE : `sqrt(y)=abs(x)`
- HALF_EVEN : `2y=x`
- DIGIT_SUM : relation décimale reconstruite
- BIT_LENGTH : `2^(y-1) <= abs(x) < 2^y`
- PELL_N : Pell par matrice binaire indépendante
- PELL_Q : `P(x²)=y*P(x)` via la même matrice indépendante, sans appeler `pell()`/`pell_q()`
- FACTOR_GAP_LOW_666 : `y(y+666)=x`
- FACTOR_GAP_HIGH_666 : `y(y-666)=x`

## Résultats locaux
- 10/10 formules actuelles : PASS
- corruption volontaire PLUS1 : FAIL détecté
- formule inconnue : LIMITED
- callback Brutomagique/T8 : delta 1:1
- tests : PASS

## Hashes POST-T8 locaux
- dashboard.py: `8a294e39869babd68ff7c5456afbbd5d740ca44aec360e60a0f5bd8a1335e94e`
- t8_countertest.py: `a93bd6cd9aaaf0fe832604de9e390e6d69de7dfb8b853e558d8c9955761cce9e`

## Garde-fous live
Le workflow exige POST-T7 exact avant mutation, teste une copie exacte du package live, puis :
`save -> pause -> backup -> patch -> restart -> start`.
Rollback automatique si le canary diverge.

Le canary exige :
- delta T8 = delta Brutomagique sur les résultats de formule ;
- `failed = 0` ;
- `limited = 0` ;
- couverture = 1.0 ;
- aucun worker_error.

## Statut avant déploiement
READY_FOR_PR — pas encore déployé au moment de cette section.
## Validation live VPS — 2026-10-13

T8 a été déployé en shadow sur le Brotoculateur live après audit PRE_T8 exact.

### Déploiement canary
- workflow: `38373497747`
- source initiale: `PRE_T8`
- backup: `brotoculateur/backups/t8-20261013T090251Z`
- état: RUNNING
- 488 résultats Brutomagique observés pendant la fenêtre canary
- 488 observations T8
- 488 PASS
- 0 FAIL
- 0 LIMITED
- couverture: 1.0
- delta T8 = delta Brutomagique = 488
- relation_passes = 488
- workflow: PASS

### Audit indépendant POST_T8
- workflow: `38373619414`
- source: `POST_T8`
- état: RUNNING
- processed_packets: 9 341
- cristaux: 1 757 480
- T7 packets: 9 341
- T8 observations: 52 709
- T8 PASS: 52 709
- T8 FAIL: 0
- T8 LIMITED: 0
- disque root: 59%
- audit: PASS

### Interprétation
T8 contre-teste toutes les sorties des 10 formules actuellement enregistrées au moyen de relations distinctes du calcul forward lorsque possible. Les résultats ci-dessus établissent le bon fonctionnement de la télémétrie T8 dans cette configuration live ; ils ne constituent pas une preuve scientifique générale.

`ValidationState.COUNTERTESTED` reste volontairement inchangé.

## Statut final
LIVE_VALIDATED_SHADOW — T8 actif, aucune autorité moteur, aucune promotion de preuve.
