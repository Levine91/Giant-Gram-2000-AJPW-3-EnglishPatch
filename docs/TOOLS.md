# Tools used and attribution

The following tools are evidenced by project scripts or the development session. They are not bundled in the repository.

| Tool | Use |
|---|---|
| Python 3 | Archive analysis, patch generation, build and verification scripts |
| NumPy | Pixel arrays, masks, VQ codebook and binary comparisons |
| Pillow | Label rendering, font handling and texture previews |
| Capstone | SH-4 disassembly and instruction analysis |
| Flycast / libretro | Emulator testing; custom Python host uses its external core |
| GLFW / Python GLFW bindings / PyOpenGL | Hidden OpenGL surface for emulator capture and testing |
| Universal Dreamcast Patcher / xdelta format | Applying the supplied `.dcp` release; package contains `.xdelta` entries. Exact patch-builder version was not recorded |
| Windows PowerShell, ripgrep | Local orchestration and source searches |
| OpenAI Codex and image generation | Assisted scripting, translation work, analysis, and generated label artwork during development. No generated images are included here |
| Git | Preparing the source repository for review |

English translation project credit, direction and review: **Levine91**. The scripts were generated with **OpenAI Codex** during that work, not written by Levine91. Third-party projects retain their authorship and licenses; see [THIRD_PARTY_NOTICES](../THIRD_PARTY_NOTICES.md).

The wider development workflow referenced both `flyinghead/flycast` (including revision `af5f67c`) and `libretro/flycast`. Emulator hosts, source downloader scripts and downloaded upstream C/C++ files are excluded from this focused export. Tools listed here describe project usage, not additional bundled code.
