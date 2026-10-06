# BrutoBac — vitrine Fourmi Aquarium 3D

Route publique : `/laboratoire/brutobac/`.

La page enveloppe le BrutoBac servi par le Queen Server à `/laboratoire/embryon-x72/api/brutobac/`. Le monde Fourmi reste une projection publique en lecture seule du transport autoritaire Antmux.

## Poussière Brotoculateur

Quand l'opérateur ouvre BrutoBac sur la même machine que le Brotoculateur, la vitrine lit uniquement le pont local `http://127.0.0.1:8780/api/status`.

La vitrine préfère les champs `dust_slots` et `dust_per_transit` lorsqu'ils sont exposés. Le pont courant expose déjà `big_crystals`; la vitrine utilise donc, en repli, la relation opérationnelle courante `poussière = big_crystals × 39`, correspondant à l'invariant `DUST_PER_TRANSIT = 39` du Structureur39.

Une augmentation de la quantité de poussière déclenche une pluie déterministe de particules au-dessus du monde Fourmi. Si le pont local est absent, aucune poussière n'est inventée.

Cette pluie est une représentation visuelle. Elle ne modifie ni `live-transport.db`, ni la Reine, ni une Fourmi, ni un cristal, et ne constitue pas une preuve mathématique.

## Sources réelles

- Fourmis / positions / matériaux : Queen Server `QUEEN_SERVER_V0_2` → BrutoBac public SSE/snapshot.
- Poussière : sortie locale du Brotoculateur → pont local read-only 8780 → couche visuelle BrutoBac.

Aucun secret, token ou contrôle opérateur n'est envoyé dans la vitrine publique.
