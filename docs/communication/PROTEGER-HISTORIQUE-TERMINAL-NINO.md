# Mode d’emploi — Protéger l’historique du terminal Nino

## Objectif

Dans Nino, toute la job exécutée dans le terminal doit survivre à `CLS`, à la fermeture de la fenêtre, à un redémarrage de Nino et à un redémarrage de Windows.

`CLS` doit seulement nettoyer l’affichage courant. Il ne doit jamais supprimer l’historique réel.

## Règles obligatoires

1. Créer un transcript append-only sur `D:\` pour chaque session du terminal Nino.
2. Enregistrer chaque commande, sortie, erreur, horodatage, répertoire courant, branche Git et identifiant de job.
3. Ne jamais tronquer ni réécrire le transcript existant.
4. `CLS` efface uniquement le tampon visuel du terminal.
5. Après `CLS`, afficher un message clair : `Affichage nettoyé — historique conservé sur D:\...`.
6. À la réouverture du terminal, proposer ou effectuer la restauration de la session précédente.
7. Après fermeture anormale, reprendre depuis le dernier checkpoint valide.
8. Ajouter une commande séparée pour consulter l’historique complet sans le modifier.
9. Toute suppression réelle d’un transcript exige une confirmation explicite de Brutus et une sauvegarde préalable.
10. Aucun fichier d’historique, cache ou checkpoint ne doit être créé sur `C:\`.

## Structure recommandée

```text
D:\runtime\nino-terminal\
  sessions\
    <SESSION-ID>\
      transcript.jsonl
      transcript.txt
      state.json
      checkpoints\
  index.jsonl
  logs\
```

## Comportement de CLS

Avant l’exécution de `CLS` :

1. vider et synchroniser les écritures en attente;
2. enregistrer un événement `DISPLAY_CLEAR_REQUESTED`;
3. créer un checkpoint;
4. nettoyer uniquement l’affichage;
5. enregistrer `DISPLAY_CLEARED`;
6. conserver le transcript intact.

`CLS` ne doit appeler aucune fonction de suppression, de troncature ou de réinitialisation du fichier de transcript.

## Rôle d’Hermès et d’Obsidian

- Le transcript brut reste dans l’espace runtime de Nino sur `D:\`.
- Hermès ne modifie jamais ce transcript brut.
- Hermès lit les événements validés et produit un résumé structuré.
- Hermès écrit dans Obsidian les faits durables, décisions, erreurs, solutions, commits, tests et le prochain point de reprise.
- Obsidian ne remplace pas le journal brut; il sert de bibliothèque et d’index durable.
- Aucun secret, clé, jeton, cookie ou mot de passe ne doit être copié dans Obsidian.

## Tests obligatoires

- [ ] Exécuter plusieurs commandes, puis `CLS`; le transcript reste complet.
- [ ] Fermer et rouvrir Nino; la session peut être restaurée.
- [ ] Forcer une fermeture anormale; le dernier checkpoint est récupéré.
- [ ] Redémarrer Windows; l’historique reste disponible.
- [ ] Vérifier que `CLS` n’a modifié ni la taille ni le hash des anciennes lignes du transcript.
- [ ] Vérifier que les nouvelles entrées sont ajoutées uniquement à la fin.
- [ ] Vérifier qu’aucun chemin actif `C:\` n’est utilisé.
- [ ] Vérifier qu’Hermès produit un résumé sans modifier le brut.
- [ ] Vérifier qu’Obsidian reçoit uniquement la mémoire validée.

## Prompt exact à introduire dans le terminal

```text
Configure le terminal Nino pour que toute la job soit persistante et récupérable.

RÈGLE PRINCIPALE
CLS doit seulement nettoyer l’affichage. Il ne doit jamais effacer, tronquer ou réinitialiser l’historique réel.

EXIGENCES
- Créer un transcript append-only par session sous D:\runtime\nino-terminal\sessions\.
- Enregistrer commandes, sorties, erreurs, timestamps, répertoire courant, branche Git et job_id.
- Synchroniser les écritures et créer un checkpoint avant chaque CLS.
- Après CLS, afficher : « Affichage nettoyé — historique conservé ».
- Restaurer la session après fermeture, panne ou redémarrage.
- Ajouter une commande de consultation de l’historique complet en lecture seule.
- Toute suppression réelle exige confirmation explicite de Brutus et sauvegarde préalable.
- Aucun chemin nouveau sur C:\.

HERMÈS ET OBSIDIAN
- Le transcript brut reste dans Nino sur D:\.
- Hermès est le seul agent qui transforme le brut validé en mémoire durable.
- Hermès écrit dans le coffre Obsidian réel sans inventer de chemin.
- Obsidian conserve les résumés, décisions, erreurs, solutions, commits, tests et la reprise exacte.
- Aucun secret dans les transcripts publiés, les résumés ou Obsidian.

VALIDATION
Démontrer avec des tests réels que :
1. CLS ne détruit rien;
2. une fermeture et un redémarrage restaurent l’historique;
3. une fermeture anormale reprend au dernier checkpoint;
4. les fichiers sont append-only;
5. Hermès résume sans modifier le brut;
6. aucun nouveau chemin C:\ n’est utilisé.

Ne pousse ni ne fusionne sans autorisation de Brutus.
Rapporte les fichiers modifiés, les chemins créés, les tests, les blocages, le commit local et la prochaine action unique.
```
