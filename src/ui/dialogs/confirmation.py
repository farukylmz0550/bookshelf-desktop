# Katip Celebi — alert and toast helpers.
# License: GPL-3.0-or-later (see LICENSE).

"""Centre-place for confirmations, notices and toasts.

Every destructive action asks here; every lightweight confirmation is a
toast. Callback style: `confirm()` resolves asynchronously, so the caller
passes `on_ok` instead of reading a return value.
"""

import pathlib

import gi

gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, Gtk


def alert(window, title: str, message: str, on_ok=None, ok_label: str = "OK") -> None:
    """Show a modal message; call `on_ok` when the user accepts."""
    dialog = Adw.AlertDialog(body=message, heading=title)
    dialog.add_response("ok", ok_label)
    dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)
    if on_ok is not None:
        dialog.choose(window, None, lambda d, result: on_ok(), None)
    else:
        dialog.choose(window, None, lambda d, result: None, None)


def confirm(window, title: str, message: str, on_ok, ok_label: str = "OK") -> None:
    """Show a modal confirmation; `on_ok` runs only when accepted."""
    dialog = Adw.AlertDialog(body=message, heading=title)
    dialog.add_response("cancel", "Cancel")
    dialog.add_response("ok", ok_label)
    dialog.set_response_appearance("ok", Adw.ResponseAppearance.DESTRUCTIVE)
    dialog.choose(
        window, None,
        lambda d, result: on_ok() if d.choose_finish(result) == "ok" else None,
        None,
    )


def toast(overlay: Adw.ToastOverlay, message: str) -> None:
    """Show a transient message over `overlay`."""
    overlay.add_toast(Adw.Toast.new(message))


def pick_folder(window, on_done, start=None) -> None:
    """Open a native folder chooser; `on_done(Path)` runs when picked."""
    dialog = Gtk.FileDialog()
    if start is not None:
        dialog.set_initial_folder(Gio.File.new_for_path(str(start)))
    dialog.select_folder(
        window, None,
        lambda d, result: (f := d.select_folder_finish(result))
        and on_done(pathlib.Path(f.get_path())),
        None,
    )


def pick_save(window, on_done, default_name: str) -> None:
    """Open a native save dialog; `on_done(Path)` runs when chosen."""
    dialog = Gtk.FileDialog()
    dialog.set_initial_name(default_name)
    dialog.save(
        window, None,
        lambda d, result: (f := d.save_finish(result))
        and on_done(pathlib.Path(f.get_path())),
        None,
    )


def pick_open(window, on_done, default_name: str = "") -> None:
    """Open a native file chooser; `on_done(Path)` runs when chosen."""
    dialog = Gtk.FileDialog()
    if default_name:
        dialog.set_initial_name(default_name)
    dialog.open(
        window, None,
        lambda d, result: (f := d.open_finish(result))
        and on_done(pathlib.Path(f.get_path())),
        None,
    )
