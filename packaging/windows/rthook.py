# Book Shelf — PyInstaller runtime hook for Windows GTK4 builds.
# License: GPL-3.0-or-later (see LICENSE).

import os
import sys

if getattr(sys, "_MEIPASS", None):
    schemas_dir = os.path.join(sys._MEIPASS, "share", "glib-2.0", "schemas")
    if os.path.isdir(schemas_dir):
        os.environ["GSETTINGS_SCHEMA_DIR"] = schemas_dir
