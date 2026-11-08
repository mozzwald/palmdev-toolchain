#!/usr/bin/env bash
set -euo pipefail
ROOT=${PALMDEV_ROOT:-$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)}
. "$ROOT/config/source-versions.conf"
LOCAL="$ROOT/.local"
sdk_dir() { printf '%s/sdk/sdk-%s' "$LOCAL" "$1"; }
sha256() { shasum -a 256 "$1" 2>/dev/null || sha256sum "$1"; }
is_tty() { [ -t 0 ] && [ -t 1 ]; }

host_backend() {
  case "$(uname -s):$(uname -m)" in
    Linux:x86_64|Linux:aarch64|Linux:arm64|Darwin:x86_64|Darwin:arm64) echo docker ;;
    *) echo "Unsupported host: $(uname -s) $(uname -m)" >&2; return 1 ;;
  esac
}

require_python() {
  command -v python3 >/dev/null || { echo 'Python 3.8 or newer is required.' >&2; return 1; }
  python3 -c 'import sys; sys.exit(sys.version_info < (3, 8))' || { echo 'Python 3.8 or newer is required.' >&2; return 1; }
}

docker_platform() {
  # Use the tested amd64 recipe on ARM hosts, explicitly under emulation.
  case "${PALMDEV_PLATFORM:-linux/amd64}" in
    linux/amd64) echo linux/amd64 ;;
    *) echo 'Only linux/amd64 toolchain images are currently supported.' >&2; return 1 ;;
  esac
}

toolchain_key() {
  python3 - "$ROOT" "$(docker_platform)" <<'PY'
import hashlib, pathlib, sys
root = pathlib.Path(sys.argv[1])
h = hashlib.sha256()
for name in ('Dockerfile', 'config/source-versions.conf'):
    h.update((root / name).read_bytes())
h.update(sys.argv[2].encode())
print(h.hexdigest())
PY
}
