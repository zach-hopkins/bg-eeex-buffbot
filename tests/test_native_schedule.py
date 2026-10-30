"""Shared scheduling uses real game-time constraints, not effect aging."""
from pathlib import Path
import pytest
from lupa.luajit21 import LuaRuntime

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture
def schedule():
    r=LuaRuntime(unpack_returned_tuples=True)
    r.execute('BfBot={}')
    r.execute((ROOT/'buffbot/BfBotTim.lua').read_text(encoding='utf-8'))
    r.execute('T=BfBot.Timing')
    return r

def test_short_caster_finishes_with_long_caster_without_extending_plan(schedule):
    assert schedule.execute('''
      local jobs={{id='haste',caster='Nalia',release=15},{id='invis',caster='Nalia',release=15}}
      for i=1,7 do jobs[#jobs+1]={id='cleric'..i,caster='Anomen',release=15}end
      local s=assert(T.Solve(jobs))
      return s.finish==555 and s.jobs.haste.start==450 and s.jobs.invis.finish==555
        and s.jobs.cleric1.start==0 and s.jobs.cleric7.finish==555
        and s.jobs.haste.age==90
    ''')

def test_targeted_buffs_precede_invisibility_even_when_that_extends_a_lane(schedule):
    assert schedule.execute('''
      local s=assert(T.Solve({
        {id='armor',caster='Anomen',release=45},
        {id='invis',caster='Nalia',release=15,after={'armor'}},
      }))
      return s.jobs.armor.finish==45 and s.jobs.invis.start==45 and s.finish==60
    ''')

def test_future_caster_waits_for_creation_but_independent_work_does_not(schedule):
    assert schedule.execute('''
      local s=assert(T.Solve({
        {id='summon',caster='Anomen',release=60},
        {id='clone',caster='image',release=30,after={{id='summon',lag=5}}},
        {id='independent',caster='Nalia',release=90},
      }))
      return s.finish==95 and s.jobs.summon.start==0 and s.jobs.clone.start==65
        and s.jobs.independent.start==5
    ''')

def test_replanning_after_a_skip_shortens_unstarted_waits(schedule):
    assert schedule.execute('''
      local before=assert(T.Solve({{id='short',caster='A',release=15},{id='long',caster='B',release=90}}))
      local after=assert(T.Solve({{id='short',caster='A',release=15}},20))
      return before.jobs.short.start==75 and after.jobs.short.start==20 and after.finish==35
    ''')

def test_observed_cast_is_never_shifted_when_remaining_work_is_rescheduled(schedule):
    assert schedule.execute('''
      local s=assert(T.Solve({
        {id='done',caster='A',release=15,fixedStart=0,fixedFinish=15},
        {id='pending',caster='A',release=15},
        {id='other',caster='B',release=150},
      },30))
      return s.jobs.done.start==0 and s.jobs.pending.start==165 and s.jobs.other.start==30 and s.finish==180
    ''')

def test_aura_cleansing_and_native_casting_time_change_lane_duration(schedule):
    assert schedule.execute('''
      local s=assert(T.Solve({{caster='A',release=10,aura=true},{caster='A',release=20,aura=true}}))
      return s.finish==30 and T.ReleaseTicks(0)==1 and T.ReleaseTicks(5)==46
    ''')

@pytest.mark.parametrize('jobs',[
    "{{id='a',after={'missing'}}}",
    "{{id='a',after={'b'}},{id='b',after={'a'}}}",
    "{{id='a'},{id='a'}}",
    "{{release=0/0}}",
    "{{release=10,duration=5}}",
    "{{notBefore='later'}}",
    "{{notBefore=-1}}",
])
def test_invalid_or_cyclic_dependencies_fail_without_running_anything(schedule,jobs):
    assert schedule.execute('local s,why=T.Solve('+jobs+');return s==nil and type(why)=="string"')
