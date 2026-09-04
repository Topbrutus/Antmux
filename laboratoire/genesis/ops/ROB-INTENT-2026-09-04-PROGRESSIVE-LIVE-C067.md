# ROB INTENT — Genesis progressive LIVE C067

Date: 2026-09-04
Authority: Topbrutus
Repository: `Topbrutus/Antmux`
Base main: `129395f0bd992e091db02c2d0de6c43af722cf08`
Branch: `genesis/progressive-live-c067-20260904`

## Mission

Préparer le runtime public progressif à recevoir C066 puis C067 avant leur publication, sans toucher au générateur Antmux, au cockpit HTML ni aux dépôts privés.

## Frontière publique

Le runtime doit accepter exactement les projections publiques validées C060→C067 et rester fail-closed pour toute clé ou valeur inattendue.

C066 ajoute uniquement des marqueurs publics non sensibles :
- `genesis003_c066=VALIDATED_10_OF_10`
- `binding_dependency_audit=COMPLETE_NO_NEW_PROVEN_BINDINGS`
- `new_bindings_proven=0`
- `generator_execution_profile_frozen=false`

C067 ajoute uniquement :
- `genesis003_c067=VALIDATED_10_OF_10`
- `control_generator_profile=FROZEN_VALIDATED_CONTROL_ONLY`
- `control_generator_deterministic=true`
- `real_generator_bindings_added=0`
- `real_generator_profile_frozen=false`

La prochaine action C067 publique est `SELECT_REAL_GENERATOR_PROVIDER_MODEL_BUILD`.

## Interdictions

Ne jamais publier :
- SHA, branche, chemin ou nom de dépôt privé Seed Genesis/GESIS ;
- digest scientifique C066/C067 ;
- digest du profil de contrôle ;
- digest du WAV de contrôle ;
- fréquence/amplitude/détails internes de calibration ;
- provider/modèle/build réel non encore sélectionné ;
- prompts A/B/C/D ;
- valeurs de bindings privées ;
- capacité d’écriture publique.

## Déploiement

Ajouter une révision progressive C067 à côté du runtime C065 existant afin de conserver un rollback simple. Après validation PR, le workflow VPS peut basculer sur cette révision. Tant que `public/live-source` reste C065, l’endpoint public doit rester C065.

## Succès attendu

- C060→C067 exacts acceptés ;
- C066/C067 partiels ou mutés rejetés ;
- public LIVE toujours read-only ;
- snapshot fallback préservé ;
- aucune fuite privée ;
- runtime C067-capable déployable avant clôture scientifique C067.
