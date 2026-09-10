# Katip Celebi — off-thread work dispatch.
# License: GPL-3.0-or-later (see LICENSE).

"""Run a callable in a thread and deliver its result on the main loop.

UI stays responsive while network and disk work happens; results arrive
through `GLib.idle_add`, so callbacks may touch widgets safely.
"""

import logging
import threading

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import GLib

logger = logging.getLogger("katipcelebi")


def run(work, on_done) -> None:
    """Call `work()` in a thread, then `on_done(result)` on the main loop."""
    def thread_body():
        try:
            result = work()
        except Exception:
            logger.exception("Background work failed")
            result = None
        GLib.idle_add(on_done, result)
    threading.Thread(target=thread_body, daemon=True).start()
