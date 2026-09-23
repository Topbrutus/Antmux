# NOYAU DYNAMIQUE X72 — page publique

URL publique conservée :

`https://antmux.com/laboratoire/parazone-x72-d13-v2/`

Le chemin historique reste identique pour préserver les liens existants, mais son contenu est remplacé par la visualisation du **Noyau dynamique X72 v0.2**.

## Source d'état

La page se connecte en lecture seule au Queen Server existant :

- WebSocket : `/laboratoire/embryon-x72/ws`
- source attendue : `QUEEN_SERVER_V0_2`
- état du noyau : `VisualState.noyau_runtime.noyau`
- autorité attendue : `NOYAU_ENGINE_HEADLESS`

La page ne crée aucun tick local et n'envoie aucune mutation au serveur.

## Visualisation

- autoroutes dynamiques gauche / droite ;
- trois passages centraux obligatoires `C1`, `C2`, `C3` ;
- SOURCE, B1, B2, B3 et SORTIE ;
- entrée et sortie explicites du premier bassin ;
- inflow / outflow / crystal_index ;
- cristaux actifs ;
- sondes d'analyse des signaux serveur ;
- quatre géométries de rendu local : HELIX, TORUS, GRID, OBSIDIAN.

Les quatre vues structurelles ne modifient pas le monde du serveur : elles changent seulement le rendu navigateur.

## Garde-fou

Si le Queen Server est joignable mais ne publie pas encore `noyau_runtime`, la page affiche explicitement **NOYAU EN ATTENTE DU DÉPLOIEMENT SERVEUR**. Aucun état fictif n'est généré.
