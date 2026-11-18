# Moteur Antmux — v0.1

## Finalité

Vision du propriétaire, sans affirmation scientifique ni archéologique : le moteur Antmux doit, à terme, servir à lire les structures invisibles à l'intérieur des pyramides, qui attendent d'être dégagées par un système logique. Rien de cette lecture n'est implémenté. Le futur composant prévu s'appelle le lecteur de structures.

La graine Genesis tient dans un petit fragment. Le README d'Antmux le dit déjà : une graine suffisamment petite pour être recalculée, suffisamment structurée pour être vérifiée ; si la graine et les règles de reconstruction survivent, la cité peut recommencer. Le propriétaire rapproche cette graine de celles qu'il imagine dans les pyramides : un seul fragment suffirait à reconstruire l'ensemble. C'est sa vision, pas un fait archéologique. Le lecteur de structures, plus tard, cherchera ce genre de fragment dans des données d'entrée qu'il ne possède pas encore.

## Concept : changer Stonehenge par les fréquences

Récit du propriétaire, sans affirmation scientifique ni archéologique. Le cercle de 30 roches représente un Stonehenge encore à moitié debout, qui, dans ce récit, ferait encore du tort par des vibrations basses, sourdes, ternes et lentes. Le but n'est pas de reconstruire le monument tel quel. Le but est de changer les fréquences qui y circulent.

Le moteur distingue deux ondes :

- l'onde d'origine, étiquetée « ancienne fréquence » ;
- l'onde de remplacement : le canal à 2400 Hz et la fourmi et Brutus à 2401 Hz.

Un taux de transformation compte les cycles de 273 tics clos sans anomalie. Il n'augmente pas si le tic de clôture porte une anomalie. La page montre l'ancienne onde qui recule et la nouvelle qui traverse les pierres. La configuration par défaut laisse les 30 positions installées : le propriétaire marquera lui-même celles qui sont tombées ou réservées. Rien n'a été inventé à ce sujet.

## Ce qui est dans ce module

Un seul noyau, `Moteur`, tient l'état partagé. Les pages lisent des instantanés. Les composants s'enregistrent ; on peut en ajouter un sans réécrire les autres.

| Pièce | Rôle | Étiquette dominante |
| --- | --- | --- |
| Horloge v0.1 | 37 Hz logique, 2401 phases, pas de 64 ou 65 | DOCUMENTÉ / CALCUL EXACT |
| Roues A et B | Fibonacci et nombres premiers sur les graines 4, 7, 9, 12, 13, 16 | DOCUMENTÉ |
| Roue Z | Cascade exacte 2401 → 343 → 49 → 7 → 1 | CALCUL EXACT ; la lecture en hertz est une CIBLE |
| Six roues | Vitesses 2 à 7 sur un anneau de 273, réalignement au tic 273 | Décision du propriétaire ; l'anneau est CANDIDAT |
| Stonehenge | 30 positions de 12°, canal 2400 Hz, amplificateurs, écho | Grille DOCUMENTÉE ; profils CANDIDAT |
| Polybrutus | 7 points, 21 paires, projection sur les roches 0, 10, 15, 20 | CALCUL EXACT pour cette forme |
| Temple Z144 | Grille 12×12, index0 = 12×(ligne−1)+(colonne−1) | Formule CALCUL EXACT ; lien au tic CANDIDAT |
| Capsule | Affiche phase, coup et cellule. Définition introuvable | CANDIDAT |
| Pyramide de quartz | Motif visuel | CANDIDAT |
| Douze Épitagores | Emplacements vides, passage 6 → 7 | CANDIDAT / INCONNU |
| Colonie | Sept régimes d'une même Fourmi, phrases du README | Phrases DOCUMENTÉES ; branchements CANDIDAT |
| Cristallisation | Règle documentée 8 → 7 + 1, accumulation | Règle DOCUMENTÉE ; accumulation CANDIDAT |
| Graine | Configuration, tic, évolution, empreinte base 39 | Reconstruction CALCULABLE |
| Lecteur de structures | Interface vide | EXTENSION PRÉVUE |

Brutus est le nom du moteur, pas un huitième insecte.

## 2400 et les deux 2401

Trois objets portent des nombres voisins. Ils ne sont pas interchangeables.

- **2400 Hz** — décision du propriétaire : nombre de Z, « point de poussière », onde qui traverse les 30 pierres. 2400 / 30 = 80 passages par pierre et par seconde idéale. La période d'un battement est 1/2400 s = 1250/3 µs ≈ 416,667 µs.
- **2401 phases** — calcul exact : 7⁴, tour de l'horloge v0.1. La cascade 2401 → 343 → 49 → 7 → 1 est la même arithmétique.
- **2401 Hz, fourmi et Brutus** — décision du propriétaire. Avec le canal, l'écart |2401 − 2400| = 1 Hz est le battement audible de la page.
- **2401 Hz, cible V1.2** — candidat, cadence non mesurée. Même nombre que les phases et que la fourmi, autre rôle. Cette ambiguïté est laissée ouverte : le code garde trois clés distinctes.

Observation, sans conclusion : 2400 = 2401 − 1.

Des valeurs citées ailleurs dans la spec, et qui ne sont pas le canal : 240,1 Hz (construction femtoseconde) et la cible 2401 Hz.

## Conventions d'indexage

Fibonacci : F(0) = 0, F(1) = 1, et la graine n sélectionne F(n). Pour n ≥ 2, c'est le même terme que dans la numérotation F(1) = 1, F(2) = 1. Les graines commencent à 4.

Nombres premiers : le n-ième premier, avec p(1) = 2. La graine 4 donne 7, pas 11.

Sorties des six graines : A = 3, 13, 34, 144, 233, 987 et B = 7, 17, 23, 37, 41, 53. La graine 12 donne 144 et 37.

L'Horloge de Vie v0.1 a une autre liste (douze Fibonacci F2…F13 et les douze premiers nombres premiers). Elle est conservée et n'est pas substituée aux graines.

Temple : lignes et colonnes de 1 à 12, index0 de 0 à 143. Le couplage « index = tic mod 144 » réalise la période ppcm(37, 144) = 5328. La spec énonce la période ; elle n'écrit pas cette formule. Le couplage est CANDIDAT.

## Six roues

Chaque roue active avance de sa vitesse sur l'anneau. Elle revient à son départ après 273 / pgcd(273, vitesse) tics, soit 273, 91, 273, 273, 91 et 39 pour les vitesses 2 à 7. Le ppcm de ces périodes vaut 273 : c'est le premier tic strictement positif où les six sont réalignées. Les roues de vitesse 3 et 6 se rejoignent déjà à 91. La roue de vitesse 7 revient à 0 tous les 39 tics.

Si chaque roue n'avait pour période que sa vitesse, le ppcm(2…7) vaudrait 420, pas 273. C'est l'anneau qui donne 273. L'usage de 273 comme anneau commun est une modélisation à confirmer.

Une roue en pause ne bouge pas : sa position éditée reste sa position. Elle ne participe pas au ppcm. Changer une position de départ change la position affichée, pas le tic de réalignement, parce que (départ + vitesse × tic) ≡ départ (mod anneau) ne dépend pas du départ. Changer une vitesse ou l'anneau recalcule le tic. S'il n'est plus 273, la page le dit, sans erreur.

ppcm(30, 3, 7, 13) = 2730 = 10 × 273. Avec 2401 phases, ppcm(30, 3, 7, 13, 2401) = 936390. Ces deux cycles supposent la grille de 30.

## Polybrutus sur les pierres

Coordonnées exactes, R quelconque : P1 (0, 0, R), P2 (√3·R/2, 0, R/2), P3 (−√3·R/4, 3R/4, R/2), P4 (−√3·R/4, −3R/4, R/2), P5 (0, 0, −R), P6 (√3·R/2, 0, −R/2), P7 (−√3·R/2, 0, −R/2).

La projection sur le plan XY met P1 et P5 au centre. P2, P3, P4, P6 et P7 sont au rayon √3·R/2, aux azimuts 0°, 120°, 240°, 0° et 180°, donc sur les roches 0, 10, 20, 0 et 15. P2 et P6 se superposent sur la roche 0. Les 30 rotations de 12° donnent 30 ensembles distincts : {0, 10, 15, 20} n'a pas de symétrie non triviale modulo 30.

Un heptagone régulier ne s'emboîterait pas dans 30, parce que pgcd(7, 30) = 1. C'est la forme particulière du Polybrutus qui s'emboîte. Coïncidence géométrique exacte, pas une preuve physique.

Les familles recalculées depuis ces coordonnées, avec k = 4d²/R², sont 4, 7, 9, 12, 13, 16 avec les multiplicités 6, 2, 3, 6, 2, 2. Σk = 195. Le centroïde est (0, 0, R/14). Les 12 paires nord-sud donnent 12/21 = 4/7. Ce 12-là n'est pas la famille k = 12, qui compte 6 paires. L'attribution d'un k à une paire nommée n'est pas exposée comme une liste séparée : les k sont calculés paire par paire.

## Stonehenge, amplificateurs, roches réservées

Chaque roche a un gain, un délai et un timbre. Les 30 profils par défaut sont déterministes et tous différents. Ils sont CANDIDAT, à définir par le propriétaire. Le courant amplificateur règle l'intensité globale. Une roche `reservee` a un écho nul. Une roche `installee` amplifie.

Le cercle reflète l'état du moteur, dans le récit : sans anomalie, la résonance est harmonieuse ; avec une anomalie, elle est dissonante. L'absence de quorum entre deux convergences n'est pas une anomalie. Le quorum de l'Abeille est vrai quand les roues actives sont revenues à leur départ, donc au tic 0 et au tic 273, et faux entre les deux.

La liste des roches installées ou réservées est une configuration. Par défaut les 30 sont installées. On peut en marquer une réservée ou en ajouter. Si le nombre de positions n'est plus 30, l'instantané porte une alerte : l'emboîtement du Polybrutus et les cycles 2730 et 936390 ne s'appliquent plus tels quels. Les tests vérifient cette alerte au lieu de recalculer en silence sur une autre grille.

## Colonie

Les sept phrases viennent du README, ligne 30. Les branchements sur l'état sont CANDIDAT :

- la Fourmi mémorise et route l'état à 2401 Hz ;
- l'Abeille vérifie le quorum des roues ;
- le Scarabée transporte l'onde 2400 Hz d'une pierre à l'autre ;
- le Papillon trace la lemniscate des phases de l'anneau (le README, ligne 28) ;
- la Mante inhibe un état invalide ;
- la Libellule signale une anomalie, y compris une graine corrompue ;
- la Termite persiste le compteur d'évolution.

Le compteur d'évolution est le quotient entier du tic par l'anneau. Avec l'anneau par défaut, il vaut 1 après 273 tics, que le cycle ait été sain ou non. Le taux de transformation, lui, ne compte que les clôtures saines. L'alpha de la troisième coordonnée de la lemniscate n'est pas donné par le README : il reste INCONNU. Lier l'évolution à l'anneau éditable est CANDIDAT : si le propriétaire sépare la lemniscate de 273 et l'anneau des roues, il faudra les découpler.

## Cristallisation

La spec documente 8 → 7 + 1, à ne pas confondre avec l'ancienne règle 50 → 49 + 1. Ici, huit observations de même clé produisent un cristal de sept et laissent la huitième libre. La même règle remonte les niveaux jusqu'à L7. L'enrichissement continu est CANDIDAT.

## Capsule et Épitagores

Recherche faite dans le dépôt, le README et la reconstruction du 17 novembre 2026 : le mot « capsule » n'apparaît pas. Le mot « Épitagore » non plus. La spec parle des « 12 de Pythagore » et dit que leur sens originel reste indéterminé. Elle interdit de confondre les triplets, la grille 12×12 et l'expérience à 12 sommets.

La capsule est donc un écrin qui affiche la phase, le coup et la cellule Z144. Le propriétaire doit encore préciser sa fonction, ce qu'elle contient d'autre, et si sa place est le cœur, le sommet ou ailleurs. Elle est au centre du cercle, parce que la page y met l'état courant. Ce placement est un choix de présentation.

Les douze Épitagores sont douze emplacements vides. `configurer` n'existe pas comme remplissage automatique : on édite le texte dans la configuration, et il reste CANDIDAT. Le passage de la dimension 6 à la dimension 7 est l'énoncé du propriétaire, pas une carte calculée. Aucune correspondance avec la grille ou avec les 12 paires nord-sud n'est posée comme une identité.

## Graine et base 39

`exporter_graine()` rend la version, le tic, l'évolution, la configuration et une empreinte. `reconstruire_depuis_graine()` rejoue le tic et retrouve le même instantané. Une empreinte fausse, ou une évolution qui ne correspond pas au tic, est refusée. La Libellule peut signaler la graine corrompue.

Recherche de `base39`, `base 39`, `b39` et `BASE39` : aucun encodeur. Les chaînes « b39… » du dépôt sont des empreintes hexadécimales. L'alphabet par défaut, à confirmer par le propriétaire, est `0-9`, `A-Z`, puis `-`, `_` et `.`. L'empreinte et la graine sérialisée s'affichent en base 39. Une signature base 39 est plus courte que la même valeur en hexadécimal. Observation, sans conclusion : 39 = 3 × 13.

## Base de numération

Voir les pistes ouvertes, plus bas.

## Page

Il n'y a pas de page moteur dans la façade. Le fichier `index.html` à la racine est une application compilée dont les secteurs sont 01 NodIA, 02 BuroIA, 03 OuvrIA, 04 Dispatch, 05 QueenIA, 06 ControlIA, plus la porte. 02 BuroIA est un quartier narratif, pas le moteur. Cette page-ci est isolée : `moteur/page/index.html`. Elle ne change ni le routage, ni la configuration serveur, ni les autres pages.

Le cercle des 30 pierres est au centre. La pyramide de quartz, la capsule, le temple, Polybrutus, les Épitagores, les six roues et la colonie s'organisent autour ou dedans. Le style est mégalithique : pierre, lichen, terre, ciel nocturne. Le néon marque l'onde de remplacement, pas un décor égyptien.

Le son utilise la Web Audio API, sans fichier externe. Il ne démarre qu'après le bouton « Écouter les ondes ». Deux oscillateurs, 2400 Hz et 2401 Hz, donnent le battement de 1 Hz. Un délai fait le tour des pierres, avec un panoramique selon la pierre active. Le volume par défaut est bas. Un curseur et un bouton couper sont là. La page fonctionne sans son. En cas d'essai d'anomalie, le second oscillateur se décale : c'est un signe artistique de dissonance, pas une mesure.

## Réglages

Toutes les valeurs éditables sont dans `moteur/moteur.config.json`, chargé au démarrage Python. Les constantes du code sont les défauts. Un schéma vérifie les types et les bornes. Une valeur invalide est refusée avec un message, et la dernière configuration valide reste en place.

Sur la page, le panneau « Réglages du moteur » est repliable et groupé. Il applique les changements dans le navigateur. Réinitialiser, exporter (téléchargement JSON) et importer sont locaux. La persistance est `localStorage`, clé `antmux-moteur-config-v1`. Aucune écriture serveur, aucun endpoint, aucune base dans cette version.

Chaque roue a une vitesse, une position de départ et un état active ou en pause. L'anneau est éditable. On peut ajouter ou retirer une roue (au moins une, au plus douze). Le tic de convergence affiché est recalculé. Les roches, le courant, les fréquences, les graines, le côté du temple, les Épitagores et la règle de cristallisation sont dans le même panneau.

Un composant enregistré plus tard déclare `fragment()` et `schema_fragment()`. Le schéma, donc le panneau, les prend sans qu'on réécrive les autres composants.

### Enregistrement partagé, plus tard, réservé à l'admin

Pas dans cette version. Le jour où le propriétaire l'autorisera séparément, un seul compte admin pourrait écrire la configuration partagée, côté serveur, avec une session authentifiée. Un visiteur ne doit pas pouvoir modifier la configuration des autres. Ce n'est pas à brancher tant que ce go n'est pas donné. Aucun endpoint n'est prévu dans le code actuel.

## Ajouter un élément

1. Créer une classe avec `identifiant`, `ordre`, `au_tic(etat, config)` et `instantane(etat, config)`.
2. Si elle a des réglages, ajouter `fragment()` et `schema_fragment()`.
3. L'enregistrer sur un moteur déjà construit : `moteur.enregistrer(MonElement())`. Les autres composants ne sont pas modifiés.
4. Pour qu'elle soit dans le moteur par défaut, l'ajouter à `tous()` dans `moteur/composants/pieces.py`.

Le noyau ne importe pas les composants un par un. `usine.moteur_nu()` reçoit la liste.

Entre Stonehenge (`ordre` 40) et le cadran (`ordre` 50), `inserer_entre(..., apres="stonehenge", avant="cadran")` place un composant dans le pipeline. C'est le point prévu pour les cristaux de vibration. Il ne contient aucune logique de vibration.

## Extensions prévues

Cristal de vibration : trente cristaux individuels, un par pierre de Stonehenge, chacun entre sa roche et le cadran, pour que chaque tic produise des vibrations différentes (à définir par le propriétaire). L'interface `EmplacementCristalVibration` est indexable de 0 à n−1. Sur la grille idéale, n = 30. `transformer` lève `NotImplementedError`. Aucune vibration n'est calculée. Si le nombre de positions change, il y a un emplacement par position, et l'alerte de grille rappelle que le dessin de 30 était celui de la grille idéale.

Roches à installer : le cercle n'est pas déclaré complet. Les emplacements `reservee` et l'ajout d'une position sont là. Le propriétaire dira lesquelles manquent. Par défaut, les 30 de la grille idéale sont installées.

Lecteur de structures : interface vide. Elle recevra plus tard des relevés, des plans, des mesures ou des modèles, et produira une lecture via le moteur. Aucune logique de décodage, aucune donnée de pyramide.

## Pistes ouvertes

Bases de numération anciennes à explorer en lien avec l'encodage base 39 des empreintes et les signatures raccourcies. Le propriétaire pensait à la base 20, qu'il n'a pas encore étudiée. Repères historiques : la numération égyptienne hiéroglyphique était décimale (base 10, non positionnelle) ; la base 20 est celle des Mayas ; la base 60 est celle des Babyloniens.

Autres suites, hors de cette charpente : femtoseconde à 240,1 Hz, MAGIC_SCORE, Pell, ZELSTÉRÉOS comme autre Z, couple ou force d'un rotor. Le README du dépôt et la reconstruction restent la source. On n'en fait pas des faits physiques.

## Lancer

Depuis la racine du dépôt :

```text
python -m unittest moteur.test_moteur -v
python -m moteur.generer_page
```

Ouvrir `moteur/page/index.html` (fichier local ou petit serveur statique). Python 3.11 ou plus récent, bibliothèque standard seulement. Node sert à la parité du client de la page ; le test l'appelle s'il est présent dans l'environnement.

## Arborescence

```text
moteur/
  __init__.py          finalité, concept, graine
  constantes.py        valeurs par défaut étiquetées
  calculs.py           fonctions pures
  base39.py            encodeur et décodeur
  config.py            schéma, validation, fichier
  etat.py              état partagé
  noyau.py             Moteur, graine, pipeline
  extensions.py        interfaces vides
  usine.py             moteur_nu, moteur_par_defaut
  moteur.config.json   données, sans rebuild
  composants/
    pieces.py          composants livrés et tous()
  page/
    gabarit.html
    client.js          rejoue les règles dans le navigateur
    index.html         page générée
  test_moteur.py
  generer_page.py
  README.md
```
