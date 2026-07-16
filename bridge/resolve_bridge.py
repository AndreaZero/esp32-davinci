#!/usr/bin/env python3
"""ESP32-DaVinci Mac bridge: USB serial CMD:* → DaVinci Resolve keyboard shortcuts."""

from __future__ import annotations

import argparse
import subprocess
import sys
import threading
import time
from typing import Callable

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    print("Missing pyserial. Install with:  pip3 install pyserial", file=sys.stderr)
    sys.exit(1)

try:
    from inject_keys import (
        CHORDS,
        accessibility_help_text,
        accessibility_trusted,
        process_identity,
        send_chord,
    )
except ImportError:
    from bridge.inject_keys import (  # type: ignore
        CHORDS,
        accessibility_help_text,
        accessibility_trusted,
        process_identity,
        send_chord,
    )

# AppleScript fallback (needs Automation → System Events). Prefer Quartz.
_AS_FALLBACK: dict[str, str] = {
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
    "COLOR_ADD_SERIAL": 'keystroke "s" using option down',
    "COLOR_ADD_PARALLEL": 'keystroke "p" using option down',
    "COLOR_ADD_LAYER": 'keystroke "l" using option down',
    "COLOR_BYPASS_NODE": 'keystroke "d" using command down',
    "COLOR_BYPASS_ALL": 'keystroke "d" using shift down',
    "COLOR_RESET_NODE": "key code 115 using command down",
    "MARKER_ADD": 'keystroke "m"',
    "MARKER_NEXT": "key code 125 using shift down",
    "MARKER_PREV": "key code 126 using shift down",
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

_PERM_HINT_SHOWN = False


def _friendly_osascript_error(err: str) -> str:
    low = err.lower()
    if "-1743" in err or "non autorizzato" in low or "not authorized" in low:
        return (
            "macOS blocked Apple Events (-1743). "
            "Prefer Quartz path: install pyobjc-framework-Quartz and enable "
            "Accessibility for this app. Or: System Settings → Privacy → "
            "Automation → allow this app to control System Events"
        )
    return err


def _send_applescript(action_id: str) -> tuple[bool, str]:
    script = _AS_FALLBACK.get(action_id)
    if script is None:
        return False, f"unknown action {action_id}"
    full = f'tell application "System Events"\n  {script}\nend tell'
    r = subprocess.run(
        ["osascript", "-e", full],
        check=False,
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "osascript failed").strip()
        return False, _friendly_osascript_error(err)
    return True, "applescript"


def send_shortcut(action_id: str, *, no_focus: bool) -> tuple[bool, str]:
    global _PERM_HINT_SHOWN
    if action_id == "PING":
        return True, "ping"
    if action_id not in CHORDS and action_id not in _AS_FALLBACK:
        return False, f"unknown action {action_id}"

    # Primary: Quartz CGEvent (Accessibility only — avoids System Events -1743)
    ok, detail = send_chord(action_id, no_focus=no_focus)
    if ok:
        return True, detail

    # Fallback: AppleScript System Events
    if not no_focus:
        subprocess.run(["open", "-a", "DaVinci Resolve"], check=False)
        time.sleep(0.08)
    ok2, detail2 = _send_applescript(action_id)
    if ok2:
        return True, detail2

    if not _PERM_HINT_SHOWN:
        _PERM_HINT_SHOWN = True
        print("\n*** Permissions ***\n" + accessibility_help_text() + "\n", file=sys.stderr)
    return False, detail2


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


def handle_line(line: str, write: Callable[[str], None], *, no_focus: bool) -> None:
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

    ok, detail = send_shortcut(action, no_focus=no_focus)
    if ok:
        write(f"ACK:{action}\n")
        print(f">> ACK:{action} ({detail})")
    else:
        # Keep ERR payload short for the panel serial buffer
        short = detail.replace("\n", " ")[:180]
        write(f"ERR:{action}:{short}\n")
        print(f">> ERR:{action}:{detail}")


def run_session(
    port: str,
    baud: int,
    no_focus: bool,
    stop_event: threading.Event | None = None,
) -> None:
    ser = open_serial(port, baud)
    print(f"Connected {port} @ {baud}")
    safe_write(ser, "STAT:BRIDGE_ONLINE\n")
    buf = ""
    try:
        while True:
            if stop_event is not None and stop_event.is_set():
                break
            try:
                chunk = ser.read(256)
            except serial.SerialException as exc:
                raise ConnectionError(str(exc)) from exc

            if chunk:
                buf += chunk.decode("utf-8", errors="ignore")
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    handle_line(
                        line,
                        lambda s: safe_write(ser, s),
                        no_focus=no_focus,
                    )
            else:
                time.sleep(0.01)
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


def run_bridge(
    port: str | None = None,
    baud: int = 115200,
    no_focus: bool = False,
    stop_event: threading.Event | None = None,
) -> None:
    """Run until stop_event is set (or KeyboardInterrupt). Used by CLI and Mac app."""
    print("macOS: enable Accessibility for this app (Privacy → Accessibility)")
    print("Shortcuts use Quartz key events (no System Events / Automation needed).")
    print(f"Process: {process_identity()}")
    trusted = accessibility_trusted(prompt=True)
    print(f"Accessibility trusted: {trusted}")
    if trusted is False:
        print(accessibility_help_text(), file=sys.stderr)
    print("Close Arduino Serial Monitor.\n")

    try:
        while True:
            if stop_event is not None and stop_event.is_set():
                break
            use_port = port or guess_port()
            if not use_port:
                print("No serial port… retry in 2s", file=sys.stderr)
                if stop_event is not None:
                    stop_event.wait(2)
                else:
                    time.sleep(2)
                continue
            try:
                run_session(use_port, baud, no_focus, stop_event=stop_event)
            except KeyboardInterrupt:
                raise
            except (serial.SerialException, OSError, ConnectionError) as exc:
                print(f"\nPort lost ({exc}). Reconnect in 1.5s…")
                if stop_event is not None and stop_event.is_set():
                    break
                if stop_event is not None:
                    stop_event.wait(1.5)
                else:
                    time.sleep(1.5)
    except KeyboardInterrupt:
        print("\nBye")


def main() -> int:
    ap = argparse.ArgumentParser(description="ESP32-DaVinci → Resolve shortcut bridge")
    ap.add_argument("-p", "--port", help="Serial port (default: auto)")
    ap.add_argument("-b", "--baud", type=int, default=115200)
    ap.add_argument("--no-focus", action="store_true", help="Do not activate Resolve")
    args = ap.parse_args()

    try:
        run_bridge(port=args.port, baud=args.baud, no_focus=args.no_focus)
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
