# ESP32-DaVinci — Documentazione

Studio e piano per un pannello touch (stesso CrowPanel ESP32-S3 di `esp32-sony`) che controlla **DaVinci Resolve su Mac via USB**.

**Riferimento hardware / Arduino / UI:** solo il progetto sibling `esp32-sony` (config board, LovyanGFX, LVGL, touch).

| Doc | Contenuto |
| --- | --- |
| [00-studio-ricerca.md](./00-studio-ricerca.md) | Fonti verificate (2025–2026), vincoli hardware, API vs HID |
| [01-architettura.md](./01-architettura.md) | Architettura scelta, alternative, protocollo |
| [02-piano-sviluppo.md](./02-piano-sviluppo.md) | Fasi, milestone, struttura sketch, criteri di done |
| [03-azioni-shortcut.md](./03-azioni-shortcut.md) | Catalogo azioni MVP (Cmd+B e altre) |
| [04-hardware-board.md](./04-hardware-board.md) | Board, pin, Arduino settings (da `esp32-sony`) |

**Stato:** MVP implementato (firmware + bridge Mac). Vedi `../esp32-davinci.ino` e `../bridge/`.
