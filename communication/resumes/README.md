# Résumés automatiques Antmux

Ce répertoire reçoit les résumés copiés automatiquement par le hook Codex `Stop`.

## Déclenchement

Le hook lit le champ `last_assistant_message` reçu à la fin d’un tour. Il crée un fichier seulement lorsque la réponse contient un bloc encadré par les marqueurs suivants :

```text
🚦 DÉBUT DU RÉSUMÉ
...
🏁 FIN DU TERMINAL
```

La forme non accentuée est également reconnue :

```text
DEBUT DU RESUME
...
FIN DU TERMINAL
```

## Fichiers produits

Chaque résumé est écrit sous un nom unique :

```text
AAAA-MM-JJ_HH-mm-ss-fff_<session>_<tour>.md
```

Le fichier `LATEST.md` contient toujours une copie du résumé le plus récent.

## Métadonnées

Chaque fichier commence par un en-tête YAML contenant :

- `source`;
- `session_id`;
- `turn_id`;
- `model`;
- `created_at`.

## Emplacements locaux

Avec l’installation Antmux actuelle :

```text
D:\hooks.json
D:\hooks\save-summary.ps1
D:\communication\resumes\
```

## Activation

Après installation :

1. redémarrer Antmux;
2. taper `/hooks`;
3. examiner puis approuver le hook `Stop`;
4. demander un résumé encadré par les marqueurs.

Le hook ne modifie pas la réponse et ne bloque pas Codex si la copie échoue. Les erreurs sont consignées dans :

```text
D:\communication\resumes\hook-errors.log
```
