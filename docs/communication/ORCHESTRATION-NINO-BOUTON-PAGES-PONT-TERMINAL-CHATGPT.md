# Antmux — Mode d’emploi multi-agents pour le bouton Pages de Nino et le pont Terminal ↔ ChatGPT

## 0. Statut, autorité et objectif

- **Autorité finale :** Brutus
- **Orchestrateur Codex :** Reine-LinuxIA / Codex principal
- **Orchestrateur Grok :** Agent Grok 3 — high
- **Racine officielle :** `D:\`
- **Dépôt de documentation :** `Topbrutus/Antmux`
- **Dépôt d’application principal :** `Topbrutus/ninoscreens`
- **But de cette vague :** faire travailler réellement tous les agents sur une priorité unique : transformer le bouton **Pages** de Nino en point d’entrée fiable pour sélectionner une page ChatGPT intégrée, puis établir un pont traçable entre un terminal Antmux et cette page ChatGPT.

Le résultat visé n’est pas seulement un bouton qui change d’écran. Le résultat visé est une chaîne complète :

```text
Terminal Antmux
  ↓ requête identifiée
Pont local D-only
  ↓ cible explicite
Nino → bouton Pages → page/tile ChatGPT sélectionné
  ↓ envoi contrôlé
ChatGPT
  ↓ réponse détectée
Pont local D-only
  ↓ réponse identifiée
Terminal Antmux
```

La vague est réussie uniquement si tout le monde produit un travail réel, distinct et vérifiable, sans collision de fichiers.

---

## 1. État connu à revérifier avant toute action

L’état local sur `D:\` reste la source de vérité d’exécution. GitHub `main` sert de référence documentaire, mais ne doit pas être supposé identique à la branche locale active.

État connu au moment de la rédaction :

- Nino est dans `D:\tools\ninoscreens`.
- La branche locale connue est `feature/d-only-root`.
- Le HEAD local communiqué est `2794585a5b45ea9b367c1f97edf2e1f7ec6fd06a`.
- Les éléments non suivis connus sont `.venv/` et `data/`; ils ne doivent pas être supprimés ni intégrés aveuglément.
- Le bouton distant `Pages` de Nino est actuellement créé dans `app/windows/main_window.py` et appelle la navigation vers la page de tiles courante.
- Le pont ChatGPT existant dans Antmux cible une fenêtre Windows par titre et écran, utilise activation de fenêtre, presse-papiers, `Ctrl+V` et éventuellement `Enter`.
- Ce pont externe doit être conservé intact pendant la première construction du pont interne Nino.
- La cible souhaitée ici est une **page ChatGPT dans Nino**, identifiée sans ambiguïté par un `tile_id` ou un identifiant équivalent, et non une fenêtre Windows choisie seulement par son titre.
- Aucun processus vivant ne doit être arrêté sans ordre explicite de Brutus.
- Aucun push, merge ou force-push ne doit être effectué sans validation explicite de Brutus.

Chaque agent commence par confirmer l’état réel. Si une divergence existe, il l’écrit dans son rapport avant d’agir.

---

## 2. Décision d’architecture pour la première version

### 2.1 Pont interne Nino prioritaire

La première version doit utiliser Nino lui-même comme propriétaire de la page ChatGPT.

Le pont interne doit :

1. connaître le `tile_id` exact de la page ChatGPT;
2. vérifier que ce tile existe et que sa page est chargée;
3. vérifier que la cible ressemble réellement à ChatGPT selon une règle configurable;
4. envoyer le texte par l’API de la page Web intégrée à Nino, de préférence via `QWebEnginePage.runJavaScript` ou l’interface réelle disponible;
5. attendre une réponse stable;
6. retourner cette réponse au terminal avec le même identifiant de requête;
7. échouer fermé si la page, le champ de saisie ou la réponse ne peuvent pas être identifiés de façon sûre.

### 2.2 Pont Windows existant conservé

Le module `ChatGPT.Bridge.psm1` existant reste disponible pour le flux externe historique. Il ne doit pas devenir le mécanisme principal du bouton Pages.

Pendant cette vague :

- ne pas supprimer le pont Windows;
- ne pas renommer ses commandes publiques;
- ne pas casser Jules ou le watcher de résumés;
- ne pas remplacer silencieusement son comportement;
- préparer seulement une future couche d’adaptation si elle est utile.

### 2.3 Transport Terminal ↔ Nino

La première version recommandée utilise une queue locale, observable et D-only.

Structure cible recommandée :

```text
D:\communication\nino-chatgpt-bridge\
  inbox\
  processing\
  outbox\
  failed\
  logs\
  state\
```

Format d’une requête :

```json
{
  "request_id": "REQUEST-000001",
  "job_id": "JOB-000001",
  "created_at": "ISO-8601",
  "source": "terminal-antmux",
  "target_tile_id": 0,
  "mode": "test-only|no-enter|send",
  "message": "texte à envoyer",
  "message_sha256": "empreinte",
  "timeout_seconds": 120
}
```

Format d’une réponse :

```json
{
  "request_id": "REQUEST-000001",
  "job_id": "JOB-000001",
  "status": "completed|blocked|failed|timeout",
  "target_tile_id": 0,
  "response_text": "réponse capturée",
  "response_sha256": "empreinte",
  "started_at": "ISO-8601",
  "completed_at": "ISO-8601",
  "detail": "preuve ou cause exacte"
}
```

Le schéma final peut être ajusté après inspection du code réel, mais les propriétés suivantes sont obligatoires : identifiant unique, cible explicite, mode d’envoi, empreinte anti-doublon, état, horodatage et cause de blocage.

---

## 3. Comportement attendu du bouton Pages

Le bouton **Pages** doit rester compréhensible pour Brutus et ne pas casser la navigation existante.

Comportement cible :

1. un clic sur **Pages** ouvre une vue ou un panneau `PagesBridgeWorkspace`;
2. cette vue affiche les pages et tiles disponibles;
3. chaque tile affiche au minimum : numéro, titre, URL ou origine, état de chargement et rôle éventuel;
4. Brutus peut désigner un tile comme **ChatGPT cible**;
5. la sélection est persistée dans la session Nino;
6. l’interface affiche clairement : `AUCUNE CIBLE`, `CIBLE PRÊTE`, `ENVOI`, `ATTENTE RÉPONSE`, `RÉPONSE REÇUE`, `BLOQUÉ`;
7. un bouton de test vérifie la cible sans envoyer de message;
8. un bouton `NoEnter` ou équivalent prépare/colle le message sans l’envoyer lorsque cette méthode est utilisée;
9. un envoi réel exige une cible unique et valide;
10. la vue affiche le dernier `request_id`, le dernier statut et la cause exacte en cas d’échec.

Le bouton ne doit jamais sélectionner silencieusement le premier tile ChatGPT trouvé si plusieurs tiles sont candidats.

---

## 4. Contrat d’interface entre les deux Journaliers Codex

Les deux Journaliers travaillent en même temps dans des worktrees séparés. Ils ne modifient aucun fichier commun.

### JOURNALIER-01 — UI Pages et sélection de cible

Périmètre réservé :

- `app/windows/main_window.py`
- `app/widgets/pages_bridge_workspace.py` — nouveau fichier recommandé
- `app/widgets/page_matrix.py` seulement si nécessaire
- `app/state.py` seulement si nécessaire
- `app/session_store.py` seulement si nécessaire
- tests UI associés dans un nouveau fichier dédié

Il ne modifie pas `app/bridge/`.

### JOURNALIER-02 — moteur du pont Terminal ↔ ChatGPT

Périmètre réservé :

- `app/bridge/__init__.py`
- `app/bridge/contracts.py`
- `app/bridge/file_queue.py`
- `app/bridge/nino_chatgpt_bridge.py`
- `app/bridge/chatgpt_page_adapter.py`
- tests du pont dans de nouveaux fichiers dédiés

Il ne modifie pas `main_window.py`, `page_matrix.py`, `state.py` ou `session_store.py`.

### Interface obligatoire entre les deux travaux

Le moteur doit exposer une interface indépendante de l’UI, par exemple :

```python
class NinoChatGPTBridge:
    def register_target(self, tile_id: int, page_provider) -> None: ...
    def test_target(self, tile_id: int) -> BridgeResult: ...
    def submit_request(self, request: BridgeRequest) -> BridgeResult: ...
    def poll_response(self, request_id: str) -> BridgeResult: ...
```

L’UI doit appeler cette interface sans connaître les sélecteurs DOM internes.

Le moteur reçoit un `page_provider` ou un objet page fourni par Nino. Il ne recherche pas lui-même une fenêtre Windows globale.

Après les deux commits, Reine-LinuxIA réalise le câblage minimal dans une branche d’intégration distincte.

---

## 5. Organisation complète des agents

### Famille Grok

- **Agent Grok 3 — high :** orchestrateur Grok unique et synthèse continue.
- **Agent Grok 1 — low :** inventaire UI Pages, navigation, état de session et risques de collision.
- **Agent Grok 2 — medium :** analyse technique du pont WebEngine, sélecteurs, cycle d’envoi et capture de réponse.

### Famille Codex

- **Reine-LinuxIA / Codex principal :** orchestrateur Codex unique.
- **JOURNALIER-01 :** UI Pages et sélection explicite de la cible ChatGPT.
- **JOURNALIER-02 :** moteur local Terminal ↔ Nino ↔ ChatGPT.

### Agents spécialisés

- **Jules :** état GitHub, branches, publication future, aucun push sans validation.
- **Hermès :** mémoire Obsidian, décisions, contrats et reprise exacte.
- **GitHub Copilot :** revue indépendante baseline, puis revue des commits et de l’intégration.

Tout le monde produit un rapport distinct dans :

```text
D:\communication\worker-reports\
```

---

# 6. Prompt central — Reine-LinuxIA / Codex principal

```text
Tu es Reine-LinuxIA, orchestratrice Codex principale de la vague Nino Pages ↔ Terminal ↔ ChatGPT.

MISSION
Faire travailler réellement tous les agents sur la priorité unique suivante : transformer le bouton Pages de Nino en panneau de sélection d’une page ChatGPT cible, puis construire un pont D-only permettant à un terminal Antmux d’envoyer une requête à cette page et de récupérer la réponse.

ÉTAT ET RÈGLES
- Source de vérité d’exécution : état local sous D:\.
- Dépôt Nino : D:\tools\ninoscreens.
- Branche locale connue : feature/d-only-root, à revérifier.
- Ne pas supprimer .venv/ ni data/.
- Ne pas arrêter de processus vivant.
- Ne pas supprimer ou modifier le pont Windows existant pendant la première construction.
- Aucun push, merge, reset destructif, clean, force-push ou suppression sur C:\.
- Utiliser les commandes WorkerDock réellement présentes; ne rien inventer.

AVANT ACTION
1. Lire D:\modules\workerdock, sa configuration, ses tests et ses fonctions exportées.
2. Vérifier git status, branche, HEAD, worktrees et fichiers non suivis.
3. Vérifier les fichiers réels du bouton Pages et les classes WebTile/PageMatrix/MainWindow.
4. Vérifier l’existence et l’état du pont ChatGPT Windows historique.
5. Réserver les périmètres de fichiers avant de lancer les Journaliers.

TRAVAIL PARALLÈLE OBLIGATOIRE
- JOURNALIER-01 : UI Pages et sélection de cible, worktree dédié, aucun fichier app/bridge.
- JOURNALIER-02 : moteur du pont et queue D-only, worktree dédié, aucun fichier UI existant.
- Les deux doivent être actifs simultanément avec preuve de leurs workspaces, branches et statuts.

CONTRAT
- Cible explicite par tile_id.
- Aucun choix ambigu.
- Modes test-only, no-enter et send.
- Identifiants request_id/job_id.
- Anti-doublon SHA-256.
- Réponse retournée au terminal avec le même request_id.
- Échec fermé si la page, le champ, le bouton d’envoi ou la réponse ne sont pas identifiables.

INTÉGRATION
Après réception des deux commits locaux :
1. vérifier les rapports;
2. faire relire par Grok 3 et Copilot;
3. créer une branche d’intégration dédiée;
4. câbler l’UI au moteur avec le minimum de modifications;
5. exécuter les tests complets;
6. ne pas pousser sans validation de Brutus.

SORTIE ATTENDUE
Rapporter : état initial, commandes WorkerDock réellement utilisées, workers actifs, PID ou preuve d’activité, worktrees, branches, fichiers réservés, résultats de chaque agent, commits, tests, blocages, état du bouton Pages, état du pont terminal aller-retour et prochaine action unique.
```

---

# 7. Prompt — Agent Grok 1 low

```text
Tu es Agent Grok 1, profil low, travailleur de Agent Grok 3. Tu travailles en lecture seule pendant toute la session.

MISSION
Faire l’inventaire factuel du bouton Pages de Nino et des éléments qui contrôlent pages, tiles, focus, split, session et sélection courante.

À INSPECTER
- D:\tools\ninoscreens\app\windows\main_window.py
- PageMatrix, WebTile, FocusView, DashboardGrid et état de session
- branche active, HEAD, worktrees, fichiers modifiés et non suivis
- comportement actuel du bouton Pages
- persistance de current_page_index, last_selected_tile_id et données de tile
- emplacement où une cible ChatGPT explicite pourrait être stockée
- fichiers que JOURNALIER-01 peut modifier sans collision
- fichiers que JOURNALIER-02 doit éviter

QUESTIONS À RÉPONDRE
1. Que fait exactement le bouton Pages aujourd’hui?
2. Quel est le meilleur point d’insertion pour PagesBridgeWorkspace?
3. Comment sélectionner un tile ChatGPT sans ambiguïté?
4. Comment persister le tile cible sans casser les anciennes sessions?
5. Quels tests UI sont déjà présents et lesquels manquent?

INTERDICTIONS
- Ne modifier aucun fichier.
- Ne créer aucune branche.
- Ne lancer aucune migration.
- Ne pousser aucun commit.
- Ne tuer aucun processus.

LIVRABLE
Écrire D:\communication\worker-reports\GROK-01-INVENTAIRE-NINO-PAGES.md.
Inclure : état réel, diagramme de navigation, fichiers et classes, risques de collision, recommandations minimales, critères d’acceptation et verdict.

Verdict obligatoire : UI PRÊTE À ÊTRE MODIFIÉE, CONTRAT À CORRIGER ou BLOQUÉ.
```

---

# 8. Prompt — Agent Grok 2 medium

```text
Tu es Agent Grok 2, profil medium, travailleur de Agent Grok 3. Tu travailles en lecture seule pendant toute la session.

MISSION
Analyser la manière la plus fiable de relier un terminal Antmux à une page ChatGPT hébergée dans un WebTile Nino, puis de retourner la réponse au terminal.

À INSPECTER
- classe WebTile et accès réel à QWebEngineView/QWebEnginePage
- possibilité d’utiliser runJavaScript
- cycle de chargement et changement d’URL
- page ChatGPT authentifiée déjà ouverte dans Nino
- sélection et validation du champ de message
- envoi contrôlé avec modes test-only, no-enter et send
- détection d’une réponse nouvelle liée à request_id
- stabilité de la réponse avant capture
- clics répétés, annulation, timeout, navigation de page et rechargement
- risques de sélecteurs DOM fragiles
- queue locale D-only et anti-doublon

EXIGENCES D’ANALYSE
- Proposer une stratégie d’adaptateur ChatGPT isolée du cœur du pont.
- Prévoir plusieurs sélecteurs configurables, mais échouer fermé.
- Ne pas contourner l’authentification et ne pas stocker de cookie ou secret dans les rapports.
- Distinguer clairement : page prête, message injecté, message envoyé, réponse commencée, réponse stable, réponse retournée.
- Définir une méthode pour ne pas confondre une ancienne réponse avec la nouvelle.

INTERDICTIONS
- Ne modifier aucun fichier.
- Ne créer aucune branche.
- Ne pousser aucun commit.
- Ne déclencher aucun message réel.

LIVRABLE
Écrire D:\communication\worker-reports\GROK-02-ANALYSE-PONT-NINO-CHATGPT.md avec : architecture recommandée, pseudo-code, machine à états, risques, sélecteurs/configuration, tests et verdict.

Verdict obligatoire : PONT INTERNE FAISABLE, PROTOTYPE CONTRÔLÉ REQUIS ou BLOQUÉ.
```

---

# 9. Prompt — Agent Grok 3 high

```text
Tu es Agent Grok 3, profil high, unique orchestrateur Grok. Grok 1 et Grok 2 sont tes travailleurs.

MISSION
Maintenir une synthèse active pendant toute la session et contrôler que la construction Nino Pages ↔ Terminal ↔ ChatGPT reste cohérente, minimale et sans collision.

TRAVAIL
1. Lire les rapports Grok 1 et Grok 2.
2. Vérifier les faits contre l’état local communiqué par Reine-LinuxIA.
3. Formaliser le contrat exact entre JOURNALIER-01 et JOURNALIER-02.
4. Vérifier que les fichiers réservés sont disjoints.
5. Définir les critères d’acceptation des deux commits.
6. Examiner leurs rapports dès qu’ils sont disponibles.
7. Comparer les constats avec la revue Copilot.
8. Signaler toute architecture trop fragile ou dépendante d’un sélecteur unique.
9. Vérifier que le pont Windows historique reste intact.
10. Recommander ou refuser l’intégration.

INTERDICTIONS
- Ne modifier aucun fichier de production.
- Ne pousser ni fusionner.
- Ne devenir ni un deuxième orchestrateur Codex ni un troisième Journalier.

LIVRABLE
Écrire et mettre à jour D:\communication\worker-reports\GROK-03-DECISION-NINO-PAGES-BRIDGE.md.
Inclure : contrat final, matrice de risques, collisions, écarts, critères d’intégration, ordre des tests et verdict.

Verdict obligatoire : INTÉGRATION AUTORISABLE APRÈS TESTS, CORRECTIONS REQUISES ou BLOQUÉ.
```

---

# 10. Prompt — JOURNALIER-01 UI Pages

```text
Tu es JOURNALIER-01, travailleur Codex A. Tu travailles simultanément avec JOURNALIER-02 dans un worktree séparé.

MISSION UNIQUE
Transformer le bouton Pages de Nino en point d’entrée d’une vue de gestion des pages et de sélection explicite d’un tile ChatGPT cible, sans construire le moteur de pont.

BRANCHE ET ISOLATION
- Worktree dédié obligatoire.
- Branche recommandée : worker/journalier-01-nino-pages-ui.
- Vérifier git status, HEAD, worktrees et fichiers non suivis avant écriture.
- Ne modifier aucun fichier sous app/bridge/.

PÉRIMÈTRE AUTORISÉ
- app/windows/main_window.py
- nouveau app/widgets/pages_bridge_workspace.py
- app/widgets/page_matrix.py seulement si nécessaire
- app/state.py seulement si nécessaire
- app/session_store.py seulement si nécessaire
- tests UI nouveaux et dédiés

FONCTIONS ATTENDUES
1. Le bouton Pages ouvre PagesBridgeWorkspace.
2. La navigation existante reste accessible.
3. La vue liste les tiles avec identifiant, titre, URL/origine et état.
4. Brutus peut définir exactement un tile comme cible ChatGPT.
5. La sélection est persistée avec compatibilité ascendante des anciennes sessions.
6. La vue expose un signal ou callback `target_selected(tile_id)`.
7. La vue affiche les états du pont sans implémenter le moteur.
8. La vue prévoit les actions Test cible, NoEnter et Envoyer, mais les branche sur une interface injectée ou des signaux.
9. Aucun choix automatique ambigu.
10. Si le tile disparaît, la cible devient invalide et l’UI le montre.

CONTRAT
Utiliser une interface propre afin que Reine-LinuxIA puisse brancher ensuite NinoChatGPTBridge sans réécrire l’UI.

TESTS
- clic Pages;
- retour à la grille;
- sélection d’un tile;
- remplacement de la cible;
- persistance après sauvegarde/rechargement;
- ancienne session sans target_tile_id;
- cible absente;
- plusieurs tiles ChatGPT;
- signaux Test/NoEnter/Envoyer;
- aucune régression focus, split, fullscreen ou RUN.

COMMIT
Créer au maximum un commit local atomique. Ne pas pousser.

RAPPORT
Écrire D:\communication\worker-reports\JOURNALIER-01-NINO-PAGES-UI.md.
Terminer par DÉBUT DU RÉSUMÉ et FIN DU TERMINAL.

Verdict : PRÊT POUR INTÉGRATION, CORRECTIONS REQUISES ou BLOQUÉ.
```

---

# 11. Prompt — JOURNALIER-02 moteur du pont

```text
Tu es JOURNALIER-02, travailleur Codex B. Tu travailles simultanément avec JOURNALIER-01 dans un worktree séparé.

MISSION UNIQUE
Construire le moteur D-only Terminal ↔ Nino ↔ page ChatGPT, sans modifier l’UI existante de Nino.

BRANCHE ET ISOLATION
- Worktree dédié obligatoire.
- Branche recommandée : worker/journalier-02-nino-chatgpt-bridge.
- Vérifier git status, HEAD, worktrees et fichiers non suivis avant écriture.
- Ne modifier ni main_window.py, ni page_matrix.py, ni state.py, ni session_store.py.

PÉRIMÈTRE AUTORISÉ
- nouveau app/bridge/__init__.py
- nouveau app/bridge/contracts.py
- nouveau app/bridge/file_queue.py
- nouveau app/bridge/nino_chatgpt_bridge.py
- nouveau app/bridge/chatgpt_page_adapter.py
- nouveaux tests dédiés

FONCTIONS ATTENDUES
1. Lire des requêtes identifiées depuis une queue D-only configurable.
2. Valider le schéma, request_id, job_id, target_tile_id, mode et hash.
3. Refuser les doublons.
4. Enregistrer la cible via un page_provider fourni par Nino.
5. Tester la cible sans envoyer.
6. Supporter test-only, no-enter et send.
7. Isoler les sélecteurs ChatGPT dans chatgpt_page_adapter.py.
8. Injecter le texte seulement lorsque la page et le champ sont valides.
9. Envoyer seulement en mode send.
10. Détecter une nouvelle réponse et attendre sa stabilité.
11. Écrire la réponse ou la cause exacte dans outbox/failed.
12. Journaliser sans copier de secret.
13. Timeout, annulation et navigation de page doivent échouer proprement.
14. Ne pas dépendre d’une fenêtre Windows globale.

MACHINE À ÉTATS MINIMALE
RECEIVED → VALIDATED → TARGET_READY → PREPARED → SENT → WAITING_RESPONSE → RESPONSE_STABLE → COMPLETED
avec issues : BLOCKED, FAILED, TIMEOUT, CANCELLED.

TESTS
- schéma valide/invalide;
- doublon de request_id/hash;
- cible absente;
- cible non ChatGPT;
- page non chargée;
- champ introuvable;
- test-only sans injection;
- no-enter sans envoi;
- send;
- réponse nouvelle;
- ancienne réponse ignorée;
- réponse progressive puis stable;
- timeout;
- rechargement/navigation;
- deux requêtes séquentielles;
- refus d’exécution concurrente sur le même tile;
- tous les chemins de runtime sur D:\.

COMMIT
Créer au maximum un commit local atomique. Ne pas pousser.

RAPPORT
Écrire D:\communication\worker-reports\JOURNALIER-02-NINO-CHATGPT-BRIDGE.md.
Terminer par DÉBUT DU RÉSUMÉ et FIN DU TERMINAL.

Verdict : PRÊT POUR INTÉGRATION, CORRECTIONS REQUISES ou BLOQUÉ.
```

---

# 12. Prompt — Jules

```text
Tu es Jules, pont GitHub et gardien de publication. Tu travailles dès le début de la vague, mais tu ne pousses rien sans validation explicite de Brutus.

MISSION
Préparer la traçabilité GitHub de la construction Nino Pages ↔ Terminal ↔ ChatGPT.

TRAVAIL
- Vérifier Topbrutus/Antmux et Topbrutus/ninoscreens.
- Relever main distant, branches et commits récents.
- Comparer le distant avec l’état local communiqué.
- Préparer les fiches de publication pour JOURNALIER-01, JOURNALIER-02 et l’intégration.
- Vérifier que chaque résumé conserve PROJECT/JOB et les marqueurs obligatoires.
- Détecter les doublons PROJECT-000000 UNASSIGNED.
- Préparer un ordre de publication sans l’exécuter.

INTERDICTIONS
- Aucun push.
- Aucun merge.
- Aucun changement du clone interne.
- Aucun secret.

LIVRABLE
Écrire D:\communication\worker-reports\JULES-PUBLICATION-NINO-PAGES-BRIDGE.md.
Verdict : PRÊT À PUBLIER APRÈS VALIDATION ou NON PRÊT.
```

---

# 13. Prompt — Hermès

```text
Tu es Hermès, libraire Antmux connecté à Obsidian. Tu travailles pendant toute la vague et maintiens la mémoire de reprise.

MISSION
Créer un dossier mémoire vivant pour le bouton Pages de Nino et le pont Terminal ↔ ChatGPT.

À MÉMORISER
- état initial réel;
- architecture retenue;
- différence entre pont Windows externe et pont interne Nino;
- contrat UI/moteur;
- branches et worktrees;
- rapports Grok;
- commits des Journaliers;
- revue Copilot;
- décisions de Brutus;
- tests et blocages;
- prochaine reprise exacte.

RÈGLES
- Détecter le coffre Obsidian réel; ne pas inventer de chemin.
- Ne modifier aucun code.
- Ne stocker aucun secret, cookie ou contenu sensible inutile.
- Lier la note à Nino, WorkerDock, Jules, ChatGPT Bridge et D-only.

LIVRABLE
Écrire D:\communication\worker-reports\HERMES-MEMOIRE-NINO-PAGES-BRIDGE.md avec le coffre utilisé, les notes modifiées, les liens, les faits, les hypothèses et la reprise exacte.

Si Hermès ou le coffre n’est pas fonctionnel, répondre BLOQUÉ avec la cause réelle.
```

---

# 14. Prompt — GitHub Copilot

```text
Tu es GitHub Copilot, réviseur indépendant. Tu travailles en deux passes : baseline au début, puis revue des commits et de l’intégration.

MISSION
Détecter les régressions et failles démontrables dans la construction Nino Pages ↔ Terminal ↔ ChatGPT.

PASS 1 — BASELINE
- Lire le comportement actuel du bouton Pages.
- Lire les classes de tiles et la session.
- Lire le pont Windows historique.
- Établir les invariants à préserver.

PASS 2 — COMMITS
Relire séparément :
1. commit JOURNALIER-01 UI Pages;
2. commit JOURNALIER-02 moteur du pont;
3. commit d’intégration.

POINTS DE REVUE
- collisions de signaux Qt;
- régressions focus/split/fullscreen/RUN;
- compatibilité des anciennes sessions;
- ambiguïté de target_tile_id;
- accès thread-safe à QWebEnginePage;
- exécution JavaScript et callbacks asynchrones;
- sélecteurs DOM trop fragiles;
- double envoi;
- confusion ancienne/nouvelle réponse;
- timeout et navigation;
- logs contenant des secrets;
- chemins C:\ actifs;
- blocage de l’UI;
- absence de tests;
- pont Windows historique cassé.

CLASSIFICATION
P0, P1, P2 ou P3 avec fichier, ligne, scénario de reproduction et correction minimale.

INTERDICTIONS
- Ne modifier aucun fichier.
- Ne pousser ni fusionner.

LIVRABLE
Écrire D:\communication\worker-reports\COPILOT-REVUE-NINO-PAGES-BRIDGE.md.
Verdict : APPROUVABLE, APPROUVABLE APRÈS CORRECTIONS ou BLOQUÉ.
```

---

## 15. Ordre de lancement — tout le monde travaille

### Vague A — simultanée

Après réservation des fichiers par Reine-LinuxIA, lancer ensemble :

1. Agent Grok 1 — inventaire UI;
2. Agent Grok 2 — analyse pont;
3. Agent Grok 3 — orchestration et contrat;
4. JOURNALIER-01 — UI Pages;
5. JOURNALIER-02 — moteur du pont;
6. Jules — état distant et publication future;
7. Hermès — mémoire baseline;
8. GitHub Copilot — revue baseline.

Grok 3 reste actif et met à jour sa synthèse à chaque rapport reçu.

### Vague B — consolidation

1. Reine reçoit les deux commits Journaliers.
2. Grok 3 vérifie leur conformité au contrat.
3. Copilot fait la revue séparée des deux commits.
4. Les Journaliers corrigent uniquement leurs propres constats.
5. Reine crée la branche d’intégration et câble UI + moteur.
6. Copilot et Grok 3 relisent l’intégration.
7. Hermès met à jour la mémoire.
8. Jules prépare la publication finale sans pousser.

---

## 16. Tests d’acceptation obligatoires

### UI Pages

- [ ] Le bouton Pages ouvre la nouvelle vue.
- [ ] La grille historique reste accessible.
- [ ] Tous les tiles sont listés avec leur état réel.
- [ ] Une cible ChatGPT peut être sélectionnée explicitement.
- [ ] Une deuxième cible remplace proprement la première.
- [ ] Plusieurs candidats ne provoquent aucun choix automatique.
- [ ] La cible persiste après redémarrage.
- [ ] Une ancienne session sans nouvelle propriété se charge.
- [ ] Une cible absente devient invalide visiblement.
- [ ] Focus, split, fullscreen et RUN fonctionnent encore.

### Pont terminal vers ChatGPT

- [ ] Une requête invalide est rejetée.
- [ ] `test-only` vérifie la cible sans injection.
- [ ] `no-enter` prépare le message sans l’envoyer.
- [ ] `send` envoie une seule fois.
- [ ] Un hash déjà traité n’est pas renvoyé silencieusement.
- [ ] Une cible non ChatGPT est bloquée.
- [ ] Un champ introuvable est bloqué.
- [ ] Une navigation pendant l’envoi est bloquée.
- [ ] Le terminal reçoit le statut exact.

### Retour ChatGPT vers terminal

- [ ] Une ancienne réponse n’est pas prise pour la nouvelle.
- [ ] Une réponse en génération n’est pas retournée trop tôt.
- [ ] Une réponse stable est écrite avec le request_id original.
- [ ] Un timeout produit un fichier d’échec clair.
- [ ] Deux requêtes séquentielles retournent deux réponses distinctes.
- [ ] Une requête concurrente vers le même tile est mise en attente ou refusée clairement.

### D-only et non-régression

- [ ] Queue, logs, état et temporaires restent sur `D:\`.
- [ ] Aucun nouveau chemin actif `C:\` n’est introduit.
- [ ] Aucun processus vivant n’est arrêté.
- [ ] `.venv/` et `data/` ne sont ni supprimés ni commités aveuglément.
- [ ] Le pont Windows historique passe encore ses tests TestOnly/NoEnter.
- [ ] Aucun push ou merge n’a été effectué sans validation.

---

## 17. Critères de réussite de la vague

La vague est considérée terminée uniquement si :

1. tous les agents ont produit un rapport réel;
2. Grok 1 et Grok 2 ont travaillé en lecture seule sur leurs axes;
3. Grok 3 a produit une synthèse et une décision;
4. les deux Journaliers ont été réellement actifs simultanément;
5. les worktrees, branches et fichiers des Journaliers étaient séparés;
6. le bouton Pages permet de choisir une cible ChatGPT explicite;
7. le terminal peut exécuter au minimum `test-only` et `no-enter` contre cette cible;
8. l’envoi réel a été testé seulement après validation des étapes sûres;
9. une réponse ChatGPT peut revenir au terminal avec le même request_id, ou un blocage technique précis est démontré;
10. Copilot a revu les commits et l’intégration;
11. Jules a préparé la publication sans la déclencher;
12. Hermès a mémorisé l’état stable et la reprise exacte;
13. le pont Windows historique n’a pas été cassé;
14. aucun push ou merge non autorisé n’a eu lieu.

---

## 18. Format de rapport final de Reine-LinuxIA

```text
DÉCISION RECOMMANDÉE :

ÉTAT INITIAL :
- branche :
- HEAD :
- fichiers modifiés/non suivis :
- worktrees :
- processus hérités :

AGENTS ACTIFS :
- Grok 1 :
- Grok 2 :
- Grok 3 :
- JOURNALIER-01 :
- JOURNALIER-02 :
- Jules :
- Hermès :
- Copilot :

BOUTON PAGES :
- comportement avant :
- comportement après :
- cible ChatGPT :
- persistance :

PONT TERMINAL ↔ CHATGPT :
- transport :
- test-only :
- no-enter :
- send :
- capture réponse :
- anti-doublon :
- timeout :

COMMITS LOCAUX :
- UI :
- moteur :
- intégration :

TESTS :
- UI :
- moteur :
- intégration :
- D-only :
- non-régression pont Windows :

BLOCAGES / RISQUES :

PUBLICATION :
- push : NON sauf validation explicite
- merge : NON sauf validation explicite

MÉMOIRE HERMÈS :

PROCHAINE ACTION UNIQUE :

🚦 DÉBUT DU RÉSUMÉ
Objectif :
Travail effectué :
Fichiers créés ou modifiés :
Vérifications :
Blocages ou risques :
Niveau de confiance :
Prochaine action unique :
🏁 FIN DU TERMINAL
```

---

## 19. Première action exacte

Donner d’abord le **Prompt central — Reine-LinuxIA / Codex principal**.

Elle doit réserver les périmètres et lancer la vague simultanée. Aucun agent ne commence à écrire avant la confirmation des worktrees et des fichiers réservés.
