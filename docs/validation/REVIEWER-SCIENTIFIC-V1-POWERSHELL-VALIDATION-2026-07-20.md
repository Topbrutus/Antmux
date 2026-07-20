# Validation PowerShell — reviewer.scientific.v1

## Décision

- **Paquet :** `reviewer.scientific.v1`
- **Version :** `1.0.0`
- **Date :** `2026-07-20`
- **Statut accordé :** `VALIDATED_FOR_PROTOTYPE`
- **Activation du modèle :** non autorisée par cette validation
- **Exécution scientifique réelle :** non effectuée

## Environnement vérifié

- **Système :** Windows
- **PowerShell :** `5.1.26100.8875`
- **Mode du validateur :** `READ_ONLY`
- **Source testée :** branche `main`
- **Commit du correctif final testé :** `832aa7401670dd359e5a54521107ee6063d603b1`
- **Méthode :** clone propre du dépôt, puis lancement de `skills/reviewer.scientific.v1/tools/Test-ReviewerScientificSkill.ps1`

## Résultat observé

```text
TOTAL: 73
PASSED: 73
FAILED: 0
ALL_TESTS: PASS
```

## Portée de la preuve

La validation confirme :

- la présence de tous les fichiers obligatoires;
- les assertions du manifeste;
- la lecture des schémas et suites JSON;
- les treize décisions de permissions;
- les quinze contrats positifs et négatifs;
- le refus des outils interdits;
- le refus du réseau;
- le refus des traversées de chemins;
- le refus d'une sortie auto-déclarée `VALIDATED`;
- la cohérence des compteurs de décisions;
- l'intégrité SHA-256 complète du paquet;
- la compatibilité d'exécution avec PowerShell 5.1.

## Incident corrigé durant la validation

Le premier essai a révélé un défaut de compatibilité PowerShell 5.1 dans le cas négatif `CON-007`. Une collection vide produite par `Sort-Object -Unique` ne possédait pas de propriété `.Count` sous `StrictMode`.

Correction appliquée : enveloppement explicite du résultat dans `@(...)`, sans relâcher le contrat. Après correction, les 73 contrôles ont réussi.

## Limites maintenues

Cette preuve ne constitue pas une autorisation pour :

- lancer `local-reviewer`;
- activer Ollama;
- publier automatiquement sur GitHub;
- accéder à Internet;
- supprimer des fichiers;
- modifier les sources analysées;
- déclarer un résultat scientifique comme définitivement validé sans Reviewer indépendant.

Le statut `VALIDATED_FOR_PROTOTYPE` signifie uniquement que le paquet déclaratif et son validateur local sont prêts pour la prochaine phase contrôlée.
