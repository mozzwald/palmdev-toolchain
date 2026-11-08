# palmdev-toolchain

A reproducible, general-purpose Palm OS development environment for classic 68K applications. It builds open-source tools from pinned sources, keeps proprietary SDK files local to this checkout, and provides one build command on Linux and macOS.

```sh
git clone https://github.com/mozzwald/palmdev-toolchain
cd palmdev-toolchain
./setup.sh
./palm-build --sdk 3.1 --project examples/hello-world -- make
```

Linux and macOS use the tracked `Dockerfile`; the resulting image is local and SDK-free. Install Git, Python 3.8 or newer, and Docker with a running daemon before setup. On macOS, Docker Desktop or another Docker VM is required; Homebrew is optional. All compiler tools run inside individual containers that exit when their command finishes.

Linux x86_64 is execution-tested. macOS Intel, macOS Apple Silicon, and Linux ARM64 use the same `linux/amd64` image; ARM hosts require Docker's amd64 emulation. Those hosts still require execution testing. Native macOS compilation is not currently supported: the pinned upstream build script targets Linux and needs platform-specific changes before native support can be offered reliably.

`setup.sh` discovers SDK directories at the pinned Palm SDK revision and defaults to 3.1 and 3.5. Each selected SDK is staged separately, its included license is shown, and installation needs `agree`. At the locked revision, every discovered `sdk-*` directory has an included agreement, including 3.5, 4, and 5r4. The installer still refuses any future SDK selection for which an applicable agreement cannot be found. This repository does not grant SDK rights.

Run setup again to add SDKs; accepted, unchanged SDKs are retained. Optional Handspring SDK 4.0 is offered separately. All SDKs, downloads, acceptance hashes, and generated settings are under ignored `.local/`.

For an external project:

```sh
./palm-build --sdk 3.1 --project "/path/to/My Palm App" -- make clean
./palm-build --sdk 3.1 --project /path/to/app -- m68k-palmos-gcc --version
./palm-build --sdk 3.1 --project /path/to/app --shell
./palm-build --sdk 3.1 --workspace /path/to/workspace --project /path/to/workspace/app -- make
```

The wrapper exports `PALMOS_SDK`, `PALMDEV_DIR`, and (when installed) `HANDSPRING_INCLUDE`. It automatically mounts a Git repository root; use `--workspace` for existing Makefiles that reach sibling repositories outside that root. Applications own their Makefiles; see `templates/simple-prc` and `examples/hello-world` for conventional PilRC / `build-prc` use.

Diagnostics: `./scripts/doctor.sh`; verify every installed SDK: `./scripts/verify-toolchain.sh`.

Setup verifies the tools and builds Hello World for every installed SDK. Outputs are kept separately under `examples/hello-world/build/sdk-VERSION/`. Automated fixture tests use temporary checkouts and no real SDK licenses: `python3 tests/test-toolchain.py`.

See [installation](docs/installation.md), [SDK management](docs/sdk-management.md), [SDK licensing](docs/sdk-licensing.md), [building applications](docs/building-apps.md), and [troubleshooting](docs/troubleshooting.md). Pinned revisions and the deliberate update point are in `config/source-versions.conf`.

Third-party credit and licensing boundaries are in [attribution](docs/attribution.md).

## Limitations

This initial release targets 68K PRC applications. ARM/PEAL tooling is built by prc-tools-remix where supported, but a generic ARM template is intentionally not claimed as verified. No emulator, device deployment, Windows support, FujiNet, or NIO integration is included.
