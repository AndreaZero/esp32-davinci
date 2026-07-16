# ESP32-DaVinci Bridge (macOS app)

Desktop + **menu bar** controller for the USB serial bridge: start/stop, serial port, open at login.

## Run from source

```bash
cd mac-app
pip3 install -r requirements.txt
python3 app.py
```

Look for **DV** (stopped) or **DV●** (running) in the macOS menu bar.

## Menu bar behaviour

| Action | Result |
| --- | --- |
| Window **X** / **Hide to menu bar** | Hides the window; app keeps running |
| Menu bar → **Show ESP32-DaVinci** | Reopens the settings window |
| Menu bar → **Start / Stop bridge** | Control without opening the window |
| Menu bar → **Quit** | Fully exits (only way to quit when menu bar is available) |

Optional setting: **Start hidden in menu bar** — useful with open-at-login.

## Build `.app` / DMG

```bash
cd mac-app
chmod +x build.sh
./build.sh          # → dist/ESP32-DaVinci-Bridge.app
./build.sh --dmg    # also needs: brew install create-dmg
```

Then:

```bash
open dist/ESP32-DaVinci-Bridge.app
```

The packaged app sets `LSUIElement` so it lives primarily in the menu bar (not a persistent Dock app). Move it to **Applications** if you like.

## First launch

1. **System Settings → Privacy & Security → Accessibility** — allow **ESP32-DaVinci-Bridge** (or Terminal/Python if running from source), then quit and reopen the app.
2. Plug in the CrowPanel, pick the serial port (or Auto).
3. **Start bridge** (or use the menu bar).
4. Optional: **Open this app at Mac login**, **Start bridge automatically**, **Start hidden in menu bar**.

### Accessibility looks ON but shortcuts fail

macOS often keeps a **stale** Accessibility entry after `./build.sh` (new binary, same name). The toggle can look enabled while the process is still untrusted.

1. Menu bar → **Quit**
2. Accessibility → remove **ESP32-DaVinci-Bridge**
3. Terminal: `tccutil reset Accessibility com.andreazero.esp32-davinci-bridge`
4. `./build.sh` then `open dist/ESP32-DaVinci-Bridge.app`
5. Click **Allow** if prompted; enable the new entry
6. Prefer copying the app to `/Applications` and enabling that copy

Use the in-app **Fix Accessibility** button to see `Accessibility trusted: True/False` and the exact executable path.

## Notes

- Login item: `~/Library/LaunchAgents/com.andreazero.esp32-davinci-bridge.plist`
- Config: `~/Library/Application Support/ESP32-DaVinci/config.json`
- Prefer building and moving the `.app` to **Applications** before enabling open-at-login.
