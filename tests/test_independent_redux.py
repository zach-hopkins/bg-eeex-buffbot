"""The single Redux dashboard exposes policy and source edits without legacy views."""
from pathlib import Path
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


def test_selected_and_held_frames_and_failed_engine_lookup(visual):
    assert visual.execute('''
      EEex_Menu_GetItem=function()return {framesHeld=1}end
      assert(V.ButtonFrame('rxCast',0)==2 and V.ButtonFrame('rxBuffs',2)==2)
      assert(V.ButtonFrame('rxOptions',0,1)==1)
      EEex_Menu_GetItem=function()error('unavailable')end
      return V.ButtonFrame('rxCast',0)==0
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
