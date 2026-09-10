# Katip Celebi — background cover loading.
# License: GPL-3.0-or-later (see LICENSE).

"""Load book covers off the UI thread, with an in-memory cache.

Covers are fetched and disk-cached by `services.openlibrary.fetch_cover`;
this loader decodes them into `GdkPixbuf` objects and reports back on the
GTK main loop via a caller-supplied callback.
"""

import logging
import threading

import gi

gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf, GLib

from services.openlibrary import COVER_SIZE_LARGE, COVER_SIZE_THUMB, cover_cache_path, fetch_cover

logger = logging.getLogger("katipcelebi")

THUMB_SIZE = (150, 210)
LARGE_SIZE = (260, 380)

_SIZE_TAG = {THUMB_SIZE: COVER_SIZE_THUMB, LARGE_SIZE: COVER_SIZE_LARGE}


def crop(pixbuf, size: tuple[int, int]):
    """Scale `pixbuf` to cover `size`, cropping the overflow centred."""
    w, h = size
    scale = max(w / pixbuf.get_width(), h / pixbuf.get_height())
    scaled = pixbuf.scale_simple(
        round(pixbuf.get_width() * scale), round(pixbuf.get_height() * scale),
        GdkPixbuf.InterpType.BILINEAR,
    )
    x = max(0, (scaled.get_width() - w) // 2)
    y = max(0, (scaled.get_height() - h) // 2)
    return scaled.subpixbuf(x, y, min(w, scaled.get_width()), min(h, scaled.get_height()))


def load(isbn: str, size: tuple[int, int]):
    """Return a cropped pixbuf for `isbn`, or None. Thread-safe."""
    raw = fetch_cover(isbn, _SIZE_TAG.get(size, COVER_SIZE_THUMB))
    if raw is None:
        return None
    loader = GdkPixbuf.PixbufLoader()
    try:
        loader.write(raw)
        loader.close()
        return crop(loader.get_pixbuf(), size)
    except Exception:
        logger.exception("Cover decode failed for %s", isbn)
        return None


class CoverLoader:
    """Request covers and receive results on the main loop."""

    def __init__(self):
        self._images: dict[tuple[str, tuple[int, int]], GdkPixbuf.Pixbuf | None] = {}
        self._asked: set[tuple[str, tuple[int, int]]] = set()
        self._lock = threading.Lock()

    def request(self, key: str, isbn: str, size: tuple[int, int], on_loaded) -> None:
        """Fetch `key`'s cover; `on_loaded(key, pixbuf)` runs on the main loop."""
        slot = (key, size)
        with self._lock:
            if slot in self._images:
                result = self._images[slot]
                GLib.idle_add(on_loaded, key, result)
                return
            if slot in self._asked or not isbn:
                return
            self._asked.add(slot)
        thread = threading.Thread(target=self._work, args=(slot, isbn, on_loaded), daemon=True)
        thread.start()

    def _work(self, slot, isbn, on_loaded) -> None:
        key, size = slot
        pixbuf = load(isbn, size)
        with self._lock:
            self._images[slot] = pixbuf
        GLib.idle_add(on_loaded, key, pixbuf)

    def forget(self, key: str) -> None:
        """Drop cached covers for `key`."""
        with self._lock:
            for slot in [s for s in self._images if s[0] == key]:
                del self._images[slot]
                self._asked.discard(slot)
