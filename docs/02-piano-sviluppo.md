# 02 — Piano di sviluppo

## Scope MVP

- Stesso hardware e config di `esp32-sony`
- UI touch con bottoni azioni Resolve
- USB serial → bridge Mac → shortcut
- Azioni prioritarie: **CUT (⌘B)**, play/pause, undo, ripple delete, mark in/out, save

Fuori MVP: BLE HID, Scripting API Studio, multi-page Color/Fusion deck, Wi‑Fi.

## Fasi

### Fase 0 — Setup progetto (docs già fatte)

- [x] Studio fonti + vincoli hardware
- [x] Architettura serial + bridge
- [x] Conferma utente → sviluppo avviato

### Fase 1 — Scheletro firmware

- [x] File board da `esp32-sony` copiati
- [x] Sketch `esp32-davinci.ino` (no BLE Sony)
- [x] UI + PING / azioni MVP

**Da fare tu:** flash con Tools come Sony; tap PING → Serial `CMD:PING`.

### Fase 2 — Protocollo + mappa azioni

- [x] `serial_proto` `CMD:<id>\n` + ACK/ERR in ingresso
- [x] Griglia bottoni MVP
- [x] Debounce 200 ms + label Last / status

### Fase 3 — Bridge Mac

- [x] `bridge/resolve_bridge.py` + `requirements.txt` + README
- [x] Auto-detect porta, focus Resolve, shortcut Mac
- [ ] Verifica end-to-end sul tuo Mac (CUT in timeline)

### Fase 4 — Hardening

1. ACK opzionale host→device + status sul display
2. Modalità ARMED / SAFE
3. Lista azioni v1.1 (JKL, insert/overwrite F9–F11, page switch Shift+…) se servono
4. Documentare preset tastiera Resolve richiesto

**Done quando:** sessione editing reale 15–30 min senza tasti “persi” o doppi tagli.

## Struttura cartelle proposta

```
esp32-davinci/
  docs/                 ← siamo qui
  esp32-davinci.ino
  config.h              ← da Sony
  LovyanGFX_Driver.h
  touch.h / touch.cpp
  lvgl_port.h / .cpp
  lv_conf.h
  actions.h
  serial_proto.h / .cpp
  bridge/
    README.md
    resolve_bridge.py
    requirements.txt
```

## Ordine di lavoro consigliato

Firmware UI/serial **prima**, bridge **subito dopo** il primo `CMD:` stabile. Non espandere la UI Color/Fusion finché CUT non è affidabile.

## Criteri di accettazione MVP

| # | Criterio |
| --- | --- |
| 1 | Stesso board settings di Sony, build senza errori |
| 2 | UI leggibile a 800×480, bottoni grandi (editing touch) |
| 3 | USB collegato → bridge riceve comandi |
| 4 | CUT = ⌘B funzionante su Edit page |
| 5 | Almeno 5 azioni MVP utili oltre CUT |
| 6 | Docs aggiornate se si cambia protocollo o shortcut |

## Rischi

| Rischio | Mitigazione |
| --- | --- |
| Shortcut diversi (preset Premiere) | Tabella configurabile nel bridge; doc preset |
| Tasti inviati ad app sbagliata | Focus Resolve + modalità ARMED |
| Permessi macOS | Checklist bridge README |
| CDC vs USB Mode Arduino | Allinearsi a Sony (CDC Disabled per flash); serial resta UART bridge della board |

## Dopo conferma

Passo successivo: Fase 1 (scheletro sketch + copia file da Sony) + stub bridge.
