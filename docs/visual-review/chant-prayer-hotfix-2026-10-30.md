# Chant/Prayer and selected-state hotfix

Reproduced from a separate copy of the user's newest quicksave. The personal
save was not modified. These are fixes after the beta.5 release, not a new release.

## Missing summon sources

Installed SPPR203 (Chant) and SPPR327 (Prayer) target the caster, then use
opcode 146 to launch separate friendly and hostile child spells. The friendly
children use projectile 337 with area flags 0xC0; the hostile children use 338
with flags 0x40. The parent itself uses projectile 1. The old direct-projectile
check consequently labeled both parents strictly personal and excluded them
from summon sources, even though the copy had real uses.

The classifier now follows a bounded, cycle-checked chain of self-delivered
child casts and recognizes the actual friendly area projectile. Enemy-only
areas and purely personal children do not become Party buffs. Scanner metadata,
predicted books and actual live books use the same delivery check. Existing
caster-specific radial requests retain their caster when normalized to Party.

Native evidence: enabling Anomen's planned Vhailor use adds two Chant and two
Prayer uses; disabling it removes those future sources. A real helmet-plus-two-
spells run completed three casts, zero skips. The copy had one use of each left.
After native projectile delivery, all six party members had SPPR203D and
`#PRAYERG` effects. Speed returned to 30 updates per second; no live loan remained.

## Selected state and source tooltips

The engine's `framesHeld` field can remain nonzero after a click. It is no longer
used as a persistent selection signal. Tabs and modes derive their frame from
their actual current selection. Spell-name tooltips list selected recipients
and their assigned sources. The recipient chip's portrait, name, duration,
background and borders share a source tooltip; the gear keeps its edit hint.
The hint uses passive labels beside the pointer, with a 750 ms entry delay.
It lays out once per hovered recipient/source, has no native scroll animation
or sound, and passes mouse clicks through to the original controls.

## Verification

- 100 focused regressions passed; complete suite: 1,116 passed, six deliberately
  excluded (five Windows symlink-privilege checks and experimental IWD fixture).
- Real original-book and predicted-book snapshots, physical helmet execution,
  actual spent uses and native effects verified in the private game copy.
- The personal install received only the four existing BuffBot runtime/source
  files after an explicit backup. No installer replay, save edits or game closure.
  A restart is required to load them.
- The user confirmed the tab behavior and the final nearby, silent tooltip in
  the private copy. The requested 750 ms delay passes exact-boundary checks,
  including leaving/re-entering and switching sources. Final focused group:
  78 passed. The full-suite count above predates this tooltip follow-up.
