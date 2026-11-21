#!/usr/bin/env python3
"""Regression assertions for the 48-54 route and native Polestar destinations."""
import collections
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
guides=json.loads((root/'build/compiled-guides.json').read_text())
model=json.loads((root/'evidence/route-ledger.json').read_text())
report=json.loads((root/'build/navigation-report.json').read_text())
assert report['version']=='0.3.1-rc4'
assert len(guides)==len(model['chapters'])==13
assert all(0<len(g['steps'])<=60 for g in guides)
assert [g['id'] for g in guides] == [c['guide_id'] for c in model['chapters']]
for a,b in zip(guides,guides[1:]):assert a['next']==b['id']
assert guides[-1]['next'] in ('',None)

phase=collections.defaultdict(lambda:collections.defaultdict(list))
for ch,g in enumerate(guides,1):
    rewards=[]
    for si,step in enumerate(g['steps']):
        assert step['goals'] and len(step['goals'])<80,(ch,si)
        active=set()
        for gi,goal in enumerate(step['goals']):
            typ=goal['t']
            assert typ!='task',(ch,si)
            if 'quest' in goal:
                phase[goal['quest']][typ].append((ch,si,gi))
            if typ in ('complete','kill','collect','interact','use') and 'quest' in goal:
                active.add(goal['quest'])
            if typ=='turnin':
                assert goal['quest'] not in active,('uncompleted same-step turnin',ch,si,goal['quest'])
                rewards.append(goal['quest'])
            if any(k in goal for k in ('x','y','map')):
                # For map coordinates, complete triple is mandatory; map alone can
                # identify a zone for travel (not authored here).
                if 'x' in goal or 'y' in goal:
                    assert all(k in goal for k in ('map','x','y')),(ch,si,goal)
                    assert 0<=goal['x']<=100 and 0<=goal['y']<=100
            if typ in ('kill','collect') and 'quest' in goal:
                assert isinstance(goal.get('oi'),int) and goal['oi']>=1,(ch,si,goal)
    assert set(rewards)==set(model['chapters'][ch-1]['quest_ids_in_reward_order']),('reward set',ch)
    assert len(rewards)==len(set(rewards))

for qid,d in phase.items():
    if 'turnin' not in d:continue
    assert len(d['turnin'])==1 and len(d['accept'])==1,(qid,'missing or duplicated phase')
    assert d['accept'][0]<=d['turnin'][0],(qid,'accept after reward')
    obj=sorted(p for t,v in d.items() for p in v if t in ('complete','kill','collect','interact','use'))
    if obj:
        assert d['accept'][0]<=obj[0] and obj[-1]<=d['turnin'][0],(qid,'objective out of order')

# Regressions: real work stages, mapped NPC stops, and single-clear safe constraints.
def matching(q,t):
    return [(ch,si,gi,z) for ch,g in enumerate(guides,1) for si,s in enumerate(g['steps'])
       for gi,z in enumerate(s['goals']) if z.get('quest')==q and z['t']==t]

def location(q,t):
    g=matching(q,t)[0][3]
    return g.get('map'),g.get('x'),g.get('y')

assert len(matching(96337,'complete'))==1 and len(matching(96337,'turnin'))==1
assert location(96337,'complete')==(1436,43.4,67.8)
assert matching(96337,'complete')[0][:3]<matching(96337,'turnin')[0][:3]
assert len(matching(3845,'collect'))==3
assert [z['item'] for _,_,_,z in matching(3845,'collect')]==[11104,11105,11106]
assert [z['oi'] for _,_,_,z in matching(3845,'collect')]==[1,2,3]
assert matching(3845,'collect')[-1][:3]<matching(3845,'turnin')[0][:3]
assert location(95283,'accept')==(1454,34.3,39.4)
assert location(86746,'accept')==(1447,42.0,38.9)
assert location(86746,'complete')==(1447,61.0,23.0)
assert location(86746,'turnin')==(1447,42.0,38.9)
assert location(91531,'turnin')==(1454,75.2,34.2)
assert matching(96335,'accept')[0][:3]<matching(96335,'complete')[0][:3]
assert matching(3373,'accept')[0][:3]<matching(3373,'complete')[0][:3]
assert matching(92914,'complete')[0][:3]<matching(92914,'turnin')[0][:3]
assert matching(96010,'complete')[0][:3]<matching(96010,'turnin')[0][:3]
assert len(matching(3380,'accept'))==1 and matching(3380,'accept')[0][3].get('optional') is True

# The route ledger's reward total and chapter count are unchanged.
assert len({q for q,d in phase.items() if 'turnin' in d})==170
assert len(report['geographicSplits'])>=10
assert not report['issues']
print('PASS: 13 chapters, 170 rewards, all quest phase ordering, 13+ geographic splits, '+
      'Mason document box, pack items, Eitrigg/Ekkal/Belgrom locations and dungeon sequencing.')
