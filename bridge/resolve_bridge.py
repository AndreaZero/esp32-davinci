#!/usr/bin/env python3
"""ESP32-DaVinci Mac bridge: USB serial CMD:* → shortcuts + INFO:* from Resolve API."""

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

from resolve_api import ResolveApi

# Action ID → AppleScript fragment inside System Events (after Resolve is focused)
# Preset: DaVinci Resolve default (Mac)
SHORTCUTS: dict[str, str] = {
    "CUT": 'keystroke "b" using command down',
    "UNDO": 'keystroke "z" using command down',
    "REDO": 'keystroke "z" using {command down, shift down}',
    "RIPPLE_DEL": "key code 117 using shift down",
    "DEL": "key code 117",
    "SPLIT": "key code 42 using command down",
    "SAVE": 'keystroke "s" using command down',
    "PLAY": "keystroke space",
    "JK_BACK": 'keystroke "j"',
    "JK_STOP": 'keystroke "k"',
    "JK_FWD": 'keystroke "l"',
    "FIT": 'keystroke "z" using shift down',
    "SNAP": 'keystroke "n"',
    "SELECT_TOOL": 'keystroke "a"',
    "TRIM_TOOL": 'keystroke "t"',
    "BLADE_TOOL": 'keystroke "b"',
    "MARK_IN": 'keystroke "i"',
    "MARK_OUT": 'keystroke "o"',
    "INSERT": "key code 101",
    "OVERWRITE": "key code 109",
    "REPLACE": "key code 103",
    "PAGE_MEDIA": "key code 19 using shift down",
    "PAGE_CUT": "key code 20 using shift down",
    "PAGE_EDIT": "key code 21 using shift down",
    "PAGE_FUSION": "key code 23 using shift down",
    "PAGE_COLOR": "key code 22 using shift down",
    "PAGE_FAIRLIGHT": "key code 26 using shift down",
    "PAGE_DELIVER": "key code 28 using shift down",
    "PING": "",
}

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

# Live TC while playing — ~10 Hz over serial
INFO_INTERVAL_S = 0.1
# Console log throttle (serial still sends every INFO tick)
INFO_LOG_INTERVAL_S = 1.0


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
    ser = serial.Serial()
    ser.port = port
    ser.baudrate = baud
    ser.timeout = 0.05
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


def run_session(port: str, baud: int, api: ResolveApi, no_info: bool) -> None:
    ser = open_serial(port, baud)
    print(f"Connected {port} @ {baud}")
    safe_write(ser, "STAT:BRIDGE_ONLINE\n")
    buf = ""
    last_info = ""
    next_info_t = 0.0
    next_log_t = 0.0
    try:
        while True:
            now = time.monotonic()
            if not no_info and now >= next_info_t:
                next_info_t = now + INFO_INTERVAL_S
                status = api.get_status()
                line = status.to_info_line()
                # Always push INFO (live TC); log only on change or ~1 Hz
                safe_write(ser, line + "\n")
                if line != last_info or now >= next_log_t:
                    last_info = line
                    next_log_t = now + INFO_LOG_INTERVAL_S
                    print(f">> {line}")
            elif no_info and now >= next_info_t:
                # Heartbeat so panel detects bridge alive without API
                next_info_t = now + 0.5
                safe_write(ser, "STAT:HB\n")

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
                time.sleep(0.005)
    finally:
        try:
            safe_write(ser, "STAT:BRIDGE_OFF\n")
            time.sleep(0.05)
        except Exception:
            pass
        try:
            ser.close()
        except Exception:
            pass


def main() -> int:
    ap = argparse.ArgumentParser(description="ESP32-DaVinci → Resolve bridge")
    ap.add_argument("-p", "--port", help="Serial port (default: auto)")
    ap.add_argument("-b", "--baud", type=int, default=115200)
    ap.add_argument("--no-focus", action="store_true", help="Do not activate Resolve")
    ap.add_argument("--no-info", action="store_true", help="Disable Resolve API INFO poll")
    args = ap.parse_args()

    if args.no_focus:
        global focus_resolve

        def focus_resolve() -> None:  # type: ignore[no-redef]
            return

    api = ResolveApi()
    if not args.no_info:
        if api.connect():
            print("Resolve API: connected")
        else:
            print(
                f"Resolve API: not ready ({api.last_error}). "
                "Will retry. Check Studio + External Scripting = Local."
            )

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
                run_session(port, args.baud, api, args.no_info)
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
