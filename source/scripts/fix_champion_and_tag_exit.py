"""Keep the champion texture continuous and enable the shared exit path in tags."""
from pathlib import Path
import json,struct,shutil
R=Path(__file__).resolve().parent;G=R.parent
B=R/'before-champion-tag-exit';B.mkdir(exist_ok=True)
if not (B/'1ST_READ.BIN').exists():shutil.copy2(G/'1ST_READ.BIN',B/'1ST_READ.BIN')
b=(B/'1ST_READ.BIN').read_bytes();patches=[];report=[]
def put(at,old,new,reason):
 old=bytes.fromhex(old);new=bytes.fromhex(new)
 assert b[at:at+len(old)]==old,(hex(at),b[at:at+len(old)].hex())
 assert len(old)==len(new)
 patches.append([at,new.hex()]);report.append({'offset':hex(at),'before':old.hex(' '),'after':new.hex(' '),'reason':reason})
# The old Japanese title drew two 88-pixel characters with separated origins.
# Draw the entire existing English texture as adjacent 96-pixel halves instead.
put(0x477e4,'2367','60e7','First CHAMPION half: source width 96 instead of 88')
put(0x477e8,'0ee5','00e5','First half starts at texture x=0 instead of 14')
put(0x4781e,'2367','60e7','Second CHAMPION half: source width 96 instead of 88')
put(0x47822,'69e5','60e5','Second half starts at texture x=96 instead of 105')
put(0x4787a,'dc00','e000','First half finishes its entrance at screen x=224')
put(0x4787c,'9100','9000','Both halves use the full title row starting at texture y=144')
put(0x4787e,'5401','4001','Second half finishes at screen x=320, contiguous with the first')
# Tag/partner handling occurs first and returns when it handles the Y press.
# Otherwise, the old mode==1 guard skipped the shared ring exit handling.
# Fall through to the existing state checks and normal exit action instead.
put(0x77592,'b5a0','0900','Allow Tag Match to reach the shared manual ring-exit path after tag handling')
assert b[0x776f0:0x776f2]==bytes.fromhex('0900'),'Singles opponent-outside bypass must remain installed'
(R/'champion-tag-program-patches.json').write_text(json.dumps(patches))
(R/'champion-tag-change-report.json').write_text(json.dumps(report,indent=2))
p=R/'build_verified.py';s=p.read_text()
if "'champion-tag-program-patches.json'" not in s:
 s=s.replace("'ring-exit-program-patches.json']","'ring-exit-program-patches.json','champion-tag-program-patches.json']")
 p.write_text(s)
print('Prepared seven banner layout edits and one Tag Match branch edit; no textures or models changed.')
