# PARAZONE-X72-D13 — V2.0

Prototype séparé du laboratoire public Antmux.

## Emplacement

`laboratoire/parazone-x72-d13-v2/`

Le dossier historique `laboratoire/genesis/` reste intact. Il n'est pas supprimé ni modifié par ce module.

## Contrat actuel

- **Statut :** prototype visuel / simulation
- **Canvas logique :** 1200 × 600
- **Deux roues stéréo :** gauche / droite
- **Diamètre visuel par roue :** 560 px
- **Centres :** (300,300) et (900,300)
- **Cadran 60 :** 60 positions, 6° par position
- **Vitesse réelle de référence du cadran 60 :** 6° par minute
- **Contrôle explicite :** ouvrir, fermer, start, pause, stop, reset
- **Délai :** réglable en millisecondes
- **Cristal :** passage simulé d'un cristal lorsque la porte est ouverte

## Frontière

Cette V2.0 n'est pas connectée au Queen Server, au runtime X72 live, à une autre IA ni à un état de production. Les notions de « monde », « porte » et « passage » sont ici des métaphores/interface de simulation tant qu'un contrat technique testable n'est pas implémenté.

## Règle de coexistence

La version existante reste intacte. PARAZONE V2.0 vit dans son propre dossier afin de permettre une future communication bidirectionnelle par contrat/API/bridge sans partager directement l'état interne.
