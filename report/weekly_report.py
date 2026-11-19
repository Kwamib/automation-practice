"""weekly_report.py: build the bookshop's weekly sales report from the branches'
spreadsheets, and email it.

    python weekly_report.py --week 2026-W46            build the report, send nothing
    python weekly_report.py --week 2026-W46 --send     build it, and email it

Settings come from the environment, so the same script runs anywhere:
    SALES_DIR    where the branches' folders are        (default: sales)
    REPORT_DIR   where reports are written              (default: reports)
    SMTP_HOST, SMTP_PORT, REPORT_FROM, REPORT_TO        where the email goes
    SMTP_USER, SMTP_PASSWORD                            only if the mail server needs a login

Exit codes: 0 every branch's file was good; 1 the report was built but is
incomplete (a branch's file is missing or was rejected, and the report says
which); 2 called wrongly, or a setup problem.
"""
import argparse
import datetime
import logging
import os
import pathlib
import smtplib
import sys
import tempfile
import time
from collections import defaultdict
from dataclasses import dataclass, field
from email.message import EmailMessage

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font

BRANCHES = ["north", "south", "east", "west", "central"]
HEADERS = ["date", "isbn", "title", "quantity", "price", "amount"]
TOTAL_WORDS = {"total", "totals", "grand total", "sum"}

logging.Formatter.converter = time.gmtime
logging.basicConfig(format="%(asctime)sZ weekly_report: %(message)s",
                    datefmt="%Y-%m-%dT%H:%M:%S", level=logging.INFO)
log = logging.getLogger()


class BadFile(Exception):
    """A branch's file can't be used. The message says why, for a person to fix."""


@dataclass
class Branch:
    name: str
    status: str = "missing"            # ok, missing or rejected
    reason: str = ""
    rows: list = field(default_factory=list)
    notes: list = field(default_factory=list)

    @property
    def units(self):
        return sum(r[2] for r in self.rows)

    @property
    def sales(self):
        return round(sum(r[2] * r[3] for r in self.rows), 2)


def week_dates(week):
    """'2026-W46' -> (Monday, Sunday) of that ISO week."""
    try:
        year, num = week.split("-W")
        monday = datetime.date.fromisocalendar(int(year), int(num), 1)
    except ValueError:
        raise SystemExit(f"--week must look like 2026-W46, not {week!r}") from None
    return monday, monday + datetime.timedelta(days=6)


def whole_number(value, where, notes):
    if isinstance(value, bool):
        raise BadFile(f"{where}: quantity {value!r} isn't a whole number")
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        notes.append(f"{where}: quantity {value!r} was typed as text; read it as {int(value.strip())}")
        return int(value.strip())
    raise BadFile(f"{where}: quantity {value!r} isn't a whole number")


def read_branch(path, monday, sunday):
    """Read one branch's file. Returns (rows, notes), or raises BadFile.
    All of a file, or none of it: one bad row rejects the whole file."""
    notes, rows = [], []
    try:
        wb = load_workbook(path, read_only=True, data_only=True)
    except Exception as e:
        raise BadFile(f"it isn't a spreadsheet Excel can open ({e})") from None
    if "Sales" not in wb.sheetnames:
        raise BadFile(f"there's no sheet called Sales (it has: {', '.join(wb.sheetnames)})")
    sheet = wb["Sales"].iter_rows(values_only=True)
    header = [str(c).strip().lower() if c is not None else "" for c in next(sheet, ())]
    if header[:len(HEADERS)] != HEADERS:
        raise BadFile(f"the columns are {header}, not {HEADERS}")

    for n, row in enumerate(sheet, start=2):
        where = f"row {n}"
        cells = (list(row) + [None] * len(HEADERS))[:len(HEADERS)]
        if all(c is None or str(c).strip() == "" for c in cells):
            continue
        day, isbn, title, qty, price, amount = cells
        if day is None and isbn is None and str(title).strip().lower() in TOTAL_WORDS:
            notes.append(f"{where}: skipped a totals row, so it isn't counted twice")
            continue
        if not isinstance(day, datetime.datetime):
            raise BadFile(f"{where}: date {day!r} isn't a date")
        if not monday <= day.date() <= sunday:
            raise BadFile(f"{where}: date {day.date()} isn't in this week ({monday} to {sunday}); is this last week's file?")
        isbn = str(isbn).strip()
        if not (isbn.isdigit() and len(isbn) == 13):
            raise BadFile(f"{where}: ISBN {isbn!r} isn't 13 digits")
        qty = whole_number(qty, where, notes)
        if not isinstance(price, (int, float)) or price <= 0:
            raise BadFile(f"{where}: price {price!r} isn't a positive number")
        if isinstance(amount, (int, float)) and abs(amount - qty * price) > 0.005:
            raise BadFile(f"{where}: amount {amount} isn't quantity x price ({qty} x {price})")
        rows.append((isbn, str(title).strip(), qty, float(price)))
    if not rows:
        raise BadFile("it has no sales rows")
    return rows, notes


def gather(folder, monday, sunday):
    branches = []
    for name in BRANCHES:
        b = Branch(name)
        path = folder / f"branch-{name}.xlsx"
        if (folder / f"~$branch-{name}.xlsx").exists():
            b.notes.append("the file is open in Excel on someone's computer, so it may have unsaved changes")
        if not path.exists():
            b.reason = f"no file called {path.name}"
            log.info(f"{name}: MISSING ({b.reason})")
        else:
            try:
                b.rows, notes = read_branch(path, monday, sunday)
                b.notes += notes
                b.status = "ok"
                log.info(f"{name}: ok, {len(b.rows)} lines, {b.units} books, ${b.sales:,.2f}")
            except BadFile as e:
                b.status, b.reason = "rejected", str(e)
                log.info(f"{name}: REJECTED ({b.reason})")
        for note in b.notes:
            log.info(f"{name}: note: {note}")
        branches.append(b)
    expected = {f"branch-{n}.xlsx" for n in BRANCHES} | {f"~$branch-{n}.xlsx" for n in BRANCHES}
    for p in sorted(folder.iterdir()):
        if p.name not in expected:
            log.info(f"ignored a file nobody expects: {p.name}")
    return branches


def build_workbook(week, monday, sunday, branches):
    good = [b for b in branches if b.status == "ok"]
    problems = [b for b in branches if b.status != "ok"]
    wb = Workbook()
    ws = wb.active
    ws.title = "Summary"
    bold = Font(bold=True)
    ws.append([f"Bookshop weekly sales, {week} ({monday:%d %B} to {sunday:%d %B %Y})"])
    ws["A1"].font = Font(bold=True, size=14)
    if problems:
        ws.append([f"INCOMPLETE: {len(good)} of {len(branches)} branches. Not included: "
                   + "; ".join(f"{b.name} ({b.status}: {b.reason})" for b in problems)])
        ws["A2"].font = Font(bold=True, color="C00000")
    else:
        ws.append(["Complete: every branch's file was checked and included."])
    ws.append([])
    ws.append(["Branch", "Status", "Lines", "Books sold", "Sales", "Notes"])
    for c in ws[ws.max_row]:
        c.font = bold
    for b in branches:
        ws.append([b.name, b.status, len(b.rows) or None, b.units or None, b.sales or None,
                   "; ".join(([b.reason] if b.reason else []) + b.notes)])
    ws.append(["Total", f"{len(good)} of {len(branches)} branches", sum(len(b.rows) for b in good),
               sum(b.units for b in good), round(sum(b.sales for b in good), 2), ""])
    for c in ws[ws.max_row]:
        c.font = bold
    for row in ws.iter_rows(min_row=5, min_col=5, max_col=5):
        row[0].number_format = "$#,##0.00"
    for col, width in zip("ABCDEF", (12, 26, 8, 12, 14, 90)):
        ws.column_dimensions[col].width = width

    top = wb.create_sheet("Top books")
    top.append(["Title", "Books sold", "Sales"])
    for c in top[1]:
        c.font = bold
    by_title = defaultdict(lambda: [0, 0.0])
    for b in good:
        for _, title, qty, price in b.rows:
            by_title[title][0] += qty
            by_title[title][1] += qty * price
    for title, (units, sales) in sorted(by_title.items(), key=lambda kv: -kv[1][1]):
        top.append([title, units, round(sales, 2)])
        top.cell(top.max_row, 3).number_format = "$#,##0.00"
    for col, width in zip("ABC", (30, 12, 14)):
        top.column_dimensions[col].width = width
    return wb


def save_atomically(wb, path):
    """Write to a temporary file in the same folder, then rename: nobody ever
    opens half a report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".report-", suffix=".xlsx")
    os.close(fd)
    try:
        wb.save(tmp)
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise


def summary_text(week, branches):
    good = [b for b in branches if b.status == "ok"]
    lines = [f"Weekly sales, {week}", ""]
    for b in branches:
        if b.status == "ok":
            lines.append(f"  {b.name:<8} ${b.sales:>10,.2f}  ({b.units} books)")
        else:
            lines.append(f"  {b.name:<8} {b.status.upper()}: {b.reason}")
    lines += ["", f"  Total    ${sum(b.sales for b in good):>10,.2f}  from {len(good)} of {len(branches)} branches"]
    if len(good) < len(branches):
        lines += ["", "This report is INCOMPLETE. The branches above need to send a corrected file."]
    lines += ["", "The full report is attached. Sent by weekly_report.py."]
    return "\n".join(lines)


def send(path, subject, body):
    env = os.environ
    missing = [k for k in ("SMTP_HOST", "REPORT_FROM", "REPORT_TO") if not env.get(k)]
    if missing:
        raise SystemExit(f"can't send: set {', '.join(missing)}")
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, env["REPORT_FROM"], env["REPORT_TO"]
    msg.set_content(body)
    msg.add_attachment(path.read_bytes(), maintype="application",
                       subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=path.name)
    with smtplib.SMTP(env["SMTP_HOST"], int(env.get("SMTP_PORT", "25")), timeout=15) as smtp:
        if env.get("SMTP_USER"):                    # a real mail server: encrypt, then log in
            smtp.starttls()
            smtp.login(env["SMTP_USER"], env["SMTP_PASSWORD"])
        smtp.send_message(msg)
    log.info(f"emailed the report to {env['REPORT_TO']}")


def main(argv=None):
    p = argparse.ArgumentParser(description="Build the weekly sales report, and email it with --send.")
    p.add_argument("--week", required=True, help="the ISO week, like 2026-W46")
    p.add_argument("--send", action="store_true", help="email the report (without it, nothing is sent)")
    args = p.parse_args(argv)

    monday, sunday = week_dates(args.week)
    folder = pathlib.Path(os.environ.get("SALES_DIR", "sales")) / args.week
    if not folder.is_dir():
        log.info(f"no folder {folder}: nothing to report on")
        return 2
    branches = gather(folder, monday, sunday)
    good = [b for b in branches if b.status == "ok"]

    path = pathlib.Path(os.environ.get("REPORT_DIR", "reports")) / f"sales-{args.week}.xlsx"
    save_atomically(build_workbook(args.week, monday, sunday, branches), path)
    total = sum(b.sales for b in good)
    complete = len(good) == len(branches)
    subject = (f"Weekly sales {args.week}: ${total:,.2f} from {len(good)} of {len(branches)} branches"
               + ("" if complete else " (INCOMPLETE)"))
    log.info(f"wrote {path}: {subject}")
    print(summary_text(args.week, branches))

    if args.send:
        send(path, subject, summary_text(args.week, branches))
    else:
        log.info("not sending: add --send to email it")
    return 0 if complete else 1


if __name__ == "__main__":
    sys.exit(main())
