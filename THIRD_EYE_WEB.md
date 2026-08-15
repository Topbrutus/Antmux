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

---

## 2026-08-15 — Résultat — Rob

### Fichiers créés

- `index.html`
- `styles.css`
- `app.js`

### Commits

- Third Eye web / intention : `6eb10d70d9a6cbe563029644ea47b605ee22780f`
- Interface HTML : `5b79aba2dc17045888ca5a8aa3913d254bbfdb2f`
- Styles : `296d1b508578d0986c798b6f2d894214b7d44a43`
- Générateur : `4c71f6a0cb22c0ed29be65153a46bfeb692219ad`

### Vérifications

- `app.js` passe une vérification syntaxique JavaScript locale avec `node --check`.
- `index.html` a été relu depuis GitHub sur `main`.
- Le site ne dépend d’aucune bibliothèque externe.
- La Fourmi est calculée dans le navigateur à partir du canon Antmux.
- La génération produit un numéro d’incarnation, une phase, un pôle, une orientation, sept poids fonctionnels et un emblème SVG.
- L’empreinte est calculée en SHA-256 via Web Crypto.
- La commande `Réincarner` reconstruit la même génération et compare son empreinte.
- L’état peut être exporté en JSON.
- Le monde paramétrique accepte un numéro atomique de 1 à 118.

### Statut

**OK — première Fourmi web statique construite et versionnée.**

### Blocage restant

Le code est prêt à être servi, mais `antmux.com` n’est pas encore relié à ce nouveau dépôt depuis cette session. Il faut identifier le fournisseur qui sert actuellement le domaine ou choisir un nouveau déploiement, puis relier le domaine sans modifier les invariants du moteur.

### Reprise

1. Identifier l’hébergement actuel de `antmux.com` depuis le tableau de bord du registrar/hébergeur ou depuis le dépôt local historique.
2. Déployer `index.html`, `styles.css` et `app.js` depuis `Topbrutus/Antmux`.
3. Vérifier publiquement la génération et la réincarnation de `ANT-000001`.
4. Seulement après cette preuve, ajouter une persistance serveur et un véritable registre de Fourmis.

**Signé : Rob**
