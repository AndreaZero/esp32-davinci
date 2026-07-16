# Serial protocol

Baud: **115200**. Lines are ASCII, terminated with `\n`.

DTR/RTS are held low by the host so opening the port does not reset the ESP32.

## Device → host

```
CMD:<ACTION_ID>
STAT:READY
```

Example: `CMD:CUT`

Boot / firmware noise lines (ROM, `rst:`, `[OK]`, …) are ignored by the bridge.

## Host → device

```
ACK:<ACTION_ID>
ERR:<ACTION_ID>:<reason>
STAT:BRIDGE_ONLINE
STAT:BRIDGE_OFF
```

| Message | Meaning |
| --- | --- |
| `ACK:` | Shortcut injected successfully |
| `ERR:` | Unknown action, injection failure, or permission error |
| `STAT:BRIDGE_ONLINE` | Bridge session open |
| `STAT:BRIDGE_OFF` | Bridge session closed |

There is no live Resolve INFO / timecode stream on this protocol.

## Action IDs

See [actions.md](./actions.md).
