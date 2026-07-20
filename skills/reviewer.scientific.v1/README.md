# reviewer.scientific.v1

Prototype de référence pour **Antmux Agent Skill v1**.

Cette compétence examine des patrons extraits par un Worker, confronte chaque affirmation aux lignes exactes de la source, puis produit un verdict structuré. Elle ne modifie pas les sources, ne communique pas avec Internet et ne peut pas pousser sur GitHub.

## Statut

- **Paquet :** `reviewer.scientific.v1`
- **Version :** `1.0.0`
- **État :** `PROPOSED`
- **Exécution réelle :** interdite avant validation de tous les contrats
- **Modèle autorisé :** `local-reviewer`
- **Transport autorisé :** `stdio`
- **Réseau :** interdit
- **Mutation de rôle :** interdite

## Contenu

- `skill.yaml` — manifeste de découverte et d’autorisation;
- `instructions.md` — procédure complète chargée après sélection;
- `prompts/review-pattern.md` — prompt de travail réutilisable;
- `resources/evidence-rules.md` — règles de preuve;
- `resources/decision-classes.md` — taxonomie des décisions;
- `schemas/input.schema.json` — contrat d’entrée;
- `schemas/output.schema.json` — contrat de sortie;
- `tests/*.tests.json` — cas de validation déclaratifs;
- `tools/Test-ReviewerScientificSkill.ps1` — point d’entrée du validateur PowerShell 5.1 en lecture seule;
- `tools/lib/*.ps1` — modules internes YAML, contrats, permissions et intégrité;
- `checksums.sha256` — empreintes SHA-256 du paquet.

## Entrées attendues

1. rapport Markdown du Worker;
2. sortie JSON du Worker;
3. source numérotée ligne par ligne;
4. identifiants `task_id`, `run_id`, `agent_id` et `correlation_id`;
5. empreintes SHA-256 des trois artefacts.

## Sorties attendues

- un JSON conforme à `schemas/output.schema.json`;
- un rapport Markdown dérivé du JSON;
- une décision pour chaque patron;
- un sommaire des comptes;
- les preuves exactes utilisées;
- la provenance et les empreintes des entrées.

## Validation locale en lecture seule

Depuis PowerShell 5.1 :

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force

& ".\skills\reviewer.scientific.v1\tools\Test-ReviewerScientificSkill.ps1"
```

Le validateur :

- ne lance aucun modèle Ollama;
- ne crée, ne modifie et ne supprime aucun fichier;
- n’effectue aucun appel réseau;
- vérifie les fichiers requis et les références du manifeste;
- parse les schémas et suites JSON;
- simule les treize décisions de permissions;
- exécute les quinze cas de contrats en mémoire;
- recalcule toutes les empreintes SHA-256 du paquet.

Résultat exigé :

```text
ALL_TESTS: PASS
```

Pour recevoir également un objet de résultat dans le pipeline PowerShell :

```powershell
& ".\skills\reviewer.scientific.v1\tools\Test-ReviewerScientificSkill.ps1" -PassThru
```

## Limite de sécurité

Ce paquet ne contient aucun moteur d’exécution. Le validateur contrôle uniquement les contrats et l’intégrité du paquet. Toute activation future de `local-reviewer` devra démontrer :

```text
ALL_TESTS: PASS
```

et être autorisée explicitement par Brutus.
