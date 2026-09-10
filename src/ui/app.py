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

APP_ID = "io.github.farukylmz0550.BookShelfLegacy"
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


def main(argv=None) -> None:
    folder = config.library_dir()
    if folder is not None:
        logs.point_at(folder)
    texts.use(config.language())
    app = KatipApp()
    try:
        app.run(argv if argv is not None else sys.argv)
    except Exception:
        logger.exception("Fatal")
