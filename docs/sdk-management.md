# SDK management

Rerun `./setup.sh` to select more SDKs. Existing SDKs are shown as installed but begin unselected, so their EULAs are not shown again. An installed SDK is skipped only when both its recorded source revision and license hash match; a changed source or license requires fresh review. Local records are in `.local/licenses`; inventory is `.local/config/installed-sdks.conf`.

The selected SDK is mounted read-only in Docker and exported as `PALMOS_SDK` (a directory), alongside `PALMOS_SDK_VERSION` (the selected version). `palmdev-prep` generates a private GCC specs file for every build invocation, which is mounted into the container and removed afterward. Host compiler configuration is never changed. Additional SDK installations work on the next build without rebuilding the image.

License hashes cover stable relative filenames and contents. Old acceptance records with staging-path-dependent hashes are migrated without another prompt only when the installed and pinned agreements match and the recorded source revision is unchanged. Installation stages a replacement beside the destination and rolls back on handled interruptions or errors. SIGKILL or power loss cannot run cleanup; preserve any `.local/sdk/.sdk-*.stage-*/previous` backup for recovery before rerunning setup.
