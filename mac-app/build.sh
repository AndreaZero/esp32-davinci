# ESP32-DaVinci Bridge — macOS app
#
# Run without packaging:
#   cd mac-app && python3 app.py
#
# Build .app (requires PyInstaller):
#   ./build.sh
#
# Optional DMG (requires create-dmg: brew install create-dmg):
#   ./build.sh --dmg

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
DIST="$APP_DIR/dist"
BUILD="$APP_DIR/build"
NAME="ESP32-DaVinci-Bridge"

cd "$APP_DIR"

echo "Installing build deps (user)…"
python3 -m pip install --user -q pyinstaller pyserial \
  "pyobjc-framework-Cocoa>=10.0" \
  "pyobjc-framework-Quartz>=10.0" \
  "pyobjc-framework-ApplicationServices>=10.0"

rm -rf "$DIST" "$BUILD"

echo "Building $NAME.app…"
python3 -m PyInstaller \
  --noconfirm \
  --windowed \
  --name "$NAME" \
  --paths "$ROOT/bridge" \
  --add-data "$ROOT/bridge:bridge" \
  --hidden-import serial \
  --hidden-import serial.tools.list_ports \
  --hidden-import resolve_bridge \
  --hidden-import menubar \
  --hidden-import inject_keys \
  --hidden-import AppKit \
  --hidden-import Foundation \
  --hidden-import Quartz \
  --hidden-import ApplicationServices \
  --hidden-import objc \
  --osx-bundle-identifier com.andreazero.esp32-davinci-bridge \
  app.py

APP_BUNDLE="$DIST/$NAME.app"
PLIST="$APP_BUNDLE/Contents/Info.plist"

# Agent-style app: keep Dock quieter; primary UI is the menu bar widget.
if [[ -f "$PLIST" ]]; then
  /usr/libexec/PlistBuddy -c "Add :LSUIElement bool true" "$PLIST" 2>/dev/null \
    || /usr/libexec/PlistBuddy -c "Set :LSUIElement true" "$PLIST"
  /usr/libexec/PlistBuddy -c "Add :NSStatusItemPreferredPosition integer 10000" "$PLIST" 2>/dev/null || true
  /usr/libexec/PlistBuddy -c "Add :NSAppleEventsUsageDescription string Shortcut injection for DaVinci Resolve" "$PLIST" 2>/dev/null || true
fi

# Quarantine + ad-hoc sign so Accessibility TCC can attach to a stable binary identity.
xattr -cr "$APP_BUNDLE" 2>/dev/null || true
codesign --force --deep --sign - "$APP_BUNDLE"
echo "Signed (ad-hoc): $APP_BUNDLE"

echo "Built: $APP_BUNDLE"

if [[ "${1:-}" == "--dmg" ]]; then
  if ! command -v create-dmg >/dev/null 2>&1; then
    echo "create-dmg not found. Install with: brew install create-dmg"
    echo "Or drag $APP_BUNDLE into Applications manually."
    exit 0
  fi
  DMG="$DIST/$NAME.dmg"
  rm -f "$DMG"
  create-dmg \
    --volname "$NAME" \
    --window-pos 200 120 \
    --window-size 600 400 \
    --icon-size 100 \
    --app-drop-link 400 200 \
    "$DMG" \
    "$APP_BUNDLE"
  echo "DMG: $DMG"
fi

echo "Done."
echo "Open: open \"$APP_BUNDLE\""
echo "Look for DV / DV● in the menu bar."
echo "Accessibility: remove old entry if rebuild, then enable the new app."
echo "If stuck: tccutil reset Accessibility com.andreazero.esp32-davinci-bridge"
