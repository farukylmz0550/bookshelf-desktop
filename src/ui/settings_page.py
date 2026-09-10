# Book Shelf — the settings page.
# License: GPL-3.0-or-later (see LICENSE).

"""Everything that survives a restart: theme, language, folder, cache.

Theme and language apply live; a folder move relocates the library
atomically through `shared.relocate`. Update checks run off the main
loop and report through toasts and dialogs.
"""

import logging
import shutil

import gi

gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from shared import config, credentials, paths, relocate, texts, theme
from shared.texts import text
from services.updater import check_for_update

from .dialogs.confirmation import alert, pick_folder, toast
from .work import run

logger = logging.getLogger("bookshelf")

THEMES = ("default-light", "default-dark", "contrast-light", "contrast-dark", "custom")
LANGS = (("en", "🇬🇧 English"), ("tr", "🇹🇷 Türkçe"), ("ru", "🇷🇺 Русский"),
         ("zh", "🇨🇳 中文"), ("es", "🇪🇸 Español"), ("fr", "🇫🇷 Français"))


class SettingsPage(Adw.PreferencesPage):
    """Long-lived choices, shown as a preferences sheet."""

    def __init__(self, window):
        super().__init__(vexpand=True)
        self.window = window

        general = Adw.PreferencesGroup(title=text("settings_theme"))
        general.add(self._theme_row())
        general.add(self._language_row())
        self.add(general)

        storage = Adw.PreferencesGroup(title=text("settings_where"))
        storage.add(self._folder_row())
        storage.add(self._cache_row())
        self.add(storage)

        about = Adw.PreferencesGroup(title=text("settings_about"))
        about.add(self._updates_row())
        about.add(self._about_row())
        self.add(about)

    # -- rows ---------------------------------------------------------------
    def _theme_row(self) -> Adw.ActionRow:
        drop = Gtk.DropDown(model=Gtk.StringList.new([text(f"theme_{t}") for t in THEMES]))
        drop.set_selected(THEMES.index(config.theme()) if config.theme() in THEMES else 0)
        drop.connect("notify::selected", lambda d, _p: self._theme(THEMES[d.get_selected()]))
        row = Adw.ActionRow(title=text("settings_theme"))
        row.add_suffix(drop)
        return row

    def _theme(self, name: str) -> None:
        config.set_theme(name)
        self.window.changed_settings("theme")

    def _language_row(self) -> Adw.ActionRow:
        codes = [c for c, _ in LANGS]
        drop = Gtk.DropDown(model=Gtk.StringList.new([label for _, label in LANGS]))
        if texts.current() in codes:
            drop.set_selected(codes.index(texts.current()))
        drop.connect("notify::selected", lambda d, _p: self._language(codes[d.get_selected()]))
        row = Adw.ActionRow(title=text("settings_language"))
        row.add_suffix(drop)
        return row

    def _language(self, code: str) -> None:
        texts.use(code)
        config.set_language(code)
        self.window.changed_settings("language")

    def _folder_row(self) -> Adw.ActionRow:
        row = Adw.ActionRow(title=text("settings_where"))
        self.folder_label = Adw.ButtonContent(
            label=str(config.library_dir() or ""), icon_name="folder-open-symbolic")
        button = Gtk.Button()
        button.set_child(self.folder_label)
        button.add_css_class("flat")
        button.connect("clicked", self._choose_folder)
        row.add_suffix(button)
        return row

    def _choose_folder(self, _button) -> None:
        pick_folder(self.window, self._move_to, config.library_dir())

    def _move_to(self, folder) -> None:
        current = config.library_dir()
        if folder == current:
            return
        result = relocate.move_library(current, folder)
        if not result.ok:
            alert(self.window, text("settings_move_failed_title"),
                  text("settings_move_failed").format(path=result.failed_to))
            return
        if relocate.files_in(folder):
            alert(self.window, text("settings_move_conflict_title"), text("settings_move_conflict"))
        config.set_library_dir(folder)
        self.folder_label.set_label(str(folder))
        self.window.changed_settings("folder")

    def _cache_row(self) -> Adw.ActionRow:
        row = Adw.ActionRow(title=text("settings_cache"))
        row.set_subtitle(text("settings_cache_size").format(size=self._cache_size_mb()))
        clear = Gtk.Button(label=text("settings_clear_cache"))
        clear.add_css_class("flat")
        clear.connect("clicked", lambda _b: self._clear_cache())
        row.add_suffix(clear)
        self._cache_row_widget = row
        return row

    @staticmethod
    def _cache_size() -> str:
        cache = paths.cover_cache_dir()
        total = sum(p.stat().st_size for p in cache.glob("*") if p.is_file())
        return f"{total / (1024 * 1024):.2f}"

    def _clear_cache(self, _button=None) -> None:
        cache = paths.cover_cache_dir()
        n = 0
        for path in cache.glob("*"):
            if path.is_file():
                try:
                    path.unlink()
                    n += 1
                except OSError:
                    logger.warning("Could not delete %s", path)
        self.window.covers = type(self.window.covers)()
        toast(self.window.overlay, text("settings_cache_cleared").format(n=n))

    def _updates_row(self) -> Adw.ActionRow:
        row = Adw.ActionRow(title=text("settings_check_updates"))
        self._check_updates()
        return row

    def _check_updates(self) -> None:
        def work():
            try:
                return check_for_update(paths.project_version())
            except Exception:
                return None
        run(work, self._update_result)

    def _update_result(self, result) -> None:
        if result is None:
            return
        has_update, latest, url = result
        if has_update:
            toast(self.window.overlay, text("settings_update_latest").format(version=latest))
        else:
            toast(self.window.overlay, text("up_to_date_message"))

    def _about_row(self) -> Adw.ActionRow:
        version = paths.project_version()
        row = Adw.ActionRow(
            title=text("app_name"),
            subtitle=f"v{version} · GPL-3.0 · github.com/farukylmz0550/bookshelf-legacy",
        )
        return row
