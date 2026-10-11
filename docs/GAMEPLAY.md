# Included gameplay changes

These are the gameplay changes specifically selected for this source export. Offsets are byte offsets in the project's original `1ST_READ.BIN`, not universal addresses for every revision. The generators check expected bytes before producing patch manifests.

| Change | Script | Original â†’ replacement |
|---|---|---|
| Manual ring exit without the opponent already outside | `source/scripts/fix_manual_ring_exit.py` | At `0x776F0`: `06 89` â†’ `09 00` |
| Tag matches can reach the existing manual exit path after tag/partner handling | `source/scripts/fix_champion_and_tag_exit.py` | At `0x77592`: `B5 A0` â†’ `09 00` |
| VS menu defaults to layout 0: Singles 1P vs COM, Tag 1P/1P vs COM/COM | `source/scripts/fix_vs_defaults.py` | At `0x9CEA`: `01 E2` â†’ `00 E2` |

The ring-exit changes keep the existing input and remaining state checks. The VS change changes the initial selection, not the available matchup choices.

The singles exit generator was isolated from the earlier `finish_gameplay_revision.py`, which also contained the abandoned headgear experiment. The exported script retains only the ring-exit manifest generation. No headgear/model edits are included.

The tag-exit script also contains the seven CHAMPION banner layout corrections originally made in the same script. Those graphics-related changes are retained. It expects the singles exit patch to be present in its private backup input.

These generators are consumed by the historical build workflow. They were not executed against or used to rewrite the supplied DCP during repository preparation.
