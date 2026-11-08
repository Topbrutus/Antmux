# Horloge de la Vie — reprise contrôlée sur Antmux
**Date de checkpoint :** 2026-11-08  
**Décision de Topbrutus :** reconstruire l'Horloge de la Vie dans le dépôt `Topbrutus/Antmux`.  
**Statut de ce document :** fondation de reprise / inventaire vérifié dans GitHub; **aucune modification fonctionnelle, aucun déploiement**.  
**Base de lecture :** `main` à `447cf97c9ebd33d2473130ef484d880f3eafac63`.

## 1. Ne pas repartir de zéro
Le laboratoire possède déjà une Horloge de la Vie. Aucune suppression, réinitialisation, duplication de Queen, remplacement de vitrine ou migration destructrice n'est autorisée par ce document. Les développements progressent sur branche dédiée; `main`, les données et le serveur restent inchangés avant audit et validation.

## 2. Inventaire vérifié du dépôt
| Pièce | Chemin | Rôle documenté |
|---|---|---|
| Portail public | `laboratoire/index.html` | Lien vers `laboratoire/embryon-x72/`. |
| Horloge X72 existante | `laboratoire/embryon-x72/{index.html,app.js,styles.css}` | Affiche le VisualState de la Queen. |
| Noyau historique | `laboratoire/embryon-x72/core/ANTMUX_X72_LIFE_V02.py` | Référence de calcul, **pas** serveur live du navigateur. |
| Queen serveur | `deploy/x72-shared-queen/app/server.py` | Runtime, persistance, relations, états, API et WebSocket. |
| Frontend partagé | `deploy/x72-shared-queen/frontend/` | Vue serveur X72 à synchroniser et tester, pas autorité autonome. |
| Contrat d'intégration | `deploy/x72-shared-queen/NEXT_MODULE_INTEGRATION.md` | Frontend = consommateur sans tick officiel local. |
| Adaptateur d'observation | `deploy/x72-shared-queen/observation_adapter/` | Lecture et corrélation des observations sans mutation. |
| Horloge septénaire | `generator/` | Horloge autonome fondée sur UTC; distincte du tick Queen. |
| Monde C3RUTUS | `laboratoire/c3rutus/life-clock.mjs` | Battement numérique 240,1 + poussière, cycle 546; distinct du tick X72. |
| Parazone | `laboratoire/parazone-x72-d13-v2/` | Visualisations et cycles; à préserver. |

**Attention aux couches temporelles :** `generator/` dérive des phases à partir de l'UTC; `life-clock.mjs` échantillonne une animation de C3RUTUS; `QueenCore.tick_count` est l'autorité X72. Elles ne doivent jamais être confondues.

## 3. Chaîne d'autorité non négociable
```text
QueenCore serveur et persistance
       ↓
GET /api/health · /api/telemetry · /api/state · /api/events · /api/report
       ↓
WS /ws (VisualState partagé)
       ↓
Horloge de la Vie : rendu, tableaux, couleurs, preuves, journal
```
- Aucun `QueenCore`, événement de mutation, horodatage cognitif inventé ou tick officiel synthétique en JavaScript.
- À la déconnexion : afficher `CORE DISCONNECTED` ou `STALE`, garder le dernier état connu, reconnecter sans reset.
- Les valeurs visuelles peuvent être interpolées pour le rendu uniquement; ne jamais les réinjecter au serveur comme preuves.
- La visualisation n'invente jamais les valeurs absentes.
- Conserver séparation public lecture seule / commande privée authentifiée.
- Les secrets, réglages d'infrastructure privée et fichiers personnels restent **hors du dépôt public**.

## 4. Reconstruction incrémentale proposée
### Étape A — Baseline vérifiable (première opération de code)
1. Comparer `laboratoire/embryon-x72/app.js` et `deploy/x72-shared-queen/frontend/app.js` et établir la source de synchronisation.
2. Relever les champs réellement rendus et les champs présents dans des réponses `VisualState` de test **sans toucher au live**.
3. Exécuter, en environnement isolé, les contrôles existants : `deploy/x72-shared-queen/tests/check_frontend_authority.py`, `tests/run_server_tests.py` (adapte les chemins selon leur usage réel), tests JS de C3RUTUS.
4. Produire un état de référence horodaté : tests passés/échoués, schémas connus, écarts et captures, avec `HEAD` et empreintes.

### Étape B — Faire évoluer **la vue existante**, petit changement par petit changement
- Garder le cadran X72 actuel et ses sept synapses; ajouter les éléments manquants par composants lisibles et accessibles.
- Contrôler les états `FRESH / STALE / UNKNOWN`, les modes `READY / FAULT / REPAIR` et les erreurs WebSocket, sans casser l'existant.
- Préparer les affichages de cycles 6/7/13 et 546 comme **mesures dérivées identifiées**, sans les confondre avec la fréquence réelle d'une entité.

### Étape C — Besoins à spécifier avec Topbrutus avant de les brancher
- Registre des cristaux et ordre d'insertion (source de vérité et schéma à déterminer).
- Couleurs configurables par la base de données, choix via palette ou saisie, sans valeur inventée côté navigateur.
- Intégration du Brotoculateur **dans** l'Horloge (lectures, provenance, statuts), à condition de définir API, contrats et droits.
- Route candidate `A → B → Z → Cristal → Z → A → B → Z` : architecture de recherche; aucune connexion ou fonction n'est réputée implémentée ici.
- Préserver NinoScreen, Papillon 144 et les autres laboratoires, sans modification implicite.

## 5. Définition de « terminé » pour la première tranche
- Toute modification ciblée est additive et réversible.
- Tests de syntaxe et de non-régression PASS selon preuves exécutées, sans promettre de résultat à l'avance.
- Parité vérifiée entre les deux copies frontend si nécessaire.
- Multi-client et reconnexion vérifiés; aucun deuxième QueenCore.
- Résultat documenté : branche, `HEAD`, fichiers, tests, captures, inconnues et reprise.
- **Aucune action live, migration de base, publication ou merge automatique** sans autorisation de Topbrutus.

## 6. Prochaine action
Commencer par **l'étape A, audit d'intégrité du frontend et de la source de VisualState**. Puis proposer un premier changement visuel isolé sur la branche de travail, avec prévisualisation et test, avant toute fusion.

## 7. Provenance et statut
SOURCE : fichiers GitHub publics du dépôt `Topbrutus/Antmux` au HEAD indiqué.  
SOURCE : contrats de continuité `Topbrutus/MonCerveauGPT/brain/robots/astra/continuity/` (2026-11-03).  
INCONNU : état runtime actuellement servi par le VPS, statut de toutes les endpoints en ligne et écarts de données live; **non testés par ce document**.  
DÉCISION : le chantier se poursuit dans Antmux; la compilation et le déploiement n'ont pas été lancés.
