"""Generate the manual ring-exit patch, isolated from the reverted model experiment.

Extracted from finish_gameplay_revision.py for this source release. No model
editing or self-modification of build scripts is retained.
"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
original = (ROOT/'disc-original.bin').read_bytes()
offset = 0x776f0
assert original[offset:offset+2] == bytes.fromhex('0689')
# Bypass only the opponent-outside check on the manual Y-button exit path.
(ROOT/'ring-exit-program-patches.json').write_text(
    json.dumps([[offset, '0900']]) + '\n'
)
print('Prepared manual ring-exit condition patch; no model data modified.')
