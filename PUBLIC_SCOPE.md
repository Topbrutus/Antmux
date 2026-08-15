# Antmux — Frontière publique

Ce dépôt public expose uniquement ce qui est nécessaire pour **documenter, recalculer et tester** la partie publique d’Antmux.

## Ce qui peut être public

- les identités arithmétiques et combinatoires publiées ;
- le vérificateur indépendant exécuté dans le navigateur ;
- le générateur expérimental client-side ;
- les visualisations et artefacts destinés à la démonstration ;
- les résultats de tests reproductibles sur ces composants publics.

## Ce qui reste hors de ce dépôt

- l’implémentation du serveur dédié Antmux ;
- la topologie réseau et l’infrastructure privée ;
- les secrets, clés API, jetons, identifiants et certificats ;
- la configuration d’hébergement privée ;
- les intégrations fournisseur nécessitant des identifiants privés ;
- les mémoires, données personnelles et jeux de données privés ;
- les règles d’orchestration ou mécanismes propriétaires qui ne sont pas nécessaires à la vérification publique ;
- tout code provenant d’une sauvegarde privée du site qui appartient à l’application complète plutôt qu’à la démonstration publique.

## Principe

Le dépôt public doit permettre à un tiers de répondre à la question :

> « Les calculs publiés se recalculent-ils correctement sur ma propre machine ? »

Il n’a pas pour fonction de révéler l’application complète ou son infrastructure.

## Sécurité

Le fichier `.gitignore` réduit les risques d’ajout accidentel, mais **n’est pas une protection de secrets déjà commités**. Si un secret est un jour publié, il doit être considéré compromis, révoqué et remplacé.

## Terminologie

Les expressions narratives comme « secret atomique » désignent, dans le dépôt public, une **signature ou un état dérivé par Antmux**. Elles ne constituent pas l’affirmation d’un secret physique réel de la matière.
