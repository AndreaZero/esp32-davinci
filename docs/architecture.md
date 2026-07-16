# Architecture

## Goal

A finger-friendly Resolve deck on CrowPanel ESP32-S3: editing and color shortcuts from the touchscreen, driven by a Mac host bridge.

## Components

| Piece | Role |
| --- | --- |
| Firmware (`esp32-davinci.ino`, `ui_deck.*`, `serial_proto.*`, …) | LVGL UI, debounce, serial I/O |
| Bridge core (`bridge/resolve_bridge.py`, `bridge/inject_keys.py`) | Serial host + Quartz key injection into Resolve |
| Mac app (`mac-app/app.py`, `mac-app/menubar.py`) | Start/stop UI, menu bar widget, open at login |

## Data flow

```
UI button
  → CMD:<id>\n          (panel → Mac, USB serial @ 115200)
  → focus Resolve       (open -a)
  → Quartz key event    (Accessibility)
  → ACK:<id>\n          (Mac → panel)
```

AppleScript → System Events is only a fallback. The primary path does **not** require Automation permission.

## Why a Mac bridge?

On CrowPanel-class boards the USB-C connector is wired as **USB–UART**, not ESP32-S3 native USB OTG. GPIO 19/20 are used for touch I2C (the pins normally used for USB D+/D−). Therefore the device cannot enumerate as a USB HID keyboard. Serial + host-side key injection is the supported path.

Works with Resolve Free or Studio (shortcuts only).

## Host UX

- **Recommended:** `mac-app` menu bar app (`DV` / `DV●`). Window close hides to the menu bar; Quit from the menu.
- **CLI:** `python3 bridge/resolve_bridge.py` for debugging.

## Limitations (by design)

- No live video preview on the panel
- No live timecode / clip / page sync from Resolve (shortcut-only for reliability)
- Shortcuts depend on Resolve’s keyboard preset (default **DaVinci Resolve** on Mac)
- F9–F11 may need Fn or OS “Use F1, F2, etc. keys as standard function keys”
- macOS **Accessibility** must trust the running process (see [bridge-and-status.md](./bridge-and-status.md))
