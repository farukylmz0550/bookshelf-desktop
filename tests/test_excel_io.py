from pathlib import Path

from core import excel


def test_write_and_read_template_roundtrip(tmp_path: Path):
    path = tmp_path / "template.xlsx"
    assert excel.write_template(path)
    try:
        import openpyxl
    except ImportError:
        return
    wb = openpyxl.load_workbook(path)
    ws = wb.active
    ws["A2"] = "9780306406157"
    wb.save(path)
    wb.close()
    found = excel.read_template(path)
    assert found is not None
    assert "9780306406157" in found
