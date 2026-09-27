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

## Panneaux repliables et lettrage local

Chaque panneau de travail visible dispose maintenant de contrôles `−`, `+` et `REPLIER / DÉPLIER`.

- `−` et `+` modifient uniquement le lettrage du panneau concerné.
- plage de lettrage : 75 % à 160 %, par pas de 10 %;
- `REPLIER` réduit le panneau à sa barre de titre;
- `DÉPLIER` restaure immédiatement son contenu;
- le cœur du moteur et les commandes maîtres sont également repliables;
- l'état est mémorisé localement séparément pour chaque vue BRUTUS avec `BRUTUS_PANEL_WORKSPACE_V1:SCREEN_<n>`.

Le pliage et le zoom sont des préférences d'affichage locales : ils ne modifient ni la chaîne de preuve ni l'état scientifique partagé entre les cinq écrans.

## Bureau BRUTUS — gestionnaire de fenêtres V2

Le bouton `BUREAU` active un gestionnaire de fenêtres libre au-dessus des cinq vues sans déplacer le noyau réel.

Build vérifiable : `BRUTUS_WINDOW_MANAGER_V2`.

Dans ce mode :
- chaque panneau préparé devient une fenêtre indépendante;
- clic sur une fenêtre = focus + remontée au premier plan;
- la barre de titre sert de poignée de déplacement;
- double-clic sur la barre de titre = maximiser / restaurer;
- huit poignées redimensionnent par les quatre bords et les quatre coins;
- `LOCK / UNLOCK` verrouille ou libère position et dimensions;
- `▁` réduit une fenêtre en icône 88 × 62 px;
- `□ / ▣` maximise ou restaure une fenêtre;
- les icônes restent déplaçables et un clic les restaure;
- une fenêtre ou une icône peut être glissée sur `SCREEN 1` à `SCREEN 5` pour changer d'écran;
- la grille peut être réglée sur `OFF / 8 / 16 / 32 px`;
- `ALT` permet un placement libre sans snap;
- `MAGNET ON / OFF` contrôle l'aimantation aux bords et aux autres fenêtres;
- l'inspecteur `X / Y / L / H / SCREEN` permet un placement numérique exact;
- `CENTRER` place précisément la fenêtre sélectionnée au centre;
- les flèches déplacent une fenêtre sélectionnée de 1 px;
- `SHIFT + flèche` utilise un grand pas; `CTRL/CMD + flèche` ajuste la taille;
- `RANGER` remet les fenêtres dans leur répartition canonique;
- un arrangement peut être enregistré sous un nom puis rouvert comme module de travail.

Compatibilité conservée :
- état partagé : `BRUTUS_DESKTOP_WORKSPACE_V1`;
- bus de synchronisation : `BRUTUS_DESKTOP_WORKSPACE_V1`;
- les arrangements V1 existants sont normalisés vers le modèle V2 sans changer de clé de stockage.

Le transfert ou le redimensionnement d'une fenêtre modifie uniquement l'interface. Il ne change ni la topologie D13, ni la chaîne de preuve, ni la propriété des ressources physiques. L'écran 3 reste le propriétaire du noyau dans l'architecture actuelle.
