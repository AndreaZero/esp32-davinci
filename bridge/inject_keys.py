"""Inject Resolve shortcuts on macOS via Quartz (Accessibility) — no System Events."""

from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass

# macOS virtual key codes (ANSI)
_VK = {
    "a": 0,
    "s": 1,
    "d": 2,
    "z": 6,
    "b": 11,
    "t": 17,
    "1": 18,
    "2": 19,
    "3": 20,
    "4": 21,
    "6": 22,
    "5": 23,
    "7": 26,
    "8": 28,
    "o": 31,
    "i": 34,
    "p": 35,
    "l": 37,
    "j": 38,
    "k": 40,
    "backslash": 42,
    "n": 45,
    "m": 46,
    "space": 49,
    "f9": 101,
    "f11": 103,
    "f10": 109,
    "home": 115,
    "forward_delete": 117,
    "down": 125,
    "up": 126,
}

MOD_CMD = 1
MOD_SHIFT = 2
MOD_OPT = 4
MOD_CTRL = 8

_PROMPT_DONE = False
_WARNED_UNTRUSTED = False


@dataclass(frozen=True)
class KeyChord:
    code: int
    mods: int = 0


# Action ID → virtual key (+ modifiers). DaVinci Resolve default Mac preset.
CHORDS: dict[str, KeyChord] = {
    "CUT": KeyChord(_VK["b"], MOD_CMD),
    "UNDO": KeyChord(_VK["z"], MOD_CMD),
    "REDO": KeyChord(_VK["z"], MOD_CMD | MOD_SHIFT),
    "RIPPLE_DEL": KeyChord(_VK["forward_delete"], MOD_SHIFT),
    "DEL": KeyChord(_VK["forward_delete"]),
    "SPLIT": KeyChord(_VK["backslash"], MOD_CMD),
    "SAVE": KeyChord(_VK["s"], MOD_CMD),
    "PLAY": KeyChord(_VK["space"]),
    "JK_BACK": KeyChord(_VK["j"]),
    "JK_STOP": KeyChord(_VK["k"]),
    "JK_FWD": KeyChord(_VK["l"]),
    "FIT": KeyChord(_VK["z"], MOD_SHIFT),
    "SNAP": KeyChord(_VK["n"]),
    "SELECT_TOOL": KeyChord(_VK["a"]),
    "TRIM_TOOL": KeyChord(_VK["t"]),
    "BLADE_TOOL": KeyChord(_VK["b"]),
    "MARK_IN": KeyChord(_VK["i"]),
    "MARK_OUT": KeyChord(_VK["o"]),
    "INSERT": KeyChord(_VK["f9"]),
    "OVERWRITE": KeyChord(_VK["f10"]),
    "REPLACE": KeyChord(_VK["f11"]),
    "PAGE_MEDIA": KeyChord(_VK["2"], MOD_SHIFT),
    "PAGE_CUT": KeyChord(_VK["3"], MOD_SHIFT),
    "PAGE_EDIT": KeyChord(_VK["4"], MOD_SHIFT),
    "PAGE_FUSION": KeyChord(_VK["5"], MOD_SHIFT),
    "PAGE_COLOR": KeyChord(_VK["6"], MOD_SHIFT),
    "PAGE_FAIRLIGHT": KeyChord(_VK["7"], MOD_SHIFT),
    "PAGE_DELIVER": KeyChord(_VK["8"], MOD_SHIFT),
    "COLOR_ADD_SERIAL": KeyChord(_VK["s"], MOD_OPT),
    "COLOR_ADD_PARALLEL": KeyChord(_VK["p"], MOD_OPT),
    "COLOR_ADD_LAYER": KeyChord(_VK["l"], MOD_OPT),
    "COLOR_BYPASS_NODE": KeyChord(_VK["d"], MOD_CMD),
    "COLOR_BYPASS_ALL": KeyChord(_VK["d"], MOD_SHIFT),
    "COLOR_RESET_NODE": KeyChord(_VK["home"], MOD_CMD),
    "MARKER_ADD": KeyChord(_VK["m"]),
    "MARKER_NEXT": KeyChord(_VK["down"], MOD_SHIFT),
    "MARKER_PREV": KeyChord(_VK["up"], MOD_SHIFT),
}


def process_identity() -> str:
    exe = getattr(sys, "executable", "?")
    frozen = getattr(sys, "frozen", False)
    return f"frozen={frozen} exe={exe}"


def accessibility_trusted(*, prompt: bool = False) -> bool | None:
    """True/False if check works; None if APIs unavailable."""
    global _PROMPT_DONE
    try:
        from ApplicationServices import (  # type: ignore
            AXIsProcessTrusted,
            AXIsProcessTrustedWithOptions,
            kAXTrustedCheckOptionPrompt,
        )
        from Foundation import NSDictionary  # type: ignore

        if prompt and not _PROMPT_DONE:
            _PROMPT_DONE = True
            opts = NSDictionary.dictionaryWithObject_forKey_(
                True, kAXTrustedCheckOptionPrompt
            )
            return bool(AXIsProcessTrustedWithOptions(opts))
        return bool(AXIsProcessTrusted())
    except Exception:
        try:
            from Quartz import AXIsProcessTrusted  # type: ignore

            return bool(AXIsProcessTrusted())
        except Exception:
            return None


def open_accessibility_settings() -> None:
    # Ventura+ + older fallbacks
    for url in (
        "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility",
        "x-apple.systempreferences:com.apple.settings.PrivacySecurity.extension?Privacy_Accessibility",
    ):
        subprocess.run(["open", url], check=False)


def accessibility_help_text() -> str:
    return (
        "macOS reports Accessibility=OFF for this process even if the toggle looks on "
        "(common after rebuild).\n\n"
        f"{process_identity()}\n\n"
        "Fix:\n"
        "1) Quit ESP32-DaVinci Bridge completely (menu bar → Quit)\n"
        "2) System Settings → Privacy → Accessibility → remove ESP32-DaVinci-Bridge\n"
        "3) Terminal: tccutil reset Accessibility com.andreazero.esp32-davinci-bridge\n"
        "4) Reopen the app, click Allow if prompted, enable the NEW entry\n"
        "5) Prefer the copy in /Applications after: ./build.sh"
    )


def focus_resolve() -> None:
    subprocess.run(["open", "-a", "DaVinci Resolve"], check=False)
    time.sleep(0.1)


def _quartz_flags(mods: int) -> int:
    from Quartz import (  # type: ignore
        kCGEventFlagMaskAlternate,
        kCGEventFlagMaskCommand,
        kCGEventFlagMaskControl,
        kCGEventFlagMaskShift,
    )

    flags = 0
    if mods & MOD_CMD:
        flags |= kCGEventFlagMaskCommand
    if mods & MOD_SHIFT:
        flags |= kCGEventFlagMaskShift
    if mods & MOD_OPT:
        flags |= kCGEventFlagMaskAlternate
    if mods & MOD_CTRL:
        flags |= kCGEventFlagMaskControl
    return flags


def tap_key(chord: KeyChord) -> None:
    from Quartz import (  # type: ignore
        CGEventCreateKeyboardEvent,
        CGEventPost,
        CGEventSetFlags,
        kCGHIDEventTap,
    )

    flags = _quartz_flags(chord.mods)
    down = CGEventCreateKeyboardEvent(None, chord.code, True)
    up = CGEventCreateKeyboardEvent(None, chord.code, False)
    if flags:
        CGEventSetFlags(down, flags)
        CGEventSetFlags(up, flags)
    CGEventPost(kCGHIDEventTap, down)
    CGEventPost(kCGHIDEventTap, up)


def send_chord(action_id: str, *, no_focus: bool = False) -> tuple[bool, str]:
    """Send a shortcut. Always attempts Quartz; trust check is advisory."""
    global _WARNED_UNTRUSTED

    if action_id == "PING":
        return True, "ping"
    chord = CHORDS.get(action_id)
    if chord is None:
        return False, f"unknown action {action_id}"

    if not no_focus:
        focus_resolve()

    trusted = accessibility_trusted(prompt=False)

    try:
        tap_key(chord)
    except Exception as exc:
        return False, f"quartz failed: {exc}"

    # macOS often lists an old binary as "enabled" while AXIsProcessTrusted is still false.
    # We still post events (sometimes they work). If not trusted, warn once — do not
    # open Settings on every panel tap.
    if trusted is False:
        if not _WARNED_UNTRUSTED:
            _WARNED_UNTRUSTED = True
            print(accessibility_help_text(), file=sys.stderr)
        return True, "quartz-untrusted"

    return True, "quartz"
