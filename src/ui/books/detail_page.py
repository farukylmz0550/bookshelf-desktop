# Book Shelf — one book, in full.
# License: GPL-3.0-or-later (see LICENSE).

"""Detail page: big cover, three panels, and deletion.

Deleting respects copies and active loans: fewer copies than are out is
never allowed, and the whole book cannot go while someone still has it.
"""

import logging
from dataclasses import replace

from gi.repository import Gtk

from core.book import Book
from services.cover_loader import LARGE_SIZE
from shared.texts import text

from .facts_panel import FactsPanel
from .lending_panel import LendingPanel
from .personal_panel import PersonalPanel
from ..dialogs.confirmation import confirm, toast

logger = logging.getLogger("bookshelf")


class DetailPage(Gtk.Box):
    """Everything about one book, and the ways to change or lose it."""

    def __init__(self, window, key: str):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=16, margin_all=12)
        self.window = window
        self.key = key

        back = Gtk.Button(label=text("back"))
        back.add_css_class("flat")
        back.set_icon_name("go-previous-symbolic")
        back.connect("clicked", self._go_back)
        top = Gtk.Box(spacing=6)
        top.append(back)

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.picture = Gtk.Picture(
            content_fit=Gtk.ContentFit.COVER,
            width_request=LARGE_SIZE[0], height_request=LARGE_SIZE[1],
        )
        left.append(self.picture)
        delete = Gtk.Button(label=text("delete_book"))
        delete.add_css_class("destructive-action")
        delete.connect("clicked", lambda _b: self._delete())
        left.append(delete)
        self.append(left)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16, vexpand=True)
        right.append(top)
        self.facts = FactsPanel(window, self._facts_changed)
        self.personal = PersonalPanel(window, self._panel_changed)
        self.lending = LendingPanel(window, self._panel_changed)
        for panel in (self.facts, self.personal, self.lending):
            right.append(panel)
        scroller = Gtk.ScrolledWindow(vexpand=True)
        scroller.set_child(right)
        self.append(scroller)

        self.personal.show(key)
        self.lending.show(key)
        self.facts.show(key)
        self._load_cover()

    # -- cover ---------------------------------------------------------------
    def _load_cover(self) -> None:
        book = self.window.library.find(self.key)
        if book is None:
            return
        self.window.covers.request(
            book.key, book.isbn_13 or book.isbn_10, LARGE_SIZE, self._on_cover)

    def _on_cover(self, key: str, pixbuf) -> None:
        if key == self.key and pixbuf is not None:
            self.picture.set_paintable(Gtk.Texture.new_for_pixbuf(pixbuf))

    # -- panels ----------------------------------------------------------------
    def _panel_changed(self) -> None:
        self.window.books_changed()

    def _facts_changed(self) -> None:
        self.facts.show(self.key)
        self._panel_changed()

    # -- deletion -------------------------------------------------------------
    def _go_back(self, _button) -> None:
        from gi.repository import Adw
        ancestor = self.get_ancestor(Adw.NavigationView)
        if ancestor is not None:
            ancestor.pop()

    def _delete(self, _button) -> None:
        book = self.window.library.find(self.key)
        if book is None:
            return
        out = self.window.ledger.out_count(self.key)
        copies = book.copy_count
        if out >= copies:
            toast(self.window.overlay, text("delete_while_out"))
            return
        if copies > 1:
            self._delete_some(book, copies, out)
            return

        def on_ok():
            if self.window.library.remove(self.key):
                self._finish_delete()
        confirm(self.get_root(), text("delete_title"),
                text("delete_confirm").format(title=book.title), on_ok, text("delete_book"))

    def _delete_some(self, book: Book, copies: int, out: int) -> None:
        window = self.get_root()
        from gi.repository import Adw
        chooser = Adw.AlertDialog(
            heading=text("delete_title"),
            body=text("delete_which").format(title=book.title, copies=copies, out=out),
        )
        chooser.add_response("cancel", text("close"))
        if out < copies:
            chooser.add_response("one", text("delete_one_copy"))
        chooser.add_response("all", text("delete_all_copies"))
        chooser.choose(window, None, lambda d, r: self._which(d.choose_finish(r), book), None)

    def _which(self, answer: str, book: Book) -> None:
        if answer == "one":
            wanted = replace(book, copies=str(book.copy_count - 1))
            if self.window.library.replace(wanted):
                self._finish_delete()
        elif answer == "all":
            if self.window.library.remove(self.key):
                self._finish_delete()

    def _finish_delete(self) -> None:
        self.window.covers.forget(self.key)
        self.window.books_changed()
        from gi.repository import Adw
        ancestor = self.get_ancestor(Adw.NavigationView)
        if ancestor is not None:
            ancestor.pop()
