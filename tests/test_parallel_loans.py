"""Recipient-plan loans hold only the two actors needed for a physical handoff."""
from pathlib import Path
import pytest
from test_scheduled_execution import execution
from test_runtime_compatibility import exec_lua

ROOT=Path(__file__).resolve().parents[1]


def test_world_reset_discards_transient_loan_but_preserves_loaded_return_journal(parallel_loan):
    assert parallel_loan.execute('''
      local S=BfBot.Share
      state.transfer={item='BOOT12',owner='A',borrower='B',pack=22}
      S.liveLoan={phase='receiving'};S.waiters={p1=1};S.run={phase='receiving'}
      E._HardReset()
      return S.liveLoan==nil and S.run==nil and next(S.waiters)==nil
        and state.transfer.item=='BOOT12'and E._state=='idle'
    ''')

@pytest.fixture
def parallel_loan(execution):
    r=execution
    r.execute('''
      state={};busy={};itemUses={};area={}
      sprites[3]={name='C',m_id=102,m_baseStats={m_generalState=0}}
      for i,a in ipairs(sprites)do
        a.slot=i-1;a.items={};a.m_pArea=area
        a.m_equipment={m_items={get=function(_,n)return a.items[n]end}}
      end
      sprites[1].items[22]={pRes={resref={get=function()return 'BOOT12'end}},m_flags=1,
        m_wear=7,m_useCount1=2,m_useCount2=0,m_useCount3=0}
      EEex_Sprite_GetInPortrait=function(slot)return sprites[slot+1]end
      EEex_Sprite_GetCharacterIndex=function(a)return a.slot end
      EEex_UDToPtr=function()return 100 end
      Infinity_GetClockTicks=function()return clock*100 end
      EEex_Trigger_EvalConditionalStringAsAIBase=function(_,a)return not busy[a.name]end
      BfBot.Plan={ActorKey=function(a)return a.name end,GetState=function()return state end}
      BfBot.Persist.GetItemSwap=function()return nil end
      BfBot.Scan.InvalidateAll=function()end
      BfBot.Scan._NativeCanWearItem=function()return true end
      BfBot.Scan._NativeMoveToBackpack=function(a,src,dest)
        assert(a.items[src]and not a.items[dest]);a.items[dest]=a.items[src];a.items[src]=nil;return true
      end
      BfBot.Scan.GetCastableSpells=function(a)
        local rows={LONG={name='Long',kind='spl',count=3,class={}},SHORT={name='Short',kind='spl',count=3,class={}}}
        for _,it in pairs(a.items)do
          rows.BOOT12={name='Boots',kind='itm',count=it.m_useCount1,itemResref='BOOT12',abilityIdx=0,class={}}
        end
        return rows
      end
      EEex_Action_QueueResponseStringOnAIBase=function(action,a)
        local res,who=action:match('GiveItem%("([%w_]+)",Player(%d)%)')
        if res then
          local dest=sprites[tonumber(who)]
          for slot,it in pairs(a.items)do if it.pRes.resref:get()==res then
            for n=18,33 do if not dest.items[n]then dest.items[n]=it;a.items[slot]=nil;return end end
          end end
          error('missing transfer item')
        elseif action:find('SpellRES',1,true)then
          actions[#actions+1]={caster=a.name,time=clock};busy[a.name]=true
        end
      end
      E._QueueItem=function(_,_,entry,_,a)
        local it=a.items[entry.plannedItemSlot];assert(it)
        it.m_useCount1=it.m_useCount1-1;E._castCount=E._castCount+1
        itemUses[#itemUses+1]={caster=a.name,time=clock};busy[a.name]=true
        return true
      end
      function loanQueue()
        return {
          {caster=0,spell='LONG',target='self',plannedActor='A',plannedTarget='A',planIndex=1},
          {caster=1,spell='BOOT12',target='self',plannedActor='B',plannedTarget='B',planIndex=2,
            itemOwner='A',sharedItem='BOOT12',plannedItemSlot=22,plannedCasterName='B'},
          {caster=2,spell='SHORT',target='self',plannedActor='C',plannedTarget='C',planIndex=3},
          {caster=0,spell='SHORT',target='self',plannedActor='A',plannedTarget='A',planIndex=4},
          {caster=1,spell='SHORT',target='self',plannedActor='B',plannedTarget='B',planIndex=5},
        }
      end
      function loanTick()clock=clock+1;BfBot.Share.lastPoll=nil;BfBot.Share.Tick()end
    ''')
    r.execute((ROOT/'buffbot/BfBotShr.lua').read_text(encoding='utf-8'))
    return r

def test_physical_loan_does_not_fence_independent_casters(parallel_loan):
    assert parallel_loan.execute('''
      local S=BfBot.Share;assert(E.Start(loanQueue(),0))
      assert(#actions==2 and actions[1].caster=='A'and actions[2].caster=='C')
      loanTick();assert(S.liveLoan.phase=='request'and not state.transfer)
      clock=15;busy.A=false;E._Advance('p0');busy.C=false;E._Advance('p2')
      loanTick();assert(state.transfer and S.liveLoan.phase=='receiving')
      loanTick();assert(#itemUses==1 and itemUses[1].caster=='B'and #actions==2)
      busy.B=false;E._Advance('p1');assert(S.liveLoan.phase=='return')
      loanTick();loanTick();loanTick()
      assert(not S.liveLoan and not state.transfer and sprites[1].items[22].m_useCount1==1)
      assert(#actions==4 and E._castCount==5)
      busy.A=false;E._Advance('p0');busy.B=false;E._Advance('p1')
      return E._state=='done'and E._skipCount==0 and not next(sprites[2].items)
    ''')

def test_stop_during_native_loan_returns_without_spending_a_charge(parallel_loan):
    assert parallel_loan.execute('''
      local S=BfBot.Share;local q=loanQueue();q={q[2]};assert(E.Start(q,0))
      loanTick();assert(state.transfer and S.liveLoan.phase=='receiving')
      E.Stop();loanTick();loanTick();loanTick()
      return E._state=='stopped'and not S.liveLoan and not state.transfer
        and sprites[1].items[22].m_useCount1==2 and #itemUses==0
    ''')
