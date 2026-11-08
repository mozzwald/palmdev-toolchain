#!/usr/bin/env bash
# Safe entry point; all persistent state stays below .local.
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
export PALMDEV_ROOT="$ROOT"
. "$ROOT/scripts/common.sh"
require_python
command -v git >/dev/null || { echo 'Git is required; install Git and rerun setup.' >&2; exit 1; }
mkdir -p "$ROOT/.local"/{sdk,downloads,config,licenses,build-cache}
os=$(uname -s); arch=$(uname -m)
backend=$(host_backend)
printf 'Palmdev Toolchain: %s %s (%s backend)\n' "$os" "$arch" "$backend"
if [ "$os" = Darwin ]; then echo 'macOS uses Docker; native compiler builds are not yet supported. Homebrew is not required.'; fi
"$ROOT/scripts/install-toolchain.sh" "$backend"
"$ROOT/scripts/install-palm-sdks.sh"
compgen -G "$LOCAL/sdk/sdk-*" >/dev/null || { echo 'No Palm OS SDK installed. Rerun setup and accept at least one SDK agreement.' >&2; exit 1; }
"$ROOT/scripts/install-handspring-sdk.sh"
"$ROOT/scripts/configure-sdks.sh"
"$ROOT/scripts/doctor.sh"
"$ROOT/scripts/verify-toolchain.sh"
first_sdk=
for path in "$LOCAL"/sdk/sdk-*; do if [ -d "$path" ]; then first_sdk=${path##*/sdk-}; break; fi; done
echo "Setup finished. Example: ./palm-build --sdk $first_sdk --project examples/hello-world -- make"
