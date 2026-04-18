"""Ad-hoc SQL runner against torneo.db. Replacement for the sqlite3 CLI.

Usage:
    python scripts/query.py "SELECT short_name, owner FROM teams"
    python scripts/query.py "SELECT * FROM games" --limit 5
    python scripts/query.py --tables          # list all tables
    python scripts/query.py --schema teams    # show one table's columns
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "torneo.db")


def _fmt_cell(v: object, width: int) -> str:
    s = "NULL" if v is None else str(v)
    if len(s) > width:
        s = s[: width - 1] + "…"
    return s.ljust(width)


def _print_rows(rows: list[sqlite3.Row]) -> None:
    if not rows:
        print("(0 rows)")
        return
    cols = rows[0].keys()
    widths = {c: len(c) for c in cols}
    for r in rows:
        for c in cols:
            v = r[c]
            s = "NULL" if v is None else str(v)
            widths[c] = max(widths[c], min(len(s), 60))
    line = "  ".join(_fmt_cell(c, widths[c]) for c in cols)
    print(line)
    print("  ".join("-" * widths[c] for c in cols))
    for r in rows:
        print("  ".join(_fmt_cell(r[c], widths[c]) for c in cols))
    print(f"({len(rows)} row{'s' if len(rows) != 1 else ''})")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("sql", nargs="?", help="SQL query to run")
    ap.add_argument("--limit", type=int, default=None, help="Cap rows printed (appends LIMIT N if not present)")
    ap.add_argument("--tables", action="store_true", help="List all tables")
    ap.add_argument("--schema", metavar="TABLE", help="Show columns of a table")
    args = ap.parse_args()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if args.tables:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        _print_rows(rows)
        return

    if args.schema:
        rows = conn.execute(f"PRAGMA table_info({args.schema})").fetchall()
        _print_rows(rows)
        return

    if not args.sql:
        ap.print_help()
        sys.exit(1)

    sql = args.sql.strip().rstrip(";")
    if args.limit is not None and "limit" not in sql.lower():
        sql += f" LIMIT {args.limit}"

    try:
        rows = conn.execute(sql).fetchall()
    except sqlite3.Error as e:
        print(f"SQL error: {e}", file=sys.stderr)
        sys.exit(2)

    _print_rows(rows)


if __name__ == "__main__":
    main()
