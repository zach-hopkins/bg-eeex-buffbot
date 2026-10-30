"""Exercise the real executor with native actions replaced by a deterministic clock."""
from pathlib import Path
import pytest
from test_runtime_compatibility import exec_lua

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture
def execution(exec_lua):
    r=exec_lua
    r.execute((ROOT/'buffbot/BfBotTim.lua').read_text(encoding='utf-8'))
    r.execute('''
      E=BfBot.Exec;T=BfBot.Timing;clock=0;actions={};skipLong=false
      local rows={SHORT={resref='SHORT',kind='spl',name='SHORT',count=20,class={}},
                  LONG={resref='LONG',kind='spl',name='LONG',count=20,class={}}}
      sprites=BfBot_TestQueueWorld(rows,2)
      E._GetGameTime=function()return clock end
      E._ResolveCaster=function(ref)return sprites[ref.slot+1]end
      E._ResolveCasterForStep=function(c)return E._ResolveCaster(c.ref)end
      E._IsStateStale=function()return false end
      E._DetectCombat=function()return false end
      E._StripCheatBuffs=function()end
      E.GetForceMode=function()return 2 end
      E._CheckEntry=function(e)
        if skipLong and e.resref=='LONG'then E._skipCount=E._skipCount+1;return false end
        return true
      end
      EEex_Action_QueueResponseStringOnAIBase=function(action,sprite)
        if action:find('SpellRES',1,true)then actions[#actions+1]={time=clock,caster=sprite.name}end
      end
      function queue(smart)
        local q={}
        for caster=0,1 do for i=1,(caster==0 and 7 or 2)do
          q[#q+1]={caster=caster,spell=caster==0 and 'LONG'or'SHORT',target='self',
            smartTiming=smart,timing={release=15},planIndex=#q+1}
        end end
        return q
      end
    ''')
    return r

def test_real_executor_delays_short_lane_to_finish_with_long_lane(execution):
    assert execution.execute('''
      assert(E.Start(queue(true),0))
      assert(#actions==1 and actions[1].caster=='A')
      for i=0,6 do
        clock=i*90;T.Pump()
        if i==5 then assert(actions[#actions].time==450)end
        clock=i*90+15;E._Advance('p0')
        if i>=5 then E._Advance('p1')end
      end
      local b={};for _,a in ipairs(actions)do if a.caster=='B'then b[#b+1]=a.time end end
      return E._state=='done' and E._castCount==9 and #b==2 and b[1]==450 and b[2]==540
        and T.run==nil and #T.lastAudit>9
    ''')

def test_custom_mode_keeps_immediate_parallel_native_dispatch(execution):
    assert execution.execute('''
      assert(E.Start(queue(false),0))
      return #actions==2 and actions[1].time==0 and actions[2].time==0 and T.run==nil
    ''')

def test_unavailable_long_lane_does_not_leave_short_lane_waiting(execution):
    assert execution.execute('''
      skipLong=true;assert(E.Start(queue(true),0))
      return #actions==1 and actions[1].caster=='B' and actions[1].time==0
        and E._skipCount==7
    ''')

def test_pause_freezes_scheduled_wait_and_stop_cannot_restart_it(execution):
    assert execution.execute('''
      assert(E.Start(queue(true),0))
      for i=1,500 do T.Pump()end
      assert(#actions==1)
      E.Stop();clock=1000;T.Pump()
      return #actions==1 and T.run==nil and E._state~='running'
    ''')

def test_dependency_waits_for_actual_completion_not_estimated_finish(execution):
    assert execution.execute('''
      local q=queue(true)
      q={q[1],q[8]};q[1].plannedActor='A';q[1].plannedTarget='B'
      q[1].target=2;q[2].plannedActor='B';q[2].plannedTarget='B';q[2].invisibilityTarget='B'
      assert(E.Start(q,0));clock=60;T.Pump()
      assert(#actions==1)
      E._Advance('p0');T.Pump()
      return #actions==2 and actions[2].time==60
    ''')

def test_old_engine_completion_cannot_advance_a_replacement_run(execution):
    assert execution.execute('''
      assert(E.Start(queue(true),0));local old=E._casters.p0.advanceToken
      E.Stop();assert(E.Start(queue(true),0))
      local current=E._casters.p0.advanceToken
      E._Advance('p0',old)
      return old~=current and E._casters.p0.index==1 and E._casters.p0.advanceToken==current
    ''')

def test_duplicate_completion_cannot_skip_the_next_scheduled_spell(execution):
    assert execution.execute('''
      assert(E.Start(queue(true),0));local token=E._casters.p0.advanceToken
      clock=15;E._Advance('p0',token);assert(E._casters.p0.index==2)
      E._Advance('p0',token)
      return E._casters.p0.index==2 and #actions==1
    ''')


def test_pending_schedule_refreshes_speed_and_aura_without_rescanning_books(execution):
    assert execution.execute('''
      local speed=0;local aura=0;local reads=0
      EEex_Sprite_GetActiveStats=function()
        reads=reads+1;return {m_bAuraCleansing=aura,m_nCastingType=0,m_nMentalSpeed=speed}
      end
      BfBot.Plan={CastingSegments=function(raw,kind,bonus)return math.max(0,raw-bonus)end}
      local q=queue(true)
      for _,e in ipairs(q)do e.timing.rawSegments=5;e.timing.release=46 end
      assert(E.Start(q,0));clock=15;T.Refresh(clock)
      local first=reads;T.Refresh(clock);assert(reads==first)
      speed=4;aura=1;clock=30;T.Refresh(clock)
      local pending=0
      for _,n in ipairs(T.run.nodes)do if not n.started then
        assert(n.release==10 and n.aura);pending=pending+1
      end end
      aura=0;speed=0;clock=45;T.Refresh(clock)
      for _,n in ipairs(T.run.nodes)do if not n.started then assert(n.release==46 and not n.aura)end end
      return pending==8 and reads==first+4
    ''')


def test_disappearing_caster_counts_only_unissued_work_as_skipped(execution):
    assert execution.execute('''
      assert(E.Start(queue(false),0))
      local c=E._casters.p0;E._FinishGoneCaster(c);E._FinishGoneCaster(c)
      return E._skipCount==6 and E._castCount==2 and E._activeCasters==1
    ''')


def test_watchdog_counts_remaining_work_without_double_counting_attempts(execution):
    assert execution.execute('''
      assert(E.Start(queue(false),0));E._ForceComplete('test stall')
      return E._skipCount==7 and E._castCount==2 and E.GetState()=='done'
    ''')
