"""Prediction is compared with native engine copies, including spent spells."""
from pathlib import Path
import json
import struct
import pytest
from lupa.luajit21 import LuaRuntime

ROOT=Path(__file__).resolve().parents[1]
NATIVE=json.loads((ROOT/'tests/fixtures/summons/native-273-spent-books.json').read_text())

def table(r,value):
    if isinstance(value,dict):return r.table_from({k:table(r,v)for k,v in value.items()})
    if isinstance(value,list):return r.table_from([table(r,v)for v in value])
    return value

@pytest.fixture
def prediction():
    r=LuaRuntime(unpack_returned_tuples=True)
    r.execute('BfBot={}')
    r.execute((ROOT/'buffbot/BfBotSum.lua').read_text(encoding='utf-8'))
    r.globals().rules=table(r,NATIVE['rules'])
    r.execute('''
      S=BfBot.Summon
      function rule(name,level,column)
        local t=rules[name];if not t then return nil end
        local row=t.rows[tostring(level)]
        return row and tonumber(row[column])or 0
      end
    ''')
    return r

@pytest.mark.parametrize('case',NATIVE['cases'],ids=lambda c:c['name'])
def test_predicted_spells_match_actual_native_simulacrum(prediction,case):
    prediction.globals().case=table(prediction,case)
    assert prediction.execute('''
      local p=assert(S.Predict(case.profile,case.kind,rule))
      for i,l in ipairs(p.levels)do assert(l==case.actualLevels[i])end
      for res,count in pairs(case.actualCounts)do assert((p.counts[res]or 0)==count,res)end
      for res,count in pairs(p.counts)do assert((case.actualCounts[res]or 0)==count,res)end
      return true
    ''')

def test_selection_accounts_for_attacks_before_filtering_buffs(prediction):
    assert prediction.execute('''
      local p={class=3,levels={8},wis=10,books={Priest={
        {{res='BUFF',name='Z buff',flags=1},{res='ATTACK',name='A attack',flags=0}}
      }}}
      local r=assert(S.Predict(p,3,function(name)return name=='MXSPLWIS'and 0 or 1 end))
      return r.counts.BUFF==0 and r.counts.ATTACK==1
    ''')


def test_unnamed_helpers_sort_by_empty_native_name_before_browser_fallback(prediction):
    assert prediction.execute('''
      local p={class=11,levels={20},wis=10,books={Priest={
        {{res='BLESS',name='Bless',flags=1},{res='ZZHELPER',name='ZZHELPER',sortName='',flags=1}}
      }}}
      local result=assert(S.Predict(p,3,function(name)return name=='MXSPLWIS'and 0 or 1 end))
      return result.counts.BLESS==0 and result.counts.ZZHELPER==1
    ''')

def test_multiclass_reduction_applies_drain_to_each_class(prediction):
    assert prediction.execute('''
      local l=assert(S.CloneLevels({class=10,levels={12,12,14}},3))
      return l.drain==5 and l.levels[1]==7 and l.levels[2]==7 and l.levels[3]==9
    ''')

def test_dual_class_can_lose_access_to_original_spellcasting_class(prediction):
    assert prediction.execute('''
      local l=assert(S.CloneLevels({class=7,flags=16,levels={15,13}},3))
      return l.drain==6 and l.levels[1]==9 and l.levels[2]==13
        and l.usable[1]==nil and l.usable[2]==9
    ''')

def test_dual_class_preserves_regained_original_class_when_still_high_enough(prediction):
    assert prediction.execute('''
      local l=assert(S.CloneLevels({class=7,flags=16,levels={25,13}},3))
      return l.drain==10 and l.usable[1]==13 and l.usable[2]==15
    ''')

def test_missing_rules_report_uncertainty_instead_of_inventing_spells(prediction):
    assert prediction.execute('''
      local p,why=S.Predict({class=3,levels={8},books={Priest={{{res='X',flags=1}}}}},3,
        function()return nil end)
      return p==nil and why:find('rules unavailable',1,true)~=nil
    ''')

def test_spontaneous_choices_share_level_capacity_without_competing_by_name(prediction):
    assert prediction.execute('''
      local entries={}
      for _,res in ipairs({'A','B'})do for i=1,12 do entries[#entries+1]={res=res,flags=i>1 and 1 or 0}end end
      local p=assert(S.Predict({class=19,levels={9},books={Mage={entries}}},3,rule))
      return p.counts.A==6 and p.counts.B==6
    ''')


def test_spontaneous_copy_rebuilds_uses_instead_of_truncating_memorized_duplicates(prediction):
    assert prediction.execute('''
      local p={class=21,levels={20},books={Priest={{{res='BUFF',flags=0}}}}}
      local result=assert(S.Predict(p,3,function(name,level,column)
        assert(name=='MXSPLSHM'and level==12 and column==1);return 6
      end))
      return result.counts.BUFF==6 and #result.books.Priest[1]==6
    ''')


def test_spontaneous_image_preserves_actual_available_pool_including_zero(prediction):
    assert prediction.execute('''
      local p={class=21,levels={20},availableCounts={A=5,B=0},books={Priest={
        {{res='A',flags=1},{res='B',flags=1}}}}}
      local result=assert(S.Predict(p,2))
      return result.counts.A==5 and result.counts.B==0
    ''')


@pytest.mark.parametrize('cls,kit,expected,rule_name', [
    (19, 0x4023, 4, 'MXSPLDD'),
    (1, 0x4001, 3, 'MXSPLWIZ'),
    (1, 0x0400, 4, 'MXSPLWIZ'),
    (1, 0x80000000, 4, 'MXSPLWIZ'),
])
def test_arcane_kit_slot_rules_include_the_native_dd_bonus(prediction, cls, kit, expected, rule_name):
    prediction.globals().class_id=cls
    prediction.globals().kit_id=kit
    prediction.globals().wanted_rule=rule_name
    assert prediction.execute('''
      local p={class=class_id,kit=kit_id,levels={20},books={}}
      local levels=assert(S.CloneLevels(p,3))
      return S.Capacity(p,levels,'Mage',1,function(name)
        assert(name==wanted_rule);return 3
      end)
    ''') == expected


def test_copy_book_reduction_does_not_refill_equipment_bonus_slots(prediction):
    # Native Illusionist + RING08: the copy retains the ring effects, but the
    # surviving prepared book matches base/kit capacity, not the extra slots.
    assert prediction.execute(''' 
      local p={class=1,kit=1024,levels={20},slotEffects={
        {opcode=42,amount=1,flags=16},{opcode=42,amount=1,flags=32}}}
      local levels=assert(S.CloneLevels(p,3))
      return S.Capacity(p,levels,'Mage',5,function()return 1 end)==2
    ''')


def test_profile_and_preview_keep_live_catalog_caster_level_bonus(prediction):
    assert prediction.execute('''
      local empty={};local mem={m_spellId={get=function()return 'BUFF'end},m_flags=1}
      local lists={getReference=function(_,level)return level==0 and {mem}or empty end}
      local sprite={m_typeAI={m_Class=3},m_baseStats={m_flags=0},
        getStat=function()return 16384 end,m_memorizedSpellsPriest=lists,
        m_memorizedSpellsMage={getReference=function()return empty end},
        m_memorizedSpellsInnate={getReference=function()return empty end}}
      EEex_Sprite_GetActiveStats=function()return {m_nLevel1=18,m_nLevel2=0,m_nLevel3=0,
        m_nWIS=18,GetAverageLevel=function()return 18 end}end
      EEex_Utility_IterateCPtrList=function(list,fn)for _,e in ipairs(list)do fn(e)end end
      BfBot.Scan={GetCastableSpells=function()return {BUFF={name='Buff',casterLevel=20}}end,
        DescribeSpell=function(res,level)return {resref=res,name='Fallback',casterLevel=level}end}
      EEex_Resource_Demand=function()return {itemType=2}end
      local p=assert(S.ReadProfile(sprite));assert(p.casterLevels.BUFF==20)
      local predicted=assert(S.Predict(p,3,rule))
      local rows=S.BuildRows(p,predicted)
      return predicted.levels[1]==11 and rows.BUFF.casterLevel==13 and rows.BUFF.count==1
    ''')

def test_creation_discovery_follows_item_children_and_planetar_effect_files(prediction):
    assert prediction.execute('''
      BfBot._fields={fb_opcode='op',fb_param2='kind',fb_res='res'}
      local resources={}
      local function spell(key,effects,global)
        local a={effects=effects};local h={getAbilityForLevel=function()return a end,
          global=global,castingStartingEffect=0,castingEffectCount=global and #global or 0}
        resources[key]=h;return h,a
      end
      local item,ability=spell('ITM:HELM',{{op=146,res='IMAGE'}})
      spell('SPL:IMAGE',{{op=236,kind=3}})
      spell('SPL:PLANETAR',{},{{op=177,res='PLANEFF'}})
      resources['EFF:PLANEFF']={m_effectId=67,m_res='PLANGOOD'}
      BfBot.Scan={_GetItemAbility=function()return ability end}
      BfBot.Class={_IterateFeatureBlocks=function(h,a,fn)
        for _,e in ipairs(a.effects or h.global or {})do fn(e)end
      end}
      EEex_Resource_Demand=function(res,kind)return resources[kind..':'..res]end
      local helm=S.Discover({kind='itm',itemResref='HELM',abilityIdx=0})
      local planetar=S.Discover({kind='spl',resref='PLANETAR'})
      return #helm==1 and helm[1].image==3 and #planetar==1
        and planetar[1].resource=='PLANGOOD'
    ''')

def test_creation_discovery_stops_at_resource_cycles(prediction):
    assert prediction.execute('''
      BfBot._fields={fb_opcode='op',fb_param2='kind',fb_res='res'}
      local a={};local h={getAbilityForLevel=function()return a end}
      local visits=0
      BfBot.Class={_IterateFeatureBlocks=function(_,_,fn)
        visits=visits+1;fn({op=146,res='LOOP'})
      end}
      EEex_Resource_Demand=function()return h end
      local result=S.Discover({kind='spl',resref='LOOP'})
      return #result==0 and visits==1
    ''')

@pytest.mark.parametrize('bad',['offset','count','index','signature',None])
def test_creature_books_read_only_validated_sections(prediction,bad):
    data=bytearray(0x2D4+16+24)
    data[:8]=b'CRE V1.0'
    data[0x273]=3;data[0x234]=18;data[0x23B]=21
    struct.pack_into('<IIII',data,0x2A8,0x2D4,1,0x2D4+16,2)
    struct.pack_into('<HHHHII',data,0x2D4,0,2,2,0,0,2)
    for i,res in enumerate([b'SPPR101',b'SPPR101']):
        struct.pack_into('<8sI',data,0x2D4+16+i*12,res,1)
    if bad=='offset':struct.pack_into('<I',data,0x2B0,len(data)-4)
    if bad=='count':struct.pack_into('<I',data,0x2B4,90000)
    if bad=='index':struct.pack_into('<I',data,0x2D4+8,99)
    if bad=='signature':data[:8]=b'CRE V9.9'
    r=prediction
    r.globals().EEex_ReadU8=lambda p:data[p]
    r.globals().EEex_ReadU16=lambda p:struct.unpack_from('<H',data,p)[0]
    r.globals().EEex_ReadU32=lambda p:struct.unpack_from('<I',data,p)[0]
    r.globals().resource_size=len(data)
    r.execute('''
      EEex_Resource_Fetch=function()return {nSize=resource_size,Demand=function()return 1 end}end
      EEex_UDToPtr=function()return 0 end
      BfBot.Scan={DescribeSpell=function(res)return {name=res}end}
    ''')
    if bad:
        assert r.execute("return S.ReadCreature('PLANETAR')==nil")
    else:
        assert r.execute('''
          local p=assert(S.ReadCreature('PLANETAR'))
          return p.class==3 and p.levels[1]==18 and p.wis==21
            and #p.books.Priest[1]==2 and p.books.Priest[1][1].res=='SPPR101'
        ''')
