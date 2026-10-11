"""Default VS to player one versus CPU; preserve all six matchup choices."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
offset = 0x9CEA
original = (ROOT / 'disc-original.bin').read_bytes()
assert original[offset:offset + 2] == bytes.fromhex('01e2')
# VS entry initializes the shared controller-layout selection. Layout 0 means
# 1P vs CPU for Singles and 1P/1P vs CPU/CPU for Tag. Change only mov #1,r2.
patches = [[offset, '00e2']]
(ROOT / 'vs-default-program-patches.json').write_text(json.dumps(patches) + '\n')
print('VS default patch: layout 1 -> layout 0; matchup table unchanged.')
