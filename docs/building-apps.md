# Building applications

Use `palm-build` around an application's own Makefile. It does not edit source files or impose packaging rules. A normal 68K Makefile passes `-I$(PALMOS_SDK)/include` (and needed subdirectories), invokes `pilrc`, then packages the linked binary plus `.bin` resources with `build-prc`.

Select the SDK that the application Makefile targets. For example, a Makefile that hardcodes `sdk-5r3` must be built with `--sdk 5r3`, after SDK 5r3 has been installed and its agreement accepted.

The included template is intentionally small and checkout-independent.

`PALMOS_SDK` is a directory path, while `PALMOS_SDK_VERSION` is the requested version. The example and template put outputs under `build/sdk-$(PALMOS_SDK_VERSION)` so switching SDKs cannot reuse another SDK's object files. When changing arbitrary command-line compiler flags, use `make clean` or force a rebuild. Projects with their own Makefiles remain responsible for their own dependencies and output layout.

`--shell` requires an interactive terminal and opens Bash in the configured project directory. Ordinary commands are forwarded as argument arrays, including empty arguments, quotes, and newlines. Build outputs use the host user's UID/GID. Docker mounts the Git root by default; `--workspace` selects a larger shared root when a Makefile needs sibling repositories. Symlink targets must also be reachable within the mounted workspace.
