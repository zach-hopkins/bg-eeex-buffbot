#!/bin/bash
set -e

# tools/deploy.sh â€” Copy BuffBot files to game override for dev testing
# Usage:
#   bash tools/deploy.sh /path/to/game      # explicit path
#   BGEE_DIR=/path/to/game bash tools/deploy.sh  # env var
#   (or set BGEE_DIR in tools/deploy.conf)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_DIR="$(cd "$SCRIPT_DIR/.." && pwd)/buffbot"

# Precedence: $1 (positional arg) > $BGEE_DIR (env var) > deploy.conf (local default).
# Source deploy.conf only if BGEE_DIR isn't already set in the environment, so env-var
# overrides for test installs (e.g. BGEE_DIR=".../- Copy - Copy") aren't clobbered.
[ -z "$BGEE_DIR" ] && [ -f "$SCRIPT_DIR/deploy.conf" ] && source "$SCRIPT_DIR/deploy.conf"

GAME_DIR="${1:-${BGEE_DIR:?Set BGEE_DIR in tools/deploy.conf or pass game dir as argument}}"
OVERRIDE_DIR="$GAME_DIR/override"
CATALOG_PATH="$OVERRIDE_DIR/bfbot_l10n.tra"

# Verify source files exist
for f in M_BfBot.lua BfBotCor.lua BfBotLoc.lua BfBotThm.lua BfBotCls.lua BfBotScn.lua BfBot5e.lua BfBotExe.lua BfBotMp.lua BfBotPer.lua BfBotPln.lua BfBotTim.lua BfBotSum.lua BfBotIO.lua BfBotShr.lua BfBotFst.lua BfBotRst.lua BfBotPUI.lua BfBotVD.lua BfBotVis.lua BfBotRx.menu BfBotInn.lua BfBotUI.lua BfBotTst.lua BuffBot.menu; do
    if [ ! -f "$SRC_DIR/$f" ]; then
        echo "ERROR: $SRC_DIR/$f not found"
        exit 1
    fi
done

# Verify game override directory exists
if [ ! -d "$OVERRIDE_DIR" ]; then
    echo "ERROR: Game override directory not found: $OVERRIDE_DIR"
    exit 1
fi

# Preserve a selected language catalog; old innate references are unused.
if [ -e "$CATALOG_PATH" ] || [ -L "$CATALOG_PATH" ]; then
    if [ ! -f "$CATALOG_PATH" ] || [ -L "$CATALOG_PATH" ]; then
        echo "ERROR: override/bfbot_l10n.tra exists but is not a regular file." >&2
        exit 1
    fi
    echo "Runtime UI language: preserving existing WeiDU-selected runtime catalog; no TLK changes"
else
    echo "Runtime UI language: English fallback; no TLK changes"
fi

# Copy source files
for f in M_BfBot.lua BfBotCor.lua BfBotLoc.lua BfBotThm.lua BfBotCls.lua BfBotScn.lua BfBot5e.lua BfBotExe.lua BfBotMp.lua BfBotPer.lua BfBotPln.lua BfBotTim.lua BfBotSum.lua BfBotIO.lua BfBotShr.lua BfBotFst.lua BfBotRst.lua BfBotPUI.lua BfBotVD.lua BfBotVis.lua BfBotRx.menu BfBotInn.lua BfBotUI.lua BfBotTst.lua BuffBot.menu; do
    cp "$SRC_DIR/$f" "$OVERRIDE_DIR/$f"
done

# Copy only BuffBot-owned assets. Batch the copy: starting two Windows/MSYS
# processes per texture makes a 300-page skin pack needlessly slow to deploy.
shopt -s nullglob
asset_files=("$SRC_DIR"/visual/*.BAM "$SRC_DIR"/visual/*.PVRZ "$SRC_DIR"/*.MOS "$SRC_DIR"/*.PVRZ "$SRC_DIR"/*.BAM)
if [ "${#asset_files[@]}" -gt 0 ]; then
    cp "${asset_files[@]}" "$OVERRIDE_DIR/"
fi
shopt -u nullglob

# Create presets directory for config export/import
mkdir -p "$OVERRIDE_DIR/bfbot_plans"

# Copy diagnostic tools (optional, for development)
if [ -f "$SCRIPT_DIR/probe_clone.lua" ]; then
    cp "$SCRIPT_DIR/probe_clone.lua" "$OVERRIDE_DIR/probe_clone.lua"
fi

echo ""
echo "Done. Files deployed:"
ls -la "$OVERRIDE_DIR"/M_BfBot.lua "$OVERRIDE_DIR"/BfBot*.lua "$OVERRIDE_DIR"/BuffBot.menu

echo ""
echo "To test in-game:"
echo "  1. Launch game via InfinityLoader.exe"
echo "  2. Load a save game"
echo "  3. Open the in-game console (Ctrl-Space; needs CLUAConsole=1 in baldur.ini)"
echo "  4. Type: BfBot.Test.RunAll()"
echo ""
echo "UI panel:"
echo "  BfBot.UI.Toggle()  or  F11 key"
