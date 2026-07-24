# LinuxIA CLI PowerShell v0.1 + Shell LinuxIA Interprète 4B

Première boucle exécutable locale de LinuxIA pour Windows PowerShell 5.1, accompagnée d'un shell visuel Python lancé explicitement par l'utilisateur.

## Inspection contrôlée

```powershell
.\tools\linuxia.ps1 inspect --file ".\docs\architecture\ANTMUX-AGENT-SKILL-V1.md"
```

`inspect` effectue une lecture contrôlée avec autorisation, checkpoints immuables et journaux append-only. Sa portée reste limitée à `docs/**` et `skills/**`. Le chemin d'exécution `inspect` ne dépend pas du modèle conversationnel.

## Shell visuel LinuxIA

Le shell doit être demandé explicitement :

```powershell
.\tools\linuxia.ps1 shell
```

Prérequis :

- Python 3;
- Ollama déjà installé;
- le modèle exact `linuxia-interprete:4b` déjà présent localement.

L'intégration ne lance jamais `ollama pull`, `ollama serve`, `ollama create`, `ollama rm` ou une autre commande de gestion de modèle. Si `linuxia-interprete:4b` n'est pas déjà installé, LinuxIA refuse de le télécharger ou de le créer automatiquement et affiche une erreur honnête.

Le cadre conserve la référence visuelle `prototype-v3-clean` :

- exactement 36 images ANSI championnes, dérivées du paquet 60 × 70;
- surface terminal fixe : journal défilable au-dessus, animation centrée et ancrée;
- tampon de journal borné à 4 000 lignes en mémoire, sans écriture automatique sur disque;
- zone `SORTIE` adaptative avec retour à la ligne et effacement des caractères résiduels;
- aucune ligne `LINUXIA TRAVAILLE` ni points clignotants;
- fourmi immobile pendant l'attente;
- rotation pendant une réponse de LinuxIA Interprète ou une inspection.

## Couche de communication locale

Toutes les phrases ordinaires, y compris `bonjour`, `salut` et `comment ça va`, sont envoyées à `linuxia-interprete:4b`. Les anciennes réponses de salutation préparées ont été retirées.

Exemple attendu :

```text
linuxia> comment ça va?
LinuxIA Interprète> Ça va bien. Je suis là et je t'écoute.
```

La réponse exacte n'est pas inscrite dans le code : elle est générée localement par LinuxIA Interprète au moment de l'échange.

LinuxIA Interprète conserve un rôle volontairement limité :

- parler brièvement avec Gabi;
- garder au maximum six échanges dans la mémoire temporaire de la session;
- reconnaître qu'une demande de travail a été reçue;
- ne jamais prétendre l'avoir transmise, vérifiée ou exécutée;
- ne prendre aucune décision et n'accorder aucune autorisation;
- ne remplacer ni la Reine, ni System Job, ni l'ouvrière, ni le réviseur.

LinuxIA Interprète ne possède aucun accès direct aux fichiers, au réseau, à GitHub, aux outils de LinuxIA ou aux autorisations. La Reine, System Job, les ouvrières temporaires et le réviseur indépendant ne sont pas encore connectés à cette couche.

## Protection de la zone de sortie

Le shell réserve automatiquement une zone compacte sous la fourmi lorsque la fenêtre est basse. Les réponses sont découpées aux frontières de mots, le début du message le plus récent reste visible et chaque ligne physique est effacée avant d'être redessinée. Une saisie longue ne peut donc plus laisser de fragments à droite ou sous le cadre.

Le lancement du modèle résident utilise explicitement `--think=false`. Si la version locale d'Ollama ne fournit pas ce contrôle, LinuxIA refuse l'inférence plutôt que d'afficher le raisonnement interne. Un filtre défensif retire aussi les balises ou préfixes de raisonnement résiduels.

Sous Windows, la saisie se développe maintenant sur plusieurs lignes. Un collage conserve ses retours internes, toutes les lignes disponibles restent visibles et le cadre remonte automatiquement à mesure que le bloc de saisie grandit; seul le dernier retour du collage, ou la touche Entrée pressée séparément, envoie le message.

## Commandes personnalisées

```text
/help
/status
/langage
/langage court
/langage normal
/langage long
/langage auto
/inspect docs/architecture/ANTMUX-AGENT-SKILL-V1.md
/exit
```

Les formes historiques `help`, `status`, `inspect` et `exit` restent acceptées.

Le mode par défaut est `court` : une ou deux phrases, avec une limite demandée de 30 mots afin de rester lisible dans la zone `SORTIE`. Le mode `auto` choisit `court`, `normal` ou `long` selon la demande.

## Limites honnêtes de ce bloc

Cette version fournit une conversation locale minimale. Elle ne fournit pas encore :

- le routage réel du `System Job`;
- l'orchestration de la Reine;
- le chargement d'une ouvrière temporaire;
- la validation par un réviseur indépendant;
- le classificateur silencieux 0.6B;
- une mémoire persistante ou une base de données;
- la narration vocale;
- l'exécution automatique d'options comprises dans une phrase.

Une demande de travail peut être comprise et commentée, mais aucune action n'est lancée sans routage et autorisation explicites.

## Contrat visuel champion

- Le journal de conversation occupe toujours la zone située au-dessus du cadre LinuxIA.
- Jusqu’à 4 000 lignes logiques sont conservées en mémoire pendant la session; les quelques lignes visibles ne sont qu’une fenêtre sur ce tampon.
- Le cadre et l’animation restent ancrés au même endroit pendant la saisie et l’inférence.
- L’image source demeure 60 × 70; les marges communes sont retirées à l’affichage, puis la hauteur est adaptée au terminal sans déplacement vertical entre les frames.
- Les vraies couleurs ANSI du paquet sont conservées; `--no-color` fournit une version texte propre.
- `PgUp`, `PgDn`, `/haut`, `/bas` et `/fin` déplacent uniquement la fenêtre du journal.

## Validation

CLI et intégrité :

```powershell
powershell.exe `
    -NoProfile `
    -ExecutionPolicy Bypass `
    -File ".\tools\linuxia\Test-LinuxIACli.ps1" `
    -CliRoot ".\tools\linuxia"
```

Shell, rendu fixe et LinuxIA Interprète 4B :

```powershell
powershell.exe `
    -NoProfile `
    -ExecutionPolicy Bypass `
    -File ".\tools\linuxia\Test-LinuxIAShell.ps1" `
    -CliRoot ".\tools\linuxia"
```

Le validateur vérifie notamment l'absence de réponses de salutation préparées, le modèle exact, le précontrôle `ollama list`, le contrôle Ollama `--think=false`, l'absence de téléchargement automatique, les 36 images championnes, leur couleur ANSI, le tampon mémoire de 4 000 lignes, le retour à la ligne et l'effacement complet de chaque rangée du rendu fixe.
