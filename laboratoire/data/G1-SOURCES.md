# ANTMUX — REGISTRE DES SOURCES G1-a / G1-b / G1-c

## Règle

Ce fichier enregistre les sources documentaires autorisées comme point de départ du corpus G1.

L'inscription d'une source dans ce registre ne signifie pas que toutes les valeurs qu'elle contient sont automatiquement validées.

Chaque mesure devra ensuite être vérifiée dans la source elle-même avant d'être classée `PUBLISHED_MEASUREMENT`.

Aucune valeur numérique G1 ne doit être copiée dans ce fichier.

---

## SRC-G1-REISNER-1942

**Auteur :** George A. Reisner

**Titre :** A History of the Giza Necropolis, Volume I

**Publication :** Cambridge, Harvard University Press

**Année :** 1942

**Partie prioritaire pour G1 :**

Chapter VI, notamment pp. 125–141.

**Type :**

Publication archéologique historique / rapport de fouille et synthèse.

**Utilisation prévue :**

* sous-structures de G1-a ;
* sous-structures de G1-b ;
* sous-structures de G1-c ;
* chambres ;
* antichambres ;
* passages ;
* excavations ;
* relations architecturales.

**Statut :**

`SOURCE_REGISTERED`

**Règle :**

Toute valeur attribuée à Reisner devra être relue à la page correspondante avant import dans le jeu de données.

---

## SRC-G1-PETRIE-1883

**Auteur :** W. M. Flinders Petrie

**Titre :** The Pyramids and Temples of Gizeh

**Première édition :** London, Field and Tuer

**Année :** 1883

**Type :**

Relevé métrologique historique.

**Utilisation prévue :**

* angles ;
* orientations ;
* dimensions ;
* comparaisons avec les relevés ultérieurs.

**Statut :**

`SOURCE_REGISTERED`

**Règle :**

Les unités historiques de Petrie doivent être conservées telles que publiées avant toute conversion SI.

---

## SRC-G1-MARAGIOGLIO-RINALDI-1965-TEXT

**Auteurs :**

Vito Maragioglio
Celeste Ambrogio Rinaldi

**Titre :**

L'Architettura delle Piramidi Menfite 4 — Le Grande Piramide di Cheope — Testo

**Publication :**

Tipografia Canessa, Rapallo

**Année :**

1965

**Type :**

Étude architecturale et métrologique.

**Utilisation prévue :**

* reconstruction des bases ;
* niveaux de fondation ;
* passages ;
* pentes ;
* dimensions architecturales ;
* comparaison avec Reisner et Petrie.

**Statut :**

`SOURCE_REGISTERED`

**Règle :**

Une dimension reconstruite par Maragioglio & Rinaldi doit rester explicitement distinguée d'une mesure directe de vestige.

---

## SRC-G1-MARAGIOGLIO-RINALDI-1965-PLATES

**Auteurs :**

Vito Maragioglio
Celeste Ambrogio Rinaldi

**Titre :**

L'Architettura delle Piramidi Menfite 4 — Le Grande Piramide di Cheope — Tavole

**Publication :**

Tipografia Canessa, Rapallo

**Année :**

1965

**Type :**

Plans et planches architecturales.

**Utilisation prévue :**

* validation graphique ;
* plans ;
* coupes ;
* géométrie ;
* localisation d'une dimension citée dans le texte.

**Statut :**

`SOURCE_REGISTERED`

**Règle :**

Toujours conserver le numéro de planche lorsqu'une mesure provient directement d'une planche.

---

## SRC-G1-HAWASS-1987

**Auteur :**

Zahi A. Hawass

**Titre :**

The Funerary Establishments of Khufu, Khafra and Menkaura during the Old Kingdom

**Type :**

Thèse de doctorat

**Institution :**

University of Pennsylvania

**Année :**

1987

**Section pertinente :**

Étude des pyramides secondaires GI-a, GI-b et GI-c du complexe de Khéops.

**Utilisation prévue :**

* synthèse des dimensions publiées ;
* confrontation des sources antérieures ;
* contexte architectural ;
* identification des références utilisées par l'auteur.

**Statut :**

`SOURCE_REGISTERED`

**Règle :**

Lorsqu'Hawass reprend une valeur de Reisner ou Maragioglio & Rinaldi, conserver la provenance originale et ne pas transformer Hawass en source primaire de cette valeur.

---

## SRC-G1-DIGITAL-GIZA

**Institution :**

Digital Giza / Harvard University

**Type :**

Catalogue numérique académique.

**Objets concernés :**

* G I-a
* G I-b
* G I-c
* plans associés ;
* publications associées ;
* documents d'excavation associés.

**Utilisation prévue :**

* identification documentaire ;
* bibliographie ;
* plans ;
* liens entre monument et publication ;
* contrôle de nomenclature.

**Statut :**

`SOURCE_REGISTERED`

**Règle :**

Digital Giza peut servir de catalogue et de point d'accès documentaire.

Lorsqu'une mesure provient d'un ouvrage historique accessible via Digital Giza, l'enregistrement de mesure doit citer l'ouvrage historique lui-même comme source de la valeur.

---

# Hiérarchie de provenance

Pour une valeur donnée :

1. page ou planche originale consultée ;
2. publication archéologique contenant directement la valeur ;
3. publication secondaire citant la valeur ;
4. catalogue numérique donnant accès à la documentation.

Le niveau le plus proche de la mesure originale doit être privilégié.

---

# Conflits

Si Reisner, Petrie, Maragioglio & Rinaldi ou Hawass donnent des valeurs différentes :

* conserver chaque valeur ;
* ne pas effectuer de moyenne automatique ;
* attribuer un `conflict_group` ;
* documenter la nature du relevé ;
* comparer seulement ensuite.

Une divergence entre sources est une donnée du laboratoire, pas une erreur à effacer.

---

# Verrou d'import G1

Aucune valeur G1-a, G1-b ou G1-c ne peut devenir `PUBLISHED_MEASUREMENT` avant que soient connus :

* la source ;
* la page ou planche lorsque disponible ;
* le contexte de mesure ;
* l'unité originale ;
* le statut direct / reconstruit / estimé ;
* les conflits connus.
