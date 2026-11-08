# Hello World

Build this 68K Palm OS application through the checked-out toolchain:

```sh
./palm-build --sdk 3.1 --project examples/hello-world -- make
```

The output is `build/sdk-3.1/HelloWorld.prc` (or the selected SDK version). The Makefile uses `PALMOS_SDK` and `PALMOS_SDK_VERSION`, so it is also a compact example for external projects. The app loads a standard form and displays “Hello, World!”. Compilation and PRC validation are automated; emulator/device execution remains a manual check.
