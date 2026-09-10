# Book Shelf — PyInstaller spec for Windows builds (MSYS2 GTK4).
# License: GPL-3.0-or-later (see LICENSE).

import glob
import os

from pathlib import Path

ROOT = Path(SPECPATH).resolve().parent.parent
PREFIX = os.path.dirname(os.path.dirname(os.environ.get("GI_TYPELIB_PATH", "C:\\msys64\\mingw64\\lib\\girepository-1.0")))
SCHEMAS_DIR = os.path.join(PREFIX, "share", "glib-2.0", "schemas")

schemas = [(s, "share/glib-2.0/schemas") for s in glob.glob(os.path.join(SCHEMAS_DIR, "*"))]

a = Analysis(
    [str(ROOT / "src" / "main.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=[
        (str(ROOT / "assets"), "assets"),
        (str(ROOT / "VERSION"), "."),
        (str(ROOT / "packaging" / "windows" / "fonts"), "share/fonts"),
        *schemas,
    ],
    hiddenimports=[
        "matplotlib.backends.backend_gtk4agg",
    ],
    excludes=["tkinter"],
    hooksconfig={
        "gi": {
            "module-versions": {
                "Gtk": "4.0",
                "Gdk": "4.0",
                "Adw": "1",
                "GdkPixbuf": "2.0",
            },
        },
    },
    runtime_hooks=[str(ROOT / "packaging" / "windows" / "rthook.py")],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="BookShelf",
    debug=False,
    upx=False,
    console=False,
    icon=str(ROOT / "packaging" / "windows" / "BookShelf.ico"),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="BookShelf",
)
