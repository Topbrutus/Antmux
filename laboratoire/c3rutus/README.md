# C͡3RUTUS — Genesis World v0.1

Prototype expérimental ANTMUX. Il ne prétend pas démontrer une nouvelle loi physique.

## Invariants codés

- Z = cercle logique en 7.
- −Z = cercle logique en 6.
- Enveloppe = 13.
- Maille commune = ppcm(7,6) = 42.
- Médiane = 6,5.
- Centre de polarité = 0.
- RECTO = 555.
- Boucle trinitaire C3 :
  - R(2,3)=1
  - R(3,1)=2
  - R(1,2)=3
- 9 mondes = 3 triangles × 3 positions.
- 118 éléments = une seule table canonique référencée par les 9 mondes.

## Fresque

Le rendu 3D reconstruit la scène depuis les règles :
- une enveloppe;
- deux couches Z / −Z;
- un Verso central;
- trois triangles;
- un serpent entre les triangles;
- 9 fourmis spatiales;
- 9 projections de la même table périodique;
- une adresse ECHO déterministe.

Les points des 118 éléments sont visualisés neuf fois, mais les données ne sont pas copiées neuf fois en mémoire : chaque monde référence le même tableau canonique.

## Horloge de la Vie

Cette v0.1 reprend la référence temporelle actuellement utilisée par l'Horloge de la Vie :

- nominal : 240.1 Hz;
- exact calculé : 240.10000000005764801000001384128720100332329305696089 Hz;
- poussière : 0.00000000005764801000001384128720100332329305696089 Hz;
- cycle 6·7·13 : ppcm = 546.

Le battement exact reste séparé de l'animation : le monde échantillonne une action collective par seconde afin que les déplacements restent visibles, tout en affichant le beat, les résidus 6/7/13 et la phase 546.

À chaque tick d'action :
1. le monde actif avance sur le serpent;
2. la phase C3 avance;
3. l'élément actif avance;
4. l'adresse ECHO est reconstruite;
5. les fourmis avancent.

Le module est local au laboratoire C3RUTUS et ne modifie pas le runtime X72 existant.

## Limites

- Les propriétés physiques détaillées des 118 éléments ne sont pas encore injectées : v0.1 contient numéro atomique + symbole.
- Aucun résultat scientifique nouveau n'est déclaré par ce prototype.
- Aucun code Parazone n'est lu ou modifié.
- Aucun merge vers main n'est effectué.

## Test

```bash
node --test laboratoire/c3rutus/tests/core.test.mjs
```
