# BuffBot Redux

**In-game buff automation for Baldur's Gate: Enhanced Edition.**

Pick the buffs your party needs, then cast the whole list with one click. BuffBot finds who can cast each spell and lets party members cast at the same time.

This is an **independent single-player beta alternative to [BuffBot](https://github.com/Chrizhermann/bg-eeex-buffbot)**, originally based on v1.10.1. Redux puts the person getting a buff first. It uses one party planner; the old caster editor is retired.

## Features

- **One party list** — see your buffs in one place. Click a portrait to give that person a buff. A **Party** button adds one party-wide cast.
- **Automatic caster choice** — BuffBot picks an eligible caster, usually favoring a longer duration. You can choose a caster yourself. Shared spells and item charges are counted together, so the plan cannot spend the same use twice.
- **Skip or refresh active buffs** — skip buffs you already have, refresh those running low, or force every available cast.
- **Clear spell choices** — see icons, uses and durations. Spell Immunity's schools have separate rows, but spend the same spell slots.
- **Up to eight saved lists** — create, rename, delete, export and import plans. Your plans stay with your save.
- **Helpful cast order and timing** — Smart Order puts long buffs first and lets shorter caster sequences wait so their buffs finish closer together. It keeps incoming spells before invisibility and summon creation before the summon’s spells. Custom keeps your own order.
- **Faster preparation** — normal spell and item actions run at **2x speed** by default. Casting rules, spell slots, buff timers and delayed effects still use the game's own clock.
- **After-rest buffs** — choose a list to cast after a completed rest. Interrupted rests do not trigger it.
- **Item powers** — use supported powers from carried gear and potions. For eligible daily-use gear, a party member can borrow it, use it and return it. The real charges are spent.
- **Plan summon spells ahead** — add Simulacrum, Project Image, Vhailor’s Helm or a supported caster summon, then assign its predicted spells in the same list. No practice summon is needed. Buff targets remain the six party members.
- **Four themes** — SoD, IWD, BG1 and BG2. Infinity UI++ is optional. Auto follows its theme if installed; otherwise BuffBot uses BG1.

## Requirements

- **BG:EE, BG2:EE or EET**. **IWD:EE is experimental and untested**; the installer accepts it, but game-specific behavior and item sharing are not verified.
- **[EEex](https://github.com/Bubb13/EEex) v0.11.0-alpha or later**. EEex v1 is recommended. **LuaJIT is recommended, but optional.**

**LuaJIT enables automatic item borrowing, file import/export and file logging.**
Choose the **Recommended — with LuaJIT** download for these features; it includes
our setup helper, which activates the matching LuaJIT DLLs from your installed EEex.
The **Without LuaJIT** download keeps party planning, normal casting and plans
saved with your game. Automatic borrowing and file features are unavailable with
built-in Lua; some backpack powers need manual equipment changes. Both downloads
require EEex, and the selected UI language works in either mode.

Redux has been tested mainly in copied single-player BG2:EE/EET installs. Multiplayer and every game/mod combination have not been checked.

## Languages

The installer offers English, Simplified Chinese, Italian, German, French, Spanish, Polish, Russian and Brazilian Portuguese. Some new Redux text still uses English fallback text.

<details>
<summary>Translation status and file details</summary>

WeiDU copies the selected UTF-8 catalog to `override/bfbot_l10n.tra` and embeds it for built-in Lua. BuffBot reads the file when file access is available and uses the embedded copy otherwise; it fetches none of its own strings from the game TLK and adds none to it. Numbered preset innates and their string-reference installation are retired.

The six new catalogs began as AI-authored translations. The German catalog has since been reviewed by the maintainer; none has yet been validated in-game. Native-speaker corrections remain welcome. Earlier Chinese user screenshots confirmed readable CJK labels at the tested resolution/font; alternate resolutions/fonts remain pending. Italian was tested by its contributor. These checks do not mean every new Redux label has been translated or reviewed.

</details>

## Installation

1. Download one ZIP from [Releases](https://github.com/zach-hopkins/BuffBot-Redux/releases/tag/v1.10.1-redux-beta.6):
   - **[Recommended — with LuaJIT](https://github.com/zach-hopkins/BuffBot-Redux/releases/download/v1.10.1-redux-beta.6/buffbot-v1.10.1-redux-beta.6-RECOMMENDED-with-LuaJIT.zip)** — includes the LuaJIT setup helper; installs it before BuffBot.
   - **[Without LuaJIT](https://github.com/zach-hopkins/BuffBot-Redux/releases/download/v1.10.1-redux-beta.6/buffbot-v1.10.1-redux-beta.6-without-LuaJIT.zip)** — installs BuffBot alone.
2. Extract the ZIP into your game folder and run **Install-BuffBot.cmd**.
3. Start the game through **InfinityLoader.exe**.

For manual component selection or Project Infinity, use **setup-buffbot.exe**.
The Without LuaJIT installer leaves an already-active LuaJIT runtime in place.

When updating an installation that uses BuffBot's LuaJIT helper, select or reinstall both components together. If EEex already provides the matching LuaJIT runtime, only the main component is needed. In Project Infinity, put the optional LuaJIT helper before the main component when using both. To use built-in Lua, skip the helper and leave EEex's own optional LuaJIT component disabled. Finish any item borrowing/return in progress before switching runtimes.

For EET, BuffBot can go after `EET_end`. With EEex v0.11, install EEex and BuffBot after generalized biffing and later steps that replace files. Do not downgrade an existing EEex v1 save just to use this mod.

To uninstall, remove the main component first, then the LuaJIT helper if you used it.

## Usage

### Open and cast

- Press **F11** or left-click the **gear beside the action bar** to open BuffBot.
- Right-click the gear and pick a saved list to cast it directly. This does not add an innate-ability action before the plan.

### Make a list

1. Choose a list at the top right, or click **+** to make one.
2. In **Party Buffs**, find a spell and click the portraits of the people who need it. Click again to remove it. **Clear** removes that row's choices.
3. Use the search box to narrow the list. Click **Name** or **Duration** to sort the browser. This does not change casting order.
4. Open **Order** to choose the cast order or a preferred caster.
5. Open **Summary** to check which buffs each person will get.
6. Click **Cast**.

**Uses** shows free uses / total uses. For example, **0/1** means one use is available and already reserved by your plan. Hover over the count for a breakdown. A warning appears only when a planned cast has no usable source. Portraits stay visible when uses run out, so you can move a buff from one person to another. Self-only spells stay self-only. A duration range means the available casters can give different durations; each portrait shows its assigned or next-cast duration.

If a planned spell is unavailable, BuffBot skips it and casts the rest. The game message log shows how many planned casts were skipped. Missing entries stay in your saved list so they can work again after you rest or restore their source.

When a run ends normally, **Buff plan completed** appears above the party leader,
or in the message log if floating text is unavailable. The notice includes the
number of casts skipped during execution. It appears after pending item returns;
it confirms the run ended, rather than proving every spell effect landed.

After assigning a buff, the larger **Spell Source** message tells you who will cast it. Click the small gear in that selected recipient's upper-right corner to choose a different source, or leave it on **Auto**. The menu opens beside your click. Click the same gear again to close it.

In **Settings → Active buffs**, **Skip active** avoids buffs you already have. **Refresh Low** also renews recognized buffs with less than five minutes left. **Force All** spends uses even if the buff is already active. Unknown or permanent durations are kept by Refresh Low. This choice applies to the current session. Some effects and modded spells are harder to detect. Use **Add spell / item** if a power is missing, or **Hide** to tidy the browser. Hidden entries already in a plan stay planned.

### Choose an order

- **Smart Order**: long buffs first, with casting time and invisibility taken into account. It updates when you add, remove or change buffs.
- **Long First**: sort by duration, longest first. It also updates as you edit.
- **Custom**: restore your saved manual order. Use the up/down buttons to move a cast; moving one selects Custom.
- **Undo**: undo the last order-mode change when available.

The active mode is highlighted and saved with the list. Automatic ordering treats prepared spells and daily charges as replenished, so spending a spell does not shuffle the list. **Casting still checks your real remaining uses.** Existing lists start in Custom to preserve their order; new lists start in Smart Order.

### Set up wake-up buffs

Fresh installs start with two empty lists: **Pre-Battle Buffs** and **Wake Up Buffs**. **After Rest** starts on Wake Up Buffs. Add spells to that list to use it; an empty list quietly does nothing.

The After Rest picker can use any list, or **Off**. It is separate from the list you are editing. Existing saves keep their lists and rest choice.

After a completed standard eight-hour rest, BuffBot waits until the party can act. Combat cancels a pending run. Unavailable casts are skipped and counted in the message log; the rest of the list still runs. Shortened rests and other mods' rest systems need more testing.

### Casting speed and interruptions

In **Settings → Casting**, choose **Fast-forward 2x (Recommended)**, **4x**, or **Normal**. 4x is experimental and may not be faster on every setup. BuffBot restores the old speed when casting ends or stops.

Time really passes faster during the plan. Existing buffs, fatigue and delayed effects follow that time too. Redux's party planner no longer uses Balanced Quick Cast or rewrites buff expiry times.

Independent casters can act together. Smart Order deliberately delays shorter sequences to waste less buff time; Long First and Custom start independent casters immediately. Real prerequisites still apply: a summon must exist, shared gear must arrive, and incoming spells must finish before invisibility. Combat and lost player control can stop casting. Moving someone yourself may interrupt their current spell; their chain does not reliably resume. Let the plan finish before giving new orders when possible.

### Items, summons and saved plans

BuffBot scans supported powers on identified carried items, including backpack gear. Darkfire Bow's Improved Haste and Gargoyle Boots are supported. Eligible daily-use gear can be lent even when it has just one use, such as Vhailor's Helm. Item borrowing checks whether the borrower can wear the gear, shares its real charges, and tries to return it safely. One use can be assigned to only one person. Unsafe swaps, ambiguous copies and interactive item choices may need manual use.

You can plan spells from supported summons before they exist. First add their creation spell or item use, then choose the future summon as a Spell Source. BuffBot predicts copies from the intended caster’s current book and installed rules; a borrowed Vhailor’s Helm uses its wearer’s book. Fixed caster summons use their installed creature spellbooks. Changing recipients does not require another summon.

Creation stays before dependent casts in every order mode. When the creature appears, BuffBot checks its actual ownership, spells and uses. A failed summon or missing spell skips only the affected work. Existing allied summons also supply spells. Project Image keeps its owner’s casts before creation and does not promise extra copies of uses the owner must spend first. Summon equipment borrowing is not supported.

Use the gear menu to **export/import** a party plan as a `.bbp` file in `override/bfbot_plans`. Exports keep targets, caster choices, variants and order mode. They do not grant missing spells or items; those casts stay unavailable.

## Known Limitations

- **Single-player first.** Multiplayer behavior has not received the same testing.
- **5E Spellcasting:** converted casters are excluded from the party planner. Historical scanner compatibility remains, but the retired caster editor is no longer offered.
- **Legacy controls:** repeats, row locks and per-caster lists are not offered by Redux. Existing party plans, rest lists and source choices are preserved.
- **Missing powers:** automatic discovery does not cover every modded effect. Container contents are not scanned. Scrolls, wands and unusual powers may need manual inclusion/use; automatic coverage is not promised.
- **Item safety:** chest armor, restricted gear, duplicate copies and some child-spell powers can need manual handling. See the [compatibility report](docs/compatibility-test-report.md) for tested exceptions.
- **Estimates:** displayed durations do not capture every kit bonus or conditional effect. A cast appearing in the log does not prove its effect landed.
- **Summon predictions:** unusual scripts can add or remove powers after creation. The real creature is checked before casting; resource prediction cannot promise every scripted addition in advance.
- **Platform/UI:** file pickers use Windows directory listing. Other platforms and all resolutions/fonts have not been checked.

For more detail, see the [feature guide](docs/plan-management-and-casting-beta.md), [comparison with original BuffBot](docs/buffbot-original-vs-redux.md), and [visual review](docs/visual-review/review.md). Source-only review material is also available in the separate review download.

## Testing & Bug Reports

Please [open an issue on this fork](https://github.com/zach-hopkins/bg-eeex-buffbot/issues) with your game/EEex versions, mod list, steps to repeat the problem, and a screenshot or log if useful.

In the game console, `BfBot.Test.RunAll()` runs the built-in checks. Logs include `buffbot_test.log`, `buffbot_exec.log` and `buffbot_fast_forward_audit.jsonl`. For legacy 5E problems, run `BfBot.FiveE.Diagnose()` and include `buffbot_5e.log` and `WeiDU.log`.

## Contributing

Language pull requests are welcome. Translate a complete catalog from `buffbot/lang/english/setup.tra`; preserve IDs, placeholders and installer tokens. Use a safe lowercase folder name, set `@113` to it, and add its `LANGUAGE` stanza in `buffbot/setup-buffbot.tp2`. Keep UTF-8 and the existing one-line tilde format. Include your preferred translator credit.

Run `python -m pytest tests/test_localization.py tests/test_release_package.py -q` before submitting a language change.

<details>
<summary>Development-only deployment</summary>

From a source checkout with EEex LuaJIT already active, run `bash tools/deploy.sh /path/to/game`. Players should use WeiDU instead.

The raw development deploy keeps an existing WeiDU-selected `override/bfbot_l10n.tra` byte-for-byte. With no selected catalog it uses the English fallback. The deploy never touches a TLK and needs neither Python nor a TLK file. It stops before copying anything when `override/bfbot_l10n.tra` exists but is not a regular file.

Leftover `bfbot_strrefs.txt` and obsolete `bfbot_l10n.txt` files are left alone and unused.

</details>

## AI-Assisted Development

Original BuffBot was developed with Claude Code; Redux was developed with OpenAI Codex. Human choices and AI assistance shaped the code and tests. The source and test evidence are open for review.

## Credits

- **[Chrizhermann](https://github.com/Chrizhermann)** — original BuffBot, the base for this fork.
- **[EEex](https://github.com/Bubb13/EEex)** by Bubb — makes this entire mod possible
- **[Bubble Buffs](https://github.com/factubsio/BubbleBuffs)** by factubsio — original inspiration (Pathfinder: WotR)
- **[5E Spellcasting](https://github.com/UnearthedArcana/5E_spellcasting)** by subtledoctor — the casting system used by BuffBot's experimental 5E compatibility
- **Endarire** — encouragement and the request for 5E Spellcasting compatibility
- **[robovoid](https://github.com/robvoid)** — original Simplified Chinese translation in [PR #50](https://github.com/Chrizhermann/bg-eeex-buffbot/pull/50); the implementation was reworked on BuffBot's current localization architecture
- **[Sauler89](https://github.com/Sauler89)** — Italian translation
- **OpenAI Codex** — initial AI-authored German, French, Spanish, Polish, Russian, and Brazilian Portuguese translations; German reviewed by the maintainer
- **[Claude Code](https://claude.ai/code)** by Anthropic — AI development assistant

## License

[MIT](LICENSE)
