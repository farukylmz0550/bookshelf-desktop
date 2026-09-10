# Katip Celebi (Legacy — GTK4)

A desktop personal library manager for GNOME and Linux, built with **GTK4 + libadwaita**.

This is the final desktop edition of Katip Celebi. The main repository continues as a web project; this one keeps the desktop app alive on the GNOME stack.

## Features

- Book management: add by ISBN (auto-filled from Open Library), edit, delete, multiple copies
- Search, filtering (rating, status, signed, lent out, tags) and sorting
- Lending: borrowers, loans, trust score, take-back
- Reading tracking: status, start/finish dates, duration
- Statistics: metric cards, yearly/monthly goals, pie charts (matplotlib)
- Excel import/export of ISBN lists and the whole library
- Contributing missing books back to Open Library (keyring-stored credentials)
- Theme (light/dark/contrast via libadwaita) and six languages

## Requirements

GTK 4.10+, libadwaita 1.4+, Python 3.11+.

```bash
sudo dnf install gtk4 libadwaita python3-gobject python3-cairo
pip install -r requirements.txt
```

## Running

```bash
python3 src/main.py
```

## Tests

```bash
python3 -m pytest -q
```

## License

GPL-3.0-or-later — see [LICENSE](LICENSE).
