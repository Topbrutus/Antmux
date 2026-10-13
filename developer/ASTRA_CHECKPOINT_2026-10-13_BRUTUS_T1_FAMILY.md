# ASTRA CHECKPOINT â€” BRUTUS T1 FAMILLE â€” 2026-10-13

## Position
T1 suit immÃ©diatement C7 dans la Colonne 37 :

C1 Z-STAMP â†’ C2 Empreinte â†’ C3 BibliothÃ¨que â†’ C4 NouveautÃ© â†’ C5 RaretÃ© â†’ C6 Provenance â†’ C7 Routeur â†’ T1 Famille

## Contrat T1
T1 est strictement `SHADOW_ONLY`.

Il ne change :
- ni la valeur d'un paquet ;
- ni le scheduling ;
- ni la prioritÃ© ;
- ni la route rÃ©elle ;
- ni le statut de preuve ;
- ni le nombre de calculs exÃ©cutÃ©s.

`actual_routes_applied = 0` et `compute_skips = 0`.

## DÃ©finition de famille
La famille opÃ©rationnelle courante est dÃ©terminÃ©e par la derniÃ¨re opÃ©ration connue de `formula_chain`.

Familles V1 :
- `ROOT`
- `ARITHMETIC_EXPANSION` : PLUS1, DOUBLE, SQUARE
- `REDUCTION` : HALF_EVEN, DIGIT_SUM, BIT_LENGTH
- `PELL` : PELL_N, PELL_Q
- `FACTOR_GAP` : FACTOR_GAP_LOW_666, FACTOR_GAP_HIGH_666
- `CRYSTAL_REINJECTION` : CRYSTAL_REINJECT:* et CRYSTAL_SEPARATOR_RELEASE
- `OTHER` : formule non reconnue

T1 conserve aussi `lineage_families` et `mixed_lineage` afin qu'une trace ne perde pas les familles qu'elle a traversÃ©es.

Ce classement est une taxonomie d'ingÃ©nierie du moteur. Il ne constitue pas une classification scientifique externe.

## Couplage C7
T1 reÃ§oit la recommandation C7 correspondante et maintient une matrice `route_family_counts`.
Cela permet de mesurer quelles familles sont recommandÃ©es vers `PROVENANCE_REVIEW`, `NOVELTY_REVIEW`, `RARE_REPLAY`, etc., sans que T1 ou C7 n'appliquent la route.

## Gardes
- T1 ne peut Ãªtre actif que si C7 est actif.
- Le workflow exige C2=C3=C4=C5=C6=C7 avant mutation.
- Patch exact-hash POST-C7.
- Test sur copie exacte avant pause du live.
- Backup + rollback automatique.
- DÃ©ploiement seulement aprÃ¨s `save â†’ pause`.

## Tests locaux sur copie exacte POST-C7
PASS :
- taxonomie directe ;
- table croisÃ©e route/famille ;
- chaÃ®ne C2â†’T1 1:1 ;
- rollover conservÃ© ;
- shadow guards.

Ã‰chantillon local :
- 148 observations synchronisÃ©es ;
- ROOT 3 ;
- ARITHMETIC_EXPANSION 71 ;
- REDUCTION 53 ;
- PELL 21 ;
- rollover 148 â†’ 149.

## Hashes POST-T1 attendus
- `t1_family.py` : `e68643e72c4c0551b3d7187fde05f5d3a37c45b7e5f0d30cd750869378a32320`
- `orchestrator.py` : `453c06a2064e743e08a042ced8dc7406492ab323c664dea16b1f6de1aaa9f526`
- `dashboard.py` : `c54737bfa9213d1625f8134a7588ee37a99712b44e7aa37a2246743c5c344355`

## Ã‰tat au moment de ce checkpoint
T1 est prÃ©parÃ© et testÃ© localement. Aucun dÃ©ploiement VPS n'est revendiquÃ© par cette section tant qu'un run `canary_start` et un audit indÃ©pendant n'ont pas PASS.

## Validation live VPS
Déploiement T1 : GitHub Actions `38359261753` — SUCCESS.
Audit indépendant : GitHub Actions `38359359530` — PASS.

État audit indépendant :
- moteur : RUNNING ;
- cristaux : 1 654 746 ;
- C2=C3=C4=C5=C6=C7=T1 : 65 093 observations ;
- ROOT : 1 ;
- ARITHMETIC_EXPANSION : 33 883 ;
- REDUCTION : 18 834 ;
- PELL : 12 369 ;
- FACTOR_GAP : 0 ;
- CRYSTAL_REINJECTION : 6 ;
- OTHER : 0 ;
- source : POST_T1 ;
- disque racine : 59 % utilisé, 48 862 756 KB libres.

Gardes confirmés : T1 reste SHADOW_ONLY, ne contrôle ni routage ni scheduling, n'applique aucune route, ne saute aucun calcul et ne promeut aucune preuve.
