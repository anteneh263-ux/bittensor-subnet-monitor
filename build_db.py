"""Load a fetched run (data/raw/<run>/) into the SQLite database data/subnets.db.

Every MANIFEST hash is checked before loading. Loading the same run twice is a no-op.
Numeric fields arrive as strings or numbers; both are stored as REAL. Fields not in
FIELDS are kept as JSON in `extra_json`, so nothing the API sends is silently lost.

    python3 build_db.py                      # newest run in data/raw/
    python3 build_db.py data/raw/20261030T150000Z
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sqlite3
import sys

from fetch import extract_rows

# Documented fields of GET /public/v1/analytics/subnet/{netuid}/ (TaoMarketCap, 2026-10-30).
FIELDS = [
    "block_number", "emission_percent", "chain_buys", "subnet_tao", "total_tao_buy", "total_tao_sell",
    "total_tao_buy_24h", "total_tao_sell_24h", "volume_24h", "tx_amount_24h", "tx_count_24h",
    "neuron_registrations_24h", "circulation_supply", "total_supply", "daily_emission",
    "rao_recycled_24h", "daily_inflation", "tao_price_usd", "tao_price_eur",
]

SCHEMA = f"""
CREATE TABLE IF NOT EXISTS runs (
    run_id      TEXT PRIMARY KEY,
    source      TEXT,
    span        TEXT,
    started_utc TEXT,
    subnets     INTEGER,
    rows        INTEGER
);
CREATE TABLE IF NOT EXISTS subnet_daily (
    run_id  TEXT NOT NULL REFERENCES runs(run_id),
    netuid  INTEGER NOT NULL,
    ts      TEXT NOT NULL,
    date    TEXT NOT NULL,
    {", ".join(f"{f} REAL" for f in FIELDS)},
    extra_json TEXT,
    PRIMARY KEY (run_id, netuid, ts)
);
CREATE INDEX IF NOT EXISTS ix_daily_date ON subnet_daily(run_id, date);
CREATE VIEW IF NOT EXISTS latest AS
    SELECT * FROM subnet_daily WHERE run_id = (SELECT MAX(run_id) FROM runs);
-- one row per subnet and day (the last observation of the day) from the newest run
CREATE VIEW IF NOT EXISTS daily AS
    SELECT * FROM (
        SELECT l.*, ROW_NUMBER() OVER (PARTITION BY netuid, date ORDER BY ts DESC) AS rn FROM latest l
    ) WHERE rn = 1;
"""


def to_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def verify_manifest(run_dir: pathlib.Path) -> dict:
    manifest = json.loads((run_dir / "MANIFEST.json").read_text())
    for name, meta in manifest["files"].items():
        digest = hashlib.sha256((run_dir / name).read_bytes()).hexdigest()
        if digest != meta["sha256"]:
            raise SystemExit(f"hash mismatch for {name}: refusing to load a changed raw file")
    return manifest


def load_run(run_dir: pathlib.Path, db_path: pathlib.Path) -> int:
    manifest = verify_manifest(run_dir)
    run_id = run_dir.name
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA)
    if con.execute("SELECT 1 FROM runs WHERE run_id = ?", (run_id,)).fetchone():
        print(f"run {run_id} already loaded, nothing to do")
        con.close()
        return 0

    cols = ["run_id", "netuid", "ts", "date", *FIELDS, "extra_json"]
    sql = f"INSERT OR IGNORE INTO subnet_daily ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})"
    total = 0
    with con:
        for name, meta in sorted(manifest["files"].items()):
            for row in extract_rows(json.loads((run_dir / name).read_text())):
                ts = str(row.get("ts", ""))
                if not ts:
                    continue
                netuid = int(row.get("netuid", meta["netuid"]))
                extra = {k: v for k, v in row.items() if k not in FIELDS and k not in ("ts", "netuid")}
                values = [run_id, netuid, ts, ts[:10], *(to_float(row.get(f)) for f in FIELDS),
                          json.dumps(extra) if extra else None]
                total += con.execute(sql, values).rowcount
        con.execute("INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?)",
                    (run_id, manifest.get("source"), manifest.get("span"), manifest.get("started_utc"),
                     len(manifest["files"]), total))
    con.close()
    print(f"loaded run {run_id}: {len(manifest['files'])} subnets, {total} rows -> {db_path}")
    return total


def newest_run(raw: pathlib.Path) -> pathlib.Path:
    runs = sorted(p for p in raw.iterdir() if (p / "MANIFEST.json").exists())
    if not runs:
        raise SystemExit(f"no fetched runs in {raw}; run fetch.py first")
    return runs[-1]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir", nargs="?")
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--db", default="data/subnets.db")
    args = ap.parse_args(argv)
    run_dir = pathlib.Path(args.run_dir) if args.run_dir else newest_run(pathlib.Path(args.raw))
    load_run(run_dir, pathlib.Path(args.db))
    return 0


if __name__ == "__main__":
    sys.exit(main())
