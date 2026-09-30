# C͡3RUTUS — Architecture des mondes

## Correction centrale

Les **9 positions C3 ne sont pas 9 mondes**.

Elles sont **9 projections locales à l'intérieur d'un monde** :

```
MONDE
└── 3 triangles
    └── 3 positions chacun
        = 9 projections locales
```

Cette distinction sépare désormais clairement :

1. la géométrie interne d'un monde;
2. les mondes eux-mêmes;
3. les familles de mondes;
4. la bulle globale ANTMUX.

## Hiérarchie

```
BULLE GLOBALE ANTMUX
├── famille MATTER
│   └── monde CARBON
│       ├── Z=7
│       ├── VERSO LOCAL
│       ├── -Z=6
│       └── 9 projections C3
├── famille INFORMATION
│   └── monde CRYPTO
│       └── VERSO LOCAL
├── famille TIME
├── famille MATH
├── famille BIO
└── famille ENERGY
```

Les mondes TIME/CLOCK, MATH/GEOMETRY, BIO/CELL et ENERGY/FREQUENCY sont seulement des **ancres STUB** dans v0.1. Ils ne deviennent actifs qu'après définition de leurs contrats.

## Deux Verso distincts

### VERSO LOCAL

Le Verso local demeure au coeur du monde.

```
Z=7 <-> VERSO LOCAL <-> -Z=6
```

Il ne change donc pas d'endroit à cause de l'ajout de la grande bulle.

### VERSO GLOBAL

Le Verso global est une porte différente.

```
WORLD_A -> VERSO GLOBAL -> WORLD_B
```

Il sert seulement aux passages inter-mondes.

## World Router

Aucun passage n'existe parce que deux mondes sont simplement dessinés dans la même bulle.

Un passage doit posséder un contrat explicite :

```
PORTAL =
SOURCE
+ TRANSFORMATION
+ DESTINATION
+ PROOF
```

Sans contrat : **PORTAIL FERMÉ**.

## Premier contrat

Le premier contrat de démonstration relie :

```
MATTER/CARBON
-> VERSO-GLOBAL-01
-> INFORMATION/CRYPTO
```

Transformation actuelle :

```
UTF8-CARRIER-V1
```

Exemple :

```
"C" -> 0x43 -> 01000011
```

Ceci est un **encodage de transport**, pas du chiffrement ni un hash. Il permet seulement de montrer qu'une identité peut changer de représentation en traversant le routeur.

Le contrat exige un **ROUNDTRIP** : la représentation transportée doit pouvoir redevenir la donnée d'entrée.

## Invariants transportés par une fourmi

Une fourmi qui traverse le Verso global conserve au minimum :

- ANT_ID
- TICK
- STATE
- PROOF_REF
- ECHO

La représentation du monde peut changer; l'identité de provenance ne doit pas disparaître.

## Rôle d'ANTMUX

Dans cette architecture :

```
ANT = agent mobile
MUX = sélection / routage
ANTMUX = réseau de transport contrôlé entre mondes
```

C'est une définition d'architecture logicielle du projet, pas une affirmation de physique interdimensionnelle.

## Expérience minimale de bout en bout

`WORLD-ROUNDTRIP-0001` sert de test de référence du système complet : une fourmi part de `MATTER/CARBON`, traverse le Verso global vers `INFORMATION/CRYPTO`, puis revient vers `MATTER/CARBON`.

Le test ne cherche pas à prouver une propriété physique. Il vérifie le contrat logiciel : routage autorisé, transformation réversible, conservation des invariants de l'agent, reconstruction des données et trace complète.

```text
ANT-0001
  + WORLD_A
  + PORTAL_CONTRACT
  + TRANSFORM
  + WORLD_B
  + RETURN
  + PROOF
  = PASS | FAIL
```

Cette expérience est la base à généraliser avant d'ajouter de nouveaux mondes actifs.
