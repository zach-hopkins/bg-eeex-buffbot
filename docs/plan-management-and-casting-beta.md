# BuffBot Redux: plans and casting

Redux is an independent single-player alternative based on BuffBot v1.10.1.
It uses one recipient dashboard and native engine casting. Earlier Balanced
Quick Cast experiments are retired; historical evidence is labelled separately.

## Make and review a plan

The pages are **Party Buffs → Order → Summary**. Party Buffs includes all
available buffs, including single-target and personal spells. Click eligible
recipient portraits to toggle assignments; a Party chip requests one area cast.
Summons supply spells but never become recipients. Summary shows what each PC
will receive. Icons and portraits come from the installed game.

Uses means **free / total available**. Thus 0/1 can mean the one available use
is already assigned, which is valid. Warnings mark only planned casts with no
usable source. Eligible portraits remain visible when uses run out. Search
returns the browser to the top; Name and Duration sort that browser only.
Displayed values update without moving rows until a browser-sort refresh.

Rows retain meaningful spell/variant qualifiers. Sources with different levels
or durations keep their properties even when the visible spell row is combined.
Auto favors stronger eligible sources and reserves shared uses. Spell Immunity
schools remain separate choices using one parent resource pool. Spontaneous
choices share their spell-level pool instead of multiplying available slots.

A selected chip's small upper-right gear opens its source menu beside the
click. Click the gear again to close it. Settings, presets and the HUD gear
also toggle closed on a second click. Only one popup is open at a time;
Escape closes it. Menus clamp to panel edges; dialogs use their own modal box.

## Lists, rests and shortcuts

Fresh saves start with empty **Pre-Battle Buffs** and **Wake Up Buffs** lists.
After Rest defaults to Wake Up Buffs; an empty list quietly does nothing.
Existing saved plans and rest preferences are preserved. Only completed rests
trigger a plan, once, after returning to a safe world state.

Up to eight lists support creation, renaming and confirmed deletion. Delete
keeps at least one list and disables After Rest if its selected list is deleted.
The confirmation checks the preset identity again before changing it.

Left-click the persistent gear beside the action bar, or press F11, to open
the planner. Right-click that gear and pick a named list to cast it directly.
This does not spend an action on a preset innate. Numbered BuffBot shortcuts,
their settings, grants, recharge hooks and installer string references are
retired. Upgrade cleanup removes only exact old BFBT[0-5][1-8] abilities,
including spent duplicates, and preserves real kit/spell innates and plans.

Export and Import use bounded, non-executable .bbp data files in
`override/bfbot_plans`. Import creates a new list in a free slot; it does not
overwrite a list or grant missing resources. Targets, variants, pinned sources,
enabled state, order mode and Custom positions round-trip. Format 2 includes
ordering metadata; older format 1 imports remain supported as Custom.

## Active buffs and unavailable spells

Choose **Skip Active**, **Refresh Low** or **Force All**. Refresh Low checks
read-only effect deadlines against a five-minute threshold. Force All attempts
every available request regardless of its current effect. These are session
execution choices; they do not alter spell durations.

An unavailable request does not block the list. It stays saved, the executor
skips it, and the game log reports the skipped count. Sources are validated
again before real actions. A disappearing summon ends only its own remaining
work. Cast counts are issued native attempts, not a guarantee that effects
landed: range, immunity and engine interruptions still apply.

## Native casting and fast-forward

Settings offers **Fast-forward 2x (Recommended)**, **4x** and **Normal**. The
selection also applies to rest plans and HUD launches. Old Balanced preferences
migrate to 2x; explicit native choices remain. Requested speed is not a promise
of the same wall-time gain on every machine.

The native engine performs spells, animations, aura waits, projectiles, slot
debits, item actions and delayed effects. Time really passes. Existing effects,
new buffs, fatigue, summons and world timers follow the same game clock. Redux
does not age effects afterward or jump the clock forward.

Fast-forward temporarily changes `EEex_CChitin.TIMER_UPDATES_PER_SECOND` and,
when available, caps rendering at 30 FPS while preserving a lower existing cap.
It restores the original rate and render settings on completion or interruption.
Failed timer reads/restores retain recovery ownership and retry. Cleanup does
not overwrite a speed value changed by somebody else. There is no wall-time
limit that kills a healthy paused run and no Tactical Time integration.

Combat, dialogue/cutscene/menu transitions, exit/load and execution failure
have recovery paths. A manual move can replace a character's queued actions;
that chain does not reliably resume. Use Stop before taking control. After 450
game ticks without progress, the watchdog ends a stalled run and restores speed.
Unissued work is counted as skipped; already issued attempts are not counted twice.

The run-level audit is `buffbot_fast_forward_audit.jsonl`. Smart timing also
retains a bounded scalar start/wait/finish/skip audit in `BfBot.Timing.lastAudit`.
It uses game ticks, so pause freezes deliberate waits and fast-forward scales
them naturally. No effect observer or continuous spellbook scan is installed.

## Order and intelligent start timing

**Smart Order**, **Long First** and **Custom** are saved per list, with a bright
selected state. New lists use Smart; old lists without mode metadata migrate
to Custom. Automatic modes update when buffs or preferred sources change.
An unchanged signature avoids repeatedly sorting. Replenished capacities are
used for ordering only: resting is not required to regain a stable Smart order,
and execution never invents spent uses.

Long First sorts known durations descending, with permanent effects first.
Smart starts there and makes bounded improvements using assigned durations,
casting factors and aura recovery. Its preview and real dispatch share one
read-only game-time model. Smart also delays shorter caster sequences to finish
closer to longer ones, preserving more buff time without deliberately extending
the earliest predicted finish. This is a practical heuristic, not a global
optimality guarantee. Native action delays can change actual completion times.

Pending work is rescheduled after actual completions, skips, summon binding
or changed casting speed/aura. Casting factors are parsed once; a small active
stat read checks pending casters at most once per game second and on completion.
There is no per-frame party/spellbook rebuild. Already-started casts stay fixed.
Long First and Custom start independent casters immediately, subject to real
prerequisites. Within each caster, the saved sequence is retained.

Incoming targeted buffs precede invisibility on the same recipient. Self and
Party actions are exempt. Supported spell/variant/item child graphs are inspected
for invisibility. Casting modifiers retain required relationships. Creating a
summon precedes its spells, and Project Image follows its owner's planned work.
Manual movement cannot put a summon spell before its creation. Invalid/cyclic
timing estimates disable deliberate JIT waits rather than rewriting effects.

Custom restores separately saved manual positions. New requests append; deleted
ones disappear. Source/recipient/variant choices carry between modes. Manual
movement selects Custom. Undo restores the previous mode/order without undoing
later caster choices. An executing run is never browser-sorted or reordered.

## Purposeful item sharing

A unique identified loose daily rechargeable item can supply eligible wearers
with **one or more** daily uses, including Vhailor's Helm and Gargoyle Boots.
All aliases reserve one physical charge pool. A self-only power is still used
by its recipient, who borrows the actual item. Native inventory usability is
checked; the feature never bypasses class/kit/conditional equipment restrictions.

Transfers use engine GiveItem actions. Only the owner and borrower wait for the
physical handoff/use/return; unrelated casters continue. The normal equipment
activation path restores the borrower's original gear, returns the real item
and repositions it to the original owner's backpack slot. No replacement item
is created. Native inventory calls verify executable metadata/signatures first;
unknown engines fail closed for sharing. BG2EE 2.6.6 and 2.7.3 bridges are supported.

A validated custody journal is saved before transfer. Stop, combat and load
recovery return the item when safe. Changed/duplicate gear, missing actors or
occupied return slots pause recovery and retain the journal. Consumables,
stacks, curses/undroppable items, full backpacks and different areas are refused.
Equipped-owner loans and summon equipment loans remain outside this beta.

## Planned and live summon casters

Add supported Simulacrum, Project Image, a summoning item use or a fixed caster
summon to the list. Its future spell sources then appear without a practice
summon. Copies are derived from the intended owner's current books, installed
slot rules and native level reduction. Vhailor's Helm uses the planned wearer,
not the inventory owner. Predictions refresh after relevant source changes;
changing buff recipients does not require another summon.

Prepared copies account for all memorized spells before buff filtering, since
attacks can compete for reduced slots. Native Simulacrum refreshes copied uses
then reduces its book; Project Image preserves spent uses. Spontaneous copies
use class-level capacities per known choice and reserve one shared level pool.
Equipped extra-slot effects do not refill a Simulacrum's reduced prepared book;
prediction follows that native behavior rather than inventing extra uses.
Fixed summons use bounded validated CRE spellbook data. Creation discovery
follows supported spell/item and external-effect wrappers, including Planetars.

Future sources exist only for enabled creation requests or an actual matching
live summon. Stable saved identities retain creator, intended owner and summon
type across order changes and export/import. A live summon and its planned
alias do not duplicate physical uses. Project Image's future reservations also
account for uses the original caster must spend before being locked.

At execution the creator casts normally. Independent work continues while the
summon appears. Strict native owner/type/resource checks bind the new creature,
excluding pre-existing or already-claimed creatures. Its real book and resources
are checked before each dependent action. Failed creation, a missing spawn or
a missing actual spell skips affected requests with a bounded wait. Other lanes
continue. Allied summon AI is temporarily prevented from replacing its planned
action chain; native scripts are unchanged and AI interruption is restored when
the lane ends or stops.

Existing allied summons remain usable. Ownership checks reject proven NPC
ownership; legacy discovery tolerates temporarily unresolved allied links after
loading, while a newly created planned source requires verified ownership.
Ordinary summon self-only spells are excluded because targets remain the six
PCs. Friendly caster-centered area powers are Party casts; actual range still
controls who receives them.

Scripts may add/remove powers after creation. Actual reconciliation handles
what exists, but static prediction cannot promise every mod-script addition.
Installed rules/resources are authoritative; the feature is not a simulator for
arbitrary scripts and does not secretly spawn preview creatures.

## Discovery, themes and limits

Buff discovery follows bounded spell/item child effects rather than a per-item
whitelist. Hostile effect categories and activation/deactivation stances are
hidden by default; manual Add and saved overrides remain available. Scrolls,
wands and unusual powers can need manual inclusion. Interactive item pickers
are refused before unsafe equipment movement or charge consumption.

Themes are SoD, IWD, BG1 and BG2. Auto reads UI++'s theme when present and uses
BG1 otherwise. Optional matching fonts and toolbar geometry may also be read;
UI++ files/settings are never changed. Standalone private art is bundled.

IWD:EE installation is experimental and untested. Single-player EET/BG2EE is the
primary test scope. 5E converted casters are excluded from this planner; the old
caster editor is retired. Historical Quick Cast helpers survive only as internal
compatibility APIs, never enabled by recipient plans. The removed Balanced
prototype's earlier measurements are historical, not current runtime behavior.

See the [comparison](buffbot-original-vs-redux.md),
[compatibility report](compatibility-test-report.md) and
[fast-forward investigation](fast-forward-performance-investigation.md) for
background and earlier evidence. Current acceptance is tracked in
[the future-caster/timing checklist](https://github.com/zach-hopkins/bg-eeex-buffbot/blob/main/docs/plans/2026-10-30-future-casters-and-timing.md).
