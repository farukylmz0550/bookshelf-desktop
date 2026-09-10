# Katip Celebi — the first-run welcome page.
# License: GPL-3.0-or-later (see LICENSE).

import gi

gi.require_version("Adw", "1")
from gi.repository import Gtk

from shared.texts import text


class WelcomePage(Gtk.Box):
    """A quiet greeting and one button onward."""

    def __init__(self, on_done):
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL, spacing=24,
            valign=Gtk.Align.CENTER, halign=Gtk.Align.CENTER, vexpand=True,
        )
        line = Gtk.Label(label=text("welcome_line"), wrap=True, justify=Gtk.Justification.CENTER)
        line.add_css_class("title-2")
        self.append(line)
        start = Gtk.Button(label=text("welcome_start"))
        start.add_css_class("suggested-action")
        start.add_css_class("pill")
        start.set_size_request(160, -1)
        start.connect("clicked", lambda _b: on_done())
        self.append(start)
