# Antmux Agent Skill v1

## Statut

- **Version de spécification :** `antmux-agent-skill-v1`
- **Statut :** proposition de référence prête à prototyper
- **Dépôt :** `Topbrutus/Antmux`
- **Portée :** définition, découverte, chargement, permissions, exécution, télémétrie et validation des compétences agentives
- **Implémentation :** aucune dans ce document

---

## 1. But

Une compétence Antmux est un paquet autonome qui indique à un agent :

1. quand une procédure est pertinente;
2. quelles instructions doivent être chargées;
3. quelles ressources peuvent être consultées;
4. quels outils peuvent être appelés;
5. quelles actions sont interdites;
6. comment l’exécution doit être journalisée;
7. comment le résultat doit être validé.

La compétence ne remplace ni l’agent, ni l’outil, ni la mémoire. Elle relie ces éléments dans un contrat explicite et vérifiable.

---

## 2. Principes obligatoires

### 2.1 Refus par défaut

Tout outil, chemin, ressource, modèle, réseau ou mutation non explicitement autorisé est interdit.

### 2.2 Double application des permissions

Une permission doit être appliquée à deux endroits :

- **découverte :** l’agent ne voit pas les outils interdits;
- **exécution :** l’orchestrateur refuse tout appel non autorisé, même si le modèle le forge directement.

Masquer un outil dans l’interface ne constitue jamais une mesure de sécurité suffisante.

### 2.3 Chargement progressif

Antmux charge d’abord les métadonnées légères :

- identifiant;
- version;
- description;
- déclencheurs;
- niveau de risque;
- outils autorisés.

Les instructions détaillées et ressources volumineuses sont chargées seulement après sélection de la compétence.

### 2.4 Séparation des responsabilités

| Élément | Responsabilité |
|---|---|
| Compétence | Choisir et encadrer le workflow |
| Prompt | Décrire une procédure réutilisable |
| Ressource | Fournir de l’information consultable |
| Outil | Exécuter une opération contrôlée |
| Agent | Raisonner et produire un résultat |
| Reviewer | Vérifier le résultat et les preuves |
| Orchestrateur | Appliquer les permissions et l’état |

### 2.5 État explicite

Aucun état critique ne doit exister uniquement dans le contexte du modèle. Les décisions, appels, résultats, erreurs et validations doivent être inscrits dans SQLite, JSONL ou des artefacts immuables.

### 2.6 Version verrouillée

Une compétence et ses dépendances doivent être associées à :

- une version exacte;
- une empreinte SHA-256;
- un schéma d’entrée;
- un schéma de sortie;
- un protocole de validation.

`latest` est interdit dans les environnements contrôlés.

---

## 3. Structure recommandée d’un paquet

```text
skills/
└── reviewer.scientific.v1/
    ├── skill.yaml
    ├── instructions.md
    ├── prompts/
    │   └── review-pattern.md
    ├── resources/
    │   ├── evidence-rules.md
    │   └── decision-classes.md
    ├── schemas/
    │   ├── input.schema.json
    │   └── output.schema.json
    ├── tests/
    │   ├── manifest.tests.json
    │   ├── permissions.tests.json
    │   └── contracts.tests.json
    └── checksums.sha256
```

Le fichier `skill.yaml` est le seul document requis pour la découverte initiale. Les autres fichiers sont chargés à la demande.

---

## 4. Manifeste `skill.yaml`

### 4.1 Exemple complet

```yaml
schema_version: antmux-agent-skill-v1

skill_id: reviewer.scientific
version: 1.0.0
status: proposed

identity:
  title: Reviewer scientifique
  description: >
    Vérifie les patrons extraits d’une source scientifique, contrôle
    les preuves exactes et empêche les analogies de devenir des faits.
  owner: Antmux

selection:
  triggers:
    - audit scientifique
    - valider les preuves
    - vérifier un rapport Worker
  excludes:
    - produire du code de production
    - modifier la source analysée
  priority: 70

loading:
  mode: progressive
  metadata_first: true
  instructions:
    - instructions.md
  prompts:
    - prompts/review-pattern.md
  resources:
    - resources/evidence-rules.md
    - resources/decision-classes.md

inputs:
  schema: schemas/input.schema.json
  required:
    - worker_report
    - worker_json
    - numbered_source

outputs:
  schema: schemas/output.schema.json
  artifacts:
    - review_json
    - review_report

permissions:
  default_deny: true

  tools:
    allow:
      - source.read
      - report.read
      - review.write
    deny:
      - github.push
      - process.kill
      - filesystem.delete
      - browser.send_message

  filesystem:
    read:
      - inputs/**
      - analysis/worker/**
    write:
      - analysis/reviewer/**
      - reports/**
    deny:
      - .git/**
      - secrets/**

  network:
    allowed: false
    destinations: []

  models:
    allow:
      - local-reviewer

execution:
  protocol_version: antmux-mcp-v1
  transport:
    allow:
      - stdio
  require_task_id: true
  require_agent_id: true
  require_run_id: true
  require_correlation_id: true
  timeout_seconds: 900
  max_attempts: 2
  parallelism: 1

safety:
  risk_level: medium
  read_only: false
  destructive: false
  idempotent: true
  open_world: false
  mutation_allowed: false
  human_approval:
    before_start: false
    before_external_write: true
    before_destructive_action: true

telemetry:
  rent_enabled: true
  record:
    - messages_in
    - messages_out
    - bytes_read
    - bytes_written
    - resources_loaded
    - tools_called
    - prompt_chars
    - response_chars
    - wait_ms
    - inference_ms
    - retries
    - denied_calls

validation:
  manifest_schema: antmux-agent-skill-v1
  input_schema_required: true
  output_schema_required: true
  independent_reviewer: true
  require_source_line_ids: true
  require_checksums: true
  pass_requires_all_tests: true

lifecycle:
  states:
    - DISCOVERED
    - SELECTED
    - LOADED
    - AUTHORIZED
    - RUNNING
    - UNDER_REVIEW
    - VALIDATED
    - REJECTED
    - FAILED
    - ROLLED_BACK
```

---

## 5. Sémantique des champs

### `skill_id`

Identifiant stable et unique. Il ne doit pas inclure la version.

### `version`

Version sémantique du paquet. Toute modification de contrat exige une nouvelle version.

### `selection.triggers`

Expressions courtes utilisées pour proposer la compétence. Elles ne donnent aucune permission.

### `loading.mode`

Valeur initiale : `progressive`.

Antmux ne doit pas charger automatiquement toutes les instructions et ressources de toutes les compétences.

### `permissions.default_deny`

Doit toujours être `true` pour une compétence contrôlée.

### `permissions.tools.allow`

Liste exacte des outils exposés et exécutables.

Un outil absent de cette liste est refusé, même s’il existe dans le registre global.

### `safety.read_only`

Indique l’intention générale. Les permissions de fichiers et d’outils restent l’autorité finale.

### `safety.destructive`

Indique que la compétence peut supprimer, écraser, révoquer ou rendre inaccessible une ressource.

### `safety.idempotent`

Indique qu’une répétition contrôlée avec les mêmes entrées ne doit pas créer d’effet supplémentaire indésirable.

### `safety.open_world`

Indique que la compétence communique avec Internet, un service externe ou un environnement hors du projet local.

---

## 6. Cycle de vie

```text
DISCOVERED
→ SELECTED
→ LOADED
→ AUTHORIZED
→ RUNNING
→ UNDER_REVIEW
→ VALIDATED
```

Branches d’échec :

```text
AUTHORIZED → REJECTED
RUNNING → FAILED
RUNNING → ROLLED_BACK
UNDER_REVIEW → REJECTED
```

### Règles

- Aucun passage vers `AUTHORIZED` sans vérification du manifeste.
- Aucun passage vers `RUNNING` sans identifiants d’exécution.
- Aucun passage vers `VALIDATED` sans schéma de sortie valide.
- Une compétence marquée `destructive: true` exige une autorisation humaine avant l’action destructive.
- Une compétence externe ne peut pas être considérée idempotente sans test.

---

## 7. Enveloppe obligatoire d’un appel d’outil

Chaque appel doit porter une identité vérifiable :

```json
{
  "protocol_version": "antmux-mcp-v1",
  "method": "tools/call",
  "tool_name": "source.read",
  "skill_id": "reviewer.scientific",
  "skill_version": "1.0.0",
  "task_id": "TASK-0042",
  "agent_id": "reviewer-01",
  "run_id": "RUN-20260720-0042",
  "correlation_id": "CORR-20260720-0042-001",
  "timestamp_utc": "2026-07-20T18:00:00Z"
}
```

Les champs suivants sont obligatoires :

- `protocol_version`;
- `method`;
- `tool_name`;
- `skill_id`;
- `skill_version`;
- `task_id`;
- `agent_id`;
- `run_id`;
- `correlation_id`;
- `timestamp_utc`.

---

## 8. Vérification des permissions

### 8.1 Avant la découverte

Le registre calcule les compétences accessibles selon :

- le projet;
- le rôle;
- l’agent;
- l’environnement;
- les modèles disponibles;
- les ressources présentes.

### 8.2 Avant l’exposition des outils

Seuls les outils de `permissions.tools.allow` sont transmis à l’agent.

### 8.3 Avant chaque exécution

L’orchestrateur vérifie à nouveau :

1. l’outil est dans la liste blanche;
2. la compétence est autorisée;
3. le rôle courant correspond;
4. le chemin demandé respecte les règles;
5. le réseau demandé est permis;
6. l’identifiant de tâche existe;
7. la limite de tentatives n’est pas dépassée;
8. l’approbation humaine est présente lorsqu’elle est requise.

### 8.4 Refus structuré

```json
{
  "ok": false,
  "error_code": "TOOL_NOT_ALLOWED",
  "tool_name": "github.push",
  "skill_id": "reviewer.scientific",
  "task_id": "TASK-0042",
  "reason": "The tool is absent from permissions.tools.allow."
}
```

Un refus doit être inscrit au journal Rent.

---

## 9. Télémétrie Rent

Pour chaque exécution :

```json
{
  "task_id": "TASK-0042",
  "run_id": "RUN-20260720-0042",
  "skill_id": "reviewer.scientific",
  "agent_id": "reviewer-01",
  "messages_in": 4,
  "messages_out": 2,
  "bytes_read": 18342,
  "bytes_written": 4811,
  "resources_loaded": 2,
  "tools_called": 3,
  "prompt_chars": 9211,
  "response_chars": 2844,
  "wait_ms": 314,
  "inference_ms": 18432,
  "retries": 0,
  "denied_calls": 0,
  "result_state": "UNDER_REVIEW"
}
```

Aucun seuil universel n’est défini dans cette spécification. Les seuils doivent être établis par comparaison expérimentale.

---

## 10. Ressources et mémoire Bermuda

Une compétence peut lire des ressources classées selon l’état de validation :

- `RAW`;
- `PROPOSED`;
- `UNDER_REVIEW`;
- `VALIDATED`;
- `REJECTED`;
- `SUPERSEDED`.

Par défaut :

- un Worker peut lire `RAW`, `PROPOSED` et `VALIDATED`;
- un Reviewer doit voir l’état et la provenance;
- une décision durable ne peut citer `RAW` comme vérité validée;
- une ressource `REJECTED` ne doit pas être injectée sans justification explicite;
- une ressource `SUPERSEDED` doit pointer vers son remplacement.

---

## 11. Contrats de schéma

### 11.1 Entrées

Chaque compétence doit déclarer un JSON Schema d’entrée.

### 11.2 Sorties

Chaque résultat structuré doit être un objet JSON. Une liste brute doit être enveloppée :

```json
{
  "items": []
}
```

Cette règle évite les incompatibilités entre SDK qui exigent un objet pour le contenu structuré.

### 11.3 Compatibilité

Les schémas sont générés ou enregistrés en JSON Schema Draft 7 pour la première version d’Antmux Agent Skill.

Une migration de bibliothèque de validation ne doit pas modifier silencieusement :

- les champs obligatoires;
- les valeurs par défaut;
- la représentation des tableaux;
- les erreurs de validation;
- les propriétés supplémentaires.

---

## 12. Commandes CLI proposées

```powershell
antmux skills list
antmux skills inspect reviewer.scientific@1.0.0
antmux skills validate reviewer.scientific@1.0.0
antmux skills test reviewer.scientific@1.0.0

antmux prompts list
antmux resources list
antmux tools list

antmux tools available `
  --agent reviewer-01 `
  --task TASK-0042

antmux permissions explain `
  --agent reviewer-01 `
  --tool github.push
```

### Exemple de résultat

```text
AVAILABLE : source.read
AVAILABLE : report.read
AVAILABLE : review.write
DENIED    : github.push
DENIED    : process.kill
DENIED    : filesystem.delete
```

---

## 13. Tests minimaux obligatoires

### Manifeste

- schéma valide;
- identifiant valide;
- version valide;
- fichiers référencés présents;
- checksums valides;
- aucune permission contradictoire.

### Permissions

- outil autorisé visible;
- outil interdit invisible;
- appel direct d’un outil interdit refusé;
- chemin hors périmètre refusé;
- réseau refusé lorsque `allowed: false`;
- approbation exigée pour une action destructive.

### Contrats

- entrée valide acceptée;
- entrée invalide refusée;
- sortie valide acceptée;
- tableau brut refusé ou enveloppé;
- champs obligatoires préservés;
- valeurs par défaut préservées.

### Cycle de vie

- transition normale complète;
- échec avant autorisation;
- échec pendant l’exécution;
- rejet du Reviewer;
- rollback vérifiable;
- reprise idempotente.

### Journalisation

- chaque appel possède un `correlation_id`;
- chaque refus est journalisé;
- aucun secret n’est journalisé;
- les métriques Rent sont complètes;
- le résultat final pointe vers ses artefacts.

Résultat obligatoire avant activation :

```text
ALL_TESTS: PASS
```

---

## 14. Critères d’acceptation de la V1

La V1 est acceptée lorsque :

1. un paquet de démonstration est découvert sans charger ses ressources complètes;
2. l’agent voit uniquement les outils autorisés;
3. un appel forgé vers un outil interdit est refusé par l’orchestrateur;
4. les entrées et sorties sont validées par schéma;
5. chaque appel est associé à une tâche, un agent, un run et une corrélation;
6. la télémétrie Rent est enregistrée;
7. un Reviewer indépendant peut accepter ou rejeter le résultat;
8. la reprise après interruption ne duplique pas les écritures;
9. les empreintes SHA-256 du paquet sont vérifiées;
10. aucun secret ni identifiant sensible n’apparaît dans les journaux.

---

## 15. Prototype recommandé

Premier paquet à construire :

```text
reviewer.scientific.v1
```

Raisons :

- périmètre limité;
- réseau interdit;
- peu d’outils;
- sorties structurées;
- besoin déjà identifié dans LinuxIA Neuro Patterns;
- résultat vérifiable sur les 23 patrons existants.

Le prototype ne doit pas commencer par un agent capable de pousser sur GitHub, de supprimer des fichiers ou de contrôler des processus.

---

## 16. Non-objectifs de la V1

La première version ne cherche pas à :

- installer Firebase;
- dépendre de Firebase;
- reproduire toute la spécification MCP;
- permettre la mutation automatique des rôles;
- donner Internet à tous les agents;
- remplacer SQLite ou JSONL;
- supprimer la validation humaine pour les actions sensibles;
- charger toutes les compétences dans chaque contexte;
- automatiser un push GitHub.

---

## 17. Provenance technique de la récolte

Cette spécification est inspirée de patrons observés dans le serveur MCP officiel de Firebase, notamment :

- séparation `Tools / Prompts / Resources`;
- métadonnées d’outils (`readOnly`, `destructive`, `idempotent`, `openWorld`);
- détection du projet et des fonctions disponibles;
- vérification de l’authentification et du projet avant appel;
- filtrage `allowedTools` à la découverte et à l’exécution;
- identification de la version du protocole, de la méthode et du nom de l’outil;
- transport local `stdio` et mode réseau;
- schémas d’entrée produits en JSON Schema Draft 7;
- tests de contrats après changements de SDK.

Références vérifiées :

- `firebase/firebase-tools`, `src/mcp/README.md`;
- `firebase/firebase-tools`, `src/mcp/index.ts`;
- `firebase/firebase-tools`, `src/mcp/tool.ts`;
- commit `745519db51b90a5b98cf80dd8a1c92038ea9eb36` — filtrage `allowedTools`;
- commit `ab31956207b09b76ca0c2f8c84bf426b76e18d33` — identité des appels HTTP MCP;
- commit `782585a7baa147a3a4f6586c6065208928c1a73c` — migration Zod 4 et JSON Schema;
- commit `94da71dbf54b4b75ae90614b4a6e5393c72b8b0e` — enveloppe objet pour les tableaux structurés.

Antmux ne copie pas l’implémentation Firebase. Il récolte les patrons d’architecture et les adapte à une plateforme locale, vérifiable et contrôlée par Brutus.

---

## 18. Prochaine action unique

Construire le paquet de démonstration :

```text
skills/reviewer.scientific.v1/
```

avec :

- un manifeste `skill.yaml`;
- un schéma d’entrée;
- un schéma de sortie;
- une ressource de règles de preuve;
- des tests de permissions;
- aucune exécution réelle avant validation de tous les contrats.
