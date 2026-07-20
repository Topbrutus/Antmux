# state.checkpoint.v1

Prototype déclaratif de **checkpoint immuable** pour Antmux Agent Skill v1.

## Statut

- **Paquet :** `state.checkpoint.v1`
- **Version :** `1.0.0`
- **État :** `PROPOSED`
- **Moteur SQLite :** absent
- **Création réelle de checkpoints :** interdite
- **Réseau :** interdit
- **Modèle Ollama :** aucun
- **Suppression ou réécriture :** interdite

## Rôle

Le paquet définit les contrats nécessaires pour :

- créer un nouvel enregistrement append-only;
- vérifier une chaîne de parents et ses empreintes;
- lire ou lister des checkpoints autorisés;
- créer une branche depuis un état historique;
- produire un plan de restauration non exécutable;
- activer une branche avec approbation humaine lorsque nécessaire;
- reconstruire une projection JSONL depuis une outbox SQLite.

Un rollback ne détruit jamais l'histoire : il crée une nouvelle branche.

## Contenu

- `skill.yaml` — manifeste de découverte, permissions et sécurité;
- `instructions.md` — procédure de décision;
- `prompts/checkpoint-operation.md` — prompt structuré;
- `resources/checkpoint-rules.md` — invariants d'intégrité;
- `resources/error-codes.md` — refus structurés;
- `schemas/input.schema.json` — contrat d'entrée Draft 7;
- `schemas/output.schema.json` — contrat de sortie Draft 7;
- `tests/*.tests.json` — cas déclaratifs;
- `tools/Test-StateCheckpointSkill.ps1` — validateur PowerShell 5.1 en lecture seule;
- `checksums.sha256` — empreintes du paquet.

## Validation locale en lecture seule

Depuis Windows PowerShell 5.1 :

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force

& ".\skills\state.checkpoint.v1\tools\Test-StateCheckpointSkill.ps1"
```

Le validateur ne crée aucune base SQLite, aucun checkpoint et aucun fichier temporaire. Il ne lance aucun modèle, processus enfant ou appel réseau.

Résultat obligatoire :

```text
ALL_TESTS: PASS
```

La réussite du validateur prouve uniquement la cohérence du paquet déclaratif. Elle n'autorise pas l'activation d'un moteur de persistance.
