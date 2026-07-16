"""DaVinci Resolve Studio scripting helpers for ESP32-DaVinci bridge."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Any


def _default_mac_paths() -> tuple[str, str, str]:
    api = (
        "/Library/Application Support/Blackmagic Design/"
        "DaVinci Resolve/Developer/Scripting"
    )
    lib = (
        "/Applications/DaVinci Resolve/DaVinci Resolve.app/"
        "Contents/Libraries/Fusion/fusionscript.so"
    )
    modules = os.path.join(api, "Modules")
    return api, lib, modules


def ensure_resolve_env() -> None:
    """Set RESOLVE_SCRIPT_* / PYTHONPATH if missing (macOS defaults)."""
    api, lib, modules = _default_mac_paths()
    os.environ.setdefault("RESOLVE_SCRIPT_API", api)
    os.environ.setdefault("RESOLVE_SCRIPT_LIB", lib)
    py_path = os.environ.get("PYTHONPATH", "")
    if modules not in py_path.split(os.pathsep):
        os.environ["PYTHONPATH"] = (
            modules if not py_path else modules + os.pathsep + py_path
        )
    if modules not in sys.path:
        sys.path.insert(0, modules)


@dataclass
class ResolveStatus:
    ok: bool
    kind: str  # "ok" | "no_resolve" | "no_timeline"
    timecode: str = ""
    clip_name: str = ""
    page: str = ""

    def to_info_line(self) -> str:
        if self.kind == "no_resolve":
            return "INFO:NO_RESOLVE"
        if self.kind == "no_timeline":
            return "INFO:NO_TIMELINE"
        tc = _sanitize(self.timecode, 20)
        clip = _sanitize(self.clip_name, 48)
        page = _sanitize(self.page, 16)
        line = f"INFO:tc={tc}|clip={clip}|page={page}"
        if len(line) > 120:
            line = line[:120]
        return line


def _sanitize(s: str, max_len: int) -> str:
    out = (s or "").replace("|", "/").replace("\n", " ").replace("\r", " ").strip()
    if len(out) > max_len:
        out = out[: max_len - 1] + "…"
    return out if out else "-"


class ResolveApi:
    def __init__(self) -> None:
        self._resolve: Any = None
        self._import_error: str | None = None
        ensure_resolve_env()

    def connect(self) -> bool:
        try:
            import DaVinciResolveScript as dvr  # type: ignore
        except Exception as exc:
            self._import_error = str(exc)
            self._resolve = None
            return False

        try:
            self._resolve = dvr.scriptapp("Resolve")
        except Exception as exc:
            self._import_error = str(exc)
            self._resolve = None
            return False

        if self._resolve is None:
            self._import_error = "scriptapp returned None (Resolve closed or scripting off)"
            return False
        self._import_error = None
        return True

    @property
    def last_error(self) -> str | None:
        return self._import_error

    def get_status(self) -> ResolveStatus:
        if self._resolve is None and not self.connect():
            return ResolveStatus(ok=False, kind="no_resolve")

        resolve = self._resolve
        try:
            page = ""
            try:
                page = str(resolve.GetCurrentPage() or "")
            except Exception:
                page = ""

            project = resolve.GetProjectManager().GetCurrentProject()
            if project is None:
                return ResolveStatus(ok=False, kind="no_timeline", page=page)

            timeline = project.GetCurrentTimeline()
            if timeline is None:
                return ResolveStatus(ok=False, kind="no_timeline", page=page)

            tc = ""
            try:
                tc = str(timeline.GetCurrentTimecode() or "")
            except Exception:
                tc = ""

            clip_name = "-"
            try:
                item = timeline.GetCurrentVideoItem()
                if item is not None:
                    clip_name = str(item.GetName() or "-")
            except Exception:
                clip_name = "-"

            return ResolveStatus(
                ok=True,
                kind="ok",
                timecode=tc or "-",
                clip_name=clip_name,
                page=page or "-",
            )
        except Exception:
            # Resolve may have quit mid-call
            self._resolve = None
            return ResolveStatus(ok=False, kind="no_resolve")
