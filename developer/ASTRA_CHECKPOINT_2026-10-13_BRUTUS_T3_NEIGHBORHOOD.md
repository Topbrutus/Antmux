# ASTRA CHECKPOINT — Brutus T3 Voisinage

Date: 2026-10-13
Stage: T3 — Voisinage
Mode: SHADOW_ONLY

## Objectif

T3 mesure un voisinage sémantique entre traces structurelles distinctes après T2.
C2 reste l'identité exacte et T2 reste l'autorité pour le doublon exact.

## Règle fondamentale

T3 n'utilise jamais la distance entre les bits des SHA256 C2.
Une distance de hash cryptographique ne représente pas une proximité structurelle.

La métrique T3 compare des propriétés du paquet réel à l'intérieur d'une même famille T1:
- formule terminale;
- état de validation;
- profondeur;
- longueur de la chaîne de formules;
- ordre de grandeur binaire de la valeur;
- suffixe commun de chaîne de formules;
- proximité numérique par ordre de grandeur de l'écart.

## Classes

- EXACT_REFERENCE: T2 a déjà déclaré le même C2 exact.
- NEAR: score >= 80.
- ADJACENT: score 60–79.
- DISTANT: score < 60 avec un représentant disponible.
- ISOLATED: aucun représentant antérieur dans la famille.

## Bornes

- bassin par famille borné, défaut 128 représentants;
- aucun O(n²) global non borné;
- aucun paquet fusionné;
- aucun calcul sauté;
- aucun changement de scheduling;
- aucune promotion de preuve;
- aucune revendication de similarité scientifique.

## Tests locaux POST-T2 exact

T3_METRIC=PASS
T3_SAME_VALUE_DISTINCT_C2=PASS
T3_CHAIN=PASS
T3_ROLLOVER=PASS
T3_NEIGHBORHOOD=PASS

Échantillon local:
- observations: 440
- EXACT_REFERENCE: 167
- NEAR: 216
- ADJACENT: 42
- DISTANT: 11
- ISOLATED: 4
- rollover exact references: 167 -> 281

## Hashes POST-T3 attendus Linux

- t1_family.py: e68643e72c4c0551b3d7187fde05f5d3a37c45b7e5f0d30cd750869378a32320
- t2_exact_duplicate.py: 52b9a8a39480e0e5201d524eec330effdabb1642988fdeefebb47d00c2421e12
- t3_neighborhood.py: f4144e566508d6bd0e17279690d3ff9edd72e85a93d5a0d8dead2beeab1310d6
- orchestrator.py: 49585752a6bba0c830193be10743a7f44388cc295183478c1f8e7b8f3df8f862
- dashboard.py: 943f075765282b448c8f3d01cb3d03e54ae5d5d84bfd18dd92d79fd6b7f7f131

## Déploiement

Pas encore validé live au moment de ce checkpoint initial.
Le workflow impose audit PRE-T3, copie exacte, tests, save/pause, backup, patch, restart, start et validation live; rollback automatique sur erreur.
