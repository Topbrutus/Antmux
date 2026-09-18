# T1 — X72 intégré — 2026-09-18

Statut: CHECKPOINT DE VALIDATION POST-INTÉGRATION
Dépôt: `Topbrutus/Antmux`
Source de vérité: `main` vérifié avant branchement
HEAD T1: `6671b4b13b4293a6d79dc9b8544d068ecd5ccc25`

## 1. Chaîne d'intégration vérifiée

- [SOURCE] PR #48 Worker 2 — robustness / checkpoint corruption guard — MERGED.
- [SOURCE] PR #47 Worker 3 — telemetry / observability — MERGED.
- [SOURCE] PR #46 Worker 1 — server-authority visuals / runtime metrics — MERGED.
- [SOURCE] PR #49 Worker 5 — integration CI gate / deploy workflow correction — MERGED.
- [SOURCE] PR #50 — Queen deployment recovery hardening — MERGED.
- [SOURCE] `origin/main` et le clone propre étaient identiques à `6671b4b...` au moment du checkpoint.

## 2. CI intégrée sur le HEAD T1

Run GitHub Actions: `35340301179`
Workflow: `CI X72 Integration Validation`
HEAD: `6671b4b13b4293a6d79dc9b8544d068ecd5ccc25`
Conclusion: **SUCCESS**

Jobs vérifiés:
- Static Validation — SUCCESS
- Server Authority Contract — SUCCESS
- Workflow Audit and Stale Pattern Detection — SUCCESS
- Core Self-Tests and Hash Integrity — SUCCESS
- Integration Smoke Test (Local Queen Server) — SUCCESS
- Integration Readiness Summary — SUCCESS

## 3. Déploiement Queen corrigé

Run de déploiement: `35320855510`
Branche de validation: `hotfix/x72-queen-deploy`
HEAD: `dbbd435dc53f70c1265f16173aac7bc4705b4577`
Conclusion: **SUCCESS**

Étapes critiques vérifiées SUCCESS:
- Build vendor and validate on runner
- Recover existing Queen service before upload
- Upload deployment payload
- Install and test shared Queen server on VPS
- Upload deployment log

[INTERPRÉTATION] Ce commit est le parent fonctionnel de PR #50 maintenant intégré dans `main`.

## 4. Validation locale exacte de main

Clone propre utilisé: `Antmux-t1-validation`
Base: `main @ 6671b4b...`

- Frontend authority contract: **12/12 PASS**
- Runtime metrics contract: **PASS**
- Core self-test: **PASS**
- Robustness suite: **30/30 PASS**
- Shared Queen baseline: **40/40 PASS**
- Python syntax / compile: **PASS**
- JavaScript syntax: **PASS**
- `git diff --check`: **PASS**
- Télémétrie locale:
  - schema = `ANTMUX-X72-OBSERVABILITY-v1`
  - authority = `QUEEN_SERVER_V0_2`
  - scope = `operational_read_only`
  - entity_id = `QUEEN-X72-0072`
  - integrity_match = `true`

Robustness vérifiée notamment:
- 120 lectures concurrentes
- 16 clients WebSocket simultanés
- sérialisation des faults concurrents
- sérialisation des repairs concurrents
- S4 partagé par deux clients
- repair hash close
- restart / persistence
- rejet du checkpoint corrompu + fallback valide
- rate limiting
- absence de surface admin arbitraire

## 5. État public observé

Endpoint public: `/laboratoire/embryon-x72/`

- HTTP / health: **PASS**
- source = `QUEEN_SERVER_V0_2`
- entity_id = `QUEEN-X72-0072`
- integrity_match = `true`
- protected_h256 = reference_h256
- référence observée:
  `49e75d92d8fde33f402c3b60482bc5dcf13c12f09bd8c07c7937961d42ceaff9`
- telemetry schema = `ANTMUX-X72-OBSERVABILITY-v1`
- telemetry authority = `QUEEN_SERVER_V0_2`
- telemetry scope = `operational_read_only`

### Frontend public

SHA256 brut différent entre Git et le fichier HTTP à cause des fins de lignes / encodage.
Après normalisation LF/CRLF + BOM:
- **NORMALIZED_EQUAL = true**
- **DIFF_LINES = 0**

Les invariants sont donc fonctionnellement identiques au frontend de `main`.

### Multi-client public

Deux WebSockets publics simultanés:
- même `entity_id = QUEEN-X72-0072`
- même `reference_h256`
- intégrité vraie sur les deux
- tick observé simultanément: `564067`
- verdict: **PASS**

### Navigateur public réel

Chrome 152, page publique réelle:
- CONNECTED avec integrity = MATCH
- RAF observé: 175 avant coupure client
- fermeture volontaire de la WebSocket de cet onglet uniquement
- état gelé: `CORE DISCONNECTED`
- tick gelé: `565958`
- aucun tick local observé
- reconnexion automatique: **PASS**
- tick après reconnexion: `566023`
- integrity = MATCH après reconnexion
- RAF après reconnexion: 370

Aucune mutation de la Queen publique n'a été réalisée pendant cette validation.
Aucun fault public n'a été injecté.
Aucun restart manuel public n'a été lancé depuis cette session.

## 6. Invariants T1

`Queen Server -> API / WebSocket -> VisualState -> Horloge de la Vie`

Statuts:
- SERVER_AUTHORITY = PASS
- NO_LOCAL_QUEEN = PASS
- VISUAL_INTERPOLATION = PASS
- DISCONNECT_FREEZE = PASS
- RECONNECT = PASS
- MULTI_CLIENT = PASS
- OBSERVABILITY = PASS
- ROBUSTNESS_30_30 = PASS
- BASELINE_40_40 = PASS
- CHECKPOINT_CORRUPTION_GUARD = PASS
- INTEGRATION_CI = PASS
- DEPLOY_RECOVERY = PASS
- PUBLIC_HASH_CLOSE = PASS

## 7. Verdict

**T1_X72_INTEGRATED = PASS**

Ce checkpoint fixe l'état vérifié après intégration des Workers 1, 2, 3, 5
et du hotfix de déploiement PR #50.
