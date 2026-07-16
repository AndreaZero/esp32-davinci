# 00 — Studio e ricerca (fonti reali)

Data studio: **16 luglio 2026**. Obiettivo: capire come far parlare lo stesso CrowPanel di `esp32-sony` con DaVinci Resolve sul Mac via USB, senza inventare API inesistenti.

## 1. Cosa riusiamo da `esp32-sony` (unico riferimento di progetto)

Dal firmware Sony già in questa workspace:

| Elemento | Dove | Valore |
| --- | --- | --- |
| Board target | header `esp32-sony.ino` | ESP32-S3 Dev Module |
| Display | `config.h` | 800×480 |
| Touch I2C | `config.h` | SDA **19**, SCL **20** |
| Backlight | `config.h` | TFT_BL **2** |
| Stack UI | sketch + `LovyanGFX_Driver.h`, `lvgl_port.*`, `touch.*` | LovyanGFX + LVGL 8.3.11 |
| Arduino notes | commento sketch | USB CDC Disabled, Flash 4MB, PSRAM OPI, Huge APP |

Il progetto DaVinci **non** cambia board: stessa macchina, stesso stack display/touch. Cambia solo il “backend” (da Sony BLE a comandi Resolve).

## 2. Vincolo USB CrowPanel (critico)

Sul chip ESP32-S3, USB OTG nativo usa tipicamente **GPIO19 (D−) e GPIO20 (D+)**.

Su questo panel, in `esp32-sony` quei pin sono già **touch I2C**. Il connettore USB-C del CrowPanel, nelle schede Elecrow della stessa famiglia, è documentato come **USB-UART / serial**, non come device HID.

Fonte Elecrow (forum ufficiale, aggiornato ottobre 2024):

- Thread: [ESP32S3 Display — USB HID Support](https://forum.elecrow.com/discussion/502/esp32s3-5-inch-display-usb-hid-support)
- Risposta Elecrow: la porta USB è per connessione seriale; **non supporta HID**; D+/D− usati come seriali → “current version does not support USB HID”.

Conseguenza: **non possiamo emulare una tastiera USB nativa** su questo hardware così com’è.

## 3. Cosa può fare ESP32-S3 come HID (in generale)

Su board con USB OTG cablato correttamente, Arduino-ESP32 espone `USB.h` + `USBHIDKeyboard.h` (TinyUSB), con Tools → USB Mode = **USB-OTG (TinyUSB)**.

Fonti:

- Espressif Arduino: [`USBHIDKeyboard.h`](https://github.com/espressif/arduino-esp32/blob/master/libraries/USB/src/USBHIDKeyboard.h)
- ESP-IDF USB Device (TinyUSB): [docs ESP32-S3 USB Device](https://docs.espressif.com/projects/esp-idf/en/v5.4.4/esp32s3/api-reference/peripherals/usb_device.html)
- Esempio pratico 2025: [Virtual USB keyboard with ESP32-S3](https://philippkueng.ch/2025-06-16-creating-a-virtual-usb-keyboard-with-the-esp32-s3.html)

Utile come knowledge base, **non** come path diretto sul CrowPanel attuale.

## 4. Controllare Resolve: due strade reali

### A) Shortcut tastiera (funziona Free + Studio)

Resolve espone le azioni di editing come hotkey. Su Mac, taglio al playhead = **⌘B** (Razor / cut at playhead). Blade tool = **B**. Customizzazione in-app: **⌘⌥K**.

Fonti shortcut (Mac, layout default Resolve):

- Cheat sheet aggiornato 2026 (Resolve 18–20): [Pixflow — Resolve Keyboard Shortcuts](https://pixflow.net/blog/davinci-resolve-keyboard-shortcuts/)
- Riferimento storico ufficiale BMD (PDF Resolve 11, ancora allineato su Razor = Command B): [DaVinci Resolve 11 Mac Keyboard Shortcuts (Blackmagic)](https://documents.blackmagicdesign.com/SupportNotes/DaVinciResolve11Shortcuts/20140625-25b52d/DaVinci_Resolve_11_Mac_Keyboard_Shortcuts.pdf)
- Fonte di verità operativa: pannello **Keyboard Customization** nella tua installazione Resolve

Nota: i shortcut dipendono dal preset (Resolve / Cut / Premiere…). Il piano assume **preset DaVinci Resolve default su Mac**, configurabile.

### B) Scripting API Python/Lua (Studio per script esterni)

Blackmagic fornisce Scripting API (moduli in `…/DaVinci Resolve/Developer/Scripting`). Documentazione ufficiale in-app + mirror community:

- Mirror API: [deric/DaVinciResolve-API-Docs](https://deric.github.io/DaVinciResolve-API-Docs/)
- Gist API v21: [X-Raym Resolve Scripting API Doc](https://gist.github.com/X-Raym/2f2bf453fc481b9cca624d7ca0e19de8)

Limiti rilevanti per il nostro caso:

- Script **esterni** (da fuori Resolve) tipicamente richiedono **Studio** + permesso scripting in Preferences.
- L’API è forte su project/timeline/media/render/markers/playhead; **non espone un comando “blade/razor al playhead”** come metodo dedicato. Per il taglio clip da editor UI, il percorso pratico resta **shortcut tastiera**.

Quindi: per Cmd+B e azioni edit “da montatore”, il piano punta a **iniezione tastiera sul Mac**, non a un fantomatico `Timeline.Razor()`.

## 5. Come collegare CrowPanel ↔ Mac via USB (path realistico)

Dato il vincolo §2, USB sul panel = **CDC/UART seriale** (già usato per flash/monitor in Arduino).

Flusso proposto:

```
CrowPanel UI (LVGL)
    → invia riga comando su Serial USB
        → agent leggero sul Mac legge la porta
            → attiva Resolve + invia shortcut (⌘B, Space, …)
```

Alternative (non USB o non “same board only”):

| Alternative | Pro | Contro |
| --- | --- | --- |
| BLE HID keyboard (ESP32-S3) | Nessun agent Mac | Non è USB; pairing BT; librerie BLE HID su S3 da scegliere con cura |
| Secondo MCU USB-OTG | HID vero | Hardware extra, fuori scope “same device” |
| Solo Scripting API | Azioni “strutturate” | Studio; niente razor nativo |

**Scelta piano:** Serial USB + agent Mac (minimo) per shortcut. Opzionale fase 2: BLE HID se vuoi zero software sul Mac.

## 6. Sintesi decisioni da ricerca

1. Board/config/UI = copia pattern da `esp32-sony`.
2. USB HID nativo sul CrowPanel = **no**.
3. Taglio clip e editing quotidiano = **shortcut Mac**, non API razor.
4. USB usato come **serial command channel** verso un bridge Mac.
5. Fonti ufficiali/community citate sopra; truth finale shortcut = Keyboard Customization della tua Resolve.
