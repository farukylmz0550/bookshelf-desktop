# Katip Celebi — the lending panel: who has it, when it came back.
# License: GPL-3.0-or-later (see LICENSE).

"""Copy counts, the list of open loans, and the act of lending.

An editable dropdown names the borrower; a name nobody has lent to
before quietly becomes a person in the ledger. Each open loan carries
its own take-back button.
"""

import logging
from dataclasses import replace

from gi.repository import Gtk

from core.book import Book, MAX_COPIES
from core.ledger import Ledger
from core.person import now
from shared.texts import text

from ..dialogs.confirmation import toast

logger = logging.getLogger("katipcelebi")


class LendingPanel(Gtk.Box):
    """Everything about copies leaving and coming home."""

    def __init__(self, window, on_changed):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.window = window
        self.on_changed = on_changed
        self.key = ""

        copies_row = Gtk.Box(spacing=6)
        copies_row.append(Gtk.Label(label=text("field_copies"), xalign=0))
        self.copies = Gtk.SpinButton.new_with_range(1, MAX_COPIES, 1)
        self._copies_id = self.copies.connect("value-changed", self._save_copies)
        copies_row.append(self.copies)
        self.append(copies_row)

        self.sentence = Gtk.Label(xalign=0, wrap=True, css_classes=["dim-label"])
        self.append(self.sentence)

        self.loans_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.append(self.loans_box)

        lend_row = Gtk.Box(spacing=6)
        self.person = Gtk.ComboBoxText(has_entry=True)
        self.person.set_entry_text_column(0)
        lend_row.append(self.person)
        lend = Gtk.Button(label=text("lend"))
        lend.add_css_class("suggested-action")
        lend.connect("clicked", self._lend)
        lend_row.append(lend)
        self.append(lend_row)

    # -- refresh -----------------------------------------------------------
    def show(self, key: str) -> None:
        self.key = key
        self._fill_person_list()
        self.refresh()

    def _fill_person_list(self) -> None:
        self.person.remove_all()
        for person in self.window.ledger.people:
            self.person.append_text(person.name)

    def refresh(self) -> None:
        book = self.window.library.find(self.key)
        self._show_copies(book)
        self._show_loans(book)

    def _book_copies(self, book: Book | None) -> int:
        return book.copy_count if book else 1

    def _show_copies(self, book: Book | None) -> None:
        if book is None:
            return
        self.copies.handler_block_by_id(self._copies_id)
        self.copies.set_value(min(self._book_copies(book), MAX_COPIES))
        self.copies.handler_unblock_by_id(self._copies_id)

    def _show_loans(self, book: Book | None) -> None:
        if book is None:
            return
        for child in list(self.loans_box):
            self.loans_box.remove(child)
        out = self.window.ledger.open_loans_for(self.key)
        copies = self._book_copies(book)
        if not out:
            self.sentence.set_text(text("all_here").format(n=copies))
            return
        if out and len(out) == copies:
            self.sentence.set_text(text("all_out").format(n=copies))
        else:
            self.sentence.set_text(text("some_here").format(here=copies - len(out), n=copies))
        for loan in out:
            self.loans_box.append(self._loan_row(loan))

    def _loan_row(self, loan) -> Gtk.Widget:
        row = Gtk.Box(spacing=6)
        row.append(Gtk.Label(label=f"{loan.person_name} - {loan.lent_date}", xalign=0, hexpand=True))
        back = Gtk.Button(label=text("take_back"))
        back.connect("clicked", lambda _b, loan_id=loan.id: self._take_back(loan_id))
        row.append(back)
        return row

    # -- actions ------------------------------------------------------------
    def _save_copies(self, spin) -> None:
        book = self.window.library.find(self.key)
        if book is None:
            return
        out = self.window.ledger.out_count(self.key)
        if spin.get_value_as_int() < out:
            toast(self.window.overlay, text("copies_too_few").format(out=out))
            self.copies.set_value(max(out, 1))
            return
        if not self.window.library.replace(replace(book, copies=str(spin.get_value_as_int()))):
            return
        self.refresh()
        self.on_changed()

    def _lend(self, _button) -> None:
        book = self.window.library.find(self.key)
        entry = self.person.get_child() if self.person.has_entry else None
        raw = entry.get_text() if entry else ""
        if self.person.get_active_text():
            raw = self.person.get_active_text()
        if not raw or book is None:
            return
        ledger = self.window.ledger
        person = ledger.person_named(raw) or ledger.add_person(raw)
        if person is None or not ledger.lend(book, person):
            toast(self.window.overlay, text("lend_failed"))
            return
        self.show(self.key)
        self.on_changed()

    def _take_back(self, loan_id: str) -> None:
        self.window.ledger.take_back(loan_id)
        self.show(self.key)
        self.on_changed()
