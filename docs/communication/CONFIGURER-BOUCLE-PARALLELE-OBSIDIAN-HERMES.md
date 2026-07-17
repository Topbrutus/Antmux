# Antmux — Configurer une boucle parallèle résiliente avec Obsidian et Hermès

## 0. Autorité, portée et résultat attendu

- **Autorité finale :** Brutus
- **Orchestratrice centrale :** Reine-LinuxIA / Codex principal
- **Orchestrateur Grok :** Agent Grok 3 — high
- **Libraire et gardien de mémoire :** Hermès
- **Bibliothèque vivante :** Obsidian
- **Pont GitHub :** Jules
- **Réviseur indépendant :** GitHub Copilot
- **Exécutants Codex :** JOURNALIER-01 et JOURNALIER-02
- **Travailleurs Grok :** Agent Grok 1 — low et Agent Grok 2 — medium
- **Racine opérationnelle :** `D:\`

### Objectif

Configurer Antmux pour que les agents travaillent réellement en parallèle dans une boucle fermée, observable et récupérable, sans perte de job, sans double exécution silencieuse, sans collision de fichiers et sans oubli de mémoire.

Dans ce document, « boucle parfaite » signifie une boucle opérationnelle qui respecte les invariants suivants :

1. chaque demande reçoit un identifiant permanent;
2. chaque job possède un état unique et vérifiable;
3. chaque agent possède un périmètre réservé;
4. aucun fichier n’est modifié simultanément par deux agents;
5. chaque agent publie un heartbeat et un rapport;
6. toute interruption est détectée et reprise proprement;
7. toute sortie est revue avant intégration;
8. Hermès enrichit la job avant exécution et mémorise le résultat après validation;
9. Obsidian reste la bibliothèque canonique, mais un seul écrivain — Hermès — y écrit;
10. aucun push, merge, envoi externe ou suppression destructive ne se produit sans la règle d’autorisation applicable.

---

## 1. Architecture générale

```text
Brutus
  ↓
Reine-LinuxIA — plan de contrôle
  ↓
Registre de jobs + queue + leases + événements
  ├──────────────────────────────────────────────────────────────┐
  │                                                              │
  ↓                                                              ↓
Hermès — mémoire                                             Routeur de travail
  ↓                                                              │
Obsidian — bibliothèque canonique                               ├─ Famille Grok
  ↓                                                              │    ├─ Grok 1
Memory Pack par job                                              │    └─ Grok 2
                                                                 │
                                                                 ├─ Famille Codex
                                                                 │    ├─ JOURNALIER-01
                                                                 │    └─ JOURNALIER-02
                                                                 │
                                                                 ├─ Jules — GitHub
                                                                 └─ Copilot — revue
                                                                      ↓
                                                               Intégration + tests
                                                                      ↓
                                                           Hermès mémorise le résultat
                                                                      ↓
                                                               Job suivante / reprise
```

La boucle n’attend pas que tous les agents finissent avant de préparer la suite :

- Hermès prépare la mémoire de la prochaine job pendant que les Journaliers exécutent la job courante;
- Grok 1 fait l’inventaire pendant que Grok 2 analyse les risques;
- Grok 3 maintient la synthèse et prépare les critères d’acceptation;
- Jules suit les branches et prépare la publication sans pousser;
- Copilot prépare la baseline puis revoit les commits dès qu’ils apparaissent;
- Reine-LinuxIA arbitre, réserve les fichiers, intègre et relance la boucle.

---

## 2. Place exacte d’Obsidian et d’Hermès

### 2.1 Obsidian

Obsidian est la **bibliothèque vivante canonique**. Il contient les faits durables, les décisions, les erreurs connues, les modes d’emploi, les relations entre projets et la reprise exacte.

Obsidian n’est pas :

- un orchestrateur;
- un exécuteur de code;
- une queue de processus;
- un endroit où tous les agents écrivent directement;
- un stockage de secrets, cookies, jetons ou clés privées.

### 2.2 Hermès

Hermès est le **libraire unique** entre la boucle de travail et Obsidian.

Hermès possède deux responsabilités obligatoires :

#### Avant exécution

1. recevoir la demande originale;
2. trouver le projet, les décisions et incidents pertinents;
3. produire un `memory-pack.md` immuable pour la job;
4. indiquer les sources consultées;
5. séparer faits, hypothèses, risques et décisions humaines;
6. signaler si la mémoire est incomplète ou contradictoire.

#### Après validation

1. recevoir les rapports finaux;
2. vérifier les identifiants de job, branches, commits et tests;
3. mettre à jour la note Obsidian de la job;
4. mettre à jour les index du projet;
5. enregistrer les décisions et le prochain point de reprise;
6. lier la job aux erreurs, solutions, agents et fichiers concernés.

### 2.3 Règle d’écriture exclusive

Seul Hermès écrit dans le coffre Obsidian pendant la boucle automatisée.

Les autres agents :

- lisent le `memory-pack.md` fourni par Hermès;
- écrivent leurs rapports dans `D:\communication\worker-reports\`;
- ne modifient jamais directement les notes Obsidian;
- ne créent pas de deuxième coffre;
- ne devinent pas le chemin du coffre.

Cette règle évite les conflits Markdown, les liens cassés, les doublons et les notes contradictoires.

### 2.4 Structure Obsidian recommandée

Hermès doit détecter le coffre réel. Une fois détecté, il peut utiliser cette structure logique :

```text
00-Inbox/
10-Projects/
20-Jobs/
30-Decisions/
40-Incidents/
50-Runbooks/
60-Agents/
70-Indexes/
80-Archives/
```

Chaque job possède une note canonique :

```text
20-Jobs/JOB-000123.md
```

Elle contient au minimum :

- demande originale;
- projet;
- état;
- memory pack;
- agents affectés;
- branches et worktrees;
- fichiers réservés;
- événements importants;
- commits;
- tests;
- blocages;
- décision finale;
- prochaine reprise exacte.

---

## 3. Plan de contrôle D-only

Tous les mécanismes appartenant à Antmux doivent rester sur `D:\`.

Structure recommandée :

```text
D:\orchestration\
  config\
    orchestration.json
    agents.json
    permissions.json
  inbox\
  jobs\
    JOB-000001\
      request.md
      state.json
      events.jsonl
      memory-pack.md
      assignments.json
      leases.json
      checkpoints\
      artifacts\
      reports\
  agents\
    reine-linuxia\heartbeat.json
    grok-1\heartbeat.json
    grok-2\heartbeat.json
    grok-3\heartbeat.json
    journalier-01\heartbeat.json
    journalier-02\heartbeat.json
    jules\heartbeat.json
    hermes\heartbeat.json
    copilot\heartbeat.json
  locks\
  queue\
  retry\
  dead-letter\
  archive\
  logs\
  state\
  temp\

D:\communication\
  worker-reports\
  resumes\
```

Aucun chemin `C:\` ne doit être introduit par la nouvelle boucle.

---

## 4. Registre de jobs et états

Chaque demande reçoit un identifiant permanent :

```text
JOB-000001
JOB-000002
JOB-000003
```

### États autorisés

```text
INBOX
MEMORY_REVIEW
READY
RESERVED
RUNNING
WAITING_DEPENDENCY
VERIFYING
CORRECTION_REQUIRED
INTEGRATING
FINAL_TESTS
MEMORY_COMMIT
COMPLETED
BLOCKED
RETRY_PENDING
DEAD_LETTER
CANCELLED
```

### Règles d’état

- une job ne change d’état que par un événement enregistré;
- `state.json` contient l’état actuel;
- `events.jsonl` est append-only et contient tout l’historique;
- un agent ne peut pas déclarer lui-même `COMPLETED` sans validation;
- Hermès ne mémorise pas un résultat comme stable avant `FINAL_TESTS` réussis;
- Jules ne publie pas avant la décision de Brutus ou la règle d’autorisation prévue;
- une job bloquée conserve tous ses artefacts et sa reprise exacte.

---

## 5. Enveloppe de job obligatoire

Exemple de `state.json` :

```json
{
  "job_id": "JOB-000123",
  "project": "ninoscreens",
  "status": "RUNNING",
  "priority": 5,
  "created_at": "2026-07-17T00:00:00-04:00",
  "updated_at": "2026-07-17T00:00:30-04:00",
  "orchestrator": "reine-linuxia",
  "grok_orchestrator": "grok-3",
  "memory_status": "READY",
  "memory_pack_sha256": "...",
  "assignments": [
    "journalier-01",
    "journalier-02",
    "grok-1",
    "grok-2",
    "jules",
    "hermes",
    "copilot"
  ],
  "integration_gate": "HUMAN_APPROVAL_REQUIRED",
  "retry_count": 0,
  "max_retries": 2,
  "last_error": null
}
```

Chaque exécution reçoit aussi une clé d’idempotence :

```text
JOB-000123:<agent>:<task-version>:<input-sha256>
```

Une clé déjà terminée ne doit pas être exécutée une deuxième fois silencieusement.

---

## 6. Réservation, leases et heartbeats

### 6.1 Réservation de fichiers

Avant toute écriture, Reine-LinuxIA produit `assignments.json` :

```json
{
  "journalier-01": {
    "branch": "worker/JOB-000123-journalier-01",
    "worktree": "D:\\workers\\JOB-000123-JOURNALIER-01",
    "write_paths": [
      "app/windows/main_window.py",
      "app/widgets/pages_bridge_workspace.py"
    ]
  },
  "journalier-02": {
    "branch": "worker/JOB-000123-journalier-02",
    "worktree": "D:\\workers\\JOB-000123-JOURNALIER-02",
    "write_paths": [
      "app/bridge/"
    ]
  }
}
```

Règles :

- aucun chevauchement dans `write_paths`;
- un seul worktree par agent mutateur;
- les agents d’analyse sont lecture seule;
- un fichier partagé nécessaire à l’intégration est réservé à Reine-LinuxIA après les commits des travailleurs;
- tout changement hors périmètre provoque `BLOCKED` ou une demande d’élargissement explicite.

### 6.2 Lease

Chaque affectation mutatrice possède une lease :

```json
{
  "lease_id": "LEASE-JOB-000123-JOURNALIER-01",
  "owner": "journalier-01",
  "expires_at": "2026-07-17T00:02:00-04:00",
  "renewed_at": "2026-07-17T00:00:45-04:00"
}
```

Valeurs initiales recommandées :

- heartbeat : toutes les 15 secondes;
- durée de lease : 90 secondes;
- statut `STALE` après 3 heartbeats manqués;
- maximum 2 reprises automatiques;
- après 2 échecs : `DEAD_LETTER` ou validation humaine.

Ces valeurs doivent rester configurables.

### 6.3 Heartbeat

Chaque agent maintient un fichier heartbeat atomique :

```json
{
  "agent": "journalier-01",
  "job_id": "JOB-000123",
  "status": "RUNNING",
  "phase": "tests",
  "updated_at": "2026-07-17T00:01:15-04:00",
  "progress_note": "Arena tests running",
  "current_paths": ["app/windows/main_window.py"]
}
```

Le heartbeat ne contient ni secret ni chaîne privée inutile.

---

## 7. Capacité parallèle

### Famille Codex

- un orchestrateur actif : Reine-LinuxIA / Codex principal;
- deux exécutants simultanés : JOURNALIER-01 et JOURNALIER-02;
- chaque exécutant possède un worktree et des fichiers distincts;
- Reine-LinuxIA intègre après revue.

### Famille Grok

- un orchestrateur actif : Grok 3;
- deux travailleurs simultanés : Grok 1 et Grok 2;
- lecture seule par défaut;
- Grok 3 ne modifie pas le code de production.

### Agents spécialisés permanents

- Hermès : mémoire avant et après;
- Jules : état GitHub et préparation de publication;
- Copilot : baseline, revue des commits et revue d’intégration.

### Principe de pipeline

Quand JOURNALIER-01 et JOURNALIER-02 exécutent `JOB-000123` :

- Hermès peut préparer le memory pack de `JOB-000124`;
- Grok 1 peut inventorier `JOB-000124`;
- Grok 2 peut analyser les risques de `JOB-000124`;
- Jules peut préparer la publication de `JOB-000122`;
- Copilot peut revoir l’intégration de `JOB-000122`;
- Grok 3 maintient les synthèses des jobs actives.

Ainsi, tout le monde travaille, mais personne ne se marche dessus.

---

## 8. Boucle opérationnelle complète

### Phase 1 — Réception

1. Brutus ou une source autorisée crée une demande.
2. Le registre attribue `JOB-xxxxxx`.
3. La demande originale est conservée sans reformulation destructive.
4. L’état devient `MEMORY_REVIEW`.

### Phase 2 — Hermès avant travail

1. Hermès détecte le coffre Obsidian réel.
2. Hermès cherche les notes liées.
3. Hermès produit `memory-pack.md` avec SHA-256.
4. Hermès indique les contradictions et données manquantes.
5. L’état devient `READY`.

### Phase 3 — Planification et réservation

1. Reine-LinuxIA lit la demande et le memory pack.
2. Grok 3 prépare la stratégie d’analyse.
3. Reine-LinuxIA découpe les tâches mutatrices.
4. Les fichiers, branches et worktrees sont réservés.
5. Les leases sont créées.
6. L’état devient `RESERVED`.

### Phase 4 — Lancement parallèle

Lancer sans attendre, dans leurs périmètres :

- Grok 1;
- Grok 2;
- Grok 3;
- JOURNALIER-01;
- JOURNALIER-02;
- Jules;
- Copilot baseline;
- Hermès en veille de rapports.

L’état devient `RUNNING`.

### Phase 5 — Surveillance

1. Chaque agent publie son heartbeat.
2. Reine-LinuxIA vérifie collisions, leases et blocages.
3. Grok 3 met à jour sa synthèse.
4. Toute erreur crée un événement structuré.
5. Une lease expirée déclenche une reprise contrôlée, jamais deux travailleurs actifs sur la même affectation.

### Phase 6 — Rapports et commits

1. Chaque agent écrit un rapport distinct.
2. Les Journaliers créent au maximum un commit atomique chacun.
3. Aucun push.
4. L’état devient `VERIFYING`.

### Phase 7 — Revue

1. Copilot revoit chaque commit séparément.
2. Grok 3 compare les résultats au contrat.
3. Les constats sont classés P0 à P3.
4. Les corrections retournent uniquement au propriétaire du périmètre.
5. Les corrections produisent un commit atomique ou amendent le commit selon la règle décidée par Reine.

### Phase 8 — Intégration

1. Reine-LinuxIA crée une branche d’intégration.
2. Elle assemble les commits approuvés.
3. Elle résout uniquement les points d’intégration réservés.
4. Elle exécute les tests complets.
5. Copilot et Grok 3 revoient l’intégration.
6. L’état devient `FINAL_TESTS`.

### Phase 9 — Décision humaine et publication

1. Reine présente le rapport final.
2. Brutus valide ou refuse l’intégration/publication.
3. Jules publie seulement après autorisation.
4. Aucun force-push.
5. Les identifiants de publication sont consignés.

### Phase 10 — Hermès après travail

1. Hermès reçoit le rapport final validé.
2. Hermès met à jour Obsidian.
3. Hermès lie commits, tests, décisions et incidents.
4. Hermès écrit la prochaine reprise exacte.
5. L’état devient `COMPLETED`.
6. La job suivante déjà préparée passe à `RESERVED`.

---

## 9. Gestion des erreurs et reprise

### Erreur récupérable

Exemples :

- agent interrompu;
- test temporairement indisponible;
- fichier verrouillé;
- réseau GitHub temporairement indisponible.

Action :

1. checkpoint;
2. libération ou expiration contrôlée de la lease;
3. `RETRY_PENDING`;
4. reprise avec la même clé d’idempotence;
5. maximum 2 tentatives automatiques.

### Erreur non récupérable automatiquement

Exemples :

- conflit de périmètres;
- mémoire contradictoire critique;
- secret détecté dans un rapport;
- test P0/P1 en échec;
- cible ambiguë;
- commande WorkerDock inexistante;
- chemin Obsidian introuvable;
- différence entre l’état réel et le contrat.

Action :

```text
Bloqué + cause précise
```

La job conserve ses artefacts et attend Brutus.

### Dead letter

Après deux échecs identiques ou une impossibilité structurelle :

- déplacer l’entrée vers `D:\orchestration\dead-letter\`;
- conserver `request.md`, `state.json`, `events.jsonl`, memory pack et rapports;
- créer une note d’incident pour Hermès;
- ne pas boucler indéfiniment.

---

## 10. Invariants de sécurité

- aucune clé SSH privée n’est lue, affichée, copiée ou mémorisée;
- aucun secret n’entre dans Obsidian;
- aucun cookie ChatGPT n’est exporté;
- aucune donnée sensible n’est copiée dans les rapports;
- aucun agent ne choisit « toujours autoriser » pour un accès hors workspace sans règle explicite;
- aucun processus vivant n’est arrêté sans autorisation;
- aucun `git reset --hard`, `git clean -fd`, force-push ou suppression destructive;
- aucun agent secondaire ne pousse ou fusionne;
- toutes les écritures de boucle restent sur `D:\`;
- Obsidian n’est écrit que par Hermès;
- les rapports sont append-only ou versionnés;
- les actions externes sont fail-closed.

---

## 11. Configuration initiale recommandée

Exemple `D:\orchestration\config\orchestration.json` :

```json
{
  "root": "D:\\orchestration",
  "heartbeat_seconds": 15,
  "lease_seconds": 90,
  "missed_heartbeats_before_stale": 3,
  "max_automatic_retries": 2,
  "parallelism": {
    "codex_orchestrators": 1,
    "codex_workers": 2,
    "grok_orchestrators": 1,
    "grok_workers": 2,
    "jules": 1,
    "hermes": 1,
    "copilot": 1
  },
  "obsidian": {
    "vault_path": null,
    "discover_at_startup": true,
    "exclusive_writer": "hermes",
    "block_critical_jobs_without_memory_pack": true
  },
  "git": {
    "push_requires_human_confirmation": true,
    "merge_requires_human_confirmation": true,
    "force_push_allowed": false
  },
  "security": {
    "allow_secrets_in_reports": false,
    "allow_private_key_read": false,
    "allow_process_termination": false
  }
}
```

Le chemin du coffre Obsidian reste `null` tant qu’Hermès ne l’a pas détecté et validé.

---

## 12. Prompt exact à donner à Reine-LinuxIA / Codex principal

```text
Configure le système Antmux pour que tous les agents travaillent réellement en parallèle dans une boucle fermée, résiliente, observable et D-only.

OBJECTIF
Mettre en place une chaîne continue où les jobs sont reçues, enrichies par la mémoire, divisées, réservées, exécutées en parallèle, revues, intégrées, testées, publiées après autorisation et mémorisées avant de passer automatiquement à la job suivante.

RÈGLE FONDAMENTALE
Tout le monde doit travailler, mais aucun agent ne doit travailler sur les mêmes fichiers, la même branche mutatrice ou la même note Obsidian qu’un autre agent.

PLACE D’OBSIDIAN ET D’HERMÈS
- Obsidian est la bibliothèque canonique vivante.
- Hermès est le libraire unique et le seul écrivain automatique dans Obsidian.
- Avant chaque job, Hermès produit un memory-pack.md versionné et signé par SHA-256.
- Les travailleurs lisent le memory pack mais n’écrivent pas dans Obsidian.
- Après validation finale, Hermès mémorise les faits, décisions, commits, tests, incidents et la prochaine reprise exacte.
- Détecte le coffre réel; ne crée pas un deuxième coffre et n’invente pas son chemin.
- Ne stocke aucun secret, cookie, jeton ou clé privée dans Obsidian.

PARALLÉLISME
- Un orchestrateur Codex : Reine-LinuxIA.
- Deux travailleurs Codex simultanés : JOURNALIER-01 et JOURNALIER-02.
- Un orchestrateur Grok : Agent Grok 3 high.
- Deux travailleurs Grok simultanés : Agent Grok 1 low et Agent Grok 2 medium.
- Jules travaille en parallèle sur la traçabilité GitHub sans pousser.
- GitHub Copilot travaille en parallèle sur la baseline et les revues.
- Hermès prépare la mémoire de la prochaine job pendant l’exécution de la job courante.

PLAN DE CONTRÔLE
Créer ou réutiliser sous D:\ un registre de jobs, une queue, des états, des événements append-only, des leases, des heartbeats, des locks, des checkpoints, une zone retry et une dead-letter queue.

ÉTATS MINIMAUX
INBOX, MEMORY_REVIEW, READY, RESERVED, RUNNING, WAITING_DEPENDENCY, VERIFYING, CORRECTION_REQUIRED, INTEGRATING, FINAL_TESTS, MEMORY_COMMIT, COMPLETED, BLOCKED, RETRY_PENDING, DEAD_LETTER, CANCELLED.

RÉSERVATION
- Chaque agent mutateur reçoit un worktree, une branche et une liste de chemins d’écriture exclusifs.
- Refuse tout chevauchement.
- Les fichiers d’intégration partagés sont réservés à Reine-LinuxIA après les commits des Journaliers.
- Les agents d’analyse restent en lecture seule.

HEARTBEATS ET LEASES
- Heartbeat recommandé : 15 secondes.
- Lease recommandée : 90 secondes.
- Après 3 heartbeats manqués, marquer l’agent STALE.
- Ne jamais lancer deux remplaçants pour la même lease.
- Maximum 2 reprises automatiques, puis DEAD_LETTER ou validation humaine.

IDEMPOTENCE
Chaque tâche reçoit une clé basée sur job_id, agent, version de tâche et SHA-256 d’entrée. Une tâche déjà terminée ne doit pas être exécutée deux fois silencieusement.

BOUCLE
1. enregistrer la demande et attribuer JOB-xxxxxx;
2. Hermès produit le memory pack;
3. Reine réserve branches, worktrees et fichiers;
4. lancer Grok 1, Grok 2, Grok 3, JOURNALIER-01, JOURNALIER-02, Jules, Hermès et Copilot selon leurs rôles;
5. surveiller heartbeats, leases, événements et collisions;
6. recevoir rapports et commits locaux atomiques;
7. faire revoir séparément par Copilot et Grok 3;
8. retourner les corrections au propriétaire exact;
9. intégrer dans une branche dédiée;
10. exécuter les tests complets;
11. demander l’autorisation de Brutus pour push/merge ou action externe;
12. Jules publie après autorisation;
13. Hermès met à jour Obsidian et la reprise exacte;
14. fermer la job et promouvoir la suivante déjà préparée.

INTERDICTIONS
- Aucun chemin nouveau sur C:\.
- Aucun reset destructif, clean, force-push ou suppression non autorisée.
- Aucun arrêt de processus vivant.
- Aucune lecture ou copie de clé SSH privée.
- Aucun secret dans les logs, rapports ou Obsidian.
- Aucun push ou merge par un agent secondaire.
- Aucune commande WorkerDock inventée.
- Aucune boucle infinie : après deux reprises identiques, bloquer avec la cause exacte.

VALIDATION
Avant d’annoncer que la boucle fonctionne, démontrer :
- deux Journaliers réellement actifs simultanément;
- Grok 1 et Grok 2 actifs sous Grok 3;
- Jules, Hermès et Copilot produisant leurs livrables;
- worktrees et chemins d’écriture disjoints;
- heartbeats visibles;
- lease expirée récupérable sans double exécution;
- memory pack produit par Hermès;
- écriture finale Obsidian par Hermès seulement;
- reprise après interruption;
- job suivante préparée pendant la job courante;
- aucun nouveau chemin C:\;
- aucun push ou merge non autorisé.

SORTIE ATTENDUE
Rapporte exactement :
- architecture réellement installée;
- commandes et fonctions réellement utilisées;
- chemins créés;
- configuration;
- coffre Obsidian détecté;
- notes Hermès créées ou mises à jour;
- agents actifs et preuves d’activité;
- worktrees, branches et réservations;
- tests de concurrence, reprise et idempotence;
- blocages et risques;
- commits locaux;
- push : OUI/NON;
- prochaine action unique.

Termine par le bloc DÉBUT DU RÉSUMÉ / FIN DU TERMINAL.
```

---

## 13. Prompt exact pour Hermès

```text
Tu es Hermès, libraire unique de la boucle Antmux.

MISSION
Placer Obsidian correctement dans l’architecture et assurer une mémoire cohérente avant, pendant et après chaque job.

RÈGLES
- Détecte le coffre Obsidian réellement utilisé; ne devine pas son chemin.
- Ne crée pas de deuxième coffre.
- Tu es le seul écrivain automatique dans Obsidian.
- Les autres agents déposent leurs rapports dans D:\communication\worker-reports\.
- Tu lis ces rapports, les valides et les consolides.
- Aucun secret, jeton, cookie ou clé privée dans les notes.

AVANT CHAQUE JOB
1. lire la demande originale;
2. retrouver projets, décisions, incidents, modes d’emploi et jobs connexes;
3. produire D:\orchestration\jobs\<JOB>\memory-pack.md;
4. calculer son SHA-256;
5. distinguer faits, hypothèses, contradictions et risques;
6. indiquer les notes sources;
7. bloquer une job critique si la mémoire nécessaire est absente ou contradictoire.

PENDANT LA JOB
- surveiller les rapports disponibles sans modifier le code;
- préparer la note canonique de la job;
- préparer la mémoire de la job suivante si la capacité le permet;
- ne pas modifier le memory pack déjà remis aux travailleurs; publier une nouvelle version si nécessaire.

APRÈS VALIDATION
1. confirmer job_id, commits, branches, tests et décision humaine;
2. mettre à jour la note canonique Obsidian;
3. lier décisions, incidents, agents, fichiers et résumés;
4. enregistrer la prochaine reprise exacte;
5. publier un rapport D:\communication\worker-reports\HERMES-<JOB>-MEMOIRE.md;
6. retourner MEMORY_COMMIT_OK ou BLOQUÉ + cause précise.
```

---

## 14. Tests d’acceptation

### Orchestration

- [ ] Chaque job possède `state.json` et `events.jsonl`.
- [ ] Les transitions d’état sont traçables.
- [ ] Deux Journaliers fonctionnent simultanément.
- [ ] Les worktrees et chemins d’écriture sont disjoints.
- [ ] Grok 1 et Grok 2 fonctionnent sous Grok 3.
- [ ] Jules, Hermès et Copilot produisent chacun un livrable.
- [ ] La job suivante est préparée avant la fin de la job courante.

### Leases et reprise

- [ ] Chaque agent publie un heartbeat.
- [ ] Une lease expirée est détectée.
- [ ] Une reprise ne crée pas de double travailleur.
- [ ] La même clé d’idempotence n’est pas exécutée deux fois.
- [ ] Après deux échecs identiques, la job cesse de boucler.
- [ ] La dead-letter conserve tous les artefacts.

### Obsidian et Hermès

- [ ] Le coffre réel est détecté, pas inventé.
- [ ] Hermès est le seul écrivain automatique.
- [ ] Un memory pack est produit avant exécution.
- [ ] Le memory pack possède un SHA-256.
- [ ] Les sources Obsidian sont indiquées.
- [ ] Le résultat validé est mémorisé après les tests.
- [ ] La prochaine reprise exacte est écrite.
- [ ] Aucun secret n’est présent dans les notes.

### Sécurité et D-only

- [ ] Aucun nouveau chemin actif `C:\`.
- [ ] Aucune clé SSH privée lue ou affichée.
- [ ] Aucun processus vivant arrêté.
- [ ] Aucun push, merge ou force-push non autorisé.
- [ ] Aucun fichier supprimé par nettoyage destructif.

---

## 15. Critères de réussite finale

La boucle est considérée opérationnelle uniquement si :

1. elle traite une job de bout en bout;
2. elle prépare la suivante en parallèle;
3. tous les agents affectés produisent un travail utile;
4. aucune collision de fichiers ne survient;
5. une interruption simulée est récupérée;
6. une répétition de message ne crée pas de double exécution;
7. Copilot et Grok 3 valident l’intégration;
8. Jules prépare la publication sans la déclencher;
9. Hermès écrit le résultat final dans le coffre Obsidian réel;
10. la reprise exacte est disponible après redémarrage;
11. aucun secret et aucun chemin nouveau sur `C:\` n’ont été introduits;
12. Brutus conserve le contrôle des actions irréversibles.

---

## 16. Première action unique

Donner le prompt de la section 12 à Reine-LinuxIA / Codex principal.

Elle doit commencer en mode audit et `TestOnly` : détecter WorkerDock, le coffre Obsidian, les agents réellement disponibles, les worktrees, les chemins et les fonctions exportées. Elle ne doit annoncer l’activation de la boucle qu’après avoir fourni les preuves d’activité et passé les tests de concurrence, reprise et idempotence.
