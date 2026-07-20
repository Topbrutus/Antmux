# LinuxIA CLI PowerShell v0.1

Première boucle exécutable locale de LinuxIA pour Windows PowerShell 5.1.

## Commande disponible

```powershell
.\tools\linuxia.ps1 inspect --file ".\docs\architecture\ANTMUX-AGENT-SKILL-V1.md"
```

`inspect` effectue uniquement une lecture contrôlée :

1. normalisation et validation du chemin relatif;
2. création d'une enveloppe d'intention minimale;
3. création d'une action `READ / source.read`;
4. décision via `policy.intent-authorizer.v1`;
5. lecture du fichier seulement après `ALLOW`;
6. calcul SHA-256 des octets locaux;
7. écriture append-only d'une décision et d'un événement d'audit.

## Portée de lecture

La V0.1 accepte seulement :

- `docs/**`;
- `skills/**`.

Elle refuse les chemins absolus, les segments `..`, les jokers, les points de jonction, `.git`, `state`, `secrets`, `credentials`, ainsi que tout fichier supérieur à 2 MiB.

## Effets autorisés

Le fichier inspecté n'est jamais modifié. Avec l'audit actif, la CLI peut uniquement créer :

- `state/decisions/DECISION-*.json`;
- une nouvelle ligne dans `state/events/linuxia-cli.jsonl`.

Aucun réseau, modèle, processus enfant, installation ou commande GitHub n'est utilisé.

## Sortie JSON

```powershell
.\tools\linuxia.ps1 inspect --file ".\docs\architecture\ANTMUX-AGENT-SKILL-V1.md" --json
```

## Validation

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
& ".\tools\linuxia\Test-LinuxIACli.ps1"
```

La validation du paquet ne valide pas encore le moteur `state.checkpoint.v1` ni une orchestration multi-agent.
