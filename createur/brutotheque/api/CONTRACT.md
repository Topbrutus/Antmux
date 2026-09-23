# Contrat API privée — Brutothèque V0.1

CANDIDAT — à implémenter côté serveur avant activation des données privées.

- POST /createur/api/login : vérification d’un hash de mot de passe stocké hors Git; session HttpOnly + Secure + SameSite=Strict.
- POST /createur/api/logout : invalidation de session.
- GET /createur/api/session : état authentifié minimal.
- GET /createur/api/items : inventaire privé.
- POST /createur/api/items : création avec ID canonique.
- PATCH /createur/api/items/{id} : modification avec journal append-only.
- POST /createur/api/import/chiffres : import explicite avec manifeste de provenance.

Refus par défaut : aucune donnée privée sans session valide.
