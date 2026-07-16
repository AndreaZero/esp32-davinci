# ESP32-DaVinci

Touch control deck for **DaVinci Resolve** on macOS. Runs on an **Elecrow CrowPanel ESP32-S3** 7″ (800×480): cut, transport, tools, color nodes, markers, page switching.

The panel talks to a small **Python bridge** over USB serial. The bridge injects keyboard shortcuts into Resolve.

| | |
| --- | --- |
| Firmware | `0.5.1` |
| Hardware | CrowPanel ESP32-S3 HMI 7″, 800×480 |
| Host | macOS + DaVinci Resolve |

## How it works

```
CrowPanel (LVGL UI)
    │  USB-CDC serial @ 115200
    ▼
Mac bridge (resolve_bridge.py) ─► keyboard shortcuts → Resolve
```

The CrowPanel USB port is **UART only** (not USB HID). Native keyboard emulation is not possible on this board; the bridge is required.

## Quick start

### 1. Firmware (Arduino IDE)

1. Open the `esp32-davinci` sketch folder.
2. Board: **ESP32S3 Dev Module** — USB CDC **Disabled**, Flash **4MB**, PSRAM **OPI**, Partition **Huge APP**.
3. Libraries: **LovyanGFX** ≥ 1.2.9, **lvgl** 8.3.11.
4. Copy [`lv_conf.h`](./lv_conf.h) to `~/Documents/Arduino/libraries/lv_conf.h` (next to the `lvgl` folder). Enable `LV_USE_TABVIEW` and Montserrat 14/16/20/22/28 as in that file.
5. Flash with the bridge and Serial Monitor **closed**. Prefer **Upload Speed 115200**; hold **BOOT** during upload if the link drops.

Details: [docs/hardware.md](./docs/hardware.md).

### 2. Bridge (macOS)

**Option A — desktop / menu bar app (recommended)**

```bash
cd mac-app
pip3 install -r requirements.txt
python3 app.py
# or build: chmod +x build.sh && ./build.sh
# then: open dist/ESP32-DaVinci-Bridge.app
```

Start/stop from the window or the menu bar (**DV** / **DV●**). Closing the window keeps the app in the menu bar. Optionally **Open at Mac login**.

**Option B — CLI**

```bash
cd bridge
pip3 install -r requirements.txt
python3 resolve_bridge.py -p /dev/cu.usbserial-XXXX
```

Grant **Accessibility** (System Settings → Privacy) to the app, or to Terminal/Python if using the CLI. Keep Resolve open.

Details: [mac-app/README.md](./mac-app/README.md), [docs/bridge-and-status.md](./docs/bridge-and-status.md).

### 3. Use the deck

- Tabs: **CUT · PLAY · TOOLS · COL · PAGE**
- All buttons send shortcuts immediately (no SAFE/ARMED)

## Documentation

| Doc | Contents |
| --- | --- |
| [docs/architecture.md](./docs/architecture.md) | System design |
| [docs/hardware.md](./docs/hardware.md) | Board, pins, Arduino tools |
| [docs/protocol.md](./docs/protocol.md) | Serial CMD / ACK / INFO |
| [docs/ui.md](./docs/ui.md) | Touch UI layout |
| [docs/actions.md](./docs/actions.md) | Action IDs and Mac shortcuts |
| [docs/bridge-and-status.md](./docs/bridge-and-status.md) | Mac bridge setup |
| [mac-app/README.md](./mac-app/README.md) | Desktop app / DMG build |

## License

See repository license file if present. DaVinci Resolve and Blackmagic Design are trademarks of their respective owners.
