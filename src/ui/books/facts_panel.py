# Katip Celebi — the catalogue facts panel.
# License: GPL-3.0-or-later (see LICENSE).

"""Read-only display of a book's catalogue data, with an edit mode.

`title` leads the editable fields: it is the one most worth fixing. The
panel never rewrites `key`, which is the book's identity, not its data.
"""

from dataclasses import replace

from gi.repository import Gtk

from core.book import Book
from core.store import Library
from shared.texts import field_label, text

SHOWN = (
    "subtitle", "authors", "publishers", "publish_date", "publish_places",
    "edition_name", "series", "number_of_pages", "languages",
    "isbn_10", "isbn_13", "subjects",
)
EDITABLE = ("title",) + SHOWN


class FactsPanel(Gtk.Box):
    """What the catalogue says, and the means to correct it."""

    def __init__(self, window, on_changed):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.window = window
        self.library: Library = window.library
        self.on_changed = on_changed
        self.key = ""
        self._editor = None

        self.heading = Gtk.Label(xalign=0, wrap=True)
        self.heading.add_css_class("title-2")
        self.append(self.heading)

        self.rows: dict[str, Gtk.Label] = {}
        self.read_view = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        for field in SHOWN:
            self.read_view.append(self._read_row(field))
        self.append(self.read_view)

        edit_bar = Gtk.Box(spacing=6)
        self.edit_button = Gtk.Button(label=text("facts_edit"))
        self.edit_button.connect("clicked", self._start_editing)
        edit_bar.append(self.edit_button)
        self.append(edit_bar)

        self.edit_view = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.editors: dict[str, Gtk.Entry] = {}
        for field in EDITABLE:
            self.edit_view.append(self._edit_row(field))
        buttons = Gtk.Box(spacing=6, halign=Gtk.Align.END)
        cancel = Gtk.Button(label=text("close"))
        cancel.add_css_class("flat")
        cancel.connect("clicked", lambda _b: self._stop_editing())
        save = Gtk.Button(label=text("save"))
        save.add_css_class("suggested-action")
        save.connect("clicked", lambda _b: self._save())
        buttons.append(cancel)
        buttons.append(save)
        self.edit_view.append(buttons)
        self.edit_view.set_visible(False)
        self.append(self.edit_view)

    # -- reading view ------------------------------------------------------
    def show(self, key: str) -> None:
        self.key = key
        book = self.library.find(key)
        self.heading.set_text(book.title if book else "")
        for field, value_label in self.rows.items():
            value_label.set_text(getattr(book, field, "") if book else "")
        self._stop_editing()

    def _read_row(self, field: str) -> Gtk.Widget:
        row = Gtk.Box(spacing=8)
        label = Gtk.Label(label=field_label(field), xalign=0, width_request=140)
        label.add_css_class("dim-label")
        value = Gtk.Label(xalign=0, wrap=True, hexpand=True)
        row.append(label)
        row.append(value)
        self.rows[field] = value
        return row

    # -- editing -----------------------------------------------------------
    def _start_editing(self, _button) -> None:
        book = self.library.find(self.key)
        if book is None:
            return
        self.heading.set_text(book.title)
        for field, entry in self.editors.items():
            entry.set_text(getattr(book, field, ""))
        self.read_view.set_visible(False)
        self.edit_view.set_visible(True)

    def _edit_row(self, field: str) -> Gtk.Widget:
        row = Gtk.Box(spacing=8)
        label = Gtk.Label(label=field_label(field), xalign=0, width_request=140)
        entry = Gtk.Entry(hexpand=True)
        row.append(label)
        row.append(entry)
        self.editors[field] = entry
        return row

    def _stop_editing(self) -> None:
        self.edit_view.set_visible(False)
        self.read_view.set_visible(True)

    def _save(self) -> None:
        book = self.library.find(self.key)
        if book is None:
            return
        changes = {field: entry.get_text() for field, entry in self.editors.items()}
        if not changes.get("title", book.title).strip():
            return
        self.library.replace(replace(book, **changes))
        self.show(self.key)
        self._stop_editing()
        self.on_changed()
