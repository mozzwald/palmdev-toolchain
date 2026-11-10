# Building applications

Use `palm-build` around an application's own Makefile. It does not edit source files or impose packaging rules. A normal 68K Makefile passes `-I$(PALMOS_SDK)/include` (and needed subdirectories), invokes `pilrc`, then packages the linked binary plus `.bin` resources with `build-prc`.

Select the SDK that the application Makefile targets. For example, a Makefile that hardcodes `sdk-5r3` must be built with `--sdk 5r3`, after SDK 5r3 has been installed and its agreement accepted.

The included template is intentionally small and checkout-independent.

## Environment supplied to projects

These values describe paths **inside the container**, not host paths:

| Variable | Meaning | Example with `--sdk 3.1` |
| --- | --- | --- |
| `PALMOS_SDK` | Selected SDK directory, mounted read-only | `/opt/palmdev/sdk-3.1` |
| `PALMOS_SDK_VERSION` | SDK version suitable for `-palmosVERSION` | `3.1` |
| `PALMDEV_DIR` | Toolchain checkout, mounted read-only | `/toolchain` |
| `HANDSPRING_INCLUDE` | Handspring include directory, exported only when installed | `/toolchain/.local/sdk/handspring/Include` |

`HANDSPRING_INCLUDE` is a directory, without an `-I` prefix. Projects needing
Handspring headers should check for `$(HANDSPRING_INCLUDE)/UsbMgr.h` and pass
`-I"$(HANDSPRING_INCLUDE)"` to the compiler. Do not interpret `PALMOS_SDK` as
a version number. The wrapper selects which SDK is available; a Makefile with
a conflicting hardcoded `-palmos3.5` does not become a 3.1 build merely by
passing `--sdk 3.1`.

Python 3 is available inside the image for project build scripts, generators,
and artifact audits, as well as being required on the host for setup.
Project-specific Python packages, test harnesses, and CPU emulator dependencies
remain the project's responsibility. They are not installed by this toolchain.

`PALMOS_SDK` is a directory path, while `PALMOS_SDK_VERSION` is the requested version. The example and template put outputs under `build/sdk-$(PALMOS_SDK_VERSION)` so switching SDKs cannot reuse another SDK's object files. When changing arbitrary command-line compiler flags, use `make clean` or force a rebuild. Projects with their own Makefiles remain responsible for their own dependencies and output layout.

`--shell` requires an interactive terminal and opens Bash in the configured project directory. Ordinary commands are forwarded as argument arrays, including empty arguments, quotes, and newlines. Build outputs use the host user's UID/GID. Docker mounts the Git root by default; `--workspace` selects a larger shared root when a Makefile needs sibling repositories. Symlink targets must also be reachable within the mounted workspace.

## Projects that use sibling repositories

For a workspace containing `app/` and `common/`, with the app Makefile referring
to `../common/include`, mount their parent rather than just the app checkout:

```sh
./palm-build --sdk 3.1 --workspace "$HOME/palm-workspace" \
  --project "$HOME/palm-workspace/app" -- make
```

The command runs in `/workspace/app`, so `../common/include` remains valid.
The workspace is writable for build outputs. Choose the smallest shared parent
that contains the required sources. Paths exported by the wrapper are usable
inside this command; do not substitute host-only SDK paths into the Makefile.
