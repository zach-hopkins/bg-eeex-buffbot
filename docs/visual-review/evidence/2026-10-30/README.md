# Redux beta.5 acceptance — October 30, 2026

Native testing used the isolated EET copy, BG2EE 2.7.3.0. No personal game files,
saves or UI++ files were changed. IWD screenshots show its theme in EET;
IWD:EE gameplay was not tested.

| Evidence JSON | Result |
| --- | --- |
| redux-future-end-to-end | Sorcerer Simulacrum plus independent caster: 4 casts, 0 skips |
| redux-planned-helm-end-to-end | Borrowed helmet uses wearer's book: 5 casts, 0 skips; charge and equipment restored |
| redux-planned-image-end-to-end | Original work, Image, clone work: 4 casts, 0 skips; independent work continues |
| redux-planned-planetar-end-to-end | Fixed CRE source: 4 casts, 0 skips; AI control restored |
| redux-planned-divine-clone-0 / -1 | Druid/Shaman: 41 buff rows each match uses, caster level and duration |
| redux-dragon-disciple-end-to-end | 31 matching buff rows, including native kit bonus |
| redux-wizard-slot-gear-copy | Illusionist/RING08: class/kit book matches; extra-slot replay would invent uses |
| redux-inline-boots-run / -cancel | Real effects, charge/equipment return; cancellation retains unused charges |
| redux-inline-save-capture / -load-recovery | Save during swap, reload, original item returned with two charges |
| redux-fast-recovery-native / -load-native | Pause, stop, failed-read retry and reload restore speed/render ownership |
| redux-active-policy-native | Skip Active / Refresh Low / Force All on actual native effects |
| redux-missing-image-budget-native | Missing future Image leaves original caster's pool intact |
| redux-ui-order-dependency | Illegal move before creator rejected; valid order retained |
| redux-native-schedule-immediate / -smart | Short-lane buff time improves without lengthening preparation |
| redux-beta5-final-smoke | Fresh beta.5, modules loaded, idle, normal rate, no live loan |

Files retain native audit/log records with synthetic fixture identities.
`automated-regression.txt`: 1,110 passed, six deliberately deselected.
Subsequent localization/planner wording check: 80 passed.

PNG files include compact BG1/SoD pages, future-source menus, bottom/right fit,
active-buff policy, wide SoD pages and final BG1/BG2/IWD theme dashboards.
`*-final-*` uses the final qualifier helper; earlier captures predate that small
text fix. Native clicks verified recipient gear re-click, settings re-click,
menu edge fit and manual ordering rejection. The original gallery above retains
the unchanged modal designs and earlier full walkthrough.

`manifest.json` records file sizes and SHA-256 hashes. Arbitrary script-added
summon powers remain a live-discovery case. No claim is made that every possible
mod spell or IWD:EE game was exercised.
