# Bridge Mac — ESP32-DaVinci

Legge `CMD:<id>` dalla seriale USB del CrowPanel e invia shortcut a DaVinci Resolve.

## Setup (una volta)

```bash
cd esp32-davinci/bridge
pip3 install -r requirements.txt
```

macOS → **Impostazioni di Sistema → Privacy e sicurezza → Accessibilità**: abilita Terminal (o iTerm / Python).

## Avvio

1. Flash `esp32-davinci` (Tools come Sony).
2. Chiudi Serial Monitor Arduino.
3. Panel con UI visibile → apri Resolve → avvia bridge:

```bash
python3 resolve_bridge.py -p /dev/cu.usbserial-210
```

4. **PING** → `ACK:PING`. Per **CUT / RIPPLE / DEL**: sul panel passa a **ARMED**.

## Azioni (v0.2)

| ID | Shortcut Mac |
| --- | --- |
| CUT | ⌘B |
| UNDO / REDO | ⌘Z / ⇧⌘Z |
| RIPPLE_DEL | ⇧Delete |
| DEL | Delete (forward) |
| SPLIT | ⌘\ |
| SAVE | ⌘S |
| PLAY | Space |
| JK_BACK / STOP / FWD | J / K / L |
| FIT / SNAP | ⇧Z / N |
| SELECT_TOOL / TRIM_TOOL / BLADE_TOOL | A / T / B |
| MARK_IN / MARK_OUT | I / O |
| INSERT / OVERWRITE / REPLACE | F9 / F10 / F11 |
| PAGE_MEDIA … PAGE_DELIVER | ⇧2 … ⇧8 |
| PING | solo ACK |

Preset tastiera Resolve: **DaVinci Resolve** default.

### F-keys (Insert / Overwrite / Replace)

AppleScript usa key code: F9=`101`, F10=`109`, F11=`103`.  
Su alcuni MacBook serve **Fn+F9** a livello hardware, oppure disattiva “Use F1, F2, etc. keys as standard function keys” invertito — se non va, mappa Insert/Overwrite/Replace in Resolve su altri tasti e aggiorna `SHORTCUTS` in `resolve_bridge.py`.

### Pagine Resolve

⇧1–⇧7 dipendono dal preset. Controlla in Keyboard Customization se i numeri non cambiano pagina.
