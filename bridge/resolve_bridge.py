#!/usr/bin/env python3
"""ESP32-DaVinci Mac bridge: USB serial CMD:* → DaVinci Resolve keyboard shortcuts."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from typing import Callable

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    print("Missing pyserial. Install with:  pip3 install pyserial", file=sys.stderr)
    sys.exit(1)

# Action ID → AppleScript fragment inside System Events (after Resolve is focused)
# Preset: DaVinci Resolve default (Mac)
# F-keys: macOS key codes — F9=101, F10=109, F11=103 (may need Fn on some keyboards)
SHORTCUTS: dict[str, str] = {
    # Cut
    "CUT": 'keystroke "b" using command down',
    "UNDO": 'keystroke "z" using command down',
    "REDO": 'keystroke "z" using {command down, shift down}',
    "RIPPLE_DEL": "key code 117 using shift down",  # Shift+Fwd Delete
    "DEL": "key code 117",  # Forward Delete
    "SPLIT": "key code 42 using command down",  # Cmd+\
    "SAVE": 'keystroke "s" using command down',
    # Transport
    "PLAY": "keystroke space",
    "JK_BACK": 'keystroke "j"',
    "JK_STOP": 'keystroke "k"',
    "JK_FWD": 'keystroke "l"',
    "FIT": 'keystroke "z" using shift down',
    "SNAP": 'keystroke "n"',
    # Tools
    "SELECT_TOOL": 'keystroke "a"',
    "TRIM_TOOL": 'keystroke "t"',
    "BLADE_TOOL": 'keystroke "b"',
    "MARK_IN": 'keystroke "i"',
    "MARK_OUT": 'keystroke "o"',
    "INSERT": "key code 101",  # F9
    "OVERWRITE": "key code 109",  # F10
    "REPLACE": "key code 103",  # F11
    # Pages — must use key code (keystroke "1" using shift = types "!" on Mac)
    # Default Resolve preset: Shift+2…Shift+8 (Media…Deliver). Verify in ⌘⌥K.
    "PAGE_MEDIA": "key code 19 using shift down",      # Shift+2
    "PAGE_CUT": "key code 20 using shift down",        # Shift+3
    "PAGE_EDIT": "key code 21 using shift down",       # Shift+4
    "PAGE_FUSION": "key code 23 using shift down",     # Shift+5
    "PAGE_COLOR": "key code 22 using shift down",      # Shift+6
    "PAGE_FAIRLIGHT": "key code 26 using shift down",  # Shift+7
    "PAGE_DELIVER": "key code 28 using shift down",    # Shift+8
    # Meta
    "PING": "",
}

# Bootloader / noise lines from ESP32 after USB open — ignore
_IGNORE_PREFIXES = (
    "ESP-ROM:",
    "Build:",
    "rst:",
    "ets ",
    "SPIWP:",
    "mode:",
    "load:",
    "entry ",
    "==========",
    "[OK]",
    "[WARN]",
    "[ERR]",
    "PSRAM:",
    "    ",
)


def focus_resolve() -> None:
    subprocess.run(
        ["osascript", "-e", 'tell application "DaVinci Resolve" to activate'],
        check=False,
        capture_output=True,
    )
    time.sleep(0.12)


def send_shortcut(action_id: str) -> tuple[bool, str]:
    script = SHORTCUTS.get(action_id)
    if script is None:
        return False, f"unknown action {action_id}"
    if action_id == "PING":
        return True, "ping"

    focus_resolve()
    full = (
        'tell application "System Events"\n'
        f"  {script}\n"
        "end tell"
    )
    r = subprocess.run(
        ["osascript", "-e", full],
        check=False,
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "osascript failed").strip()
        return False, err
    return True, "ok"


def guess_port() -> str | None:
    candidates = []
    for p in list_ports.comports():
        blob = f"{p.device} {p.description} {p.manufacturer or ''}".lower()
        if any(
            k in blob
            for k in (
                "usbserial",
                "wchusb",
                "cp210",
                "ch340",
                "esp32",
                "silicon labs",
                "usbmodem",
            )
        ):
            candidates.append(p.device)
    return candidates[0] if candidates else None


def open_serial(port: str, baud: int) -> serial.Serial:
    """Open without toggling DTR/RTS (avoids ESP32 reset + macOS port drop)."""
    ser = serial.Serial()
    ser.port = port
    ser.baudrate = baud
    ser.timeout = 0.2
    ser.write_timeout = 1.0
    ser.dsrdtr = False
    ser.rtscts = False
    ser.open()
    try:
        ser.setDTR(False)
        ser.setRTS(False)
    except Exception:
        pass
    time.sleep(0.3)
    try:
        ser.reset_input_buffer()
    except Exception:
        pass
    return ser


def safe_write(ser: serial.Serial, data: str) -> None:
    try:
        ser.write(data.encode("utf-8"))
    except Exception as exc:
        print(f"(write failed: {exc})")


def handle_line(line: str, write: Callable[[str], None]) -> None:
    line = line.strip()
    if not line:
        return

    if any(line.startswith(p) for p in _IGNORE_PREFIXES):
        return

    print(f"<< {line}")

    if not line.startswith("CMD:"):
        return

    action = line[4:].strip()
    if not action:
        write("ERR::empty\n")
        return

    ok, detail = send_shortcut(action)
    if ok:
        write(f"ACK:{action}\n")
        print(f">> ACK:{action} ({detail})")
    else:
        write(f"ERR:{action}:{detail}\n")
        print(f">> ERR:{action}:{detail}")


def run_session(port: str, baud: int) -> None:
    ser = open_serial(port, baud)
    print(f"Connected {port} @ {baud}")
    safe_write(ser, "STAT:BRIDGE_ONLINE\n")
    buf = ""
    try:
        while True:
            try:
                chunk = ser.read(256)
            except serial.SerialException as exc:
                raise ConnectionError(str(exc)) from exc

            if chunk:
                buf += chunk.decode("utf-8", errors="ignore")
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)

                    def _w(s: str, _ser: serial.Serial = ser) -> None:
                        safe_write(_ser, s)

                    handle_line(line, _w)
            else:
                time.sleep(0.01)
    finally:
        try:
            ser.close()
        except Exception:
            pass


def main() -> int:
    ap = argparse.ArgumentParser(description="ESP32-DaVinci → Resolve shortcut bridge")
    ap.add_argument("-p", "--port", help="Serial port (default: auto)")
    ap.add_argument("-b", "--baud", type=int, default=115200)
    ap.add_argument("--no-focus", action="store_true", help="Do not activate Resolve")
    args = ap.parse_args()

    if args.no_focus:
        global focus_resolve

        def focus_resolve() -> None:  # type: ignore[no-redef]
            return

    print("macOS: allow Terminal/Python under Privacy → Accessibility")
    print("Chiudi Serial Monitor Arduino. Solo questo bridge sulla porta.")
    print("Ctrl+C to quit.\n")

    try:
        while True:
            port = args.port or guess_port()
            if not port:
                print("Nessuna porta… riprovo tra 2s", file=sys.stderr)
                time.sleep(2)
                continue
            try:
                run_session(port, args.baud)
            except KeyboardInterrupt:
                raise
            except (serial.SerialException, OSError, ConnectionError) as exc:
                print(f"\nPorta persa ({exc}). Riconnetto tra 1.5s…")
                time.sleep(1.5)
    except KeyboardInterrupt:
        print("\nBye")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
