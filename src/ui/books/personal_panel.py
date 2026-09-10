# Book Shelf — the personal panel: rating, reading, tags, notes.
# License: GPL-3.0-or-later (see LICENSE).

"""Everything about this book and me, not about the work itself.

Every change is written through immediately; a failed save restores the
previous value so the page never lies about what is on disk.
"""

import logging
from dataclasses import replace

from gi.repository import Gtk

from core import reading, tags as tg
from core.book import Book
from core.store import Library
from shared.texts import text

from ..widgets.star_rating import StarRating

logger = logging.getLogger("bookshelf")

MEANS_YES = ("yes", "true", "1", "evet")


class PersonalPanel(Gtk.Box):
    """Rating, reading progress, tags and notes for one book."""

    def __init__(self, window, on_changed):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.window = window
        self.library: Library = window.library
        self.on_changed = on_changed
        self.key = ""

        self.stars = StarRating(editable=True, on_change=lambda v: self._save("rating", str(v)))
        self.append(self.stars)

        self.signed = Gtk.CheckButton(label=text("field_signed"))
        self.signed.connect("toggled", self._signed_changed)
        self.append(self.signed)

        self.status_combo = Gtk.DropDown(model=Gtk.StringList.new(
            [text(f"status_{s}") for s in reading.STATUSES]))
        self.status_combo.connect("notify::selected", self._status_changed)
        self.append(self.status_combo)

        self.step_button = Gtk.Button()
        self.step_button.add_css_class("flat")
        self.step_button.connect("clicked", self._reading_step)
        self.append(self.step_button)

        self.tags_entry = Gtk.Entry(placeholder_text=text("tags_hint"))
        self.tags_entry.connect("changed", self._tags_changed)
        self.append(self.tags_entry)

        self.notes = Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD_CHAR, height_request=100)
        self.notes.get_buffer().connect("changed", lambda _b: self._notes_changed())
        self.append(self.notes)

        self.preview = Gtk.Label(xalign=0, wrap=True, css_classes=["dim-label"])
        self.append(self.preview)

    # -- book access ---------------------------------------------------------
    def show(self, key: str) -> None:
        self.key = key
        book = self.library.find(key)
        self._refresh(book, replay=False)

    def _refresh(self, book: Book | None, replay: bool = True) -> None:
        if book is None:
            return
        self.stars.set_rating(int(book.rating or 0))
        self.signed.set_active(book.signed.strip().lower() in MEANS_YES)
        self.status_combo.set_selected(reading.STATUSES.index(reading.status_of(book)))
        self.step_button.set_label(text(reading.next_step(book)))
        if not replay:
            self.tags_entry.set_text(tg.show(book.tags))
            self.notes.get_buffer().set_text(book.notes or "")
        self.preview.set_text(book.notes or text("notes_preview"))

    # -- change handlers -------------------------------------------------------
    def _save(self, field: str, value) -> None:
        book = self.library.find(self.key)
        if book is None:
            return
        old = getattr(book, field)
        updated = self.library.replace(replace(book, **{field: value}))
        if not updated:
            self._refresh(book, replay=False)
            return
        self.on_changed()

    def _signed_changed(self, button) -> None:
        self._save("signed", "yes" if button.get_active() else "")

    def _status_changed(self, combo, _param) -> None:
        self._save("status", reading.STATUSES[combo.get_selected()])

    def _reading_step(self, _button) -> None:
        book = self.library.find(self.key)
        if book is None:
            return
        step = reading.next_step(book)
        updated = reading.start_reading(book) if step == "reading_start" else reading.finish_reading(book)
        if self.library.replace(updated):
            self.show(self.key)
            self.on_changed()

    def _tags_changed(self, entry) -> None:
        self._save("tags", tg.store(entry.get_text()))

    def _notes_changed(self) -> None:
        buffer = self.notes.get_buffer()
        body = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
        self.preview.set_text(body or text("notes_preview"))
        self._save("notes", body)
