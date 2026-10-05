# BRUTOTABLEUR — vitrine publique

Route publique visée :

`https://antmux.com/laboratoire/brutotableur/`

## Frontière

- la page publique est une vitrine figée et non interactive;
- elle publie une capture de la version Brutotableur indiquée dans `PUBLIC-PROVENANCE.json`;
- aucun mot de passe, hash de mot de passe, token ou secret n'est stocké ici;
- le bouton **DÉBARRER LA VITRINE** cible `/laboratoire/brutotableur/private/`;
- la route privée doit être protégée par Nginx avant toute publication de l'application interactive.

## Invariant

`PUBLIC_SHOWCASE != PRIVATE_INTERACTIVE_APP`

`SOFTWARE_VERSION_EVIDENCE != MATHEMATICAL_PROOF`
