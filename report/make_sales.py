"""make_sales.py: make a week of made-up sales spreadsheets, one per branch,
with the problems real ones have. Run it again any time to start over.

    python make_sales.py            the files as they first arrive
    python make_sales.py --resend   East, West and Central send corrected files,
                                    and North's file is closed in Excel
"""
import datetime
import pathlib
import shutil
import sys

from openpyxl import Workbook

WEEK = "2026-W46"                      # Monday 9 to Sunday 15 November 2026
MONDAY = datetime.date(2026, 11, 9)
HEADERS = ["date", "isbn", "title", "quantity", "price", "amount"]
BOOKS = [
    ("9780141439518", "Pride and Prejudice", 8.99),
    ("9780451524935", "Nineteen Eighty-Four", 9.99),
    ("9780061120084", "To Kill a Mockingbird", 10.99),
    ("9780743273565", "The Great Gatsby", 7.99),
    ("9780547928227", "The Hobbit", 12.99),
]


def rows(seed):
    """Two weeks' worth of plausible sales, the same every time."""
    out = []
    for day in range(7):
        for i, (isbn, title, price) in enumerate(BOOKS):
            qty = (seed * 7 + day * 5 + i * 3) % 6
            if qty:
                out.append([MONDAY + datetime.timedelta(days=day), isbn, title, qty, price, round(qty * price, 2)])
    return out


def save(path, data, extra=None):
    wb = Workbook()
    ws = wb.active
    ws.title = "Sales"
    ws.append(HEADERS)
    for r in data:
        ws.append(r)
    if extra:
        extra(ws, data)
    wb.save(path)


folder = pathlib.Path("sales") / WEEK
shutil.rmtree(folder, ignore_errors=True)
folder.mkdir(parents=True)

# North: tidy.
save(folder / "branch-north.xlsx", rows(1))


# South: the manager added a blank row and a TOTAL row at the bottom, as people do.
def totals(ws, data):
    ws.append([])
    ws.append([None, None, "TOTAL", sum(r[3] for r in data), None, round(sum(r[5] for r in data), 2)])


save(folder / "branch-south.xlsx", rows(2), totals)

# East: one quantity typed as text with a space ("3 "), and one typed as a word.
east = rows(3)
east[4][3] = "3 "
east[4][5] = round(3 * east[4][4], 2)
east[9][3] = "two"
save(folder / "branch-east.xlsx", east)

# West sent last week's file again, by mistake, under this week's name.
old = rows(4)
for r in old:
    r[0] = r[0] - datetime.timedelta(days=7)
save(folder / "branch-west.xlsx", old)

# And Central hasn't sent a file at all.

# North's file is open in Excel on someone's computer: Excel leaves a small
# "owner file" next to it, starting with ~$, while it's open.
(folder / "~$branch-north.xlsx").write_bytes(b"\x03Sam" + b"\x00" * 40)

if "--resend" in sys.argv:
    east[9][3] = 2
    east[9][5] = round(2 * east[9][4], 2)
    save(folder / "branch-east.xlsx", east)          # "3 " is still text: that one's fine
    save(folder / "branch-west.xlsx", rows(4))       # this week's, this time
    save(folder / "branch-central.xlsx", rows(5))
    (folder / "~$branch-north.xlsx").unlink()

for p in sorted(folder.iterdir()):
    print(f"{p.stat().st_size:>7}  {p}")
