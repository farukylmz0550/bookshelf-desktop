# Book Shelf — the add-book page.
# License: GPL-3.0-or-later (see LICENSE).

"""Look a book up by ISBN, check it over, keep it.

The form lists the catalogue fields in three groups; the personal block
covers rating, status, tags and notes. Bulk import reads ISBNs from an
Excel sheet and fetches each one, with a small delay to stay polite to
Open Library. Books Open Library has never heard of may be contributed,
with credentials kept in the OS keyring when allowed.
"""

import logging
import time

from gi.repository import Adw, Gtk

from core import tags as tg
from core.book import Book, check_isbn, normalize_isbn
from core.excel import FileTooLarge, read_template, write_template
from core.reading import STATUSES
from services.openlibrary import (SUBMIT_DENIED, SUBMIT_FAILED, SUBMIT_LOGIN,
                                  SUBMIT_NETWORK, SUBMIT_OK, fetch_book, submit_book)
from shared import credentials
from shared.texts import field_label, text

from ..dialogs.confirmation import alert, pick_open, pick_save
from ..work import run
from ..widgets.star_rating import StarRating

logger = logging.getLogger("bookshelf")

SECTIONS = (
    ("section_basic", ("title", "subtitle", "authors", "publishers",
                       "publish_date", "publish_places", "edition_name", "series")),
    ("section_physical", ("number_of_pages", "languages", "isbn_10", "isbn_13")),
    ("section_content", ("subjects",)),
)

MEANS_YES = {"yes", "true", "1", "evet"}


class AddPage(Gtk.Box):
    """Fetch a record, review it, and file it on the shelf."""

    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_all=12)
        self.window = window
        self.stars = StarRating()

        isbn_row = Gtk.Box(spacing=6)
        isbn_row.append(Gtk.Label(label=text("isbn_label"), xalign=0))
        self.isbn_entry = Gtk.Entry(placeholder_text=text("isbn_hint"), hexpand=True)
        self.isbn_entry.connect("activate", lambda _e: self.look_up())
        isbn_row.append(self.isbn_entry)
        fetch = Gtk.Button(label=text("fetch"))
        fetch.connect("clicked", lambda _b: self.look_up())
        isbn_row.append(fetch)
        self.append(isbn_row)

        bulk_row = Gtk.Box(spacing=6)
        template = Gtk.Button(label=text("template_button"))
        template.connect("clicked", self.save_template)
        bulk_row.append(template)
        importing = Gtk.Button(label=text("import_button"))
        importing.connect("clicked", self.import_list)
        bulk_row.append(importing)
        self.append(bulk_row)

        self.status = Gtk.Label(xalign=0, wrap=True)
        self.status.add_css_class("dim-label")
        self.append(self.status)

        scroller = Gtk.ScrolledWindow(vexpand=True)
        form = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.fields: dict[str, Gtk.Entry] = {}
        for heading, names in SECTIONS:
            form.append(self._heading(text(heading)))
            for field in names:
                form.append(self._field(field_label(field), field))
        form.append(self._heading(text("section_personal")))
        form.append(self._personal())
        form.append(self._heading(text("field_notes")))
        self.notes = Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD_CHAR, height_request=80)
        self.notes.get_buffer().connect("changed", self._preview_notes)
        frame = Gtk.Frame(child=self.notes)
        form.append(frame)
        self.preview = Gtk.Label(xalign=0, wrap=True, css_classes=["dim-label"])
        form.append(self.preview)

        buttons = Gtk.Box(spacing=6, halign=Gtk.Align.END)
        clear = Gtk.Button(label=text("clear"))
        clear.add_css_class("flat")
        clear.connect("clicked", lambda _b: self.clear_form())
        save = Gtk.Button(label=text("save"))
        save.add_css_class("suggested-action")
        save.connect("clicked", lambda _b: self.save_book())
        buttons.append(clear)
        buttons.append(save)
        form.append(buttons)

        scroller.set_child(form)
        self.append(scroller)
        self.refresh_tags()

    # -- widgets -----------------------------------------------------------
    @staticmethod
    def _heading(label: str) -> Gtk.Label:
        heading = Gtk.Label(label=label, xalign=0)
        heading.add_css_class("heading")
        return heading

    def _field(self, label: str, field: str) -> Gtk.Entry:
        row = Gtk.Box(spacing=6)
        row.append(Gtk.Label(label=label, xalign=0, width_request=130))
        entry = Gtk.Entry(hexpand=True)
        row.append(entry)
        self.fields[field] = entry
        return row

    def _personal(self) -> Gtk.Widget:
        personal = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        rating_row = Gtk.Box(spacing=6)
        rating_row.append(Gtk.Label(label=text("field_rating"), xalign=0, width_request=150))
        personal.append(rating_row)
        personal.append(self.stars)
        status_row = Gtk.Box(spacing=6)
        status_row.append(Gtk.Label(label=text("field_status"), xalign=0, width_request=150))
        self.status_combo = Gtk.DropDown(model=Gtk.StringList.new(
            [text(f"status_{s}") for s in STATUSES]))
        status_row.append(self.status_combo)
        personal.append(status_row)
        self.signed = Gtk.CheckButton(label=text("field_signed"))
        personal.append(self.signed)
        self.tags_entry = Gtk.Entry(placeholder_text=text("tags_hint"))
        personal.append(self.tags_entry)
        self.tags_pick = Gtk.DropDown(model=Gtk.StringList.new([text("tags_pick")]))
        self.tags_pick.connect("notify::selected", self._add_picked_tag)
        personal.append(self.tags_pick)
        return personal

    def refresh_tags(self) -> None:
        """Reload the suggestion list from the library."""
        options = tg.suggestions(self.window.library.rows)
        self.tags_pick.set_model(Gtk.StringList.new([text("tags_pick")] + options))

    def _add_picked_tag(self, drop, _param) -> None:
        picked = drop.get_model()[drop.get_selected()].dup()
        drop.set_selected(0)
        if picked == text("tags_pick") or not picked:
            return
        current = self.tags_entry.get_text()
        if tg.display(picked) not in tg.split_tags(current):
            self.tags_entry.set_text(tg.store(f"{current} {tg.display(picked)}" if current else tg.display(picked)))

    def _preview_notes(self, _buffer=None) -> None:
        body = self.notes.get_buffer().get_text(self.notes.get_buffer().get_start_iter(),
                                                self.notes.get_buffer().get_end_iter(), False)
        self.preview.set_text(body or text("notes_preview"))

    # -- lookup ------------------------------------------------------------
    def look_up(self) -> None:
        raw = normalize_isbn(self.isbn_entry.get_text())
        complaint = check_isbn(raw)
        if raw and complaint:
            self._say(alert, text("isbn_invalid_title"), complaint)
            return
        self.status.set_text(text("fetching"))
        run(lambda: fetch_book(raw), self._lookup_done)

    def _lookup_done(self, book) -> None:
        if book is None:
            self.status.set_text(text("fetch_not_found"))
            self._not_found_isbn = normalize_isbn(self.isbn_entry.get_text())
            return
        self.status.set_text(text("fetch_ok"))
        self.fill(book)

    def fill(self, book: Book) -> None:
        """Write a fetched book into the form, keeping the user's tags."""
        self.fields["title"].set_text(book.title)
        for field in ("subtitle", "authors", "publishers", "publish_date", "publish_places",
                      "edition_name", "series", "number_of_pages", "languages",
                      "isbn_10", "isbn_13", "subjects"):
            self.fields[field].set_text(getattr(book, field, ""))
        typed = tg.split_tags(tg.store(self.tags_entry.get_text()))
        found = tg.split_tags(book.tags)
        merged = typed + [t for t in found if t not in typed]
        self.tags_entry.set_text(tg.show(", ".join(merged)))
        self.stars.set_rating(0)
        self.signed.set_active(False)
        self.notes.get_buffer().set_text(book.notes or "")
        self.refresh_tags()

    def clear_form(self) -> None:
        self.isbn_entry.set_text("")
        for entry in self.fields.values():
            entry.set_text("")
        self.stars.set_rating(0)
        self.status_combo.set_selected(0)
        self.signed.set_active(False)
        self.tags_entry.set_text("")
        self.notes.get_buffer().set_text("")
        self.status.set_text("")

    def _say(self, title: str, message: str) -> None:
        alert(self.get_root(), title, message)

    def _complain(self, complaint: str) -> None:
        alert(self.get_root(), text("isbn_invalid_title"), complaint)

    # -- bulk --------------------------------------------------------------
    def save_template(self, _button) -> None:
        def save(path):
            ok = write_template(path)
            self.status.set_text(text("template_done" if ok else "template_failed"))
        pick_save(self.get_root(), save, "isbn_list.xlsx")

    def import_list(self, _button) -> None:
        def open(path):
            try:
                isbns = read_template(path)
            except FileTooLarge:
                self._say(text("import_too_large_title"), text("import_too_large"))
                return
            if isbns is None:
                self._say(text("import_unreadable_title"), text("import_unreadable"))
                return
            if not isbns:
                self._say(text("import_none_title"), text("import_none"))
                return
            self.status.set_text(text("importing").format(n=len(isbns)))
            run(lambda: self._fetch_all(isbns), self._import_done)
        pick_open(self.get_root(), open, "isbn_list.xlsx")

    @staticmethod
    def _fetch_all(isbns):
        found, missing = [], []
        misses = 0
        for isbn in isbns:
            book = fetch_book(isbn)
            if book is not None:
                found.append(book)
                misses = 0
            else:
                missing.append(isbn)
                misses += 1
                if misses >= 3:
                    break
            time.sleep(0.2)
        return found, missing, bool(misses >= 3)

    def _import_done(self, result) -> None:
        if result is None:
            self._say(text("import_network_error_title"), text("import_network_error"))
            return
        found, missing, network = result
        added = duplicates = 0
        for book in found:
            if self.window.library.add(book):
                added += 1
            else:
                duplicates += 1
        self.window.books_changed()
        self.refresh_tags()
        self.status.set_text(text("import_done").format(added=added, duplicates=duplicates))
        if missing:
            self._say(text("import_not_found"), "\n".join(missing[:20]))

    # -- save ---------------------------------------------------------------
    def save_book(self) -> None:
        book = self._form_book()
        if not book.title.strip():
            self.status.set_text(text("title_required"))
            return
        isbn = normalize_isbn(book.isbn_13 or book.isbn_10)
        if isbn and (complaint := check_isbn(isbn)):
            self._complain(complaint)
            return
        if not self.window.library.add(book):
            self._one_more_copy(book)
            return
        self.window.books_changed()
        offered = getattr(self, "_not_found_isbn", "") == book.key and not book.is_local_key
        self.clear_form()
        self.status.set_text(text("saved"))
        if offered:
            self._not_found_isbn = ""
            self._offer_submission(book)

    def _form_book(self) -> Book:
        selected = STATUSES[self.status_combo.get_selected()]
        return Book(
            key=Book.new_local_key(),
            title=self.fields["title"].get_text(),
            subtitle=self.fields["subtitle"].get_text(),
            authors=self.fields["authors"].get_text(),
            publishers=self.fields["publishers"].get_text(),
            publish_date=self.fields["publish_date"].get_text(),
            publish_places=self.fields["publish_places"].get_text(),
            edition_name=self.fields["edition_name"].get_text(),
            series=self.fields["series"].get_text(),
            number_of_pages=self.fields["number_of_pages"].get_text(),
            languages=self.fields["languages"].get_text(),
            isbn_10=self.fields["isbn_10"].get_text(),
            isbn_13=self.fields["isbn_13"].get_text(),
            subjects=self.fields["subjects"].get_text(),
            rating=str(self.stars.rating()),
            status=selected,
            tags=tg.store(self.tags_entry.get_text()),
            signed="yes" if self.signed.get_active() else "",
            notes=self._notes_text(),
        )

    def _notes_text(self) -> str:
        buffer = self.notes.get_buffer()
        return buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)

    def _one_more_copy(self, book: Book) -> None:
        """Same ISBN twice is one book, twice -- not two books."""
        from dataclasses import replace
        from core.book import MAX_COPIES
        existing = next(b for b in self.window.library.rows
                        if (b.isbn_13 or b.isbn_10) == (book.isbn_13 or book.isbn_10))
        wanted = replace(existing, copies=str(min(existing.copy_count + 1, MAX_COPIES)))
        if not self.window.library.replace(wanted):
            self._say(text("save_failed_title"), text("save_failed").format(path=self.window.library.path))
            return
        self.window.books_changed()
        self.clear_form()
        self._say(text("copies_added_title"),
                  text("copies_added").format(title=existing.title, n=wanted.copy_count))

    # -- Open Library contribution ------------------------------------------
    def _offer_submission(self, book: Book) -> None:
        self._book_to_send = book
        dialog = Adw.AlertDialog(heading=text("ol_offer_title"), body=text("ol_offer"))
        dialog.add_response("no", "No")
        dialog.add_response("yes", "Yes")
        dialog.set_response_appearance("yes", Adw.ResponseAppearance.SUGGESTED)
        dialog.choose(self.get_root(), None,
                      lambda d, r: self._ask_to_sign_in() if d.choose_finish(r) == "yes" else None, None)

    def _ask_to_sign_in(self) -> None:
        saved = credentials.load() if credentials.can_remember() else None
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self._username = Gtk.Entry(placeholder_text=text("ol_username"),
                                   text=saved.get("username", "") if saved else "")
        self._password = Gtk.PasswordEntry(placeholder_text=text("ol_password"))
        self._remember = Gtk.CheckButton(label=text("ol_remember"), active=bool(saved))
        for widget in (self._username, self._password, self._remember):
            box.append(widget)
        dialog = Adw.AlertDialog(heading=text("ol_signin_title"))
        dialog.set_extra_child(box)
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("ok", "OK")
        dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)
        dialog.choose(self.get_root(), None, self._do_sign_in, None)

    def _do_sign_in(self, dialog, result) -> None:
        if dialog.choose_finish(result) != "ok":
            return
        user, passw = self._username.get_text(), self._password.get_text()
        if self._remember.get_active() and credentials.can_remember():
            credentials.save(user, passw)
        self.status.set_text(text("ol_sending"))
        run(lambda: submit_book(self._book_to_send, user, passw), self._submission_done)

    def _submission_done(self, outcome: str) -> None:
        outcomes = {
            SUBMIT_OK: ("ol_thanks_title", "ol_thanks"),
            SUBMIT_LOGIN: ("ol_failed_title", "ol_login"),
            SUBMIT_DENIED: ("ol_failed_title", "ol_denied"),
            SUBMIT_NETWORK: ("ol_failed_title", "ol_network"),
            SUBMIT_FAILED: ("ol_failed_title", "ol_failed"),
        }
        title_key, message_key = outcomes.get(outcome, ("ol_failed_title", "ol_failed"))
        self._say(text(title_key), text(message_key))
