# Third Eye — Antmux Web

## 2026-08-15 — Intention — Rob

**Dépôt :** `Topbrutus/Antmux`  
**Branche :** `main`

### État vérifié

- Le noyau Antmux existe sur `main` avec `README.md`, `antmux_formula.py` et le Third Eye principal.
- Aucun `index.html`, `app.js` ou `styles.css` n’existe encore à la racine.
- Le dépôt historique du site n’est pas visible dans les dépôts GitHub connectés.
- Le domaine public `antmux.com` n’a pas pu être inspecté de manière fiable depuis les outils publics au moment de cette intervention.

### Intention

Construire une première interface web statique, sans backend et sans dépendance externe, qui :

1. génère une Fourmi déterministe à partir des invariants canoniques Antmux ;
2. calcule sa phase `3 × 7 × 13 -> 273` ;
3. contient les sept fonctions internes Fourmi, Abeille, Scarabée, Papillon, Mante, Libellule et Termite ;
4. produit un emblème SVG calculé avec sept pôles, sept branches et treize orientations ;
5. calcule une empreinte SHA-256 de l’incarnation ;
6. permet une réincarnation de la même graine et vérifie que l’empreinte reste identique ;
7. exporte l’état de la Fourmi en JSON ;
8. conserve la traversée du tableau périodique comme monde paramétrique ;
9. ne prétend pas démontrer une conscience ou une propriété physique nouvelle.

### Limite de déploiement

Les fichiers seront prêts à être servis directement comme site statique. Le branchement final de `antmux.com` dépend du fournisseur d’hébergement/DNS actuel, qui doit être identifié avant toute modification de domaine.

**Signé : Rob**
