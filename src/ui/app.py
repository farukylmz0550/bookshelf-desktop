# Book Shelf — the GtkApplication itself.
# License: GPL-3.0-or-later (see LICENSE).

"""Application bootstrap: flags, theming, and the single main window."""

import logging
import sys

import gi

gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib

from shared import config, logs, texts, theme
from ui.window import MainWindow

from shared.paths import APP_ID  # noqa: F401 - re-exported for the application
logger = logging.getLogger("bookshelf")


class KatipApp(Adw.Application):
    """Owns the main window and the shutdown hooks."""

    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.HANDLES_OPEN)

    def do_activate(self):
        theme.apply(config.theme())
        window = MainWindow(self)
        window.present()

    def do_open(self, files, n, hint):
        self.do_activate()


def _use_fontconfig_fontmap() -> None:
    """Force Pango's fontconfig fontmap on Windows.

    Pango picks its Win32 fontmap there, whose GDI text rendering comes out
    mangled (garbled glyphs under Wine and thin rendering on real Windows);
    the fontconfig fontmap renders cleanly and is what the bundle is built
    around. Must run before GTK opens the first display.
    """
    if sys.platform != "win32":
        return
    gi.require_version("PangoCairo", "1.0")
    from gi.repository import PangoCairo

    fontmap = PangoCairo.FontMap.new_for_font_type(1)  # 1 = cairo FT backend
    fontmap.set_default()


def main(argv=None) -> None:
    _use_fontconfig_fontmap()
    folder = config.library_dir()
    if folder is not None:
        logs.point_at(folder)
    texts.use(config.language())
    app = KatipApp()
    try:
        app.run(argv if argv is not None else sys.argv)
    except Exception:
        logger.exception("Fatal")
