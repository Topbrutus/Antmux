# ROB INTENT — VALIDATE_PUBLIC_ADAPTER — 2026-09-03

## Base

- repository: `Topbrutus/Antmux`
- base branch: `main`
- base HEAD: `0bb4b3d392ac53b6bd6150db4662848b772c0f2b`
- work branch: `genesis/validate-public-adapter`

## Mission

Valider le **Genesis Public Adapter** comme frontière de publication avant tout SNAPSHOT réel ou LIVE_READ_ONLY.

## Limites obligatoires

- ne pas connecter le navigateur public au dépôt privé `Topbrutus/seedgenesis`;
- ne lire ni secrets, seeds privées, audits privés, credentials, topologie réseau privée ou sorties oracle;
- ne pas activer `SNAPSHOT` réel;
- ne pas activer `LIVE_READ_ONLY`;
- ne pas modifier `/generator/`;
- conserver `DENY BY DEFAULT -> EXPLICIT WHITELIST -> PUBLIC`;
- conserver `MEASURED != DERIVED != INTERPRETED != HYPOTHESIS != UNKNOWN`;
- une sortie de l'Adapter doit être validée par `PUBLIC-CONTRACT-v2` avant publication.

## Validation visée

Construire un harness public et synthétique qui prouve que l'Adapter :

1. accepte une entrée privée-like synthétique sans publier implicitement ses champs;
2. construit une enveloppe v2 uniquement à partir d'une whitelist explicite;
3. rejette/retire les champs interdits et les marqueurs de secrets/chemins privés;
4. refuse les catégories et champs inconnus;
5. ne crée aucune capacité d'écriture vers Genesis;
6. produit un snapshot de test qui passe le validateur public v2;
7. résiste à des tests adversariaux de fuite et de contamination sémantique.

## Critère de fermeture

`VALIDATE_PUBLIC_ADAPTER = COMPLETE_VALIDATED_ON_BRANCH` seulement si le harness, les tests adversariaux et la CI sont verts. La gate `adapter` ne sera promue à `PASSED` dans le snapshot canonique qu'après cette validation; `snapshot` et `live-read-only` restent `PENDING`.
