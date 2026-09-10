from pathlib import Path

from core.book import Book
from core import excel


def test_export_library_creates_file(tmp_path: Path):
    out = tmp_path / "export.xlsx"
    b = Book()
    b.key = "9780306406157"
    b.title = "Test Book"
    b.authors = "A. Author"
    ok = excel.export_library([b], ledger=None, path=out)
    assert ok
    assert out.exists()
    assert out.stat().st_size > 100
