"""End-to-end tests on SYNTHETIC data shaped like the TaoMarketCap response. No network."""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import pathlib
import sqlite3
import tempfile
import unittest

import build_db
import report
from fetch import extract_rows, parse_netuids

ROOT = pathlib.Path(__file__).resolve().parent.parent


def make_run(base: pathlib.Path, days: int = 100) -> pathlib.Path:
    """Three subnets with 50/30/20 % of a network emission of 7 200 TAO (amounts in rao, as the API sends).
    SN2 is wrapped in {'data': [...]}, some values as strings."""
    run = base / "20261030T120000Z"
    run.mkdir(parents=True)
    start = dt.date(2026, 7, 23)
    manifest = {"source": "synthetic", "span": "ALL", "started_utc": "2026-10-30T12:00:00Z",
                "files": {}, "skipped": {"3": "HTTP 404, empty"}}
    for netuid, share in ((1, 50.0), (2, 30.0), (4, 20.0)):
        rows = []
        for i in range(days):
            day = start + dt.timedelta(days=i)
            rows.append({
                "ts": f"{day.isoformat()}T23:59:00Z", "netuid": netuid, "block_number": 1000 + i,
                "emission_percent": str(share), "volume_24h": str(100e9 * netuid),
                "tx_count_24h": 10 * netuid, "neuron_registrations_24h": 1,
                "daily_emission": "7200000000000", "tao_price_usd": "400.0", "unexpected_field": "kept",
            })
        payload = {"data": rows} if netuid == 2 else rows
        body = json.dumps(payload).encode()
        name = f"sn{netuid:03d}.json"
        (run / name).write_bytes(body)
        manifest["files"][name] = {"netuid": netuid, "url": "synthetic", "status": 200, "rows": days,
                                   "sha256": hashlib.sha256(body).hexdigest()}
    (run / "MANIFEST.json").write_text(json.dumps(manifest))
    return run


class FetchHelpers(unittest.TestCase):
    def test_parse_netuids(self):
        self.assertEqual(parse_netuids("0-3,7,2"), [0, 1, 2, 3, 7])

    def test_extract_rows_accepts_list_and_wrappers(self):
        self.assertEqual(extract_rows([{"a": 1}]), [{"a": 1}])
        self.assertEqual(extract_rows({"data": [{"a": 1}]}), [{"a": 1}])
        self.assertEqual(extract_rows({"detail": "not found"}), [])


class Pipeline(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = pathlib.Path(self.tmp.name)
        self.run_dir = make_run(self.base / "raw")
        self.db = self.base / "subnets.db"

    def tearDown(self):
        self.tmp.cleanup()

    def test_load_parses_numbers_and_keeps_unknown_fields(self):
        self.assertEqual(build_db.load_run(self.run_dir, self.db), 300)
        con = sqlite3.connect(self.db)
        e, extra = con.execute("SELECT emission_percent, extra_json FROM subnet_daily WHERE netuid=2 LIMIT 1").fetchone()
        self.assertEqual(e, 30.0)
        self.assertEqual(json.loads(extra), {"unexpected_field": "kept"})
        self.assertEqual(con.execute("SELECT COUNT(*) FROM daily").fetchone()[0], 300)

    def test_second_load_is_a_no_op(self):
        build_db.load_run(self.run_dir, self.db)
        self.assertEqual(build_db.load_run(self.run_dir, self.db), 0)
        con = sqlite3.connect(self.db)
        self.assertEqual(con.execute("SELECT COUNT(*) FROM subnet_daily").fetchone()[0], 300)

    def test_changed_raw_file_is_refused(self):
        (self.run_dir / "sn001.json").write_text("[]")
        with self.assertRaises(SystemExit):
            build_db.load_run(self.run_dir, self.db)

    def test_report_writes_every_query_with_correct_values(self):
        build_db.load_run(self.run_dir, self.db)
        out = self.base / "output"
        counts = report.run(self.db, ROOT / "sql" / "analysis.sql", out)
        self.assertEqual(set(counts), {"emission_share_check", "coverage", "latest_snapshot", "network_daily", "concentration_by_day",
                                       "activity_vs_reward_30d", "emission_trend_90d",
                                       "subnet_daily_dashboard", "concentration_by_month"})
        dash = list(csv.DictReader(open(out / "subnet_daily_dashboard.csv")))
        self.assertEqual(len(dash), 300)
        self.assertEqual(dash[0]["subnet"], "SN1")
        self.assertAlmostEqual(float(dash[0]["emission_share_pct"]), 50.0)
        conc = list(csv.DictReader(open(out / "concentration_by_day.csv")))
        self.assertEqual(len(conc), 100)
        self.assertAlmostEqual(float(conc[-1]["top10_share"]), 1.0)          # only 3 subnets
        self.assertAlmostEqual(float(conc[-1]["hhi"]), 0.5**2 + 0.3**2 + 0.2**2, places=4)
        self.assertEqual(conc[-1]["quality_ok"], "0")        # only 3 subnets with a share: fails rule (b)
        self.assertEqual(list(csv.DictReader(open(out / "concentration_by_month.csv"))), [])
        act = {r["netuid"]: r for r in csv.DictReader(open(out / "activity_vs_reward_30d.csv"))}
        self.assertEqual(int(act["1"]["days"]), 30)
        self.assertAlmostEqual(float(act["4"]["avg_volume_tao_24h"]), 400.0)          # rao -> TAO
        self.assertAlmostEqual(float(act["4"]["avg_subnet_emission_tao"]), 0.2 * 7200)  # 20 % of network
        self.assertAlmostEqual(float(act["4"]["volume_to_emission"]), round(400.0 / 1440.0, 3))
        check = list(csv.DictReader(open(out / "emission_share_check.csv")))
        self.assertAlmostEqual(float(check[0]["percent_sum"]), 100.0)
        trend = list(csv.DictReader(open(out / "emission_trend_90d.csv")))
        self.assertEqual(len(trend), 3)
        self.assertTrue(all(float(r["change_pp"]) == 0.0 for r in trend))  # constant shares


if __name__ == "__main__":
    unittest.main()
