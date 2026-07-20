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

## Limite de sécurité

Ce paquet ne contient aucun moteur d’exécution. Il décrit un contrat vérifiable. Toute activation future devra démontrer :

```text
ALL_TESTS: PASS
```

et être autorisée explicitement par Brutus.
