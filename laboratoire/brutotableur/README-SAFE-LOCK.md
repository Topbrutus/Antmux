# Brutotableur — verrou temporaire sûr

Tant que l'inclusion Nginx authentifiée n'a pas été appliquée une fois en root, `/laboratoire/brutotableur/private/` doit servir uniquement `BRUTOTABLEUR_PRIVATE_SAFE_STUB`.

Une fois l'authentification serveur active, Nginx prend priorité sur ce fallback et renvoie `401` aux visiteurs non authentifiés.

Invariant : `PUBLIC_SHOWCASE != INTERACTIVE_ACCESS`.
