# BRUTUS — squelette technique hiérarchique T1

URL publique conservée :

`https://antmux.com/laboratoire/parazone-x72-d13-v2/`

Le chemin public reste inchangé. La page actuelle est une coquille technique locale destinée à rendre les connexions, mesures, preuves et versions de topologie explicitement observables.

## Invariants conservés

Cette évolution ne reconstruit pas Antmux et ne modifie pas les chemins fonctionnels existants. Elle ajoute uniquement une couche descriptive autour du squelette courant.

- T0 reste la référence visuelle figée.
- Le seul chemin T1 actif reste `SOURCE-00 -> FLOW-01 -> B1.INPUT`.
- B1 reste `IDENTITY_CAPTURE`.
- B2, B3, GATE-01, CRYSTAL-01, FLOW-02..05 et les retours locaux restent distincts du moteur serveur; aucune logique scientifique candidate n'est inventée pour eux.
- La fréquence reste une configuration locale explicite; elle n'est pas déduite du moteur serveur.
- `MOTOR-BRIDGE-01` ouvre uniquement le WebSocket public existant `/laboratoire/embryon-x72/ws` en lecture seule.
- Le pont accepte seulement `QUEEN_SERVER_V0_2` + `NOYAU_ENGINE_HEADLESS` + `ANTMUX-X72-NOYAU-DYNAMIC-v0.2` avant d'afficher l'état moteur.
- Aucune écriture serveur, aucun endpoint de mutation et aucune nouvelle Queen ne sont ajoutés.
- Aucune formule scientifique candidate n'est branchée.

## Contrat de topologie

La topologie de référence est déclarée sous la forme `G_REFERENCE` avec :

- `MODULE_ID`
- `INSTANCE_ID`
- `PARENT_ID`
- `LEVEL`
- `PORT`
- `EDGE_ID`
- `EDGE_TYPE = INTRA_LEVEL | INTER_LEVEL`
- `FROM`
- `TO`
- `TOPOLOGY_VERSION`

Version actuelle :

`ANTMUX-TOPOLOGY-T1.0.0`

Le graphe racine est `G_ANTMUX`. Les composants SOURCE-00, B1, B2, B3, GATE-01 et CRYSTAL-01 sont des unités de niveau 1 rattachées à ce graphe.

Chaque module peut plus tard recevoir une structure interne sans modifier son interface externe. Aucun sous-module interne n'est créé aujourd'hui et aucun nombre de sous-modules n'est imposé.

Exemple futur autorisé :

`B1` peut rester une unité vue depuis le niveau supérieur tout en devenant parent d'un graphe interne `G_B1`.

## Référence et candidat

La page distingue explicitement :

`G_REFERENCE`

`G_CANDIDATE`

`DELTA_G`

État initial volontaire :

`G_CANDIDATE = NONE`

`DELTA_G = NONE`

Une future topologie candidate devra être comparée à la référence avant toute promotion. La référence ne doit jamais être écrasée silencieusement.

## Validation structurelle

Le navigateur valide la cohérence déclarative de `G_REFERENCE` :

- unicité des `MODULE_ID` ;
- unicité des `EDGE_ID` ;
- présence des `INSTANCE_ID` ;
- cohérence `PARENT_ID` / `LEVEL` ;
- type d'arête autorisé ;
- existence des extrémités `FROM` et `TO` ;
- port explicite pour toute arête utilisable.

Les retours historiques `RETURN-L01` et `RETURN-R01` restent déclarés `DISCONNECTED` avec liaison de port `UNRESOLVED`. Ils ne peuvent donc pas être interprétés comme connexions actives.

Cette validation est une preuve de cohérence logicielle, pas une preuve scientifique.

## Registre de continuité

Chaque mesure T1 conserve maintenant :

- `QUI`
- `ETAT`
- `TICK`
- `AVANT`
- `APRES`
- `TOPOLOGY_VERSION`
- `RESULTAT`
- `PROOF_REF`

Le paquet de preuve T1 utilise le schéma `BRUTUS_T1_TRANSPORT_V3` et référence explicitement la topologie, le module, l'instance, le parent, le niveau, le port, l'arête, son type et ses extrémités.

## Règle

`AUCUNE CONNEXION INVISIBLE`

Workflow visé pour une future variation structurelle :

`STRUCTURE -> VARIATION -> MESURE -> COMPARAISON -> PREUVE -> GARDE ou REJET`

Aucune variation structurelle n'est appliquée dans cette version.


## MOTOR-BRIDGE-01 — vieux moteur branché

Le noyau dynamique déjà existant dans `deploy/x72-shared-queen/app/noyau_runtime/` reste le moteur serveur. La page PARAZONE ne le duplique pas.

Chemin:

`NoyauEngine -> QueenCore.visual_state() -> /ws -> MOTOR-BRIDGE-01 -> anneau visuel + télémétrie`

Le pont affiche uniquement des champs déjà produits par le moteur:
- tick, world, speed, coherence;
- node_signals SOURCE / B1 / B2 / B3 / SORTIE;
- basin inflow / outflow / crystal_index;
- whole_h256.

Les phases gauche/droite du moteur déplacent l'anneau visuel central. Ce mouvement est une représentation logicielle de l'état du moteur, pas une mesure physique.

La sortie audio reste locale dans `OUTPUT-ADAPTER-01` sur cette même page et conserve son armement manuel.
