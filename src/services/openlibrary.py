# Network client for Open Library (HTTP access, covers, submit)
import json
import logging
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from core.excel import MAX_IMPORT_BYTES
from shared.paths import project_version, cover_cache_dir
from core.book import normalize_isbn

logger = logging.getLogger("bookshelf")

USER_AGENT = f"BookShelf/{project_version()} (+https://github.com/farukylmz0550/bookshelf-legacy)"
API_ROOT = "https://openlibrary.org"
COVERS_ROOT = "https://covers.openlibrary.org/b/isbn/"
TIMEOUT = 10

COVER_SIZE_THUMB = "M"
COVER_SIZE_LARGE = "L"


def _get_json(url: str) -> Any:
    """Fetch and parse JSON. None on any failure."""
    attempts = 3
    backoff = 0.5
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=TIMEOUT) as reply:
                cl = reply.getheader("Content-Length")
                if cl is not None:
                    try:
                        size = int(cl)
                    except Exception:
                        size = None
                    if size is not None and size > MAX_IMPORT_BYTES:
                        logger.warning("Open Library reply too large: %s (%d bytes)", url, size)
                        return None
                data = reply.read(MAX_IMPORT_BYTES + 1)
                if len(data) > MAX_IMPORT_BYTES:
                    logger.warning("Open Library reply exceeded max size: %s", url)
                    return None
                return json.loads(data.decode("utf-8"))
        except urllib.error.HTTPError as error:
            code = getattr(error, "code", None)
            if code == 429 or (code and 500 <= code < 600):
                logger.debug("Transient HTTP error %s on %s, retrying (attempt %d)", code, url, attempt + 1)
                time.sleep(backoff * (2 ** attempt))
                continue
            logger.debug("Open Library HTTP error: %s %s", code, url, exc_info=True)
            return None
        except (
            urllib.error.URLError,
            json.JSONDecodeError,
            UnicodeDecodeError,
            OSError,
            TimeoutError,
        ):
            logger.debug("Open Library request failed: %s (attempt %d)", url, attempt + 1, exc_info=True)
            time.sleep(backoff * (2 ** attempt))
            continue
    return None


# Submission result constants
SUBMIT_OK = ""
SUBMIT_LOGIN = "login"
SUBMIT_DENIED = "denied"
SUBMIT_NETWORK = "network"
SUBMIT_FAILED = "failed"


def _edition(book) -> dict:
    from core.book import normalize_isbn

    isbn = normalize_isbn(book.key)
    edition = {
        "title": book.title,
        "source_records": [f"bookshelf-manual:{isbn}"],
    }
    if book.authors.strip():
        edition["authors"] = [
            {"name": name.strip()} for name in book.authors.split(",") if name.strip()
        ]
    if book.publishers.strip():
        edition["publishers"] = [p.strip() for p in book.publishers.split(",") if p.strip()]
    if book.publish_date.strip():
        edition["publish_date"] = book.publish_date.strip()
    if book.number_of_pages.strip():
        edition["number_of_pages"] = book.number_of_pages.strip()
    if len(isbn) == 13:
        edition["isbn_13"] = [isbn]
    elif len(isbn) == 10:
        edition["isbn_10"] = [isbn]
    return edition


def _post(opener, url: str, payload: dict):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
        method="POST",
    )
    return opener.open(request, timeout=TIMEOUT)


def submit_book(book, username: str, password: str) -> str:
    """Offer a book to Open Library. Returns empty string on success or a reason."""
    import http.cookiejar

    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    try:
        _post(
            opener,
            f"{API_ROOT}/account/login",
            {"username": username, "password": password},
        ).close()
    except urllib.error.HTTPError:
        logger.warning("Open Library login refused for %s", username)
        return SUBMIT_LOGIN
    except (urllib.error.URLError, OSError, TimeoutError):
        logger.warning("Open Library login could not be reached")
        return SUBMIT_NETWORK

    try:
        reply = _post(opener, f"{API_ROOT}/api/import", _edition(book))
        with reply:
            if reply.status in (200, 201):
                logger.info("Submitted %s to Open Library", book.key)
                return SUBMIT_OK
        logger.warning("Open Library import returned %s", reply.status)
        return SUBMIT_FAILED
    except urllib.error.HTTPError as error:
        reason = SUBMIT_DENIED if error.code == 403 else SUBMIT_FAILED
        logger.warning("Open Library import failed (HTTP %s)", error.code)
        return reason
    except (urllib.error.URLError, OSError, TimeoutError):
        logger.warning("Open Library import could not be reached")
        return SUBMIT_NETWORK


_IMAGE_MAGIC = (
    b"\xff\xd8\xff",
    b"\x89PNG\r\n\x1a\n",
    b"GIF87a",
    b"GIF89a",
    b"RIFF",
)


def _is_image(data: bytes) -> bool:
    return bool(data) and data.startswith(_IMAGE_MAGIC)


def cover_cache_path(isbn: str, size: str) -> Path:
    return cover_cache_dir() / (f"{normalize_isbn(isbn)}_{size}.jpg")


def fetch_cover(isbn: str, size: str = COVER_SIZE_THUMB) -> bytes | None:
    key = normalize_isbn(isbn)
    if not key:
        return None

    cached = cover_cache_path(key, size)
    if cached.exists():
        try:
            data = cached.read_bytes()
            if data:
                return data
        except OSError:
            logger.debug("Could not read the cached cover %s", cached, exc_info=True)

    url = f"{COVERS_ROOT}{key}-{size}.jpg?default=false"
    try:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=TIMEOUT) as reply:
            cl = reply.getheader("Content-Length")
            if cl is not None:
                try:
                    size = int(cl)
                except Exception:
                    size = None
                if size is not None and size > MAX_IMPORT_BYTES:
                    logger.debug("Cover reply too large: %s (%d bytes)", url, size)
                    return None
            data = reply.read(MAX_IMPORT_BYTES + 1)
            if len(data) > MAX_IMPORT_BYTES:
                logger.debug("Cover reply exceeded max size: %s", url)
                return None
    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        OSError,
        TimeoutError,
    ):
        logger.debug("No cover for %s (%s)", key, size, exc_info=True)
        return None

    if not _is_image(data):
        logger.debug("The cover reply for %s is not an image; not caching it", key)
        return None

    try:
        cached.write_bytes(data)
    except OSError:
        logger.debug("Could not cache the cover %s", cached, exc_info=True)
    return data


import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from core import tags
from core.book import Book, normalize_isbn

logger = logging.getLogger("bookshelf")

LANGUAGES = {
    "/languages/eng": "English",
    "/languages/tur": "Turkish",
    "/languages/fra": "French",
    "/languages/deu": "German",
    "/languages/spa": "Spanish",
    "/languages/ita": "Italian",
    "/languages/rus": "Russian",
    "/languages/zho": "Chinese",
    "/languages/jpn": "Japanese",
    "/languages/ara": "Arabic",
}


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        return str(value.get("value", "")).strip()
    if isinstance(value, list):
        return ", ".join(part for part in (_text(item) for item in value) if part)
    return ""


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _dict_list(value: Any) -> list[dict]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _author_name(key: str) -> str:
    data = _get_json(f"{API_ROOT}{key}.json")
    return _text(data.get("name")) if isinstance(data, dict) else ""


def _work_subjects(work_key: str) -> list[str]:
    if not work_key:
        return []
    data = _get_json(f"{API_ROOT}{work_key}.json")
    return _string_list(data.get("subjects")) if isinstance(data, dict) else []


def fetch_book(isbn: str) -> Book | None:
    key = normalize_isbn(isbn)
    edition = _get_json(f"{API_ROOT}/isbn/{key}.json")
    if not isinstance(edition, dict):
        return None

    book = Book(key=key)
    book.title = _text(edition.get("title"))
    book.subtitle = _text(edition.get("subtitle"))
    book.publish_date = _text(edition.get("publish_date"))
    book.publishers = _text(edition.get("publishers"))
    book.publish_places = _text(edition.get("publish_places"))
    book.edition_name = _text(edition.get("edition_name"))
    book.series = _text(edition.get("series"))
    book.number_of_pages = _text(edition.get("number_of_pages"))
    book.isbn_10 = ", ".join(_string_list(edition.get("isbn_10")))
    book.isbn_13 = ", ".join(_string_list(edition.get("isbn_13")))

    author_keys = [a.get("key") for a in _dict_list(edition.get("authors")) if a.get("key")]
    names = []
    if author_keys:
        max_workers = min(8, len(author_keys))
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {ex.submit(_author_name, k): k for k in author_keys}
            for fut in as_completed(futures):
                try:
                    n = fut.result()
                except Exception:
                    n = ""
                if n:
                    names.append(n)
    book.authors = ", ".join(name for name in names if name)

    spoken = []
    for entry in _dict_list(edition.get("languages")):
        code = str(entry.get("key", ""))
        spoken.append(LANGUAGES.get(code, code.replace("/languages/", "")))
    book.languages = ", ".join(name for name in spoken if name)

    subjects = _string_list(edition.get("subjects"))
    if not subjects:
        works = _dict_list(edition.get("works"))
        if works:
            subjects = _work_subjects(str(works[0].get("key", "")))
    book.subjects = ", ".join(subjects[:15])
    book.tags = tags.from_subjects(subjects[:15])

    return book
