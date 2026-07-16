# Serial protocol

Baud: **115200**. Lines are ASCII, terminated with `\n`.

## Device → host

```
CMD:<ACTION_ID>
STAT:READY
```

Example: `CMD:CUT`

## Host → device

```
ACK:<ACTION_ID>
ERR:<ACTION_ID>:<reason>
STAT:BRIDGE_ONLINE
STAT:BRIDGE_OFF
```

## Action IDs

See [actions.md](./actions.md).
