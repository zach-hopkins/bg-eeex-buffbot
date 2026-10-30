-- Temporary simulation acceleration. Spell/item actions remain native; no
-- acceleration helper, clock jumps or effect-expiry corrections are applied.
BfBot.Fast=BfBot.Fast or {}
local F=BfBot.Fast
local function rate() return EEex_CChitin and EEex_CChitin.TIMER_UPDATES_PER_SECOND end
local function setRate(value)
    EEex_CChitin.TIMER_UPDATES_PER_SECOND=value
    return rate()==value
end
local function gameTick()
    return EngineGlobals.g_pBaldurChitin.m_pObjectGame.m_worldTime.m_gameTime
end
local function truth(value) return value~=nil and value~=false and value~=0 end
function F.Safe()
    if BfBot.Mp and BfBot.Mp._IsMpSession() then return false,'multiplayer' end
    if not e or not worldScreen or e:GetActiveEngine()~=worldScreen then return false,'outside world' end
    local input=EngineGlobals.g_pBaldurChitin.m_pObjectGame.m_gameSave.m_inputMode
    if bit.band(input-0x1016E,0xFFFDFFFF)==0 or bit.band(input,0x801)==0
        or sidebarsGreyed==1 then return false,'dialogue or cutscene' end
    for _,menu in ipairs({'WORLD_DIALOG','WORLD_DIALOG_CONFIRM','STORE','LOAD_SCREEN',
        'POPUP_INFO','POPUP_TWOBUTTON','POPUP_THREEBUTTON','POPUP_FOURBUTTON'}) do
        if truth(Infinity_IsMenuOnStack(menu)) then return false,'menu' end
    end
    if not BfBot.Rest or BfBot.Rest.Combat() then return false,'combat' end
    return true
end
function F.Reset(reason)
    local run=F.run
    if not run then return true end
    run.releaseReason=run.releaseReason or reason or 'reset'
    local ok,current=pcall(rate)
    local restored=run.rateRestored or false
    if not ok or type(current)~='number' then
        if not run.warnedRestore then BfBot._Warn('Fast forward: rate read failed; restoration pending');run.warnedRestore=true end
        return false
    end
    if current==run.applied then
        local changed,result=pcall(setRate,run.original)
        restored=changed and result==true
        if not restored then
            if not run.warnedRestore then BfBot._Warn('Fast forward: could not restore simulation speed; retrying');run.warnedRestore=true end
            return false
        end
        run.rateRestored=true
    end
    local renderRestored=false
    if run.render then
        local read,ours=pcall(function()
            return EEex.UncapFPS_FPSLimitEnabled==true and EEex.UncapFPS_FPSLimit==run.render.applied
        end)
        if not read then return false end
        if ours then
            local changed=pcall(function()
                EEex.UncapFPS_FPSLimit=run.render.original
                EEex.UncapFPS_FPSLimitEnabled=run.render.enabled
            end)
            renderRestored=changed
            if not changed then return false end
        end
    end
    F.run=nil -- release only after readable/restored ownership decisions
    local clockOk,now=pcall(Infinity_GetClockTicks)
    local audit={original=run.original,applied=run.applied,reason=run.releaseReason,
        restored=restored,wallMs=clockOk and type(now)=='number' and now-run.wall or 0,gameTicks=0,
        renderCap=run.render and run.render.applied or 0,renderRestored=renderRestored}
    local read,tick=pcall(gameTick)
    if read then audit.gameTicks=tick-run.tick end
    F.lastAudit=audit
    if io then
        local file=io.open('buffbot_fast_forward_audit.jsonl','a')
        if file then
            file:write(string.format('{"original":%d,"applied":%d,"wallMs":%d,"gameTicks":%d,"restored":%s,"renderCap":%d,"renderRestored":%s,"reason":"%s"}\n',
                audit.original,audit.applied,audit.wallMs,audit.gameTicks,tostring(restored),
                audit.renderCap,tostring(renderRestored),
                audit.reason:gsub('[%c"\\]',' ')))
            file:close()
        end
    end
    return restored
end
-- Adapted from upstream: lifecycle transitions may remove the normal UI tick.
-- Retry a bounded number of times, retaining ownership on failure for later.
function F.Release(reason)
    for _=1,3 do
        if not F.run then return true end
        F.Reset(reason)
        if not F.run then return true end
    end
    return false
end
function F.Start(queue,preset)
    if type(queue)~='table' or #queue==0 then return false,'reason.exec.empty_queue',{} end
    if F.run or BfBot.Exec.GetState()=='running' or BfBot.Share and BfBot.Share.run then
        return false,'reason.exec.already_running',{}
    end
    local safe,allowed,why=pcall(F.Safe)
    if not safe or not allowed then
        BfBot.Exec._NotifyLeader('Fast forward unavailable: '..tostring(safe and why or 'engine inspection failed'))
        return false,'reason.exec.empty_queue',{}
    end
    local ok,original=pcall(rate)
    if not ok or type(original)~='number' or original%1~=0 or original<1 or original>=120 then
        BfBot.Exec._NotifyLeader('Fast forward unavailable: unsupported simulation rate')
        return false,'reason.exec.empty_queue',{}
    end
    local state=BfBot.Plan.GetState()
    local multiplier=state and state.fastRate==4 and 4 or 2
    local wallOk,wall=pcall(Infinity_GetClockTicks)
    local tickOk,tick=pcall(gameTick)
    if not wallOk or type(wall)~='number' or not tickOk or type(tick)~='number' then return false,'reason.exec.empty_queue',{} end
    local applied=math.min(120,original*multiplier)
    local run={original=original,applied=applied,wall=wall,tick=tick}
    F.run=run
    -- EEex decouples render and simulation rates. Rendering every possible
    -- frame can starve faster logic; 30 FPS retains the native game's visual
    -- cadence without raising a player's existing lower limit. Never persist.
    pcall(function()
        local limit,enabled=EEex.UncapFPS_FPSLimit,EEex.UncapFPS_FPSLimitEnabled
        if type(limit)=='number' and limit>=1 and type(enabled)=='boolean' then
            run.render={original=limit,enabled=enabled,applied=enabled and math.min(limit,30) or 30}
            EEex.UncapFPS_FPSLimit=run.render.applied
            EEex.UncapFPS_FPSLimitEnabled=true
        end
    end)
    local changed,result=pcall(setRate,applied)
    if not changed or not result then
        local read,current=pcall(rate)
        if read and type(current)=='number' then run.applied=current end
        F.Release('start failed');return false,'reason.exec.empty_queue',{}
    end
    local copy={}
    for i,entry in ipairs(queue or {}) do
        copy[i]={};for k,v in pairs(entry) do copy[i][k]=v end
        copy[i].cheat=0 -- no inherited per-entry Quick Cast override
    end
    local started,a,b,c=pcall(BfBot.Exec.Start,copy,0,preset)
    if not started or not a then
        F.Release('start failed')
        if not started then error(a) end
        return a,b,c
    end
    F.CheckDone()
    return a,b,c
end
function F.CheckDone()
    if F.run and BfBot.Exec.GetState()~='running' and not (BfBot.Share and BfBot.Share.run) then
        F.Reset('complete')
    end
end
function F.Tick()
    local run=F.run;if not run then return end
    if run.releaseReason then return F.Reset(run.releaseReason) end
    local clockOk,now=pcall(Infinity_GetClockTicks)
    if not clockOk or type(now)~='number' or now<run.wall then
        F.Reset('clock unavailable or reset');BfBot.Exec.Stop();return
    end
    -- The menu callback can run at uncapped rendering FPS. Area-wide combat
    -- checks belong on a short wall-time cadence, not every rendered frame.
    if run.lastGuard and now>=run.lastGuard and now-run.lastGuard<50 then return F.CheckDone() end
    run.lastGuard=now
    local ok,current=pcall(rate)
    local checked,safe,why=pcall(F.Safe)
    local reason
    if not ok or current~=run.applied then reason='external speed change'
    elseif not checked or not safe then reason=checked and why or 'engine inspection failed'
    end
    -- Pauses and healthy long plans do not time out in wall time. The executor
    -- already has a no-progress watchdog measured in game time, frozen on pause.
    if reason then
        F.Reset(reason)
        BfBot.Exec.Stop() -- normal item recovery continues at the restored rate
        return
    end
    F.CheckDone()
end
function F.OnDestroyed()
    F.Release('load or exit')
    -- Same-party reloads keep the same portrait names but lose every queued
    -- completion callback. Reset execution explicitly, even in Normal mode.
    if BfBot.Exec and BfBot.Exec._HardReset then BfBot.Exec._HardReset()end
    if BfBot._CloseLog then BfBot._CloseLog()end
end
function F.Init()
    if BfBot._fastListenersRegistered then return end
    EEex_GameState_AddDestroyedListener(function() BfBot.Fast.OnDestroyed()end)
    BfBot._fastListenersRegistered=true
end
