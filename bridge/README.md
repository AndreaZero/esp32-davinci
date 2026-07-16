# Mac bridge

See the full guide: [docs/bridge-and-status.md](../docs/bridge-and-status.md).

```bash
pip3 install -r requirements.txt
python3 resolve_bridge.py -p /dev/cu.usbserial-XXXX
```

Requires Resolve **Studio** + External scripting **Local** for live `INFO` lines. Use `--no-info` for shortcut-only mode.
