import pathlib,zipfile,json
root=pathlib.Path(__file__).resolve().parents[1]
addon=root/'addon'/'PolestarPack_FiveFriends4854'
assert (addon/'PolestarPack_FiveFriends4854.toc').exists()
assert 'five-friends-48-54' in (addon/'Pack.lua').read_text()
assert (addon/'Guides.lua').read_text().count('Polestar.RegisterGuide({')==13
report=json.loads((root/'validation.json').read_text())
assert report['max_steps']<=60 and report['all_links_resolve']
out=root/'dist';out.mkdir(exist_ok=True)
name='PolestarPack_FiveFriends4854-v0.1.0-rc1-forever.zip'
with zipfile.ZipFile(out/name,'w',compression=zipfile.ZIP_DEFLATED) as z:
 for f in sorted(addon.rglob('*')):
  if f.is_file():z.write(f,f.relative_to(root/'addon'))
print(out/name)
