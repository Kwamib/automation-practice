"""Tests for weekly_report.py: one for each kind of problem a branch's file can have.

    python -m pytest -v
"""
import datetime

import pytest
from openpyxl import Workbook

import weekly_report as wr

MONDAY, SUNDAY = wr.week_dates("2026-W46")
DAY = datetime.datetime(2026, 11, 10)
GOOD = [DAY, "9780141439518", "Pride and Prejudice", 2, 8.99, 17.98]


def sheet(tmp_path, *rows, headers=wr.HEADERS, title="Sales"):
    wb = Workbook()
    ws = wb.active
    ws.title = title
    ws.append(headers)
    for r in rows:
        ws.append(r)
    path = tmp_path / "branch-north.xlsx"
    wb.save(path)
    return path


def test_a_good_file_is_read(tmp_path):
    rows, notes = wr.read_branch(sheet(tmp_path, GOOD), MONDAY, SUNDAY)
    assert rows == [("9780141439518", "Pride and Prejudice", 2, 8.99)]
    assert notes == []


def test_a_totals_row_is_skipped_not_counted(tmp_path):
    rows, notes = wr.read_branch(sheet(tmp_path, GOOD, [], [None, None, "TOTAL", 2, None, 17.98]), MONDAY, SUNDAY)
    assert len(rows) == 1
    assert "totals row" in notes[0]


def test_a_number_typed_as_text_is_read_and_noted(tmp_path):
    rows, notes = wr.read_branch(sheet(tmp_path, [DAY, "9780141439518", "Pride and Prejudice", "3 ", 8.99, 26.97]), MONDAY, SUNDAY)
    assert rows[0][2] == 3
    assert "typed as text" in notes[0]


@pytest.mark.parametrize("row, message", [
    ([DAY, "9780141439518", "Pride and Prejudice", "two", 8.99, None], "isn't a whole number"),
    ([datetime.datetime(2026, 11, 2), "9780141439518", "Pride and Prejudice", 2, 8.99, 17.98], "isn't in this week"),
    ([DAY, "978014143951", "Pride and Prejudice", 2, 8.99, 17.98], "isn't 13 digits"),
    ([DAY, "9780141439518", "Pride and Prejudice", 2, 8.99, 20.00], "isn't quantity x price"),
    ([DAY, "9780141439518", "Pride and Prejudice", 2, "free", None], "isn't a positive number"),
])
def test_one_bad_row_rejects_the_whole_file(tmp_path, row, message):
    with pytest.raises(wr.BadFile, match=message):
        wr.read_branch(sheet(tmp_path, GOOD, row), MONDAY, SUNDAY)


def test_wrong_columns_are_rejected(tmp_path):
    with pytest.raises(wr.BadFile, match="the columns are"):
        wr.read_branch(sheet(tmp_path, GOOD, headers=["Date", "ISBN", "Qty"]), MONDAY, SUNDAY)


def test_a_file_that_isnt_a_spreadsheet_is_rejected(tmp_path):
    path = tmp_path / "branch-north.xlsx"
    path.write_bytes(b"\x03Sam" + b"\x00" * 40)
    with pytest.raises(wr.BadFile, match="isn't a spreadsheet"):
        wr.read_branch(path, MONDAY, SUNDAY)


def test_missing_branches_and_excel_lock_files(tmp_path):
    sheet(tmp_path, GOOD)
    (tmp_path / "~$branch-north.xlsx").write_bytes(b"\x03Sam")
    branches = {b.name: b for b in wr.gather(tmp_path, MONDAY, SUNDAY)}
    assert branches["north"].status == "ok"
    assert "open in Excel" in branches["north"].notes[0]
    assert branches["central"].status == "missing"


def test_an_incomplete_week_says_so_and_exits_1(tmp_path, monkeypatch):
    (tmp_path / "sales" / "2026-W46").mkdir(parents=True)
    sheet(tmp_path / "sales" / "2026-W46", GOOD)
    monkeypatch.setenv("SALES_DIR", str(tmp_path / "sales"))
    monkeypatch.setenv("REPORT_DIR", str(tmp_path / "reports"))
    assert wr.main(["--week", "2026-W46"]) == 1
    assert (tmp_path / "reports" / "sales-2026-W46.xlsx").exists()
