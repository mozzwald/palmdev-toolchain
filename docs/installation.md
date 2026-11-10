# Installation

Install Git, Python 3.8 or newer, and Docker, then run `./setup.sh`. Linux and macOS build the local `palmdev-toolchain:local` image from the tracked Dockerfile. On macOS, use Docker Desktop or another Docker VM with directory sharing enabled for the toolchain and your projects. Homebrew is not required, and setup does not install it or write host compiler directories.

SDK selection is interactive: arrows or j/k move, Space toggles an SDK, and Enter confirms. Existing SDKs are marked and start unselected. With existing SDKs, Enter with no selections continues setup. Each new agreement requires its own `agree` response. In a noninteractive session `PALMDEV_SDK_SELECTION='3.1 3.5'` chooses versions; it never accepts licenses. There is no global acceptance option.

With the locked Palm SDK revision, every discovered `sdk-*` directory has an included agreement. The default 3.1 and 3.5 selections can be installed after individual review.

The supported image platform is `linux/amd64`. ARM Linux and Apple Silicon hosts use amd64 emulation; setup announces this explicitly. If Docker reports an execution-format error, enable its amd64 emulation. Native ARM toolchain compilation and native macOS compilation are not offered by setup. macOS and ARM hosts have not yet been execution-tested.

Setup preserves the previous Docker image if rebuilding fails. After SDK installation it runs doctor and compiles/packages the example against every installed SDK, inspecting each PRC's database identity and resource table. A failed check makes setup fail instead of printing a success message.

Both doctor and `scripts/verify-toolchain.sh` first check tools inside the real
container. This includes Python 3.8+ and a Python smoke check for binary data,
JSON files, temporary directories, and subprocesses used by build helpers.
Missing Python or an unexpected tool banner fails verification. After updating
this checkout, run `./scripts/install-toolchain.sh` to rebuild the image without
changing SDK selections, then doctor and verify-toolchain. Existing SDKs stay
installed; no repeated SDK download is needed for a Python-only image update.

Source pins, the Debian base image digest, and Debian package snapshot date live in `config/source-versions.conf`. Maintainers update those deliberately, verify revisions/artifacts against upstream, run `./setup.sh` to rebuild, and run the offline tests plus real SDK builds before committing. The image cache key includes the Dockerfile, lockfile, and image platform. Direct `docker build` defaults in the Dockerfile must be kept in sync with the lockfile; normal setup passes the lockfile values as build arguments. Snapshot repositories retain Debian signature verification; only their expiry check is disabled for historical builds. Bit-for-bit compiler outputs across different hosts are not claimed.

Run `python3 tests/test-toolchain.py` for offline regression tests. They require Git, Bash, Python, and a host C compiler (`cc`), but do not need Docker, proprietary SDKs, or real license acceptance. Tests create and remove private temporary checkouts. To repeat the shell compatibility tests with another Bash, use `PALMDEV_TEST_BASH=/path/to/bash python3 tests/test-toolchain.py`. The suite has passed with GNU Bash 3.2 and Bash 5.2 on Linux; this does not replace execution testing on macOS.
