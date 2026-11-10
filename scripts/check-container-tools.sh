#!/usr/bin/env bash
# Executed inside the image by doctor and verify-toolchain; no SDK required.
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
. "$ROOT/config/source-versions.conf"

for tool in python3 m68k-palmos-gcc m68k-palmos-ar m68k-palmos-objcopy m68k-palmos-objdump m68k-palmos-nm pilrc build-prc palmdev-prep; do
  command -v "$tool" >/dev/null || { echo "Required container tool is missing: $tool" >&2; exit 1; }
done
python3 - <<'PY'
import json
import pathlib
import struct
import subprocess
import sys
import tempfile

if sys.version_info < (3, 8):
    raise SystemExit('Container Python 3.8 or newer is required')
assert struct.unpack('>I', bytes.fromhex('12345678')) == (0x12345678,)
with tempfile.TemporaryDirectory() as directory:
    path = pathlib.Path(directory) / 'check.json'
    path.write_text(json.dumps({'python': True}))
    assert json.loads(path.read_text()) == {'python': True}
assert subprocess.check_output([sys.executable, '-c', 'print("ok")'], text=True).strip() == 'ok'
print('Container Python:', sys.version.split()[0], '(build-helper smoke check passed)')
PY
gcc_banner=$(m68k-palmos-gcc --version)
[[ "$gcc_banner" == "$GCC_BANNER_VERSION" ]] || { echo "Unexpected GCC banner: $gcc_banner" >&2; exit 1; }
prc_banner=$(build-prc --version)
[[ "${prc_banner%%$'\n'*}" == "build-prc (prc-tools) $BUILD_PRC_BANNER_VERSION" ]] || { echo "Unexpected build-prc banner: $prc_banner" >&2; exit 1; }
pilrc_banner=$(pilrc 2>&1) || [ "$?" = 1 ]
[[ "${pilrc_banner%%$'\n'*}" == "PilRC v$PILRC_BANNER_VERSION" ]] || { echo "Unexpected PilRC banner: $pilrc_banner" >&2; exit 1; }
printf 'prc-tools-remix source: %s (%s); build-prc banner: %s; GCC: %s\n' \
  "$PRC_TOOLS_VERSION" "$PRC_TOOLS_REV" "$BUILD_PRC_BANNER_VERSION" "$gcc_banner"
printf 'PilRC source: %s (%s); banner: %s\n' "$PILRC_VERSION" "$PILRC_REV" "$PILRC_BANNER_VERSION"
test -f /usr/m68k-palmos/lib/crt0.o
