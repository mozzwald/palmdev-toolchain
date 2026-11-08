#!/usr/bin/env bash
set -euo pipefail
. "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/common.sh"
meta="$LOCAL/licenses/handspring.accepted"
dest="$LOCAL/sdk/handspring"
require_python
# A matching installed revision was already reviewed. Avoid a misleading
# second opt-in prompt during every setup run.
if python3 "$ROOT/scripts/sdk-state.py" status "$dest" "$meta" "$HANDSPRING_SDK_REV"; then
  echo 'Handspring SDK is already installed; skipping installation prompt.'
  exit 0
fi
answer=${PALMDEV_HANDSPRING:-}
if [ -z "$answer" ] && is_tty; then read -r -p 'Install optional Handspring SDK? [y/N] ' answer; fi
[[ $answer =~ ^[Yy] ]] || { echo 'Handspring SDK not selected.'; exit 0; }
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
trap 'exit 130' INT
trap 'exit 143' HUP TERM
git clone "$HANDSPRING_SDK_REPO" "$tmp/source" >/dev/null
git -C "$tmp/source" checkout --detach "$HANDSPRING_SDK_REV" >/dev/null
if python3 "$ROOT/scripts/sdk-state.py" install "$dest" "$meta" "$HANDSPRING_SDK_REV" "$tmp/source" 'Handspring SDK'; then :; else
  status=$?; case "$status" in 3|4) exit 0 ;; *) exit "$status" ;; esac
fi
