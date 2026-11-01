"""Exercise the built-in Lua 5.2 path with no file or native-call libraries."""
from pathlib import Path

import pytest
from lupa.lua52 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]


def source(name):
    return (ROOT / 'buffbot' / name).read_text(encoding='utf-8')


def builtin():
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute('io=nil; os=nil; package=nil; require=nil; jit=nil; bit=bit32; BfBot={_noIO=true,_noLuaJIT=true}')
    lua.execute('Infinity_DisplayString=function()end')
    lua.execute(source('BfBotCor.lua'))
    return lua


def test_complete_bootstrap_loads_with_builtin_lua52_and_no_file_libraries():
    lua = builtin()
    lua.execute('''
      EEex_Active=true; bit=nil; listeners={}; marshalHandlers={}
      function EEex_Menu_AddAfterMainFileLoadedListener(f)listeners[#listeners+1]=f end
      function EEex_Sprite_AddMarshalHandlers(name,save,restore)
        marshalHandlers[name]={save=save,restore=restore}
      end
      function EEex_GameState_AddDestroyedListener(...)end
      function EEex_Sprite_AddLoadedListener(...)end
    ''')
    lua.globals().Infinity_DoFile = lambda name: lua.execute(source(name + '.lua'))
    lua.execute(source('M_BfBot.lua'))
    assert lua.eval('BfBot._noIO and BfBot._noLuaJIT and bit==bit32')
    assert lua.eval('marshalHandlers.BuffBotParty~=nil')
    assert lua.eval('BfBot.PartyUI~=nil and BfBot.Visual~=nil and BfBot.Fast~=nil')
    assert lua.eval('not BfBot.Scan.NativeBackpackMovesAvailable()')


@pytest.mark.parametrize('path', sorted((ROOT / 'buffbot').glob('*.lua')), ids=lambda p: p.name)
def test_all_modules_compile_in_builtin_lua52(path):
    lua = builtin()
    compile_chunk = lua.eval('function(s) local f,err=load(s); assert(f,err) end')
    compile_chunk(path.read_text(encoding='utf-8'))


@pytest.mark.parametrize('catalog', sorted((ROOT / 'buffbot/lang').glob('*/setup.tra')), ids=lambda p: p.parent.name)
def test_embedded_translation_works_without_io_and_remains_inert(catalog):
    lua = builtin()
    text = catalog.read_text(encoding='utf-8')
    assert ']====]' not in text
    text += '\n@305 = ~"; injected=true; --~\n'
    lua.execute(source('BfBotLoc.lua').replace('local _installedCatalog = nil', 'local _installedCatalog = [====['+text+']====]'))
    from tests.test_localization import parse_tra
    entries, _ = parse_tra(catalog)
    assert lua.eval('BfBot.L10N.Get("common.party")') == entries[301]
    assert lua.eval('injected') is None


def test_nojit_never_probes_native_inventory_or_offers_borrowed_sources():
    lua = builtin()
    lua.execute(source('BfBotScn.lua'))
    lua.execute(source('BfBotShr.lua'))
    lua.execute('''
      EEex_GetImageBase=function()error('native probe must not run')end
      assert(not BfBot.Scan.NativeBackpackMovesAvailable())
      assert(BfBot.Scan._NativeCanWearItem({}, {})==nil)
      assert(not BfBot.Scan._NativeMoveToBackpack({},18,19))
      local snapshot={groups={G={sources={{id='owner'}}}}}
      BfBot.Share.AddSources(snapshot)
      assert(#snapshot.groups.G.sources==1)
      assert(not BfBot.Share.CanBorrow({row={}},{}))
      assert(not BfBot.Share.Start({{itemOwner='owner'}},0))
      local entry,why=BfBot.Share.MaterializeLoan('p0',{}, {})
      assert(entry==nil and why=='item sharing requires LuaJIT')
      assert(BfBot.Share.run==nil and BfBot.Share.liveLoan==nil)
    ''')


def test_builtin_core_keeps_planning_and_save_serialization_without_file_io():
    lua = builtin()
    for name in ('BfBotLoc.lua','BfBotPer.lua','BfBotTim.lua','BfBotPln.lua','BfBotIO.lua'):
        lua.execute(source(name))
    lua.execute('''
      BfBot._OpenLog(); assert(not BfBot._OpenLogAppend())
      local snap={actors={A={name='A',alive=true,slot=0}},
        order={},groups={BUFF={name='Buff',sources={{id='s',actor='A',casterName='A',
          slot=0,duration=60,pool='spell',row={resref='BUFF',kind='spl'}}}}},pools={spell=1}}
      local requests={{group='BUFF',target='A',on=1}}
      local queue=BfBot.Plan.BuildQueue(snap,requests)
      assert(#queue==1)
      local cfg={requests=requests}
      local copy=BfBot.Persist._MarshalSafeCopy(cfg)
      assert(copy.requests[1].group=='BUFF')
      assert(not BfBot.PlanIO.Export({}))
      assert(#BfBot.PlanIO.List()==0)
    ''')
