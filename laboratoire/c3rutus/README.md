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
- 9 projections locales = 3 triangles × 3 positions dans un monde.
- Bulle globale ANTMUX = conteneur des familles et mondes.
- Verso local = interface Z ↔ −Z à l'intérieur d'un monde.
- Verso global = interface de transit entre mondes.
- World Router = aucun passage sans contrat explicite.
- 118 éléments = une seule table canonique référencée par les 9 projections locales.

## Fresque

Le rendu 3D reconstruit la scène depuis les règles :
- une grande bulle globale ANTMUX;
- un monde actif MATTER/CARBON;
- deux couches locales Z / −Z;
- un Verso local qui reste au coeur du monde;
- un Verso global distinct pour les passages inter-mondes;
- un monde INFORMATION/CRYPTO distinct;
- trois triangles et neuf projections locales C3;
- un serpent entre les projections;
- 9 fourmis locales;
- une fourmi de transit pour le portail;
- une adresse ECHO déterministe qui inclut le monde et la projection.

Les points des 118 éléments sont visualisés neuf fois dans le monde actif, mais les données ne sont pas copiées neuf fois en mémoire : chaque projection référence le même tableau canonique.

Le premier contrat de passage est MATTER/CARBON → VERSO-GLOBAL-01 → INFORMATION/CRYPTO. Il utilise UTF8-CARRIER-V1 comme démonstration réversible de transport. Ce mécanisme est un contrat logiciel; il ne constitue pas une affirmation de voyage physique entre dimensions.

## Première expérience complète — WORLD-ROUNDTRIP-0001

Le premier noyau fonctionnel complet du système multi-mondes à agents est un aller-retour vérifiable :

```text
MATTER/CARBON
    ↓
VERSO-GLOBAL-01
    ↓
INFORMATION/CRYPTO
    ↓
VERSO-GLOBAL-01
    ↓
MATTER/CARBON
```

L'expérience utilise une seule fourmi logique, `ANT-0001`, et le contrat `PORTAL-CARBON-CRYPTO-01`.

Valeur de démonstration :

```text
C
→ UTF8-CARRIER-V1
→ hex 43
→ bits 01000011
→ C
```

Le verdict est `PASS` seulement si :

- le trajet aller est ouvert ;
- le trajet retour est ouvert ;
- `ANT_ID`, `TICK`, `STATE`, `PROOF_REF` et `ECHO` restent identiques ;
- le même contrat réversible est utilisé dans les deux directions ;
- la transformation annoncée correspond au carrier utilisé ;
- le mode de preuve est `ROUNDTRIP` ;
- la donnée reconstruite est identique à la donnée de départ ;
- les neuf événements obligatoires de la trace sont présents dans l'ordre.

La trace produite est immuable en mémoire pour cette exécution. Elle constitue une preuve structurelle de l'expérience, mais pas encore un journal persistant ou une preuve cryptographique.

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

La page publique est publiée comme contenu statique du laboratoire. Les changements du backend Shared Queen restent un cycle de déploiement séparé.

## Limites

- Les propriétés physiques détaillées des 118 éléments ne sont pas encore injectées : v0.1 contient numéro atomique + symbole.
- Aucun résultat scientifique nouveau n'est déclaré par ce prototype.
- Aucun code Parazone n'est lu ou modifié.
- C͡3RUTUS v0.1 est intégré à `main`; les extensions futures continuent de passer par branches, PR et validation CI.

## Test

```bash
node --test laboratoire/c3rutus/tests/core.test.mjs
```
