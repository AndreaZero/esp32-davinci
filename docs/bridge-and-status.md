# Bridge and host setup

Python host under `bridge/`. Requires **pyserial**.

## Role

1. Open the CrowPanel serial port (DTR/RTS off to avoid ESP reset).
2. On `CMD:*`, focus Resolve and send the mapped keyboard shortcut.
3. Reply with `ACK:` / `ERR:`.

No Resolve Scripting API / live timecode — shortcuts only.

## Desktop app (recommended)

UI under `mac-app/`: start/stop, serial port, log, open at login, **menu bar widget** (`DV` / `DV●`). Closing the window hides to the menu bar; quit only from the menu bar **Quit** item.

```bash
cd mac-app
pip3 install -r requirements.txt
python3 app.py
```

Build a macOS `.app` (and optional DMG):

```bash
cd mac-app
chmod +x build.sh
./build.sh          # → dist/ESP32-DaVinci-Bridge.app
./build.sh --dmg    # needs: brew install create-dmg
```

1. System Settings → Privacy → **Accessibility** — allow **ESP32-DaVinci-Bridge** (or Python/Terminal if running from source), then **quit and reopen** the app
2. Resolve open (any edition; Free is enough for shortcuts)
3. Keyboard preset: **DaVinci Resolve** default
4. Start the bridge from the app or menu bar; optionally enable **Open this app at Mac login**

Shortcuts are injected with **Quartz** key events (Accessibility only). You should **not** need Automation → System Events. If you still see error `-1743`, Accessibility is missing or the wrong binary is listed — remove old entries, re-enable the current `.app`, restart.

See [mac-app/README.md](../mac-app/README.md).

## CLI setup

```bash
cd bridge
pip3 install -r requirements.txt
python3 resolve_bridge.py -p /dev/cu.usbserial-XXXX
```

| Flag | Effect |
| --- | --- |
| `--no-focus` | Do not activate Resolve before each shortcut |

## See also

- [protocol.md](./protocol.md)
- [actions.md](./actions.md)
- [bridge/README.md](../bridge/README.md)
- [mac-app/README.md](../mac-app/README.md)
