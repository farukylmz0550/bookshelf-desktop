# Book Shelf — one book in the wall of covers.
# License: GPL-3.0-or-later (see LICENSE).

"""A compact card: cover picture on top, one caption line, badges.

Clicks are handled by the GtkFlowBox that owns the card; the card itself
stays a dumb display. `refresh()` re-reads the book after an edit.
"""

from gi.repository import Gdk, GdkPixbuf, Gtk

from core import reading
from core.book import Book
from shared.texts import text

from .star_rating import StarRating


class BookCard(Gtk.Box):
    """Everything a cover grid cell needs."""

    def __init__(self, book: Book, thumb):
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL, spacing=6,
            margin_top=6, margin_bottom=6, margin_start=6, margin_end=6,
        )
        self.key = book.key
        self.picture = Gtk.Picture(
            content_fit=Gdk.ContentFit.COVER, width_request=thumb[0], height_request=thumb[1],
        )
        self.picture.add_css_class("card-cover")
        self.append(self.picture)
        self.badges = Gtk.Label(xalign=0)
        self.badges.add_css_class("caption")
        self.badges.add_css_class("dim-label")
        self.append(self.badges)
        self.caption = Gtk.Label(xalign=0, ellipsize=3, single_line_mode=True)
        self.caption.add_css_class("caption")
        self.append(self.caption)
        self.stars = StarRating()
        self.append(self.stars)
        self.refresh(book)

    def refresh(self, book: Book) -> None:
        """Re-read the book's caption, badges and rating."""
        self.caption.set_text(self._caption(book))
        self.stars.set_rating(int(book.rating or 0))
        self.badges.set_text(self._badges(book))
        self.badges.set_visible(bool(self._badges(book)))

    @staticmethod
    def _caption(book: Book) -> str:
        title = book.title or text("no_results")
        return f"{book.authors} - {title}" if book.authors else title

    @staticmethod
    def _badges(book: Book) -> str:
        badges = []
        status = reading.status_of(book)
        if status != reading.NOT_READ:
            badges.append(text(f"status_{status}"))
        if book.signed and book.signed.strip() in ("yes", "true", "1", "evet"):
            badges.append(text("field_signed"))
        return " · ".join(badges)

    def set_cover(self, pixbuf: GdkPixbuf.Pixbuf | None) -> None:
        if pixbuf is not None:
            self.picture.set_paintable(Gdk.Texture.new_for_pixbuf(pixbuf))
