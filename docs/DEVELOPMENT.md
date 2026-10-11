# Development

## Environment

Python 3, NumPy and Pillow are used for archive analysis and texture edits. Capstone, GLFW, PyOpenGL and Flycast were used elsewhere in development, but those diagnostics/emulator scripts are excluded from this curated export. Windows font paths in historical scripts refer to locally installed fonts such as Arial, Arial Bold/Italic, Impact and Consolas. No font files are included.

`requirements.txt` lists the NumPy and Pillow dependencies used by the included scripts. These are dependency names, not a tested lockfile or claim that every historical script works against every version.

## Private workspace layout

All Python files live in `source/scripts/`. For patch development, copy that single `scripts/` folder into a disposable private extracted-game workspace, beside `1ST_READ.BIN` and `TEX.AFS`. The texture helper and name-spacing editor use its parent as the game root. Later patch scripts keep their private intermediate files alongside the scripts. Copy the required historical intermediate data from your private working folder into this private `scripts/` directory before using those stages; it is not supplied in Git. Local module imports now resolve within this one folder. The repository validator is the exception: run it from the repository, not the game workspace.

Do not execute the historical scripts inside a public checkout: they create game-derived output. Inspect each script's inputs and output paths first. Some files execute work immediately when imported. Graphics scripts that also update text pointers or on-screen positions are included intact because those changes are part of reinserting the edited graphics. Earlier patch stages and their private intermediate data must exist before the later stages can run. Hard-coded personal preview paths were replaced with `private_previews/`; one missing generated-art input now points to `private_inputs/venue-labels-input.png`.

## Workflow represented by the source

1. Decode AFS entries and 256Ã—256 VQ texture blocks; inspect text and program references.
2. Produce translated labels, runtime glyph pairs, and byte patches; retain untouched pixels/bytes where asserted.
3. Apply successive per-feature manifests in `source/scripts/build_verified.py`, update disc sectors, and regenerate/check sector checksums.
4. Use `source/scripts/install_verified.py` to synchronize the private extracted files and compare them with the rebuilt disc.
5. Use targeted visual/emulator checks as needed. User hardware testing is separate.

The named JSON manifests, generated labels, texture blocks, original disc, executable, archives, and save states required by those steps are deliberately not shipped here. The repository alone cannot reproduce the supplied DCP. No automated rebuild claim is made.

The failed Kongo headgear experiments, emulator hosts and unrelated gameplay-code patch generators are excluded. Ring-exit and VS-default generators are included as explicitly requested; see GAMEPLAY.md. The build scripts still reference private manifests for the completed release; these manifests are not part of this source-only export.

## Repository-only validation

Run `python source/scripts/validate_repository.py`. It parses source without importing it, enforces the source-only file types, checks the export manifest, and scans for local user paths, credential-shaped strings and large embedded binary strings. It does not run the game or execute patch scripts.

The local preparation checks are source syntax/content checks. They are not a new emulator or real-hardware certification, and the supplied DCP has not been reapplied during preparation.
