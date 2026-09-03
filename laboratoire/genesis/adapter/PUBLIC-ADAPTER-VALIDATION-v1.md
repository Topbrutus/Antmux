# GENESIS PUBLIC ADAPTER — VALIDATION v1

## Statut

`VALIDATE_PUBLIC_ADAPTER`

Cette phase valide la **frontière de publication** avant tout snapshot réel. Elle ne connecte pas le dépôt privé Genesis.

## Architecture

`PRIVATE-LIKE INPUT (synthetic test only)`
→ `EXPLICIT PUBLICATION CANDIDATE`
→ `GENESIS PUBLIC ADAPTER`
→ `PUBLIC CONTRACT v2 VALIDATOR`
→ `PUBLIC ENVELOPE`

## Règles

1. `DENY BY DEFAULT`.
2. Seul `public_payload` est une zone de publication candidate.
3. Les champs privés ou inconnus hors de cette zone ne sont jamais copiés.
4. Un champ inconnu **dans** `public_payload` fait échouer l'Adapter.
5. L'Adapter n'a aucune fonction réseau, SSH, GitHub, filesystem privé ou écriture vers Genesis.
6. Dans cette phase, l'Adapter accepte uniquement `mode=DEMO` et `source_status=SYNTHETIC`.
7. La sortie doit passer `validatePublicV2` avant d'être considérée publiable.
8. Les motifs sensibles dans un champ public autorisé doivent être rejetés par le validateur public.
9. `MEASURED != DERIVED != INTERPRETED != HYPOTHESIS != UNKNOWN` reste obligatoire.
10. `SNAPSHOT` et `LIVE_READ_ONLY` restent interdits dans cette phase.

## Preuves attendues

- la fixture privée-like contient volontairement de faux marqueurs privés hors `public_payload`;
- aucun de ces marqueurs ne doit apparaître dans la sortie;
- les catégories/champs inconnus dans `public_payload` sont rejetés;
- les chemins privés, tokens factices et endpoints privés placés dans un champ public autorisé sont rejetés;
- la sortie canonique synthétique passe `PUBLIC-CONTRACT-v2`;
- aucune hypothèse gagnante n'est inventée;
- aucune promotion vers un Evidence Ledger privé n'est effectuée.

## Hors périmètre

- lecture de `Topbrutus/seedgenesis`;
- connexion à un filesystem privé;
- publication d'un snapshot réel;
- activation de `LIVE_READ_ONLY`;
- écriture depuis le navigateur vers Genesis;
- modification de `/generator/`.
