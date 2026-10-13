# BRUTUS — Colonne 37 (prototype)

Prototype isolé du live VPS.

## Architecture

- 33 vertèbres = 33 instruments déterministes.
- 4 organes maîtres = Cortex Brutus / Pinéale, Papillon, Bibliothèque rapide 37, Reine/Fourmis.
- Total = 37 postes.
- Le Cortex Brutus est inséré entre C1 et C2 sans devenir une vertèbre supplémentaire.
- Papillon conserve ses 144 routes et ajoute une voie locale 0..36.
- La bibliothèque utilise 37 buckets et une identité Z canonique.

## Porte d’entrée Z

Parcours verrouillé :

`C1 Entrée -> Cortex Brutus / Pinéale -> Z-STAMP -> C2 Empreinte Z -> C3 Bibliothèque`

Le `Z-ID` identifie la matière canonique. Le chemin, la provenance et le parent Z sont conservés séparément afin que plusieurs routes puissent converger vers un même canonique sans perdre leur histoire.

## Constante Brutus

`B = 7^21 / 10^17 = 5.58545864083284007`

La constante est transportée comme référence dans le Cortex Brutus. Elle n'est pas multipliée automatiquement dans les valeurs. Toute application numérique future doit être explicite et traçable.

## Poussière / fourmis

Les répétitions d’un même `Z-ID` ne recréent pas 245 000 objets complets. La bibliothèque garde un cristal canonique et incrémente :

- le compteur d’occurrences;
- les chemins indépendants;
- les digests de provenance;
- les parents Z observés;
- la première et la dernière apparition.

## Test massif

Le test de référence injecte 245 000 observations identiques par 37 chemins :

- 1 cristal canonique;
- 245 000 occurrences;
- 244 999 répétitions absorbées;
- 37 chemins/provenances distincts;
- 33 évaluations vertébrales seulement pour cette identité.

## Sécurité

Ce laboratoire ne commande pas le Brotoculateur VPS. Il sert à construire et falsifier l’architecture avant toute éventuelle intégration live.
