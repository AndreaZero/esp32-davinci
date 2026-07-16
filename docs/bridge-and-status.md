# Bridge and host setup

Host code lives under `bridge/` (core) and `mac-app/` (desktop controller).

## Role

1. Open the CrowPanel serial port (DTR/RTS off to avoid ESP reset).
2. On `CMD:*`, bring Resolve forward and inject the mapped keyboard shortcut.
3. Reply with `ACK:` / `ERR:`.
4. Send `STAT:BRIDGE_ONLINE` / `STAT:BRIDGE_OFF` when the session starts/stops.

No Resolve Scripting API and no live timecode — shortcuts only.

## Shortcut injection

| Path | Module | Permission |
| --- | --- | --- |
| **Primary** | Quartz `CGEvent` via `inject_keys.py` | **Accessibility** |
| Fallback | AppleScript → System Events | Accessibility + **Automation** (System Events) |

Key map: `bridge/inject_keys.py` (`CHORDS`).  
Focus Resolve with `open -a "DaVinci Resolve"` (not Apple Events to Resolve).

At startup the host logs `Accessibility trusted: True/False`. Shortcuts should report `ACK:… (quartz)` when working.

## Desktop app (recommended)

UI under `mac-app/`: start/stop, serial port, log, open at login, **menu bar** (`DV` / `DV●`).

```bash
cd mac-app
pip3 install -r requirements.txt
python3 app.py
```

Build a macOS `.app` (and optional DMG):

```bash
cd mac-app
chmod +x build.sh
./build.sh          # → dist/ESP32-DaVinci-Bridge.app (ad-hoc signed)
./build.sh --dmg    # needs: brew install create-dmg
```

### First-run checklist

1. System Settings → Privacy & Security → **Accessibility** — allow **ESP32-DaVinci-Bridge** (or Python/Terminal if from source), then **quit and reopen** the app
2. Resolve open; keyboard preset **DaVinci Resolve** (default)
3. Start the bridge; confirm log shows `Accessibility trusted: True`
4. Optional: **Open at Mac login**, **Start bridge automatically**, **Start hidden in menu bar**

### Stale Accessibility (toggle ON but `trusted: False`)

Common after rebuild (new binary, same name):

1. Menu bar → **Quit**
2. Accessibility → remove **ESP32-DaVinci-Bridge**
3. `tccutil reset Accessibility com.andreazero.esp32-davinci-bridge`
4. Rebuild / reopen; enable the **new** entry (prefer `/Applications`)

In-app **Fix Accessibility** shows process path and trust status.

Bundle id: `com.andreazero.esp32-davinci-bridge`  
Config: `~/Library/Application Support/ESP32-DaVinci/config.json`  
Login item: `~/Library/LaunchAgents/com.andreazero.esp32-davinci-bridge.plist`

Full UI notes: [mac-app/README.md](../mac-app/README.md).

## CLI setup

```bash
cd bridge
pip3 install -r requirements.txt
python3 resolve_bridge.py -p /dev/cu.usbserial-XXXX
```

Grant Accessibility to **Terminal** or **Python**, not the `.app`.

| Flag | Effect |
| --- | --- |
| `-p` / `--port` | Serial port (default: auto-detect) |
| `-b` / `--baud` | Baud rate (default `115200`) |
| `--no-focus` | Do not activate Resolve before each shortcut |

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `ERR:… (-1743)` / System Events | Old AppleScript path; use current Quartz build + Accessibility |
| `Accessibility trusted: False` | Reset TCC (above); re-enable correct binary |
| Port busy / no connect | Quit bridge, Serial Monitor, other serial tools |
| ACK but Resolve ignores key | Wrong keyboard preset; Resolve not frontmost; Fn for F-keys |
| Panel USB shows offline | Bridge not running or wrong port |

## See also

- [protocol.md](./protocol.md)
- [actions.md](./actions.md)
- [architecture.md](./architecture.md)
- [bridge/README.md](../bridge/README.md)
- [mac-app/README.md](../mac-app/README.md)
