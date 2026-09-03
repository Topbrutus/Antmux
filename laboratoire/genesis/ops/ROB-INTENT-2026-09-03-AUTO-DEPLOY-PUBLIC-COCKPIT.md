# ROB — INTENTION — GENESIS PUBLIC COCKPIT AUTO-DEPLOY

Date: 2026-09-03
Authority: Topbrutus
Executor: Rob
Repository: Topbrutus/Antmux
Start main: 368b5da378ec2c33c8aa374226726698bee97afe
Working branch: genesis/auto-deploy-public-cockpit-20260903

## Problème observé

Le dépôt `Antmux/main` contient le cockpit Genesis LIVE / SNAPSHOT, mais la page servie sur `https://antmux.com/laboratoire/genesis/` est encore l'ancienne version SNAPSHOT-only. Le backend LIVE public est déjà actif; le frontend public n'a simplement pas suivi le dernier `index.html` validé.

## Intention

Rendre le déploiement des fichiers statiques du Genesis Vision Center automatique après une fusion sur `main`, uniquement lorsque les fichiers publics explicitement autorisés changent.

## Frontières

- conserver le déploiement manuel `DEPLOY-GENESIS` comme voie de secours;
- autoriser le déploiement automatique uniquement sur `push` vers `main` et uniquement pour la liste de chemins publics du cockpit;
- ne pas toucher au générateur Antmux;
- ne pas toucher à GESIS;
- ne pas toucher à Seed Genesis;
- ne pas déployer de secrets ni de fichiers privés;
- ne pas supprimer le dossier LIVE existant;
- conserver le snapshot fallback;
- conserver la vérification SSH pinée, les SHA256 et le backup VPS;
- faire échouer le déploiement si les validations publiques échouent.

## Résultat attendu

Après fusion validée, le `index.html` canonique de `Antmux/main` doit être installé sur le VPS automatiquement. Les futures modifications validées du cockpit public suivront de la même manière, tandis que les données scientifiques LIVE continueront d'arriver par le bridge read-only séparé.
