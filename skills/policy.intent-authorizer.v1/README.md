# policy.intent-authorizer.v1

Prototype déclaratif d’**autorisation déterministe par intention** pour Antmux Agent Skill v1.

## Statut

- **Paquet :** `policy.intent-authorizer.v1`
- **Version :** `1.0.0`
- **État :** `PROPOSED`
- **Moteur d’autorisation :** absent
- **Exécution d’outils métier :** interdite
- **Réseau :** interdit
- **Modèle Ollama :** aucun
- **Auto-autorisation par un modèle :** interdite

## Rôle

Le paquet définit les contrats nécessaires pour comparer, avant une action :

1. les permissions statiques du skill et de l’agent;
2. l’enveloppe d’intention confirmée;
3. l’action exacte et ses arguments;
4. les politiques de risque;
5. les approbations humaines;
6. le budget Rent courant et estimé.

La décision est exactement l’une des valeurs suivantes :

```text
ALLOW
DENY
REQUIRE_HUMAN_APPROVAL
```

Une approbation humaine peut satisfaire une exigence d’approbation. Elle ne peut jamais créer une permission statique absente ni neutraliser un refus absolu.

## Contenu

- `skill.yaml` — découverte, permissions et sécurité;
- `instructions.md` — ordre déterministe d’évaluation;
- `prompts/authorize-action.md` — contrat de décision;
- `resources/decision-rules.md` — invariants;
- `resources/reason-codes.md` — raisons normalisées;
- `schemas/input.schema.json` — contrat d’entrée Draft 7;
- `schemas/output.schema.json` — contrat de sortie Draft 7;
- `tests/*.tests.json` — assertions et cas de décision;
- `tools/Test-IntentAuthorizerSkill.ps1` — validateur PowerShell 5.1 en lecture seule;
- `checksums.sha256` — empreintes du paquet.

## Validation locale

Depuis Windows PowerShell 5.1 :

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force

& ".\skills\policy.intent-authorizer.v1\tools\Test-IntentAuthorizerSkill.ps1"
```

Résultat obligatoire :

```text
ALL_TESTS: PASS
```

La réussite valide uniquement le paquet déclaratif. Elle n’active aucun moteur et n’autorise aucune action réelle.
