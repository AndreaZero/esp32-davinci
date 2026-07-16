# Bridge Mac — ESP32-DaVinci

Legge `CMD:<id>` dalla seriale USB del CrowPanel e invia shortcut a DaVinci Resolve.

## Setup (una volta)

```bash
cd esp32-davinci/bridge
pip3 install -r requirements.txt
```

macOS → **Impostazioni di Sistema → Privacy e sicurezza → Accessibilità**: abilita Terminal (o iTerm / Python) così `osascript` può digitare.

## Avvio

1. Flash `esp32-davinci` sul panel (stesse Tools di Sony).
2. **Chiudi** Serial Monitor di Arduino (stessa porta = conflitto).
3. Aspetta che il panel abbia finito il boot (UI visibile).
4. Apri **DaVinci Resolve**, timeline Edit.
5. Avvia il bridge:

```bash
python3 resolve_bridge.py
# oppure
python3 resolve_bridge.py -p /dev/cu.usbserial-210
```

Sul panel: **PING** → `ACK:PING` sullo status. **CUT** → ⌘B in Resolve.

Se vedi `ESP-ROM:` e poi errore porta: il bridge è già aggiornato per evitare il reset DTR; riavvia lo script. Non aprire Resolve “sopra” al flash: ordine = flash → boot UI → bridge.

## Azioni MVP

| ID | Tasto |
| --- | --- |
| CUT | ⌘B |
| PLAY | Space |
| UNDO / REDO | ⌘Z / ⇧⌘Z |
| RIPPLE_DEL | ⇧Delete |
| MARK_IN / MARK_OUT | I / O |
| SAVE | ⌘S |
| PING | solo ACK |

Preset tastiera Resolve: **DaVinci Resolve** default.
