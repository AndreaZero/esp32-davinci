# 04 — Hardware e board (da `esp32-sony`)

Unica fonte di verità per la macchina: il progetto **esp32-sony** in questa workspace.

## Target

- Device: CrowPanel-class **ESP32-S3** HMI 7" 800×480 (come Sony)
- Sketch notes (da header `esp32-sony.ino`):
  - Board: **ESP32S3 Dev Module**
  - USB CDC: **Disabled** (come Sony)
  - Flash: **4MB**
  - PSRAM: **OPI**
  - Partition: **Huge APP**

## Pin / display (da `config.h` + `LovyanGFX_Driver.h`)

| Funzione | Valore |
| --- | --- |
| `SCREEN_WIDTH` / `HEIGHT` | 800 / 480 |
| `TOUCH_SDA` / `TOUCH_SCL` | GPIO **19** / **20** |
| `TFT_BL` | GPIO **2** |
| RGB panel | pin bus come in `LovyanGFX_Driver.h` Sony (GPIO 0,1,3–9,14–16,21,39–41,45–48, …) |

Implicazione USB: GPIO 19/20 occupati dal touch → **niente USB OTG HID** sullo stesso chip wiring (vedi studio).

## Librerie (come Sony)

- LovyanGFX ≥ 1.1.16
- lvgl **8.3.11**
- `lv_conf.h` nello sketch (e copia in libraries se già usata per Sony)

## Cosa non portare da Sony

- `sony_ble.*`, `sony_protocol.h`
- `nvs_store.*` (pairing camera) — a meno di NVS per preferenze UI deck in futuro
- Bottoni Scan / Connect / Shutter / Rec

## Cosa portare e adattare

- Init LCD + backlight (`backlight_on` pattern)
- `touch_init` + `lvgl_port_init` / `lvgl_port_loop`
- Stile UI scuro / bottoni grandi (editing touch)
- `Serial.begin(115200)` come canale comandi verso Mac

## Collaudo hardware minimo

1. Flash con le stesse Tools di Sony
2. Touch risponde
3. Serial Monitor vede output
4. Solo dopo: collegare bridge e Resolve
