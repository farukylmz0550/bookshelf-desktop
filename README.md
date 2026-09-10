# Book Shelf (Legacy — GTK4)

A desktop personal library manager for GNOME and Linux, built with **GTK4 + libadwaita**.

This is the final desktop edition of Book Shelf. The main repository continues as a web project; this one keeps the desktop app alive on the GNOME stack.

## Features

- Book management: add by ISBN (auto-filled from Open Library), edit, delete, multiple copies
- Search, filtering (rating, status, signed, lent out, tags) and sorting
- Lending: borrowers, loans, trust score, take-back
- Reading tracking: status, start/finish dates, duration
- Statistics: metric cards, yearly/monthly goals, pie charts (matplotlib)
- Excel import/export of ISBN lists and the whole library
- Contributing missing books back to Open Library (keyring-stored credentials)
- Theme (light/dark/contrast via libadwaita) and six languages

## Install

Download a package from the [releases](https://github.com/farukylmz0550/bookshelf-desktop/releases) page.

**Flatpak** — everything included, works on any distribution:

```bash
flatpak install ./BookShelf-1.1.0.flatpak
```

**RPM** (Fedora and derivatives) — dependencies resolve automatically:

```bash
sudo dnf install ./bookshelf-1.1.0-1.noarch.rpm
```

**DEB** (Debian, Ubuntu and derivatives):

```bash
sudo apt install ./bookshelf_1.1.0-1_all.deb
```

**Arch** (also usable as a PKGBUILD for AUR submission):

```bash
sudo pacman -U bookshelf-1.1.0-1-any.pkg.tar.zst
```

**Windows** — a portable build is attached to the release
(`BookShelf-*-windows-x64.zip`): unpack it anywhere and run `BookShelf.exe`.
The zip contains everything the app needs, including the GTK runtime,
Python and the bundled Adwaita Sans font, so it works on a clean system.
Build it yourself with PyInstaller against an MSYS2 GTK4 stack:

```bash
python -m PyInstaller packaging/windows/BookShelf.spec
```

The `packaging/windows` folder holds the spec, the runtime hook, the
executable icon and the font files; the `dist/BookShelf` folder it produces
is what an Inno Setup project points at to create the installer.


## Requirements (running from source)

GTK 4.10+, libadwaita 1.4+, Python 3.11+.

```bash
sudo dnf install gtk4 libadwaita python3-gobject python3-cairo
pip install -r requirements.txt
```

## Running

```bash
python3 src/main.py
```

## Packaging

Build scripts for every target live under `packaging/`:

```bash
sh packaging/build-rpm.sh      # bookshelf-*.rpm
sh packaging/build-deb.sh      # bookshelf_*_all.deb
sh packaging/build-arch.sh     # bookshelf-*.pkg.tar.zst (requires makepkg)
sh packaging/build-flatpak.sh  # BookShelf-*.flatpak (requires flatpak-builder)
```

All scripts stage the tree with `git archive`, so every packaging commit must be committed first.

## Licenses and credits

Book Shelf itself is **GPL-3.0-or-later** (see [LICENSE](LICENSE)). It stands
on the shoulders of these projects, thanks to all of them:

| Technology | Role | License |
| --- | --- | --- |
| [GTK 4](https://www.gtk.org/) | Widget toolkit | LGPL-2.1-or-later |
| [libadwaita](https://gitlab.gnome.org/GNOME/libadwaita) | Application shell and design | LGPL-2.1-or-later |
| [PyGObject](https://pygobject.gnome.org/) | Python bindings for the GNOME stack | LGPL-2.1-or-later |
| [pycairo](https://www.cairographics.org/pycairo/) | Cairo bindings | LGPL-2.1-or-later |
| [Python](https://www.python.org/) | The language itself | PSF-2.0 |
| [matplotlib](https://matplotlib.org/) | Reading statistics charts | Matplotlib license (BSD-compatible) |
| [openpyxl](https://openpyxl.readthedocs.io/) | Excel import/export | MIT |
| [keyring](https://github.com/jaraco/keyring) | Credential storage | MIT |
| [Adwaita Sans](https://gitlab.gnome.org/GNOME/adwaita-fonts) | UI font (bundled in the Windows build) | OFL-1.1 |
| [MSYS2](https://www.msys2.org/) | GTK runtime for the Windows build | BSD-3-Clause (packages under their own licenses) |

Third-party licenses are respected and reproduced where redistribution
applies (see `packaging/windows/fonts/OFL.txt` for the font).

## Tests

```bash
python3 -m pytest -q
```

## License

GPL-3.0-or-later — see [LICENSE](LICENSE).
