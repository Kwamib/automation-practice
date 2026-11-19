"""naive.py: the quick way. Add up the "amount" column of every spreadsheet
in a folder. It prints a confident total. Is it right?

    python naive.py sales/2026-W46
    python naive.py sales/2026-W46 'branch-*.xlsx'    (only files matching a pattern)
"""
import pathlib
import sys

from openpyxl import load_workbook

total = 0
for path in sorted(pathlib.Path(sys.argv[1]).glob(sys.argv[2] if len(sys.argv) > 2 else "*.xlsx")):
    ws = load_workbook(path).active
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row and isinstance(row[5], (int, float)):
            total += row[5]
    print(f"added {path.name}")
print(f"Total sales this week: ${total:,.2f}")
