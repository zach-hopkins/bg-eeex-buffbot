-- Read-only native-time scheduling. This module never changes effects, speed,
-- sprites or action queues. The same solution feeds Smart Order and dispatch.
BfBot.Timing = {}
local T=BfBot.Timing
T.TICKS_PER_SECOND=15
T.AURA_TICKS=90
local function finite(n)
    return type(n)=='number' and n==n and n~=math.huge and n~=-math.huge
end
function T.ReleaseTicks(segments)
    return math.max(1,math.ceil((finite(segments) and math.max(0,segments) or 10)*9+1))
end

-- Jobs are in the selected per-caster order. A dependency normally waits for
-- its predecessor's completion; {id=...,from='start',lag=...} expresses aura
-- or another start-relative restriction. fixedStart/fixedFinish are observed
-- game times for work that already began, not estimates to move backward.
-- Returns the earliest feasible finish with each unstarted job placed as late
-- as its successors allow. Delaying a short lane never extends that finish.
function T.Solve(jobs,now)
    now=now or 0
    if type(jobs)~='table' or #jobs>256 or not finite(now) or now<0 then
        return nil,'Invalid timing input'
    end
    local nodes,order,previous={},{},{}
    for i,job in ipairs(jobs)do
        local id=job.id or i
        if (type(id)~='string' and type(id)~='number') or nodes[id] then
            return nil,'Duplicate or invalid timing identity'
        end
        local duration=job.duration or job.release or 0
        local release=job.release or duration
        local spacing=job.spacing or math.max(duration,job.aura==true and 0 or T.AURA_TICKS)
        if not finite(duration) or duration<0 or not finite(release) or release<0
            or release>duration or not finite(spacing) or spacing<0 then
            return nil,'Invalid casting duration'
        end
        if job.fixedStart~=nil and (not finite(job.fixedStart) or job.fixedStart<0) then
            return nil,'Invalid observed start'
        end
        if job.notBefore~=nil and (not finite(job.notBefore) or job.notBefore<0) then
            return nil,'Invalid earliest start'
        end
        if job.fixedFinish~=nil then
            if job.fixedStart==nil or not finite(job.fixedFinish) or job.fixedFinish<job.fixedStart then
                return nil,'Invalid observed finish'
            end
            duration=job.fixedFinish-job.fixedStart
            release=math.min(release,duration)
        elseif job.fixedStart~=nil then
            duration=math.max(duration,now-job.fixedStart)
        end
        local n={id=id,index=i,job=job,duration=duration,release=release,spacing=spacing,
            incoming={},outgoing={},count=0,earliest=job.fixedStart or math.max(now,job.notBefore or now)}
        if not finite(n.earliest) or n.earliest<0 then return nil,'Invalid earliest start' end
        nodes[id]=n;order[i]=n
    end
    local function edge(a,b,weight)
        if not a or not b then return false end
        local old=a.outgoing[b.id]
        if not old then b.count=b.count+1 end
        if old==nil or weight>old then
            a.outgoing[b.id]=weight;b.incoming[a.id]=weight
        end
        return true
    end
    for _,n in ipairs(order)do
        local job=n.job
        if job.caster then
            local prev=previous[job.caster]
            if prev then edge(prev,n,math.max(prev.duration,prev.spacing)) end
            previous[job.caster]=n
        end
        for _,dependency in ipairs(job.after or {})do
            local spec=type(dependency)=='table' and dependency or {id=dependency}
            local before=nodes[spec.id]
            local lag=spec.lag or 0
            if not before or not finite(lag) or lag<0 then return nil,'Missing or invalid casting dependency' end
            edge(before,n,(spec.from=='start' and 0 or before.duration)+lag)
        end
    end
    local ready,topology={},{}
    for _,n in ipairs(order)do if n.count==0 then ready[#ready+1]=n end end
    local cursor,finish=1,now
    while cursor<=#ready do
        local n=ready[cursor];cursor=cursor+1
        topology[#topology+1]=n
        if n.job.fixedStart~=nil and n.earliest>n.job.fixedStart+0.00001 then
            return nil,'Observed cast violates a dependency'
        end
        finish=math.max(finish,n.earliest+n.duration)
        for id,weight in pairs(n.outgoing)do
            local nextNode=nodes[id]
            nextNode.earliest=math.max(nextNode.earliest,n.earliest+weight)
            nextNode.count=nextNode.count-1
            if nextNode.count==0 then ready[#ready+1]=nextNode end
        end
    end
    if #topology~=#order then return nil,'Cyclic casting dependencies' end
    for i=#topology,1,-1 do
        local n=topology[i]
        local latest=finish-n.duration
        for id,weight in pairs(n.outgoing)do latest=math.min(latest,nodes[id].start-weight) end
        n.start=n.job.fixedStart or math.max(n.earliest,latest)
    end
    local result={finish=finish,order={},jobs={}}
    for _,n in ipairs(topology)do
        result.order[#result.order+1]=n.id
        result.jobs[n.id]={start=n.start,earliest=n.earliest,finish=n.start+n.duration,
            release=n.start+n.release,age=math.max(0,finish-n.start-n.release)}
    end
    return result
end

-- Add the same game restrictions to the preview model and the real dispatcher.
-- Copy descriptors: sorting previews must not mutate saved requests or queues.
function T.Constrain(input)
    local jobs={}
    for i,j in ipairs(input)do
        local c={};for k,v in pairs(j)do c[k]=v end
        c.id=j.id or i;c.after={}
        for _,v in ipairs(j.after or {})do c.after[#c.after+1]=v end
        jobs[i]=c
    end
    for i,j in ipairs(jobs)do
        for k,other in ipairs(jobs)do
            if i~=k then
                local earlier=(other.rank or k)<(j.rank or i)
                local prerequisite=j.prerequisite and not j.ownerImage
                    and (j.affects=='party' or other.actor==j.affects)
                local target=j.invisible and not other.party and other.target~='party'
                    and other.actor~=other.target and (j.party or other.target==j.target)
                    and (not other.invisible or earlier)
                if prerequisite then
                    local before,after=earlier and other or j,earlier and j or other
                    after.after[#after.after+1]=before.id
                end
                if target then j.after[#j.after+1]=other.id end
                if j.ownerImage and other.actor==j.affects then j.after[#j.after+1]=other.id end
                if j.provider and other.id==j.provider then j.after[#j.after+1]=other.id end
            end
        end
    end
    return jobs
end

local function tick()
    return BfBot.Exec and BfBot.Exec._GetGameTime and BfBot.Exec._GetGameTime()
end
local function audit(run,event,node,now,extra)
    -- At most a start, wait, issue and outcome per entry, plus bounded replans.
    if #run.audit<1536 then
        run.audit[#run.audit+1]={event=event,id=node and node.id,time=now,
            caster=node and node.caster,spell=node and node.spell,detail=extra}
    end
end
function T.Reset(reason)
    if T.run then
        audit(T.run,'end',nil,tick(),reason)
        T.lastAudit=T.run.audit
    end
    T.run=nil
end

-- Schedule data contains scalar identities only. Resolve engine sprites at
-- each real dispatch, just as Exec does; never retain their userdata here.
function T.Begin(casters)
    T.Reset('replaced')
    local enabled,jit=false,false
    for _,c in pairs(casters)do for _,e in ipairs(c.queue)do
        if e.smartTiming then enabled=true;jit=true end
        if e.future or e.providerPlanIndex then enabled=true end
    end end
    local now=tick()
    if not enabled or not finite(now) then return end
    local run={nodes={},byEntry={},waiting={},audit={},origin=now,revision=0,jit=jit,byPlan={}}
    for key,c in pairs(casters)do
        for index,e in ipairs(c.queue)do
            local timing=e.timing or {}
            local node={id=key..':'..index,caster=key,actor=e.plannedActor or key,
                target=e.plannedTarget,rank=e.planIndex,spell=e.resref,
                release=timing.release or T.AURA_TICKS,aura=timing.aura==true,
                rawSegments=timing.rawSegments,
                prerequisite=timing.prerequisite,affects=timing.affects or e.plannedTarget,
                ownerImage=timing.ownerPrerequisite,providerIndex=e.providerPlanIndex,
                invisible=e.invisibilityTarget~=nil,party=e.isAoE or e.plannedTarget=='party',
                index=index,key=key}
            run.nodes[#run.nodes+1]=node;run.byEntry[e]=node
            if e.planIndex then run.byPlan[e.planIndex]=node end
        end
    end
    table.sort(run.nodes,function(a,b)
        if a.rank and b.rank and a.rank~=b.rank then return a.rank<b.rank end
        if a.key~=b.key then return a.key<b.key end
        return a.index<b.index
    end)
    for _,n in ipairs(run.nodes)do
        local provider=n.providerIndex and run.byPlan[n.providerIndex]
        n.provider=provider and provider.id or nil
    end
    run.nodes=T.Constrain(run.nodes)
    -- Constrain copied nodes, so rebind the entry lookup to those copies.
    local byId={};for _,n in ipairs(run.nodes)do byId[n.id]=n end
    for e,n in pairs(run.byEntry)do run.byEntry[e]=byId[n.id] end
    for i,n in pairs(run.byPlan)do run.byPlan[i]=byId[n.id]end
    run.byId=byId
    T.run=run;T.Replan(now)
    for _,n in ipairs(run.nodes)do
        local p=run.solution and run.solution.jobs[n.id]
        audit(run,'planned',n,now,p and p.start)
    end
end

function T.Replan(now)
    local run=T.run;if not run then return end
    now=now or tick();if not finite(now)then T.Reset('game clock unavailable');return end
    local jobs,finished,ready={},{},{}
    for _,n in ipairs(run.nodes)do if n.outcome then finished[n.id]=n end end
    for _,n in ipairs(run.nodes)do
        if not n.outcome then
            local j={};for k,v in pairs(n)do j[k]=v end
            j.notBefore=now;j.after={}
            for _,d in ipairs(n.after)do
                local id=type(d)=='table' and d.id or d
                if finished[id] then j.notBefore=math.max(j.notBefore,finished[id].finished or now)
                else j.after[#j.after+1]=d end
            end
            j.notBefore=math.max(j.notBefore,ready[n.caster] or 0)
            if n.started then
                j.fixedStart=n.started;j.notBefore=nil
                -- An active native action can exceed the estimate (movement,
                -- aura or scripts). Pending work follows observed game time.
                j.duration=math.max(n.release,now-n.started+1)
            end
            jobs[#jobs+1]=j
        end
        if n.started then ready[n.caster]=math.max(ready[n.caster] or 0,
            n.started+math.max(n.release,n.aura and 0 or T.AURA_TICKS))end
    end
    local solution,why=T.Solve(jobs,now)
    run.solution=solution;run.revision=run.revision+1
    if not solution then
        -- Keep native casting usable on an unsupported timing combination.
        -- Dependencies in Exec remain enforced; only deliberate JIT is lost.
        audit(run,'timing fallback',nil,now,why)
    end
end

function T.Enter(key,index)
    local run=T.run;if not run then return end
    local now=tick()
    -- Advancing synchronously without an engine completion means preflight
    -- skipped that attempt. Retire it so it cannot keep another lane waiting.
    local changed=false
    for _,n in ipairs(run.nodes)do
        if n.key==key and n.index<index and not n.outcome then
            n.outcome='skipped';n.finished=now;changed=true
            audit(run,'skipped',n,now)
        end
    end
    if changed then T.Replan(now)end
end
function T.Gate(key,index,entry)
    local run=T.run;local n=run and run.byEntry[entry]
    if not n or n.started then return false end
    local now=tick();local planned=run.solution and run.solution.jobs[n.id]
    local blocked=T.Blocked(run,n)
    if not blocked and (not run.jit or not finite(now) or not planned or now>=planned.start) then
        run.waiting[key]=nil;return false
    end
    if not run.waiting[key]then audit(run,'wait',n,now,planned and planned.start or 'dependency')end
    run.waiting[key]={index=index,entry=entry}
    return true
end
function T.Provider(index)
    return T.run and T.run.byPlan[index]
end
function T.Record(event,entry,detail)
    local run=T.run;if run then audit(run,event,run.byEntry[entry],tick(),detail)end
end
function T.Replace(old,entry)
    local run=T.run;local n=run and run.byEntry[old]
    if not n then return end
    run.byEntry[old]=nil;run.byEntry[entry]=n
    local timing=entry.timing
    if timing then
        n.release=timing.release or n.release;n.aura=timing.aura==true
        n.rawSegments=timing.rawSegments
    end
    T.Replan()
end
function T.Blocked(run,node)
    for _,d in ipairs(node.after)do
        local id=type(d)=='table' and d.id or d
        local before=run.byId[id]
        if before and not before.outcome then return true end
    end
    return false
end
function T.Issued(entry)
    local run=T.run;local n=run and run.byEntry[entry]
    if not n then return end
    n.started=tick();audit(run,'issued',n,n.started)
end
function T.Finished(entry)
    local run=T.run;local n=run and run.byEntry[entry]
    if not n or n.outcome then return end
    n.outcome='finished';n.finished=tick();audit(run,'finished',n,n.finished)
    T.Refresh(n.finished,true)
    T.Replan(n.finished)
end
function T.Gone(key)
    local run=T.run;if not run then return end
    for _,n in ipairs(run.nodes)do if n.key==key and not n.outcome then
        n.outcome='caster gone';n.finished=tick();audit(run,'caster gone',n,n.finished)
    end end
    run.waiting[key]=nil;T.Replan()
end

-- Read only the small active-stat block, once per game second or completion.
-- Pending spells retain their parsed casting factor; no spellbook/resource scan
-- is needed when an aura or casting-speed effect starts or expires.
function T.Refresh(now,force)
    local run=T.run
    if not run or not run.jit or not finite(now) then return end
    if not force and run.lastStats and now-run.lastStats<T.TICKS_PER_SECOND then return end
    run.lastStats=now
    if type(EEex_Sprite_GetActiveStats)~='function' or not BfBot.Plan
        or not BfBot.Plan.CastingSegments then return end
    local stats,changed={},false
    for _,n in ipairs(run.nodes)do
        if not n.outcome and not n.started then
            if stats[n.key]==nil then
                local caster=BfBot.Exec._casters[n.key]
                local ok,value=pcall(function()
                    local sprite=caster and BfBot.Exec._ResolveCasterForStep(caster)
                    return sprite and EEex_Sprite_GetActiveStats(sprite)
                end)
                stats[n.key]=ok and value or false
            end
            local ds=stats[n.key]
            if ds then
                local aura=n.aura
                if ds.m_bAuraCleansing~=nil then aura=ds.m_bAuraCleansing~=0 end
                local release=n.release
                if n.rawSegments and type(ds.m_nCastingType)=='number'
                    and type(ds.m_nMentalSpeed)=='number'then
                    release=T.ReleaseTicks(BfBot.Plan.CastingSegments(
                        n.rawSegments,ds.m_nCastingType,ds.m_nMentalSpeed))
                end
                if release~=n.release or aura~=n.aura then
                    n.release,n.aura=release,aura;changed=true
                    audit(run,'timing changed',n,now,release)
                end
            end
        end
    end
    if changed then T.Replan(now)end
end
function T.Pump()
    local run=T.run;if not run then return end
    if BfBot.Exec._state~='running'then T.Reset('not running');return end
    local now=tick()
    T.Refresh(now)
    if not finite(now) or now==run.lastPump and run.lastPumpRevision==run.revision then return end
    run.lastPump=now;run.lastPumpRevision=run.revision
    local ready={}
    for key,w in pairs(run.waiting)do
        local n=run.byEntry[w.entry]
        local planned=run.solution and run.solution.jobs[n.id]
        if not T.Blocked(run,n) and (not run.jit or not planned or now>=planned.start)then
            ready[#ready+1]={key=key,index=w.index}
        end
    end
    -- Release only existing pending records. Stop/replacement clears T.run;
    -- no delayed engine callback can resurrect a previous plan.
    for _,w in ipairs(ready)do
        if T.run~=run then break end
        run.waiting[w.key]=nil
        if BfBot.Exec._DetectCombat()then BfBot.Exec.Stop();break end
        BfBot.Exec._ProcessCasterEntry(w.key,w.index)
    end
end
