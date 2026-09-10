# Book Shelf — the library page: search, filters, cover grid.
# License: GPL-3.0-or-later (see LICENSE).

"""A wall of covers with a search bar and an advanced filter panel.

The grid is a GtkFlowBox; filters are read into a `core.filters.Filters`
whenever anything changes, and the grid is rebuilt from the filtered
result. Export writes the whole library, not the visible slice.
"""

from gi.repository import Gtk

from core import filters as flt
from core import tags as tg
from core.excel import EXPORT_DEFAULT_NAME, export_library
from core.reading import STATUSES, STATUS_ANY
from shared.texts import text

from ..widgets.book_card import BookCard
from ..dialogs.confirmation import alert, pick_save

SEARCH_FIELDS = ("all", "title", "authors", "isbn", "publishers")
SORTS = ("title", "rating", "year")
SIGNED = ("any", "yes", "no")
LENT = ("any", "home", "out")


class LibraryPage(Gtk.Box):
    """The page showing every book as a card."""

    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6, margin_all=12)
        self.window = window
        self._cards: dict[str, BookCard] = {}

        top = Gtk.Box(spacing=6)
        self.search = Gtk.SearchEntry(placeholder_text=text("search_hint"), hexpand=True)
        self.search.connect("search-changed", lambda _e: self.refresh())
        top.append(self.search)
        self.field = self._drop("search_in_%s", SEARCH_FIELDS, self.refresh)
        top.append(self.field)
        self.append(top)

        advanced = Gtk.Box(spacing=6, margin_top=6)
        self.advanced = Gtk.Revealer(child=advanced)
        self.toggle = Gtk.ToggleButton(label=text("advanced_search"))
        self.toggle.connect("toggled", lambda b: self.advanced.set_reveal_child(b.get_active()))
        self.rating = self._rating_drop()
        self.signed = self._drop("filter_signed_%s", SIGNED, self.refresh)
        self.lent = self._drop("filter_lent_%s", LENT, self.refresh)
        self.status = self._drop("filter_status_%s", [STATUS_ANY] + list(STATUSES), self.refresh)
        self.tag = Gtk.DropDown(model=Gtk.StringList.new([text("filter_tag_any")]))
        self.tag.connect("notify::selected", lambda d, _p: self.refresh())
        self.sort = self._drop("sort_by_%s", SORTS, self.refresh)
        self.direction = Gtk.ToggleButton(label=text("sort_ascending"))
        self.direction.connect("toggled", lambda b: (
            b.set_label(text("sort_descending") if b.get_active() else text("sort_ascending")),
            self.refresh()))
        clear = Gtk.Button(label=text("clear_filters"))
        clear.add_css_class("flat")
        clear.connect("clicked", lambda _b: self.clear_filters())
        export = Gtk.Button(label=text("export_button"))
        export.connect("clicked", self._export)
        for widget in (self.rating, self.signed, self.lent, self.status, self.tag,
                       self.sort, self.direction, clear, export):
            advanced.append(widget)
        header = Gtk.Box(spacing=6)
        header.append(self.toggle)
        header.append(Gtk.Box(hexpand=True))
        header.append(clear)
        header.append(export)
        self.append(header)
        self.append(self.advanced)

        self.count = Gtk.Label(xalign=0)
        self.count.add_css_class("dim-label")
        self.append(self.count)

        self.scroller = Gtk.ScrolledWindow(vexpand=True)
        self.flow = Gtk.FlowBox(
            valign=Gtk.Align.START, selection_mode=Gtk.SelectionMode.NONE,
            homogeneous=False, max_children_per_line=10, min_children_per_line=3,
        )
        self.flow.connect("child-activated", self._open)
        self.scroller.set_child(self.flow)
        self.append(self.scroller)
        self.refresh()

    # -- helpers -----------------------------------------------------------
    def _drop(self, key_pattern, values, on_change) -> Gtk.DropDown:
        model = Gtk.StringList.new(
            [text(key_pattern % v) if "%" in key_pattern else v for v in values]
        )
        drop = Gtk.DropDown(model=model)
        drop.connect("notify::selected", lambda d, _p: on_change())
        drop._values = values  # noqa: SLF001 - kept beside the widget
        return drop

    def _rating_drop(self) -> Gtk.DropDown:
        """Rating filter: 'any' plus '{n} stars or more', highest first."""
        values = ("any", "5", "4", "3", "2", "1")
        labels = [text("filter_rating_any")] + [
            text("filter_rating_min").format(n=k) for k in (5, 4, 3, 2, 1)
        ]
        drop = Gtk.DropDown(model=Gtk.StringList.new(labels))
        drop.connect("notify::selected", lambda d, _p: self.refresh())
        drop._values = values  # noqa: SLF001 - kept beside the widget
        return drop

    def _pick(self, drop: Gtk.DropDown):
        values = getattr(drop, "_values", None)
        return values[drop.get_selected()] if values else None

    def filters(self) -> flt.Filters:
        status = getattr(self.status, "_values", None)
        return flt.Filters(
            query=self.search.get_text(),
            search_field=self._pick(self.field) or "all",
            min_rating=int(self._pick(self.rating) or 0),
            signed=self._pick(self.signed),
            lent=self._pick(self.lent),
            status=(status[self.status.get_selected()] if status else STATUS_ANY),
            tag=self._pick(self.tag),
        )

    def refresh(self) -> None:
        """Re-read the model and rebuild the grid."""
        if not getattr(self, "window", None):
            return
        self._fill_tag_filter()
        books = flt.arrange(
            self._filtered(),
            self._pick(self.sort) or "title",
            self.direction.get_active(),
        )
        self.flow.remove_all()
        self._cards.clear()
        from services.cover_loader import THUMB_SIZE
        for book in books:
            card = BookCard(book, THUMB_SIZE)
            self._cards[book.key] = card
            self.flow.append(card)
            self.window.covers.request(
                book.key, book.isbn_13 or book.isbn_10, THUMB_SIZE, self._cover)
        self.count.set_text(self._count(len(books)))

    def _filtered(self) -> list:
        ledger = self.window.ledger
        return [b for b in self.window.library.rows
                if self.filters().allows(b, ledger.is_lent_out(b.key))]

    @staticmethod
    def _count(n: int) -> str:
        return text("book_count").format(n=n)

    def _cover(self, key: str, pixbuf) -> None:
        if pixbuf is not None and (card := self._cards.get(key)):
            card.set_cover(pixbuf)

    def _fill_tag_filter(self) -> None:
        chosen = self._pick(self.tag)
        model = Gtk.StringList.new([text("filter_tag_any")] + tg.tags_in_use(self.window.library.rows))
        self.tag.set_model(model)
        if chosen:
            position = next((i for i in range(model.get_n_items()) if model[i].get_string() == chosen), 0)
            self.tag.set_selected(position)

    def clear_filters(self) -> None:
        self.search.set_text("")
        for drop in (self.field, self.rating, self.signed, self.lent, self.status, self.tag, self.sort):
            drop.set_selected(0)
        self.direction.set_active(False)
        self.refresh()

    def _open(self, _flow, child) -> None:
        card = child.get_child()
        self.window.open_book(card.key)

    def _export(self, _button) -> None:
        def save(path):
            if export_library(self.window.library.rows, self.window.ledger, path):
                alert(self.get_root(), text("export_done_title"), text("export_done").format(path=path))
            else:
                alert(self.get_root(), text("export_failed_title"), text("export_failed"))
        pick_save(self.get_root(), save, EXPORT_DEFAULT_NAME)
