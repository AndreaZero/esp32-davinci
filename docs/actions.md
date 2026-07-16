# Actions and shortcuts

Preset assumed: **DaVinci Resolve** (default), **macOS**.  
Verify in Resolve → **Keyboard Customization** (⌘⌥K).

## Cut

| ID | UI | Mac shortcut |
| --- | --- | --- |
| `CUT` | CUT | ⌘B |
| `UNDO` | UNDO | ⌘Z |
| `REDO` | REDO | ⇧⌘Z |
| `RIPPLE_DEL` | RIPPLE DEL | ⇧Delete |
| `DEL` | DEL | Forward Delete |
| `SPLIT` | SPLIT | ⌘\ |
| `SAVE` | SAVE | ⌘S |

## Transport

| ID | UI | Mac shortcut |
| --- | --- | --- |
| `PLAY` | PLAY / PAUSE | Space |
| `JK_BACK` | J | J |
| `JK_STOP` | K | K |
| `JK_FWD` | L | L |
| `FIT` | FIT | ⇧Z |
| `SNAP` | SNAP | N |

## Tools

| ID | UI | Mac shortcut |
| --- | --- | --- |
| `SELECT_TOOL` | SELECT A | A |
| `TRIM_TOOL` | TRIM T | T |
| `BLADE_TOOL` | BLADE B | B |
| `MARK_IN` | IN | I |
| `MARK_OUT` | OUT | O |
| `INSERT` | INSERT | F9 |
| `OVERWRITE` | OVERWRITE | F10 |
| `REPLACE` | REPLACE | F11 |

## Color (use on Color page)

| ID | UI | Mac shortcut |
| --- | --- | --- |
| `COLOR_ADD_SERIAL` | SERIAL + | ⌥S |
| `COLOR_ADD_PARALLEL` | PARALLEL + | ⌥P |
| `COLOR_ADD_LAYER` | LAYER + | ⌥L |
| `COLOR_BYPASS_NODE` | BYPASS NODE | ⌘D |
| `COLOR_BYPASS_ALL` | BYPASS ALL | ⇧D |
| `COLOR_RESET_NODE` | RESET NODE | ⌘Home |

## Markers

| ID | UI | Mac shortcut |
| --- | --- | --- |
| `MARKER_ADD` | MARK + | M |
| `MARKER_NEXT` | M NEXT | ⇧↓ |
| `MARKER_PREV` | M PREV | ⇧↑ |

## Pages

| ID | UI | Mac shortcut |
| --- | --- | --- |
| `PAGE_MEDIA` | MEDIA | ⇧2 |
| `PAGE_CUT` | CUT | ⇧3 |
| `PAGE_EDIT` | EDIT | ⇧4 |
| `PAGE_FUSION` | FUSION | ⇧5 |
| `PAGE_COLOR` | COLOR | ⇧6 |
| `PAGE_FAIRLIGHT` | FAIRLIGHT | ⇧7 |
| `PAGE_DELIVER` | DELIVER | ⇧8 |

⇧1 = Project Manager, ⇧9 = Project Settings (not on the deck).

## Meta

| ID | Notes |
| --- | --- |
| `PING` | ACK only (bridge connectivity test) |

Mappings live in `bridge/resolve_bridge.py` (`SHORTCUTS`). Page keys use AppleScript **key codes** with Shift (not `keystroke "1" using shift`, which types `!` on macOS).
