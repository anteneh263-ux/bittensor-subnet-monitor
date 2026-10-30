"""Run every query in sql/analysis.sql against data/subnets.db and write output/<name>.csv.

The CSV files are what the dashboard (Power BI, Tableau Public or Looker Studio) reads.

    python3 report.py
"""
from __future__ import annotations

import argparse
import csv
import pathlib
import re
import sqlite3
import sys


def parse_queries(text: str) -> dict[str, str]:
    blocks = re.split(r"^-- name:\s*(\S+)\s*$", text, flags=re.M)
    return {name: sql.strip() for name, sql in zip(blocks[1::2], blocks[2::2])}


def run(db: pathlib.Path, sql_file: pathlib.Path, out: pathlib.Path) -> dict[str, int]:
    if not db.exists():
        raise SystemExit(f"{db} not found; run fetch.py and build_db.py first")
    out.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db)
    counts = {}
    for name, sql in parse_queries(sql_file.read_text()).items():
        cur = con.execute(sql)
        header = [c[0] for c in cur.description]
        rows = cur.fetchall()
        with open(out / f"{name}.csv", "w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(header)
            writer.writerows(rows)
        counts[name] = len(rows)
        print(f"{name}: {len(rows)} rows -> {out / (name + '.csv')}")
    con.close()
    return counts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default="data/subnets.db")
    ap.add_argument("--sql", default="sql/analysis.sql")
    ap.add_argument("--out", default="output")
    args = ap.parse_args(argv)
    run(pathlib.Path(args.db), pathlib.Path(args.sql), pathlib.Path(args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
