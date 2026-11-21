import ctypes, ctypes.util
from pathlib import Path
lib=ctypes.CDLL(ctypes.util.find_library('lua5.4'))
lib.luaL_newstate.restype=ctypes.c_void_p
lib.luaL_openlibs.argtypes=[ctypes.c_void_p]
lib.luaL_loadstring.argtypes=[ctypes.c_void_p,ctypes.c_char_p]
lib.luaL_loadstring.restype=ctypes.c_int
lib.luaL_loadfilex.argtypes=[ctypes.c_void_p,ctypes.c_char_p,ctypes.c_char_p]
lib.luaL_loadfilex.restype=ctypes.c_int
lib.lua_pcallk.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p]
lib.lua_pcallk.restype=ctypes.c_int
lib.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.POINTER(ctypes.c_size_t)]
lib.lua_tolstring.restype=ctypes.c_void_p
lib.lua_close.argtypes=[ctypes.c_void_p]
L=lib.luaL_newstate();lib.luaL_openlibs(L)
def err():
 z=lib.lua_tolstring(L,-1,None)
 return ctypes.cast(z,ctypes.c_char_p).value.decode('utf-8',errors='replace') if z else 'unknown Lua error'
def exe(code):
 rc=lib.luaL_loadstring(L,code.encode())
 if rc:raise RuntimeError('load: '+err())
 rc=lib.lua_pcallk(L,0,0,0,0,None)
 if rc:raise RuntimeError('run: '+err())
def file(f):
 rc=lib.luaL_loadfilex(L,str(f).encode(),None)
 if rc:raise RuntimeError(f'loadfile {f}: '+err())
 rc=lib.lua_pcallk(L,0,0,0,0,None)
 if rc:raise RuntimeError(f'runfile {f}: '+err())
exe('''Polestar={__pack=nil,__frames=nil,__guides={},
RegisterPack=function(x) assert(x.id=='five-friends-48-54' and x.format==5); Polestar.__pack=x end,
RegisterMapFrames=function(x,id) assert(id=='five-friends-48-54'); Polestar.__frames=x end,
RegisterGuide=function(g)
 assert(type(g.id)=='string' and g.pack=='five-friends-48-54')
 assert(type(g.steps)=='table' and #g.steps>0 and #g.steps<=60)
 for _,s in ipairs(g.steps) do
  assert(type(s.goals)=='table' and #s.goals>0)
  for _,z in ipairs(s.goals) do
   assert(z.t~='task')
   if z.x then assert(z.map and z.x>=0 and z.x<=100 and z.y>=0 and z.y<=100) end
  end
 end
 table.insert(Polestar.__guides,g)
end}''')
base=Path(__file__).resolve().parents[1]/'addon/PolestarPack_FiveFriends4854'
for name in ('Pack.lua','MapFrames.lua','Guides.lua'):
 file(base/name)
 print('EXECUTED',name,(base/name).stat().st_size)
exe('''assert(Polestar.__pack~=nil and Polestar.__frames~=nil)
assert(#Polestar.__guides==13)
local quests={}
local n=0
for i,g in ipairs(Polestar.__guides) do
 assert(g.next==((Polestar.__guides[i+1] or {}).id) or i==13)
 for _,s in ipairs(g.steps) do
  for _,z in ipairs(s.goals) do
   if z.t=='turnin' then
    assert(not quests[z.quest])
    quests[z.quest]=true
    n=n+1
   end
  end
 end
end
assert(n==170)''')
lib.lua_close(L)
print('PASS Lua 5.4: correct pack, frames, 13 guides, 170 rewards, links, no tasks, valid goal coordinates')
