# Hardware and Arduino setup

## Target board

Elecrow **CrowPanel** ESP32-S3 HMI **7″**, **800×480** RGB panel, capacitive touch (GT911), USB–UART for flash and serial.

Display/touch stack: LovyanGFX RGB bus + LVGL 8.3.

## Pin / config (`config.h`)

| Item | Value |
| --- | --- |
| Resolution | 800 × 480 |
| Touch I2C | SDA **19**, SCL **20** |
| Backlight | GPIO **2** |
| Firmware version | `FW_VERSION` in `config.h` (currently `0.5.1`) |

RGB panel pinout: see `LovyanGFX_Driver.h`.

USB on this board is **UART only** (not native USB HID). See [architecture.md](./architecture.md).

## Arduino IDE — Tools

| Setting | Value |
| --- | --- |
| Board | ESP32S3 Dev Module |
| USB CDC On Boot | **Disabled** |
| Flash Size | 4MB |
| PSRAM | OPI PSRAM |
| Partition Scheme | Huge APP (3MB No OTA) |
| Upload Speed | **115200** recommended (921600 often fails mid-flash) |

## Libraries

| Library | Version |
| --- | --- |
| LovyanGFX | ≥ **1.2.9** (needed with esp32 core 3.x / RGB) |
| lvgl | **8.3.11** (not 9.x) |

Also copy project `lv_conf.h` to `Arduino/libraries/lv_conf.h`. Required flags include `LV_USE_TABVIEW 1` and Montserrat fonts 14/16/20/22/28.

esp32 board package: prefer a stable **3.2.x** or a **3.3.x** known to build with your LovyanGFX version.

## Flashing tips

1. Quit the Mac bridge (menu bar → **Quit**) and Serial Monitor — they hold the same port.
2. Use Upload Speed **115200**.
3. If upload dies mid-app: **Erase Flash → All Flash Contents**, hold **BOOT** for the whole upload.
4. Incomplete flash leaves a boot loop (`No bootable app partitions`). Re-flash completely before running the bridge.
5. Start the bridge only after the UI is up.

Typical serial device name: `/dev/cu.usbserial-XXXX` (e.g. `usbserial-210`).
