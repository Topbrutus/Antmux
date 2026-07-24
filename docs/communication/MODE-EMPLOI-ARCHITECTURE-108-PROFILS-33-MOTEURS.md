# Mode d’emploi — Architecture de 108 profils de travailleurs et 33 moteurs

**Projet :** LinuxIA / Antmux  
**Décideur final :** Brutus  
**Constructeur :** Rob  
**Version :** 1.0  
**Date :** 24 juillet 2026  
**Statut :** architecture directrice à construire progressivement  
**Principe :** une chose à la fois

---

## 0. But du document

Ce mode d’emploi définit comment construire un système dans lequel :

- 108 profils spécialisés de travailleurs existent durablement;
- 33 moteurs CLI ou modèles sont disponibles dans un pool partagé;
- chaque travailleur conserve son identité, sa mémoire et son expérience;
- les moteurs peuvent être remplacés sans effacer le travailleur;
- chaque travailleur possède un bureau isolé;
- une bibliothèque commune distribue les compétences et procédures;
- 32 composants logiques assurent la communication interne;
- un 33e composant spécial protège la gouvernance;
- GitHub conserve la mémoire durable;
- le disque D conserve l’atelier runtime.

Ce document ne commande pas de créer les 108 travailleurs immédiatement. Il définit l’architecture et l’ordre de construction.

---

## 1. Principe fondateur

```text
Le travailleur n’est pas le moteur.
Le bureau n’est pas le programme.
La mémoire n’est pas le cache.
La bibliothèque n’est pas une copie de chaque bureau.
L’orchestrateur n’est pas le gouverneur.
```

Formule générale :

```text
108 profils persistants
        ↓
bureaux et mémoires isolés
        ↓
bibliothèque commune
        ↓
orchestrateur d’affectation
        ↓
33 moteurs partagés
        ↓
révision et validation
```

Couche de communication :

```text
32 composants logiques
+ 1 composant spécial de gouvernance
```

Cette couche est distincte des profils et des moteurs.

---

## 2. Définitions officielles

### 2.1 Profil de travailleur

Un profil est une identité durable.

Il contient :

- un identifiant immuable;
- un nom;
- un numéro;
- un département;
- une mission;
- des responsabilités;
- des permissions;
- des compétences;
- une mémoire;
- un historique;
- des relations;
- des réviseurs;
- des moteurs compatibles.

### 2.2 Bureau

Le bureau est l’espace de travail personnel du profil.

Il contient uniquement les données et artefacts nécessaires à ce travailleur.

Il ne contient pas une copie du moteur.

### 2.3 Moteur

Un moteur est une capacité d’exécution temporaire.

Exemples :

- OpenCode;
- Kimi Code;
- Gemini CLI;
- Antigravity;
- Hermes;
- Jules;
- Codex;
- Grok;
- Claude Code;
- modèle local;
- futur CLI.

### 2.4 Bibliothèque

La bibliothèque contient les ressources communes :

- procédures;
- patrons;
- normes;
- schémas;
- compétences;
- références;
- politiques;
- exemples validés;
- modes d’emploi;
- leçons réutilisables.

### 2.5 Orchestrateur

L’orchestrateur affecte une tâche à un profil et à un moteur.

Il ne remplace pas le travailleur et ne modifie pas les règles constitutionnelles.

### 2.6 Gouverneur ou 33e spécial

Le 33e spécial représente les règles supérieures :

- autorisation;
- cohérence;
- sécurité;
- arbitrage;
- limites;
- priorités;
- interdictions;
- preuve requise.

Il ne doit pas être un agent tout-puissant sans contrôle.

---

## 3. Organisation des 108 profils

Les 108 profils logiciels fournis par Brutus sont divisés en 15 départements.

### 3.1 Architecture et conception

Profils 1 à 10 :

1. Architecture globale;
2. Frontières de modules;
3. Domain-Driven Design;
4. Microservices;
5. Monolithe modulaire;
6. Event-Driven;
7. CQRS et Event Sourcing;
8. Dette technique;
9. Architecture Decision Records;
10. Scalabilité logicielle.

### 3.2 Backend

Profils 11 à 20 :

11. API REST;
12. API GraphQL;
13. API gRPC;
14. Authentification;
15. Files de messages;
16. Traitements asynchrones;
17. Services distribués;
18. Contrats d’API;
19. Résilience backend;
20. Idempotence.

### 3.3 Frontend

Profils 21 à 30 :

21. React;
22. Vue;
23. Svelte;
24. Angular;
25. Accessibilité;
26. Internationalisation;
27. Progressive Web App;
28. Performance navigateur;
29. Design System;
30. State Management.

### 3.4 Fullstack et intégration

Profils 31 à 36 :

31. Fullstack;
32. Intégration frontend/backend;
33. Authentification transversale;
34. Sessions;
35. Synchronisation offline/online;
36. Contrats partagés.

### 3.5 Systèmes et performance

Profils 37 à 44 :

37. Systèmes bas niveau;
38. Concurrence;
39. Parallélisme;
40. Temps réel;
41. Gestion mémoire;
42. Profiling;
43. WebAssembly;
44. Optimisation CPU/GPU.

### 3.6 Mobile

Profils 45 à 50 :

45. iOS;
46. Android;
47. React Native;
48. Flutter;
49. Publication stores;
50. Contraintes mobiles.

### 3.7 Embarqué et IoT

Profils 51 à 56 :

51. Logiciel embarqué;
52. Temps réel embarqué;
53. Communication hardware;
54. Edge software;
55. Contraintes ressources;
56. OTA.

### 3.8 Données

Profils 57 à 64 :

57. Architecture de données;
58. Modélisation de données;
59. SQL avancé;
60. NoSQL;
61. Migrations;
62. Optimisation de requêtes;
63. Caching de données;
64. Intégrité des données.

### 3.9 Data et pipelines

Profils 65 à 70 :

65. Pipelines;
66. ETL/ELT;
67. Streaming;
68. Qualité des données;
69. Feature engineering;
70. Gouvernance data.

### 3.10 Machine Learning et MLOps

Profils 71 à 77 :

71. Entraînement de modèles;
72. Déploiement de modèles;
73. Model serving;
74. Évaluation de modèles;
75. Versionnement de modèles;
76. Monitoring de modèles;
77. MLOps.

### 3.11 LLM et agents

Profils 78 à 84 :

78. Prompt engineering;
79. Intégration LLM;
80. Tool calling;
81. Mémoire d’agents;
82. Frameworks d’agents;
83. Orchestration multi-agents;
84. Évaluation d’agents.

### 3.12 Plateforme et DevOps

Profils 85 à 93 :

85. CI/CD;
86. Conteneurs;
87. Orchestration de conteneurs;
88. Infrastructure as Code;
89. Build systems;
90. Packages;
91. Dépendances;
92. Releases;
93. Feature flags.

### 3.13 Qualité et tests

Profils 94 à 100 :

94. Stratégie de tests;
95. Tests unitaires;
96. Tests d’intégration;
97. Tests end-to-end;
98. Property-based testing;
99. Mutation testing;
100. Tests de charge.

### 3.14 Sécurité applicative

Profils 101 à 104 :

101. Sécurité applicative;
102. Modélisation des menaces;
103. Revue sécurité;
104. Dépendances vulnérables.

### 3.15 Fiabilité et observabilité

Profils 105 à 108 :

105. Observabilité;
106. Debugging avancé;
107. Analyse d’incidents;
108. Fiabilité et recovery.

---

## 4. Structure du disque D

Structure cible proposée :

```text
D:\
├── workers\
│   └── software\
│       ├── 001-architecture-globale\
│       ├── 002-frontieres-modules\
│       ├── ...
│       └── 108-fiabilite-recovery\
│
├── engines\
│   ├── registry\
│   ├── launchers\
│   ├── adapters\
│   └── health\
│
├── library\
│   ├── procedures\
│   ├── skills\
│   ├── standards\
│   ├── schemas\
│   ├── examples\
│   └── lessons\
│
├── orchestration\
│   ├── jobs\
│   ├── queue\
│   ├── routing\
│   ├── assignments\
│   └── checkpoints\
│
└── runtime\
    ├── logs\
    ├── cache\
    ├── temp\
    └── locks\
```

Cette structure est une cible. Elle ne doit pas être créée intégralement avant validation du profil canonique.

---

## 5. Structure canonique d’un bureau

Exemple pour le profil 011 :

```text
D:\workers\software\011-api-rest\
├── worker.yaml
├── STATE.md
├── permissions.yaml
├── engine-policy.yaml
├── skills.yaml
├── memory\
│   ├── decisions.md
│   ├── lessons.md
│   ├── incidents.jsonl
│   ├── patterns.md
│   └── index.json
├── inbox\
├── outbox\
├── workspace\
├── checkpoints\
└── logs\
```

### 5.1 `worker.yaml`

Contient l’identité stable.

Exemple :

```yaml
schema_version: antmux.worker-profile.v1

id: worker.software.backend.rest
number: 11
name: Travailleur API REST
office: Bureau API REST
department: backend

mission: >
  Concevoir, analyser, maintenir et réviser des API REST robustes,
  cohérentes, testables et documentées.

status: DORMANT

responsibilities:
  - contrats HTTP
  - ressources
  - méthodes
  - codes de statut
  - pagination
  - erreurs
  - versionnement
  - compatibilité

default_permissions:
  read: true
  propose_changes: true
  write: false
  execute: false
  commit: false
  push: false
  production: false

reviewers:
  - worker.software.testing.integration
  - worker.software.security.review
  - worker.software.architecture.global
```

### 5.2 `STATE.md`

Contient uniquement l’état courant vérifiable :

- tâche actuelle;
- identifiant JOB;
- moteur affecté;
- statut;
- dernier checkpoint;
- blocage;
- prochaine action.

### 5.3 `permissions.yaml`

Définit :

- chemins lisibles;
- chemins modifiables;
- commandes permises;
- commandes interdites;
- accès réseau;
- accès aux secrets;
- autorisations exceptionnelles;
- réviseur obligatoire.

### 5.4 `engine-policy.yaml`

Définit les moteurs compatibles et interdits.

Exemple :

```yaml
preferred:
  - opencode
  - kimi
  - codex

allowed:
  - gemini-cli
  - hermes
  - local-model

forbidden_for_sensitive_code:
  - unverified-free-provider

selection:
  optimize_for:
    - correctness
    - privacy
    - quota
    - cost
```

---

## 6. Registre des 33 moteurs

Chaque moteur doit avoir une fiche séparée.

Exemple :

```text
D:\engines\registry\opencode.yaml
```

Schéma minimal :

```yaml
schema_version: antmux.engine.v1

id: opencode
type: cli-router
command: opencode
status: AVAILABLE

version: 1.18.4

platforms:
  - windows

providers:
  - opencode-zen
  - google
  - zai

capabilities:
  read_files: true
  write_files: configurable
  shell: configurable
  git: configurable
  multi_model: true

limits:
  concurrent_jobs: 1
  rate_limit_behavior: provider_dependent
  context_limit: unknown

cost:
  mode: mixed
  requires_verification: true

security:
  secrets_in_logs: forbidden
  default_mode: read_only
```

Le registre doit contenir des faits vérifiés, pas des impressions.

---

## 7. États d’un travailleur

États officiels proposés :

```text
REGISTERED
DORMANT
RESERVED
LOADING
READY
RUNNING
WAITING_RATE_LIMIT
RESULT_PROPOSED
UNDER_REVIEW
VALIDATED
REJECTED
BLOCKED
UNLOADING
UNLOADED
```

### 7.1 `WAITING_RATE_LIMIT`

Cet état est obligatoire pour les fournisseurs qui imposent un timer.

Il doit conserver :

- JOB;
- profil;
- moteur;
- dernière commande;
- dernier résultat;
- checkpoint;
- heure de reprise;
- nombre de tentatives;
- clé d’idempotence.

Le système ne doit pas recommencer aveuglément toute la tâche.

---

## 8. Cycle complet d’un JOB

```text
1. Brutus formule la demande.
2. L’Interprète reformule sans exécuter.
3. Le routeur identifie le département.
4. Le routeur sélectionne un profil.
5. Le gouverneur vérifie les permissions.
6. L’orchestrateur sélectionne un moteur.
7. Un checkpoint PRE_ACTION est créé.
8. Le profil travaille avec le moteur.
9. Le résultat devient RESULT_PROPOSED.
10. Un réviseur indépendant vérifie les preuves.
11. Le résultat devient VALIDATED ou REJECTED.
12. Un checkpoint POST_ACTION est créé.
13. La mémoire durable est mise à jour.
14. Le moteur est libéré.
15. Le profil retourne à DORMANT.
```

---

## 9. Algorithme d’affectation profil ↔ moteur

L’affectation ne doit jamais être fixe.

Ordre de décision :

1. compatibilité avec la mission;
2. accès requis;
3. confidentialité;
4. fiabilité historique;
5. qualité attendue;
6. quota;
7. coût;
8. vitesse;
9. contexte maximal;
10. disponibilité;
11. état du fournisseur;
12. besoin de reprise.

Pseudo-règle :

```text
sélectionner uniquement un moteur :
- autorisé pour le profil;
- disponible;
- suffisamment fiable;
- dont le quota n’est pas bloqué;
- dont le coût est accepté;
- dont les outils couvrent la tâche.
```

---

## 10. Politique de mémoire

### 10.1 Mémoire durable sur GitHub

Doivent être versionnés :

- profils;
- missions;
- permissions;
- décisions validées;
- leçons;
- procédures;
- schémas;
- index;
- normes;
- résumés de sessions;
- états stables;
- rapports validés.

### 10.2 Mémoire locale sur D

Doivent rester locaux :

- contexte courant;
- scratchpad;
- cache;
- temporaires;
- sortie brute;
- journaux volumineux;
- états runtime;
- fichiers de verrouillage;
- résultats non validés.

### 10.3 Secrets

Interdit :

- clé API dans Markdown;
- secret dans JSONL;
- secret dans commit;
- secret dans prompt sauvegardé;
- secret dans log.

Autorisé seulement par mécanisme sécurisé :

- Keyring;
- Credential Manager;
- variable runtime;
- coffre approuvé.

---

## 11. Bibliothèque commune

La bibliothèque ne doit pas dupliquer les mémoires personnelles.

Exemple :

```text
D:\library\skills\backend\rest\
├── SKILL.md
├── checklist.md
├── schemas\
├── tests\
└── examples\
```

Un profil lit la compétence commune, puis conserve seulement :

- décisions propres;
- leçons propres;
- incidents propres;
- préférences validées;
- expérience liée à ses missions.

---

## 12. Communication logique

Les 32 composants logiques doivent être lus depuis leur source canonique avant intégration.

Ce mode d’emploi fixe seulement leur fonction générale :

- transporter les intentions;
- représenter les états;
- exprimer les autorisations;
- transmettre les événements;
- lier les JOB;
- imposer les contrats;
- assurer la traçabilité;
- séparer proposition, révision et validation.

Le 33e spécial assure :

- constitution;
- règles absolues;
- arbitrage;
- sécurité;
- cohérence.

Règle :

```text
Ne jamais inventer la liste exacte des 32 composants.
Lire la source canonique.
```

---

## 13. Politique de preuve

Un travailleur ne peut pas conclure à partir d’une absence dans un README.

Ordre de preuve recommandé :

1. fichier réel;
2. `git ls-files`;
3. commande de validation;
4. test ciblé;
5. sortie avec code;
6. documentation;
7. inférence explicitement marquée.

Exemple Laguna :

```text
README incomplet
≠
fichier absent
```

Autre exemple :

```text
PySide6 absent du Python global
≠
point d’entrée cassé
```

---

## 14. Politique de revue

Chaque résultat important doit avoir un réviseur indépendant.

Exemples :

```text
API REST
→ réviseur Tests d’intégration
→ réviseur Sécurité
```

```text
CI/CD
→ réviseur Fiabilité
→ réviseur Sécurité
```

```text
Orchestration multi-agents
→ réviseur Mémoire d’agents
→ réviseur Évaluation d’agents
→ gouvernance spéciale
```

Le même moteur ne doit pas être considéré automatiquement comme un réviseur indépendant s’il réutilise exactement le même contexte et les mêmes hypothèses.

---

## 15. Découverte de nouveaux CLI

La veille CLI devient un workflow de bibliothèque.

Entrée :

```text
nom de modèle + CLI
```

Sortie normalisée :

```yaml
name: exemple-cli
status: TO_REVIEW
license: unknown
price: unknown
platform: unknown
last_release: unknown
repository: unknown
security_review: pending
recommended_action: WATCH
```

États :

```text
DISCOVERED
VERIFIED
INSTALLED
TESTING
ACTIVE
WATCH
REJECTED
RETIRED
```

Interdictions :

- aucune installation automatique;
- aucune clé enregistrée sans autorisation;
- aucun accès au dépôt live pendant le premier test;
- aucun classement « gratuit » sans vérifier les limites;
- aucun moteur ajouté au pool sans micro-test.

---

## 16. Tests obligatoires d’un nouveau moteur

### Test A — identité

Vérifier le nom, la version et le fournisseur.

### Test B — lecture seule

Lire deux fichiers sans modification.

### Test C — preuves

Exiger les chemins exacts.

### Test D — correction

Donner une preuve contraire et vérifier qu’il se corrige.

### Test E — environnement

Utiliser l’environnement réel du projet.

### Test F — rate limit

Observer le comportement en attente.

### Test G — secret

Vérifier qu’aucune clé n’apparaît dans les sorties.

### Test H — dépôt

Vérifier qu’aucun fichier n’a changé :

```text
git status
git diff --check
```

Classification finale :

```text
SCOUT
WORKER
REVIEWER
UNTRUSTED
```

---

## 17. Montée en charge

### Phase 0 — gel

- ne rien générer en masse;
- conserver la liste des 108;
- conserver la cible des 33 moteurs.

### Phase 1 — action suivante unique

Créer le profil canonique d’un travailleur.

Livrables :

- schéma;
- exemple;
- tests;
- règles;
- validation humaine.

### Phase 2 — premier profil

Créer un seul profil réel.

Candidat recommandé :

```text
001 Architecture globale
```

### Phase 3 — trois profils pilotes

Après validation du premier :

- Architecture globale;
- API REST;
- Stratégie de tests.

### Phase 4 — trois moteurs pilotes

Utiliser au maximum trois moteurs déjà vérifiés.

### Phase 5 — routage manuel

Affecter manuellement chaque JOB.

### Phase 6 — orchestrateur minimal

Automatiser uniquement l’affectation déjà prouvée manuellement.

### Phase 7 — montée progressive

```text
3 profils
→ 9 profils
→ 15 départements
→ 33 profils
→ 108 profils
```

Les 33 moteurs ne doivent pas être actifs simultanément.

---

## 18. Critères d’acceptation du profil canonique

Le modèle est accepté seulement si :

- l’identité ne dépend pas du moteur;
- la mémoire est séparée du cache;
- les permissions sont explicites;
- le bureau est léger;
- aucun secret n’est présent;
- les états sont définis;
- la pause de quota est gérée;
- la preuve est obligatoire;
- la revue indépendante est définie;
- le profil peut changer de moteur;
- le profil revient à DORMANT;
- GitHub et D ont des responsabilités distinctes.

---

## 19. Interdictions absolues

1. Créer 108 dossiers avant validation du modèle.
2. Copier 33 moteurs dans 108 bureaux.
3. Associer définitivement un profil à un moteur.
4. Donner des permissions d’écriture par défaut.
5. Laisser un fournisseur gratuit accéder au dépôt live sans test.
6. Confondre attente de quota et travail actif.
7. Confondre erreur d’environnement et erreur du code.
8. Sauvegarder une clé API.
9. Déclarer `VALIDATED` sans réviseur.
10. Construire l’orchestrateur avant les profils.

---

## 20. Commandement opérationnel

```text
Comprendre
→ Structurer
→ Vérifier l’état
→ Planifier
→ Vérifier les risques
→ Exécuter
→ Vérifier
→ Mémoriser
→ Améliorer
→ Recommencer
```

Priorités :

```text
Accuracy
> Safety
> Robustness
> Coherence
> Speed
```

---

## 21. Action immédiate

```text
Créer le profil canonique d’un travailleur.
```

Aucune autre construction ne doit précéder sa validation.

---

## 22. Résumé final

```text
108 profils = les travailleurs
33 moteurs = les capacités d’exécution
15 départements = l’organisation
1 bureau par profil = identité et mémoire isolées
1 bibliothèque = savoir commun
32 composants logiques = langage interne
1 composant spécial = gouvernance
GitHub = mémoire durable
D: = atelier vivant
orchestrateur = affectation future
```
