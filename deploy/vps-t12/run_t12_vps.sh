#!/usr/bin/env bash
set -euo pipefail

MODE="${MODE:-audit}"
case "$MODE" in audit|canary_start|disable) ;; *) echo "invalid MODE" >&2; exit 2 ;; esac

BROTO_ROOT="$HOME/brotoculateur"
PKG="$BROTO_ROOT/src/brotoculateur"
PAP="$PKG/papillon_engine.py"
T6MOD="$PKG/t6_papillon.py"
T7MOD="$PKG/t7_calculation.py"
T8MOD="$PKG/t8_countertest.py"
T9MOD="$PKG/t9_stability.py"
T10MOD="$PKG/t10_replay.py"
T11MOD="$PKG/t11_budget.py"
T12MOD="$PKG/t12_candidate.py"
ORCH="$PKG/orchestrator.py"
DASH="$PKG/dashboard.py"
STATUS_URL='http://127.0.0.1:8781/api/status'

EXPECT_PAP='87045c18db95871f4cc9521bdfae1c7c4175dcf0a09ef33a8f7e35c5879fa50a'
EXPECT_T6='6c58c96cd46de6f10851e443b5882ffdd2c505c82f907b325cae250e1ffd0792'
EXPECT_T7='5d6ce094a5b9238994182d56b1740555633f4c49983a40e4abceb0a7495303fd'
EXPECT_T8='a93bd6cd9aaaf0fe832604de9e390e6d69de7dfb8b853e558d8c9955761cce9e'
EXPECT_T9='c0e0309dfe6d571c1d786010f72bc6f8bf3ccdada1f5fa960ab6f428e3640dd1'
EXPECT_T10='9fe9b3bbb9a42c790d02e2d85638b2ea11e067750dc1cc5c6812b2c42f40a3be'
EXPECT_T11='559824ead9ed8f824955e10cbe4d3826da4eb4673a43a64125cf46e01985221d'
EXPECT_T12='582566a439ce1fdb9665237a81398f52476e4a85b715ee855d310ed7d407a4f9'
EXPECT_ORCH='cf4978cb315f817abf2283f41630c322a80ccbb94c75662eac8b4a87c7a05d63'
PRE_DASH='9991bbb5513101ea66d22411dfe7da8e1ba79ebc2d1bea668ef07acec3546021'

sha() { sha256sum "$1" | awk '{print $1}'; }

for f in "$PAP" "$T6MOD" "$T7MOD" "$T8MOD" "$T9MOD" "$T10MOD" "$T11MOD" "$ORCH" "$DASH"; do test -f "$f"; done
systemctl --user is-active --quiet brotoculateur.service
curl -fsS --max-time 5 "$STATUS_URL" >/tmp/t12-before.json

test "$(sha "$PAP")" = "$EXPECT_PAP"
test "$(sha "$T6MOD")" = "$EXPECT_T6"
test "$(sha "$T7MOD")" = "$EXPECT_T7"
test "$(sha "$T8MOD")" = "$EXPECT_T8"
test "$(sha "$T9MOD")" = "$EXPECT_T9"
test "$(sha "$T10MOD")" = "$EXPECT_T10"
test "$(sha "$T11MOD")" = "$EXPECT_T11"
test "$(sha "$ORCH")" = "$EXPECT_ORCH"

dash_hash=$(sha "$DASH")
t12_hash='ABSENT'; [ ! -f "$T12MOD" ] || t12_hash=$(sha "$T12MOD")
source_state='UNKNOWN'
if [ "$dash_hash" = "$PRE_DASH" ] && [ "$t12_hash" = 'ABSENT' ]; then
  source_state='PRE_T12'
elif [ "$t12_hash" = "$EXPECT_T12" ]; then
  if python3 - "$DASH" <<'PY'
import sys
text=open(sys.argv[1],encoding='utf-8').read()
markers=[
    'from .t12_candidate import T12CandidateTelemetry',
    'self.t12_candidate = T12CandidateTelemetry()',
    't11_outcome = self.t11_budget.observe(formula_id, source, out, t10_outcome)',
    'self.t12_candidate.observe(formula_id, source, out, t11_outcome)',
    '"t12_candidate": self.t12_candidate.status(),',
]
assert all(text.count(m) >= 1 for m in markers)
assert text.count('from .t12_candidate import T12CandidateTelemetry') == 1
assert text.count('"t12_candidate": self.t12_candidate.status(),') == 1
PY
  then source_state='POST_T12'; fi
fi
test "$source_state" != 'UNKNOWN'
echo "T12_SOURCE_STATE=$source_state"
echo "T12_DASHBOARD_SHA256=$dash_hash"
echo "T12_MODULE_SHA256=$t12_hash"

SOURCE_STATE="$source_state" python3 - <<'PY'
import json, os
d=json.load(open('/tmp/t12-before.json',encoding='utf-8'))
t8=d.get('t8_countertest') or {}; t9=d.get('t9_stability') or {}; t10=d.get('t10_replay') or {}
t11=d.get('t11_budget') or {}; t12=d.get('t12_candidate') or {}; bm=d.get('brutomagique') or {}
for k,v in (
    ('STATE',d.get('state')),('PROCESSED',d.get('processed_packets')),('CRYSTALS',bm.get('total_crystals')),
    ('T8_OBSERVATIONS',t8.get('observations')),('T8_FAIL',t8.get('failed')),('T8_LIMITED',t8.get('limited')),
    ('T9_OBSERVATIONS',t9.get('observations')),('T9_DRIFTS',t9.get('drifts')),
    ('T10_OBSERVATIONS',t10.get('observations')),('T11_OBSERVATIONS',t11.get('observations')),
    ('T11_DEMAND_TOTAL',t11.get('demand_total')),('T11_ADVISED_TOTAL',t11.get('advised_total')),
    ('T11_CLIPPED_TOTAL',t11.get('clipped_total')),('T12_MODE',t12.get('mode')),
    ('T12_ENABLED',t12.get('enabled')),('T12_OBSERVATIONS',t12.get('observations')),
    ('T12_CANDIDATE_RECORDS',t12.get('candidate_records')),('T12_UNIQUE_IDS',t12.get('unique_candidate_ids')),
    ('T12_BLOCKED',t12.get('blocked_t11_other')),
): print(f'{k}={v}')
assert not d.get('worker_error'), d.get('worker_error')
assert t8.get('enabled') is True and t8.get('authority')=='SHADOW_ONLY'
assert int(t8.get('failed') or 0)==0 and int(t8.get('limited') or 0)==0
assert t9.get('enabled') is True and t9.get('authority')=='SHADOW_ONLY' and int(t9.get('drifts') or 0)==0
assert int(t9.get('observations') or 0)==int(t8.get('observations') or 0)
assert t10.get('enabled') is True and t10.get('authority')=='SHADOW_ONLY'
assert int(t10.get('observations') or 0)==int(t9.get('observations') or 0)
assert t11.get('enabled') is True and t11.get('authority')=='SHADOW_ONLY'
assert t11.get('physical_calibration') is False and t11.get('execution_eligible') is False
assert int(t11.get('observations') or 0)==int(t10.get('observations') or 0)
assert int(t11.get('blocked_t10_other') or 0)==0
if os.environ['SOURCE_STATE']=='POST_T12' and t12.get('enabled') is True:
    assert t12.get('authority')=='SHADOW_ONLY'
    assert t12.get('source_of_truth')=='T11_BUDGET_OUTCOME_CALLBACK'
    assert t12.get('candidate_definition')=='TECHNICAL_PRE_SCORE_RECORD'
    assert t12.get('l1_crystal_score_input') is True
    assert t12.get('assigns_score') is False and t12.get('applies_threshold') is False
    assert t12.get('scientific_candidate_claim') is False and t12.get('scientific_proof_claim') is False
    assert t12.get('canonizes') is False and t12.get('promotes_proof') is False
    assert t12.get('validation_state_mutated') is False
    assert t12.get('controls_calculation') is False and t12.get('reserves_resources') is False
    assert t12.get('executes_replay') is False and t12.get('proof_promotion') is False
    assert int(t12.get('observations') or 0)==int(t11.get('observations') or 0)
    assert int(t12.get('blocked_t11_other') or 0)==0
    assert int(t12.get('candidate_records') or 0)==int(t12.get('observations') or 0)
print('T12_AUDIT_ONLY=PASS')
PY
df -P / | awk 'NR==2 {print "ROOT_DISK_USED=" $5 " ROOT_DISK_FREE_KB=" $4}'
[ "$MODE" != audit ] || exit 0

if [ "$MODE" = canary_start ]; then
  test "$source_state" = 'PRE_T12'
  python3 - <<'PY'
import json
d=json.load(open('/tmp/t12-before.json',encoding='utf-8'))
t8=d.get('t8_countertest') or {}; t9=d.get('t9_stability') or {}; t10=d.get('t10_replay') or {}; t11=d.get('t11_budget') or {}
assert d.get('state') in {'RUNNING','PAUSED'} and not d.get('worker_error')
assert t8.get('enabled') is True and int(t8.get('failed') or 0)==0 and int(t8.get('limited') or 0)==0
assert t9.get('enabled') is True and int(t9.get('drifts') or 0)==0
assert t10.get('enabled') is True and t10.get('authority')=='SHADOW_ONLY'
assert t11.get('enabled') is True and t11.get('authority')=='SHADOW_ONLY'
assert t11.get('candidate_advisory_only') is True and t11.get('t12_candidate_input') is True
assert t11.get('physical_calibration') is False and t11.get('execution_eligible') is False
assert int(t11.get('blocked_t10_other') or 0)==0
print('T12_REQUIRES_T8_T9_T10_T11=PASS')
PY
  STAGE="/tmp/brotoculateur-t12-stage-$$"
  rm -rf "$STAGE"; mkdir -p "$STAGE/src"
  cp -a "$PKG" "$STAGE/src/brotoculateur"
  python3 /tmp/patch_brotoculateur_t12_candidate.py "$STAGE"
  test "$(sha "$STAGE/src/brotoculateur/t8_countertest.py")" = "$EXPECT_T8"
  test "$(sha "$STAGE/src/brotoculateur/t9_stability.py")" = "$EXPECT_T9"
  test "$(sha "$STAGE/src/brotoculateur/t10_replay.py")" = "$EXPECT_T10"
  test "$(sha "$STAGE/src/brotoculateur/t11_budget.py")" = "$EXPECT_T11"
  test "$(sha "$STAGE/src/brotoculateur/t12_candidate.py")" = "$EXPECT_T12"
  python3 -m py_compile "$STAGE/src/brotoculateur/dashboard.py" "$STAGE/src/brotoculateur/t12_candidate.py"
  PYTHONPATH="$STAGE/src" BROTO_T8_ENABLED=1 BROTO_T9_ENABLED=1 BROTO_T10_ENABLED=1 BROTO_T11_ENABLED=1 BROTO_T12_ENABLED=1 \
    BROTO_T11_CPU_SLOTS=8 BROTO_T11_MEMORY_SLOTS=8 BROTO_T11_STORAGE_SLOTS=8 BROTO_T11_TIME_SLOTS=8 \
    python3 /tmp/test_t12_candidate.py
  STAGE_DASH_SHA=$(sha "$STAGE/src/brotoculateur/dashboard.py")
  echo "T12_STAGE_DASHBOARD_SHA256=$STAGE_DASH_SHA"
  echo 'T12_EXACT_LIVE_STAGE=PASS'
else
  test "$source_state" = 'POST_T12'
fi

WAS_RUNNING=$(python3 - <<'PY'
import json
print('1' if json.load(open('/tmp/t12-before.json',encoding='utf-8')).get('state')=='RUNNING' else '0')
PY
)
if [ "$WAS_RUNNING" = 1 ]; then
  curl -fsS --max-time 10 -X POST -H 'Content-Type: application/json' -d '{}' http://127.0.0.1:8781/api/save >/tmp/t12-save.json
  curl -fsS --max-time 10 -X POST -H 'Content-Type: application/json' -d '{}' http://127.0.0.1:8781/api/pause >/tmp/t12-pause.json
fi
curl -fsS --max-time 5 "$STATUS_URL" >/tmp/t12-paused.json
python3 - <<'PY'
import json
assert json.load(open('/tmp/t12-paused.json',encoding='utf-8')).get('state')=='PAUSED'
print('T12_PAUSE_VERIFY=PASS')
PY

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
BACKUP="$BROTO_ROOT/backups/t12-$STAMP"
mkdir -p "$BACKUP"
for f in "$DASH" "$T8MOD" "$T9MOD" "$T10MOD" "$T11MOD"; do cp -a "$f" "$BACKUP/"; done
[ ! -f "$T12MOD" ] || cp -a "$T12MOD" "$BACKUP/"
cp -a /tmp/t12-before.json "$BACKUP/status-before.json"
DROPIN_DIR="$HOME/.config/systemd/user/brotoculateur.service.d"; DROPIN="$DROPIN_DIR/99-brutus-t12.conf"; mkdir -p "$DROPIN_DIR"
HAD_DROPIN=0; [ ! -f "$DROPIN" ] || { HAD_DROPIN=1; cp -a "$DROPIN" "$BACKUP/99-brutus-t12.conf"; }
HAD_T12=0; [ ! -f "$T12MOD" ] || HAD_T12=1
echo "T12_BACKUP=$BACKUP"

rollback() {
  rc=$?; set +e; echo "T12_ROLLBACK_BEGIN rc=$rc"
  cp -a "$BACKUP/dashboard.py" "$DASH"; cp -a "$BACKUP/t8_countertest.py" "$T8MOD"; cp -a "$BACKUP/t9_stability.py" "$T9MOD"
  cp -a "$BACKUP/t10_replay.py" "$T10MOD"; cp -a "$BACKUP/t11_budget.py" "$T11MOD"
  if [ "$HAD_T12" = 1 ]; then cp -a "$BACKUP/t12_candidate.py" "$T12MOD"; else rm -f "$T12MOD"; fi
  if [ "$HAD_DROPIN" = 1 ]; then cp -a "$BACKUP/99-brutus-t12.conf" "$DROPIN"; else rm -f "$DROPIN"; fi
  systemctl --user daemon-reload; systemctl --user restart brotoculateur.service; sleep 2
  if [ "$WAS_RUNNING" = 1 ]; then curl -fsS --max-time 10 -X POST -H 'Content-Type: application/json' -d '{}' http://127.0.0.1:8781/api/start >/tmp/t12-rollback-start.json || true; fi
  echo 'T12_ROLLBACK_DONE'; exit "$rc"
}
trap rollback ERR

if [ "$MODE" = canary_start ]; then
  cp -a "$STAGE/src/brotoculateur/dashboard.py" "$DASH"; cp -a "$STAGE/src/brotoculateur/t12_candidate.py" "$T12MOD"
  printf '[Service]\nEnvironment="BROTO_T12_ENABLED=1"\n' > "$DROPIN"
else
  printf '[Service]\nEnvironment="BROTO_T12_ENABLED=0"\n' > "$DROPIN"
fi
systemctl --user daemon-reload; systemctl --user restart brotoculateur.service
ok=0
for _ in $(seq 1 20); do
  if systemctl --user is-active --quiet brotoculateur.service && curl -fsS --max-time 2 "$STATUS_URL" >/tmp/t12-after.json; then ok=1; break; fi
  sleep 1
done
test "$ok" = 1

MODE="$MODE" python3 - <<'PY'
import json, os
d=json.load(open('/tmp/t12-after.json',encoding='utf-8')); t12=d.get('t12_candidate') or {}
assert not d.get('worker_error'), d.get('worker_error')
if os.environ['MODE']=='canary_start':
    assert t12.get('mode')=='BRUTUS_T12_CANDIDATE_V1' and t12.get('enabled') is True and t12.get('authority')=='SHADOW_ONLY'
    assert t12.get('candidate_definition')=='TECHNICAL_PRE_SCORE_RECORD' and t12.get('l1_crystal_score_input') is True
    assert t12.get('assigns_score') is False and t12.get('applies_threshold') is False
    assert t12.get('scientific_candidate_claim') is False and t12.get('proof_promotion') is False
else:
    assert t12.get('enabled') is False
print('T12_DEPLOY_VERIFY=PASS')
PY

if [ "$MODE" = canary_start ] || [ "$WAS_RUNNING" = 1 ]; then
  BASE_T11=$(python3 -c "import json;d=json.load(open('/tmp/t12-after.json'));print(int((d.get('t11_budget') or {}).get('observations') or 0))")
  BASE_T12=$(python3 -c "import json;d=json.load(open('/tmp/t12-after.json'));print(int((d.get('t12_candidate') or {}).get('observations') or 0))")
  curl -fsS --max-time 10 -X POST -H 'Content-Type: application/json' -d '{}' http://127.0.0.1:8781/api/start >/tmp/t12-start.json
  live=0
  for _ in $(seq 1 30); do
    curl -fsS --max-time 2 "$STATUS_URL" >/tmp/t12-live.json || true
    if BASE_T11="$BASE_T11" BASE_T12="$BASE_T12" MODE="$MODE" python3 - <<'PY'
import json, os, sys
try: d=json.load(open('/tmp/t12-live.json',encoding='utf-8'))
except Exception: sys.exit(1)
t8=d.get('t8_countertest') or {}; t9=d.get('t9_stability') or {}; t10=d.get('t10_replay') or {}; t11=d.get('t11_budget') or {}; t12=d.get('t12_candidate') or {}
good=d.get('state')=='RUNNING' and not d.get('worker_error')
if os.environ.get('MODE')=='canary_start':
    dt11=int(t11.get('observations') or 0)-int(os.environ['BASE_T11']); dt12=int(t12.get('observations') or 0)-int(os.environ['BASE_T12'])
    good=good and dt12>0 and dt12==dt11
    good=good and int(t8.get('failed') or 0)==0 and int(t8.get('limited') or 0)==0 and int(t9.get('drifts') or 0)==0
    good=good and int(t10.get('blocked_t8_fail') or 0)==0 and int(t10.get('blocked_t8_limited') or 0)==0 and int(t10.get('blocked_t9_drift') or 0)==0
    good=good and int(t11.get('blocked_t10_other') or 0)==0 and int(t12.get('blocked_t11_other') or 0)==0
    good=good and int(t12.get('candidate_records') or 0)>0 and int(t12.get('candidate_records') or 0)==int(t12.get('observations') or 0)
sys.exit(0 if good else 1)
PY
    then live=1; break; fi
    sleep 1
  done
  test "$live" = 1
  BASE_T11="$BASE_T11" BASE_T12="$BASE_T12" python3 - <<'PY'
import json, os
d=json.load(open('/tmp/t12-live.json',encoding='utf-8')); t11=d.get('t11_budget') or {}; t12=d.get('t12_candidate') or {}
dt11=int(t11.get('observations') or 0)-int(os.environ['BASE_T11']); dt12=int(t12.get('observations') or 0)-int(os.environ['BASE_T12'])
for k,v in (
 ('T12_LIVE_STATE',d.get('state')),('T12_LIVE_PROCESSED',d.get('processed_packets')),('T12_LIVE_T11_OBSERVATIONS',t11.get('observations')),
 ('T12_LIVE_OBSERVATIONS',t12.get('observations')),('T12_LIVE_CANDIDATE_RECORDS',t12.get('candidate_records')),
 ('T12_LIVE_UNIQUE_IDS',t12.get('unique_candidate_ids')),('T12_LIVE_BLOCKED',t12.get('blocked_t11_other')),
 ('T12_LIVE_BUDGET_CLASSES',t12.get('budget_classes')),('T12_LIVE_DELTA_T11',dt11),('T12_LIVE_DELTA_T12',dt12),
): print(f'{k}={v}')
print('T12_LIVE_VERIFY=PASS')
PY
fi

if [ "$MODE" = canary_start ]; then
  test "$(sha "$DASH")" = "$STAGE_DASH_SHA"; test "$(sha "$T12MOD")" = "$EXPECT_T12"
  test "$(sha "$T8MOD")" = "$EXPECT_T8"; test "$(sha "$T9MOD")" = "$EXPECT_T9"; test "$(sha "$T10MOD")" = "$EXPECT_T10"; test "$(sha "$T11MOD")" = "$EXPECT_T11"
  echo "T12_POST_DASHBOARD_SHA256=$STAGE_DASH_SHA"
fi
df -P / | awk 'NR==2 {print "T12_ROOT_DISK_USED=" $5 " T12_ROOT_DISK_FREE_KB=" $4}'
trap - ERR
rm -rf "${STAGE:-}"
echo 'T12_WORKFLOW=PASS'
