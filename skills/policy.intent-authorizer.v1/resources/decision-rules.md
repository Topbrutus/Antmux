# Invariants de décision

1. **Refus par défaut** — l’absence d’autorisation équivaut à un refus.
2. **Séparation** — intention, action, permissions, risque et approbation restent des objets distincts.
3. **Déterminisme** — les mêmes entrées canoniques produisent la même décision.
4. **Permission statique prioritaire** — aucune approbation ne peut la contourner.
5. **Portée minimale** — une action ne dépasse jamais l’objectif, les outils, les chemins ou les quantités confirmés.
6. **Approbation liée** — elle cite l’empreinte exacte de l’action et de l’intention.
7. **Expiration** — intention, approbation et décision expirées ne valent plus.
8. **Budget Rent** — le coût courant plus le coût estimé doit rester dans les limites.
9. **Zéro secret** — aucun mot de passe, jeton, cookie, secret ou clé API.
10. **Chemins relatifs** — aucun chemin absolu ni segment `..`.
11. **Aucun effet métier** — le skill écrit seulement une décision append-only.
12. **Audit complet** — chaque résultat cite task, run, corrélation et empreintes.
13. **ALLOW strict** — aucune violation et aucune approbation manquante.
14. **Doute humain** — une extension potentiellement acceptable demande une approbation; une interdiction absolue reste refusée.
