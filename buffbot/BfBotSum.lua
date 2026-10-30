-- Predicted spellbooks for planned image casters. Resource analysis is read-only:
-- no preview creature is created and no effects or memorization flags are changed.
BfBot.Summon = {}
local S=BfBot.Summon
local components={
    [1]={1},[2]={2},[3]={3},[4]={4},[5]={5},[6]={6},[7]={2,1},
    [8]={2,3},[9]={2,4},[10]={2,1,4},[11]={11},[12]={12},[13]={1,4},
    [14]={3,1},[15]={3,4},[16]={2,11},[17]={2,1,3},[18]={3,12},
    [19]={19},[20]={20},[21]={21},
}
local originalFlags={[2]=8,[1]=16,[3]=32,[4]=64,[11]=128,[12]=256}
local tables={}
local function tableData(name)
    if tables[name]then return tables[name]end
    local source=BfBot.Scan and BfBot.Scan.ReadTextResource
        and BfBot.Scan.ReadTextResource(name,'2DA')
    if source then
        local lines={}
        for line in source:gmatch('[^\r\n]+')do
            line=line:gsub('//.*','')
            local words={};for word in line:gmatch('%S+')do words[#words+1]=word end
            if #words>0 then lines[#lines+1]=words end
        end
        if lines[1]and lines[1][1]=='2DA'and lines[3]then
            local out={};local default=tonumber(lines[2]and lines[2][1])or 0
            for i=4,#lines do
                local cells={};out[lines[i][1]]=cells
                for col,label in ipairs(lines[3])do cells[label]=tonumber(lines[i][col+1])or default end
            end
            tables[name]=out;return out
        end
    end
    if type(EEex_Resource_Load2DA)~='function'then return nil end
    local ok,rows=pcall(function()
        local t=EEex_Resource_Load2DA(name);if not t then return nil end
        local x,y=t:getDimensions();local out={}
        for row=0,y-1 do
            local cells={};out[tostring(t:getRowLabel(row))]=cells
            for col=0,x-2 do cells[tostring(t:getColumnLabel(col))]=tonumber(t:getAtPoint(col,row)) or 0 end
        end
        return out
    end)
    if ok and rows then tables[name]=rows;return rows end
end
function S.Rule(name,row,column)
    local data=tableData(name)
    if not data then return nil end
    local cells=data[tostring(row)]
    return cells and cells[tostring(column)] or 0
end
function S.ClearRules()tables={}end

function S.Classes(class,flags)
    local parts=components[class]
    if not parts then return nil,'Unsupported caster class' end
    local active,previous
    if #parts==2 then for _,part in ipairs(parts)do
        local mask=originalFlags[part]
        if mask and bit.band(flags or 0,mask)~=0 then previous=part end
    end end
    if previous then for _,part in ipairs(parts)do if part~=previous then active=part end end end
    return parts,active,previous
end

-- Match the native 236/type3 drain: floor(2 * GetAverageLevel(activeClass) / 5).
-- In dual classes the engine's average-level query uses the first level field;
-- retain that behavior rather than silently substituting a nicer rule.
function S.CloneLevels(profile,kind)
    local parts,active,previous=S.Classes(profile.class,profile.flags)
    if not parts then return nil,active end
    local levels={};local total=0
    for i=1,#parts do levels[i]=profile.levels[i] or 0;total=total+levels[i]end
    local average=profile.copyLevel or (active and levels[1] or math.ceil(total/#parts))
    local drain=kind==3 and math.floor(average*2/5)or 0
    for i,part in ipairs(parts)do
        if not active or part==active then levels[i]=math.max(1,levels[i]-drain)end
    end
    local usable={}
    for i,part in ipairs(parts)do
        if not previous or part~=previous then usable[part]=levels[i]
        else
            local activeLevel=0
            for k,c in ipairs(parts)do if c==active then activeLevel=levels[k]end end
            if activeLevel>levels[i]then usable[part]=levels[i]end
        end
    end
    return {levels=levels,usable=usable,drain=drain,active=active,previous=previous}
end

function S.Capacity(profile,levels,book,spellLevel,rule)
    rule=rule or S.Rule
    local best=0
    for class,level in pairs(levels.usable)do
        local tableName
        if book=='Mage'then
            tableName=({[1]='MXSPLWIZ',[5]='MXSPLBRD',[19]='MXSPLSRC'})[class]
            if class==19 and bit.band(profile.kit or 16384,bit.bnot(16384))==35 then tableName='MXSPLDD'end
        elseif book=='Priest'then
            tableName=({[3]='MXSPLPRS',[11]='MXSPLDRU',[6]='MXSPLPAL',[12]='MXSPLRAN',[21]='MXSPLSHM'})[class]
        end
        if tableName then
            local count=rule(tableName,level,spellLevel)
            if count==nil then return nil,'Spell-slot rules unavailable: '..tableName end
            if count>0 then
                if class==1 then
                    local kit=profile.kit or 16384
                    local specialist=bit.band(kit,0x4000)==0 and bit.band(kit,0x3FC0)~=0
                        or bit.band(kit,0x80000000)~=0
                    if specialist then count=count+1 end
                elseif class==19 then
                    -- Native DD copies get the kit slot on top of MXSPLDD;
                    -- reading that lower table alone undercounts every level.
                    if profile.kit and profile.kit~=16384 then count=count+1 end
                elseif class==3 or class==11 then
                    local bonus=rule('MXSPLWIS',profile.wis or 10,spellLevel)
                    if bonus==nil then return nil,'Wisdom spell-slot rules unavailable'end
                    count=count+bonus
                end
            end
            best=math.max(best,count)
        end
    end
    -- Native copies reduce memorized entries against class/kit/WIS slots.
    -- Equipped slot bonuses survive on the copy but do not refill the book;
    -- replaying them here would invent prepared spells (native RING08 test).
    return best
end

-- Keep all memorized entries, including attacks. The engine sorts by generic
-- localized name, then truncates to the reduced capacity. Simulacrum refreshes
-- copied memorization before this reduction; Project Image preserves spent uses.
-- Filtering buffs before that step invents spell slots.
function S.Predict(profile,kind,rule)
    if kind~=2 and kind~=3 then return nil,'Unsupported image type'end
    local levels,why=S.CloneLevels(profile,kind)
    if not levels then return nil,why end
    local result={counts={},books={},levels=levels.levels,drain=levels.drain,usable=levels.usable}
    for book,bookLevels in pairs(profile.books or {})do
        result.books[book]={}
        for level,entries in ipairs(bookLevels)do
            local capacity
            if kind==2 or book=='Innate'then capacity=#entries
            else capacity,why=S.Capacity(profile,levels,book,level,rule)end
            if capacity==nil then return nil,why end
            local copies={}
            for i,e in ipairs(entries)do
                copies[i]={res=e.res,name=e.sortName or e.name or e.res,flags=e.flags or 0,index=i}
            end
            local spontaneous=book=='Mage'and profile.class==19 or book=='Priest'and profile.class==21
            if kind==3 and book~='Innate'then
                table.sort(copies,function(a,b)
                    if a.name~=b.name then return a.name<b.name end
                    return a.index<b.index
                end)
            end
            local uses={}
            for i,e in ipairs(copies)do
                uses[e.res]=(uses[e.res]or 0)+1
                result.books[book][level]=result.books[book][level]or {}
                local list=result.books[book][level]
                if spontaneous then
                    -- The engine rebuilds spontaneous copies from the known
                    -- choices and class capacity. A short/stale memorized list
                    -- is not the number of uses the new copy receives.
                    if uses[e.res]==1 then
                        local count=kind==3 and capacity or profile.availableCounts and profile.availableCounts[e.res]
                        if count==nil then
                            count=0;for _,entry in ipairs(copies)do
                                if entry.res==e.res and bit.band(entry.flags,3)==1 then count=count+1 end
                            end
                        end
                        count=math.max(0,math.min(512,count))
                        result.counts[e.res]=count
                        for n=1,math.max(1,count)do list[#list+1]={res=e.res,flags=n<=count and 1 or 0}end
                    end
                else
                    local within=kind==2 or book=='Innate'or i<=capacity
                    local available=within and (kind==3 or bit.band(e.flags,3)==1)
                    result.counts[e.res]=(result.counts[e.res]or 0)+(available and 1 or 0)
                    list[#list+1]={res=e.res,flags=available and 1 or 0}
                end
            end
        end
    end
    return result
end

function S.ReadProfile(sprite)
    local ok,value=pcall(function()
        local ds=EEex_Sprite_GetActiveStats(sprite)
        local profile={class=sprite.m_typeAI.m_Class,flags=sprite.m_baseStats.m_flags,
            levels={ds.m_nLevel1,ds.m_nLevel2,ds.m_nLevel3},wis=ds.m_nWIS,
            kit=sprite:getStat(152),books={},casterLevels={},availableCounts={}}
        local parts,active=S.Classes(profile.class,profile.flags)
        if not parts then return nil end
        profile.copyLevel=ds:GetAverageLevel(active or profile.class)
        local names,sortNames={},{};local catalog=BfBot.Scan.GetCastableSpells(sprite)
        for _,book in ipairs({'Mage','Priest','Innate'})do
            local rows={};profile.books[book]=rows
            for level=0,(book=='Mage'and 8 or book=='Priest'and 6 or 0)do
                local entries={};rows[level+1]=entries
                EEex_Utility_IterateCPtrList(sprite['m_memorizedSpells'..book]:getReference(level),function(e)
                    local res=e.m_spellId:get()
                    if not names[res]then
                        local row=catalog[res]or BfBot.Scan.DescribeSpell(res,1)
                        names[res]=row and row.name or res
                        -- Native book reduction sorts the generic TLK name,
                        -- including empty names on hidden/helper spells. The
                        -- browser's resref fallback would move those to the end
                        -- and predict the wrong surviving prepared spells.
                        local named,text=pcall(function()
                            local h=EEex_Resource_Demand(res,'SPL')
                            return h and Infinity_FetchString(h.genericName)
                        end)
                        sortNames[res]=named and type(text)=='string'and text or names[res]
                        profile.casterLevels[res]=row and row.casterLevel or nil
                        profile.availableCounts[res]=row and row.count or nil
                    end
                    entries[#entries+1]={res=res,name=names[res],sortName=sortNames[res],flags=e.m_flags}
                end)
            end
        end
        return profile
    end)
    return ok and value or nil,not ok and tostring(value)or nil
end

function S.BookCounts(profile)
    local counts={}
    for _,levels in pairs(profile.books or {})do for _,entries in ipairs(levels)do
        for _,e in ipairs(entries)do
            counts[e.res]=(counts[e.res]or 0)+(bit.band(e.flags or 0,3)==1 and 1 or 0)
        end
    end end
    return counts
end
local function castingLevel(usable,spellType)
    if spellType==1 then return math.max(usable[1]or 0,usable[5]or 0,usable[19]or 0,1)end
    if spellType==2 then return math.max(usable[3]or 0,usable[11]or 0,usable[21]or 0,
        (usable[6]or 0)-8,(usable[12]or 0)-7,1)end
    local best=1;for _,n in pairs(usable)do best=math.max(best,n)end;return best
end
function S.BuildRows(profile,prediction)
    local original=S.CloneLevels(profile,2)
    local usable=prediction and prediction.usable or original and original.usable or {}
    local counts=prediction and prediction.counts or S.BookCounts(profile)
    local rows,locations={},{}
    for _,book in ipairs({'Mage','Priest','Innate'})do
        for level,entries in ipairs(profile.books[book]or {})do for _,e in ipairs(entries)do
            locations[e.res]=locations[e.res]or {level=level,kind=({Mage=1,Priest=2,Innate=4})[book]}
        end end
    end
    for res,count in pairs(counts)do
        local h=EEex_Resource_Demand(res,'SPL')
        if h then
            local spellType=h.itemType or h.spellType or 0
            local level=castingLevel(usable,spellType)
            local before=original and castingLevel(original.usable,spellType)or level
            if profile.casterLevels and profile.casterLevels[res]then
                level=math.max(1,level+profile.casterLevels[res]-before)
            end
            local row=BfBot.Scan.DescribeSpell(res,level)
            if row then
                row.count=count;row.predicted=1;rows[res]=row
                local where=locations[res]
                if where then row.bookLevel=where.level;row.bookType=where.kind end
            end
        end
    end
    return rows
end

-- CRE V1.0 is a file format, not an executable-specific sprite offset.
-- Validate every section against CRes.nSize before reading native memory.
function S.ReadCreature(resource)
    local ok,value=pcall(function()
        local res=EEex_Resource_Fetch(resource,'CRE')
        local data=res and res:Demand()
        local size=res and res.nSize
        if not data or type(size)~='number'or size<0x2D4 then return nil end
        local base=EEex_UDToPtr(data)
        local function str(offset,length)
            local out={}
            for i=0,length-1 do
                local c=EEex_ReadU8(base+offset+i);if c==0 then break end
                out[#out+1]=string.char(c)
            end
            return table.concat(out)
        end
        if str(0,8)~='CRE V1.0'then return nil end
        local function u32(offset)return EEex_ReadU32(base+offset)end
        local function u16(offset)return EEex_ReadU16(base+offset)end
        local function section(offset,count,stride,limit)
            return offset>=0x2D4 and count<=limit and offset+count*stride<=size
        end
        local memOffset,memCount=u32(0x2B0),u32(0x2B4)
        local infoOffset,infoCount=u32(0x2A8),u32(0x2AC)
        if not section(memOffset,memCount,12,4096)or not section(infoOffset,infoCount,16,32)then return nil end
        local profile={resource=resource,class=EEex_ReadU8(base+0x273),flags=u32(0x10),
            levels={EEex_ReadU8(base+0x234),EEex_ReadU8(base+0x235),EEex_ReadU8(base+0x236)},
            wis=EEex_ReadU8(base+0x23B),books={Mage={},Priest={},Innate={}}}
        if Infinity_FetchString then
            local named,name=pcall(Infinity_FetchString,u32(8))
            if named and type(name)=='string'and name~=''and #name<=120 and not name:find('%c')then
                profile.name=name
            end
        end
        local names={}
        for i=0,infoCount-1 do
            local p=infoOffset+i*16;local level=u16(p)+1
            local book=({[0]='Priest',[1]='Mage',[2]='Innate'})[u16(p+6)]
            local first,count=u32(p+8),u32(p+12)
            if not book or level>9 or first+count>memCount then return nil end
            local levels=profile.books[book]
            for n=1,level do levels[n]=levels[n]or {}end
            for n=first,first+count-1 do
                local offset=memOffset+n*12;local spell=str(offset,8)
                if not names[spell]then
                    local row=BfBot.Scan.DescribeSpell(spell,profile.levels[1])
                    names[spell]=row and row.name or spell
                end
                local entries=levels[level]
                entries[#entries+1]={res=spell,name=names[spell],flags=u32(offset+8)}
            end
        end
        return profile
    end)
    return ok and value or nil,not ok and tostring(value)or nil
end

-- Return actual installed creation mechanics, including wrapped item powers.
-- An ordinary summon needs its CRE book inspected; never assume that all
-- creatures with a familiar display name have the vanilla Planetar spellbook.
function S.Discover(row)
    local found,seen,budget={},{},128
    local visit, effect
    local function resourceText(res)
        if type(res)~='string'then res=res and res:get()end
        return type(res)=='string'and res~=''and res or nil
    end
    effect=function(op,param2,res,depth)
        budget=budget-1;if budget<0 then return end
        if op==236 and (param2==2 or param2==3)then
            found[#found+1]={kind='clone',image=param2}
        elseif res and (op==67 or op==127)then
            found[#found+1]={kind='creature',resource=res:upper(),opcode=op}
        elseif res and op==146 then visit(res,'SPL',nil,depth+1)
        elseif res and op==177 then visit(res,'EFF',nil,depth+1)end
    end
    visit=function(res,kind,abilityIndex,depth)
        local key=kind..':'..res..':'..tostring(abilityIndex)
        if seen[key]or depth>4 or budget<=0 then return end;seen[key]=true
        local h=EEex_Resource_Demand(res,kind)
        if kind=='EFF'then
            if h then effect(h.m_effectId,h.m_dWFlags,resourceText(h.m_res),depth)end
            return
        end
        local a=h and (kind=='ITM'and BfBot.Scan._GetItemAbility(h,abilityIndex or 0)
            or h:getAbilityForLevel(row.casterLevel or 1))
        if not a then return end
        local function scan(f)
            local fields=BfBot._fields
            effect(f[fields.fb_opcode],f[fields.fb_param2],resourceText(f[fields.fb_res]),depth)
        end
        if kind=='SPL'and (h.castingEffectCount or 0)>0 then
            BfBot.Class._IterateFeatureBlocks(h,{startingEffect=h.castingStartingEffect,
                effectCount=h.castingEffectCount},scan)
        end
        BfBot.Class._IterateFeatureBlocks(h,a,scan)
    end
    local ok=pcall(visit,row.kind=='itm'and row.itemResref or row.resref,
        row.kind=='itm'and'ITM'or'SPL',row.abilityIdx,0)
    return ok and found or {}
end

local mechanics,creatures={},{}
local forecasts,forecastCount={},0
function S.Forecast(profile,image,key)
    local stamp={tostring(profile.class),tostring(profile.flags),tostring(profile.kit),
        tostring(profile.wis),tostring(profile.copyLevel),table.concat(profile.levels or {},',')}
    for _,book in ipairs({'Mage','Priest','Innate'})do
        stamp[#stamp+1]=book
        for level,entries in ipairs(profile.books[book]or {})do
            stamp[#stamp+1]=tostring(level)
            for _,e in ipairs(entries)do
                stamp[#stamp+1]=table.concat({e.res,tostring(e.flags),tostring(e.sortName),
                    tostring(profile.casterLevels and profile.casterLevels[e.res]),
                    tostring(profile.availableCounts and profile.availableCounts[e.res]),
                    tostring(BfBot._overrides and BfBot._overrides[e.res])},':')
            end
        end
    end
    stamp=table.concat(stamp,'|');key=key..':'..image
    local cached=forecasts[key]
    if cached and cached.stamp==stamp then return cached.rows end
    local predicted=S.Predict(profile,image)
    local rows=predicted and S.BuildRows(profile,predicted)
    if not rows then return nil end
    if not cached then forecastCount=forecastCount+1 end
    if forecastCount>16 then forecasts={};forecastCount=1 end
    forecasts[key]={stamp=stamp,rows=rows}
    return rows
end
function S.Creators(row,variant)
    local key=table.concat({row.kind or 'spl',row.itemResref or row.resref or '',
        tostring(row.abilityIdx or 0),tostring(row.casterLevel or 1),variant or ''},':')
    if mechanics[key]then return mechanics[key]end
    local selected=row
    if variant then selected={kind='spl',resref=variant,casterLevel=row.casterLevel}end
    local found={}
    for _,d in ipairs(S.Discover(selected))do
        if d.kind=='clone'then found[#found+1]=d
        else
            if creatures[d.resource]==nil then
                local p=S.ReadCreature(d.resource)
                creatures[d.resource]=p and {profile=p,rows=S.BuildRows(p)}or false
            end
            local c=creatures[d.resource]
            if c then
                for _,r in pairs(c.rows)do
                    if r.count>0 and BfBot.Plan.IsAutomaticBuff(r)
                        and (r.isSelfOnly~=1 or r.isAoE==1)then
                        found[#found+1]=d;break
                    end
                end
            end
        end
    end
    mechanics[key]=found;return found
end
function S.IsCreator(row)return #S.Creators(row)>0 end
local function matches(actor,owner,description)
    if not actor.sprite or not actor.casterRef or actor.casterRef.kind~='summon'then return false end
    local a=actor.sprite
    local origin=BfBot.Scan._ReadSummonOrigin(a)
    if not origin or origin.ownerId~=owner.sprite.m_id then return false end
    if description.kind=='clone'then return origin.kind=='clone'and origin.cloneType==description.image end
    return a.m_resref:get():upper()==description.resource
end

-- Only enabled creation steps in THIS preset expose future books. Saved source
-- identities derive from the owner, creation resource and image/creature type;
-- they survive reordering, save/load and data-only preset export/import.
function S.AddSources(snapshot,preset,preferences)
    if not preset or type(preset.requests)~='table'then return end
    local P=BfBot.Plan
    local current=P.Assign(snapshot,preset.requests)
    local reference=P.Assign(P.OrderSnapshot(snapshot),preset.requests)
    local profiles,added={},{}
    local existing={};for _,actor in ipairs(snapshot.casters)do existing[#existing+1]=actor end
    for i,request in ipairs(preset.requests)do
        local decision=current.decisions[i]
        local source=decision.source or reference.decisions[i].source
        if not source and request.on~=0 then
            -- Project Image locks its owner after creation. That must not hide
            -- the saved planned identity of the image which is already live.
            local group=snapshot.groups[request.group]
            for _,s in ipairs(group and group.sources or {})do
                local a=snapshot.actors[s.actor]
                if a and a.projectImageLocked and (not request.source or request.source==s.actor)then
                    local copy={};for k,v in pairs(s)do copy[k]=v end;copy.reason=nil
                    if P.SourceAllowed(snapshot,copy,request)then source=s;break end
                end
            end
        end
        local owner=source and snapshot.actors[source.actor]
        if request.on~=0 and owner and owner.alive and owner.controlled and not owner.ambiguous then
            for _,description in ipairs(S.Creators(source.row,request.var))do
                local kind=description.kind=='clone'and ('image'..description.image)or description.resource
                local key='summon:planned:'..owner.key..':'..kind..':'..request.group
                if #key<=200 and not added[key]then
                    added[key]=true
                    local live
                    for _,actor in ipairs(existing)do if matches(actor,owner,description)then
                        -- One existing resource pool, even when exposed through
                        -- both its live label and this saved planned identity.
                        live=actor;break
                    end end
                    local rows,profile
                    if live then rows=live.rows
                    elseif description.kind=='clone'then
                        if not profiles[owner.key]then profiles[owner.key]=S.ReadProfile(owner.sprite)or false end
                        profile=profiles[owner.key]
                        if profile then
                            rows=S.Forecast(profile,description.image,owner.key)
                        end
                    else
                        local c=creatures[description.resource]
                        if c then profile,rows=c.profile,c.rows end
                    end
                    if rows and (live or not owner.projectImageLocked)then
                        local label=description.kind=='clone'and P.CloneLabel(description.image)
                            or (live and live.name or profile and profile.name or source.row.name or description.resource)
                        local name=owner.name..' - '..label..(live and ''or ' (planned)')
                        local spec={kind=description.kind,image=description.image,resource=description.resource,
                            owner=owner.key,key=key,exclude={}}
                        for _,actor in ipairs(existing)do
                            if actor.casterRef and actor.casterRef.kind=='summon'then
                                spec.exclude[#spec.exclude+1]=actor.casterRef.oid
                            end
                        end
                        local actor={key=key,name=name,rows=rows,alive=true,controlled=true,
                            class=live and live.class or profile.class,
                            poolKey=live and live.poolKey or key,
                            casterRef=live and live.casterRef or nil,sprite=live and live.sprite or nil,
                            future=not live and spec or nil}
                        snapshot.casters[#snapshot.casters+1]=actor;snapshot.casterActors[key]=actor
                        for _,row in pairs(rows)do
                            -- The owner must finish before Project Image locks
                            -- them. A use spent by the owner is absent from the
                            -- new image, so both sources reserve ONE budget.
                            local sharedImage=not live and description.kind=='clone'and description.image==2
                                and decision.source~=nil
                            local pool,reason=P.SpellPool(sharedImage and owner or actor,row)
                            local full=row.count
                            local count=live and full or decision.source and full or 0
                            if pool then snapshot.pools[pool]=math.min(snapshot.pools[pool]or count,count)end
                            local groupKey=P.GroupKey(row)
                            local manual=preferences and preferences.include and preferences.include[groupKey]==1
                            if row.class and (P.IsAutomaticBuff(row)or manual)
                                and (row.isSelfOnly~=1 or row.isAoE==1)then
                                local group=snapshot.groups[groupKey]
                                if not group then
                                    group={key=groupKey,name=row.name,kind=row.kind,icon=row.icon,sources={}}
                                    snapshot.groups[groupKey]=group
                                end
                                local durations={}
                                for _,v in ipairs(row.variants or {})do
                                    local variant=BfBot.Scan.DescribeSpell(v.resref,row.casterLevel)
                                    durations[v.resref]=variant and variant.duration or 0
                                end
                                group.sources[#group.sources+1]={id=key..'/'..groupKey,actor=key,
                                    casterName=name,casterRef=actor.casterRef,lane=actor.poolKey,
                                    liveActor=live and live.key or nil,row=row,pool=pool or key..':unavailable',
                                    reason=reason,duration=row.duration,casterLevel=row.casterLevel,
                                    fullCount=full,selfOnly=row.isSelfOnly==1,aoe=row.isAoE==1,
                                    variants=row.variants,variantDurations=durations,
                                    future=actor.future,providerRequest=not live and request or nil}
                            end
                        end
                    end
                end
            end
        end
    end
    snapshot.orderSnapshot=nil -- the replenished view now includes future pools
end

function S.ValidFuture(spec)
    if type(spec)~='table'or type(spec.key)~='string'or #spec.key>200
        or type(spec.owner)~='string'or #spec.owner>200 then return false end
    if spec.kind=='clone'then
        if spec.image~=2 and spec.image~=3 then return false end
    elseif spec.kind~='creature'or type(spec.resource)~='string'or #spec.resource>8
        or not spec.resource:match('^[%w_#%-]+$')then return false end
    if type(spec.exclude)~='table'or #spec.exclude>256 then return false end
    for _,oid in ipairs(spec.exclude)do
        if type(oid)~='number'or oid%1~=0 or oid<0 then return false end
    end
    return true
end
local function partyActor(key)
    local found
    for slot=0,5 do
        local a=EEex_Sprite_GetInPortrait(slot)
        if a and BfBot.Plan.ActorKey(a)==key then
            if found then return nil end
            found={key=key,sprite=a}
        end
    end
    return found
end
function S.BeginExecution(casters)
    local run={waiting={},claimed={},owners={},started=BfBot.Exec._GetGameTime()}
    for key,caster in pairs(casters)do for _,entry in ipairs(caster.queue)do
        if entry.future then
            local owner=partyActor(entry.future.owner)
            run.owners[entry.future.owner]=owner and owner.sprite.m_id or false
            run.waiting[key]=true
        end
    end end
    S.runtime=next(run.waiting)and run or nil
end
local function candidates(run,now)
    if not run.candidates or not run.candidateTime or now-run.candidateTime>=3 then
        run.candidates={};run.candidateTime=now
        BfBot.Scan.InvalidateSummons()
        for _,e in ipairs(BfBot.Scan.GetAlliedSummons())do
            run.candidates[#run.candidates+1]={kind='summon',oid=e.oid,name=e.name}
        end
        table.sort(run.candidates,function(a,b)return a.oid<b.oid end)
    end
    return run.candidates
end
function S.Materialize(key,caster,entry)
    local run=S.runtime
    if not run then return nil,'planned summon run ended'end
    local spec=entry.future
    if not S.ValidFuture(spec)then return nil,'invalid planned summon'end
    if caster.ref.kind=='planned'then
        local provider=BfBot.Timing.Provider(entry.providerPlanIndex)
        if not provider then run.waiting[key]=nil;return nil,'summon creation step unavailable'end
        if not provider.outcome then run.waiting[key]=true;return nil,'wait'end
        if provider.outcome~='finished'or not provider.started then
            run.waiting[key]=nil;return nil,'summon creation was skipped'
        end
        local now=BfBot.Exec._GetGameTime()
        local owner=partyActor(spec.owner)
        if not now or not owner or owner.sprite.m_id~=run.owners[spec.owner]then
            run.waiting[key]=nil;return nil,'summon owner changed'
        end
        local excluded={};for _,oid in ipairs(spec.exclude)do excluded[oid]=true end
        for _,ref in ipairs(candidates(run,now))do
            if not excluded[ref.oid]and (not run.claimed[ref.oid]or run.claimed[ref.oid]==key)then
                local a=BfBot.Exec._ResolveCaster(ref)
                if a and matches({sprite=a,casterRef=ref},owner,spec)then
                    run.claimed[ref.oid]=key;caster.ref=ref;caster.futureSpec=spec
                    caster.name=caster.name:gsub(' %(planned%)$','')
                    BfBot.Timing.Record('summon bound',entry,spec.key..' -> '..ref.oid)
                    break
                end
            end
        end
        if caster.ref.kind=='planned'then
            if now-(provider.finished or now)>=225 then
                run.waiting[key]=nil
                BfBot.Timing.Record('summon missing',entry,spec.key)
                return nil,'summon did not appear'
            end
            run.waiting[key]=true;return nil,'wait'
        end
    end
    run.waiting[key]=nil
    local sprite=BfBot.Exec._ResolveCasterForStep(caster)
    if not sprite then return nil,'summon no longer available'end
    local raw={};for k,v in pairs(entry.raw)do raw[k]=v end
    raw.future=nil;raw.casterRef=caster.ref;raw.caster=nil
    raw.plannedActor=BfBot.Plan.CasterKey(sprite)
    if not raw.plannedActor then return nil,'summon identity unavailable'end
    local byCaster=BfBot.Exec._BuildQueue({raw},0)
    local entries=byCaster and byCaster[BfBot.Exec._CasterKey(caster.ref)]
    local result=entries and entries[1]
    if not result then return nil,'planned spell is not in the actual summon book'end
    result.casterName=caster.name
    local rows=BfBot.Scan.GetCastableSpells(sprite)
    result.timing=BfBot.Plan.EstimateCast({casterRef=caster.ref,row=rows[result.resref]})
    return result
end
function S.Pump()
    local run=S.runtime;if not run then return end
    if BfBot.Exec._state~='running'then S.runtime=nil;return end
    local now=BfBot.Exec._GetGameTime()
    if not now then return end
    if run.started and now<run.started then BfBot.Exec.Stop();return end
    if run.lastPump and now-run.lastPump<3 then return end
    run.lastPump=now
    local waiting={};for key in pairs(run.waiting)do waiting[#waiting+1]=key end
    table.sort(waiting)
    for _,key in ipairs(waiting)do
        if S.runtime~=run then return end
        local caster=BfBot.Exec._casters[key]
        if caster and not caster.done then
            BfBot.Exec._ProcessCasterEntry(key,math.max(1,caster.index))
        else run.waiting[key]=nil end
    end
end
