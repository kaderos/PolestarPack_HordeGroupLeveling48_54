#!/usr/bin/env python3
"""Author a navigable 48-54 Polestar pack from researched sources.

Sources: prior 43-48 authored guide DSL; previous 49-54 compiled navigation
payloads; revised 48-54 reward ledger. All source locations are preserved or
explicitly described. No fabricated indoor dungeon coordinates are added.
"""
import collections, copy, hashlib, json, re, shutil, subprocess, zipfile
from pathlib import Path

DEST=Path(__file__).resolve().parents[1]
ROOT=DEST/'inputs'
MODEL=json.loads((DEST/'evidence/route-ledger.json').read_text())
Q={q['id']:q for q in MODEL['quests']}
REF=ROOT/'ref49/reference'
QDB=json.loads((REF/'quests.json').read_text())
NDB=json.loads((REF/'npcs.json').read_text())
IDB=json.loads((REF/'items.json').read_text())
REFSRC=json.loads((ROOT/'ref49/build/compiled-payloads.json').read_text())
R49={p['guide']['id'].split('/')[-1]:p['guide'] for p in REFSRC}
MAPS={"Shen'dralas":2652, 'Feralas':1444,'Desolace':1443,'Maraudon':280,'Azshara':1447,'Felwood':1448,'The Hinterlands':1425,'Hinterlands':1425,'Tanaris':1446,"Un'Goro Crater":1449,'Searing Gorge':1427,'Blasted Lands':1419,'Western Plaguelands':1422,'Swamp of Sorrows':1435,'Orgrimmar':1454,'Thunder Bluff':1456,'Mulgore':1412,'Moonglade':1450,'Dustwallow Marsh':1445,'Alcaz Island':1445,'Sunken Temple':109,"Temple of Atal'Hakkar":109,'Ashenvale':1440,'Winterspring':1452,'Undercity':1458,'The Barrens':1413,'Westfall':1436,'Eastern Plaguelands':1423,'The Hinterlands':1425}
NAME='PolestarPack_FiveFriends4854'; PID='five-friends-48-54'; VERSION='0.3.1-rc4'
MANA_MAP=2652

def src_old(filename):
    steps=[]; cur=None; map_id=None
    for raw in (ROOT/'prev/guides'/filename).read_text().splitlines():
        line=raw.strip()
        if not line or line.startswith('#') or line.startswith('--'):continue
        m=re.match(r'^zone map\s+(\d+)',line)
        if m:map_id=int(m.group(1));continue
        if line.startswith('step '):
            if cur:steps.append(cur)
            cur={'title':line[5:].strip(),'note_parts':[], 'goals':[], '_source':f'43-48/{filename}'};continue
        if cur is None:continue
        if line.startswith('tip ') or line.startswith('note '):
            v=line.split(' ',1)[1].strip();
            if v.startswith('"') and v.endswith('"'):v=v[1:-1]
            cur['note_parts'].append(v); continue
        if line.startswith('task '):
            cur['note_parts'].append('CHECK: '+line[5:].strip().strip('"'));continue
        if line.startswith('zone map '):
            map_id=int(line.split()[-1]);continue
        m=re.match(r'^(accept|complete|turnin|collect|kill|use|interact|goto|enter|level)\s*(.*)',line)
        if not m:continue
        t,body=m.groups()
        if t=='level':continue
        if t=='enter':
            cur['goals'].append({'t':'enter','zone':body.strip().strip('"')});continue
        if t=='goto':
            coord=re.match(r'(\d+(?:\.\d+)?),(\d+(?:\.\d+)?)',body)
            if coord:cur['goals'].append({'t':'goto','map':map_id,'x':float(coord.group(1)),'y':float(coord.group(2)),'text':'Travel via this waypoint'});
            continue
        val=re.match(r'^(\d+)',body)
        if not val:continue
        ident=int(val.group(1));qmeta=Q.get(ident,{});gol={'t':t}
        if t in ('accept','complete','turnin'):
            gol.update({'quest':ident,'title':qmeta.get('name',str(ident))})
            if t=='accept':gol.update({'minLevel':qmeta.get('min_level',1),'qlvl':qmeta.get('level',0)})
            if t=='turnin':gol['rewards']={'xp':qmeta.get('xp',0)}
        elif t=='collect':
            qq=re.search(r'\bquest\s+(\d+)(?:\.(\d+))?',body)
            if qq:
                gol.update({'quest':int(qq.group(1)),'oi':int(qq.group(2)) if qq.group(2) else 1,'title':Q.get(int(qq.group(1)),{}).get('name','')})
            gol.update({'item':ident,'itemName':IDB.get(str(ident),{}).get('name',f'Item {ident}')})
            ct=re.search(r'\bx(\d+)',body);gol['count']=int(ct.group(1)) if ct else 1
        elif t=='kill':
            qq=re.search(r'\bquest\s+(\d+)(?:\.(\d+))?',body)
            if qq:gol.update({'quest':int(qq.group(1)),'oi':int(qq.group(2)) if qq.group(2) else 1,'title':Q.get(int(qq.group(1)),{}).get('name','')})
            gol.update({'npc':ident,'target':NDB.get(str(ident),{}).get('name',f'NPC {ident}')})
            ct=re.search(r'\bx(\d+)',body);gol['count']=int(ct.group(1)) if ct else 1
        else:continue
        xy=re.search(r'@(\d+(?:\.\d+)?),(\d+(?:\.\d+)?)',body)
        mp=re.search(r'\bmap\s+(\d+)',body)
        if xy:
            gol.update({'map':int(mp.group(1)) if mp else map_id,'x':float(xy.group(1)),'y':float(xy.group(2))})
        if ' group 5' in body:gol['group']={'kind':'group','size':5}
        cur['goals'].append(gol)
    if cur:steps.append(cur)
    return steps

OLD={p.stem:src_old(p.name) for p in (ROOT/'prev/guides').glob('*.guide')}
# Cached best research goals; reliable quest-giver/turn-in coordinates, plus objective areas.
SOURCEMETA=collections.defaultdict(lambda:collections.defaultdict(list))
for c in list(R49.values()):
    for si,s in enumerate(c['steps']):
        for goal in s['goals']:
            if goal.get('quest') and goal.get('t') in ('accept','complete','turnin','kill','collect','interact','use','talk'):
                SOURCEMETA[goal['quest']][goal['t']].append(copy.deepcopy(goal))
for c in list(OLD.values()):
    for si,s in enumerate(c):
        for goal in s['goals']:
            if goal.get('quest') and goal.get('t') in ('accept','complete','turnin','kill','collect','interact','use','talk'):
                SOURCEMETA[goal['quest']][goal['t']].append(copy.deepcopy(goal))

# Reconciled known locations omitted from the published 48-54 ledger. Coordinates are
# from prior .guide sources and source-specific research, never inferred from unrelated NPCs.
KNOWN={
 (3380,'accept'):(1444,74.4,43.4),(3380,'turnin'):(1446,52.7,45.9),
 (4120,'accept'):(1444,76.2,43.8),(4120,'complete'):(1448,58.0,18.0),(4120,'turnin'):(1444,76.2,43.8),
 (3063,'accept'):(1444,76.2,43.8),(3063,'complete'):(1444,38.2,14.5),(3063,'turnin'):(1444,76.2,43.8),
 (97378,'accept'):(1456,61.5,80.9),(97378,'complete'):(1444,48.0,46.0),(97378,'turnin'):(1456,61.5,80.9),
 (96776,'accept'):(1412,32.6,24.0),(96776,'turnin'):(1412,32.6,24.0),
 (93362,'accept'):(2652,53.2,75.8),(93362,'complete'):(2652,70,80),(93362,'turnin'):(2652,53.2,75.8),
 (98203,'accept'):(1425,78.0,77.8),(98203,'complete'):(1425,26,65),(98203,'turnin'):(1425,78.0,77.8),
 (96376,'turnin'):(1454,31.8,37.8), # Nazgrel/Orgrimmar delivery: route note, verify in game
 (4492,'accept'):(1449,43.62,8.50),(4492,'complete'):(1449,51.90,49.85),(4492,'turnin'):(1449,51.90,49.85),
 (7066,'turnin'):(1450,36.2,41.8),
 (93404,'complete'):(2652,69.5,71.9),(93404,'turnin'):(2652,69.5,71.9),
 (1446,'accept'):(1425,33.8,75.2),(1446,'turnin'):(1425,33.8,75.2),
 (4787,'accept'):(1446,67.0,22.4),(4787,'turnin'):(1446,67.0,22.4),
 (3446,'accept'):(1446,52.7,45.9),(3447,'accept'):(1446,52.7,45.9),
 (91548,'accept'):(1454,48.5,45.4),(91548,'turnin'):(1454,48.5,45.4),
 (4987,'turnin'):(1456,75.8,31.8),
 (96376,'accept'):(1436,43.4,67.8),
 (95483,'turnin'):(1454,31.7,37.8),
 (650,'accept'):(1454,59.6,36.9),
 (93594,'turnin'):(2652,69.4,71.8),
 (5158,'turnin'):(1413,65.8,43.8),
}
# Additional objective areas recovered from authored map pins, game-quest
# location databases, and the 2026-11-21 Forever quest references. A location
# is a search/objective pin; it is not automatically a quest NPC pickup.
KNOWN.update({
 (93016,'complete'):(2652,35.0,46.7),
 (99257,'complete'):(2652,46.0,78.2),
 (99258,'complete'):(2652,42.5,59.7), # rift search hint only
 (3517,'complete'):(1447,38.0,54.0), # Eldarath ruins search
 (91568,'complete'):(1447,47.0,54.0), # beach fragments, Questie cluster
 (86746,'complete'):(1447,57.2,21.3),
 (3601,'complete'):(1447,59.5,31.3), # Legashi/Sin'dorei camp search
 (91500,'complete'):(1447,60.0,31.0),
 (91538,'complete'):(1447,22.56,51.42),
 (3561,'complete'):(1447,29.25,40.54),
 (3565,'complete'):(1447,22.56,51.42),
 (91531,'complete'):(1454,75.5,34.3),
 (3541,'complete'):(1454,55.53,33.86),
 (91547,'complete'):(1454,48.47,45.42),
 (95283,'complete'):(1445,35.2,30.7),
 (95284,'complete'):(1445,70.3,18.9),
 (95285,'complete'):(1445,70.3,18.9),
 (96337,'complete'):(1436,43.4,67.8),
 (3542,'complete'):(1458,54.1,74.1),
 (3380,'complete'):(1446,52.7,45.9),
 (5158,'complete'):(1413,65.8,43.8),
 (7815,'complete'):(1425,81.0,61.0), # east-coast snapjaw search
 (7816,'complete'):(1425,81.0,59.0), # Gammerita coastline search
 (7828,'complete'):(1425,50.0,40.0),
 (7829,'complete'):(1425,46.0,43.0),
 (7830,'complete'):(1425,51.0,42.0),
 (7844,'complete'):(1425,64.0,73.0),
 (7839,'complete'):(1425,62.0,71.0),
 (7846,'complete'):(1425,59.6,77.9), # Hitah'ya search / elder terrace
 (7850,'complete'):(1425,60.0,78.0),
 (7849,'complete'):(1425,59.6,77.9),
 (7861,'complete'):(1425,60.0,78.0),
 (7862,'complete'):(1425,60.0,78.0),
 (4787,'complete'):(1425,57.5,86.8), # Ancient Egg upper cave
 (3442,'complete'):(1427,41.0,57.0),
 (3443,'complete'):(1427,48.0,56.0),
 (4449,'complete'):(1427,54.0,58.0),
 (7729,'complete'):(1427,48.0,55.0),
 (7727,'complete'):(1427,46.0,63.0),
 (7701,'complete'):(1427,44.0,57.0),
 (7722,'complete'):(1427,44.0,57.0),
 (3452,'complete'):(1427,40.0,52.0),
 (7723,'complete'):(1427,46.0,56.0),
 (7724,'complete'):(1427,48.0,58.0),
 (3518,'complete'):(1456,75.8,31.8),
 (2965,'complete'):(1456,75.8,31.8),
 (3444,'complete'):(1413,62.5,38.5), # Ratchet chest
 (2966,'complete'):(1446,37.63,81.4), # Uldum pedestal
 (4290,'complete'):(1449,68.6,57.3),
 (87492,'complete'):(1449,66.3,75.2),
 (4291,'complete'):(1449,66.8,73.1),
 (4292,'complete'):(1449,79.5,49.9),
 (3844,'complete'):(1449,63.1,69.1),
 (3845,'complete'):(1449,44.66,8.1),
 (4284,'complete'):(1449,41.9,7.3), # Collie review; crystals are along-route
 (4289,'complete'):(1449,67.0,15.0), # Fungal Rock entrance
 (3883,'complete'):(1449,48.6,85.2),
 (3881,'complete'):(1449,38.5,66.0), # western crate last
 (4301,'complete'):(1449,68.5,12.6),
 (4321,'complete'):(1449,41.9,7.3),
 (5165,'complete'):(1448,36.0,56.0), # braziers in Shadow Hold
 (91548,'complete'):(1419,39.5,33.0), # Altar of Storms, quest NPC spawn
})
# These objectives consist of actual terrain stops; include all stops to force
# the navigation trail to move before requiring quest-log objective completion.
MULTISTOP={
 92914:[(2652,43.7,34.4,'Western pylon'),(2652,73.5,23.0,'Eastern pylon'),(2652,47.4,77.7,'Temple pylon')],
 96010:[(1443,67.9,78.9,'Magram pylon fragment'),(1443,36.2,85.9,'Gelkis pylon shard')],
 96018:[(2652,46.1,78.1,'Take Mana Sieve'),(2652,43.5,34.2,'Repair western pylon'),(2652,73.0,23.3,'Repair eastern pylon')],
 3463:[(1427,33.3,54.5,'Tower 1'),(1427,35.7,60.7,'Tower 2'),(1427,44.0,60.9,'Tower 3'),(1427,50.1,54.8,'Tower 4')],
 4285:[(1449,56.5,12.5,'Northern pylon')],
 4287:[(1449,77.2,50.0,'Eastern pylon')],
 4288:[(1449,23.9,59.2,'Western pylon')],
 4120:[(1448,58.0,18.0,'Angerclaw / Felpaw wildlife')],
 93362:[(2652,70.0,80.0,'Garden flowers')],
 98203:[(1425,26.0,65.0,'Witch Doctor Ti’ik cave area')],
}

MULTISTOP.update({
 91497:[(1447,56.5,26.8,'Hawkhelm seal'),(1447,66.0,29.0,'Suncrest seal'),(1447,69.0,30.0,'Lydrea patrol seal')],
 4290:[(1449,68.6,57.3,'Lar\'korwi carcass')],
 4291:[(1449,66.8,73.1,'Lar\'korwi nest 1'),(1449,66.5,67.1,'Lar\'korwi nest 2')],
 3442:[(1427,41,57,'Heart of Flame source'),(1427,46,56,'Golem Oil source')],
 5165:[(1448,36,56,'Brazier of Pain'),(1448,38,53,'Brazier of Malice'),(1448,37,53,'Brazier of Suffering'),(1448,36,55,'Brazier of Hatred')],
 3517:[(1447,36,53,'Eldarath west tablet search'),(1447,41,54,'Eldarath east tablet search')],
 3881:[(1449,67,49,'Eastern expedition equipment'),(1449,38.5,66.0,'Western expedition equipment')],
})

# Classification: an absent completion is normal for pure courier/dialogue quests,
# but not an excuse to skip all meaningful objectives. The source-detected
# complete goals win over guesses from quest titles.
def has_obj(qid):
    d=QDB.get(str(qid),{});return bool(d.get('objectives'))

def coords(qid,t,context=None):
    if (qid,t) in KNOWN:return KNOWN[qid,t]
    q=Q.get(qid,{})
    for loc in q.get('locations',[]):
        role={'accept':'start','turnin':'end','complete':'objective'}.get(t)
        if loc.get('role')==role and loc.get('zone') in MAPS:
            xy=loc.get('xy')
            if isinstance(xy,list) and len(xy)==2 and all(isinstance(x,(int,float)) for x in xy):return (MAPS[loc['zone']],*xy)
    for cand in SOURCEMETA[qid][t]:
        if all(k in cand for k in ('map','x','y')):
            return cand['map'],cand['x'],cand['y']
    return None

def add_point(goal,point):
    if point and not all(k in goal for k in ('map','x','y')):
        goal.update({'map':int(point[0]),'x':float(point[1]),'y':float(point[2])})
    if 'x' in goal and not ('map' in goal and 'y' in goal):
        goal.pop('x',None);goal.pop('y',None)
    return goal

def get_meta(qid,t):
    for g in SOURCEMETA[qid][t]:
        if 'npc' in g or 'object' in g or 'item' in g:
            return copy.deepcopy(g)
    return None

def quest_goal(qid,t,optional=False):
    q=Q[qid];ref=get_meta(qid,t)
    if ref is None:ref={'t':t,'quest':qid,'title':q['name']}
    ref['title']=q['name'];ref['quest']=qid;ref['t']=t
    if t=='accept':ref['minLevel']=q.get('min_level') or 1;ref['qlvl']=q.get('level') or 1
    if t=='turnin':ref['rewards']={'xp':int(q.get('xp') or 0)}
    add_point(ref,coords(qid,t))
    if optional or qid in OPTIONAL_QIDS:ref['optional']=True
    return ref

def goto(point,label,optional=False):
    return {'t':'goto','map':int(point[0]),'x':float(point[1]),'y':float(point[2]),'text':label,**({'optional':True} if optional else {})}

def step(title,goals,note='',**kw):
    s={'title':title[:110], 'goals':[g for g in goals if g]}
    if note:s['note']=note.strip()
    s.update(kw)
    return s

def source_obj_goals(qid,orig=None):
    """Use quest-log-indexed targets and recorded spawn points to drive the arrow.

    Do not create an unverified destination for objects/dungeon bosses: use
    authored multistops or retain the complete quest goal with clear cave text.
    """
    q=Q[qid];d=QDB.get(str(qid),{})
    out=[]
    if qid in MULTISTOP:
        for point in MULTISTOP[qid]:out.append(goto(point[:3],point[3]))
        out.append(quest_goal(qid,'complete'))
        return out
    # For every *recorded* kill objective make an individual tracked kill goal.
    # The reference subset includes 52 kill targets, with 52 associated spawn records.
    if d.get('objectives') and all(o.get('type')=='kill' for o in d['objectives']):
        for i,o in enumerate(d['objectives'],1):
            npc=NDB.get(str(o['id']),{})
            wanted=int(d.get('zone') or 0)
            spawns=npc.get('spawns',{});records=spawns.get(str(wanted),{})
            if not records and len(spawns)==1:records=next(iter(spawns.values()))
            pts=[p for p in records.get('pts',[]) if isinstance(p,list) and len(p)==2]
            if not pts:
                out=[];break
            # The source records are deterministic, but not all are one camp.
            # Use a location from the source if that quest's author set it;
            # otherwise choose the densest documented cluster, not a guessed spot.
            src=coords(qid,'complete')
            if src and src[0] == wanted:
                px,py=src[1:]
            else:
                # pick medoid among samples, biased toward local density within 8 map %.
                def density(p):return sum(1 for x in pts if (x[0]-p[0])**2+(x[1]-p[1])**2<=7.0**2)
                px,py=max(pts,key=density)
            pmap=wanted or (int(next(iter(spawns))) if spawns else 0)
            gg={'t':'kill','quest':qid,'title':q['name'],'oi':i,'npc':int(o['id']),'target':npc.get('name',f'NPC {o["id"]}'),'count':int(o.get('count') or 1),'map':pmap,'x':round(px,2),'y':round(py,2),'group':{'kind':'group','size':5}}
            # Include nearby sample locations to let Polestar treat it as a hunt area.
            near=sorted(pts,key=lambda x:(x[0]-px)**2+(x[1]-py)**2)[:6]
            gg['spots']=[{'x':round(x,2),'y':round(y,2),'r':75,'n':1,**({'alt':True} if j else {})} for j,(x,y) in enumerate(near)]
            out.append(gg)
        if out:return out
    # Prefer an explicit authored objective pin from another properly compiled pack.
    for o in SOURCEMETA[qid]['complete']:
        if 'map' in o and 'x' in o and 'y' in o:
            g=quest_goal(qid,'complete');g.update({k:copy.deepcopy(o[k]) for k in ('map','x','y')});return [g]
    gg=quest_goal(qid,'complete')
    if not all(k in gg for k in ('map','x','y')):
        # If there is no reliable objective coordinate, the tracked quest still
        # advances automatically. Don't send the party to the quest giver.
        gg.pop('map',None);gg.pop('x',None);gg.pop('y',None)
    return [gg]

# Desired active chapters by quest reward, plus carried pickup/inside work.
REWARDS={int(c['number']):list(map(int,c['quest_ids_in_reward_order'])) for c in MODEL['chapters']}
RCH={qid:c for c,ids in REWARDS.items() for qid in ids}
# Carryover goals that must be done BEFORE their quest's actual reward chapter.
EARLY_ACCEPT={3380:1,4120:1,96776:1,97378:1,93404:1,7066:2,5158:3,3518:3,3542:3,3563:3,91548:3,95283:3,95483:4,4787:4,1446:4,3446:7,3447:7,3528:7,2967:7,4987:11,5093:9}
EARLY_COMPLETE={96776:2,4120:9,4787:5,91548:12}
# Special source accept fallbacks and optional once-per-party branches.
OPTIONAL_QIDS={3380,97378,4787,3528,4987,5093,5405}

# The order in each chapter is the order of the underlying authored route.
STREAMS={
 1:[('old','04-shendralas')],
 2:[('old','08-maraudon-finish')],
 3:[('old','03-tanaris-feralas'),('ref','04-felwood'),('ref','01-azshara'),('old','08-maraudon-finish')],
 4:[('ref','02-alcaz'),('ref','03-tanaris-ungoro'),('ref','04-felwood')],
 5:[('old','06-hinterlands'),('ref','02-alcaz')],
 6:[('old','05-searing-gorge')],
 7:[('ref','08-kalimdor-rewards'),('ref','03-tanaris-ungoro')],
 8:[('ref','03-tanaris-ungoro')],
 9:[('ref','04-felwood'),('old','08-maraudon-finish'),('ref','09-winterspring')],
 10:[('ref','08-kalimdor-rewards'),('ref','09-winterspring')],
 11:[('ref','06-western-plaguelands')],
 12:[('ref','05-blasted-temple')],
 13:[('ref','05-blasted-temple'),('ref','08-kalimdor-rewards'),('ref','06-western-plaguelands')],
}

# Add anchor notes and correct early objectives to preserve the dungeon constraints.
INTRO={
 1:'Start with at least 20 free quest slots (Forever capacity: 40). Your party already ran Zul\'Farrak. If Uzer\'i has no Sunken Temple quest, check prior completion rather than waiting. Dungeon quests must be prepared before each run.',
 2:'FULL MARAUDON: do not enter until Pariah, Vyletongue, Princess, Legends, Rot and Regret, and An\'she are prepared. Do the exterior khans, orange and purple wings, Celebras, Princess, then Rotgrip water. No second clear budget.',
 3:'Finish the compact Feralas kills, early Felwood water and Azshara. Accept overlapping quests before clearing camps. The Sin\'dorei tome sets up Vek\'zol in Blasted Lands.',
 4:'ALCAZ: Leave The Questioner alive. All five must accept Mason\'s The Man in the Iron Chains BEFORE killing him. Also prepare the Ancient Egg and Jammal\'an quests for the later Sunken Temple run.',
 5:'One Jintha\'Alor climb. Talk to Elder Torntusk and accept Recover the Key BEFORE killing Hitah\'ya. Collect the Ancient Egg if eligible; otherwise skip the Hakkar branch.',
 6:'Bring 15 Silk Cloth per player. Accept Forging the Shaft before the main Dark Iron kills. Light the four towers using the torch and check all five players.',
 7:'Batch capital receipts and Tanaris kills. Accept The Stone Circle BEFORE the Ratchet chest pickup, then take BOTH Sunken Temple follow-ups from Marvon.',
 8:'Accept all three pylon quests before visiting the pylons. Finish Apes of Un\'Goro and accept Mighty U\'cha before killing the named ape.',
 9:'Resume Felwood\'s blessed-water quest. Do both moonwell visits, northern Deadwood work, the Malorne statue and Seed of Life hand-in in Moonglade.',
 10:'Close capital hand-ins, Talo\'s Strength of Corruption and the receipts. WPL can be skipped only when the lowest member has enough XP to cover remaining Blasted/Temple rewards.',
 11:'At each cauldron, loot the keeper key, open the cauldron and return the new courier quest to Shadow Priestess Vandis at the Bulwark before starting the next farm.',
 12:'Complete the Fallen Hero story and Vek\'zol with the item prepared in Azshara. Stop before the level-60 follow-up.',
 13:'SUNKEN TEMPLE: turn in Into the Depths and Secret of the Circle INSIDE, then loot Essence of Eranikus and use the font before leaving. Finish Jammal\'an and Hakkar if eligible, then batch capital rewards.',
}

def src_steps(kind,key):
    if kind=='old':return copy.deepcopy(OLD[key])
    return copy.deepcopy(R49[key]['steps'])

def eligible(qid,t,ch):
    if qid not in Q:return False
    if t=='accept':return ch==EARLY_ACCEPT.get(qid,RCH.get(qid))
    if t=='complete':return ch==EARLY_COMPLETE.get(qid,RCH.get(qid))
    if t=='turnin':return ch==RCH.get(qid)
    return ch==EARLY_COMPLETE.get(qid,RCH.get(qid))

AUTHOR_STEPS={};STATS={};QA=[]
for chapter in MODEL['chapters']:
    ch=chapter['number'];buf=[];pending=[];seent=collections.Counter()
    def add_step(st):
        nonlocal_dummy=None
        gs=[g for g in st['goals'] if g]
        if not gs:
            if st.get('note'):pending.append(st['note'])
            return
        x=copy.deepcopy(st);x['goals']=gs
        if pending:
            x['note']=(' | '.join(pending)+' | '+x.get('note',''))[:2100];pending.clear()
        buf.append(x)
    def direct(qid,t,note='',optional=False):
        assert qid in Q, qid
        return step(('Pick up ' if t=='accept' else 'Hand in ')+Q[qid]['name'],[quest_goal(qid,t,optional)],note)
    def work(qid,note='',point=None):
        gg=source_obj_goals(qid)
        if point:
            for item in gg:
                if item['t']=='complete':add_point(item,point)
        return step('Complete '+Q[qid]['name'],gg,note)
    # Mandatory preflight pickups at their grounded giver coordinates.
    if ch==1:
        add_step(step('Camp Mojache: prepare for Felwood and the Temple', [quest_goal(3380,'accept',True),quest_goal(4120,'accept')],
          'Witch Doctor Uzer\'i (3380) and Talo Thornhoof (4120) are different NPCs. The Sunken Temple introduction may already be finished or unavailable on some characters; check instead of blocking the group.'))
        add_step(step('Skywatcher Plateau: take An\'she\'s Radiance', [quest_goal(96776,'accept')],
          'Olana Brighthoof in northern Mulgore at 32.6,24.0. Keep this for the Maraudon crystal beside Landslide.'))
        add_step(step('Thunder Bluff: check Mirrorscale', [quest_goal(97378,'accept',True)],
          'Melor Stonehoof at 61.5,80.9. If the quest is unavailable, do not wait; check its prerequisite on your character and skip this optional branch.'))
    if ch==4:
        # The first Alcaz introduction was accepted during Azshara by Eitrigg.
        pass
    if ch==5:
        add_step(step('Orgrimmar: catch Ripple Recovery if missing',[quest_goal(650,'accept',True)],
          'If Ripple Recovery was accepted in the previous pack, its accept auto-skips. Otherwise pick it up in Orgrimmar before leaving for Hinterlands.'))
    if ch==9:
        add_step(step('Felwood wildlife for Talo',source_obj_goals(4120),
          'Kill 12 Angerclaw Grizzlies and 12 Felpaw Ravagers in northern Felwood. Return the reward to Talo in chapter 10.'))
    # source spans, with latest sources taking precedence for all quest-stage text.
    for kind,key in STREAMS[ch]:
        src=src_steps(kind,key)
        for st in src:
            source_goals=st.get('goals',[])
            filtered=[]
            for g in source_goals:
                t=g.get('t')
                qid=g.get('quest')
                if t in ('accept','complete','turnin'):
                    if qid in Q and eligible(qid,t,ch):
                        gg=quest_goal(qid,t,optional=(qid in OPTIONAL_QIDS and t=='accept'))
                        # Keep the author-location if known; it is usually a live coordinate.
                        if all(k in g for k in ('map','x','y')):
                            gg.update({k:g[k] for k in ('map','x','y')})
                        for k in ('npc','npcName','object','objectName','spots','group','direct'):
                            if k in g:gg[k]=copy.deepcopy(g[k])
                        filtered.append(gg)
                elif t in ('collect','kill','interact','use'):
                    if qid in Q and eligible(qid,t,ch):filtered.append(copy.deepcopy(g))
                elif t in ('enter', 'getfp','goto'):
                    # Only retain travel if a remaining tracked quest in the same step needs it.
                    if any(g2.get('quest') in Q and eligible(g2.get('quest'),g2.get('t'),ch) for g2 in source_goals):filtered.append(copy.deepcopy(g))
            if not filtered:continue
            note=st.get('note','') or ' | '.join(st.get('note_parts',[]))
            # Kill goals from upstream are preferred. For old quest-level complete goals,
            # inject a deterministic subobjective and its route points at the same step.
            expanded=[]
            for g in filtered:
                if g['t']=='complete':
                    qid=g['quest']
                    # For direct-completes where quest has no objective data, retain original goal.
                    original=copy.deepcopy(g)
                    expansion=source_obj_goals(qid,original)
                    if any(z['t']=='kill' for z in filtered):expanded.append(original)
                    else:
                        # Source-specific location overrides on whole-quest completes.
                        if expansion and expansion[-1]['t']=='complete' and all(k in original for k in ('map','x','y')):
                            expansion[-1].update({k:original[k] for k in ('map','x','y')})
                        expanded+=expansion
                else:expanded.append(g)
            # Preserve the authored goal order. In particular a turn-in must precede
            # its newly unlocked follow-up accept in the SAME NPC interaction; moving
            # all turnins to the last step breaks Blizzard's quest offer and Polestar.
            # Split only when a quest is accepted and worked in one step or when a
            # quest is worked and then rewarded in that step.  Those are distinct
            # travel destinations, even if another quest is already available here.
            groups=[];current=[];taken=set();worked=set()
            for g in expanded:
                qid=g.get('quest');t=g['t']
                split=(qid in taken and t in ('complete','kill','collect','interact','use')) or \
                      (qid in worked and t=='turnin')
                if split and current:
                    groups.append(current);current=[];taken=set();worked=set()
                current.append(g)
                if qid and t=='accept':taken.add(qid)
                if qid and t in ('complete','kill','collect','interact','use'):worked.add(qid)
            if current:groups.append(current)
            for j,group in enumerate(groups):
                if not group:continue
                # The given source title and notes apply to the entire encounter.
                ttl=st['title'] if j==0 else (('Work objectives: ' if group[0]['t'] in ('complete','kill','collect','interact','use') else 'Quest handoff: ')+st['title'])
                add_step(step(ttl,group,note if j==0 else ('Continue: '+note)[:1500]))
    # Standalone content absent from the old packs: Forever additions and missed old chain.
    if ch==1:
        # Must occur AFTER Forlorn Gardens and before Word of the Woods.
        pass
    AUTHOR_STEPS[ch]=buf

# Edit the source-derived timeline without dropping its known route stops.
def insert_at(ch, predicate, items, after=False):
    s=AUTHOR_STEPS[ch]
    found=next((i for i,st in enumerate(s) if predicate(st)),None)
    if found is None:found=len(s)-1
    s[found+(1 if after else 0):found+(1 if after else 0)] = items

def contains(st,qid,typ=None):
    return any(g.get('quest')==qid and (typ is None or g.get('t')==typ) for g in st['goals'])

def ensure_stage(ch,qid,t,before=None,after=None,note='',optional=False):
    steps=AUTHOR_STEPS[ch]
    if any(contains(s,qid,t) for s in steps):return
    if t=='complete':new=step('Complete '+Q[qid]['name'],source_obj_goals(qid),note)
    else:new=step(('Accept ' if t=='accept' else 'Turn in ')+Q[qid]['name'],[quest_goal(qid,t,optional)],note)
    if before:
        insert_at(ch,lambda s:contains(s,before),[new])
    elif after:
        insert_at(ch,lambda s:contains(s,after),[new],after=True)
    else:
        steps.append(new)

# Missing garden follow-up must be inserted BEFORE Word of the Woods, not at chapter end.
ensure_stage(1,93362,'accept',before=93594,note="Take this only AFTER turning in Forlorn Gardens to Mithera.")
ensure_stage(1,93362,'complete',before=93594,note="In Forlorn Gardens kill 4 Rowdy Roses, 4 Terrible Tulips, 20 Malevolent Marigolds.")
ensure_stage(1,93362,'turnin',before=93594,note="Return to Mithera before taking Word of the Woods.")
# Ensure the other cross-chapter pickups don't come at the last moment or get omitted.
ensure_stage(1,93404,'accept',after=93594,note="From Woodwyrd at 69.5,71.9. Keep this until you collect the Rotgrip pool water in Maraudon.")
# In Maraudon, entry and follow-on quests are taken BEFORE their work; move the
# Pariah, Vyletongue and Princess pickups ahead of Legends/instance encounter.
for qid in (7067,7029,7064):
    ensure_stage(2,qid,'accept',before=7044,note='Pick up before entering Maraudon for the full clear.')
    aa=AUTHOR_STEPS[2]
    existing=next((i for i,s in enumerate(aa) if contains(s,qid,'accept')),None)
    if existing is not None:
        st=aa[existing]
        # When the pickup was grouped with other quests, move just that goal.
        g=next(g for g in st['goals'] if g.get('quest')==qid and g['t']=='accept')
        st['goals'].remove(g)
        if not st['goals']:aa.pop(existing)
        insert_at(2,lambda s:contains(s,7044,'accept'),[step('Pick up '+Q[qid]['name'],[g],'Before the instance; all five accept.')])
# Celebras follow-up is only available after Legends turn-in, and before his ritual.
# Keep dungeon 'complete' stages separated from reward arrows.
ensure_stage(2,96776,'complete',before=7064,note="Fixed crystal beside Landslide; not ordinary boss loot. Each player clicks it.")
ensure_stage(2,7066,'accept',after=7064,note="After Princess, talk to Zaetar's Spirit BEFORE dropping into the water; carry Seed of Life to Moonglade.")
# A route leg to the dungeon entrance explicitly grounds the first inner objective.
insert_at(2,lambda s:contains(s,7044,'accept'),[step('Enter Maraudon for the full quest clear',[{'t':'enter','zone':'Maraudon'}],INTRO[2])],after=True)
# External entrance: coordinates are known; interior floors do not have
# verified usable MapUI positions in the reference database.
insert_at(2,lambda st:any(g['t']=='enter' and g.get('zone')=='Maraudon' for g in st['goals']),
          [step('Maraudon valley approach',[goto((1443,35.7,55.5),'Maraudon entrance, Desolace')],
                'Follow the cavern to Cavindra and the orange/purple portals; finish all outside khans first.')])
# Chapter 3 extra objective/quest givers.
for t in ('accept','complete','turnin'):
    ensure_stage(3,3063,t,before=8460,
      note='Harpies at Feralas 38.2,14.5, four of each type. Talo Thornhoof is at Camp Mojache 76.2,43.8.')
    if t!='accept':ensure_stage(3,97378,t,before=8460 if t!='turnin' else 5535,
      note='The named Mirrorscale is around Feralas 48.0,46.0. Deliver the wing to Melor in Thunder Bluff. This is conditional if the quest was offered.')
ensure_stage(3,96776,'turnin',before=8460,note="Turn in the Maraudon crystal to Olana at Mulgore 32.6,24.0.")
ensure_stage(3,5158,'accept',after=5157,note='Carry the water to Islen Waterseer at Ratchet during the chapter 4 boat visit.')
ensure_stage(3,3542,'accept',after=3517,note='Andron Gant delivery to Undercity; save until the eastern crossing.')
ensure_stage(3,95283,'accept',after=91547,note='Get The Missing Kor\'kron from Eitrigg before travelling to Alcaz.')
ensure_stage(3,91548,'accept',after=91547,note='After Zevrost\'s tome handoff, carry Vek\'zol for Blasted Lands.')
insert_at(4,lambda st:contains(st,95309,'complete'),
  [step('Alcaz Prison entrance building',[goto((1445,74.6,14.6),'Prison building at north end of Alcaz Island')],
   'Swim from the Dustwallow coast. Enter the north prison building and follow stairs down to its basement portal; avoid killing The Questioner until Mason offers the key quest.')])
# Alcaz route: preserve the final prisoner before Questioner. Build only source-backed goals.
ensure_stage(4,3380,'turnin',after=96332,note='Marvon Rivetseeker at Broken Pillar Tanaris 52.7,45.9. If the intro was never offered, diagnose/skip rather than blocking the dungeon plan.')
ensure_stage(4,5158,'turnin',after=3380,note='Ratchet Islen Waterseer, 65.8,43.8. Take the blessed water back to Felwood.')
ensure_stage(4,4787,'accept',after=3380,note='Yeh\'kinya at Steamwheedle Port. Only available after the completed Zul\'Farrak prophecy. Keep for Jintha\'Alor egg.')
ensure_stage(4,1446,'accept',after=4787,note='Atal\'ai Exile in the Hinterlands 33.8,75.2, before Sunken Temple.')
# Rearrange the four end-of-chapter preparations in the intended geography.
# The relevant accepting steps remain automatic and independently skippable.
# Hinterlands: explicit Forever-specific named mob and Egg interaction.
ensure_stage(5,98203,'accept',before=7850,note='Qujo in Revantusk at 78.0,77.8.')
ensure_stage(5,98203,'complete',before=7850,note='Witch Doctor Ti\'ik in the cave west of Hiri\'watha, target search area 26,65. Check five heads; Nov 20 hotfix improved party drops.')
ensure_stage(5,98203,'turnin',before=7850,note='Return to Qujo at Revantusk 78.0,77.8.')
ensure_stage(5,4787,'complete',after=7846,note='During Jintha\'Alor climb, take the Ancient Egg from the top altar if Prophecy of Mosh\'aru is complete.')
# Searing: every tower is an actual ordered location rather than a note only.
# Capital, Tanaris and Temple preflight.
ensure_stage(7,96376,'turnin',before=3518,note='If you took Mason\'s State Secrets follow-up in Westfall, deliver the document to the indicated Orgrimmar recipient. The coordinates are a city search hint.')
ensure_stage(7,95483,'turnin',before=3518,note='After Alcaz, Thrall Needs to Know is handed to Thrall in Orgrimmar.')
ensure_stage(7,3446,'accept',after=3444,note='Accept at Marvon after returning the Stone Circle. Keep for Temple.')
ensure_stage(7,3447,'accept',after=3444,note='Accept at Marvon after returning the Stone Circle. Keep for Temple.')
ensure_stage(7,3528,'accept',after=4787,note='Accept only if you could finish The Ancient Egg and Yeh\'kinya offers God Hakkar.')
ensure_stage(7,2967,'accept',after=2954,note='Hold this for scheduled Thunder Bluff rewards.')
# Un'Goro: Lost! is an existing ordinary chain after starting at Ringo's cave.
for t in ('accept','complete','turnin'):
    ensure_stage(8,4492,t,before=974 if t=='accept' else 4301,
      note='Pick up Lost! from Spraggle Frock (43.6,8.5); find and turn in to Ringo on Fire Plume Ridge (51.9,49.9). The escort is a SEPARATE follow-up, not included in this reward.')
# The chapter reward count explicitly keeps this quest; no fake auto progression for an absent NPC.
# Felwood finale and Moonglade carried quest.
ensure_stage(9,7066,'turnin',after=8465,note='Deliver Seed of Life to Keeper Remulos in Moonglade 36.2,41.8. Group cannot all use Druid Teleport: Moonglade.')
ensure_stage(9,5242,'accept',before=8461,note='Ask Greta Mosshoof for A Final Blow before going into Shadow Hold.')
ensure_stage(9,5242,'complete',after=8461,note='Shadow Lord Fel\'dan and both guards in Shadow Hold; source objective area around Felwood 38.9,46.8.')
ensure_stage(9,5242,'turnin',after=8461,note='Return to Greta at Bloodvenom Post.')
# Strength of Corruption tracked during Felwood; deliver later.
ensure_stage(10,4120,'turnin',after=2968,note='Fly to Camp Mojache; hand back to Talo Thornhoof at Feralas 76.2,43.8.')
for qid in (3562,3563,3564):ensure_stage(10,qid,'turnin',before=2967,note='Return this tablet payment to Jediga in Azshara 22.6,51.4.')
# Remaining prepared Temple objectives and scattered reward recipients.
for qid in REWARDS[13]:ensure_stage(13,qid,'turnin',note='Finish the quest at the indicated in-dungeon object or reward NPC.')
for qid in (3446,3447,3373,1446,3528):ensure_stage(13,qid,'complete',before=qid,note='Complete this inside Sunken Temple before the final external turn-ins.')
ensure_stage(13,3373,'accept',before=3373,note='Loot Essence starter from Shade of Eranikus and use the font in the same chamber BEFORE leaving.')
# Grounded route to Sunken Temple before the first interior objective. The
# entry is on the swamp surface; no invented dungeon-floor map positions.
AUTHOR_STEPS[13].insert(0,step('Swamp of Sorrows: enter Sunken Temple',
  [goto((1435,69.7,53.0),'Sunken Temple, Pool of Tears'),{'t':'enter','zone':"Temple of Atal'Hakkar"}],
  'Go down the temple stairs, cross the flooded halls to the dungeon portal. Check all five have Marvon, Jammal\'an and (when eligible) Hakkar quests before entering.'))
# Recover every required acceptance in a safe point. Courier quests without a
# quest-log objective should progress accept->turnin automatically by design.
for ch,ids in REWARDS.items():
    for qid in ids:
        target_ch=EARLY_ACCEPT.get(qid,ch)
        if target_ch==ch:ensure_stage(ch,qid,'accept',before=qid,note='Take this quest before its objectives. Check party member eligibility.')
    if ch!=13:
        for qid in ids:
            if qid in EARLY_COMPLETE and EARLY_COMPLETE[qid]!=ch:continue
            if not any(contains(s,qid,'complete') or any(g.get('quest')==qid and g['t'] in ('kill','collect') for g in s['goals']) for s in AUTHOR_STEPS[ch]):
                # Don't manufacture a completion stage for courier chains with no objectives.
                if has_obj(qid) or (qid not in QDB and qid in {7044,7046,7067,7029,7064,93404,92914,96010,96018,99257,99258,93341,93362,3063,97378,98203,4492,7840,7850,7846,3442,3443,3452,3463}):
                    ensure_stage(ch,qid,'complete',before=qid,note=Q[qid].get('objective',''))
# Reconcile src-derived duplicate goals and objective stages; imported v0.2 had
# misplaced source acceptance, so prefer earliest appropriate stage.
for ch,steps in AUTHOR_STEPS.items():
    seen=set();out=[]
    for st in steps:
        keep=[]
        for g in st['goals']:
            t=g['t'];qid=g.get('quest')
            key=(t,qid,g.get('oi')) if qid and t in ('accept','turnin','complete') else None
            if key and key in seen:continue
            if key:seen.add(key)
            keep.append(g)
        if keep:
            st['goals']=keep;out.append(st)
    AUTHOR_STEPS[ch]=out

# Repair carryover ordering inherited from source chunks. The *quest* is
# authoritative for event ordering, not the human-readable source title. The
# previous exporter appended missing starts after work and misplaced a few
# bare courier completion nodes. Do not regress to that release's ordering.
def remove_single(ch,qid,t):
    for st in AUTHOR_STEPS[ch]:
        for g in list(st['goals']):
            if g.get('quest')==qid and g['t']==t:
                st['goals'].remove(g)
                return g
    return None

def clean_empty(ch):
    AUTHOR_STEPS[ch]=[st for st in AUTHOR_STEPS[ch] if st['goals']]

def relocate_before(ch,qid,t,anchor_qid,anchor_t=None):
    g=remove_single(ch,qid,t)
    if g is None:return
    clean_empty(ch)
    insert_at(ch,lambda st:contains(st,anchor_qid,anchor_t),
              [step(('Accept' if t=='accept' else 'Turn in' if t=='turnin' else 'Complete')+' '+Q[qid]['name'],[g],Q[qid].get('objective',''))])

def relocate_after(ch,qid,t,anchor_qid,anchor_t=None):
    g=remove_single(ch,qid,t)
    if g is None:return
    clean_empty(ch)
    insert_at(ch,lambda st:contains(st,anchor_qid,anchor_t),
              [step(('Accept' if t=='accept' else 'Turn in' if t=='turnin' else 'Complete')+' '+Q[qid]['name'],[g],Q[qid].get('objective',''))],after=True)

# The Mihtera garden chain: first turn in Forlorn Gardens, then the peonies
# prerequisite, then she offers Word of the Woods.
relocate_after(1,93341,'turnin',93341,'complete')
# The old Maraudon source already supplies the correct follow-up quest order.
# 4492 starts at Spraggle Frock and turns in to Ringo, NOT the reverse.
relocate_before(8,4492,'accept',4492,'complete')
relocate_before(8,974,'accept',974,'complete')
ensure_stage(8,974,'turnin',after=974,
  note='Return to Krakle in Un\'Goro, 30.9,49.6, after the thermometer registers the hottest spot.')
relocate_after(8,974,'turnin',974,'complete')
# The Essence is a *quest-starting item*. Accept from the item after Eranikus
# dies; use the font and reward it. It must precede the quest-completion flag.
relocate_before(13,3373,'accept',3373,'complete')
# Horde Kirsta chain: each reward must be handed in before the follow-up becomes
# available. The 0.2 package omitted all three rewards entirely.
for qid, nxt in [(6004,6023),(6023,6025),(6025,5238)]:
    ensure_stage(11,qid,'turnin',before=nxt,
      note='Return to Kirsta Deepshadow at the northern WPL watch area and claim this reward before the next Unfinished Business stage.')
    relocate_before(11,qid,'accept',qid,'kill' if qid in (6004,6023) else 'complete')
relocate_after(11,6025,'turnin',6025,'complete')
# Courier quests are automatically finished at their recipient and are NOT
# quest-objective tracking stages: a naked `complete` in front of `accept`
# points to nowhere and prevents onward travel.
for ch,qid in [(3,91538),(3,3561),(3,3565),(3,91531),(3,3541),(3,91547),
               (4,95283),(4,95284),(4,95285),(4,96337),(4,3542),(4,3380),(4,5158),
               (7,3518),(7,2965),(8,3845),(8,4321),
               (10,2967),(10,3563),
               (9,5159),(10,3562),(10,3564),
               (11,5230),(11,5023),(11,5049),(11,5050),
               (11,5232),(11,5234),(11,5236)]:
    remove_single(ch,qid,'complete')
    clean_empty(ch)
# Some cross-zone claims in the source are at the correct NPC but have no
# explicit complete flag: leave the authored turn-in at the correct recipient.
# A few conditional quest chains need optionality across *all* stages, not just
# acceptance; otherwise a missing Uzer'i quest will halt the entire party.
for ch,steps in AUTHOR_STEPS.items():
    for st in steps:
        for g in st['goals']:
            if g.get('quest') in OPTIONAL_QIDS:
                g['optional']=True

# Final navigation-repair pass: add actual objective targets where the source
# only had a generic complete. Never put the reward NPC's coordinates on a kill
# completion step. Use explicit checked points for old chains.
for ch,steps in AUTHOR_STEPS.items():
    for st in steps:
        new=[]
        for g in st['goals']:
            if g.get('t')=='complete' and g.get('quest') in Q:
                qid=g['quest']
                if not all(k in g for k in ('map','x','y')):
                    if qid in MULTISTOP and not any(z['t']=='goto' for z in st['goals']):
                        for point in MULTISTOP[qid]:new.append(goto(point[:3],point[3]))
                    # Use source objective pin or named hunt area, not recipient.
                    p=coords(qid,'complete')
                    if p:add_point(g,p)
                    else:
                        src=next((z for z in SOURCEMETA[qid]['complete'] if all(k in z for k in ('map','x','y'))),None)
                        if src: g.update({k:src[k] for k in ('map','x','y')})
                # If there is reliable target metadata, replace a blanket complete
                # with per-mob quest-indexed goals (and their own spawn areas).
                expansion=source_obj_goals(qid)
                if expansion and any(x['t']=='kill' for x in expansion) and not any(z['t']=='kill' and z.get('quest')==qid for z in st['goals']):
                    new.extend(expansion);continue
            new.append(g)
        st['goals']=new

# Important authored manual objective steps and chapter gates. Document the
# actual multi-goal path rather than sending the arrow straight to turn-in.
for ch,steps in AUTHOR_STEPS.items():
    for st in steps:
        for g in st['goals']:
            if g['t'] in ('accept','turnin') and 'quest' in g:
                add_point(g,coords(g['quest'],g['t']))
        # Notes retain prose but never become blocking click-to-complete tasks.
        if 'CHECK:' in st.get('note',''):st['note']=st['note'].replace('CHECK: ','Check together: ')

# Rebuild parent/source metadata and audit every reward/phase.
result=[];issues=[];map_reports=[];t_counts=collections.Counter()
for chapter in MODEL['chapters']:
    ch=chapter['number'];steps=AUTHOR_STEPS[ch]
    # If authored notes exceed the Polestar guide frame limits trim to readable
    # diagnostics. Source long notes remain in evidence JSON.
    for st in steps:
        if 'note' in st:st['note']=st['note'][:1800]
        for g in st['goals']:
            t_counts[g['t']]+=1
            if 'x' in g or 'y' in g:
                assert all(k in g for k in ('map','x','y')),(ch,st['title'],g)
                assert 0<=g['x']<=100 and 0<=g['y']<=100,(ch,st['title'],g)
                map_reports.append({'chapter':ch,'title':st['title'],'goal':g['t'],'quest':g.get('quest'),'map':g['map'],'x':g['x'],'y':g['y']})
            if g.get('t')=='task':issues.append(f"manual goal {ch} {st['title']}")
    names={'quest:'+str(x):Q[x]['name'] for x in Q if any(z.get('quest')==x for s in steps for z in s['goals'])}
    g={'id':chapter['guide_id'],'pack':PID,'title':chapter['display_title'], 'faction':'Horde',
       'minLevel':int(chapter['levels_header'].replace('levels ','').split('-')[0]),
       'maxLevel':int(chapter['levels_header'].replace('levels ','').split('-')[1]),
       'category':'Leveling','folder':'Five Friends 48-54',
       'keywords':['group','horde','five friends','dungeon','navigation'],
       'why':'Quest-aware acceptance, objectives, rewards and mapped route between quest work and turn-ins.',
       'zone':{1:2652,2:280,3:1444,4:1445,5:1425,6:1427,7:1446,8:1449,9:1448,10:1454,11:1422,12:1419,13:109}[ch],
       'next':chapter['next_guide_id'],'author':'Five Friends','version':3,'group':True,
       'names':names,'steps':steps}
    result.append(g)
    if len(steps)>60:issues.append(f'Chapter {ch} has {len(steps)} steps > 60 limit')
    ids=[z.get('quest') for s in steps for z in s['goals'] if z.get('t')=='turnin']
    for qid in REWARDS[ch]:
        if ids.count(qid)!=1:issues.append(f'Chapter {ch} has {ids.count(qid)} turnins for {qid}')
    STATS[ch]={'steps':len(steps),'mappedGoals':sum('map' in z and 'x' in z for s in steps for z in s['goals']),
               'goalTypes':dict(collections.Counter(z['t'] for s in steps for z in s['goals'])),
               'rewardCount':len(ids)}

# Validate prerequisite phase presence across chapters.
ALLGOALS=[(ch,i,j,g) for ch,steps in AUTHOR_STEPS.items() for i,s in enumerate(steps) for j,g in enumerate(s['goals'])]
for qid in Q:
    acc=[k for k in ALLGOALS if k[3].get('quest')==qid and k[3]['t']=='accept']
    turn=[k for k in ALLGOALS if k[3].get('quest')==qid and k[3]['t']=='turnin']
    if len(turn)!=1:issues.append(f'{qid} turnin count {len(turn)}')
    if len(acc)!=1:issues.append(f'{qid} accept count {len(acc)}')
    if acc and turn and acc[0][:3]>turn[0][:3]:issues.append(f'{qid} accepted after turnin')
# Separate objectives must stand before rewards; check each real work stage.
for ch,steps in AUTHOR_STEPS.items():
    for i,s in enumerate(steps):
        k=[g for g in s['goals'] if g['t'] in ('kill','collect','complete','interact','use') and 'quest' in g]
        r=[g for g in s['goals'] if g['t']=='turnin']
        bad={z['quest'] for z in k} & {z['quest'] for z in r}
        if bad:issues.append(f'Chapter {ch} step {i} contains objective and turnin for {bad}')

# Author-provenance stats and navigation checks.
NAV_REPORT={'version':VERSION,'chapterStats':STATS,'allGoalTypes':dict(t_counts),'mappedGoals':len(map_reports),
            'unmappedObjectiveGoals':[{'chapter':ch,'quest':g['quest'],'name':Q[g['quest']]['name'],'title':AUTHOR_STEPS[ch][i]['title']} for ch,i,j,g in ALLGOALS if g['t'] in ('complete','kill','collect') and g.get('quest') in Q and not all(p in g for p in ('map','x','y'))],
            'mappedDetails':map_reports,'issues':issues,
            'method':'Quest-state progression authored from prior functional source packs; spawn points from targeted reference data or explicit researched coordinates; no invented indoor points.',
            'limitations':['Static goal validation only; no live WoW client testing.','Indoor dungeon map objective pins are intentionally omitted when unavailable in verified source.','Polestar navigation lines require Polestar\'s own Nav module and route-line settings.']}

(DEST/'build').mkdir(exist_ok=True)
(DEST/'build/compiled-guides.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
(DEST/'build/navigation-report.json').write_text(json.dumps(NAV_REPORT,ensure_ascii=False,indent=2))
(DEST/'evidence').mkdir(exist_ok=True)
# Revised route-ledger.json is a checked-in input in this self-contained source archive.
(DEST/'evidence/origin-files.txt').write_text('Previous 43-48 authored .guide source: Five_Friends_Polestar_GitHub_Repo_v1.2.1.zip\nPrevious 49-54 compiled guide payload: Five_Friends_Horde_49-54_v1.0.0_GitHub_Source.zip\nRevised 48-54 route ledger: Five_Friends_Horde_48-54_Revised_Plan.json\nResearch for new goal coordinates: see docs/LOCATION_EVIDENCE.md\n')
(DEST/'scripts').mkdir(exist_ok=True)
# The source script already lives inside DEST/scripts.

# Lua output generated directly from the tested format-5 compiled payload schema.
def lua_dump(v):
    if v is None:return 'nil'
    if isinstance(v,bool):return 'true' if v else 'false'
    if isinstance(v,str):return json.dumps(v,ensure_ascii=False)
    if isinstance(v,(float,int)):return repr(v)
    if isinstance(v,list):return '{'+', '.join(map(lua_dump,v))+'}'
    if isinstance(v,dict):
        return '{'+', '.join((k if re.fullmatch(r'[A-Za-z_]\w*',k) else '['+lua_dump(k)+']')+' = '+lua_dump(x) for k,x in v.items())+'}'
    raise TypeError(type(v))

addon=DEST/'addon'/NAME;addon.mkdir(parents=True,exist_ok=True)
(addon/'Guides.lua').write_text('-- Five Friends 48-54, navigable quest-aware goal pack. Version '+VERSION+'\n'+ '\n'.join('do\n local function register()\n  Polestar.RegisterGuide('+lua_dump(g)+')\n end\n if Polestar and Polestar.RegisterGuide then register() end\nend\n' for g in result))
(addon/'Pack.lua').write_text('local ADDON = ...\nPolestar.RegisterPack({addon = ADDON, id = '+lua_dump(PID)+', format = 5, title = "Five Friends: Horde 48-54", author = "Five Friends", version = '+lua_dump(VERSION)+', license = "CC0-1.0", source = "Coordinated five-player Horde leveling route; researched quests and navigation."})\n')
(addon/'MapFrames.lua').write_text((ROOT/'prev/addon/PolestarPack_FiveFriends4348/MapFrames.lua').read_text().replace('five-friends-43-48', PID))
(addon/(NAME+'.toc')).write_text('## Interface: 16001\n## Title: Polestar Community: Five Friends: Horde 48-54\n## Notes: Quest-aware objectives with mapped navigation and 13 linked Horde chapters\n## Author: Five Friends\n## Version: '+VERSION+'\n## Category: Polestar\n## Group: Polestar\n## Dependencies: Polestar\n## X-Polestar-Pack: '+PID+'\n## X-Polestar-Format: 5\n## X-Polestar-Needs: 0.4.1\n## X-License: CC0-1.0\nPack.lua\nMapFrames.lua\nGuides.lua\n')
(DEST/'pack.json').write_text(json.dumps({'id':PID,'folder':NAME,'version':VERSION,'title':'Five Friends: Horde 48-54','author':'Five Friends','format':5,'guides':len(result)},indent=2))
# Release documentation, QA scripts and CI are maintained as source files, not overwritten by rebuild.
print('VERSION',VERSION)
print('STATS',json.dumps(STATS))
print('ISSUES',len(issues),issues[:60])
print('UNMAPPED',len(NAV_REPORT['unmappedObjectiveGoals']))
print('PATH',DEST)
