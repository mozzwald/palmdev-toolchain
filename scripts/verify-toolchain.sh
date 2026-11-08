#!/usr/bin/env bash
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd); any=0; fail=0
. "$ROOT/scripts/common.sh"
require_python
summary=$(mktemp); trap 'rm -f "$summary"' EXIT
for sdk_path in "$ROOT"/.local/sdk/sdk-*; do
  [ -d "$sdk_path" ] || continue; any=1; sdk=${sdk_path##*/sdk-}
  # Force every compile/package step without deleting other SDK outputs.
  if "$ROOT/palm-build" --sdk "$sdk" --project "$ROOT/examples/hello-world" -- make -B all &&
     python3 "$ROOT/scripts/check-prc.py" "$ROOT/examples/hello-world/build/sdk-$sdk/HelloWorld.prc"; then
    echo "Palm OS SDK $sdk  PASS" >> "$summary"
  else echo "Palm OS SDK $sdk  FAIL" >> "$summary"; fail=1; fi
done
[ "$any" = 1 ] || { echo 'No installed SDKs: cannot verify.' >&2; exit 2; }
cat "$summary"
exit "$fail"
