# Architecture

## Goal

A finger-friendly Resolve deck on CrowPanel ESP32-S3: editing shortcuts from the touchscreen, plus live timeline status on the header.

## Components

| Piece | Role |
| --- | --- |
| Firmware (`esp32-davinci.ino`, `ui_deck.*`, `serial_proto.*`) | LVGL UI, debounce, serial I/O |
| Bridge (`bridge/resolve_bridge.py`) | Serial host + AppleScript keystrokes into Resolve |

## Data flow

```
UI button → CMD:<id>\n → bridge → focus Resolve → keystroke → ACK
```

## Why a Mac bridge?

On CrowPanel-class boards the USB-C connector is wired as **USB–UART**, not ESP32-S3 native USB OTG. GPIO 19/20 are used for touch I2C (the pins normally used for USB D+/D−). Therefore the device cannot enumerate as a USB HID keyboard. Serial + host-side key injection is the supported path.

Works with Resolve Free or Studio (shortcuts only).

## Limitations (by design)

- No live video preview on the panel
- No live timecode/clip status (kept shortcut-only for reliability)
- Shortcuts depend on Resolve’s keyboard preset (default **DaVinci Resolve** on Mac)
- F9–F11 may need Fn or OS “use F1, F2 as standard function keys”
