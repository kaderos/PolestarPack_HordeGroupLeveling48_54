#!/usr/bin/env python3
"""Apply the rc4 location fixes and split geographically incompatible steps.

This is a conservative post-pass over the deterministic original authoring
build. We do NOT fabricate indoor map positions or straight-line walking paths.
A mapped goal already supplies a native Polestar destination. Redundant goto
commands ahead of those goals would interfere with native distance/search logic.
"""
import collections
import copy
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPILED = ROOT/'build/compiled-guides.json'
REPORT = ROOT/'build/navigation-report.json'
P = ROOT/'evidence/route-ledger.json'
GUIDES = json.loads(COMPILED.read_text())
REPORT_BEFORE = json.loads(REPORT.read_text())
MODEL = json.loads(P.read_text())
QUESTS = {q['id']: q for q in MODEL['quests']}
ITEMS = json.loads((ROOT/'inputs/ref49/reference/items.json').read_text())
VERSION = '0.3.1-rc4'

# All three location fixes are grounded in independent, current Forever
# quest references. Details and links are in docs/LOCATION_EVIDENCE.md.
KNOWN_FIXES = {
    (95283, 'accept'): (1454, 34.3, 39.4),  # Eitrigg, Orgrimmar
    (86746, 'accept'): (1447, 42.0, 38.9),  # Ekkal, Azshara
    (86746, 'turnin'): (1447, 42.0, 38.9),  # Ekkal, Azshara
    (86746, 'complete'): (1447, 61.0, 23.0),  # Legashi satyr camp area
    (91531, 'turnin'): (1454, 75.2, 34.2),  # Belgrom Rockmaul, Orgrimmar
}


def goal_point(g):
    if all(k in g for k in ('map','x','y')):
        return (int(g['map']), float(g['x']), float(g['y']))
    return None


def distance(a, b):
    if a is None or b is None:
        return 0 if a==b else 999
    if a[0]!=b[0]:return 999
    return math.hypot(a[1]-b[1],a[2]-b[2])


def quest_summary(g):
    qid=g.get('quest')
    if qid in QUESTS:return QUESTS[qid]['name']
    return str(g.get('text') or g.get('title') or g['t'])


# 1. Repair exact quest-giver, hand-in and hunt-area pins.
fixed=[]
for guide in GUIDES:
    for st in guide['steps']:
        for g in st['goals']:
            k=(g.get('quest'), g['t'])
            if k in KNOWN_FIXES:
                p=KNOWN_FIXES[k]
                for field,val in zip(('map','x','y'),p):g[field]=val
                fixed.append({'chapter':guide['id'],'quest':k[0],'goal':k[1],'point':list(p)})

# 2. A *physical objective* that rc3 mistakenly treated as a courier:
# Mason's supplied note leads to Loose Floorboards/Connery's Trunk upstairs in
# Moonbrook's inn. The tracked quest turn-in is the actual fixed object there.
# Do not create an objective at Mason's indoor NPC: that is a different map.
for guide in GUIDES:
    steps=guide['steps']
    for i,st in enumerate(steps):
        if any(g.get('quest')==96337 and g['t']=='turnin' for g in st['goals']):
            # This is the only written hand-in; insert objective immediately
            # before it so navigation cannot bypass work for a pickup.
            point=(1436,43.4,67.8)
            steps.insert(i,{
                'title': 'Recover Mason Connery\'s hidden Document Box',
                'note': 'Travel to Moonbrook in Westfall (43.4, 67.8). Search upstairs inside the inn, use the Loose Floorboards / Connery\'s Trunk indicated by Mason\'s Note and secure the Document Box. Every party member checks their quest before handing it in. This is a fixed interaction, not a boss drop.',
                'goals':[{'t':'complete','quest':96337,'title':QUESTS[96337]['name'],'map':point[0],'x':point[1],'y':point[2]}],
            })
            break

# 3. The raft's Small Pack is *not* a courier item: the player must open it to
# expose all three items. rc3 had removed the quest-objective goal entirely.
for guide in GUIDES:
    steps=guide['steps']
    for i,st in enumerate(steps):
        if any(g.get('quest')==3845 and g['t']=='turnin' for g in st['goals']):
            item_ids=(11104,11105,11106)
            goals=[]
            for oi,item_id in enumerate(item_ids,1):
                goals.append({'t':'collect','quest':3845,'oi':oi,'item':item_id,
                              'itemName':ITEMS[str(item_id)]['name'],'count':1,
                              'title':QUESTS[3845]['name']})
            steps.insert(i,{
                'title':'Open A Small Pack and recover its three contents',
                'note':'At the wrecked raft in Un\'Goro (63.1, 69.1), use A Small Pack obtained from the previous quest. Verify Large Compass, Curled Map Parchment and Lion-headed Key in every character\'s inventory before delivering to Linken. The objective count updates from the quest log; no manual click-to-complete step is required.',
                'goals':goals,
            })
            break

# 4. Describe the newer Forever-specific Azshara work explicitly, since the
# 2026 reference cache lacks q86746's three objective rows.
for guide in GUIDES:
    for st in guide['steps']:
        if any(g.get('quest')==86746 and g['t']=='complete' for g in st['goals']):
            st['note']=('Kill 5 Legashi Satyrs, 5 Legashi Rogues and 5 Legashi Hellcallers '
                         'in the Legashi camp around Azshara 61,23. Return to Ekkal '
                         'at Azshara 42.0,38.9 for the reward. '+st.get('note',''))[:1800]
        if any(g.get('quest')==95283 and g['t']=='accept' for g in st['goals']):
            st['note']=('Eitrigg is inside Orgrimmar at 34.3,39.4 (Throne Room). '
                        +st.get('note',''))[:1800]

# 5. Geographically coherent steps. Each step is one stop; a player who has
# already completed the earlier quest can skip its goal normally. This prevents
# Polestar from choosing the first known location in a multi-stop group and
# immediately presenting an unrelated hand-in elsewhere, without explicit
# navigation to that intermediate work location.
#
# Keep original multistop goto circuits intact: they encode the specific path
# of pylon fragments, tower torches, seals, etc. Split *after* their route if
# subsequent located goals are separated by a large distance.
SPLIT_DISTANCE = 4.0  # zone-coordinate percentage, a coarse town-vs-hunt separation
split_log=[]
for guide in GUIDES:
    new=[]
    for original in guide['steps']:
        goals=original['goals']
        chunks=[]
        active=[]
        anchor=None
        # Explicit authored goto legs are meaningful. Use a final goto anchor
        # until the end of the authored approach; do not split its consecutive
        # waypoints into one-step walks (these can depend on prior script state).
        last_goto=None
        for g in goals:
            p=goal_point(g)
            if g['t']=='goto':
                if last_goto is not None and chunks:
                    # Already inside an authored route; keep it together.
                    pass
                last_goto=p
                active.append(g)
                continue
            # Only separate on a change between two measured locations,
            # preserving order and all manual approach waypoints.
            reference=last_goto if last_goto is not None else anchor
            if (p and reference and distance(p,reference)>SPLIT_DISTANCE
                    and active and not any(h['t']=='goto' and distance(goal_point(h),p)<=SPLIT_DISTANCE for h in active)):
                chunks.append(active)
                active=[]
                anchor=None
                last_goto=None
            active.append(g)
            if p:
                anchor=p
                last_goto=None
        if active:chunks.append(active)
        if len(chunks)==1:
            new.append(original)
            continue
        for j,chunk in enumerate(chunks):
            s=copy.deepcopy(original)
            s['goals']=chunk
            if j:
                first=next((g for g in chunk if g['t'] in ('accept','turnin','complete','kill','collect','interact')),chunk[0])
                t=first['t']
                phrase={'accept':'Pick up','turnin':'Hand in','complete':'Finish objectives for','kill':'Hunt for','collect':'Collect for'}.get(t,'Travel for')
                s['title']=(phrase+' '+quest_summary(first))[:110]
                s['note']=('Separate destination (the previous stop is in a different area). '
                           + original.get('note',''))[:1800]
            new.append(s)
        split_log.append({'chapter':guide['id'],'original_title':original['title'],'parts':len(chunks),
                          'goal_types':[[g['t'] for g in chunk] for chunk in chunks]})
    guide['steps']=new

# 6. Keep the pack's unchanged quest/guide identities, reward ledger and order.
# The runtime's focus logic uses each goal's mapped location or spawn areas.
# Thus we never insert a redundant goto in front of a located NPC/quest goal.
chapter_stats={}
counts=collections.Counter()
mapped=0
unmapped=[]
issues=[]
for guide in GUIDES:
    steps=guide['steps']
    if len(steps)>60:
        issues.append(f"{guide['id']} exceeds 60 steps: {len(steps)}")
    for s in steps:
        if not s['goals']:issues.append(f"empty step: {guide['id']} {s['title']}")
        for goal in s['goals']:
            counts[goal['t']]+=1
            p=goal_point(goal)
            if p:
                mapped+=1
                if not (0<=p[1]<=100 and 0<=p[2]<=100):issues.append('bad coordinate '+str(p))
            elif goal['t'] in ('complete','kill','collect','accept','turnin'):
                unmapped.append({'chapter':guide['id'],'step':s['title'],'quest':goal.get('quest'),'type':goal['t']})
        work={g['quest'] for g in s['goals'] if g['t'] in ('complete','kill','collect','use','interact') and 'quest' in g}
        handins={g['quest'] for g in s['goals'] if g['t']=='turnin'}
        if work & handins:issues.append('same step work and turnin: '+guide['id'])
    chapter_stats[guide['id']]={'steps':len(steps),'goals':sum(map(lambda x:len(x['goals']),steps)),
                                'mapped_goals':sum(bool(goal_point(g)) for s in steps for g in s['goals'])}

COMPILED.write_text(json.dumps(GUIDES,ensure_ascii=False,indent=2)+'\n')


def lua_dump(v):
    if v is None:return 'nil'
    if isinstance(v,bool):return 'true' if v else 'false'
    if isinstance(v,str):return json.dumps(v,ensure_ascii=False)
    if isinstance(v,(int,float)):return repr(v)
    if isinstance(v,list):return '{'+', '.join(map(lua_dump,v))+'}'
    if isinstance(v,dict):return '{'+', '.join((k if re.fullmatch(r'[A-Za-z_]\w*',k) else '['+lua_dump(k)+']')+' = '+lua_dump(x) for k,x in v.items())+'}'
    raise TypeError(type(v))

addon=ROOT/'addon/PolestarPack_FiveFriends4854'
(addon/'Guides.lua').write_text('-- Five Friends 48-54, objective-aware routed quest pack. Version '+VERSION+'\n'+
    '\n'.join('do\n local function register()\n  Polestar.RegisterGuide('+lua_dump(g)+')\n end\n if Polestar and Polestar.RegisterGuide then register() end\nend\n' for g in GUIDES))

summary={
    'version':VERSION,
    'predecessor':'0.3.0-rc3',
    'chapterStats':chapter_stats,
    'allGoalTypes':dict(counts),
    'mappedGoals':mapped,
    'remainingUnmappedGoals':unmapped,
    'knownLocationCorrections':fixed,
    'geographicSplits':split_log,
    'issues':issues,
    'limitations':[
        'Static build and Lua registration tested; WoW Forever client not available.',
        'True walk-to-target route polylines depend on Polestar_Nav plus continent-specific Polestar_Nav_EK and Polestar_Nav_Kalimdor. No fabricated Legs.lua.',
        'Known dungeon-interior quest goals lack verified usable map coordinates; follow step notes inside Maraudon, Alcaz and Sunken Temple.',
        'Quest state, optional availability, coordinates, group completion and routing still require a live five-character smoke test.'
    ]
}
REPORT.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print('v'+VERSION,'chapters',len(GUIDES),'steps',sum(len(g['steps']) for g in GUIDES),
      'geographic splits',len(split_log),'mapped',mapped,'unmapped',len(unmapped),
      'issues',len(issues),'types',dict(counts))
for k,v in chapter_stats.items():print(k,v['steps'])
if issues:raise SystemExit('FAILED: '+json.dumps(issues,indent=2))
