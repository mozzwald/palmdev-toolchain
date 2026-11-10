# Attribution and licenses

## Pinned tool releases

| Tool | Pinned source release | Runtime version output |
| --- | --- | --- |
| prc-tools-remix | 2.3.6, commit `db9a91d746bac4c5921e3786c39b5dc3eca7b83c` | `build-prc (prc-tools) 2.3`; GCC `2.95.3-kgpd` |
| PilRC | 3.2.91, commit `981f88186a1aee57c4c19adc5c497016f01a4743` | `PilRC v3.2.90` |

Source release numbers come from each pinned repository's root `VERSION` file.
The runtime banners retain older component versions: PilRC's pinned
`version.h` still declares 3.2.90, and build-prc reports the prc-tools component
version. These are not interchangeable identifiers. The lockfile records both
the source releases and expected banners; container checks validate the latter.
When changing a pin, review `VERSION` and the runtime banner together rather
than modifying upstream version strings merely to make them agree.

The toolchain builds pinned copies of [prc-tools-remix](https://github.com/mozzwald/prc-tools-remix) and [PilRC](https://github.com/mozzwald/pilrc). Their source trees retain their own copyright and license notices; prc-tools includes GNU GPL components and PilRC includes its upstream license.

The Palm OS SDK collection and Handspring SDK are not redistributed by this repository or its Docker image. They remain subject to the agreements displayed by the installer. The Hello World structure is informed by the public examples in `savaughn/palmdev-macos` and `User7142/palmdev-macos`; this repository contains an independently maintained, minimal sample.
