# Included scripts

All Python scripts are under `source/scripts/`. Project scripts cover extraction, graphics/font editing, reinsertion/build, and the requested ring-exit and VS defaults. The separate repository validator checks the export without executing game-editing scripts.

`export_crusher_moveset.py` and `export_portraits.py` were removed: their report/gallery output is not consumed by the included reinsertion scripts. `extract_main_menu.py` remains because its decoder and texture-layout helpers are imported by the graphics patchers.

Read [Development](DEVELOPMENT.md) before executing historical scripts.

| File | Role | Category |
|---|---|---|
| [source/scripts/build_verified.py](../source/scripts/build_verified.py) | Build a separate GDI; preserve originals and verify Mode 1 checksums. | Reinsertion/build |
| [source/scripts/center_main_vs.py](../source/scripts/center_main_vs.py) | Optically center VS by shifting its existing artwork two pixels left. | Graphics/font editing and reinsertion |
| [source/scripts/clean_controller_labels.py](../source/scripts/clean_controller_labels.py) | Remove original Japanese glyph overhangs above all 36 controller labels. | Graphics/font editing and reinsertion |
| [source/scripts/correct_run.py](../source/scripts/correct_run.py) | Correct only the six Move labels in the existing options and pause patches. | Graphics/font editing and reinsertion |
| [source/scripts/extract_main_menu.py](../source/scripts/extract_main_menu.py) | Extract main menu | Data extraction |
| [source/scripts/fix_all_history_names.py](../source/scripts/fix_all_history_names.py) | Roll out approved History Mode lettering; no additional emulator tests. | Graphics/font editing and reinsertion |
| [source/scripts/fix_all_intro_names.py](../source/scripts/fix_all_intro_names.py) | Apply the approved introduction lettering without any further emulator runs. | Graphics/font editing and reinsertion |
| [source/scripts/fix_arcade.py](../source/scripts/fix_arcade.py) | Render the prompt across its two actual atlas interiors, excluding the frame. | Graphics/font editing and reinsertion |
| [source/scripts/fix_arcade_tag.py](../source/scripts/fix_arcade_tag.py) | Render the prompt across its two actual atlas interiors, excluding the frame. | Graphics/font editing and reinsertion |
| [source/scripts/fix_catchphrase_update.py](../source/scripts/fix_catchphrase_update.py) | Translate the complete CAW word bank and History Match 2; align Weight. | Graphics/font editing and reinsertion |
| [source/scripts/fix_caw_alignment.py](../source/scripts/fix_caw_alignment.py) | Fix caw alignment | Graphics/font editing and reinsertion |
| [source/scripts/fix_caw_polish.py](../source/scripts/fix_caw_polish.py) | Fix caw polish | Graphics/font editing and reinsertion |
| [source/scripts/fix_caw_requests.py](../source/scripts/fix_caw_requests.py) | Fix caw requests | Graphics/font editing and reinsertion |
| [source/scripts/fix_champion_and_tag_exit.py](../source/scripts/fix_champion_and_tag_exit.py) | Keep the champion texture continuous and enable the shared exit path in tags. | Requested ring-exit / VS-default gameplay change |
| [source/scripts/fix_credit_translations.py](../source/scripts/fix_credit_translations.py) | Translate the three remaining Japanese credit cards across their tile seams. | Graphics/font editing and reinsertion |
| [source/scripts/fix_history_13_24.py](../source/scripts/fix_history_13_24.py) | Translate the twelve alternate-perspective Historic Match descriptions. | Graphics/font editing and reinsertion |
| [source/scripts/fix_history_match3.py](../source/scripts/fix_history_match3.py) | Install the third History Mode passage in its original text slot. | Graphics/font editing and reinsertion |
| [source/scripts/fix_history_match4.py](../source/scripts/fix_history_match4.py) | Use a reusable History alphabet and align the History pause choices. | Graphics/font editing and reinsertion |
| [source/scripts/fix_history_polish.py](../source/scripts/fix_history_polish.py) | Fix history polish | Graphics/font editing and reinsertion |
| [source/scripts/fix_history_remaining.py](../source/scripts/fix_history_remaining.py) | Translate History matches 5-12 with the established single-letter font. | Graphics/font editing and reinsertion |
| [source/scripts/fix_history_results.py](../source/scripts/fix_history_results.py) | Translate the pin objective and repair complete result-label strips. | Graphics/font editing and reinsertion |
| [source/scripts/fix_history_sample.py](../source/scripts/fix_history_sample.py) | Fix history sample | Graphics/font editing and reinsertion |
| [source/scripts/fix_history_story.py](../source/scripts/fix_history_story.py) | Install the user-approved first History Mode passage in its original text slot. | Graphics/font editing and reinsertion |
| [source/scripts/fix_history_ui.py](../source/scripts/fix_history_ui.py) | Fix history ui | Graphics/font editing and reinsertion |
| [source/scripts/fix_history_weight_credit.py](../source/scripts/fix_history_weight_credit.py) | Match the shared history-button lettering to its digits; add translation credit. | Graphics/font editing and reinsertion |
| [source/scripts/fix_interview_names.py](../source/scripts/fix_interview_names.py) | Translate the remaining two interview name atlases; preserve translated labels. | Graphics/font editing and reinsertion |
| [source/scripts/fix_intro_sample.py](../source/scripts/fix_intro_sample.py) | Two-name approval sample only: one continuous strip per introduction name. | Graphics/font editing and reinsertion |
| [source/scripts/fix_main_spacing.py](../source/scripts/fix_main_spacing.py) | Restore the exact prior menu rows; replace only History and CAW lettering. | Graphics/font editing and reinsertion |
| [source/scripts/fix_manual_ring_exit.py](../source/scripts/fix_manual_ring_exit.py) | Generate the manual ring-exit patch, isolated from the reverted model experiment. | Requested ring-exit / VS-default gameplay change |
| [source/scripts/fix_match_messages.py](../source/scripts/fix_match_messages.py) | Translate shared match sprites while preserving adjacent art and atlas geometry. | Graphics/font editing and reinsertion |
| [source/scripts/fix_missed_moves.py](../source/scripts/fix_missed_moves.py) | Fill missed move tables by reusing the game's existing translated strings. | Graphics/font editing and reinsertion |
| [source/scripts/fix_moves.py](../source/scripts/fix_moves.py) | Fix moves | Graphics/font editing and reinsertion |
| [source/scripts/fix_name_spacing.py](../source/scripts/fix_name_spacing.py) | Fix name spacing | Graphics/font editing and reinsertion |
| [source/scripts/fix_october_labels.py](../source/scripts/fix_october_labels.py) | Translate the requested injury, result, system and Honda interview labels. | Graphics/font editing and reinsertion |
| [source/scripts/fix_options_layout.py](../source/scripts/fix_options_layout.py) | Repair options typography and missing setting labels on the cumulative archive. | Graphics/font editing and reinsertion |
| [source/scripts/fix_prompt.py](../source/scripts/fix_prompt.py) | Render the prompt across its two actual atlas interiors, excluding the frame. | Graphics/font editing and reinsertion |
| [source/scripts/fix_remaining_ui.py](../source/scripts/fix_remaining_ui.py) | Remaining tournament labels and command prefixes; isolate the ring prompt sprite. | Graphics/font editing and reinsertion |
| [source/scripts/fix_rules_lettering.py](../source/scripts/fix_rules_lettering.py) | Restore rule brackets and the original warm gradient, gold rim and shadow. | Graphics/font editing and reinsertion |
| [source/scripts/fix_tournament_alignment.py](../source/scripts/fix_tournament_alignment.py) | Align tournament names and the two split-atlas confirmation prompts. | Graphics/font editing and reinsertion |
| [source/scripts/fix_venue_cards.py](../source/scripts/fix_venue_cards.py) | Fit generated English headings into the three existing venue-card textures. | Graphics/font editing and reinsertion |
| [source/scripts/fix_vmu_port.py](../source/scripts/fix_vmu_port.py) | Fix vmu port | Graphics/font editing and reinsertion |
| [source/scripts/fix_vs_defaults.py](../source/scripts/fix_vs_defaults.py) | Default VS to player one versus CPU; preserve all six matchup choices. | Requested ring-exit / VS-default gameplay change |
| [source/scripts/install_verified.py](../source/scripts/install_verified.py) | Install verified | Reinsertion/build |
| [source/scripts/patch_backup_confirm.py](../source/scripts/patch_backup_confirm.py) | Patch backup confirm | Graphics/font editing and reinsertion |
| [source/scripts/patch_caw.py](../source/scripts/patch_caw.py) | Translate CAW texture labels, retaining earlier patches and untouched pixels. | Graphics/font editing and reinsertion |
| [source/scripts/patch_english_menu.py](../source/scripts/patch_english_menu.py) | Pack generated English labels into the existing Dreamcast VQ texture. | Graphics/font editing and reinsertion |
| [source/scripts/patch_expanded.py](../source/scripts/patch_expanded.py) | Pause, tournament, Backup/loading localization plus runtime wrestler names. | Graphics/font editing and reinsertion |
| [source/scripts/patch_options.py](../source/scripts/patch_options.py) | Pack options translations into the existing textures; keep the main-menu patch. | Graphics/font editing and reinsertion |
| [source/scripts/patch_pause.py](../source/scripts/patch_pause.py) | Translate pause textures on top of English_Options; requires NumPy/Pillow. | Graphics/font editing and reinsertion |
| [source/scripts/patch_vs.py](../source/scripts/patch_vs.py) | Translate VS selection textures without changing earlier menu patches. | Graphics/font editing and reinsertion |
| [source/scripts/patch_wrestler_names.py](../source/scripts/patch_wrestler_names.py) | Localize selection-screen name rows, preserving the cumulative VS patch. | Graphics/font editing and reinsertion |
| [source/scripts/polish_menus.py](../source/scripts/polish_menus.py) | Consistent cap heights, centered pause labels, and outlined VS descriptions. | Graphics/font editing and reinsertion |
| [source/scripts/rename_difficulty.py](../source/scripts/rename_difficulty.py) | Replace only the options Level label in the corrected cumulative archive. | Graphics/font editing and reinsertion |
| [source/scripts/restore_main_style.py](../source/scripts/restore_main_style.py) | Restore the original English artwork and case; normalize its letter size. | Graphics/font editing and reinsertion |
| [source/scripts/runtime_localize.py](../source/scripts/runtime_localize.py) | Localize existing two-byte text using unused font cells, without code hooks. | Graphics/font editing and reinsertion |
| [source/scripts/translate_all_interviews.py](../source/scripts/translate_all_interviews.py) | Replace the complete interview bank without changing its selectors or unrelated text. | Graphics/font editing and reinsertion |
| [source/scripts/translate_champion_panels.py](../source/scripts/translate_champion_panels.py) | Localize championship atlas cells using the existing game texture pipeline. | Graphics/font editing and reinsertion |
| [source/scripts/translate_how_to_play.py](../source/scripts/translate_how_to_play.py) | Translate the six requested tutorial tiles; preserve the 512-pixel strip packing. | Graphics/font editing and reinsertion |
| [source/scripts/translate_tit4_panels.py](../source/scripts/translate_tit4_panels.py) | Localize the six ranking/VM tutorial tiles without changing their sprite layout. | Graphics/font editing and reinsertion |
| [source/scripts/widen_caw_labels.py](../source/scripts/widen_caw_labels.py) | Widen caw labels | Graphics/font editing and reinsertion |
| [source/scripts/validate_repository.py](../source/scripts/validate_repository.py) | Source-only repository checks | Repository maintenance |
