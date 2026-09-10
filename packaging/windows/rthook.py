# Book Shelf — PyInstaller runtime hook for Windows GTK4 builds.
# License: GPL-3.0-or-later (see LICENSE).

import os
import sys
import tempfile

if getattr(sys, "_MEIPASS", None):
    schemas_dir = os.path.join(sys._MEIPASS, "share", "glib-2.0", "schemas")
    if os.path.isdir(schemas_dir):
        os.environ["GSETTINGS_SCHEMA_DIR"] = schemas_dir

    bundled_fonts = os.path.join(sys._MEIPASS, "share", "fonts")
    if os.path.isdir(bundled_fonts):
        conf = "\n".join(
            [
                "<fontconfig>",
                f'<dir>{bundled_fonts}</dir>',
                "<dir>WINDOWSFONTDIR</dir>",
                f'<cachedir>{tempfile.gettempdir()}\\bookshelf-fccache</cachedir>',
                "</fontconfig>",
            ]
        )
        path = os.path.join(tempfile.gettempdir(), "bookshelf-fonts.conf")
        try:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(conf)
            os.environ["FONTCONFIG_FILE"] = path
        except OSError:
            pass
