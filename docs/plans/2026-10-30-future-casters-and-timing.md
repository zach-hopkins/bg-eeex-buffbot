# Future casters and Smart Order timing

Status: implementation, native acceptance, package verification and fork push complete.
Single-player EET/BG2EE is the tested scope. IWD:EE was deliberately not run.

## Accepted behavior

- [x] Party Buffs, Order, Summary; no character filters or exposed legacy caster
      editor. Preserve wake-up lists, source choices and partial execution.
- [x] Recipient source gear anchors beside the click and toggles closed.
      Settings/preset/HUD toggles and compact/wide edge placement verified.
- [x] Refresh Low / Force All use actual remaining effects; reserved uses are
      not unavailable warnings.
- [x] Eligible one-use/multi-use backpack lending reserves one physical item,
      checks engine usability, spends real charges and restores equipment.
      Only its owner/borrower wait; independent casters continue.
- [x] Recover speed/render settings on completion, stop, pause/retry and load.
      Preserve recovery ownership after failed reads and loaded return journals.

## Predicted and actual summon sources

- [x] Simulacrum uses current books, installed class/kit/WIS rules and native
      reduction/selection. No learning summon or hidden preview creature.
- [x] Consider attacks before buff filtering, native empty-name book sorting,
      refreshed Simulacrum memorization and spent Project Image uses.
- [x] Rebuild spontaneous capacity and reserve shared spell-level pools.
- [x] Borrowed Vhailor's Helm uses its planned wearer, not inventory owner.
- [x] Discover supported fixed caster summons from installed CRE/resources,
      including Planetar spell/effect wrappers.
- [x] Bounded forecast caches; stable creator/owner/type identities; live and
      planned aliases share physical resources. Missing Image creation does
      not consume its original caster's resources.
- [x] Creator-before-dependent order in Smart, Long First and Custom; reject
      illegal manual movement. Image waits for required original-caster work.
- [x] Bind verified new allied spawns, check real books and skip only affected
      requests on missing/failed creation. Independent work continues.
- [x] Protect summon action chains from script replacement and restore AI
      control on finish/stop. Summons remain sources, never recipients.
- [x] Preserve saved identities, export/import and save/load. Discard old-world
      transient execution while keeping the loaded item-return journal.

## Intelligent start timing

- [x] One read-only game-time model feeds Smart Order and real dispatch.
- [x] Delay shorter lanes toward the earliest modeled finish; retain useful
      long-first ordering within a lane.
- [x] Respect aura/casting speed, invisibility, creation, image locks and item
      custody. No global barrier between independent spellcasters.
- [x] Replan unstarted work after completions/skips, late summons and timing
      changes. Never move already-issued work or rewrite native buff effects.
- [x] Custom/Long First start immediately except real prerequisites. Game pause
      freezes waits; 2x/4x scale them. Tokens reject stale/duplicate callbacks.
- [x] Bounded timing audit records planned/actual starts, finishes, waits,
      bindings and skips. No Balanced aging or Tactical Time code added.

## Verification and delivery

- [x] 1,110 automated tests passed; six exclusions: five Windows symlink
      privilege tests and the deliberately excluded experimental IWD fixture.
      Subsequent localization/planner wording checks: 80 passed.
- [x] Native Sorcerer, Shaman, Druid, Dragon Disciple and Illusionist prediction.
      Druid/Shaman: 41 matching buff rows each; Dragon Disciple: 31.
      RING08 effects do not refill the native reduced prepared book.
- [x] End-to-end Simulacrum, borrowed Vhailor, Image and Planetar: 4/5/4/4 casts,
      respectively, all zero skips. Actual spells/effects/resources checked.
- [x] Two-use boots, cancellation, save during equipment swap and loaded return
      journal: original item, equipment and remaining charges recovered.
- [x] Native pause, failed-read restoration retry and same-party reload.
- [x] Immediate versus Smart fixture: 157 versus 154 game ticks; remaining
      Haste 62.8 to 69.6 seconds, Blur 292.07 to 298.93. That fixture had aura
      cleansing; separate clone chains exercised the ordinary 90-tick aura.
- [x] Compact BG1/SoD pages, changed source/settings/policy menus, bottom/right
      fit, wide SoD pages and other theme smoke checks. The original full modal
      gallery is historical; current changed-control captures are October 30.
- [x] Fresh on-disk beta.5 loads: modules present, idle, normal rate, no live loan.
- [x] README, feature guide, comparison and evidence index updated.
- [x] Player archive verified (463 files, bundled art hashes and source equality).
- [x] Implementation commit `00f3b65` pushed to Redux fork `main`; remote SHA
      verified. This final documentation checkpoint records that verification.

Evidence: [October 30 review](../visual-review/evidence/2026-10-30/README.md).

## Deliberate limits

This is a practical scheduler, not a proof of global optimality. Native actions
and projectiles vary, so pending estimates are revised. Arbitrary script-added
summon powers may require live discovery; actual reconciliation skips affected
requests. Equipped-owner loans and summon equipment lending remain excluded.
IWD:EE gameplay and multiplayer are not claimed tested. Personal installation,
saves and UI++ files were not modified.
