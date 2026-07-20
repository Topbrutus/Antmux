# Instructions — policy.intent-authorizer.v1

## Autorité

L’orchestrateur demeure l’autorité finale d’exécution. Ce skill ne lance aucun outil métier. Il produit uniquement une décision structurée.

## Règles absolues

1. Le modèle ne s’autorise jamais lui-même.
2. Une permission statique absente produit toujours `DENY`.
3. Une approbation ne peut pas créer une permission statique.
4. Tout élément absent de l’enveloppe d’intention est refusé.
5. Une intention expirée produit `DENY`.
6. Une ambiguïté ou une extension de portée produit `REQUIRE_HUMAN_APPROVAL` ou `DENY`, jamais `ALLOW`.
7. Les empreintes SHA-256 sont en hexadécimal minuscule.
8. Aucun secret brut n’est accepté.
9. Une modification de l’action ou de l’intention invalide toute approbation antérieure.
10. Les décisions sont append-only et de courte durée.

## Ordre déterministe

1. Valider le schéma d’entrée.
2. Vérifier les identités de tâche, run et corrélation.
3. Vérifier les empreintes de l’intention, de l’action, des permissions et de la politique.
4. Vérifier l’expiration de l’intention.
5. Appliquer les permissions statiques et les refus absolus.
6. Comparer l’opération et l’outil à l’intention.
7. Comparer les chemins, destinations et modes d’accès.
8. Vérifier réseau, effets externes et caractère destructif.
9. Vérifier les limites quantitatives et le budget Rent.
10. Déterminer les approbations requises.
11. Vérifier que l’approbation vise exactement l’intention et l’action évaluées.
12. Retourner une seule décision et un code de raison principal.

## Priorité des décisions

```text
INPUT_INVALID
→ INTENT_EXPIRED
→ STATIC_PERMISSION_*
→ INTENT_*
→ RENT_OR_ITEM_LIMIT
→ APPROVAL_REQUIRED
→ ALLOW
```

Une approbation valide n’est évaluée qu’après toutes les interdictions statiques et d’intention.

## Sortie

La sortie respecte `schemas/output.schema.json` et cite les empreintes exactes évaluées. Une décision `ALLOW` ne contient aucune contrainte violée ni approbation manquante.
