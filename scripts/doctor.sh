#!/usr/bin/env bash
set -euo pipefail
. "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/common.sh"
echo "Host: $(uname -s) $(uname -m)"
host_backend >/dev/null
require_python
echo "Backend: Docker ($(docker_platform)); Homebrew is not required"
case "$(uname -m)" in arm64|aarch64) echo 'Architecture: amd64 emulation required (ARM hosts not yet execution-tested).' ;; esac
fail=0; image=${PALMDEV_IMAGE:-$TOOLCHAIN_IMAGE}
if ! command -v docker >/dev/null; then echo 'Docker: MISSING — install Docker and rerun setup.'; fail=1
elif ! docker info >/dev/null 2>&1; then echo 'Docker daemon: UNAVAILABLE'; fail=1
else
  echo "Docker: $(docker --version)"
  if docker image inspect "$image" >/dev/null 2>&1; then
    if ! docker run --rm --platform "$(docker_platform)" --entrypoint /bin/bash "$image" -euo pipefail -c '
      m68k-palmos-gcc --version
      command -v pilrc
      pilrc_version=$(pilrc 2>&1) || [ "$?" = 1 ]
      [[ "$pilrc_version" == PilRC* ]]
      printf "%s\n" "$pilrc_version" | sed -n "1p"
      command -v build-prc
      command -v palmdev-prep
      test -f /usr/m68k-palmos/lib/crt0.o
    '; then echo 'Tool availability: FAIL'; fail=1; fi
    installed=$(docker image inspect --format '{{ index .Config.Labels "palmdev.toolchain-key" }}' "$image")
    if [ "$installed" != "$(toolchain_key)" ]; then echo 'Toolchain revision: STALE — rerun ./setup.sh'; fail=1; fi
  else echo 'Toolchain image: MISSING — run ./setup.sh'; fail=1; fi
fi
echo 'SDKs:'; found=0
for p in "$LOCAL"/sdk/sdk-*; do
  [ -d "$p" ] || continue
  found=1; echo "  ${p##*/sdk-}"
  if [ ! -f "$LOCAL/licenses/${p##*/}.accepted" ]; then echo '    acceptance record: MISSING'; fail=1; fi
done
if [ "$found" = 0 ]; then echo '  none — run ./setup.sh'; fail=1; fi
[ -d "$LOCAL/sdk/handspring" ] && echo 'Handspring: installed' || echo 'Handspring: absent'
echo 'palmdev-prep: specs are generated for each palm-build invocation; host compiler files are untouched.'
if [ ! -f "$LOCAL/config/installed-sdks.conf" ]; then echo 'SDK inventory: MISSING — run ./scripts/configure-sdks.sh'; fail=1; fi
exit "$fail"
