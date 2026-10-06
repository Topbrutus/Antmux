# BrutoBac — vitrine Fourmi Aquarium 3D

Route publique : `/laboratoire/brutobac/`.

La page enveloppe le BrutoBac servi par le Queen Server à `/laboratoire/embryon-x72/api/brutobac/`. Le monde Fourmi reste une projection publique en lecture seule du transport autoritaire Antmux.

## Poussière Brotoculateur

Quand l'opérateur ouvre BrutoBac sur la même machine que le Brotoculateur, la vitrine lit uniquement le pont local `http://127.0.0.1:8780/api/status`.

Champs utilisés :

- `dust_slots` — quantité cumulée observée;
- `dust_per_transit` — quantité de référence par transit.

Une augmentation de `dust_slots` déclenche une pluie déterministe de particules au-dessus du monde Fourmi. Si le pont local est absent, aucune poussière n'est inventée.

Cette pluie est une représentation visuelle. Elle ne modifie ni `live-transport.db`, ni la Reine, ni une Fourmi, ni un cristal, et ne constitue pas une preuve mathématique.

## Sources réelles

- Fourmis / positions / matériaux : Queen Server `QUEEN_SERVER_V0_2` → BrutoBac public SSE/snapshot.
- Poussière : sortie locale du Brotoculateur → pont local read-only 8780 → couche visuelle BrutoBac.

Aucun secret, token ou contrôle opérateur n'est envoyé dans la vitrine publique.
