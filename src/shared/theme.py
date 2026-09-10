# Book Shelf — theme handling via libadwaita.
# License: GPL-3.0-or-later (see LICENSE).

"""Colour scheme management backed by Adwaita.

Config names map to Adwaita colour schemes; the system theme is used
whenever the stored name is unknown.
"""

import gi

gi.require_version("Adw", "1")
from gi.repository import Adw

DEFAULT = "default-dark"
HIGH_CONTRAST = {"contrast-light", "contrast-dark"}


def apply(name: str) -> None:
    """Apply the stored theme name to the Adwaita style manager."""
    style = Adw.StyleManager.get_default()
    if name == "contrast-light":
        style.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
    elif name == "contrast-dark":
        style.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
    elif name == "default-light":
        style.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
    elif name == "default-dark":
        style.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
    else:  # custom / unknown: follow the system
        style.set_color_scheme(Adw.ColorScheme.DEFAULT)
