# Book Shelf — clickable five-star rating.
# License: GPL-3.0-or-later (see LICENSE).

"""A row of five stars drawn with text, lit up to the current rating.

Clicks set the rating, clicking the lit value again clears it. Read-only
instances are used on book cards.
"""

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk


class StarRating(Gtk.Box):
    """Five star glyphs and, optionally, mouse handling."""

    def __init__(self, rating: int = 0, editable: bool = False, on_change=None):
        super().__init__()
        self._rating, self._hover, self._editable = rating, 0, editable
        self.on_change = on_change
        self._label = Gtk.Label(label=self._glyphs())
        self._label.add_css_class("stars")
        self.append(self._label)
        if editable:
            click = Gtk.GestureClick()
            click.connect("released", self._clicked)
            self.add_controller(click)
            motion = Gtk.EventControllerMotion()
            motion.connect("enter", lambda _m, x, _y: self._preview(x))
            motion.connect("leave", lambda _m: self._preview(-1))
            self.add_controller(motion)

    # -- state -----------------------------------------------------------
    def rating(self) -> int:
        return self._rating

    def set_rating(self, value: int, emit: bool = False) -> None:
        self._rating = max(0, min(5, int(value)))
        self._label.set_text(self._glyphs())
        if emit and self.on_change:
            self.on_change(self._rating)

    def _glyphs(self) -> str:
        shown = self._hover if self._hover else self._rating
        return "\u2605" * shown + "\u2606" * (5 - shown)

    # -- input -------------------------------------------------------------
    def _clicked(self, gesture, _n, x, _y) -> None:
        value = round(x / self._label.get_allocated_width() * 5)
        value = 0 if value == self._rating else max(1, min(5, value))
        self.set_rating(value, emit=True)

    def _preview(self, x) -> None:
        self._hover = max(1, min(5, round(x / max(self._label.get_allocated_width(), 1) * 5))) if x >= 0 else 0
        self._label.set_text(self._glyphs())
