# Jules — module de publication des résumés

## But

Ce module prépare le rôle local de **Jules** dans Antmux.

Jules reçoit un fichier de résumé déjà produit, le valide, lui associe un numéro de projet et, si disponible, un numéro de job, puis le publie dans le dépôt GitHub `Topbrutus/Antmux` sous :

```text
communication/resumes/
```

Le déclenchement automatique par dossier ou par hook sera ajouté dans l’étape suivante. Le présent module fournit d’abord une commande manuelle vérifiable.

## Flux

```text
Résumé local
  ↓
Jules.SummaryPublisher
  ↓
Validation du bloc de résumé
  ↓
Classement par PROJECT-xxxxxx
  ↓
Commit Git
  ↓
Push vers GitHub
```

## Portabilité

Les chemins techniques sont relatifs à la racine du disque portant le nom de volume `Antmux`.

Le miroir Git local est placé dans :

```text
<racine-Antmux>\.antmux-git\Antmux
```

Ainsi, le module peut continuer à fonctionner si la lettre du disque change sur une autre machine, à condition que le volume conserve le nom `Antmux` et que Git soit disponible.

## Fichiers

```text
modules/jules/Jules.SummaryPublisher.psm1
modules/jules/Send-AntmuxSummary.ps1
config/jules-summary-publisher.json
INSTALL-JULES-SUMMARY-PUBLISHER.ps1
```

## Sécurité

- aucun jeton GitHub n’est enregistré dans le module;
- aucun mot de passe n’est écrit dans la configuration;
- l’authentification Git existante de Windows est utilisée;
- un verrou empêche deux publications simultanées;
- un résumé identique n’est pas publié deux fois;
- un fichier existant avec un contenu différent n’est jamais écrasé;
- le dépôt miroir doit être propre avant chaque publication.

## Format accepté

Le fichier doit contenir un bloc complet :

```text
DÉBUT DU RÉSUMÉ
...
FIN DU TERMINAL
```

Les marqueurs peuvent contenir ou non les émojis utilisés par Antmux.

## Numéros de projet et de job

Le projet Antmux utilise par défaut :

```text
PROJECT-000000
```

Le module cherche le numéro de job dans cet ordre :

1. paramètre `-JobId`;
2. champ `job_id:` dans le front matter;
3. nom du fichier contenant `JOB-xxxxxx`.

Lorsqu’un numéro de job est présent, le fichier publié se nomme :

```text
JOB-000014-RESUME.md
```

et est rangé sous :

```text
communication/resumes/PROJECT-000000/JOB-000014-RESUME.md
```

Si aucune job n’est encore attribuée, Jules publie sous un nom temporaire `UNASSIGNED-...md` sans inventer un numéro permanent.

## Installation locale

Télécharger puis exécuter :

```powershell
Invoke-WebRequest -UseBasicParsing `
  "https://raw.githubusercontent.com/Topbrutus/Antmux/main/INSTALL-JULES-SUMMARY-PUBLISHER.ps1" `
  -OutFile "D:\INSTALL-JULES-SUMMARY-PUBLISHER.ps1"

Set-ExecutionPolicy -Scope Process Bypass -Force
& "D:\INSTALL-JULES-SUMMARY-PUBLISHER.ps1"
```

## Test sans publication

```powershell
& "D:\modules\jules\Send-AntmuxSummary.ps1" `
  -SummaryPath "D:\communication\resumes\LATEST.md" `
  -ProjectId "PROJECT-000000" `
  -DryRun
```

Le résultat doit afficher `Status : dry-run` et le chemin Git prévu.

## Première publication réelle

Avec une job connue :

```powershell
& "D:\modules\jules\Send-AntmuxSummary.ps1" `
  -SummaryPath "D:\communication\resumes\LATEST.md" `
  -ProjectId "PROJECT-000000" `
  -JobId "JOB-000001"
```

Sans job attribuée :

```powershell
& "D:\modules\jules\Send-AntmuxSummary.ps1" `
  -SummaryPath "D:\communication\resumes\LATEST.md" `
  -ProjectId "PROJECT-000000"
```

Au premier `push`, Git peut demander l’authentification GitHub. Cette authentification appartient à Git/Windows et n’est pas stockée par Jules.

## Résultat attendu

```text
Status    : published
ProjectId : PROJECT-000000
JobId     : JOB-000001
GitPath   : communication/resumes/PROJECT-000000/JOB-000001-RESUME.md
Commit    : <sha>
```

## Étape suivante

Brancher l’apparition d’un nouveau fichier dans `communication/resumes/` sur la commande `Send-AntmuxSummary.ps1`.

Cette future action devra transmettre le chemin du nouveau résumé au module. Le module reste l’unique composant responsable de la validation et du push GitHub.
