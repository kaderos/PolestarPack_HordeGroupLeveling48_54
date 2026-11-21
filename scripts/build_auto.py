import json,re,zipfile,shutil,hashlib,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'auto_release' if (ROOT/'Five_Friends_Horde_48-54_Revised_Plan.json').exists() else ROOT
OUT.mkdir(exist_ok=True)
route_file=(ROOT/'Five_Friends_Horde_48-54_Revised_Plan.json') if (ROOT/'Five_Friends_Horde_48-54_Revised_Plan.json').exists() else (ROOT/'evidence/route-ledger.json')
P=json.loads(route_file.read_text())
Q={int(q['id']):q for q in P['quests']}
rc_path=(ROOT/'work/rc48/PolestarPack_FiveFriends4854/Guides.lua') if (ROOT/'work/rc48/PolestarPack_FiveFriends4854/Guides.lua').exists() else (ROOT/'source/rc1-Guides.lua')
rc=rc_path.read_text()
# Parse original RC1 one-line source steps; each is an individually delimited line, not a textual guess.
rx=r'"(?:\\.|[^"\\])*"'
lines=rc.splitlines()
blocks=[];current=[]
for line in lines:
 if 'Polestar.RegisterGuide({' in line:
  if current:blocks.append(current)
  current=[line]
 elif current:current.append(line)
if current:blocks.append(current)
assert len(blocks)==13,len(blocks)
pat=re.compile(r'^\{ title = ('+rx+r')(?:, note = ('+rx+r'))?, goals = (.*) \},?$')

def lua_str(s):
 return json.dumps(str(s),ensure_ascii=False).replace('\\u2028',' ')

def from_lua_str(s):
 if s is None:return ''
 try:return json.loads(s)
 except: return s[1:-1].replace('\\"','"').replace('\\n','\n').replace('\\\\','\\')

def quest_goal(t,qid):
 q=Q.get(qid)
 if q is None: return None
 d={'t':t,'quest':qid,'title':q['name']}
 if t=='accept':
  d['minLevel']=q.get('min_level') or 1;d['qlvl']=q['level']
  location=next((x for x in q.get('locations',[]) if x.get('role')=='start' and len(x.get('xy') or [])==2),None)
 elif t=='turnin':
  d['rewards']={'xp':int(q.get('xp') or 0)}
  location=next((x for x in q.get('locations',[]) if x.get('role')=='end' and len(x.get('xy') or [])==2),None)
 else: location=next((x for x in q.get('locations',[]) if x.get('role') not in ('start','end') and len(x.get('xy') or [])==2),None)
 if location:
  x,y=location['xy']; d['x']=x;d['y']=y
  d['map']={'Shen\'dralas':2652,'Feralas':1444,'Desolace':1443,'Maraudon':280,'Azshara':1447,'Felwood':1448,'The Hinterlands':1425,'Hinterlands':1425,'Tanaris':1446,'Un\'Goro Crater':1449,'Searing Gorge':1427,'Blasted Lands':1419,'Western Plaguelands':1422,'Swamp of Sorrows':1435,'Orgrimmar':1454,'Thunder Bluff':1456,'Mulgore':1412,'Moonglade':1450,'Dustwallow Marsh':1445,'Alcaz Island':1445,'Sunken Temple':109,'Temple of Atal\'Hakkar':109,'Ashenvale':1440}.get(location['zone'])
  if not d['map']:d.pop('map',None);d.pop('x',None);d.pop('y',None)
  # Do not force a vendor/NPC type: newer quest starters can be items and world objects.
  # Polestar can resolve the giver from its quest data when only the quest ID is supplied.
 return d

def lua_dump(v):
 if isinstance(v,bool):return 'true' if v else 'false'
 if v is None:return 'nil'
 if isinstance(v,str):return lua_str(v)
 if isinstance(v,(int,float)):return str(v)
 if isinstance(v,list):return '{'+', '.join(lua_dump(x) for x in v)+'}'
 if isinstance(v,dict):return '{'+', '.join((k if re.match(r'^[A-Za-z_]\w*$',k) else '['+lua_str(k)+']')+' = '+lua_dump(x) for k,x in v.items())+'}'
 raise TypeError(v)

allguides=[]; warnings=[]; stats=[]
for chapter,block in zip(P['chapters'],blocks):
 i=chapter['number'];gid=chapter['guide_id'];qids=set(chapter['quest_ids_in_reward_order'])
 inside=False; raw=[]
 for line in block:
  if 'steps = {' in line:inside=True
  if not inside:continue
  m=pat.match(line.strip())
  if m:
   title=from_lua_str(m[1]);note=from_lua_str(m[2]);raw.append({'title':title,'note':note,'goals':m[3]})
 assert sum(x['title'].startswith('Quest reward:') for x in raw)==len(chapter['quest_ids_in_reward_order']),(i,len(raw),sum(x['title'].startswith('Quest reward:') for x in raw),len(chapter['quest_ids_in_reward_order']))
 registered_accept=set(); reward_done=set(); steps=[]; pending=[]; j=0
 for item in raw:
  title,note=item['title'],item['note']
  if title.startswith('Quest reward:'):
   qid=chapter['quest_ids_in_reward_order'][j];j+=1
   q=Q[qid]
   goals=[]
   # Acceptance is essential for every reward, even if a preceding route section didn't name an explicit pickup.
   if qid not in registered_accept:goals.append(quest_goal('accept',qid)); registered_accept.add(qid)
   # Completion is tracked from quest-log objective status. A few dialogue-only quests have no objectives.
   obj=(q.get('objective') or '').lower().strip()
   if not any(obj.startswith(w) for w in ['speak to ','talk to ','return to ','deliver ','report to ']):goals.append(quest_goal('complete',qid))
   goals.append(quest_goal('turnin',qid)); reward_done.add(qid)
   # stage guidance remains visible on the active quest rather than disappearing via a no-op manual stage.
   note_parts=[x for x in pending[-2:] if x]
   if note and note not in note_parts:note_parts.append(note)
   pending=[]
   joined=' | '.join(note_parts)
   if len(joined)>1800:joined=joined[:1797]+'...'
   step={'title':q['name'],'goals':goals}
   if joined:step['note']=joined
   steps.append(step)
  elif title.startswith('Stage ') or title.startswith('Group readiness'):
   pending.append(note)
   mentioned=[]
   # Accept only quests appearing in this stage whose reward is later in this chapter.
   for qid in sorted(qids,key=lambda x:chapter['quest_ids_in_reward_order'].index(x)):
    if qid not in registered_accept and qid not in reward_done and re.search(r'(?<!\d)'+str(qid)+r'(?!\d)',note):
     if all(pid in reward_done or pid not in qids for pid in Q[qid].get('prereq_ids',[]) if isinstance(pid,int)):
      mentioned.append(qid)
   if mentioned:
    # Pre-accept is a separate step to maintain game detection before clearing the targets.
    step={'title':('Pick up: '+', '.join(Q[x]['name'] for x in mentioned))[:110], 'note':note,'goals':[quest_goal('accept',x) for x in mentioned]}
    steps.append(step)
    registered_accept.update(mentioned)
  else:
   # Optional tips are guidance for the next quest step; no click-to-continue UI.
   if note:pending.append(note)
 assert j==len(qids)
 if pending:
  # Last travel instruction can be displayed alongside final tracked reward.
  if steps:steps[-1]['note']=(steps[-1].get('note','')+' | '+' | '.join(pending[-2:]))[:2100]
 assert len(steps)<=60,(i,len(steps))
 # full native registry metadata + preserved direct integration with the earlier addon version.
 names={'quest:'+str(x):Q[x]['name'] for x in sorted(qids)}
 g={'id':gid,'pack':'five-friends-48-54','title':chapter['display_title'],'faction':'Horde','minLevel':int(chapter['levels_header'].replace('levels ','').split('-')[0]),'maxLevel':int(chapter['levels_header'].replace('levels ','').split('-')[1]),'category':'Leveling','folder':'Five Friends 48-54','keywords':['group','horde','five friends','dungeon'],'why':'Automatic quest pickups, objective completion and rewards. Party members use their own quest log. Route notes are not blocking click-to-complete tasks.','zone':{1:2652,2:280,3:1444,4:1445,5:1425,6:1427,7:1446,8:1449,9:1448,10:1454,11:1422,12:1419,13:109}[i],'next':chapter['next_guide_id'],'author':'Five Friends','version':2,'group':True,'names':names,'steps':steps}
 allguides.append(g)
 stats.append({'chapter':i,'steps':len(steps),'auto_accept_goals':sum(z['t']=='accept' for s in steps for z in s['goals']),'auto_complete_goals':sum(z['t']=='complete' for s in steps for z in s['goals']),'auto_turnin_goals':sum(z['t']=='turnin' for s in steps for z in s['goals']),'manual_tasks':sum(z['t']=='task' for s in steps for z in s['goals'])})

name='PolestarPack_FiveFriends4854';addon=OUT/'addon'/name;addon.mkdir(parents=True,exist_ok=True)
orig=(ROOT/'work/rc48'/name) if (ROOT/'work/rc48'/name).exists() else (ROOT/'source')
if (orig/'MapFrames.lua').resolve() != (addon/'MapFrames.lua').resolve(): shutil.copy2(orig/'MapFrames.lua',addon/'MapFrames.lua')
version='0.2.0-rc2'
(addon/'Pack.lua').write_text('local ADDON = ...\nPolestar.RegisterPack('+lua_dump({'addon':None})+')\n' if False else 'local ADDON = ...\nPolestar.RegisterPack({addon = ADDON, id = "five-friends-48-54", format = 5, title = "Five Friends: Horde 48-54", author = "Five Friends", version = "'+version+'", license = "CC0-1.0", source = "Original coordinated five-player leveling route, November 2026."})\n')
(addon/(name+'.toc')).write_text('## Interface: 16001\n## Title: Polestar Community: Five Friends: Horde 48-54\n## Notes: Auto-tracked quest steps in 13 linked leveling chapters\n## Author: Five Friends\n## Version: '+version+'\n## Category: Polestar\n## Group: Polestar\n## Dependencies: Polestar\n## X-Polestar-Pack: five-friends-48-54\n## X-Polestar-Format: 5\n## X-Polestar-Needs: 0.4.1\n## X-License: CC0-1.0\nPack.lua\nMapFrames.lua\nGuides.lua\n')
(lua:=addon/'Guides.lua').write_text('-- Auto quest-state tracked revision for Horde 48-54.\n'+'\n'.join('do\n local function register()\n  Polestar.RegisterGuide('+lua_dump(g)+')\n end\n if Polestar and Polestar.RegisterGuide then register() end\nend\n' for g in allguides))
(OUT/'compiled-guides.json').write_text(json.dumps(allguides,ensure_ascii=False,indent=2))
(OUT/'validation.json').write_text(json.dumps({'version':version,'stats':stats,'total':{'steps':sum(x['steps'] for x in stats),'accept':sum(x['auto_accept_goals'] for x in stats),'complete':sum(x['auto_complete_goals'] for x in stats),'turnin':sum(x['auto_turnin_goals'] for x in stats),'manual':0},'limit':60,'notes':'Static goal validation. Upstream Forge compiler, native Lua runtime and in-client test not executed.'},indent=2))
(OUT/'README.md').write_text('# Five Friends Horde 48–54 — automatic quest goals\n\nRelease candidate '+version+'. This replaces the manually acknowledged quest steps in v0.1.0-rc1 with Polestar native `accept`, `complete` and `turnin` goals. Route text is attached to the active quest step, not a manual blocking task.\n\nInstall the addon directory in `_forever_/Interface/AddOns/` and restart WoW. Do not install both v0.1.0 and v0.2.0 under distinct folders; overwrite the `PolestarPack_FiveFriends4854` directory.\n\n**Warning:** This is statically validated, not in-game tested. Complex chain transitions may need corrections; report any quest where an accept goal remains blocked after its predecessor is rewarded. Some quests already accepted or completed in previous chapters can be automatically skipped.\n')
(OUT/'CHANGELOG.md').write_text('# Changelog\n\n## '+version+'\n- Replaced manual task checkpoints with quest-state goals for accept, objective completion and reward.\n- Moved narrative guidance into active tracked steps.\n- Preserved thirteen-chapter route and eight prerequisite/dungeon constraints from the route ledger.\n- Retained 40-quest-log-slot management from the plan.\n')
(OUT/'evidence').mkdir(exist_ok=True)
if route_file.resolve() != (OUT/'evidence'/'route-ledger.json').resolve():shutil.copy2(route_file,OUT/'evidence'/'route-ledger.json')
(OUT/'scripts').mkdir(exist_ok=True)
if Path(__file__).resolve() != (OUT/'scripts'/'build_auto.py').resolve():shutil.copy2(__file__,OUT/'scripts'/'build_auto.py')
(OUT/'source').mkdir(exist_ok=True)
if rc_path.resolve() != (OUT/'source/rc1-Guides.lua').resolve():shutil.copy2(rc_path,OUT/'source/rc1-Guides.lua')
if (orig/'MapFrames.lua').resolve() != (OUT/'source/MapFrames.lua').resolve():shutil.copy2(orig/'MapFrames.lua',OUT/'source/MapFrames.lua')
(OUT/'.github/workflows').mkdir(parents=True,exist_ok=True)
(OUT/'.github/workflows/release.yml').write_text('name: Release addon\non:\n  push:\n    tags:\n      - "v*"\npermissions:\n  contents: write\njobs:\n  release:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - name: Package addon\n        run: |\n          mkdir -p dist\n          cd addon\n          zip -r ../dist/PolestarPack_FiveFriends4854-${GITHUB_REF_NAME}-forever.zip PolestarPack_FiveFriends4854\n      - uses: softprops/action-gh-release@v2\n        with:\n          prerelease: true\n          files: dist/*.zip\n')
(OUT/'pack.json').write_text(json.dumps({'id':'five-friends-48-54','folder':name,'version':version,'guides':len(allguides)},indent=2))
dist=OUT/'dist';dist.mkdir(exist_ok=True)
install=dist/(name+'-v'+version+'-forever.zip')
with zipfile.ZipFile(install,'w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(addon.rglob('*')):
  if f.is_file():z.write(f,f.relative_to(addon.parent).as_posix())
repo=dist/('Five_Friends_Horde_48-54_GitHub_Source_v'+version+'.zip')
with zipfile.ZipFile(repo,'w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(OUT.rglob('*')):
  if f.is_file() and 'dist' not in f.relative_to(OUT).parts:z.write(f,f.relative_to(OUT).as_posix())
print('STATS',json.dumps(stats));print('INSTALL',install,install.stat().st_size);print('REPO',repo,repo.stat().st_size)
