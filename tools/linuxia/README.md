# LinuxIA CLI PowerShell v0.1

Première boucle exécutable locale de LinuxIA pour Windows PowerShell 5.1.

## Commande disponible

```powershell
.\tools\linuxia.ps1 inspect --file ".\docs\architecture\ANTMUX-AGENT-SKILL-V1.md"
```

`inspect` effectue une lecture contrôlée avec checkpoints :

1. normalisation et validation du chemin relatif;
2. création d'une enveloppe d'intention minimale;
3. création d'une action `READ / source.read`;
4. décision via `policy.intent-authorizer.v1`;
5. checkpoint immuable `PRE_ACTION` après `ALLOW`;
6. lecture du fichier;
7. calcul SHA-256 des octets locaux;
8. checkpoint enfant immuable `POST_ACTION`;
9. écriture append-only des événements d'audit.

Le checkpoint `POST_ACTION` référence obligatoirement le checkpoint `PRE_ACTION`. Les deux objets passent les contrats d'entrée et de sortie de `state.checkpoint.v1`.

## Portée de lecture

La V0.1 accepte seulement :

- `docs/**`;
- `skills/**`.

Elle refuse les chemins absolus, les segments `..`, les jokers, les points de jonction, `.git`, `state`, `secrets`, `credentials`, ainsi que tout fichier supérieur à 2 MiB.

## Effets autorisés

Le fichier inspecté n'est jamais modifié. Avec l'audit actif, la CLI peut uniquement créer :

- `state/decisions/DECISION-*.json`;
- `state/checkpoints/RUN-*/CHK-*.json`;
- une nouvelle ligne dans `state/events/checkpoints.jsonl`;
- une nouvelle ligne dans `state/events/linuxia-cli.jsonl`.

Les artefacts de décision et de checkpoint utilisent une création immuable. Les journaux sont append-only.

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

La validation couvre l'adaptateur de checkpoints JSON/JSONL de la CLI. Elle ne valide pas encore un backend SQLite, les opérations `FORK`, `RESTORE_PLAN`, `ACTIVATE_BRANCH` ni une orchestration multi-agent.
