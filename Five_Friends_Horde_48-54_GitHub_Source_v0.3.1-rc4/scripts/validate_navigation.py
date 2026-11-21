#!/usr/bin/env python3
import json, re, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
guides=json.loads((root/'build/compiled-guides.json').read_text())
r=json.loads((root/'evidence/route-ledger.json').read_text())
expected={c['number']:set(c['quest_ids_in_reward_order']) for c in r['chapters']}
assert len(guides)==13
ids=set(g['id'] for g in guides)
assert len(ids)==13
seen=[]
for i,g in enumerate(guides,1):
 assert 1<=len(g['steps'])<=60,(i,len(g['steps']))
 assert (g['next'] in ids if g['next'] else i==13)
 assert g['pack']=='five-friends-48-54'
 rewards=[]
 for st in g['steps']:
  assert st['goals']
  obj=set(z.get('quest') for z in st['goals'] if z['t'] in ('complete','kill','collect','use','interact'))
  turn=set(z.get('quest') for z in st['goals'] if z['t']=='turnin')
  assert not obj & turn,(i,st['title'],obj & turn)
  for z in st['goals']:
   assert z['t']!='task'
   if 'x' in z: assert isinstance(z.get('map'),int) and 0<=z['x']<=100 and 0<=z['y']<=100
   if z['t']=='turnin':rewards.append(z['quest']);seen.append(z['quest'])
 assert set(rewards)==expected[i],(i,sorted(expected[i]-set(rewards)),sorted(set(rewards)-expected[i]))
 assert len(rewards)==len(set(rewards)),i
assert len(seen)==170 and len(set(seen))==170
print('PASS: 13 linked chapters, 170 unique rewards, separate objective and turn-in stages, <=60 steps per chapter.')
