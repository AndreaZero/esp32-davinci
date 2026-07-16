# 01 — Architettura

## Obiettivo

Pannello touch sul CrowPanel ESP32-S3 (stesso di `esp32-sony`) che, collegato al Mac via USB, esegue azioni Resolve (es. taglio ⌘B).

## Architettura target (MVP)

```
┌─────────────────────────────┐         USB-C          ┌──────────────────────────┐
│  CrowPanel ESP32-S3         │  CDC Serial 115200     │  Mac                     │
│  LVGL UI (da pattern Sony)  │ ─────────────────────► │  bridge (Python o Swift) │
│  actions → Serial.println   │                        │  → focus Resolve         │
│                             │ ◄─── ACK / status ──── │  → CGEvent / osascript   │
└─────────────────────────────┘                        │  → keystroke ⌘B …        │
                                                       └──────────────────────────┘
```

### Perché così

- Il CrowPanel **non** fa USB HID (vedi `00-studio-ricerca.md`).
- USB resta il cavo che già usi (come richiesto).
- I comandi di editing Resolve sono shortcut; il Mac è il posto giusto per generarli.
- Lo sketch Arduino resta semplice: UI + mappa bottone → ID azione.

### Cosa non fa il firmware

- Non parla direttamente all’API Scripting di Resolve.
- Non emula tastiera USB sul bus OTG (impossibile su questa board).

## Componenti

### 1. Firmware Arduino (`esp32-davinci`)

Riuso da Sony (stessi file/pattern, adattati):

- `config.h`, `LovyanGFX_Driver.h`, `touch.*`, `lvgl_port.*`, `lv_conf.h`
- Sketch principale con UI bottoni (niente `sony_ble` / NVS camera)

Nuovo:

- `actions.h` — ID azioni (`CUT`, `PLAY`, `UNDO`, …)
- `serial_proto.*` — protocollo riga testo verso Mac + ACK
- UI “deck” Resolve invece di Scan/Shutter/Rec

### 2. Bridge Mac (companion minimo)

Processo locale che:

1. Apre la porta seriale del CrowPanel
2. Legge comandi (`CUT\n`, …)
3. Porta Resolve in foreground
4. Invia la combo tastiera corrispondente
5. Opzionale: risponde `OK CUT` / `ERR …`

Implementazione suggerita MVP: **Python 3** + `pyserial` + eventi tastiera macOS (`Quartz` / `pyobjc`, oppure `osascript` System Events). Nessuna dipendenza da altri progetti.

Permessi macOS: Accessibility (e spesso Input Monitoring) per sintetizzare tasti.

### 3. Resolve

- App in primo piano (o almeno focused) quando arriva il comando
- Preset tastiera **DaVinci Resolve** default (documentare se usi altro preset)
- Free o Studio: indifferente per path shortcut

## Protocollo seriale (bozza)

Baud: **115200** (allineato a `Serial.begin` Sony).

Formato: una riga ASCII, terminata `\n`.

```
# device → host
CMD:<id>\n

# host → device (opzionale MVP+)
ACK:<id>\n
ERR:<id>:<reason>\n
STAT:READY\n
```

Esempi `id`: `CUT`, `PLAY`, `UNDO`, `REDO`, `RIPPLE_DEL`, `MARK_IN`, `MARK_OUT`, `SAVE`.

Regole:

- Un comando alla volta; debounce UI 150–250 ms
- ID stabili (non cambiare stringhe dopo MVP)
- Nessun payload binario in MVP

## Mappa azioni → tasti (Mac, preset default)

Vedi `03-azioni-shortcut.md`. Il bridge possiede la tabella; il firmware invia solo l’ID.

## Alternative (fuori MVP, documentate)

1. **BLE HID** dal CrowPanel → Mac vede una tastiera Bluetooth; niente bridge. Trade-off: non è USB; pairing; stack BLE da validare su S3.
2. **Scripting API** per azioni non-UI (markers, timecode, render). Richiede Studio + agent che chiama `DaVinciResolveScript`. Non sostituisce ⌘B.

## Sicurezza / UX

- Bridge attivo solo a Resolve aperto (altrimenti tasti finiscono altrove)
- Opzione “hold to enable” o LED/status “ARMED” sul panel
- Non loggare payload sensibili (non ce ne sono in MVP)
