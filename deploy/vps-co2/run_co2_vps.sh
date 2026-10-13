#!/usr/bin/env bash
set -euo pipefail

ROOT="$HOME/brotoculateur"
PKG="$ROOT/src/brotoculateur"
DASH="$PKG/dashboard.py"
CO1="$PKG/co1_archive.py"
CO2="$PKG/co2_proof_chain.py"
S5="$PKG/s5_fast_index.py"
C3="$PKG/c3_library.py"
ARCHIVE="$ROOT/data/co1/archive-v1.jsonl"
CHAIN="$ROOT/data/co2/proof-chain-v1.jsonl"
URL="http://127.0.0.1:8781/api/status"

PRE_DASH="210abbe5d72fd4dcc4b154cb3d13a8d954567ac29ef5435381fe2f16fbce109b"
CO1_SHA="032ba9e665349b7d426e32c19d3c532467a0245e35a27da2cd66e2d1209864d2"
S5_SHA="de885d1f4748d236a0050cbea87560cf26fc74a08a95a8a02b119241ce6b0334"
C3_SHA="b7970583e688488d0f9fd8a90838d9163d00b08b7e6afedd499434e79a06c434"

MODE="${MODE:-audit}"
CO2SHA="${CO2SHA:?CO2SHA required}"
EXPECTED_POST="${EXPECTED_POST:-}"

sha() { sha256sum "$1" | awk '{print $1}'; }
wait_api() {
  for _ in $(seq 1 30); do
    curl -fsS "$URL" >/dev/null 2>&1 && return 0
    sleep 1
  done
  return 1
}
api_post() {
  curl -fsS -X POST -H 'Content-Type: application/json' -d '{}' "$1" >/dev/null
}

case "$MODE" in audit|canary_start) ;; *) echo "invalid MODE=$MODE" >&2; exit 2;; esac

test "$(sha "$CO1")" = "$CO1_SHA"
test "$(sha "$S5")" = "$S5_SHA"
test "$(sha "$C3")" = "$C3_SHA"
systemctl --user is-active --quiet brotoculateur.service
wait_api
curl -fsS "$URL" > /tmp/co2-before.json

dh="$(sha "$DASH")"
co2hash="ABSENT"
[ ! -f "$CO2" ] || co2hash="$(sha "$CO2")"

if [ "$dh" = "$PRE_DASH" ] && [ "$co2hash" = "ABSENT" ]; then
  SOURCE_STATE="PRE_CO2"
else
  test -n "$EXPECTED_POST"
  test "$dh" = "$EXPECTED_POST"
  test "$co2hash" = "$CO2SHA"
  SOURCE_STATE="POST_CO2"
fi

echo "CO2_SOURCE_STATE=$SOURCE_STATE"
echo "CO2_DASHBOARD_SHA256=$dh"
echo "CO2_MODULE_SHA256=$co2hash"
echo "CO2_EXPECTED_MODULE_SHA256=$CO2SHA"

SOURCE_STATE="$SOURCE_STATE" python3 - <<'PY'
import json, os
d=json.load(open('/tmp/co2-before.json'))
t8=d.get('t8_countertest') or {}
t9=d.get('t9_stability') or {}
s5=d.get('s5_fast_index') or {}
co1=d.get('co1_archive') or {}
co2=d.get('co2_proof_chain') or {}
bm=d.get('brutomagique') or {}
keys=[
 ('STATE',d.get('state')),('PROCESSED',d.get('processed_packets')),
 ('CRYSTALS',bm.get('total_crystals')),('S5_OBSERVATIONS',s5.get('observations')),
 ('S5_INDEXED',s5.get('indexed')),('CO1_OBSERVATIONS',co1.get('observations')),
 ('CO1_ELIGIBLE',co1.get('eligible_s5')),('CO1_APPENDED',co1.get('appended_records')),
 ('CO1_PRESENT',co1.get('already_present')),('CO1_PHYSICAL',co1.get('physical_records_seen')),
 ('CO1_LOAD_ERRORS',co1.get('load_errors')),('CO1_WRITE_ERRORS',co1.get('write_errors')),
 ('CO2_OBSERVATIONS',co2.get('observations')),('CO2_ELIGIBLE',co2.get('eligible_co1')),
 ('CO2_BACKFILLED',co2.get('backfilled_links')),('CO2_RUNTIME_APPENDED',co2.get('runtime_appended_links')),
 ('CO2_CHAIN_LINKS',co2.get('chain_links')),('CO2_ARCHIVE_SEEN',co2.get('archive_records_seen')),
 ('CO2_INTEGRITY_FAILURES',co2.get('integrity_failures')),('CO2_WRITE_ERRORS',co2.get('write_errors')),
 ('CO2_HEAD',co2.get('head_chain_hash')),
]
for k,v in keys: print(f"{k}={v}")
assert not d.get('worker_error')
assert int(t8.get('failed') or 0)==0 and int(t8.get('limited') or 0)==0
assert int(t9.get('drifts') or 0)==0
assert co1.get('enabled') is True and co1.get('available') is True
assert int(co1.get('load_errors') or 0)==0 and int(co1.get('write_errors') or 0)==0
assert int(co1.get('observations') or 0)==int(s5.get('observations') or 0)
assert int(co1.get('eligible_s5') or 0)==int(s5.get('indexed') or 0)
if os.environ['SOURCE_STATE']=='POST_CO2':
    assert co2.get('enabled') is True and co2.get('available') is True
    assert co2.get('authority')=='TRACE_INTEGRITY_ONLY'
    assert co2.get('source_of_truth')=='CO1_ARCHIVE_PHYSICAL_ORDER'
    assert co2.get('hash_algorithm')=='SHA-256'
    assert co2.get('chain_definition')=='PHYSICAL_CO1_ARCHIVE_RECORD_ORDER'
    assert co2.get('append_only') is True and co2.get('rewrites_existing_links') is False
    assert co2.get('co1_archive_mutated') is False
    assert co2.get('trace_integrity_claim') is True
    assert co2.get('scientific_proof_claim') is False
    assert co2.get('truth_of_claim_established') is False
    assert co2.get('historical_attestation_claim') is False
    assert co2.get('external_trust_anchor') is False
    assert co2.get('digital_signature_enabled') is False
    assert co2.get('validation_state_mutated') is False and co2.get('proof_promotion') is False
    assert co2.get('controls_routing') is False and co2.get('controls_scheduling') is False and co2.get('controls_calculation') is False
    assert co2.get('co3_checkpoint_input') is True
    assert int(co2.get('observations') or 0)==int(co1.get('observations') or 0)
    assert int(co2.get('eligible_co1') or 0)==int(co1.get('eligible_s5') or 0)
    assert int(co2.get('blocked_co1_other') or 0)==int(co1.get('observations') or 0)-int(co1.get('eligible_s5') or 0)
    assert int(co2.get('blocked_chain_unavailable') or 0)==0
    assert int(co2.get('archive_load_errors') or 0)==0
    assert int(co2.get('chain_load_errors') or 0)==0
    assert int(co2.get('write_errors') or 0)==0
    assert int(co2.get('integrity_failures') or 0)==0
    assert int(co2.get('chain_links') or 0)==int(co2.get('archive_records_seen') or 0)
print('CO2_AUDIT_ONLY=PASS')
PY

if [ -f "$ARCHIVE" ]; then
  echo "CO2_ARCHIVE_LINES=$(wc -l < "$ARCHIVE")"
  echo "CO2_ARCHIVE_SHA256=$(sha "$ARCHIVE")"
fi
if [ -f "$CHAIN" ]; then
  echo "CO2_CHAIN_LINES=$(wc -l < "$CHAIN")"
  echo "CO2_CHAIN_SHA256=$(sha "$CHAIN")"
fi
df -P / | awk 'NR==2 {print "ROOT_DISK_USED=" $5 " ROOT_DISK_FREE_KB=" $4}'

[ "$MODE" = "canary_start" ] || exit 0
test "$SOURCE_STATE" = "PRE_CO2"

STAGE="/tmp/co2-stage-$$"
mkdir -p "$STAGE/src"
cp -a "$PKG" "$STAGE/src/brotoculateur"
python3 /tmp/patch_brotoculateur_co2_proof_chain.py "$STAGE"
test "$(sha "$STAGE/src/brotoculateur/co2_proof_chain.py")" = "$CO2SHA"
POST_DASH="$(sha "$STAGE/src/brotoculateur/dashboard.py")"
echo "CO2_STAGED_POST_DASHBOARD_SHA256=$POST_DASH"

PYTHONPATH="$STAGE/src" \
BROTO_T8_ENABLED=1 BROTO_T9_ENABLED=1 BROTO_T10_ENABLED=1 BROTO_T11_ENABLED=1 \
BROTO_T12_ENABLED=1 BROTO_L1_ENABLED=1 BROTO_L2_ENABLED=1 BROTO_L3_ENABLED=1 \
BROTO_L4_ENABLED=1 BROTO_L5_ENABLED=1 BROTO_S1_ENABLED=1 BROTO_S2_ENABLED=1 \
BROTO_S3_ENABLED=1 BROTO_S4_ENABLED=1 BROTO_S5_ENABLED=1 BROTO_CO1_ENABLED=1 BROTO_CO2_ENABLED=1 \
BROTO_L2_THRESHOLD=75 BROTO_T11_CPU_SLOTS=8 BROTO_T11_MEMORY_SLOTS=8 \
BROTO_T11_STORAGE_SLOTS=8 BROTO_T11_TIME_SLOTS=8 \
python3 /tmp/test_co2_proof_chain.py
echo "CO2_EXACT_LIVE_STAGE=PASS"

before_state="$(python3 -c "import json;print(json.load(open('/tmp/co2-before.json')).get('state'))")"
if [ "$before_state" = "RUNNING" ]; then
  api_post http://127.0.0.1:8781/api/save
  api_post http://127.0.0.1:8781/api/pause
fi

B="$ROOT/backups/co2-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$B"
cp -a "$DASH" "$CO1" "$S5" "$C3" "$B/"
cp -a /tmp/co2-before.json "$B/status-before.json"
[ ! -f "$ARCHIVE" ] || cp -a "$ARCHIVE" "$B/archive-before.jsonl"
[ ! -f "$CHAIN" ] || cp -a "$CHAIN" "$B/chain-before.jsonl"
echo "CO2_BACKUP=$B"

D="$HOME/.config/systemd/user/brotoculateur.service.d"
F="$D/99-brutus-co2.conf"
mkdir -p "$D"

rollback() {
  set +e
  cp -a "$B/dashboard.py" "$DASH"
  rm -f "$CO2" "$F"
  systemctl --user daemon-reload
  systemctl --user restart brotoculateur.service
  wait_api
  [ "$before_state" != "RUNNING" ] || api_post http://127.0.0.1:8781/api/start
  echo "CO2_ROLLBACK_ARCHIVE_PRESERVED=YES"
  echo "CO2_ROLLBACK_CHAIN_PRESERVED=YES"
  exit 1
}
trap rollback ERR

cp -a "$STAGE/src/brotoculateur/dashboard.py" "$DASH"
cp -a "$STAGE/src/brotoculateur/co2_proof_chain.py" "$CO2"
printf '[Service]\nEnvironment="BROTO_CO2_ENABLED=1"\n' > "$F"
systemctl --user daemon-reload
systemctl --user restart brotoculateur.service
wait_api
api_post http://127.0.0.1:8781/api/start

ok=0
for _ in $(seq 1 45); do
  sleep 1
  curl -fsS "$URL" > /tmp/co2-live.json
  if python3 - <<'PY'
import json,sys
d=json.load(open('/tmp/co2-live.json'))
co1=d.get('co1_archive') or {}
co2=d.get('co2_proof_chain') or {}
good=(
 d.get('state')=='RUNNING'
 and int(co2.get('observations') or 0)>0
 and int(co2.get('observations') or 0)==int(co1.get('observations') or 0)
 and int(co2.get('eligible_co1') or 0)==int(co1.get('eligible_s5') or 0)
 and int(co2.get('blocked_chain_unavailable') or 0)==0
 and int(co2.get('integrity_failures') or 0)==0
 and int(co2.get('write_errors') or 0)==0
 and co2.get('available') is True
)
sys.exit(0 if good else 1)
PY
  then ok=1; break; fi
done
test "$ok" = 1

python3 - <<'PY'
import json
d=json.load(open('/tmp/co2-live.json'))
co1=d.get('co1_archive') or {}
co2=d.get('co2_proof_chain') or {}
for k,v in [
 ('CO2_LIVE_STATE',d.get('state')),
 ('CO2_LIVE_CO1_OBSERVATIONS',co1.get('observations')),
 ('CO2_LIVE_OBSERVATIONS',co2.get('observations')),
 ('CO2_LIVE_ELIGIBLE',co2.get('eligible_co1')),
 ('CO2_LIVE_BACKFILLED',co2.get('backfilled_links')),
 ('CO2_LIVE_RUNTIME_APPENDED',co2.get('runtime_appended_links')),
 ('CO2_LIVE_CHAIN_LINKS',co2.get('chain_links')),
 ('CO2_LIVE_ARCHIVE_SEEN',co2.get('archive_records_seen')),
 ('CO2_LIVE_HEAD',co2.get('head_chain_hash')),
]: print(f"{k}={v}")
print("CO2_LIVE_VERIFY=PASS")
PY

api_post http://127.0.0.1:8781/api/save
api_post http://127.0.0.1:8781/api/pause
frozen=0
for _ in $(seq 1 30); do
  sleep 1
  curl -fsS "$URL" > /tmp/co2-quiescent.json
  if python3 -c "import json,sys;sys.exit(0 if json.load(open('/tmp/co2-quiescent.json')).get('state')=='PAUSED' else 1)"; then
    frozen=1
    break
  fi
done
test "$frozen" = 1

a1="$(wc -l < "$ARCHIVE")"
c1="$(wc -l < "$CHAIN")"
sleep 1
curl -fsS "$URL" > /tmp/co2-quiescent.json
a2="$(wc -l < "$ARCHIVE")"
c2="$(wc -l < "$CHAIN")"
test "$a1" -eq "$a2"
test "$c1" -eq "$c2"
test "$a2" -eq "$c2"

PYTHONPATH=/tmp python3 /tmp/verify_co2_chain_files.py "$ARCHIVE" "$CHAIN"

STATUS_LINKS="$(python3 -c "import json;print(int((json.load(open('/tmp/co2-quiescent.json')).get('co2_proof_chain') or {}).get('chain_links') or 0))")"
test "$STATUS_LINKS" -eq "$a2"
echo "CO2_QUIESCENT_ARCHIVE_LINES=$a2"
echo "CO2_QUIESCENT_CHAIN_LINES=$c2"
echo "CO2_QUIESCENT_PHYSICAL_MATCH=PASS"

test "$(sha "$DASH")" = "$POST_DASH"
test "$(sha "$CO2")" = "$CO2SHA"
echo "CO2_ARCHIVE_SHA256=$(sha "$ARCHIVE")"
echo "CO2_CHAIN_SHA256=$(sha "$CHAIN")"
echo "CO2_POST_DASHBOARD_SHA256=$POST_DASH"

api_post http://127.0.0.1:8781/api/start
running=0
for _ in $(seq 1 30); do
  sleep 1
  curl -fsS "$URL" > /tmp/co2-restarted.json
  if python3 -c "import json,sys;sys.exit(0 if json.load(open('/tmp/co2-restarted.json')).get('state')=='RUNNING' else 1)"; then
    running=1
    break
  fi
done
test "$running" = 1
echo "CO2_RESTART_AFTER_PROOF=PASS"

trap - ERR
rm -rf "$STAGE"
echo "CO2_WORKFLOW=PASS"
