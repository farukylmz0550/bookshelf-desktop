# Katip Celebi — symbolic icon names for buttons and navigation.
# License: GPL-3.0-or-later (see LICENSE).

"""Standard icon names resolved through the GTK icon theme."""

APP_LOGO = "assets/katipcelebi.svg"

# Logical name -> freedesktop/GNOME symbolic icon name.
ICONS = {
    "nav_add": "library-add-symbolic",
    "nav_library": "view-grid-symbolic",
    "nav_people": "system-users-symbolic",
    "nav_stats": "bar-chart-symbolic",
    "nav_settings": "preferences-system-symbolic",
    "fetch": "system-search-symbolic",
    "save": "document-save-symbolic",
    "clear": "edit-clear-symbolic",
    "delete_book": "user-trash-symbolic",
    "export": "document-save-symbolic",
    "import": "document-open-symbolic",
    "template": "x-office-spreadsheet-symbolic",
    "move": "folder-open-symbolic",
    "reload": "view-refresh-symbolic",
    "back": "go-previous-symbolic",
}


def name(logical: str) -> str:
    """Resolve a logical icon name, falling back to a generic one."""
    return ICONS.get(logical, "image-missing-symbolic")
