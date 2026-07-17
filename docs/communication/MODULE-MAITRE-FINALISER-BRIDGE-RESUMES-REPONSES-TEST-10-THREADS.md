# Antmux — Module maître pour terminer définitivement le Bridge, les résumés et la boîte de réponses

## 0. Autorité, portée et définition de « terminé »

- **Autorité finale :** Brutus
- **Orchestratrice centrale :** Reine-Linuxia / Codex principal
- **Orchestrateur Grok unique :** Agent Grok 3 — high
- **Dépôt d’exécution principal :** `D:\tools\ninoscreens`
- **Dépôt documentaire et modules Antmux :** `Topbrutus/Antmux`
- **Racine opérationnelle obligatoire :** `D:\`
- **Push ou merge :** interdits sans autorisation explicite de Brutus
- **But :** fermer une fois pour toutes les trois fonctions qui doivent fonctionner ensemble dans une même exécution intégrée.

Les trois fonctions sont :

1. **Bridge bidirectionnel** entre le terminal Antmux, Nino et une page ChatGPT explicitement sélectionnée;
2. **Résumé automatique de fin de job**, classé au bon endroit puis remis à Jules;
3. **Boîte de réponses**, qui reçoit la réponse corrélée, l’affiche dans Nino, la retourne au terminal et l’archive avec la job.

Le mot **terminé** est interdit tant que les trois fonctions n’ont pas réussi dans le même test de bout en bout.

Un simple bouton visible, une queue créée, une réponse simulée ou un résumé généré sans transmission ne suffisent pas.

Le résultat final obligatoire est :

```text
Demande terminal
  ↓
JOB + REQUEST identifiés
  ↓
Bridge D-only
  ↓
Tile ChatGPT Nino explicitement sélectionné
  ↓
Envoi contrôlé
  ↓
Réponse réellement capturée
  ↓
Boîte de réponses Nino
  ↓
Retour au terminal
  ↓
Fin de job validée
  ↓
Résumé atomique dans D:\communication\resumes\<PROJECT>\<JOB>\
  ↓
Jules valide, prépare la publication et transmet selon autorisation
  ↓
Hermès mémorise les faits validés dans le coffre Obsidian réel
```

---

## 1. État local connu à revérifier avant toute action

L’état local sur `D:\` est la source de vérité. GitHub `main` est une référence documentaire et peut être en retard sur la branche locale.

État communiqué par Brutus au moment de la rédaction :

- dépôt local : `D:\tools\ninoscreens`;
- branche : `feature/d-only-root`;
- correctif AudioContext déjà commité : `045dc8bfbe7ed245c4b8e93f91506a538a8b44db`;
- correctif de focus Terminal déjà commité : `d21ca1a91d55dc903a8ee6c5699c4a582a8966bf`;
- aucun push effectué;
- changements suivis encore présents après le correctif Terminal :
  - `app/session_store.py`;
  - `app/state.py`;
  - `app/windows/main_window.py`;
  - `app/widgets/pages_bridge_workspace.py`;
- éléments non suivis à laisser intacts :
  - `.venv/`;
  - `data/`.

### 1.1 Prévol obligatoire

Avant de lancer un agent mutateur, Reine-Linuxia doit produire :

```text
D:\communication\checkpoints\<JOB>\git-status.txt
D:\communication\checkpoints\<JOB>\head.txt
D:\communication\checkpoints\<JOB>\branch.txt
D:\communication\checkpoints\<JOB>\worktrees.txt
D:\communication\checkpoints\<JOB>\tracked-diff.patch
D:\communication\checkpoints\<JOB>\untracked-list.txt
D:\communication\checkpoints\<JOB>\processes.txt
```

Le patch doit être produit sans modifier le worktree :

```powershell
git diff --binary > D:\communication\checkpoints\<JOB>\tracked-diff.patch
```

Interdictions :

- aucun `git reset --hard`;
- aucun `git clean`;
- aucun checkout destructif d’un fichier modifié;
- aucune suppression de `.venv/` ou `data/`;
- aucune copie aveugle des dossiers non suivis dans les worktrees;
- aucun arrêt d’un processus Nino, agent ou navigateur sans autorisation.

### 1.2 Porte de préparation du code local

Si les quatre fichiers suivis modifiés appartiennent bien au chantier Pages/Bridge :

1. les inspecter;
2. vérifier qu’ils ne contiennent aucun secret;
3. exécuter `py_compile` et les tests déjà disponibles;
4. créer un **commit local de checkpoint atomique**, sans push;
5. créer ensuite les worktrees à partir de ce checkpoint.

Message recommandé :

```text
wip(nino): checkpoint pages bridge before final integration
```

Si leur provenance ou leur cohérence est incertaine :

```text
Bloqué + fichiers exacts + cause précise + décision demandée à Brutus
```

Aucun agent ne doit reconstruire silencieusement ces changements dans une autre branche.

---

## 2. Invariants non négociables

Chaque implémentation et chaque test doit respecter les invariants suivants.

### 2.1 Identité et corrélation

Chaque opération possède au minimum :

- `project_id`;
- `job_id`;
- `request_id`;
- `correlation_id`;
- `session_id`;
- `turn_id`;
- `target_tile_id`;
- `message_sha256`;
- horodatages ISO-8601 UTC ou avec fuseau explicite.

Une réponse sans `request_id` correspondant est une réponse orpheline et ne doit pas être présentée comme le résultat de la demande courante.

### 2.2 Cible explicite

- Une cible ChatGPT est désignée par `tile_id` ou identité persistante équivalente.
- Le titre seul ne suffit pas.
- L’origine et l’URL doivent être validées selon une configuration.
- Plusieurs candidats produisent `AMBIGUOUS_TARGET`.
- Aucun choix silencieux du premier résultat.

### 2.3 Idempotence

La clé d’idempotence minimale est :

```text
SHA-256(project_id | job_id | request_id | target_tile_id | mode | message_sha256)
```

Une clé déjà terminée ne doit pas déclencher un second envoi silencieux.

### 2.4 Écriture atomique

Tous les fichiers JSON et Markdown produits par la boucle utilisent :

1. écriture dans un fichier temporaire;
2. fermeture complète;
3. calcul du SHA-256;
4. renommage atomique vers le nom final;
5. événement append-only confirmant la publication locale.

Un lecteur ne traite jamais un fichier suffixé `.tmp`, `.partial` ou `.writing`.

### 2.5 Échec fermé

En cas d’incertitude sur :

- la page;
- le champ de saisie;
- le bouton d’envoi;
- la nouvelle réponse;
- la fin du streaming;
- le projet;
- la job;
- l’autorisation de publication;

le système s’arrête avec :

```text
BLOCKED + code + cause précise + artefacts conservés
```

### 2.6 Aucun résultat simulé

- Aucun faux heartbeat.
- Aucun faux PID.
- Aucun rapport prétendant qu’un agent a travaillé sans trace d’exécution.
- Aucun contenu de réponse généré localement pour simuler ChatGPT.
- Aucun test déclaré réussi uniquement parce qu’un mock a réussi.

Les mocks sont permis pour les tests unitaires, mais le test final exige une vraie page Nino et une vraie réponse.

---

## 3. Architecture D-only définitive

### 3.1 Plan de contrôle

```text
D:\orchestration\
  config\
    orchestration.json
    agents.json
    permissions.json
    providers.json
  jobs\
    <JOB>\
      request.md
      state.json
      events.jsonl
      assignments.json
      leases.json
      memory-pack.md
      checkpoints\
      reports\
      artifacts\
  agents\
    <agent-id>\heartbeat.json
  locks\
  queue\
  retry\
  dead-letter\
  logs\
  state\
```

### 3.2 Bridge

```text
D:\communication\nino-chatgpt-bridge\
  inbox\
  processing\
  outbox\
  failed\
  cancelled\
  archive\
  logs\
  state\
  locks\
```

### 3.3 Résumés

```text
D:\communication\resumes\
  _inbox\
  _unassigned\
  <PROJECT>\
    LATEST.md
    <JOB>\
      SUMMARY.md
      manifest.json
      delivery.json
      reply.md
      reply.json
      commits.json
      tests.json
      decision.json
      reports\
      artifacts\
```

### 3.4 Rapports des travailleurs

```text
D:\communication\worker-reports\
  <JOB>\
    GROK-1.md
    GROK-2.md
    GROK-3.md
    CLAUDE-1.md
    GEMINI-FLASH-1.md
    OSS-LOCAL-1.md
    JOURNALIER-01.md
    JOURNALIER-02.md
    JULES.md
    HERMES.md
    COPILOT.md
    REINE-LINUXIA.md
```

### 3.5 Obsidian

Obsidian reste le coffre canonique de mémoire durable. Son chemin doit être détecté, jamais inventé.

Hermès est le seul écrivain automatique dans le coffre.

Les autres agents lisent exclusivement le `memory-pack.md` produit pour la job et écrivent leurs rapports hors du coffre.

---

## 4. Contrats de données définitifs

## 4.1 Requête Bridge

Nom recommandé :

```text
<created_at_compact>__<request_id>.request.json
```

Schéma minimal :

```json
{
  "schema_version": 1,
  "project_id": "PROJECT-000001",
  "job_id": "JOB-000001",
  "request_id": "REQUEST-000001",
  "correlation_id": "CORR-000001",
  "session_id": "SESSION-000001",
  "turn_id": "TURN-000001",
  "source": "terminal-antmux",
  "target_tile_id": 12,
  "target_provider": "chatgpt",
  "mode": "test-only",
  "message": "texte à envoyer",
  "message_sha256": "sha256-hex",
  "created_at": "2026-07-17T03:00:00-04:00",
  "expires_at": "2026-07-17T03:03:00-04:00",
  "timeout_seconds": 180,
  "parent_request_id": null,
  "summary_path": null,
  "metadata": {
    "initiator": "Brutus",
    "purpose": "bridge-final-e2e"
  }
}
```

Valeurs de `mode` :

- `test-only` : valide la cible et le DOM sans modifier le champ;
- `no-enter` : place le texte et déclenche les événements de saisie sans envoyer;
- `send` : envoie après toutes les validations.

## 4.2 Résultat Bridge

```json
{
  "schema_version": 1,
  "project_id": "PROJECT-000001",
  "job_id": "JOB-000001",
  "request_id": "REQUEST-000001",
  "correlation_id": "CORR-000001",
  "session_id": "SESSION-000001",
  "turn_id": "TURN-000001",
  "status": "completed",
  "phase": "response_captured",
  "target_tile_id": 12,
  "target_provider": "chatgpt",
  "target_origin": "https://chatgpt.com",
  "response_text": "réponse réelle",
  "response_sha256": "sha256-hex",
  "response_node_fingerprint": "sha256-hex",
  "started_at": "ISO-8601",
  "sent_at": "ISO-8601",
  "first_response_seen_at": "ISO-8601",
  "stable_at": "ISO-8601",
  "completed_at": "ISO-8601",
  "detail": "preuve lisible",
  "evidence": {
    "baseline_message_count": 8,
    "final_message_count": 9,
    "streaming_indicator_seen": true,
    "stable_window_ms": 2000
  }
}
```

Valeurs minimales de `status` :

```text
accepted
processing
target_ready
message_prepared
sent
waiting_response
completed
blocked
failed
timeout
cancelled
duplicate
```

## 4.3 Manifeste du résumé

```json
{
  "schema_version": 1,
  "project_id": "PROJECT-000001",
  "job_id": "JOB-000001",
  "summary_id": "SUMMARY-000001",
  "status": "validated",
  "summary_path": "D:\\communication\\resumes\\PROJECT-000001\\JOB-000001\\SUMMARY.md",
  "summary_sha256": "sha256-hex",
  "created_at": "ISO-8601",
  "validated_at": "ISO-8601",
  "source_session_id": "SESSION-000001",
  "source_terminal": "antmux",
  "commits": [],
  "tests": [],
  "reports": [],
  "bridge_request_id": "REQUEST-000002",
  "publication": {
    "authorized": false,
    "prepared": true,
    "pushed": false
  }
}
```

## 4.4 Livraison Jules

```json
{
  "schema_version": 1,
  "project_id": "PROJECT-000001",
  "job_id": "JOB-000001",
  "summary_id": "SUMMARY-000001",
  "delivery_id": "DELIVERY-000001",
  "summary_sha256": "sha256-hex",
  "target": "nino-chatgpt-bridge",
  "target_tile_id": 12,
  "status": "confirmed",
  "bridge_request_id": "REQUEST-000002",
  "prepared_at": "ISO-8601",
  "sent_at": "ISO-8601",
  "confirmed_at": "ISO-8601",
  "duplicate": false,
  "detail": "preuve"
}
```

## 4.5 Réponse archivée

`reply.json` :

```json
{
  "schema_version": 1,
  "project_id": "PROJECT-000001",
  "job_id": "JOB-000001",
  "request_id": "REQUEST-000002",
  "delivery_id": "DELIVERY-000001",
  "status": "completed",
  "response_sha256": "sha256-hex",
  "response_path": "reply.md",
  "received_at": "ISO-8601",
  "returned_to_terminal_at": "ISO-8601",
  "displayed_in_nino_at": "ISO-8601"
}
```

---

## 5. Composant 1 — Bridge Terminal ↔ Nino ↔ ChatGPT

## 5.1 Responsabilité du Bridge

Le Bridge est responsable de :

1. recevoir une requête atomique;
2. valider le schéma et les identifiants;
3. réclamer la requête une seule fois;
4. résoudre la cible explicite;
5. tester la page;
6. établir une empreinte de la conversation avant envoi;
7. préparer ou envoyer le texte selon le mode;
8. détecter uniquement la nouvelle réponse;
9. attendre qu’elle soit stable;
10. produire un résultat atomique;
11. notifier Nino et le terminal;
12. archiver les preuves.

## 5.2 Réclamation de requête

La transition recommandée est un déplacement atomique :

```text
inbox\REQUEST.json
→ processing\REQUEST.json
```

Un seul processus peut réussir ce déplacement.

Une lock séparée peut être utilisée si nécessaire :

```text
locks\REQUEST-000001.lock
```

Elle contient :

- PID;
- identité de l’agent;
- démarrage;
- expiration de lease;
- clé d’idempotence.

## 5.3 Validation de cible

Avant toute injection :

- le `tile_id` existe;
- le tile possède une `QWebEnginePage` active;
- la page n’est pas en navigation critique;
- l’origine est autorisée;
- le profil fournisseur correspond;
- un seul champ de saisie valide est trouvé;
- en mode `send`, un mécanisme d’envoi unique est disponible.

Le profil fournisseur est configurable dans :

```text
D:\orchestration\config\providers.json
```

Aucun sélecteur fragile ne doit être dispersé dans l’UI. Tous les détails DOM appartiennent à l’adaptateur fournisseur.

## 5.4 Interface recommandée

```python
class NinoChatGPTBridge:
    def register_target(self, tile_id: int, page_provider) -> None: ...
    def unregister_target(self, tile_id: int) -> None: ...
    def test_target(self, request) -> BridgeResult: ...
    def prepare_message(self, request) -> BridgeResult: ...
    def send_message(self, request) -> BridgeResult: ...
    def poll_response(self, request_id: str) -> BridgeResult: ...
    def cancel_request(self, request_id: str) -> BridgeResult: ...
```

```python
class ChatGPTPageAdapter:
    def inspect(self, page) -> TargetInspection: ...
    def snapshot_conversation(self, page) -> ConversationSnapshot: ...
    def prepare_message(self, page, message: str) -> AdapterResult: ...
    def send_prepared_message(self, page) -> AdapterResult: ...
    def detect_new_response(self, page, baseline) -> ResponseObservation: ...
    def is_response_stable(self, page, observation) -> bool: ...
```

L’UI ne connaît pas les sélecteurs DOM.

## 5.5 Préparation de texte

L’adaptateur doit :

- sélectionner un champ unique;
- lui donner le focus;
- injecter le texte d’une manière compatible avec les événements attendus par l’application Web;
- vérifier que le texte visible correspond au texte attendu;
- calculer une empreinte du contenu préparé;
- ne pas envoyer en mode `no-enter`.

Un simple changement de propriété DOM sans événements ne suffit pas si l’application ne reconnaît pas la saisie.

## 5.6 Détection de la nouvelle réponse

Avant l’envoi, produire un baseline :

- nombre de messages;
- empreinte du dernier message assistant;
- empreintes des derniers nœuds pertinents;
- présence ou non d’un indicateur de streaming;
- horodatage.

Après l’envoi :

1. attendre qu’un nouveau nœud assistant apparaisse;
2. refuser un nœud dont l’empreinte existait dans le baseline;
3. suivre le contenu pendant le streaming;
4. vérifier que l’indicateur de génération est disparu;
5. attendre une fenêtre de stabilité recommandée de 2 secondes;
6. relire une dernière fois;
7. produire le texte final et son SHA-256.

Si la page recharge, change d’origine, perd le tile ou devient ambiguë : `BLOCKED`.

## 5.7 Retour au terminal

Le terminal doit surveiller l’outbox par `request_id`, jamais par « dernier fichier créé » seulement.

Format d’affichage recommandé :

```text
[BRIDGE]
project_id: PROJECT-000001
job_id: JOB-000001
request_id: REQUEST-000001
status: completed
target_tile_id: 12
received_at: 2026-07-17T03:00:00-04:00
response_sha256: ...

--- réponse ---
<contenu réel>
--- fin réponse ---
```

Le consommateur écrit ensuite un reçu local afin de ne pas réafficher la même réponse comme nouvelle.

---

## 6. Composant 2 — Résumé automatique de fin de job

## 6.1 Source du résumé

La réponse finale de l’agent principal doit contenir exactement un bloc :

```text
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

Le hook Stop extrait seulement ce bloc.

## 6.2 Réception initiale

Le hook dépose d’abord le résumé dans :

```text
D:\communication\resumes\_inbox\
```

Il ne doit pas écrire directement dans un projet deviné.

Le fichier initial contient ou accompagne :

- session_id;
- date;
- SHA-256;
- source;
- indices PROJECT/JOB détectés;
- statut de détection.

## 6.3 Validation Jules

Jules doit :

1. vérifier les deux marqueurs;
2. vérifier qu’un seul résumé est présent;
3. déterminer `project_id` et `job_id` à partir de données structurées;
4. refuser une association ambiguë;
5. vérifier l’existence de la job;
6. vérifier que `FINAL_TESTS` a réussi;
7. vérifier la décision de publication;
8. calculer le SHA-256;
9. vérifier l’anti-doublon;
10. créer l’arborescence finale;
11. écrire `SUMMARY.md` et `manifest.json` atomiquement;
12. maintenir `LATEST.md` du projet;
13. préparer la livraison Bridge;
14. préparer Git sans pousser tant que Brutus n’a pas autorisé.

## 6.4 Résumés non assignables

Si PROJECT ou JOB est absent ou contradictoire :

```text
D:\communication\resumes\_unassigned\
```

Le système produit :

```text
BLOCKED_SUMMARY_ROUTING
```

Il ne doit pas transformer automatiquement toute erreur de routage en `PROJECT-000000`.

## 6.5 Anti-doublon

L’empreinte minimale de publication est :

```text
SHA-256(project_id | job_id | summary_sha256 | destination)
```

États recommandés :

```text
received
validated
routed
prepared
awaiting_authorization
published
delivered_to_bridge
reply_received
archived
blocked
```

## 6.6 Transmission du résumé à ChatGPT

Après validation locale, Jules prépare une requête Bridge distincte :

- nouveau `request_id`;
- même `project_id` et `job_id`;
- `source = jules-summary`;
- `summary_path` renseigné;
- `message_sha256` calculé sur le contenu envoyé;
- `parent_request_id` lié à la demande principale si pertinent.

La première transmission réelle du résumé doit demander une confirmation explicite et facilement vérifiable, par exemple :

```text
Accuse réception de ce résumé en commençant exactement par :
SUMMARY-RECEIVED <JOB-ID> <REQUEST-ID>
```

La confirmation reçue doit être archivée dans `reply.md` et `reply.json`.

---

## 7. Composant 3 — Boîte de réponses Nino

## 7.1 Objectif

La boîte de réponses est une vue utilisateur réelle, et non seulement un dossier d’outbox.

Elle doit permettre à Brutus de :

- voir les demandes en cours;
- voir la cible sélectionnée;
- distinguer préparation, envoi, attente, réponse, erreur et timeout;
- lire la réponse complète;
- copier la réponse;
- retourner à la page source;
- ouvrir le dossier de job;
- ouvrir le résumé;
- envoyer un suivi en créant un nouveau `request_id` lié au précédent;
- archiver une réponse traitée;
- voir les preuves de corrélation.

## 7.2 États visuels

```text
AUCUNE CIBLE
CIBLE À TESTER
CIBLE PRÊTE
PRÉPARATION
PRÊT SANS ENVOI
ENVOI
ATTENTE RÉPONSE
RÉPONSE EN COURS
RÉPONSE STABLE
RÉPONSE REÇUE
RETOURNÉE AU TERMINAL
ARCHIVÉE
BLOQUÉ
TIMEOUT
ANNULÉ
DOUBLON
```

## 7.3 Contenu d’une fiche réponse

Chaque fiche affiche :

- project_id;
- job_id;
- request_id;
- parent_request_id;
- target_tile_id;
- fournisseur;
- URL ou origine;
- mode;
- date d’envoi;
- durée;
- statut;
- réponse;
- SHA-256;
- cause précise si bloqué;
- liens vers les artefacts.

## 7.4 Actions et sécurité

Actions :

- **Copier**;
- **Ouvrir la cible**;
- **Ouvrir le résumé**;
- **Ouvrir le dossier de job**;
- **Créer un suivi**;
- **Annuler** si encore actif;
- **Archiver**.

Un suivi ne réutilise jamais le même `request_id`.

Une action « Renvoyer » doit créer une nouvelle requête avec `parent_request_id`, sinon elle risque de contourner l’idempotence.

## 7.5 Retour automatique au terminal

Quand une réponse devient stable :

1. écrire le résultat dans l’outbox;
2. mettre à jour la boîte de réponses;
3. émettre un événement Nino;
4. laisser le terminal consommer par `request_id`;
5. écrire le reçu de consommation;
6. afficher `RETOURNÉE AU TERMINAL`.

La boîte de réponses ne doit pas marquer « retournée » avant le reçu du terminal.

---

## 8. Test contrôlé de 10 threads de travail simultanés

## 8.1 Définition

Dans ce module, « 10 threads » signifie **10 voies de travail réelles et simultanées**, chacune ayant :

- une identité;
- une tâche utile;
- un PID, identifiant de session ou preuve équivalente;
- un démarrage et une fin;
- un heartbeat;
- un rapport;
- un périmètre de lecture ou d’écriture.

Il est interdit d’ouvrir dix fenêtres vides ou de fabriquer dix heartbeats pour prétendre que le test a réussi.

Les deux orchestrateurs restent actifs au-dessus du pool :

- Reine-Linuxia;
- Grok 3.

Ils ne comptent pas dans les dix voies de travail, car leur rôle est le contrôle et l’arbitrage.

## 8.2 Les dix voies obligatoires

### THREAD-01 — JOURNALIER-01 — UI Pages et boîte de réponses

Responsabilités :

- finaliser `PagesBridgeWorkspace`;
- sélection persistante de cible;
- boîte de réponses;
- états visuels;
- câblage Nino;
- tests UI.

Écriture réservée recommandée :

```text
app/widgets/pages_bridge_workspace.py
app/widgets/bridge_response_workspace.py
app/windows/main_window.py
nouveaux tests UI dédiés
```

Ne modifie pas `app/bridge/`.

### THREAD-02 — JOURNALIER-02 — moteur Bridge

Responsabilités :

- contrats;
- queue;
- adaptateur ChatGPT;
- baseline de conversation;
- détection de réponse stable;
- outbox;
- idempotence;
- tests du moteur.

Écriture réservée :

```text
app/bridge/__init__.py
app/bridge/contracts.py
app/bridge/file_queue.py
app/bridge/nino_chatgpt_bridge.py
app/bridge/chatgpt_page_adapter.py
nouveaux tests du bridge
```

Ne modifie pas les fichiers UI existants.

### THREAD-03 — Grok 1 low — inventaire réel

Lecture seule :

- état Git;
- classes Nino;
- session;
- routes Pages;
- fichiers modifiés;
- collisions possibles;
- preuve des worktrees.

Produit : `GROK-1.md`.

### THREAD-04 — Grok 2 medium — analyse DOM et réponses

Lecture seule :

- cycle QWebEngine;
- injection;
- sélecteurs;
- streaming;
- stabilité;
- navigation;
- erreurs et timeouts;
- plan de tests réels.

Produit : `GROK-2.md`.

### THREAD-05 — Claude 1 — architecture indépendante

Lecture seule :

- audit des contrats;
- conditions de course;
- atomicité;
- idempotence;
- séparation UI/moteur;
- scénarios d’échec;
- revue des plans de test.

Produit : `CLAUDE-1.md`.

### THREAD-06 — Gemini Flash 1 — parcours et observabilité

Lecture seule :

- clarté de la page Bridge;
- parcours cible → envoi → réponse;
- états visuels;
- ergonomie de la boîte de réponses;
- scénarios rapides;
- cohérence des messages à Brutus.

Produit : `GEMINI-FLASH-1.md`.

### THREAD-07 — OSS Local 1 — harness et charge

Autorisé à exécuter des tests, sans modifier le code sauf fichier de test explicitement réservé.

Responsabilités :

- tests unitaires;
- tests JSON;
- tests de queue;
- vérification SHA-256;
- surveillance CPU/RAM;
- collecte des PIDs;
- chronologie des heartbeats;
- rapport de charge.

Produit : `OSS-LOCAL-1.md`.

### THREAD-08 — Jules — résumés, livraison et retour

Écriture réservée dans les modules Jules et les zones de résumé seulement.

Responsabilités :

- valider le résumé;
- router PROJECT/JOB;
- anti-doublon;
- produire manifest et delivery;
- préparer Git sans push;
- envoyer le résumé au Bridge après la porte prévue;
- recevoir la réponse corrélée;
- produire `reply.md` et `reply.json`.

Produit : `JULES.md`.

### THREAD-09 — Hermès — mémoire et Obsidian

Responsabilités :

- détecter le coffre réel;
- produire le memory pack avant exécution;
- surveiller les rapports en lecture seule;
- préparer la note finale;
- écrire dans Obsidian seulement après validation;
- inscrire la reprise exacte.

Produit : `HERMES.md`.

### THREAD-10 — GitHub Copilot — baseline et revues

Lecture seule pendant l’exécution :

- baseline avant modifications;
- revue du commit JOURNALIER-01;
- revue du commit JOURNALIER-02;
- revue Jules;
- revue de l’intégration finale;
- sévérité P0/P1/P2/P3.

Produit : `COPILOT.md`.

## 8.3 Preuve de simultanéité

Pour chaque voie, enregistrer :

```json
{
  "thread_id": "THREAD-01",
  "agent_id": "journalier-01",
  "family": "codex",
  "pid_or_session": "preuve réelle",
  "worktree": "D:\\worktrees\\...",
  "branch": "...",
  "mode": "read-only|mutator|review|memory|publisher",
  "started_at": "ISO-8601",
  "last_heartbeat_at": "ISO-8601",
  "finished_at": null,
  "report_path": "..."
}
```

Le test exige une fenêtre d’au moins 60 secondes où les dix voies sont toutes en état `RUNNING` avec heartbeat réel.

## 8.4 Heartbeats et leases

Configuration de test recommandée :

- heartbeat : 10 secondes;
- lease : 60 secondes;
- `STALE` après trois heartbeats manqués;
- un seul remplacement possible par lease;
- maximum deux reprises automatiques;
- troisième échec : `DEAD_LETTER` ou décision humaine.

Aucun remplaçant ne doit être lancé pendant que la lease originale reste valide.

## 8.5 Charge CPU contrôlée

Le but est une forte utilisation utile, pas une boucle artificielle.

Cibles :

- CPU moyen visé pendant la fenêtre utile : 80 à 92 %;
- ne pas maintenir plus de 95 % pendant plus de 20 secondes;
- garder Nino interactif;
- conserver au moins 15 % de mémoire disponible, ou un minimum de 2 Go, la valeur la plus prudente;
- ralentir si le disque devient le goulot;
- ne jamais lancer de busy-loop seulement pour remplir le CPU.

Actions de charge utiles permises :

- tests unitaires séparés;
- compilation Python;
- analyse statique;
- vérification de schémas;
- calculs SHA-256 sur artefacts;
- harness de concurrence;
- inspection de logs;
- revues de commits;
- tests de queue et d’idempotence.

## 8.6 Paliers du test

### Palier A — baseline

Durée : 60 secondes.

Mesurer avec Nino ouvert mais sans vague :

- CPU;
- mémoire;
- disque;
- nombre de processus;
- réactivité de l’interface;
- délai de focus Terminal.

### Palier B — dix voies en lecture/test

Durée minimale : 90 secondes.

Les mutateurs ne modifient pas encore les fichiers partagés. Vérifier :

- dix identités;
- dix heartbeats;
- aucune collision;
- Nino reste utilisable;
- le terminal accepte la saisie immédiatement.

### Palier C — deux mutateurs et huit voies parallèles

Durée minimale : 3 minutes.

- JOURNALIER-01 et JOURNALIER-02 écrivent dans des worktrees et périmètres disjoints;
- les huit autres voies analysent, testent, surveillent ou préparent leurs livrables;
- Jules et Hermès ne modifient pas les fichiers Nino;
- Copilot ne modifie rien pendant la revue.

### Palier D — intégration et test réel

Reine-Linuxia intègre les commits dans une branche dédiée, puis exécute le test de bout en bout.

Les dix voies peuvent continuer avec leurs rôles de test, revue, mémoire et publication préparée.

## 8.7 Réduction automatique

Réduire temporairement la concurrence si :

- CPU > 95 % pendant 20 secondes;
- mémoire disponible sous le seuil;
- Nino ne répond pas pendant 3 secondes;
- le terminal perd la saisie;
- trois heartbeats deviennent `STALE`;
- le disque empêche les écritures atomiques;
- WebEngine tombe ou recharge répétitivement.

Ordre de réduction recommandé :

1. suspendre les tests OSS les plus lourds;
2. suspendre Gemini Flash après son premier rapport;
3. suspendre Claude après son premier rapport;
4. conserver les deux Journaliers, Grok, Jules, Hermès et Copilot;
5. reprendre graduellement lorsque le système est stable.

---

## 9. Branches, worktrees et propriété des fichiers

## 9.1 Branches recommandées

```text
feature/bridge-final-ui
feature/bridge-final-engine
feature/jules-summary-return
integration/bridge-summary-response-final
```

## 9.2 Worktrees recommandés

```text
D:\worktrees\nino-bridge-ui
D:\worktrees\nino-bridge-engine
D:\worktrees\antmux-jules-summary-return
D:\worktrees\nino-bridge-integration
```

Les chemins réels doivent être choisis selon la configuration locale, mais doivent rester sur `D:\`.

## 9.3 Table de réservation obligatoire

Avant démarrage, créer :

```text
D:\orchestration\jobs\<JOB>\assignments.json
```

Il contient pour chaque mutateur :

- branche;
- worktree;
- fichiers autorisés;
- fichiers interdits;
- durée de lease;
- identifiant d’agent;
- objectif;
- tests attendus.

Toute intersection de chemins d’écriture doit faire échouer la réservation.

## 9.4 Fichiers d’intégration partagés

Les fichiers partagés ne sont modifiés par Reine-Linuxia qu’après les commits des propriétaires.

Exemples probables :

- `app/windows/main_window.py`;
- `app/state.py`;
- `app/session_store.py`.

Le Journalier UI peut proposer le changement, mais l’intégration de contrats issus du moteur appartient à la branche d’intégration.

---

## 10. Ordre d’exécution complet

### Phase 0 — Enregistrement

1. créer PROJECT et JOB;
2. enregistrer la demande originale;
3. créer `state.json` et `events.jsonl`;
4. inscrire l’autorité de Brutus;
5. interdire push/merge.

### Phase 1 — Mémoire

1. Hermès détecte Obsidian;
2. Hermès produit `memory-pack.md`;
3. SHA-256 du memory pack;
4. sources indiquées;
5. contradictions signalées.

### Phase 2 — Prévol Git et processus

1. état Git;
2. commits connus;
3. fichiers modifiés;
4. patch de checkpoint;
5. processus actifs;
6. ports et queues existants;
7. modules Jules existants;
8. pont Windows historique.

### Phase 3 — Réservation

1. créer branches;
2. créer worktrees;
3. réserver fichiers;
4. créer leases;
5. vérifier zéro intersection;
6. écrire assignments.json.

### Phase 4 — Lancement des dix voies

1. démarrer les dix voies;
2. capturer PID/session;
3. attendre dix heartbeats;
4. vérifier l’overlap;
5. démarrer la collecte CPU/RAM;
6. maintenir Reine et Grok 3 comme contrôleurs.

### Phase 5 — Développement parallèle

- J01 : UI et boîte de réponses;
- J02 : moteur Bridge;
- Jules : résumé, delivery et reply;
- Hermès : mémoire;
- Grok/Claude/Gemini : analyses;
- OSS : harness et charge;
- Copilot : baseline.

### Phase 6 — Commits atomiques

Chaque mutateur :

1. montre `git diff --stat`;
2. montre la liste exacte des fichiers;
3. exécute ses tests;
4. commit local;
5. montre le SHA;
6. ne pousse pas.

### Phase 7 — Revues indépendantes

- Grok 3;
- Claude;
- Copilot.

Chaque problème est retourné au propriétaire exact du fichier.

### Phase 8 — Intégration

Reine-Linuxia :

1. crée la branche d’intégration;
2. intègre les commits vérifiés;
3. résout sans écraser les changements existants;
4. exécute py_compile;
5. exécute les tests ciblés;
6. exécute les tests complets disponibles.

### Phase 9 — Test réel du Bridge

1. sélectionner explicitement un tile ChatGPT;
2. `test-only`;
3. `no-enter` avec un texte unique;
4. vérifier le texte sans envoi;
5. annuler ou vider proprement;
6. préparer la requête réelle;
7. confirmation de Brutus si le système l’exige;
8. `send`;
9. capturer la nouvelle réponse;
10. retour terminal;
11. affichage boîte de réponses.

### Phase 10 — Test réel du résumé

1. terminer une job de test;
2. générer le bloc résumé;
3. hook vers `_inbox`;
4. Jules valide PROJECT/JOB;
5. classement final;
6. manifest;
7. delivery préparée;
8. transmission par Bridge;
9. réponse reçue;
10. reply archivée;
11. terminal notifié.

### Phase 11 — Mémoire finale

1. tests finaux réussis;
2. Hermès vérifie preuves et commits;
3. écrit la note Obsidian;
4. lie la job, le résumé et la réponse;
5. écrit la prochaine reprise exacte;
6. retourne `MEMORY_COMMIT_OK`.

### Phase 12 — Fermeture

La job passe à `COMPLETED` seulement si les trois portes de réussite sont vertes.

---

## 11. Test de bout en bout final

Nom recommandé :

```text
PROJECT-NINO
JOB-BRIDGE-FINAL-E2E-001
```

## 11.1 Requête de test

Créer un message contenant un jeton unique :

```text
Réponds exactement sur la première ligne :
BRIDGE-OK JOB-BRIDGE-FINAL-E2E-001 REQUEST-<ID>

Sur la deuxième ligne, écris :
Réponse capturée par Nino.
```

## 11.2 Critères Bridge

- la cible est explicite;
- `test-only` réussit;
- `no-enter` prépare sans envoyer;
- `send` envoie une seule fois;
- la première ligne attendue est capturée;
- la réponse est stable;
- l’outbox contient le même request_id;
- le terminal affiche la réponse;
- la boîte Nino affiche la réponse;
- aucun ancien message n’est pris pour le nouveau.

## 11.3 Critères résumé

- le bloc final est extrait une seule fois;
- `_inbox` reçoit le fichier complet;
- Jules route vers le bon PROJECT/JOB;
- `SUMMARY.md` et `manifest.json` existent;
- SHA-256 concordant;
- LATEST.md pointe vers la bonne job;
- aucun PROJECT-000000 artificiel;
- aucun doublon.

## 11.4 Critères livraison et réponse

- Jules crée une nouvelle requête Bridge;
- `delivery.json` existe;
- la confirmation ChatGPT contient JOB et REQUEST;
- `reply.md` et `reply.json` existent;
- la boîte Nino affiche la confirmation;
- le terminal reçoit la confirmation;
- Hermès relie résumé et réponse dans Obsidian.

## 11.5 Critères concurrence

- dix voies réelles;
- fenêtre commune ≥ 60 secondes;
- dix heartbeats;
- deux worktrees mutateurs simultanés;
- zéro chevauchement d’écriture;
- CPU utile fortement occupé sans busy-loop;
- Nino reste interactif;
- Terminal conserve son focus fonctionnel;
- aucune perte de job;
- aucun double envoi.

---

## 12. Matrice de tests

### Bridge

- [ ] cible absente;
- [ ] cible unique;
- [ ] deux cibles ambiguës;
- [ ] page non chargée;
- [ ] origine interdite;
- [ ] champ absent;
- [ ] plusieurs champs candidats;
- [ ] test-only;
- [ ] no-enter;
- [ ] send;
- [ ] double clic;
- [ ] même requête déposée deux fois;
- [ ] timeout;
- [ ] annulation;
- [ ] navigation pendant attente;
- [ ] rechargement;
- [ ] réponse ancienne présente;
- [ ] streaming long;
- [ ] réponse vide;
- [ ] retour terminal.

### Boîte de réponses

- [ ] liste vide;
- [ ] demande active;
- [ ] réponse partielle;
- [ ] réponse stable;
- [ ] erreur;
- [ ] timeout;
- [ ] copie;
- [ ] ouverture de cible;
- [ ] ouverture résumé;
- [ ] suivi avec nouveau request_id;
- [ ] archivage;
- [ ] reçu terminal.

### Résumés

- [ ] marqueurs valides;
- [ ] marqueur de début absent;
- [ ] marqueur de fin absent;
- [ ] deux résumés dans la même réponse;
- [ ] PROJECT absent;
- [ ] JOB absent;
- [ ] job inexistante;
- [ ] job non validée;
- [ ] SHA incorrect;
- [ ] doublon;
- [ ] classement;
- [ ] LATEST;
- [ ] préparation Git;
- [ ] push refusé sans autorisation;
- [ ] livraison Bridge;
- [ ] reply archivée.

### Concurrence

- [ ] dix identités;
- [ ] dix preuves de processus/session;
- [ ] dix heartbeats;
- [ ] lease expirée;
- [ ] remplacement unique;
- [ ] deux retries maximum;
- [ ] collision de chemin refusée;
- [ ] saturation CPU contrôlée;
- [ ] mémoire basse;
- [ ] interface figée;
- [ ] reprise;
- [ ] dead-letter.

### Non-régression Nino

- [ ] bouton Pages;
- [ ] bouton Terminal et focus automatique;
- [ ] RUN;
- [ ] grille;
- [ ] focus;
- [ ] split;
- [ ] fullscreen;
- [ ] sessions;
- [ ] AudioContext;
- [ ] page matrix;
- [ ] pont Windows historique.

---

## 13. Codes d’erreur recommandés

```text
INVALID_REQUEST_SCHEMA
MISSING_PROJECT_ID
MISSING_JOB_ID
MISSING_REQUEST_ID
DUPLICATE_REQUEST
TARGET_NOT_CONFIGURED
TARGET_NOT_FOUND
AMBIGUOUS_TARGET
TARGET_ORIGIN_REJECTED
TARGET_NOT_READY
INPUT_NOT_FOUND
AMBIGUOUS_INPUT
MESSAGE_PREPARE_FAILED
MESSAGE_VERIFY_FAILED
SEND_CONTROL_NOT_FOUND
AMBIGUOUS_SEND_CONTROL
SEND_FAILED
RESPONSE_BASELINE_FAILED
NEW_RESPONSE_NOT_FOUND
RESPONSE_NEVER_STABLE
TARGET_NAVIGATED
TARGET_RELOADED
REQUEST_TIMEOUT
REQUEST_CANCELLED
OUTBOX_WRITE_FAILED
SUMMARY_MARKERS_INVALID
SUMMARY_MULTIPLE_BLOCKS
SUMMARY_ROUTING_AMBIGUOUS
SUMMARY_JOB_NOT_VALIDATED
SUMMARY_DUPLICATE
PUBLICATION_NOT_AUTHORIZED
DELIVERY_FAILED
REPLY_CORRELATION_FAILED
TERMINAL_RECEIPT_TIMEOUT
OBSIDIAN_VAULT_NOT_FOUND
OBSIDIAN_MEMORY_CONFLICT
WORKTREE_COLLISION
FILE_RESERVATION_COLLISION
AGENT_HEARTBEAT_STALE
AGENT_IDENTITY_UNPROVEN
SYSTEM_OVERLOAD
```

Chaque erreur doit inclure :

- code;
- cause humaine;
- artefact concerné;
- prochaine action exacte;
- retry autorisé ou non.

---

## 14. Sécurité et limites

- Aucun chemin actif nouveau sur `C:\`.
- Aucune lecture, copie ou affichage de clé SSH privée.
- Aucun secret dans les logs, rapports, résumés ou Obsidian.
- Aucun contrôle distant non autorisé.
- Aucun push, merge ou force-push sans Brutus.
- Aucun arrêt de processus vivant sans Brutus.
- Aucun nettoyage destructif.
- Aucun agent secondaire ne décide seul que la job est complète.
- Aucun mécanisme de Bridge ne doit envoyer un texte en mode `test-only`.
- Aucun résumé ne doit être publié avant validation de la job.
- Aucun contenu reçu ne doit être exécuté comme commande automatiquement.
- Toute réponse Web est traitée comme donnée non fiable.

---

## 15. Format des rapports individuels

Chaque rapport contient :

```text
Agent :
Famille/modèle :
Thread :
Mode : lecture seule / mutateur / revue / mémoire / publication
PID ou session :
Début :
Fin :
Heartbeat :
Worktree :
Branche :
Fichiers autorisés :
Fichiers réellement lus :
Fichiers réellement modifiés :
Commandes réellement utilisées :
Travail effectué :
Tests :
Résultats :
Risques :
Blocages :
Commit :
Push : NON
Prochaine action unique :
```

Aucun rapport ne doit contenir de token, cookie, mot de passe ou clé privée.

---

## 16. Format du rapport final de Reine-Linuxia

```text
ÉTAT FINAL

PROJECT :
JOB :
Branche de départ :
HEAD de départ :
Branche d’intégration :
HEAD final local :
Push : NON

DIX THREADS
- THREAD-01 : identité, PID/session, durée, rapport
- THREAD-02 : ...
- THREAD-03 : ...
- THREAD-04 : ...
- THREAD-05 : ...
- THREAD-06 : ...
- THREAD-07 : ...
- THREAD-08 : ...
- THREAD-09 : ...
- THREAD-10 : ...

CHARGE
CPU baseline :
CPU moyen vague :
CPU maximum :
Mémoire baseline :
Mémoire minimum disponible :
Réactivité Nino :
Réduction de charge déclenchée : OUI/NON

BRIDGE
Test-only :
No-enter :
Send :
Request ID :
Target tile :
Réponse réelle capturée :
Retour terminal :
Preuves :

RÉSUMÉ
Chemin :
SHA-256 :
Manifest :
Jules validation :
Publication préparée :
Push : NON

BOÎTE DE RÉPONSES
Réponse affichée :
Copie :
Lien cible :
Lien résumé :
Reçu terminal :
Reply archivée :

HERMÈS / OBSIDIAN
Coffre détecté :
Memory pack :
SHA-256 :
Note finale :
Prochaine reprise :

COMMITS LOCAUX
- ...

TESTS
- ...

REVUES
Grok 3 :
Claude :
Copilot :

BLOCAGES
- ...

VERDICT
BRIDGE : PASS/FAIL
RÉSUMÉ : PASS/FAIL
RÉPONSE : PASS/FAIL
10 THREADS : PASS/FAIL
NON-RÉGRESSION : PASS/FAIL

Terminé une fois pour toutes : OUI seulement si tout est PASS.
Prochaine action unique :
```

---

# 17. Prompt central exact à donner à Reine-Linuxia

```text
Tu es Reine-Linuxia, orchestratrice centrale d’Antmux.

MISSION UNIQUE
Terminer définitivement et dans une même vague intégrée :
1. le Bridge Terminal Antmux ↔ Nino ↔ page ChatGPT;
2. le résumé automatique correctement classé et remis à Jules;
3. la boîte de réponses Nino avec retour corrélé au terminal.

Le résultat n’est terminé que si les trois réussissent dans le même test réel de bout en bout.

SOURCE DE VÉRITÉ
- D:\tools\ninoscreens
- état Git local à revérifier
- branche connue : feature/d-only-root
- commits connus :
  - AudioContext : 045dc8bfbe7ed245c4b8e93f91506a538a8b44db
  - focus Terminal : d21ca1a91d55dc903a8ee6c5699c4a582a8966bf
- changements suivis connus : session_store.py, state.py, main_window.py, pages_bridge_workspace.py
- non suivis à ne pas toucher : .venv/ et data/
- aucun push ou merge

PRÉVOL
1. Produis un checkpoint non destructif sous D:\communication\checkpoints\<JOB>\.
2. Vérifie status, branche, HEAD, worktrees, processus et diff.
3. Inspecte les changements suivis existants.
4. S’ils sont cohérents et intentionnels, crée un commit local de checkpoint sans push.
5. Sinon, bloque avec la cause précise.
6. Détecte les agents réels depuis leurs fichiers et configurations; n’invente aucun nom.
7. Détecte le coffre Obsidian réel; ne crée pas de second coffre.

ORCHESTRATEURS
- Toi : unique orchestratrice Codex.
- Grok 3 high : unique orchestrateur Grok.

TEST DE 10 THREADS RÉELS
Lance dix voies utiles et simultanées, avec preuve de PID/session, heartbeat, tâche et rapport :
1. JOURNALIER-01 : UI Pages et boîte de réponses.
2. JOURNALIER-02 : moteur Bridge et queue.
3. Grok 1 : inventaire local, lecture seule.
4. Grok 2 : analyse DOM/réponse, lecture seule.
5. Claude 1 : architecture et conditions de course, lecture seule.
6. Gemini Flash 1 : parcours UI et observabilité, lecture seule.
7. OSS Local 1 : harness, tests et charge.
8. Jules : résumé, livraison et réponse.
9. Hermès : memory pack et Obsidian.
10. Copilot : baseline et revues.

Les dix voies doivent partager une fenêtre de RUNNING d’au moins 60 secondes avec heartbeats réels.
Ne fabrique jamais de processus ou de rapport.
Ne lance aucune busy-loop artificielle.
Vise une charge CPU utile de 80 à 92 %, réduis si CPU > 95 % pendant 20 secondes, mémoire insuffisante ou Nino non réactif.

PARALLÉLISME ET FICHIERS
- JOURNALIER-01 et JOURNALIER-02 utilisent des worktrees, branches et fichiers disjoints.
- Jules n’écrit pas dans Nino.
- Hermès n’écrit que dans le coffre Obsidian réel après validation et dans ses rapports.
- Les agents d’analyse restent en lecture seule.
- Copilot reste en lecture seule.
- Toute collision de chemin bloque la réservation.

BRIDGE
- cible explicite par tile_id;
- validation de l’origine;
- test-only, no-enter, send;
- request_id, job_id, project_id, correlation_id, session_id, turn_id;
- SHA-256 anti-doublon;
- baseline conversation avant envoi;
- nouvelle réponse seulement;
- attente de fin de streaming et stabilité;
- outbox atomique;
- retour au terminal avec le même request_id;
- échec fermé.

RÉSUMÉ
- hook Stop avec un seul bloc DÉBUT DU RÉSUMÉ / FIN DU TERMINAL;
- dépôt initial dans D:\communication\resumes\_inbox\;
- Jules valide PROJECT/JOB;
- classement D:\communication\resumes\<PROJECT>\<JOB>\;
- SUMMARY.md, manifest.json, delivery.json, reply.md, reply.json;
- anti-doublon;
- aucun PROJECT-000000 inventé;
- Git préparé mais aucun push sans Brutus.

BOÎTE DE RÉPONSES
- liste des demandes;
- statuts visibles;
- réponse complète;
- copier;
- ouvrir la cible;
- ouvrir le résumé;
- créer un suivi avec nouveau request_id;
- reçu du terminal;
- archivage.

JULES
- valide et classe le résumé;
- prépare la publication;
- transmet le résumé au Bridge selon la porte d’autorisation;
- attend la réponse corrélée;
- écrit reply.md et reply.json;
- retourne la réponse au terminal;
- ne pousse pas.

HERMÈS
- produit memory-pack.md avant exécution;
- indique les sources et le SHA-256;
- prépare la mémoire pendant la job;
- écrit dans Obsidian seulement après FINAL_TESTS;
- lie job, commits, résumé, livraison, réponse et reprise exacte.

TEST FINAL RÉEL
Exécute PROJECT-NINO / JOB-BRIDGE-FINAL-E2E-001 :
1. sélectionner une cible ChatGPT unique;
2. test-only;
3. no-enter;
4. send avec un jeton unique;
5. capturer la réponse réelle;
6. afficher dans la boîte de réponses;
7. retourner au terminal;
8. terminer la job;
9. créer et classer le résumé;
10. Jules transmet le résumé;
11. capturer l’accusé de réception;
12. archiver reply;
13. Hermès mémorise;
14. exécuter les non-régressions.

INTERDICTIONS
- aucun chemin nouveau sur C:\;
- aucune clé SSH privée lue ou copiée;
- aucun secret dans les logs;
- aucun arrêt de processus;
- aucun reset, clean ou force-push;
- aucun push ou merge;
- aucun double envoi;
- aucun résultat simulé;
- deux reprises automatiques maximum.

VALIDATION
Ne déclare terminé que si :
- Bridge PASS;
- résumé PASS;
- boîte de réponses PASS;
- dix threads PASS;
- non-régression PASS;
- Hermès MEMORY_COMMIT_OK;
- push NON.

Rapporte toutes les preuves selon le format du module maître.
Termine par exactement un bloc 🚦 DÉBUT DU RÉSUMÉ / 🏁 FIN DU TERMINAL.
```

---

## 18. Prompts individuels minimaux

### JOURNALIER-01

```text
Tu es JOURNALIER-01. Tu modifies uniquement l’UI Pages/Bridge et la boîte de réponses dans ton worktree réservé. Tu ne modifies pas app/bridge. Implémente la sélection persistante de cible, les états visuels, la liste des réponses, l’affichage, la copie, les liens, les suivis avec nouveau request_id et le reçu terminal. Préserve Terminal, RUN, grille, focus, split, fullscreen et sessions. Commit local atomique, aucun push.
```

### JOURNALIER-02

```text
Tu es JOURNALIER-02. Tu modifies uniquement le moteur app/bridge et ses nouveaux tests. Implémente contrats, queue atomique, cible explicite, modes test-only/no-enter/send, adaptateur ChatGPT, baseline, réponse nouvelle et stable, timeout, annulation, idempotence et outbox. Tu ne modifies aucun fichier UI existant. Commit local atomique, aucun push.
```

### Grok 1

```text
Lecture seule. Vérifie l’état réel, la structure Pages, les worktrees, les branches, les fichiers modifiés, les réservations et les preuves des dix voies. Signale toute divergence ou simulation.
```

### Grok 2

```text
Lecture seule. Analyse QWebEngine, le DOM ChatGPT, la préparation de texte, l’envoi, le streaming, la capture de la nouvelle réponse, la stabilité et les scénarios d’échec. Propose des tests précis sans modifier les fichiers.
```

### Claude 1

```text
Lecture seule. Audite l’architecture, les contrats, l’atomicité, les conditions de course, l’idempotence, les erreurs, la sécurité et les critères de fermeture définitive.
```

### Gemini Flash 1

```text
Lecture seule. Audite le parcours utilisateur Pages → cible → envoi → attente → réponse → résumé, les états visibles, les messages et l’ergonomie de la boîte de réponses.
```

### OSS Local 1

```text
Exécute les harnesses et tests autorisés, surveille CPU/RAM/PIDs/heartbeats, vérifie JSON, SHA-256, queue et idempotence. Ne modifie aucun fichier non réservé et ne lance aucune busy-loop.
```

### Jules

```text
Valide les résumés, route PROJECT/JOB, calcule les empreintes, écrit SUMMARY/manifest/delivery/reply, prépare Git sans pousser, transmet au Bridge selon autorisation et retourne la réponse corrélée au terminal.
```

### Hermès

```text
Détecte le coffre Obsidian réel, produit le memory pack signé, surveille les rapports sans modifier le code, puis après FINAL_TESTS écrit la note canonique, lie tous les artefacts et inscrit la reprise exacte.
```

### Copilot

```text
Lecture seule. Fais la baseline puis revois chaque commit et l’intégration finale. Classe les problèmes P0/P1/P2/P3. Ne modifie rien.
```

---

## 19. Verdict final

Le chantier peut être fermé uniquement quand toutes les cases suivantes sont vraies :

```text
[ ] Le terminal envoie une requête identifiée.
[ ] Nino cible un tile ChatGPT unique.
[ ] test-only fonctionne.
[ ] no-enter fonctionne.
[ ] send fonctionne une seule fois.
[ ] La nouvelle réponse réelle est capturée.
[ ] La réponse revient au terminal.
[ ] La boîte de réponses l’affiche et la corrèle.
[ ] Le résumé final est généré une seule fois.
[ ] Jules le classe au bon PROJECT/JOB.
[ ] Jules prépare la publication sans push.
[ ] Jules transmet le résumé au Bridge.
[ ] L’accusé de réception est archivé.
[ ] Hermès met à jour Obsidian après validation.
[ ] Dix voies ont réellement travaillé simultanément.
[ ] Aucune collision de fichiers.
[ ] Aucun nouveau chemin C:\.
[ ] Aucun secret exposé.
[ ] Aucun processus arrêté.
[ ] Aucun push ou merge.
[ ] Toutes les non-régressions passent.
```

Si une case échoue :

```text
Pas terminé.
Bloqué + cause précise + propriétaire + artefact + prochaine action unique.
```
