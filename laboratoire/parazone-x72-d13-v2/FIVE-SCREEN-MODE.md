# BRUTUS — MODE 5 ÉCRANS

Architecture: 1 CORE -> 5 VIEWS -> 1 STATE -> 1 CLOCK -> 1 PROOF CHAIN.

Écran 1: MASTER — moteur et vue principale.
Écran 2: ANALYSIS — mesures, moniteurs et qualité.
Écran 3: OPERATOR — presets, table, microphone, générateur et sortie audio. Propriétaire du noyau.
Écran 4: CONTROL — T1 à T5, connexions et preuves.
Écran 5: SETTINGS — état partagé, topologie, cadrans et contrôles maîtres.

Lanceur: five-screens.html.

Ordre conseillé:
1. Ouvrir le lanceur.
2. Ouvrir l'écran 3 en premier.
3. Ouvrir les quatre autres vues.
4. Déplacer chaque fenêtre sur son écran physique.
5. Autoriser les pop-ups pour antmux.com si nécessaire.

Bus partagé: BRUTUS_FIVE_SCREEN_V1.
Les commandes des vues sont relayées au noyau; le noyau renvoie T1-T5, preuves, sampler, timebase, micro, générateur, sortie audio, table, preset et état maître.

START / PAUSE / MASTER STOP sont disponibles dans la barre supérieure de chaque vue.
MASTER STOP coupe la session et la sortie audio, sans effacer les preuves T1 déjà acquises.

index.html reste le cockpit complet mono-fenêtre.


## Placement automatique sur les moniteurs physiques

Le lanceur propose maintenant `DÉTECTER + PLACER LES 5`.

Quand l'API Window Management du navigateur est disponible et autorisée:
1. les moniteurs physiques sont détectés;
2. chaque vue BRUTUS est associée à un moniteur;
3. les cinq fenêtres sont ouvertes, déplacées et redimensionnées;
4. la correspondance est mémorisée dans `BRUTUS_SCREEN_PLACEMENT_V1`.

Le tableau `PLACEMENT PHYSIQUE` permet de modifier manuellement chaque correspondance avant le prochain lancement.

Si le navigateur bloque les pop-ups, le lanceur indique combien de fenêtres ont réellement été ouvertes. Il faut alors autoriser les pop-ups pour antmux.com et relancer. Si l'API multi-écrans n'est pas disponible, les cinq fenêtres restent utilisables avec placement manuel.


## Auto-fit individuel à 100 % navigateur

Chaque vue multi-écrans possède son propre profil de densité afin de rester lisible avec le zoom du navigateur à 100 %:
- MASTER: cible 108 % interne;
- ANALYSIS: cible 100 % interne;
- OPERATOR: cible 90 % interne;
- CONTROL: cible 108 % interne;
- SETTINGS: cible 108 % interne.

Le fit se recalcule automatiquement au chargement, après synchronisation et lors d'un redimensionnement. Le badge supérieur affiche la valeur active sous la forme `FIT n%`.

## Panneaux minimisables et lettrage local

Chaque panneau de travail visible dispose de contrôles `−`, `+` et `REPLIER`.

- `−` et `+` modifient uniquement le lettrage du panneau concerné.
- plage de lettrage : 75 % à 160 %, par pas de 10 %;
- `REPLIER` retire complètement le panneau de sa grille et le transforme en icône flottante;
- l'icône est déplaçable avec un semi-snap de 16 px; un clic la restaure; aucune rangée fantôme n'est conservée.
- le cœur du moteur et les commandes maîtres sont également minimisables;
- l'état minimisé et la position de l'icône sont mémorisés localement séparément pour chaque vue BRUTUS avec `BRUTUS_PANEL_WORKSPACE_V1:SCREEN_<n>`.

La minimisation et le zoom sont des préférences d'affichage locales : ils ne modifient ni la chaîne de preuve ni l'état scientifique partagé entre les cinq écrans.

## Bureau BRUTUS — cartes libres multi-écrans

Le bouton `BUREAU` active une couche de travail libre au-dessus des cinq vues sans déplacer le noyau réel.

Dans ce mode :
- chaque panneau préparé devient une carte indépendante;
- la barre de titre sert de poignée de déplacement;
- le coin inférieur droit redimensionne la carte;
- position et dimensions se recalent sur une grille semi-snap de 16 px;
- le bouton `▁` réduit une carte en icône 88 × 62 px;
- les icônes restent déplaçables et se recalent elles aussi sur la grille;
- un clic sur une icône restaure sa carte;
- une carte ou une icône peut être glissée sur `SCREEN 1` à `SCREEN 5` pour changer d'écran;
- `RANGER` remet les cartes dans leur répartition canonique;
- un arrangement peut être enregistré sous un nom puis rouvert comme module de travail.

État partagé du bureau : `BRUTUS_DESKTOP_WORKSPACE_V1`.
Bus de synchronisation du bureau : `BRUTUS_DESKTOP_WORKSPACE_V1`.

Le transfert d'une carte change son emplacement d'interface, pas la propriété des ressources physiques. Le noyau reste propriétaire des opérations concernées; une commande déplacée continue de passer par le bus BRUTUS existant. En particulier, l'écran 3 reste le propriétaire du noyau dans l'architecture actuelle.

## Six semi-snaps magnétiques

Le bureau BRUTUS et les icônes issues de `REPLIER` disposent de six points d'ancrage magnétiques :
haut-gauche, haut-centre, haut-droite, bas-gauche, bas-centre et bas-droite.

- rayon d'aimantation : environ 92 px;
- hors aimant, le placement normal utilise la grille de 16 px;
- une zone fantôme `SNAP 1` à `SNAP 6` indique l'ancrage actif;
- maintenir `Shift` pendant le déplacement désactive immédiatement les six aimants et la grille 16 px;
- avec `Shift`, la position est conservée au pixel près et reste précise après sauvegarde/rechargement;
- `Shift` désactive également l'arrondi de taille lors d'un redimensionnement en mode BUREAU.

## Gestionnaire de fenêtres V2 — contrôle fin

Le bureau BRUTUS conserve les six ancres magnétiques de la version précédente et ajoute une couche de contrôle fin sans modifier le noyau D13.

Build vérifiable : `BRUTUS_WINDOW_MANAGER_V2`.

Contrôles :
- glisser la barre de titre pour déplacer une fenêtre;
- glisser une fenêtre ou une icône sur `SCREEN 1–5` pour changer d'écran;
- 8 poignées de redimensionnement : N, E, S, O et les quatre coins;
- clic sur une fenêtre : focus et remontée au premier plan;
- `LOCK / UNLOCK` : verrouille ou libère position et taille;
- `□ / ▣` ou double-clic sur la barre de titre : maximiser / restaurer;
- réduction en icône conservée;
- `GRID OFF / 8 / 16 / 32` : pas de grille ou granularité choisie;
- `MAGNET ON / OFF` : active ou désactive les six ancres magnétiques;
- `SHIFT` pendant un drag : placement libre précis, comportement #146 conservé;
- inspecteur `X / Y / L / H / SCREEN` : placement numérique exact au pixel;
- `CENTRER` : recentrage exact de la fenêtre sélectionnée;
- flèches : déplacement de 1 px;
- `SHIFT + flèche` : grand pas selon la grille;
- `CTRL/CMD + flèche` : ajuste largeur ou hauteur;
- `RANGER`, sauvegarde et réouverture des modules restent compatibles.

Compatibilité :
- stockage et bus restent `BRUTUS_DESKTOP_WORKSPACE_V1`;
- les six snaps magnétiques et leur fantôme visuel restent actifs;
- les géométries précises existantes sont conservées;
- déplacer/redimensionner une fenêtre ne change ni la topologie D13, ni la chaîne de preuve, ni la propriété du noyau.

