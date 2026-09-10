# Book Shelf — the people page.
# License: GPL-3.0-or-later (see LICENSE).

"""A table of borrowers and the loan history of whoever is selected.

Rows are tiny `GObject.Object` wrappers so the column factories can
bind straight to their cell values; the wrapper keeps the `Person`, so
selection never needs row indices.
"""

import gi

gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GObject, Gtk

from core.person import Person
from shared.texts import text

from .dialogs.confirmation import alert, toast


class Row(GObject.Object):
    """One table row: plain cell strings plus the item they came from."""

    def __init__(self, cells: tuple[str, ...], item=None):
        super().__init__()
        self.cells = cells
        self.item = item

    def __getitem__(self, index: int) -> str:
        return self.cells[index]


def make_column(title: str, index: int, expand: bool = False) -> Gtk.ColumnViewColumn:
    """One column bound to cell `index` of a `Row`."""
    factory = Gtk.SignalListItemFactory()
    factory.connect("setup", lambda _f, li: li.set_child(Gtk.Label(xalign=0)))
    factory.connect("bind", _bind, index)
    column = Gtk.ColumnViewColumn(title=text(title), factory=factory)
    column.set_expand(expand)
    return column


def _bind(_factory, list_item, index: int) -> None:
    list_item.get_child().set_text(list_item.get_item()[index])


def table(*titles) -> Gtk.ColumnView:
    """A column view with one column per title, returning it and its model."""
    model = Gio.ListStore.new(Row)
    view = Gtk.ColumnView(model=Gtk.SingleSelection.new(model))
    for i, title in enumerate(titles):
        view.append_column(make_column(title, i, expand=i == 0))
    return view


class PeoplePage(Gtk.Box):
    """Who you lend to, what they have, and what they bring back."""

    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8, margin_all=12)
        self.window = window

        add_row = Gtk.Box(spacing=6)
        self.name_entry = Gtk.Entry(placeholder_text=text("person_name_hint"), hexpand=True)
        self.name_entry.connect("activate", lambda _e: self.add_person())
        add_row.append(self.name_entry)
        add_button = Gtk.Button(label=text("person_add"))
        add_button.add_css_class("suggested-action")
        add_button.connect("clicked", lambda _b: self.add_person())
        add_row.append(add_button)
        remove_button = Gtk.Button(label=text("person_remove"))
        remove_button.connect("clicked", lambda _b: self.remove_person())
        add_row.append(remove_button)
        self.append(add_row)

        self.count = Gtk.Label(xalign=0, css_classes=["dim-label"])
        self.append(self.count)

        self.table = table("col_person", "col_trust", "col_returned", "col_out")
        self.people_model = self.table.get_model().get_model()
        scroller = Gtk.ScrolledWindow(vexpand=True, height_request=260)
        scroller.set_child(self.table)
        self.append(scroller)

        self.history_heading = Gtk.Label(xalign=0, wrap=True, css_classes=["heading"])
        self.append(self.history_heading)
        self.history = table("col_book", "col_lent", "col_returned_on")
        self.history_model = self.history.get_model().get_model()
        history_scroller = Gtk.ScrolledWindow(vexpand=True)
        history_scroller.set_child(self.history)
        self.append(history_scroller)

        selection = self.table.get_model()
        selection.connect("selection-changed", lambda _m, _p, _n: self._show_history())
        self.refresh()

    # -- refresh ---------------------------------------------------------------
    def refresh(self) -> None:
        ledger = self.window.ledger
        self.people_model.remove_all()
        for person in ledger.people:
            self.people_model.append(Row((
                person.name,
                str(ledger.trust_score(person.id)),
                str(pm.returned_count(ledger.loans, person.id)),
                str(len(pm.books_out_with(ledger.loans, person.id))),
            ), person))
        self.count.set_text(text("people_count").format(n=len(ledger.people)))
        self._show_history()

    def selected_person(self) -> Person | None:
        row = self.table.get_model().get_selected_item()
        return row.item if row is not None else None

    # -- actions ---------------------------------------------------------------
    def add_person(self) -> None:
        person = self.window.ledger.add_person(self.name_entry.get_text())
        if person is None:
            name = self.name_entry.get_text().strip()
            if not name:
                toast(self.window.overlay, text("person_needs_name"))
            elif self.window.ledger.person_named(name):
                toast(self.window.overlay, text("person_already_known"))
            return
        self.name_entry.set_text("")
        toast(self.window.overlay, text("person_added").format(name=person.name))
        self.refresh()

    def remove_person(self) -> None:
        person = self.selected_person()
        if person is None:
            toast(self.window.overlay, text("person_pick_first"))
            return
        ledger = self.window.ledger
        if ledger.books_out_with(person.id):
            alert(self.get_root(), text("person_still_has_books_title"),
                  text("person_still_has_books").format(name=person.name))
            return

        def on_ok():
            if ledger.remove_person(person.id):
                toast(self.window.overlay, text("person_removed").format(name=person.name))
            self.refresh()
        alert(self.get_root(), text("person_remove_title"),
              text("person_remove_confirm").format(name=person.name), on_ok, text("person_remove"))

    def _show_history(self) -> None:
        person = self.selected_person()
        if person is None:
            self.history_heading.set_text("")
            self.history_model.remove_all()
            return
        ledger = self.window.ledger
        loans = ledger.loans_of(person.id)
        self.history_heading.set_text(text("history_of").format(name=person.name))
        self.history_model.remove_all()
        for loan in loans:
            returned = loan.return_date or text("still_out")
            self.history_model.append(Row((loan.book_title, loan.lent_date, returned)))
