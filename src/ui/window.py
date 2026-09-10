# Katip Celebi — the main window and page navigation.
# License: GPL-3.0-or-later (see LICENSE).

"""Application shell: sidebar navigation plus a stack of pages.

First run shows the welcome and setup pages instead; once a library
folder is chosen the five main pages take over. A language change tears
the shell down and rebuilds it, since every page reads its strings at
build time.
"""

import logging
from pathlib import Path

import gi

gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib, Gtk

from core.goals import Goals
from core.ledger import Ledger
from core.store import Library
from services.cover_loader import CoverLoader
from shared import config, texts, theme
from shared.logs import point_at
from shared.texts import text

from .books.add_page import AddPage
from .books.library_page import LibraryPage
from .people_page import PeoplePage
from .settings_page import SettingsPage
from .stats_page import StatsPage
from .setup_wizard import SetupPage
from .welcome import WelcomePage

logger = logging.getLogger("katipcelebi")


class MainWindow(Adw.ApplicationWindow):
    """The single window: everything else lives inside it."""

    def __init__(self, app):
        super().__init__(application=app)
        self.set_title(text("app_name"))
        self.set_default_size(1000, 640)
        self.covers = CoverLoader()

        self.overlay = Adw.ToastOverlay()
        self.main_nav = Adw.NavigationView()
        self.split = Adw.NavigationSplitView()
        self.split.set_sidebar(Adw.NavigationPage(child=self._sidebar(), title=text("app_name")))
        self.split.set_content(Adw.NavigationPage(child=self.main_nav, title=text("app_name")))
        self.overlay.set_child(self.split)
        self.set_content(self.overlay)
        folder = config.library_dir()
        if config.setup_done() and folder:
            self.library = Library(folder)
            self.ledger = Ledger(folder)
            self.goals = Goals(folder)
            self._load_library()
        else:
            self.library = None
            self._show_welcome()

    # -- first-run flow -------------------------------------------------
    def _show_welcome(self) -> None:
        welcome = Adw.NavigationPage(
            child=WelcomePage(on_done=lambda: self._nav_push("setup")),
            title=text("app_name"),
        )
        self.main_nav.replace([welcome])

    def _nav_push(self, tag: str) -> None:
        if tag == "setup":
            setup = SetupPage(
                on_done=lambda folder: self._setup_done(folder),
                on_theme=self._pick_setup_theme,
                on_language=self._pick_language,
            )
            self.main_nav.push(Adw.NavigationPage(child=setup, title=text("setup_title")))
    def _setup_done(self, folder: Path) -> None:
        point_at(folder)
        if config.set_library_dir(folder):
            config.set_setup_done(True)
            self._open_library()
        else:
            self.overlay.add_toast(Adw.Toast.new(text("setup_folder_missing")))

    # -- sidebar ---------------------------------------------------------
    def _sidebar(self) -> Gtk.Widget:
        side = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=12,
            margin_start=12, margin_end=12, margin_top=12, margin_bottom=12,
        )
        brand = Gtk.Label(label=text("app_name"), xalign=0)
        brand.add_css_class("title-3")
        side.append(brand)
        side.append(Gtk.Separator())
        self._nav_buttons: dict[str, Gtk.Button] = {}
        entries = (
            ("nav_add", "add"), ("nav_library", "library"), ("nav_people", "people"),
            ("nav_stats", "stats"), ("nav_settings", "settings"),
        )
        for key, tag in entries:
            button = Gtk.Button()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            box.append(Gtk.Image.new_from_icon_name(self._icon(key)))
            box.append(Gtk.Label(label=text(key), xalign=0, hexpand=True))
            button.set_child(box)
            button.add_css_class("flat")
            button.connect("clicked", self._nav_clicked, tag)
            side.append(button)
            self._nav_buttons[tag] = button
        side.append(Gtk.Box(vexpand=True))  # spacer
        side.append(Gtk.Label(
            label=str(config.library_dir() or ""), xalign=0, wrap=True,
            css_classes=["caption", "dim-label"],
        ))
        frame = Adw.Clamp(maximum_size=280, tightening_threshold=200)
        frame.set_child(side)
        return frame

    def _icon(self, key: str) -> str:
        from shared.icons import name
        return name(key)

    def _nav_clicked(self, _button, tag: str) -> None:
        page = getattr(self, f"_{tag}_page", None)
        if page is None:
            return
        visible = self.main_nav.get_visible_page()
        if visible is not page:
            self.main_nav.pop_to_page(self._root_page)
            self.main_nav.push(page)

    # -- library ----------------------------------------------------------
    def _load_library(self) -> None:
        try:
            self.library.load()
            self.ledger.load()
            self.goals.load()
        except Exception:
            logger.exception("Library load failed")
        if getattr(self.library, "rescued_to", None):
            self._report_damage(self.library.rescued_to)
        self._build_pages()

    def _open_library(self) -> None:
        folder = config.library_dir()
        self.library = Library(folder)
        self.ledger = Ledger(folder)
        self.goals = Goals(folder)
        self._load_library()

    def _build_pages(self) -> None:
        self._add_page = AddPage(self)
        self._library_page = LibraryPage(self)
        self._people_page = PeoplePage(self)
        self._stats_page = StatsPage(self)
        self._settings_page = SettingsPage(self)
        pages = (
            (self._add_page, text("nav_add")),
            (self._library_page, text("nav_library")),
            (self._people_page, text("nav_people")),
            (self._stats_page, text("nav_stats")),
            (self._settings_page, text("nav_settings")),
        )
        ordered = [Adw.NavigationPage(child=w, title=t) for w, t in pages]
        self._page_of = {page.get_child(): page for page in ordered}
        first = ordered[0]
        self.main_nav.replace([first])
        for page in ordered[1:]:
            self.main_nav.add(page)
        self._root_page = first
        self.refresh_all()

    def _nav_clicked(self, _button, tag: str) -> None:
        page = getattr(self, f"_{tag}_page", None)
        if page is None:
            return
        target = self._page_of.get(page)
        if target is not None and self.main_nav.get_visible_page() is not target:
            self.main_nav.pop_to_page(self._root_page)
            self.main_nav.push(target)

    def refresh_all(self) -> None:
        self._library_page.refresh()
        self._people_page.refresh()
        self._stats_page.refresh()

    def books_changed(self) -> None:
        self._library_page.refresh()
        self._stats_page.refresh()

    def open_book(self, key: str) -> None:
        from .books.detail_page import DetailPage
        page = DetailPage(self, key)
        self.main_nav.push(Adw.NavigationPage(child=page, title=text("facts_heading")))

    def _pick_setup_theme(self, theme_name: str) -> None:
        config.set_theme(theme_name)
        theme.apply(theme_name)

    def _pick_language(self, code: str) -> None:
        texts.use(code)
        config.set_language(code)
        if getattr(self, "_root_page", None) is not None:
            self._rebuild_language()

    def _rebuild_language(self) -> None:
        self.main_nav = Adw.NavigationView()
        self.split.set_content(Adw.NavigationPage(child=self.main_nav, title=text("app_name")))
        self._open_library()

    def changed_settings(self, what: str) -> None:
        if what == "theme":
            theme.apply(config.theme())
        elif what == "language":
            self._pick_language(config.language())
        elif what == "folder":
            self._open_library()

    def _report_damage(self, rescued) -> None:
        from .dialogs.confirmation import alert
        alert(self, text("damaged_title"), text("damaged").format(path=rescued))
