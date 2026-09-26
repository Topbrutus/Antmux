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
