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

## Tests

```bash
python3 -m pytest -q
```

## License

GPL-3.0-or-later — see [LICENSE](LICENSE).
