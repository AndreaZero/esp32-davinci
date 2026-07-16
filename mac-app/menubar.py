"""macOS menu bar (status item) helper for the bridge app."""

from __future__ import annotations

from typing import Any, Callable


_CALLBACKS: dict[str, Callable[[], None]] = {}


def _call(name: str) -> None:
    fn = _CALLBACKS.get(name)
    if fn:
        fn()


class MenuBarController:
    """NSStatusItem wrapper. No-op if PyObjC is unavailable."""

    def __init__(
        self,
        *,
        on_show: Callable[[], None],
        on_start: Callable[[], None],
        on_stop: Callable[[], None],
        on_quit: Callable[[], None],
    ) -> None:
        _CALLBACKS["show"] = on_show
        _CALLBACKS["start"] = on_start
        _CALLBACKS["stop"] = on_stop
        _CALLBACKS["quit"] = on_quit
        self._item: Any = None
        self._delegate: Any = None
        self.available = False
        self._install()

    def _install(self) -> None:
        try:
            from AppKit import (  # type: ignore
                NSApplication,
                NSMenu,
                NSMenuItem,
                NSStatusBar,
                NSVariableStatusItemLength,
            )
            from Foundation import NSObject  # type: ignore
        except Exception:
            return

        NSApplication.sharedApplication()

        class _MenuDelegate(NSObject):  # type: ignore[misc, valid-type]
            def showWindow_(self, _sender):  # noqa: N802
                _call("show")

            def startBridge_(self, _sender):  # noqa: N802
                _call("start")

            def stopBridge_(self, _sender):  # noqa: N802
                _call("stop")

            def quitApp_(self, _sender):  # noqa: N802
                _call("quit")

        self._delegate = _MenuDelegate.alloc().init()
        menu = NSMenu.alloc().init()

        def add(title: str, action: str) -> None:
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                title, action, ""
            )
            item.setTarget_(self._delegate)
            menu.addItem_(item)

        add("Show ESP32-DaVinci", "showWindow:")
        menu.addItem_(NSMenuItem.separatorItem())
        add("Start bridge", "startBridge:")
        add("Stop bridge", "stopBridge:")
        menu.addItem_(NSMenuItem.separatorItem())
        add("Quit", "quitApp:")

        bar = NSStatusBar.systemStatusBar()
        item = bar.statusItemWithLength_(NSVariableStatusItemLength)
        item.setMenu_(menu)
        item.button().setTitle_("DV")
        item.button().setToolTip_("ESP32-DaVinci Bridge")

        self._item = item
        self.available = True

    def set_running(self, running: bool) -> None:
        if not self.available or self._item is None:
            return
        title = "DV●" if running else "DV"
        try:
            self._item.button().setTitle_(title)
            tip = "Bridge running" if running else "Bridge stopped"
            self._item.button().setToolTip_(f"ESP32-DaVinci — {tip}")
        except Exception:
            pass

    def remove(self) -> None:
        if not self.available or self._item is None:
            return
        try:
            from AppKit import NSStatusBar  # type: ignore

            NSStatusBar.systemStatusBar().removeStatusItem_(self._item)
        except Exception:
            pass
        self._item = None
        self.available = False
