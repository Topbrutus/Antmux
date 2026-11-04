# ANTMUX — Admin V0.1 (prototype isolé)

## Objectif

Créer la première interface du tableau d'administration d'Antmux, avec accès public « Brutus » à gauche et bouton « Admin » à droite à intégrer après contrôle d'accès.

La maquette inclut neuf sections navigables et un mode compact local. Tous les contrôles serveur, éditeurs, API, mesures et sauvegardes restent volontairement **inactifs**. Les états sont marqués « À vérifier » : aucune télémétrie n'est simulée.

## Voir la prévisualisation

Ouvrir `index.html` dans un navigateur. Aucun serveur ni compte n'est nécessaire pour la prévisualisation, **qui n'est pas une page d'administration sécurisée**.

## Préconditions de déploiement

1. Configurer un fournisseur d'identité ou une passerelle d'accès avec MFA côté serveur/proxy.
2. Protéger **toutes** les routes `/admin/`, `/admin/*`, les sous-domaines et API d'administration ; vérifier que les non-autorisés obtiennent un refus et jamais un fallback public.
3. Servir le dashboard seulement après contrôle d'authentification et vérifier l'autorisation côté API pour chaque opération. Aucun secret ni jeton dans les fichiers statiques.
4. Intégrer dans la navigation du site, tout à droite : `<a href="/admin/">ADMIN</a>` uniquement après protection vérifiée.
5. Ajouter les APIs réelles en lecture seule, puis les commandes une par une avec prévisualisation, confirmation, audit et rollback.
6. Tester le site public, `/brutus/`, les routes d'administration, les visiteurs non autorisés, la reconnexion et la coupure VPS.

**Ne pas déployer ce prototype sur le site public tel quel.** Une page HTML, même avec un formulaire de connexion en JavaScript, ne protège pas les données.

## Inventaire vérifié au 4 novembre 2026

- Dépôt : `Topbrutus/Antmux` (public), branche `main` au départ : `447cf97c9ebd33d2473130ef484d880f3eafac63`.
- Serveur Antmux : racine web `/var/www/antmux`, `index.html` actuel React embarqué de ~8,2 Mo, nav statique `#antmux-quick-nav` comprenant `BRUTUS`, `LABORATOIRE` et `FORMULES`.
- Nginx : `location /` avec `try_files $uri $uri/ /index.html`; `/admin/` renvoyait 200 avec la page publique lors de la vérification. Pas de protection admin constatée sur ce chemin.
- Aucun fichier de production modifié par la création du prototype.

## Rollback

L'effacement ou l'abandon de la branche de prototype ne change pas le site en production. Une future publication exigera un point de reprise mesuré et le revert de la modification de navigation et des règles de déploiement.