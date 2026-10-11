from pathlib import Path
import json,shutil,hashlib
ROOT=Path(__file__).resolve().parent;GAME=ROOT.parent
backup=ROOT/'before-final-fix';backup.mkdir(exist_ok=True)
for relative in ['1ST_READ.BIN','TEX.AFS','TEX/spr_sel3.bin','TEX/zi.bin']:
 target=backup/relative;target.parent.mkdir(exist_ok=True)
 if not target.exists():shutil.copyfile(GAME/relative,target)
program=(ROOT/'verified-program.bin').read_bytes()
archive=bytearray((GAME/'TEX.AFS').read_bytes())
meta=json.loads((ROOT/'prompt_patch.json').read_text());block=(ROOT/'prompt-fixed.bin').read_bytes()
offset=meta['archive_offset'];archive[offset:offset+len(block)]=block
if (ROOT/'moves-font.bin').exists():
 fm=json.loads((ROOT/'moves-font-meta.json').read_text());font=(ROOT/'moves-font.bin').read_bytes();archive[fm['archive_offset']:fm['archive_offset']+len(font)]=font
if (ROOT/'caw-texture-patches.json').exists():
 for o,f in json.loads((ROOT/'caw-texture-patches.json').read_text()):
  data=(ROOT/f).read_bytes();archive[o:o+len(data)]=data
 for name,o,n in [('spr_cmk2.bin',8312832,866304),('spr_sys.bin',978944,110592)]: (GAME/'TEX'/name).write_bytes(archive[o:o+n])
if (ROOT/'arcade_patch.json').exists():
 m=json.loads((ROOT/'arcade_patch.json').read_text());block=(ROOT/'arcade-fixed.bin').read_bytes();archive[m['archive_offset']:m['archive_offset']+len(block)]=block
if (ROOT/'match-texture-patches.json').exists():
 for o,f in json.loads((ROOT/'match-texture-patches.json').read_text()):
  data=(ROOT/f).read_bytes();archive[o:o+len(data)]=data
 if (ROOT/'intro-texture-patches.json').exists():
  for o,f in json.loads((ROOT/'intro-texture-patches.json').read_text()):
   data=(ROOT/f).read_bytes();archive[o:o+len(data)]=data
 for name,(o,n) in json.loads((ROOT/'game-entries.json').read_text()).items():(GAME/'TEX'/(name+'.bin')).write_bytes(archive[o:o+n])
 (GAME/'TEX/spr_sys.bin').write_bytes(archive[978944:978944+110592])
if (ROOT/'history-texture-patches.json').exists():
 for o,f in json.loads((ROOT/'history-texture-patches.json').read_text()):
  data=(ROOT/f).read_bytes();archive[o:o+len(data)]=data
if (ROOT/'history-ui-texture-patches.json').exists():
 for o,f in json.loads((ROOT/'history-ui-texture-patches.json').read_text()):
  data=(ROOT/f).read_bytes();archive[o:o+len(data)]=data
 for name,o,n in [('spr_sel.bin',2803712,966656),('spr_sel2.bin',3770368,276480)]:
  (GAME/'TEX'/name).write_bytes(archive[o:o+n])
if (ROOT/'history-polish-texture-patches.json').exists():
 for o,f in json.loads((ROOT/'history-polish-texture-patches.json').read_text()):
  data=(ROOT/f).read_bytes();archive[o:o+len(data)]=data
 for name,(o,n) in json.loads((ROOT/'game-entries.json').read_text()).items():
  (GAME/'TEX'/(name+'.bin')).write_bytes(archive[o:o+n])
if (ROOT/'caw-polish-texture-patches.json').exists():
 for o,f in json.loads((ROOT/'caw-polish-texture-patches.json').read_text()):
  data=(ROOT/f).read_bytes();archive[o:o+len(data)]=data
 for name,(o,n) in (json.loads((ROOT/'caw-entries.json').read_text())|json.loads((ROOT/'game-entries.json').read_text())).items():
  (GAME/'TEX'/(name+'.bin')).write_bytes(archive[o:o+n])
if (ROOT/'catchphrase-texture-patches.json').exists():
 for o,f in json.loads((ROOT/'catchphrase-texture-patches.json').read_text()):
  data=(ROOT/f).read_bytes();archive[o:o+len(data)]=data
 for name,(o,n) in json.loads((ROOT/'caw-entries.json').read_text()).items():
  (GAME/'TEX'/(name+'.bin')).write_bytes(archive[o:o+n])
if (ROOT/'history4-texture-patches.json').exists():
 for o,f in json.loads((ROOT/'history4-texture-patches.json').read_text()):
  data=(ROOT/f).read_bytes();archive[o:o+len(data)]=data
 for name,(o,n) in json.loads((ROOT/'game-entries.json').read_text()).items():
  (GAME/'TEX'/(name+'.bin')).write_bytes(archive[o:o+n])
if (ROOT/'results-texture-patches.json').exists():
 for o,f in json.loads((ROOT/'results-texture-patches.json').read_text()):
  data=(ROOT/f).read_bytes();archive[o:o+len(data)]=data
 for name,(o,n) in json.loads((ROOT/'game-entries.json').read_text()).items():
  (GAME/'TEX'/(name+'.bin')).write_bytes(archive[o:o+n])
if (ROOT/'remaining-texture-patches.json').exists():
 for o,f in json.loads((ROOT/'remaining-texture-patches.json').read_text()):
  data=(ROOT/f).read_bytes();archive[o:o+len(data)]=data
 for name,(o,n) in json.loads((ROOT/'game-entries.json').read_text()).items():
  (GAME/'TEX'/(name+'.bin')).write_bytes(archive[o:o+n])
if (ROOT/'venue-texture-patches.json').exists():
 for o,f in json.loads((ROOT/'venue-texture-patches.json').read_text()):
  data=(ROOT/f).read_bytes();archive[o:o+len(data)]=data
if (ROOT/'october-texture-patches.json').exists():
 for o,f in json.loads((ROOT/'october-texture-patches.json').read_text()):
  data=(ROOT/f).read_bytes();archive[o:o+len(data)]=data
 for name,(o,n) in json.loads((ROOT/'game-entries.json').read_text()).items():
  (GAME/'TEX'/(name+'.bin')).write_bytes(archive[o:o+n])
 (GAME/'TEX/spr_sys.bin').write_bytes(archive[978944:978944+110592])
if (ROOT/'interview-texture-patches.json').exists():
 for o,f in json.loads((ROOT/'interview-texture-patches.json').read_text()):
  data=(ROOT/f).read_bytes();archive[o:o+len(data)]=data
 o,n=json.loads((ROOT/'game-entries.json').read_text())['spr_gam3']
 (GAME/'TEX/spr_gam3.bin').write_bytes(archive[o:o+n])
if (ROOT/'credits-texture-patches.json').exists():
 for o,f in json.loads((ROOT/'credits-texture-patches.json').read_text()):
  data=(ROOT/f).read_bytes();archive[o:o+len(data)]=data
 o,n=json.loads((ROOT/'game-entries.json').read_text())['spr_gam3']
 (GAME/'TEX/spr_gam3.bin').write_bytes(archive[o:o+n])
if (ROOT/'alignment-texture-patches.json').exists():
 for o,f in json.loads((ROOT/'alignment-texture-patches.json').read_text()):
  data=(ROOT/f).read_bytes();archive[o:o+len(data)]=data
 o,n=json.loads((ROOT/'caw-entries.json').read_text())['spr_cmk2']
 (GAME/'TEX/spr_cmk2.bin').write_bytes(archive[o:o+n])
for o,f in json.loads((ROOT/'wide-caw-texture-patches.json').read_text()):
 data=(ROOT/f).read_bytes();archive[o:o+len(data)]=data
o,n=json.loads((ROOT/'caw-entries.json').read_text())['spr_cmk2']
(GAME/'TEX/spr_cmk2.bin').write_bytes(archive[o:o+n])
for o,f in json.loads((ROOT/'champion-panels-texture-patches.json').read_text()):
 data=(ROOT/f).read_bytes();archive[o:o+len(data)]=data
o,n=json.loads((ROOT/'game-entries.json').read_text())['spr_gam2']
(GAME/'TEX/spr_gam2.bin').write_bytes(archive[o:o+n])
for o,f in json.loads((ROOT/'tutorial-texture-patches.json').read_text()):
 data=(ROOT/f).read_bytes();archive[o:o+len(data)]=data
(GAME/'TEX/spr_tit5.bin').write_bytes(archive[2582528:2582528+221184])
for o,f in json.loads((ROOT/'tit4-texture-patches.json').read_text()):
 data=(ROOT/f).read_bytes();archive[o:o+len(data)]=data
(GAME/'TEX/spr_tit4.bin').write_bytes(archive[2379776:2379776+202752])
for o,f in json.loads((ROOT/'main-vs-texture-patches.json').read_text()):
 data=(ROOT/f).read_bytes();archive[o:o+len(data)]=data
(GAME/'TEX/spr_tit.bin').write_bytes(archive[1089536:1089536+921600])
for o,f in json.loads((ROOT/'history-weight-credit-texture-patches.json').read_text()):
 data=(ROOT/f).read_bytes();archive[o:o+len(data)]=data
(GAME/'TEX/spr_gam3.bin').write_bytes(archive[6793216:6793216+589824])
model=bytearray((GAME/'MDL.AFS').read_bytes())
for o,f in json.loads((ROOT/'original-model-restores.json').read_text()):
 data=(ROOT/f).read_bytes();model[o:o+len(data)]=data
 (GAME/'MDL'/f.removeprefix('restored-')).write_bytes(data)
(GAME/'MDL.AFS').write_bytes(model)
for o,f in json.loads((ROOT/'tournament-texture-patches.json').read_text()):
 data=(ROOT/f).read_bytes();archive[o:o+len(data)]=data
(GAME/'TEX/spr_gam2.bin').write_bytes(archive[5779456:5779456+1013760])
for o,f in json.loads((ROOT/'vmu-port-texture-patches.json').read_text()):
 data=(ROOT/f).read_bytes();archive[o:o+len(data)]=data
(GAME/'TEX/spr_cmk2.bin').write_bytes(archive[8312832:8312832+866304])
(GAME/'1ST_READ.BIN').write_bytes(program);(GAME/'TEX.AFS').write_bytes(archive)
(GAME/'TEX/spr_sel3.bin').write_bytes(archive[meta['entry']:meta['entry']+meta['length']])
(GAME/'TEX/zi.bin').write_bytes((ROOT/('moves-font.bin' if (ROOT/'moves-font.bin').exists() else 'tested-font.bin')).read_bytes())
out=GAME/'English_Names_Verified'
with (out/'track03.bin').open('rb') as f:
 for extent,expected in [(546682,program),(317680,archive),(167878,model)]:
  f.seek((extent-45000)*2352);raw=f.read(((len(expected)+2047)//2048)*2352)
  actual=b''.join(raw[i+16:i+2064] for i in range(0,len(raw),2352))[:len(expected)]
  assert actual==expected,'Disc and extracted files differ'
manifest={p:hashlib.sha256((GAME/p).read_bytes()).hexdigest() for p in ['1ST_READ.BIN','TEX.AFS','TEX/spr_sel3.bin','TEX/zi.bin']}
(out/'verified-files.json').write_text(json.dumps(manifest,indent=2))
for name in ['final-confirm-clear','verified-tag','verified-tournament','verified-disc-hud']:
 shutil.copyfile(ROOT/(name+'.png'),out/(name+'.png'))
(out/'README.txt').write_text('Open Giant Gram 2000.gdi from this folder in Flycast. Keep all three track files beside it.\nStart the game fresh: an old emulator save state restores old executable code and textures.\n\nNames were visually checked in Champion Carnival, Tag League, One-Night Tournament and the in-match HUD using an off-screen Flycast core. The confirmation prompt was checked from a fresh boot of this GDI.\n\nThe extracted 1ST_READ.BIN, TEX.AFS, TEX/spr_sel3.bin and TEX/zi.bin also match this corrected build. Original project disc tracks were left untouched. Pre-change extracted files are in scripts/before-final-fix.\n')
print('Installed; entire executable and TEX.AFS match the tested disc.')
