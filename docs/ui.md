# User interface

800×480 LVGL 8 deck. Implementation: `ui_deck.cpp` / `ui_deck.h`.

## Layout

| Zone | Height | Content |
| --- | --- | --- |
| Header | ~56 px | Title, Last CMD, transport badge (STOP / PLAYING / REV), USB status, PING |
| Content | ~360 px | Active tab |
| Tab bar | ~64 px | CUT · PLAY · TOOLS · COL · PAGE |

All actions are always enabled (no SAFE/ARMED lock).

### Transport badge (local UX)

Updated from deck buttons only (not synced from Resolve keyboard):

| Control | Badge / PLAY button |
| --- | --- |
| PLAY | toggles STOP ↔ PLAYING; PLAY button turns green → **PAUSE** |
| L | PLAYING |
| J | REV (amber) |
| K | STOP |

## Tabs

**CUT** — hero CUT; UNDO / REDO / RIPPLE DEL; DEL / SPLIT / SAVE  

**PLAY** — J / K / L; PLAY; FIT / SNAP  

**TOOLS** — SELECT / TRIM / BLADE; IN / OUT / MARK+; INSERT / OVERWRITE / REPLACE; marker prev/next  

**COL** — jump to Color page; serial / parallel / layer node; bypass node / bypass all; reset node  

**PAGE** — Media, Cut, Edit, Fusion, Color, Fairlight, Deliver  

## Feedback

- Pressed button state (lighten)
- CMD → amber “sent” → green ACK (~800 ms) → **USB: ready**
- ERR in red
- Debounce 200 ms

## Palette

| Role | Hex |
| --- | --- |
| Background | `#0D0D0F` |
| Surface | `#1A1A1F` |
| Cut accent | `#C9A227` |
| Danger | `#E85D4C` |
| Transport | `#2A4A6A` |
| OK | `#4CAF50` |
| Muted | `#6B6B70` |
