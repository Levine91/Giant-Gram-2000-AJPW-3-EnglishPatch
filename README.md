# Giant Gram 2000 — English Translation

English fan translation project by **Levine91** for Giant Gram 2000 on Dreamcast.

This repository contains Python scripts generated with OpenAI Codex during the project, plus development documentation. Levine91 directed and reviewed the translation project; this is not a claim that Levine91 wrote the scripts. The playable patch is distributed separately as the **v1.0** release attachment, **GG2000EnglishV1.dcp**.

## Apply the patch

Use your own compatible game image with [Universal Dreamcast Patcher](https://github.com/DerekPascarella/UniversalDreamcastPatcher). Select your source image, select `GG2000EnglishV1.dcp`, then choose a separate output location and apply the patch. Keep the unmodified source image. The patch's exact accepted source revision has not been independently verified in this repository preparation.

### Source image

Source-image details supplied by the maintainer:

- **File Name:** `Giant Gram 2000 - All Japan Pro Wrestling 3 v1.004 (2000)(Sega)(JP)[!][2MS1].gdi`
- **SHA-1:** `980036E44AD9D694EA1699CD05C86CCD0C894C47`
- **CRC32:** `468C1495`

## Contents

- [Complete script index](docs/SCRIPTS.md): data extraction, graphics/font editing, reinsertion/build, and the specifically requested ring-exit and VS-default scripts.
- [Included gameplay changes](docs/GAMEPLAY.md): manual ring exit and default player assignments.
- [Development notes](docs/DEVELOPMENT.md): prerequisites, workflow, and omitted inputs.
- [Tools and attribution](docs/TOOLS.md) and [third-party licenses](THIRD_PARTY_NOTICES.md).
- [v1.0 release notes](releases/v1.0.md) and [release manifest](releases/v1.0-manifest.json).

The source tree contains no game archives, extracted assets, screenshots, emulator binaries, BIOS, saves, fonts, or patch binaries. The separate DCP release is the maintainer-supplied package, preserved unchanged; it contains both binary deltas and complete embedded game files. See the release manifest for its contents summary.

## Source availability

This is a source archive of the development workflow, **not a self-contained reproducible build**. Scripts also require private game files, prior-stage backups, generated label artwork, and intermediate JSON/binary data that are intentionally excluded. Do not run all scripts in sequence. Some are superseded graphics revisions. Emulator hosts, diagnostics, unrelated gameplay-code scripts and headgear experiments are excluded.

## License

Original project code is available under the MIT license. See [LICENSE](LICENSE). This does not license the game, embedded release assets, third-party software, or proprietary fonts. See [licensing scope](docs/LICENSING.md).

Unofficial fan project; not affiliated with or endorsed by the original game's rights holders.
