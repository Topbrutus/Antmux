# Antmux — règle de résumé automatique

Lorsqu’un utilisateur demande un résumé, une sauvegarde de session, une fermeture de session ou un rapport final, terminer la réponse avec exactement un bloc de cette forme :

```text
🚦 DÉBUT DU RÉSUMÉ

Objectif :

Travail effectué :

Fichiers créés ou modifiés :

Vérifications :

Blocages ou risques :

Niveau de confiance :

Prochaine action unique :

🏁 FIN DU TERMINAL
```

Règles :

- conserver les deux marqueurs;
- ne pas placer un second résumé dans la même réponse;
- indiquer explicitement lorsqu’aucun fichier n’a été modifié;
- indiquer un niveau de confiance;
- terminer par une seule prochaine action;
- ne jamais prétendre qu’une action a réussi sans vérification.

Le hook `D:\hooks\save-summary.ps1` copie automatiquement ce bloc dans `D:\communication\resumes\`.
