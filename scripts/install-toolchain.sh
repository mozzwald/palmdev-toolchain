#!/usr/bin/env bash
set -euo pipefail
. "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/common.sh"
require_python
backend=${1:-$(host_backend)}
[ "$backend" = docker ] || { echo 'Native macOS builds are not supported yet; use the Docker backend.' >&2; exit 2; }
command -v docker >/dev/null || { echo 'Docker is required. On macOS install Docker Desktop (or another Docker VM), then start its daemon and rerun setup.' >&2; exit 1; }
docker info >/dev/null 2>&1 || { echo 'Docker daemon is unavailable. Start Docker and check your access permissions.' >&2; exit 1; }
platform=$(docker_platform)
case "$(uname -m)" in arm64|aarch64) echo 'Using linux/amd64 under Docker emulation; native ARM compiler builds are not verified.' ;; esac
recipe_hash=$(toolchain_key)
installed_hash=$(docker image inspect --format '{{ index .Config.Labels "palmdev.toolchain-key" }}' "$TOOLCHAIN_IMAGE" 2>/dev/null || true)
if [ "$installed_hash" = "$recipe_hash" ]; then
  echo "Toolchain image already present: $TOOLCHAIN_IMAGE"
else
  echo 'Building pinned toolchain image (this can take several minutes)...'
  # Docker only replaces this tag after a successful build; an old working image survives failures.
  docker build --platform "$platform" --label "palmdev.toolchain-key=$recipe_hash" \
    --build-arg BASE_IMAGE="$BASE_IMAGE" --build-arg DEBIAN_SNAPSHOT="$DEBIAN_SNAPSHOT" \
    --build-arg PRC_TOOLS_REPO="$PRC_TOOLS_REPO" --build-arg PRC_TOOLS_REV="$PRC_TOOLS_REV" \
    --build-arg PILRC_REPO="$PILRC_REPO" --build-arg PILRC_REV="$PILRC_REV" \
    -t "$TOOLCHAIN_IMAGE" "$ROOT"
fi
mkdir -p "$LOCAL/config"
printf 'backend=docker\nplatform=%s\ntoolchain_key=%s\nprc_tools_revision=%s\npilrc_revision=%s\n' \
  "$platform" "$recipe_hash" "$PRC_TOOLS_REV" "$PILRC_REV" > "$LOCAL/config/toolchain.conf.tmp"
mv "$LOCAL/config/toolchain.conf.tmp" "$LOCAL/config/toolchain.conf"
