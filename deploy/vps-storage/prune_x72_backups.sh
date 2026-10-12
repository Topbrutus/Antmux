#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$HOME/antmux-x72-queen-backups}"
EXPECTED="$HOME/antmux-x72-queen-backups"

if [ "$ROOT" != "$EXPECTED" ]; then
  printf 'REFUSING_BACKUP_ROOT=%s\n' "$ROOT" >&2
  exit 2
fi

mkdir -p "$ROOT"

size_kb() {
  du -sk "$1" 2>/dev/null | awk '{print $1+0}'
}

prune_pattern() {
  local pattern="$1"
  local keep="$2"
  local label="$3"
  local -a dirs=()
  local i

  mapfile -t dirs < <(
    find "$ROOT" -mindepth 1 -maxdepth 1 -type d -name "$pattern" -printf '%T@ %p\n' 2>/dev/null \
      | sort -rn \
      | cut -d' ' -f2-
  )

  printf 'RETENTION_%s_FOUND=%s KEEP=%s\n' "$label" "${#dirs[@]}" "$keep"
  for ((i=keep; i<${#dirs[@]}; i++)); do
    case "${dirs[$i]}" in
      "$ROOT"/*) ;;
      *) printf 'REFUSING_DELETE=%s\n' "${dirs[$i]}" >&2; exit 3 ;;
    esac
    printf 'PRUNE_%s=%s SIZE_KB=%s\n' "$label" "${dirs[$i]}" "$(size_kb "${dirs[$i]}")"
    rm -rf -- "${dirs[$i]}"
  done
}

before_kb="$(size_kb "$ROOT")"
printf 'X72_BACKUP_ROOT=%s\n' "$ROOT"
printf 'X72_BACKUP_BEFORE_KB=%s\n' "$before_kb"

# Full deploy snapshots were the main source of runaway growth.
prune_pattern '20*' 3 FULL
# Surgical rollback points are small/useful, but still bounded.
prune_pattern 'hotfix-live-*' 5 HOTFIX
prune_pattern 'relation-runtime-*' 5 RELATION
prune_pattern 'z3-final-birth-*' 3 Z3
prune_pattern 'frontend-server-authority-*' 3 FRONTEND
prune_pattern 'nginx-*' 3 NGINX

after_kb="$(size_kb "$ROOT")"
printf 'X72_BACKUP_AFTER_KB=%s\n' "$after_kb"
printf 'X72_BACKUP_FREED_KB=%s\n' "$(( before_kb - after_kb ))"
printf 'X72_RETENTION=PASS\n'
