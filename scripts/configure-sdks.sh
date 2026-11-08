#!/usr/bin/env bash
set -euo pipefail
. "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/common.sh"
mkdir -p "$LOCAL/config"
{ echo "# Generated local SDK inventory"; for path in "$LOCAL"/sdk/sdk-*; do [ -d "$path" ] && printf '%s=%s\n' "${path##*/sdk-}" "$path"; done; true; } > "$LOCAL/config/installed-sdks.conf.tmp"
mv "$LOCAL/config/installed-sdks.conf.tmp" "$LOCAL/config/installed-sdks.conf"
echo "SDK configuration written to .local/config/installed-sdks.conf"
