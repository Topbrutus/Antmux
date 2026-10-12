# Brotoculateur — vitrine publique Antmux

Cette vitrine publie la capture de l'interface Brotoculateur/BrutoCalculateur en grand format et ajoute uniquement une télémétrie live sanitisée (état, paquets, cristaux L1→Ln) depuis /brutus/public-state.json.

- URL canonique : `/laboratoire/brotoculateur/`
- Alias public : `/laboratoire/brutocalculateur/`
- Interaction publique : **désactivée**
- Télémétrie live : **lecture seule, sanitisée** via Brutus public-state
- Backend privé : **non publié**
- Accès propriétaire : renvoi vers un stub sûr; l'application live reste côté propriétaire/Nino.
- Source épinglée : `Topbrutus/Brotoculateur` — commit `d15088f16b04e02b3291847bd7db4983c21df2f4`
- Vérification locale avant capture : **24/24 tests PASS**, UI HTTP **200**.
- Capture SHA-256 : `2e24e952a2d8ebc8035b7f2a025a316f5630e898df737c80f81c3973222131b1`

La vitrine ne doit contenir ni secret, ni mot de passe, ni token, ni backend interactif.
