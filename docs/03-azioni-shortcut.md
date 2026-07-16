# 03 — Catalogo azioni e shortcut (Mac)

Preset assunto: **DaVinci Resolve** (default), macOS.  
Verifica sempre in Resolve → **Keyboard Customization** (⌘⌥K).

Fonte primaria shortcut: pannello Resolve + PDF storico BMD (Razor = Command B) + cheat sheet community 2026.

## MVP — priorità alta

| ID firmware | Label UI | Shortcut Mac | Note |
| --- | --- | --- | --- |
| `CUT` | Cut / Razor | ⌘B | Taglia al playhead (tutte le track auto-select) |
| `PLAY` | Play/Pause | Space | |
| `UNDO` | Undo | ⌘Z | |
| `REDO` | Redo | ⇧⌘Z | |
| `RIPPLE_DEL` | Ripple Delete | ⇧Delete | |
| `MARK_IN` | Mark In | I | |
| `MARK_OUT` | Mark Out | O | |
| `SAVE` | Save | ⌘S | |

## MVP+ — editing quotidiano

| ID | Label | Shortcut | Note |
| --- | --- | --- | --- |
| `BLADE_TOOL` | Blade tool | B | Seleziona tool; non taglia da solo |
| `SELECT_TOOL` | Selection | A | |
| `TRIM_TOOL` | Trim | T | |
| `SNAP` | Snap | N | toggle |
| `DEL` | Delete | Delete | lift, non ripple |
| `SPLIT` | Split clip | ⌘\ | Split al playhead (comando distinto da Razor in alcuni layout) |
| `FIT` | Fit timeline | ⇧Z | |
| `JK_BACK` | J | J | |
| `JK_STOP` | K | K | |
| `JK_FWD` | L | L | |

## Edit insert (opzionale)

| ID | Label | Shortcut |
| --- | --- | --- |
| `INSERT` | Insert | F9 |
| `OVERWRITE` | Overwrite | F10 |
| `REPLACE` | Replace | F11 |

## Navigazione pagine (opzionale)

| ID | Label | Shortcut |
| --- | --- | --- |
| `PAGE_MEDIA` | Media | ⇧1 |
| `PAGE_CUT` | Cut | ⇧2 |
| `PAGE_EDIT` | Edit | ⇧3 |
| `PAGE_FUSION` | Fusion | ⇧4 |
| `PAGE_COLOR` | Color | ⇧5 |
| `PAGE_FAIRLIGHT` | Fairlight | ⇧6 |
| `PAGE_DELIVER` | Deliver | ⇧7 |

(Confermare numerazione sul tuo Resolve: può variare leggermente tra versioni/preset.)

## Layout UI suggerito (800×480)

Riga status in alto (USB / last CMD / ARMED).

Griglia primaria (grandi):

```
[ CUT ]     [ PLAY ]
[ UNDO ]    [ RIPPLE_DEL ]
[ I ] [ O ] [ SAVE ]
```

Seconda pagina o riga secondaria: J/K/L, Fit, Snap.

## Note implementative bridge

- Prima di ogni shortcut: `tell application "DaVinci Resolve" to activate` (o equivalente)
- Delay breve (~50–150 ms) dopo focus
- Modifier Mac: **Command**, non Control
- Non tenere tasti premuti: press+release puliti
- Debounce lato firmware; bridge può ignorare comandi duplicati <100 ms

## Cosa non mettere in MVP

- Azioni Color (⌥S add node, ecc.) — rischio conflitto se non sei in Color page
- Macro complesse multi-step
- Dipendenza da Scripting API per il cut
