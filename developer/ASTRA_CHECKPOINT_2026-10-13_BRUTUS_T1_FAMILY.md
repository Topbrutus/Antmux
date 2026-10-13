# ASTRA CHECKPOINT — BRUTUS T1 FAMILLE — 2026-10-13

## Position
T1 suit immédiatement C7 dans la Colonne 37 :

C1 Z-STAMP → C2 Empreinte → C3 Bibliothèque → C4 Nouveauté → C5 Rareté → C6 Provenance → C7 Routeur → T1 Famille

## Contrat T1
T1 est strictement `SHADOW_ONLY`.

Il ne change :
- ni la valeur d'un paquet ;
- ni le scheduling ;
- ni la priorité ;
- ni la route réelle ;
- ni le statut de preuve ;
- ni le nombre de calculs exécutés.

`actual_routes_applied = 0` et `compute_skips = 0`.

## Définition de famille
La famille opérationnelle courante est déterminée par la dernière opération connue de `formula_chain`.

Familles V1 :
- `ROOT`
- `ARITHMETIC_EXPANSION` : PLUS1, DOUBLE, SQUARE
- `REDUCTION` : HALF_EVEN, DIGIT_SUM, BIT_LENGTH
- `PELL` : PELL_N, PELL_Q
- `FACTOR_GAP` : FACTOR_GAP_LOW_666, FACTOR_GAP_HIGH_666
- `CRYSTAL_REINJECTION` : CRYSTAL_REINJECT:* et CRYSTAL_SEPARATOR_RELEASE
- `OTHER` : formule non reconnue

T1 conserve aussi `lineage_families` et `mixed_lineage` afin qu'une trace ne perde pas les familles qu'elle a traversées.

Ce classement est une taxonomie d'ingénierie du moteur. Il ne constitue pas une classification scientifique externe.

## Couplage C7
T1 reçoit la recommandation C7 correspondante et maintient une matrice `route_family_counts`.
Cela permet de mesurer quelles familles sont recommandées vers `PROVENANCE_REVIEW`, `NOVELTY_REVIEW`, `RARE_REPLAY`, etc., sans que T1 ou C7 n'appliquent la route.

## Gardes
- T1 ne peut être actif que si C7 est actif.
- Le workflow exige C2=C3=C4=C5=C6=C7 avant mutation.
- Patch exact-hash POST-C7.
- Test sur copie exacte avant pause du live.
- Backup + rollback automatique.
- Déploiement seulement après `save → pause`.

## Tests locaux sur copie exacte POST-C7
PASS :
- taxonomie directe ;
- table croisée route/famille ;
- chaîne C2→T1 1:1 ;
- rollover conservé ;
- shadow guards.

Échantillon local :
- 148 observations synchronisées ;
- ROOT 3 ;
- ARITHMETIC_EXPANSION 71 ;
- REDUCTION 53 ;
- PELL 21 ;
- rollover 148 → 149.

## Hashes POST-T1 attendus
- `t1_family.py` : `e68643e72c4c0551b3d7187fde05f5d3a37c45b7e5f0d30cd750869378a32320`
- `orchestrator.py` : `453c06a2064e743e08a042ced8dc7406492ab323c664dea16b1f6de1aaa9f526`
- `dashboard.py` : `c54737bfa9213d1625f8134a7588ee37a99712b44e7aa37a2246743c5c344355`

## État au moment de ce checkpoint
T1 est préparé et testé localement. Aucun déploiement VPS n'est revendiqué par cette section tant qu'un run `canary_start` et un audit indépendant n'ont pas PASS.
