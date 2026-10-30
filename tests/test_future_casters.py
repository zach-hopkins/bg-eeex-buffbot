"""The real executor keeps independent work running while a planned caster spawns."""
from pathlib import Path
import pytest
from test_scheduled_execution import execution
from test_runtime_compatibility import exec_lua
from test_party_planner import lua

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture
def future_execution(execution):
    r=execution
    r.execute((ROOT/'buffbot/BfBotSum.lua').read_text(encoding='utf-8'))
    r.execute('''
      S=BfBot.Summon;spawned=false
      clone={name='Clone A',m_id=200,m_resref={get=function()return 'CLONE'end}}
      BfBot.Plan={ActorKey=function(a)return a.name end,CasterKey=function()return 'clone:A'end,
        EstimateCast=function()return {release=15}end}
      E._ResolveCaster=function(ref)
        if ref.kind=='party'then return sprites[ref.slot+1]end
        if ref.kind=='summon'and spawned and ref.oid==200 then return clone end
      end
      E._ResolveCasterForStep=function(c)return E._ResolveCaster(c.ref)end
      BfBot.Scan.InvalidateSummons=function()end
      BfBot.Scan.GetAlliedSummons=function()
        return spawned and {{oid=200,name='Clone A'}}or {}
      end
      BfBot.Scan._ReadSummonOrigin=function()return {kind='clone',cloneType=3,ownerId=100}end
      function futureQueue()
        local q=queue(false)
        return {q[1],{spell='SHORT',target=2,plannedTarget='B',plannedActor='future:A',
          planIndex=2,providerPlanIndex=1,plannedCasterName='A — Simulacrum (planned)',
          spellName='SHORT',timing={release=15},future={kind='clone',image=3,owner='A',key='future:A',exclude={}}},
          {caster=1,spell='SHORT',target='self',planIndex=3,plannedActor='B',plannedTarget='B'}}
      end
    ''')
    return r

def test_deferred_source_uses_actual_spawn_without_blocking_independent_caster(future_execution):
    assert future_execution.execute('''
      assert(E.Start(futureQueue(),0));assert(#actions==2)
      clock=15;E._Advance('p0');E._Advance('p1')
      assert(E._state=='running'and E._activeCasters==1)
      clock=18;spawned=true;S.Pump()
      assert(#actions==3 and actions[3].caster=='Clone A'and actions[3].time==18)
      clock=33;E._Advance('f1')
      local bound=false;for _,a in ipairs(T.lastAudit)do if a.event=='summon bound'then bound=true end end
      return E._state=='done'and E._castCount==3 and E._skipCount==0 and bound
    ''')

def test_failed_creation_skips_only_its_dependent_casts(future_execution):
    assert future_execution.execute('''
      skipLong=true;assert(E.Start(futureQueue(),0));assert(#actions==1 and actions[1].caster=='B')
      clock=1;S.Pump();assert(E._skipCount==2)
      clock=15;E._Advance('p1')
      return E._state=='done'and E._castCount==1 and E._skipCount==2
    ''')

def test_missing_spawn_has_bounded_game_time_wait_and_does_not_finish_prematurely(future_execution):
    assert future_execution.execute('''
      assert(E.Start(futureQueue(),0));clock=15;E._Advance('p0');E._Advance('p1')
      for i=1,100 do S.Pump()end
      assert(E._state=='running'and E._skipCount==0)
      clock=241;S.Pump()
      return E._state=='done'and E._skipCount==1 and E._castCount==2
    ''')

def test_spawn_with_wrong_owner_cannot_supply_the_planned_book(future_execution):
    assert future_execution.execute('''
      assert(E.Start(futureQueue(),0));clock=15;E._Advance('p0');E._Advance('p1')
      BfBot.Scan._ReadSummonOrigin=function()return {kind='clone',cloneType=3,ownerId=999}end
      spawned=true;clock=18;S.Pump();assert(#actions==2)
      clock=241;S.Pump()
      return E._state=='done'and E._skipCount==1
    ''')

def test_preexisting_spawn_is_not_reused_as_a_new_resource_budget(future_execution):
    assert future_execution.execute('''
      local q=futureQueue();q[2].future.exclude={200}
      assert(E.Start(q,0));clock=15;E._Advance('p0');E._Advance('p1')
      spawned=true;clock=18;S.Pump();assert(#actions==2)
      clock=241;S.Pump()
      return E._skipCount==1 and E._state=='done'
    ''')


@pytest.mark.parametrize('stop', [False, True])
def test_summon_ai_guard_is_scoped_and_restored(future_execution, stop):
    future_execution.globals().stop_early = stop
    assert future_execution.execute('''
      clone.m_bNoInterrupt=0
      EEex_GameObject_Get=function(id)if id==200 then return clone end end
      EEex_GameObject_IsSprite=function()return true end
      EEex_GameObject_CastUserType=function(a)return a end
      assert(E.Start(futureQueue(),0));clock=15;E._Advance('p0');E._Advance('p1')
      spawned=true;clock=18;S.Pump();assert(clone.m_bNoInterrupt==1)
      if stop_early then E.Stop()else clock=33;E._Advance('f1')end
      return clone.m_bNoInterrupt==0 and E._casters.f1.aiGuard==nil
    ''')

@pytest.fixture
def predicted_plan(lua):
    r=lua
    r.execute((ROOT/'buffbot/BfBotSum.lua').read_text(encoding='utf-8'))
    r.execute('''
      S=BfBot.Summon
      S.ReadProfile=function()return {class=3,levels={20},books={}}end
      S.Predict=function()return {}end
      S.BuildRows=function()return {
        BUFF={resref='BUFF',kind='spl',name='Buff',count=2,duration=600,casterLevel=12,
          isSelfOnly=0,isAoE=0,class={isBuff=true}},
        SELF={resref='SELF',kind='spl',name='Self buff',count=1,duration=600,
          isSelfOnly=1,isAoE=0,class={isBuff=true}}}
      end
      S.Creators=function(row)return row.resref=='CREATE'and {{kind='clone',image=3}}or {}end
      function futurePlan(available)
        local s=snapshot();s.casters={};s.casterActors={}
        for _,a in pairs(s.actors)do
          a.key=a.name;a.sprite={m_id=a.slot+100};a.controlled=true;a.class=3;a.rows={}
          a.casterRef={kind='party',slot=a.slot};s.casters[#s.casters+1]=a;s.casterActors[a.key]=a
        end
        local create=source(s,'CREATE','A',600,'creation',available)
        create.selfOnly=true;create.row.name='Create';create.row.kind='spl'
        create.row.casterLevel=20;create.fullCount=1
        local preset={requests={request('CREATE','A','A')},orderMode='custom'}
        S.AddSources(s,preset,{})
        return s,preset
      end
    ''')
    return r

def test_prediction_does_not_require_a_previous_cast_and_summons_are_only_casters(predicted_plan):
    assert predicted_plan.execute('''
      local s,preset=futurePlan(1)
      local group=s.groups['spl:BUFF'];local src=assert(group.sources[1])
      return src.future.image==3 and src.providerRequest==preset.requests[1]
        and s.pools[src.pool]==2 and not s.groups['spl:SELF']and not s.actors[src.actor]
    ''')

def test_spent_creator_preserves_ordering_metadata_without_inventing_live_uses(predicted_plan):
    assert predicted_plan.execute('''
      local s=futurePlan(0);local src=assert(s.groups['spl:BUFF'].sources[1])
      return s.pools[src.pool]==0 and P.OrderSnapshot(s).pools[src.pool]==2
    ''')

@pytest.mark.parametrize('mode',['smart','long'])
def test_creation_precedes_its_buffs_in_automatic_order(predicted_plan,mode):
    predicted_plan.globals().mode=mode
    assert predicted_plan.execute('''
      local s,preset=futurePlan(1);local src=s.groups['spl:BUFF'].sources[1]
      local create=preset.requests[1];local child=request('spl:BUFF','B',src.actor)
      preset.requests={child,create};preset.orderMode=mode
      local sorted=P.SortRequests(s,preset.requests,mode)
      return sorted[1]==create and sorted[2]==child
    ''')

def test_custom_movement_cannot_put_summon_buffs_before_creation(predicted_plan):
    assert predicted_plan.execute('''
      local s,preset=futurePlan(1);local src=s.groups['spl:BUFF'].sources[1]
      local create=preset.requests[1];local child=request('spl:BUFF','B',src.actor)
      preset.requests={child,create};assert(not P.OrderAllowed(s,preset.requests))
      assert(P.EnsureDependencies(s,preset))
      return preset.requests[1]==create and P.OrderAllowed(s,preset.requests)
    ''')

def test_project_image_and_owner_reserve_one_precreation_spell_budget(predicted_plan):
    assert predicted_plan.execute('''
      S.Creators=function(row)return row.resref=='CREATE'and {{kind='clone',image=2}}or {}end
      local s,preset=futurePlan(1);local image=s.groups['spl:BUFF'].sources[1]
      source(s,'spl:BUFF','A',600,'A:spell:BUFF',2)
      local requests={preset.requests[1],request('spl:BUFF','B','A'),
        request('spl:BUFF','B',image.actor),request('spl:BUFF','A',image.actor)}
      local result=P.Assign(s,requests)
      return image.pool=='A:spell:BUFF'and result.missing==1 and result.used[image.pool]==2
    ''')


def test_unavailable_image_creation_cannot_zero_the_owners_real_spell_pool(predicted_plan):
    assert predicted_plan.execute('''
      S.Creators=function(row)return row.resref=='CREATE'and {{kind='clone',image=2}}or {}end
      local s,preset=futurePlan(0)
      source(s,'spl:BUFF','A',600,'A:spell:BUFF',2)
      S.AddSources(s,preset,{})
      local image=s.groups['spl:BUFF'].sources[#s.groups['spl:BUFF'].sources]
      local result=P.Assign(s,{request('spl:BUFF','B','A'),request('spl:BUFF','A',image.actor)})
      return s.pools['A:spell:BUFF']==2 and image.pool~='A:spell:BUFF'
        and result.decisions[1].source~=nil and result.decisions[2].source==nil
    ''')

def test_future_identity_survives_reordering_and_data_only_export(predicted_plan):
    predicted_plan.execute((ROOT/'buffbot/BfBotIO.lua').read_text(encoding='utf-8'))
    assert predicted_plan.execute('''
      local s,preset=futurePlan(1);preset.name='Future';local src=s.groups['spl:BUFF'].sources[1]
      preset.requests[#preset.requests+1]=request('spl:BUFF','B',src.actor)
      P.SaveCustomOrder(preset)
      local copy=assert(BfBot.PlanIO.Decode(assert(BfBot.PlanIO.Encode(preset))))
      return copy.requests[2].source==src.actor and copy.requests[1].group=='CREATE'
    ''')
