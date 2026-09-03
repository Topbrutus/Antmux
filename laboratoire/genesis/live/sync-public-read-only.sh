#!/usr/bin/env bash
set -euo pipefail

umask 077

required_vars=(
  GENESIS_PRIVATE_REPO_SSH
  GENESIS_PRIVATE_REF
  GENESIS_PRIVATE_RESULT_PATH
  GENESIS_DEPLOY_KEY
  GENESIS_GITHUB_KNOWN_HOSTS
  GENESIS_RUNTIME_DIR
  GENESIS_PUBLIC_OUTPUT
  GENESIS_BUILDER
  GENESIS_BRIDGE
  GENESIS_VALIDATOR
  GENESIS_PUBLIC_LIVE_ACTIVE
)
for name in "${required_vars[@]}"; do
  test -n "${!name:-}" || { printf 'GENESIS_LIVE_SYNC_INVALID: missing %s\n' "$name" >&2; exit 1; }
done

test "$GENESIS_PUBLIC_LIVE_ACTIVE" = '0' || test "$GENESIS_PUBLIC_LIVE_ACTIVE" = '1' || {
  printf 'GENESIS_LIVE_SYNC_INVALID: GENESIS_PUBLIC_LIVE_ACTIVE must be 0 or 1\n' >&2
  exit 1
}

for command_name in git node mktemp; do
  command -v "$command_name" >/dev/null 2>&1 || { printf 'GENESIS_LIVE_SYNC_INVALID: missing command %s\n' "$command_name" >&2; exit 1; }
done

test -f "$GENESIS_DEPLOY_KEY" || { printf 'GENESIS_LIVE_SYNC_INVALID: deploy key missing\n' >&2; exit 1; }
test -f "$GENESIS_GITHUB_KNOWN_HOSTS" || { printf 'GENESIS_LIVE_SYNC_INVALID: known_hosts missing\n' >&2; exit 1; }
test -f "$GENESIS_BUILDER" || { printf 'GENESIS_LIVE_SYNC_INVALID: builder missing\n' >&2; exit 1; }
test -f "$GENESIS_BRIDGE" || { printf 'GENESIS_LIVE_SYNC_INVALID: bridge missing\n' >&2; exit 1; }
test -f "$GENESIS_VALIDATOR" || { printf 'GENESIS_LIVE_SYNC_INVALID: validator missing\n' >&2; exit 1; }

mkdir -p "$GENESIS_RUNTIME_DIR"
mkdir -p "$(dirname "$GENESIS_PUBLIC_OUTPUT")"

lock_dir="$GENESIS_RUNTIME_DIR/.sync-lock"
if ! mkdir "$lock_dir" 2>/dev/null; then
  printf 'GENESIS_LIVE_SYNC_SKIPPED: another sync is running\n'
  exit 0
fi

work_dir="$(mktemp -d "$GENESIS_RUNTIME_DIR/.work.XXXXXX")"
private_status="$work_dir/private-status.txt"
bridge_input="$work_dir/bridge-input.json"
staging_public="$(mktemp "$(dirname "$GENESIS_PUBLIC_OUTPUT")/.public-read-only.json.XXXXXX")"
cleanup() {
  rm -rf "$work_dir" "$lock_dir"
  rm -f "$staging_public"
}
trap cleanup EXIT INT TERM

ssh_command="ssh -i $GENESIS_DEPLOY_KEY -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$GENESIS_GITHUB_KNOWN_HOSTS -o HostKeyAlgorithms=ssh-ed25519"
source_git="$GENESIS_RUNTIME_DIR/private-source.git"

if test ! -d "$source_git"; then
  git init --bare -q "$source_git"
  git --git-dir="$source_git" remote add origin "$GENESIS_PRIVATE_REPO_SSH"
else
  actual_remote="$(git --git-dir="$source_git" remote get-url origin)"
  test "$actual_remote" = "$GENESIS_PRIVATE_REPO_SSH" || { printf 'GENESIS_LIVE_SYNC_INVALID: private source remote mismatch\n' >&2; exit 1; }
fi

GIT_SSH_COMMAND="$ssh_command" git --git-dir="$source_git" fetch -q --no-tags --prune --depth=1 origin "$GENESIS_PRIVATE_REF"
source_commit="$(git --git-dir="$source_git" rev-parse FETCH_HEAD)"
git --git-dir="$source_git" show "FETCH_HEAD:$GENESIS_PRIVATE_RESULT_PATH" > "$private_status"

(
  cd "$work_dir"
  node "$GENESIS_BUILDER" "$private_status" "$bridge_input" >/dev/null
  node "$GENESIS_BRIDGE" "$bridge_input" >/dev/null
  node "$GENESIS_VALIDATOR" "$work_dir/.build/genesis-public-read-only-bridge/public-read-only-envelope.json" >/dev/null
)

generated="$work_dir/.build/genesis-public-read-only-bridge/public-read-only-envelope.json"
test -s "$generated" || { printf 'GENESIS_LIVE_SYNC_INVALID: public envelope missing\n' >&2; exit 1; }

if grep -Fq "$GENESIS_PRIVATE_REPO_SSH" "$generated" || \
   grep -Fq "$GENESIS_PRIVATE_REF" "$generated" || \
   grep -Fq "$GENESIS_PRIVATE_RESULT_PATH" "$generated"; then
  printf 'GENESIS_LIVE_SYNC_INVALID: private source identifier leaked into public envelope\n' >&2
  exit 1
fi

printf '%s\n' "$source_commit" > "$GENESIS_RUNTIME_DIR/last-source-commit"
chmod 0600 "$GENESIS_RUNTIME_DIR/last-source-commit"

cp "$generated" "$staging_public"
chmod 0644 "$staging_public"
mv -f "$staging_public" "$GENESIS_PUBLIC_OUTPUT"

printf 'GENESIS_LIVE_SYNC_VALID\n'
printf 'PUBLIC_MODE=LIVE_READ_ONLY\n'
printf 'PUBLIC_SOURCE=PUBLIC_READ_ONLY\n'
printf 'PUBLIC_LIVE_ACTIVE=%s\n' "$GENESIS_PUBLIC_LIVE_ACTIVE"
printf 'PUBLIC_WRITE_CAPABILITY=NONE\n'
printf 'PRIVATE_IDENTIFIERS_PROJECTED=no\n'
