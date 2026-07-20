# Instructions — state.checkpoint.v1

## Autorité

L'orchestrateur demeure l'autorité des transitions de tâche. Ce skill conserve un état autorisé; il ne décide jamais seul qu'une tâche est `AUTHORIZED`, `VALIDATED`, `REJECTED` ou `ROLLED_BACK`.

## Procédure commune

1. Valider l'enveloppe d'identité et le schéma d'entrée.
2. Refuser tout secret, chemin absolu, traversée de chemin ou outil absent de la liste blanche.
3. Vérifier la clé d'idempotence.
4. Vérifier les préconditions propres à l'opération.
5. Produire uniquement un résultat conforme au schéma.
6. Ne jamais réécrire ni supprimer un checkpoint existant.
7. Journaliser le refus ou le résultat avec le `correlation_id`.

## CREATE

- `sequence = 1` exige un parent nul.
- `sequence > 1` exige un `expected_parent_checkpoint_id`.
- les artefacts ont des chemins relatifs et des SHA-256 minuscules;
- les identifiants d'artefact sont uniques;
- le payload ne contient aucun secret.

## VERIFY

- exige un `checkpoint_id`;
- vérifie le snapshot, le parent, les artefacts et la cohérence d'audit;
- ne modifie aucune donnée.

## FORK

- exige un checkpoint source;
- la nouvelle branche diffère de la branche source;
- la branche d'origine reste intacte.

## RESTORE_PLAN

- produit un plan seulement;
- ne déplace aucun pointeur;
- n'exécute aucun effet externe.

## ACTIVATE_BRANCH

- exige une référence d'approbation si l'état courant est `RUNNING`, `UNDER_REVIEW`, `VALIDATED`, `REJECTED`, `FAILED` ou `ROLLED_BACK`;
- ne modifie que le pointeur actif autorisé;
- ne modifie aucun snapshot historique.

## REBUILD_AUDIT_PROJECTION

- rejoue l'outbox SQLite vers JSONL;
- déduplique par identifiant d'événement;
- ne modifie aucun checkpoint.
