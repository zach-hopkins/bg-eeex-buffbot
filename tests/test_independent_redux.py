"""The single Redux dashboard exposes policy and source edits without legacy views."""
from pathlib import Path
import pytest
from lupa.luajit21 import LuaRuntime
from test_visual_redesign import visual
from test_party_dashboard import dashboard
from test_party_planner import lua

ROOT=Path(__file__).resolve().parents[1]


def test_order_labels_pinned_future_caster_instead_of_marking_it_missing(visual):
    assert visual.execute('''
      local s=snapshot();source(s,'WARD','A',120,'a',2)
      setup(s,{request('WARD','A')})
      bbPartyRequests[1].request.source='future:A'
      U.snapshot.casterActors={['future:A']={name='A - Simulacrum (planned)'}}
      return V.CasterName(1)=='A - Simulacrum (planned)'
    ''')


def test_compact_duration_ranges_fit_without_losing_fractional_differences(visual):
    assert visual.execute('''
      U.RowDuration=function()return '12.0m - 20.0m'end
      V.wide=false;assert(V.RowDuration(1)=='12–20m')
      U.RowDuration=function()return '3.1m - 4.4m'end
      assert(V.RowDuration(1)=='3.1–4.4m')
      V.wide=true;return V.RowDuration(1)=='3.1m–4.4m'
    ''')


def test_friendly_qualifiers_keep_same_named_priest_spells_distinguishable(visual):
    assert visual.execute('''
      U.snapshot={groups={A={sources={{row={kind='spl',spellType=2,resref='SPPR603'}}}},
                         B={sources={{row={kind='spl',spellType=2,resref='SPPR698'}}}}}}
      bbPartyRows={{key='A',name='Blade Barrier',qualifier='Spell / SPPR603'},
                   {key='B',name='Blade Barrier',qualifier='Spell / SPPR698'}}
      return V.RowQualifier(1)~=V.RowQualifier(2)
        and V.RowQualifier(1):find('SPPR603',1,true)~=nil
        and V.RowQualifier(2):find('SPPR698',1,true)~=nil
    ''')


def test_chip_gear_edits_only_its_recipient_and_retains_other_requests(visual):
    assert visual.execute('''
      local s=snapshot();source(s,'WARD','A',120,'a',2);source(s,'WARD','B',60,'b',2)
      setup(s,{request('WARD','A'),request('WARD','B')});findrow('WARD')
      assert(U.EditRecipientSource(bbPartyRowSelection,2))
      assert(U.choiceRequest.target=='B' and U.choiceRequest==U.preset.requests[2])
      U.SetCaster('B')
      findrow('WARD')
      return U.preset.requests[2].source=='B' and U.preset.requests[1].source==nil
        and #U.preset.requests==2 and V.ChipSourceTip(bbPartyRowSelection,2):find('Spell Source: B',1,true)~=nil
        and bbPartyFeedback:find('Spell Source: B',1,true)~=nil
    ''')


def test_released_buttons_ignore_stale_hold_counters_and_keep_selected_state(visual):
    assert visual.execute('''
      EEex_Menu_GetItem=function()return {framesHeld=1}end
      assert(V.ButtonFrame('rxCast',0)==0 and V.ButtonFrame('rxBuffs',2)==2)
      assert(V.ButtonFrame('rxOptions',0,1)==0)
      assert(V.ButtonFrame('rxBuffs',0)==0 and V.ButtonFrame('rxOrder',2)==2)
      assert(V.ButtonFrame('rxOrder',0)==0 and V.ButtonFrame('rxSummary',2)==2)
      EEex_Menu_GetItem=function()error('unavailable')end
      return V.ButtonFrame('rxCast',0)==0
    ''')


def test_selected_spell_and_chip_tooltips_show_assigned_source(visual):
    assert visual.execute('''
      local s=snapshot();source(s,'WARD','A',120,'a',2);source(s,'WARD','B',60,'b',2)
      setup(s,{request('WARD','A'),request('WARD','B')});findrow('WARD')
      U.EditRecipientSource(bbPartyRowSelection,2);U.SetCaster('B');findrow('WARD')
      local tip=V.RowTip(bbPartyRowSelection)
      return V.ChipTip(bbPartyRowSelection,2):find('Source: B',1,true)~=nil
        and tip:find('Source: B',1,true)~=nil and tip:find('Source: A',1,true)~=nil
    ''')


@pytest.mark.parametrize('wide',[False,True])
def test_list_tooltip_uses_hovered_recipient_and_scroll_not_selected_row(visual,wide):
    visual.globals().wide=wide
    assert visual.execute('''
      local s=snapshot();source(s,'WARD','A',120,'a',2);source(s,'WARD','B',60,'b',2)
      setup(s,{request('WARD','A'),request('WARD','B')});findrow('WARD')
      U.EditRecipientSource(bbPartyRowSelection,2);U.SetCaster('B');findrow('WARD')
      V.popup=nil;V.wide=wide
      local index=bbPartyRowSelection;local width=wide and 1764 or 1124
      local rh=wide and 54 or 48;local prefix=0
      for _,p in ipairs(wide and {3,22,4,7}or{4,20,5,9})do prefix=prefix+math.floor(width*p/100)end
      local chip=math.floor(width*(wide and 10 or 9)/100)
      EEex_Menu_GetItemArea=function()return 100,200,width+28,464 end
      EEex_Menu_GetItem=function()return {scrollbar={top=(index-1)*rh+10}}end
      local mx,my=100+prefix+chip*1.5,210
      EEex_Menu_GetMousePos=function()return mx,my end
      bbPartyRowSelection=999
      assert(V.DashboardHover().text:find('Source: B',1,true))
      mx=100+prefix+chip*.5
      assert(V.DashboardHover().text:find('Source: A',1,true))
      V.popup='menu';assert(V.DashboardHover()==nil);V.popup=nil
      mx=100+width+5;assert(V.DashboardHover()==nil)
      mx=90;return V.DashboardHover()==nil
    ''')


def test_source_hover_is_passive_and_does_not_trigger_native_scroll_tooltips():
    menu=(ROOT/'buffbot/BfBotRx.menu').read_text(encoding='utf-8')
    assert 'tooltip lua "BfBot.Visual.DashboardTip()"' not in menu
    hint=menu[menu.index('name "rxHoverText"'):]
    assert 'ignoreEvents' in hint.split('}')[0]


def test_hover_hint_positions_once_per_recipient_and_is_silent_and_bounded(visual):
    assert visual.execute('''
      V.active=true;local now=0;local changes=0
      Infinity_GetClockTicks=function()return now end
      Infinity_GetScreenSize=function()return 1280,720 end
      Infinity_SetArea=function()changes=changes+1 end
      local target={text='Source: Anomen',key='ward:one',x=1260,y=25}
      V.DashboardHover=function()return target end
      V.UpdateHover();assert(not V.hoverVisible and changes==0)
      now=749;V.UpdateHover();assert(not V.hoverVisible and changes==0)
      now=750;V.UpdateHover();assert(V.hoverVisible and changes==6)
      local rect=V.hover.rect
      assert(rect[1]>=8 and rect[1]+rect[3]<=1272 and rect[2]>=8 and rect[2]+rect[4]<=712)
      target={text=target.text,key=target.key,x=1250,y=30}
      for i=1,30 do now=now+40;V.UpdateHover()end
      assert(changes==6 and V.hoverVisible)
      target=nil;V.UpdateHover();assert(not V.hoverVisible)
      target={text='Source: Aerie',key='ward:two',x=300,y=400}
      V.UpdateHover();now=now+749;V.UpdateHover();assert(not V.hoverVisible and changes==6)
      now=now+1;V.UpdateHover()
      assert(V.hoverVisible and changes==12)
      return V.DashboardTip()==''
    ''')


def test_source_menu_uses_click_anchor_before_open_and_same_gear_closes(visual):
    assert visual.execute('''
      local s=snapshot();source(s,'WARD','A',120,'a',2);source(s,'WARD','B',60,'b',2)
      setup(s,{request('WARD','A'),request('WARD','B')});findrow('WARD');V.active=true
      V.x=0;V.y=0;V.w=1280;V.h=720
      EEex_Menu_GetItemArea=function()return 68,160,1152,464 end
      EEex_Menu_GetItem=function()return {scrollbar={top=900}}end
      EEex_Menu_GetMousePos=function()return 780,340 end
      local openedAt
      local push=Infinity_PushMenu
      Infinity_PushMenu=function(n)
        if n=='BUFFBOT_RX_POPMENU' then openedAt=U.choiceAnchor;V.LayoutPopup() end
        push(n)
      end
      V.DashboardClick(8)
      assert(openedAt and openedAt.x==772 and openedAt.y==352)
      assert(U.choiceRequest.target=='B' and V.ChipSourceOpen(bbPartyRowSelection,2))
      assert(V.popupRect[2]==358 and areas.rxMenuTrigger[2]==324)
      assert(areas.rxMenuTrigger[1]<=780 and areas.rxMenuTrigger[1]+areas.rxMenuTrigger[3]>=780)
      V.DashboardClick(8)
      return V.popup==nil and not stack.BUFFBOT_RX_POPMENU and #U.preset.requests==2
    ''')


def test_settings_gear_toggles_and_repeats_its_trigger_on_popup(visual):
    assert visual.execute('''
      local s=snapshot();source(s,'WARD','A',120,'a',2);setup(s)
      V.active=true;V.x=0;V.y=0;V.w=1280;V.h=720
      EEex_Menu_GetItemArea=function(n)return 1160,30,30,30 end
      V.ToggleChoices('settings');V.LayoutPopup()
      assert(stack.BUFFBOT_RX_POPMENU and areas.rxMenuTrigger[1]==1160 and areas.rxMenuTrigger[2]==30)
      V.ToggleChoices('settings')
      return V.popup==nil and not stack.BUFFBOT_RX_POPMENU
    ''')


def test_main_hud_gear_remains_a_close_toggle_above_panel_and_menu_shields(visual):
    assert visual.execute('''
      BfBot.UI={_hudX=900,_hudY=660}
      V.LayoutHudTrigger('rxHudTrigger');V.LayoutHudTrigger('rxMenuHudTrigger')
      return areas.rxHudTrigger[1]==904 and areas.rxHudTrigger[2]==664
        and areas.rxMenuHudTrigger[3]==48 and areas.rxMenuHudTrigger[4]==48
    ''')
    menu=(ROOT/'buffbot/BfBotRx.menu').read_text(encoding='utf-8')
    assert 'name "rxHudTrigger"' in menu and 'name "rxMenuHudTrigger"' in menu


def test_only_three_product_pages_and_separate_source_cells():
    menu=(ROOT/'buffbot/BfBotRx.menu').read_text(encoding='utf-8')
    fallback=(ROOT/'buffbot/BuffBot.menu').read_text(encoding='utf-8')
    assert "Party Buffs" in menu and 'rxRecipient' not in menu
    assert 'bpRecipient' not in fallback and 'BUFFBOT_MAIN' not in fallback
    assert 'BfBot.Visual.DashboardClick(cellNumber)' in menu
    assert 'BfBot.Visual.ChipSourceTip(rowNumber,6)' in menu


def test_refresh_and_force_check_remaining_time_without_writing_deadlines():
    lua=LuaRuntime(unpack_returned_tuples=True)
    lua.execute('BfBot={REFRESH_LOW_SECONDS=300,Persist={GetRefreshBelow=function()return 0 end}}')
    lua.execute((ROOT/'buffbot/BfBotExe.lua').read_text(encoding='utf-8'))
    assert lua.execute('''
      local E=BfBot.Exec
      local remaining=E._EffectRemaining({m_durationType=4096,m_duration=1800},1500)
      assert(remaining==20 and E._RefreshThreshold(1)==300)
      assert(E._ActiveBlocksCast(remaining,0,false))
      assert(not E._ActiveBlocksCast(remaining,300,false))
      assert(not E._ActiveBlocksCast(math.huge,0,true))
      assert(E._ActiveBlocksCast(math.huge,300,false))
      E.SetForceMode(2)
      return E.GetForceMode()==2 and E._ForceAll(2) and E.CycleForceMode()==0
    ''')
