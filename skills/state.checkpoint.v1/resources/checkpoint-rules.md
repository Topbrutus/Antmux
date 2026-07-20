# Invariants de checkpoint

1. **Immutabilité** — un snapshot commis n'est jamais modifié.
2. **Parent explicite** — chaque checkpoint non racine cite son parent immédiat.
3. **Branchement** — une restauration crée une nouvelle branche.
4. **Idempotence** — une même clé retourne le même résultat logique.
5. **Canonicalisation** — UTF-8 sans BOM, LF, clés triées, UTC, chemins `/`, Unicode NFC.
6. **Intégrité** — toutes les empreintes sont `sha256:` suivies de 64 hexadécimaux minuscules.
7. **État explicite** — aucune décision critique ne reste uniquement dans le contexte du modèle.
8. **Audit append-only** — JSONL est une projection rejouable de l'outbox SQLite.
9. **Autorité externe** — l'orchestrateur autorise les transitions; le skill les conserve.
10. **Zéro secret** — aucun jeton, cookie, mot de passe ou clé API dans les snapshots.
11. **Chemins relatifs** — aucun chemin absolu et aucune traversée `..`.
12. **Aucun effet externe** — le paquet déclaratif ne lance aucun processus, réseau ou moteur.
