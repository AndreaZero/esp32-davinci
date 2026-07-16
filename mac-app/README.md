# ESP32-DaVinci Bridge (macOS app)

Desktop + **menu bar** controller for the USB serial bridge: start/stop, serial port, open at login, Accessibility helpers.

## Run from source

```bash
cd mac-app
pip3 install -r requirements.txt
python3 app.py
```

Menu bar label: **DV** (bridge stopped) or **DV●** (bridge running).

## Features

| Feature | Description |
| --- | --- |
| Start / Stop | Runs `bridge/resolve_bridge.py` in-process |
| Serial port | Auto or manual; Refresh scans ports |
| Menu bar | Show window, Start/Stop, Quit |
| Hide on close | Window **X** hides to menu bar (does not quit) |
| Open at login | LaunchAgent for this app |
| Auto-start bridge | Start listening when the app opens |
| Start in menu bar | Launch hidden (no window) |
| Fix Accessibility | Shows trust status + opens Privacy settings |

## Menu bar behaviour

| Action | Result |
| --- | --- |
| Window **X** / **Hide to menu bar** | Hides the window; app keeps running |
| Menu bar → **Show ESP32-DaVinci** | Reopens the settings window |
| Menu bar → **Start / Stop bridge** | Control without opening the window |
| Menu bar → **Quit** | Fully exits |

## Build `.app` / DMG

```bash
cd mac-app
chmod +x build.sh
./build.sh          # → dist/ESP32-DaVinci-Bridge.app (ad-hoc codesign)
./build.sh --dmg    # also needs: brew install create-dmg
```

```bash
open dist/ESP32-DaVinci-Bridge.app
```

The packaged app sets `LSUIElement` (menu-bar oriented, not a persistent Dock app). Prefer installing under **Applications** before enabling open-at-login.

## First launch

1. **System Settings → Privacy & Security → Accessibility** — allow **ESP32-DaVinci-Bridge** (or Terminal/Python from source), then quit and reopen.
2. Confirm log: `Accessibility trusted: True`.
3. Plug in the CrowPanel; pick serial port (or Auto).
4. **Start bridge** (or use the menu bar).
5. Optional: open at login / auto-start bridge / start hidden in menu bar.

### Accessibility looks ON but shortcuts fail

macOS often keeps a **stale** Accessibility entry after `./build.sh`.

1. Menu bar → **Quit**
2. Accessibility → remove **ESP32-DaVinci-Bridge**
3. `tccutil reset Accessibility com.andreazero.esp32-davinci-bridge`
4. `./build.sh` then reopen; enable the **new** entry
5. Prefer the copy in `/Applications`

Use **Fix Accessibility** for path + `trusted` status.

## Paths

| Item | Location |
| --- | --- |
| Bundle id | `com.andreazero.esp32-davinci-bridge` |
| Config | `~/Library/Application Support/ESP32-DaVinci/config.json` |
| Login item | `~/Library/LaunchAgents/com.andreazero.esp32-davinci-bridge.plist` |

## See also

- [docs/bridge-and-status.md](../docs/bridge-and-status.md)
- [bridge/README.md](../bridge/README.md)
- [docs/actions.md](../docs/actions.md)
