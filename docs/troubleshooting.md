# Troubleshooting

Run `./scripts/doctor.sh` first. Failures commonly mean Docker is missing, its daemon is unavailable, or the image has not built. Docker is required on macOS too; native compiler installation is not supported. On ARM64 hosts, enable amd64 emulation in Docker. All builds explicitly request `linux/amd64`.

If an SDK is unavailable, rerun setup and inspect the reported EULA condition. Do not copy proprietary SDK files into the image or repository.

After updating the source lockfile or Dockerfile, rerun `./setup.sh`; doctor reports a stale image until it has been rebuilt. If macOS Docker denies a mount, allow directory sharing for the checkout and the project/workspace. SDK paths containing spaces are supported by the wrapper. A missing vendor-specific header still requires the relevant separate SDK and the application's own include flags.
