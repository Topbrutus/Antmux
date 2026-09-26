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
