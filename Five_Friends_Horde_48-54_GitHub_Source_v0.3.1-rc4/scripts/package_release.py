#!/usr/bin/env python3
"""Create reproducible installer/source ZIPs and SHA-256 checksums (no network)."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

root=Path(__file__).resolve().parents[1]
info=json.loads((root/'pack.json').read_text())
version=info['version']
assert version=='0.3.1-rc4',version
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--out',type=Path,default=root.parent,help='Output folder for ZIPs and checksums')
args=p.parse_args()
args.out.mkdir(parents=True,exist_ok=True)

addon=root/'addon/PolestarPack_FiveFriends4854'
assert addon.is_dir()
assert 'Version: '+version in (addon/'PolestarPack_FiveFriends4854.toc').read_text()

install_name=f'PolestarPack_FiveFriends4854-v{version}-forever.zip'
source_name=f'Five_Friends_Horde_48-54_GitHub_Source_v{version}.zip'
sums_name=f'Five_Friends_48-54_v{version}_SHA256SUMS.txt'

# Same date in all ZIP entries. Flags stable across platforms, ASCII ZIP names.
ZIP_DATE=(2026,11,21,0,0,0)

def zip_paths(name,items):
    path=args.out/name
    with ZipFile(path,'w',ZIP_DEFLATED,compresslevel=9) as arc:
        for src,dest in sorted(items,key=lambda v:v[1]):
            zi=ZipInfo(dest,ZIP_DATE)
            zi.compress_type=ZIP_DEFLATED
            zi.external_attr=(0o100644 << 16)
            arc.writestr(zi,src.read_bytes(),compress_type=ZIP_DEFLATED,compresslevel=9)
        bad=arc.testzip()
        if bad:raise RuntimeError('ZIP CRC failure: '+bad)
    print('CREATED',path,'size',path.stat().st_size)
    return path

installer_items=[(x, 'PolestarPack_FiveFriends4854/'+x.relative_to(addon).as_posix())
                 for x in addon.rglob('*') if x.is_file()]
expected={'PolestarPack_FiveFriends4854/Pack.lua',
          'PolestarPack_FiveFriends4854/MapFrames.lua',
          'PolestarPack_FiveFriends4854/Guides.lua',
          'PolestarPack_FiveFriends4854/PolestarPack_FiveFriends4854.toc'}
assert expected<=set(n for _,n in installer_items)
source_items=[]
for x in root.rglob('*'):
    if not x.is_file():continue
    if '__pycache__' in x.parts or x.name.endswith('.pyc') or '.git' in x.parts:
        continue
    source_items.append((x,x.relative_to(root).as_posix()))
assert len(source_items)>20
inst=zip_paths(install_name,installer_items)
src=zip_paths(source_name,source_items)
lines=[]
for filename in (install_name,source_name):
    v=args.out/filename
    lines.append(hashlib.sha256(v.read_bytes()).hexdigest()+'  '+filename)
(args.out/sums_name).write_text('\n'.join(lines)+'\n')
print('CREATED',args.out/sums_name)
