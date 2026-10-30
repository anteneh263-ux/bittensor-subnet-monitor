"""Fetch daily per-subnet history from TaoMarketCap's public API (no API key needed).

Writes one JSON file per subnet into a NEW run folder under data/raw/ plus a MANIFEST.json
with URL, HTTP status, row count and SHA-256 for every file. Existing runs are never overwritten.

Anonymous limits (per IP): 10 requests/minute, 600/hour. The script waits between calls,
so a full run over all subnets takes roughly 15 minutes.

    python3 fetch.py                 # all netuids 0..128, span=ALL (up to 365 daily rows)
    python3 fetch.py --netuids 1-5   # a quick test on five subnets
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import sys
import time
import urllib.error
import urllib.request

BASE = "https://api.taomarketcap.com/public/v1/analytics/subnet/{netuid}/?span={span}"
MIN_INTERVAL_S = 6.5          # stays under 10 requests/minute
USER_AGENT = "bittensor-subnet-monitor/0.1 (portfolio project)"


def parse_netuids(spec: str) -> list[int]:
    out: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-")
            out.extend(range(int(lo), int(hi) + 1))
        elif part:
            out.append(int(part))
    return sorted(set(out))


def http_get(url: str, retries: int = 5) -> tuple[int, bytes]:
    """GET with polite retries. Returns (status, body); 404 returns (404, b'')."""
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.status, resp.read()
        except urllib.error.HTTPError as err:
            if err.code == 404:
                return 404, b""
            if err.code == 429:
                wait = int(err.headers.get("Retry-After") or 60)
                print(f"  rate limited, waiting {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            if 500 <= err.code < 600:
                time.sleep(10 * (attempt + 1))
                continue
            raise
        except urllib.error.URLError as err:
            print(f"  network error ({err.reason}), retrying", file=sys.stderr)
            time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"giving up after {retries} attempts: {url}")


def extract_rows(payload) -> list[dict]:
    """The endpoint returns a JSON array; tolerate a {'data': [...]} / {'results': [...]} wrapper."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("data", "results", "items"):
            if isinstance(payload.get(key), list):
                return payload[key]
    return []


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--netuids", default="0-128")
    ap.add_argument("--span", default="ALL", choices=["1D", "1W", "1M", "1Y", "ALL"])
    ap.add_argument("--out", default="data/raw")
    args = ap.parse_args(argv)

    started = dt.datetime.now(dt.timezone.utc)
    run_dir = pathlib.Path(args.out) / started.strftime("%Y%m%dT%H%M%SZ")
    run_dir.mkdir(parents=True, exist_ok=False)
    manifest = {"source": "taomarketcap public API (anonymous)", "span": args.span,
                "started_utc": started.isoformat(), "files": {}, "skipped": {}}

    netuids = parse_netuids(args.netuids)
    last_call = 0.0
    for i, netuid in enumerate(netuids, 1):
        wait = MIN_INTERVAL_S - (time.monotonic() - last_call)
        if wait > 0:
            time.sleep(wait)
        url = BASE.format(netuid=netuid, span=args.span)
        last_call = time.monotonic()
        status, body = http_get(url)
        if status == 404 or not body:
            manifest["skipped"][str(netuid)] = f"HTTP {status}, empty"
            print(f"[{i}/{len(netuids)}] SN{netuid}: skipped (HTTP {status})")
            continue
        rows = extract_rows(json.loads(body))
        if not rows:
            manifest["skipped"][str(netuid)] = "no rows"
            print(f"[{i}/{len(netuids)}] SN{netuid}: no rows")
            continue
        name = f"sn{netuid:03d}.json"
        (run_dir / name).write_bytes(body)
        manifest["files"][name] = {"netuid": netuid, "url": url, "status": status, "rows": len(rows),
                                   "sha256": hashlib.sha256(body).hexdigest()}
        print(f"[{i}/{len(netuids)}] SN{netuid}: {len(rows)} rows")

    manifest["finished_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    (run_dir / "MANIFEST.json").write_text(json.dumps(manifest, indent=2))
    print(f"\nDone: {len(manifest['files'])} subnets saved, {len(manifest['skipped'])} skipped -> {run_dir}")
    return 0 if manifest["files"] else 1


if __name__ == "__main__":
    sys.exit(main())
