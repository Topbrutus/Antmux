# Contrat API — Brutothèque V0.2

## Principe
PUBLIC READ / OWNER WRITE / ADMIN APPROVE.

Le serveur vérifie identité, rôle et propriétaire à chaque écriture.

## Rôles
VISITOR : lecture publiée et messagerie autorisée. CREATOR : écriture dans son propre laboratoire. ADMIN : approbation/refus/blocage et administration de plateforme.

## Comptes et demandes
- POST /createur/api/registrations : demande PENDING.
- GET /createur/api/admin/registrations : ADMIN.
- POST /createur/api/admin/registrations/{id}/approve : ADMIN.
- POST /createur/api/admin/registrations/{id}/reject : ADMIN.
- POST /createur/api/admin/registrations/{id}/block : ADMIN.
- POST /createur/api/login : hash hors Git; session HttpOnly + Secure + SameSite=Strict.
- POST /createur/api/logout : invalide la session.
- GET /createur/api/session : identité et rôle minimaux.

## Laboratoires
- GET /createur/api/creators : créateurs publics approuvés.
- GET /createur/api/labs/{owner}/items : objets publiés.
- POST /createur/api/labs/{owner}/items : propriétaire uniquement.
- PATCH /createur/api/labs/{owner}/items/{id} : propriétaire uniquement.

## Interphone texte
- POST /createur/api/labs/{owner}/messages : texte brut seulement, taille bornée, rate-limit, anti-spam.
- GET /createur/api/labs/{owner}/messages : propriétaire uniquement.
- POST /createur/api/labs/{owner}/blocks/{sender_id} : propriétaire uniquement.
- DELETE /createur/api/labs/{owner}/blocks/{sender_id} : propriétaire uniquement.

## Visibilité
PUBLIC, VITRINE ou PRIVATE. PRIVATE n'est jamais sérialisé dans une réponse publique.

## Invariants sécurité
- mots de passe jamais dans Git, HTML, JS ou logs;
- refus par défaut pour toute écriture sans session valide;
- contrôle owner côté serveur à chaque mutation;
- messages rendus comme texte, jamais comme HTML;
- journal d'audit pour approbations, écritures et blocages;
- aucune donnée privée publiée par GitHub Pages.
