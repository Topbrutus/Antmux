# Noyau dynamique X72 — prototype visualisable v0.1

## Statut

Prototype de laboratoire. Ce dossier n'est pas encore le runtime autoritaire du serveur.

Le but de cette première étape est de déposer dans Antmux le moteur visualisable qui permet d'observer :
- les deux voies dynamiques opposées ;
- les trois bassins / niveaux ;
- les passages centraux obligatoires ;
- l'entrée et la sortie du bassin 1 ;
- les ports d'injection et d'interception ;
- l'apparition de cristaux simulés ;
- la sélection d'un point d'analyse ;
- le changement de monde structurel.

## Fichier principal

`noyau_dynamique_visualiseur.py`

Dépendances :
```text
numpy
matplotlib
```

Lancement local :
```bash
python noyau_dynamique_visualiseur.py
```

## Règle d'intégration Antmux

Le dépôt X72 existant est server-authoritative. Cette v0.1 ne doit donc pas être branchée directement au serveur en production.

Étape suivante sûre :
1. séparer `DynamicCrystalEngine` de la couche Matplotlib ;
2. définir un état sérialisable `NoyauState` ;
3. exposer des entrées contrôlées : injection, interception, changement de monde ;
4. ajouter des invariants et tests déterministes ;
5. seulement ensuite relier ce noyau au runtime partagé `deploy/x72-shared-queen/app/server.py`.

La règle existante reste :
```text
ETAT -> TELEMETRIE -> VISUALISATION
```

Le visuel ne doit jamais inventer un état absent du moteur.

## Statut scientifique

Les variables de cohérence, feedback, cristallisation et mondes structurels sont ici des paramètres de simulation expérimentale. Elles ne constituent pas des mesures physiques ou une preuve de conscience.

## Provenance

Source locale vérifiée avant dépôt :
`D:\noyau\noyau_dynamique_visualiseur.py`

Compilation locale `python -m py_compile` : PASS avant publication de cette branche.
