# Giant Gram 2000 — English Translation

English fan translation project by **Levine91** for Giant Gram 2000 on Dreamcast.

Just an FYI, despite the use of AI, I'm a lifelong pro wrestling fan with extensive knowledge of puroresu as well, so much of this was easy enough to give a proper translation to.
The AI was heavily relied on for automating all the graphics that needed to be ripped and reimplemented.

As far as I can tell, I was able to get everything in the game translated with 2 exceptions:
- There is a number of left over graphics that were clearly from the NAOMI version, so I did not bother with those.
- In Create-A-Wrestler, the English alphabet is present but only a certain amount of letters. This may be fixed in a future update.

Additionally, a couple of minor gameplay changes were implemented.
- Originally, you could never leave the ring unless you knocked your opponent out of the ring or they knocked you out of the ring. It's now possible at any time to press "Y" next to the ropes and you'll go out on your own.
- In VS mode, the Singles and Tag matches would always default to 1P vs. 2P and 1P/1P vs. 2P/2P. I've simply adjusted this so it now defaults to 1P vs. COM and 1P/1P vs. COM/COM. The other options remain intact, they just aren't the first selected now.

Please submit an issue request if you find any mistakes or have any suggestions!

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
