# Codes de refus

- `INPUT_INVALID` — l'objet ne respecte pas le contrat général.
- `IDENTITY_INVALID` — identifiants d'exécution absents ou mal formés.
- `OPERATION_NOT_ALLOWED` — opération inconnue ou non autorisée.
- `TOOL_NOT_ALLOWED` — outil absent de la liste blanche.
- `PATH_NOT_ALLOWED` — chemin hors des préfixes autorisés.
- `PATH_TRAVERSAL` — segment `..` détecté.
- `NETWORK_NOT_ALLOWED` — accès réseau demandé.
- `SECRET_FIELD_FORBIDDEN` — propriété sensible détectée.
- `SHA256_INVALID` — empreinte absente ou non canonique.
- `PARENT_REQUIRED` — parent attendu absent.
- `ROOT_PARENT_MUST_BE_NULL` — checkpoint racine avec parent.
- `SEQUENCE_INVALID` — séquence non positive ou incohérente.
- `DUPLICATE_ARTIFACT_ID` — identifiant d'artefact répété.
- `BRANCH_CONFLICT` — nouvelle branche identique à la branche source.
- `APPROVAL_REQUIRED` — activation sensible sans approbation.
- `OUTPUT_INVALID` — résultat non conforme.
- `CHECKSUM_MISMATCH` — intégrité du paquet invalide.
