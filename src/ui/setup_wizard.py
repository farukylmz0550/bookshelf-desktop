# Book Shelf — first-run setup: language, folder, theme.
# License: GPL-3.0-or-later (see LICENSE).

"""Three choices and a start button.

The stored theme applies live so the picker previews honestly; the
language switch is applied on confirm, since a half-translated wizard
is worse than a fully English one.
"""

from pathlib import Path

import gi

gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from shared import config, texts
from shared.texts import text
from shared.theme import DEFAULT

from .dialogs.confirmation import pick_folder

LANG_FILES = {"en": "🇬🇧 English", "tr": "🇹🇷 Türkçe", "ru": "🇷🇺 Русский",
              "zh": "🇨🇳 中文", "es": "🇪🇸 Español", "fr": "🇫🇷 Français"}
THEMES = ("default-light", "default-dark", "contrast-light", "contrast-dark", "custom")


class SetupPage(Gtk.Box):
    """Collect the three setup answers and hand over."""

    def __init__(self, on_done, on_theme, on_language):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=24, valign=Gtk.Align.CENTER)
        self.set_margin_top(24)
        self.on_done, self.on_theme, self.on_language = on_done, on_theme, on_language

        title = Gtk.Label(label=text("setup_title"), wrap=True)
        title.add_css_class("title-1")
        explain = Gtk.Label(label=text("setup_explain"), wrap=True, xalign=0.5)
        group = Adw.PreferencesGroup()
        group.add(self._row(text("settings_language"), self._languages()))
        group.add(self._theme_row())
        group.add(self._folder_row())
        start = Gtk.Button(label=text("setup_start"))
        start.add_css_class("suggested-action")
        start.add_css_class("pill")
        start.set_size_request(160, -1)
        start.connect("clicked", self._start)
        for widget in (title, explain, group, start):
            self.append(widget)

    # -- rows ----------------------------------------------------------
    def _row(self, title: str, control: Gtk.Widget) -> Adw.ActionRow:
        row = Adw.ActionRow(title=title)
        row.add_suffix(control)
        return row

    def _languages(self) -> Gtk.DropDown:
        codes = list(LANG_FILES)
        self._lang_model = Gtk.StringList.new([LANG_FILES[c] for c in codes])
        drop = Gtk.DropDown(model=self._lang_model)
        drop.set_selected(codes.index(texts.current() or "en"))
        drop.connect("notify::selected", lambda d, _p: self.on_language(codes[d.get_selected()]))
        return drop

    def _theme_row(self) -> Adw.ActionRow:
        self._themes = ["default-light", "default-dark", "contrast-light", "contrast-dark", "custom"]
        model = Gtk.StringList.new(
            [text(f"theme_{t}") if t != "custom" else text("theme_custom") for t in self._themes]
        )
        drop = Gtk.DropDown(model=model)
        current = config.theme() or DEFAULT
        if current in self._themes:
            drop.set_selected(self._themes.index(current))
        drop.connect("notify::selected", lambda d, _p: self._theme(d.get_selected()))
        return self._row(text("settings_theme"), drop)

    def _theme(self, index: int) -> None:
        name = self._themes[index]
        config.set_theme(name)
        self.on_theme(name)

    def _folder_row(self) -> Adw.ActionRow:
        self.folder = config.library_dir() or Path.home() / "Documents" / "BookShelf"
        self.folder_label = Gtk.Label(label=str(self.folder), ellipsize=3)
        row = Adw.ActionRow(title=text("settings_where"))
        row.set_subtitle_widget(self.folder_label)
        browse = Gtk.Button(label=text("setup_browse"))
        browse.add_css_class("flat")
        browse.connect("clicked", self._choose)
        row.add_suffix(browse)
        return row

    def _choose(self, _button) -> None:
        pick_folder(self.get_root(), self._picked, self.folder)

    def _picked(self, folder: Path) -> None:
        self.folder = folder
        self.folder_label.set_text(str(folder))

    def _start(self, _button) -> None:
        self.on_done(self.folder)
