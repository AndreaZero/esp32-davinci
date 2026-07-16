# Mac bridge (CLI)

Serial host that turns panel `CMD:*` lines into DaVinci Resolve shortcuts on macOS.

## Install

```bash
cd bridge
pip3 install -r requirements.txt
```

Dependencies: **pyserial**, **PyObjC** (Quartz + ApplicationServices) for key injection.

## Run

```bash
python3 resolve_bridge.py -p /dev/cu.usbserial-XXXX
```

| Flag | Effect |
| --- | --- |
| `-p` / `--port` | Serial port (default: auto) |
| `-b` / `--baud` | Baud (default `115200`) |
| `--no-focus` | Do not bring Resolve to the front |

Grant **Accessibility** to Terminal or Python (System Settings → Privacy & Security → Accessibility).

## Modules

| File | Role |
| --- | --- |
| `resolve_bridge.py` | Serial loop, ACK/ERR, CLI entry |
| `inject_keys.py` | Quartz key chords (`CHORDS`) |

For day-to-day use, prefer the menu bar app: [mac-app/README.md](../mac-app/README.md).

Full host notes: [docs/bridge-and-status.md](../docs/bridge-and-status.md).  
Action list: [docs/actions.md](../docs/actions.md).
