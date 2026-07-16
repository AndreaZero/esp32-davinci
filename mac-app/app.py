#!/usr/bin/env python3
"""ESP32-DaVinci Bridge — macOS desktop controller with menu bar widget."""

from __future__ import annotations

import json
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from menubar import MenuBarController


# Resolve bridge package path (dev + PyInstaller)
def _bridge_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "bridge"  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent / "bridge"


BRIDGE_DIR = _bridge_dir()
sys.path.insert(0, str(BRIDGE_DIR))

from resolve_bridge import guess_port, run_bridge  # noqa: E402


APP_NAME = "ESP32-DaVinci Bridge"
BUNDLE_ID = "com.andreazero.esp32-davinci-bridge"
SUPPORT_DIR = Path.home() / "Library" / "Application Support" / "ESP32-DaVinci"
CONFIG_PATH = SUPPORT_DIR / "config.json"
LAUNCH_AGENT = Path.home() / "Library" / "LaunchAgents" / f"{BUNDLE_ID}.plist"

BG = "#0D0D0F"
SURFACE = "#1A1A1F"
TEXT = "#F0F0F2"
MUTED = "#6B6B70"
ACCENT = "#C9A227"
OK = "#4CAF50"
DANGER = "#E85D4C"
BTN = "#2A2A32"


def load_config() -> dict:
    SUPPORT_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "port": "",
        "baud": 115200,
        "no_focus": False,
        "open_at_login": False,
        "auto_start_bridge": True,
        "start_in_menubar": False,
    }


def save_config(cfg: dict) -> None:
    SUPPORT_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def app_launch_args() -> list[str]:
    """Command used by LaunchAgent to open this app at login."""
    if getattr(sys, "frozen", False):
        # …/ESP32-DaVinci-Bridge.app/Contents/MacOS/<bin>
        app_bundle = Path(sys.executable).resolve().parents[2]
        return ["/usr/bin/open", "-a", str(app_bundle)]
    return [sys.executable, str(Path(__file__).resolve())]


def write_launch_agent(enabled: bool) -> None:
    LAUNCH_AGENT.parent.mkdir(parents=True, exist_ok=True)
    label = BUNDLE_ID
    if not enabled:
        if LAUNCH_AGENT.exists():
            subprocess.run(["launchctl", "unload", str(LAUNCH_AGENT)], check=False)
            LAUNCH_AGENT.unlink(missing_ok=True)
        return

    args_xml = "\n".join(f"      <string>{a}</string>" for a in app_launch_args())
    program_args = f"""
    <array>
{args_xml}
    </array>"""

    plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>{label}</string>
  <key>ProgramArguments</key>{program_args}
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <false/>
</dict>
</plist>
"""
    LAUNCH_AGENT.write_text(plist, encoding="utf-8")
    subprocess.run(["launchctl", "unload", str(LAUNCH_AGENT)], check=False)
    subprocess.run(["launchctl", "load", str(LAUNCH_AGENT)], check=False)


class BridgeApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        self.geometry("520x520")
        self.minsize(480, 440)
        self.configure(bg=BG)

        self.cfg = load_config()
        self.stop_event: threading.Event | None = None
        self.worker: threading.Thread | None = None
        self.log_q: queue.Queue[str] = queue.Queue()
        self._running = False
        self._quitting = False
        self.menubar: MenuBarController | None = None

        self._build_style()
        self._build_ui()
        self._refresh_ports()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(200, self._drain_log)
        self.after(50, self._setup_menubar)
        # TCC prompt must run on the UI thread (not the bridge worker).
        self.after(150, self._request_accessibility)

        if self.cfg.get("auto_start_bridge"):
            self.after(500, self.start_bridge)

        if self.cfg.get("start_in_menubar"):
            self.after(100, self.hide_to_menubar)

    def _setup_menubar(self) -> None:
        self.menubar = MenuBarController(
            on_show=lambda: self.after(0, self.show_window),
            on_start=lambda: self.after(0, self.start_bridge),
            on_stop=lambda: self.after(0, self.stop_bridge),
            on_quit=lambda: self.after(0, self.quit_app),
        )
        if self.menubar.available:
            self.menubar.set_running(self._running)
            self._append_log("Menu bar widget ready (DV). Close window to keep running there.")
        else:
            self._append_log(
                "Menu bar unavailable — install: pip3 install pyobjc-framework-Cocoa"
            )
            self.detail_var.set("Install pyobjc-framework-Cocoa for menu bar widget")

    def _request_accessibility(self) -> None:
        try:
            from inject_keys import (
                accessibility_help_text,
                accessibility_trusted,
                process_identity,
            )
        except Exception as exc:
            self._append_log(f"Accessibility check unavailable: {exc}")
            return
        self._append_log(f"Process: {process_identity()}")
        trusted = accessibility_trusted(prompt=True)
        self._append_log(f"Accessibility trusted: {trusted}")
        if trusted is False:
            self._append_log(
                "Toggle looks on but macOS still says OFF — remove entry, "
                "run tccutil reset, rebuild/sign, reopen (see Fix Accessibility)."
            )

    def _fix_accessibility(self) -> None:
        try:
            from inject_keys import (
                accessibility_help_text,
                accessibility_trusted,
                open_accessibility_settings,
                process_identity,
            )
        except Exception as exc:
            messagebox.showerror(APP_NAME, str(exc))
            return
        trusted = accessibility_trusted(prompt=True)
        open_accessibility_settings()
        msg = (
            f"Trusted now: {trusted}\n\n"
            f"{process_identity()}\n\n"
            f"{accessibility_help_text()}"
        )
        self._append_log(f"Accessibility trusted: {trusted}")
        messagebox.showinfo(APP_NAME, msg)

    def _build_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TFrame", background=BG)
        style.configure("Card.TFrame", background=SURFACE)
        style.configure("TLabel", background=BG, foreground=TEXT, font=("Helvetica", 13))
        style.configure("Muted.TLabel", background=BG, foreground=MUTED, font=("Helvetica", 11))
        style.configure("Card.TLabel", background=SURFACE, foreground=TEXT, font=("Helvetica", 13))
        style.configure("Status.TLabel", background=SURFACE, foreground=ACCENT, font=("Helvetica", 15, "bold"))
        style.configure("TCheckbutton", background=BG, foreground=TEXT, font=("Helvetica", 12))
        style.configure("TButton", font=("Helvetica", 12))
        style.configure("TCombobox", font=("Helvetica", 12))

    def _build_ui(self) -> None:
        pad = {"padx": 16, "pady": 8}
        root = ttk.Frame(self, style="TFrame")
        root.pack(fill=tk.BOTH, expand=True, **pad)

        title = tk.Label(
            root,
            text="ESP32-DaVinci",
            bg=BG,
            fg=TEXT,
            font=("Helvetica", 22, "bold"),
        )
        title.pack(anchor="w")

        sub = ttk.Label(
            root,
            text="Menu bar: DV / DV● — close this window to keep the bridge in the menu bar.",
            style="Muted.TLabel",
        )
        sub.pack(anchor="w", pady=(0, 12))

        card = tk.Frame(root, bg=SURFACE, highlightthickness=0)
        card.pack(fill=tk.X, pady=(0, 12))

        self.status_var = tk.StringVar(value="Stopped")
        self.status_lbl = tk.Label(
            card,
            textvariable=self.status_var,
            bg=SURFACE,
            fg=MUTED,
            font=("Helvetica", 16, "bold"),
        )
        self.status_lbl.pack(anchor="w", padx=16, pady=(14, 4))

        self.detail_var = tk.StringVar(value="Bridge is not running")
        tk.Label(
            card,
            textvariable=self.detail_var,
            bg=SURFACE,
            fg=MUTED,
            font=("Helvetica", 11),
        ).pack(anchor="w", padx=16, pady=(0, 14))

        row = ttk.Frame(root)
        row.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(row, text="Serial port").pack(side=tk.LEFT)
        self.port_var = tk.StringVar(value=self.cfg.get("port") or "")
        self.port_combo = ttk.Combobox(row, textvariable=self.port_var, width=28)
        self.port_combo.pack(side=tk.LEFT, padx=(8, 8))
        ttk.Button(row, text="Refresh", command=self._refresh_ports).pack(side=tk.LEFT)

        btns = ttk.Frame(root)
        btns.pack(fill=tk.X, pady=(4, 8))
        self.btn_start = tk.Button(
            btns,
            text="Start bridge",
            command=self.start_bridge,
            bg=OK,
            fg="#fff",
            activebackground="#388E3C",
            relief=tk.FLAT,
            padx=16,
            pady=8,
            font=("Helvetica", 13, "bold"),
        )
        self.btn_start.pack(side=tk.LEFT)
        self.btn_stop = tk.Button(
            btns,
            text="Stop",
            command=self.stop_bridge,
            bg=BTN,
            fg=TEXT,
            activebackground="#3A3A42",
            relief=tk.FLAT,
            padx=16,
            pady=8,
            font=("Helvetica", 13),
            state=tk.DISABLED,
        )
        self.btn_stop.pack(side=tk.LEFT, padx=(8, 0))
        self.btn_hide = tk.Button(
            btns,
            text="Hide to menu bar",
            command=self.hide_to_menubar,
            bg=BTN,
            fg=TEXT,
            activebackground="#3A3A42",
            relief=tk.FLAT,
            padx=16,
            pady=8,
            font=("Helvetica", 13),
        )
        self.btn_hide.pack(side=tk.LEFT, padx=(8, 0))
        self.btn_ax = tk.Button(
            btns,
            text="Fix Accessibility",
            command=self._fix_accessibility,
            bg=BTN,
            fg=TEXT,
            activebackground="#3A3A42",
            relief=tk.FLAT,
            padx=12,
            pady=8,
            font=("Helvetica", 12),
        )
        self.btn_ax.pack(side=tk.LEFT, padx=(8, 0))

        self.login_var = tk.BooleanVar(value=bool(self.cfg.get("open_at_login")))
        self.autostart_var = tk.BooleanVar(value=bool(self.cfg.get("auto_start_bridge", True)))
        self.menubar_start_var = tk.BooleanVar(value=bool(self.cfg.get("start_in_menubar")))
        self.nofocus_var = tk.BooleanVar(value=bool(self.cfg.get("no_focus")))

        opts = ttk.Frame(root)
        opts.pack(fill=tk.X, pady=(8, 4))
        tk.Checkbutton(
            opts,
            text="Open this app at Mac login",
            variable=self.login_var,
            command=self._on_login_toggle,
            bg=BG,
            fg=TEXT,
            activebackground=BG,
            activeforeground=TEXT,
            selectcolor=SURFACE,
            font=("Helvetica", 12),
        ).pack(anchor="w")
        tk.Checkbutton(
            opts,
            text="Start bridge automatically when app opens",
            variable=self.autostart_var,
            command=self._save_prefs,
            bg=BG,
            fg=TEXT,
            activebackground=BG,
            activeforeground=TEXT,
            selectcolor=SURFACE,
            font=("Helvetica", 12),
        ).pack(anchor="w")
        tk.Checkbutton(
            opts,
            text="Start hidden in menu bar (no window)",
            variable=self.menubar_start_var,
            command=self._save_prefs,
            bg=BG,
            fg=TEXT,
            activebackground=BG,
            activeforeground=TEXT,
            selectcolor=SURFACE,
            font=("Helvetica", 12),
        ).pack(anchor="w")
        tk.Checkbutton(
            opts,
            text="Do not focus Resolve before each shortcut",
            variable=self.nofocus_var,
            command=self._save_prefs,
            bg=BG,
            fg=TEXT,
            activebackground=BG,
            activeforeground=TEXT,
            selectcolor=SURFACE,
            font=("Helvetica", 12),
        ).pack(anchor="w")

        ttk.Label(root, text="Log", style="Muted.TLabel").pack(anchor="w", pady=(12, 4))
        self.log = tk.Text(
            root,
            height=12,
            bg=SURFACE,
            fg=TEXT,
            insertbackground=TEXT,
            relief=tk.FLAT,
            font=("Menlo", 11),
        )
        self.log.pack(fill=tk.BOTH, expand=True)
        self.log.insert("end", "Ready.\n")
        self.log.configure(state=tk.DISABLED)

    def _refresh_ports(self) -> None:
        try:
            from serial.tools import list_ports

            ports = [p.device for p in list_ports.comports()]
        except Exception as exc:
            self._append_log(f"Port scan failed: {exc}")
            ports = []
        auto = guess_port()
        values = []
        if auto:
            values.append(f"Auto ({auto})")
        values.extend(ports)
        if not values:
            values = ["(no ports found)"]
        self.port_combo["values"] = values
        if self.port_var.get() not in values and values:
            self.port_var.set(values[0])

    def _selected_port(self) -> str | None:
        raw = self.port_var.get().strip()
        if not raw or raw.startswith("(no"):
            return None
        if raw.startswith("Auto"):
            return None
        return raw

    def _save_prefs(self) -> None:
        self.cfg["port"] = self._selected_port() or ""
        self.cfg["open_at_login"] = bool(self.login_var.get())
        self.cfg["auto_start_bridge"] = bool(self.autostart_var.get())
        self.cfg["start_in_menubar"] = bool(self.menubar_start_var.get())
        self.cfg["no_focus"] = bool(self.nofocus_var.get())
        save_config(self.cfg)

    def _on_login_toggle(self) -> None:
        self._save_prefs()
        try:
            write_launch_agent(bool(self.login_var.get()))
            state = "enabled" if self.login_var.get() else "disabled"
            self._append_log(f"Open at login {state}.")
        except Exception as exc:
            messagebox.showerror(APP_NAME, f"Could not update Login Item:\n{exc}")
            self.login_var.set(False)

    def _append_log(self, line: str) -> None:
        self.log.configure(state=tk.NORMAL)
        self.log.insert("end", line.rstrip() + "\n")
        self.log.see("end")
        self.log.configure(state=tk.DISABLED)

    def _drain_log(self) -> None:
        try:
            while True:
                self._append_log(self.log_q.get_nowait())
        except queue.Empty:
            pass
        self.after(200, self._drain_log)

    def _set_running(self, running: bool) -> None:
        self._running = running
        if running:
            self.status_var.set("Running")
            self.status_lbl.configure(fg=OK)
            self.detail_var.set("Listening for panel commands · menu bar DV●")
            self.btn_start.configure(state=tk.DISABLED)
            self.btn_stop.configure(state=tk.NORMAL)
        else:
            self.status_var.set("Stopped")
            self.status_lbl.configure(fg=MUTED)
            self.detail_var.set("Bridge is not running · menu bar DV")
            self.btn_start.configure(state=tk.NORMAL)
            self.btn_stop.configure(state=tk.DISABLED)
        if self.menubar:
            self.menubar.set_running(running)

    def show_window(self) -> None:
        self.deiconify()
        self.lift()
        self.focus_force()
        try:
            self.attributes("-topmost", True)
            self.after(200, lambda: self.attributes("-topmost", False))
        except Exception:
            pass

    def hide_to_menubar(self) -> None:
        self._save_prefs()
        if self.menubar and self.menubar.available:
            self.withdraw()
        else:
            self.iconify()

    def start_bridge(self) -> None:
        if self._running:
            return
        self._save_prefs()
        port = self._selected_port()
        no_focus = bool(self.nofocus_var.get())
        self.stop_event = threading.Event()

        class QueueWriter:
            def __init__(self, q: queue.Queue[str]) -> None:
                self.q = q

            def write(self, s: str) -> int:
                if s and s.strip():
                    self.q.put(s.rstrip())
                return len(s)

            def flush(self) -> None:
                return None

        def worker() -> None:
            old_out, old_err = sys.stdout, sys.stderr
            sys.stdout = QueueWriter(self.log_q)  # type: ignore[assignment]
            sys.stderr = QueueWriter(self.log_q)  # type: ignore[assignment]
            try:
                run_bridge(
                    port=port,
                    baud=int(self.cfg.get("baud", 115200)),
                    no_focus=no_focus,
                    stop_event=self.stop_event,
                )
            except Exception as exc:
                self.log_q.put(f"Bridge error: {exc}")
            finally:
                sys.stdout, sys.stderr = old_out, old_err
                self.after(0, lambda: self._set_running(False))

        self.worker = threading.Thread(target=worker, name="bridge", daemon=True)
        self.worker.start()
        self._set_running(True)
        self._append_log("Bridge starting…")

    def stop_bridge(self) -> None:
        if self.stop_event is not None:
            self.stop_event.set()
            self._append_log("Stopping bridge…")
        self._set_running(False)

    def quit_app(self) -> None:
        self._quitting = True
        self._save_prefs()
        if self._running:
            self.stop_bridge()
            if self.worker:
                self.worker.join(timeout=2.0)
        if self.menubar:
            self.menubar.remove()
        self.destroy()

    def _on_close(self) -> None:
        """Close button (X): hide to menu bar instead of quitting."""
        if self._quitting:
            return
        if self.menubar and self.menubar.available:
            self.hide_to_menubar()
            return
        # Fallback without menu bar: confirm quit
        self._save_prefs()
        if self._running:
            if not messagebox.askyesno(APP_NAME, "Stop the bridge and quit?"):
                return
            self.stop_bridge()
            if self.worker:
                self.worker.join(timeout=2.0)
        self.destroy()


def main() -> int:
    app = BridgeApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
