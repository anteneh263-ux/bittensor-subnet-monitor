# Bittensor Subnet Monitor

A small data pipeline and analysis of the Bittensor network's subnets, built the way an analytics
consultant would deliver it: a business question first, then data, SQL, a dashboard and a one-page memo.

> Descriptive analysis only. Nothing here is investment advice or a recommendation to buy, stake in or
> mine any subnet or token.

## Dashboard

**[Open the interactive dashboard on Tableau Public](https://public.tableau.com/app/profile/anteneh.hailu/viz/Book1bittensorsubnet/Overview)**

One page, three views, built from the CSV files in `output/`:

- **Concentration**: monthly average share of emission going to the 10 largest subnets (rose from about 48% to 60-68%).
- **Activity versus reward**: daily trading volume against daily reward per subnet, last 30 days (log scales).
- **Winners and losers**: change in emission share, last 30 days versus 61-90 days ago, for subnets that moved at least 1 point.

## The question

Bittensor is a decentralised network where independent *subnets* produce digital services (inference,
compute, storage, prediction) and are rewarded in the TAO token. A client considering the ecosystem would
ask: **which subnets show real activity and sustainable economics, and which mainly live on rewards?**

Three sub-questions, fixed before looking at the data:

1. **Concentration** — how much of the network's emission goes to the top 10 subnets, and is that rising or falling?
2. **Activity versus reward** — which subnets show trading and transaction activity in proportion to the reward they receive?
3. **Momentum** — which subnets gained or lost emission share over the last 90 days?

## Data

[TaoMarketCap public API](https://api.taomarketcap.com), endpoint `GET /public/v1/analytics/subnet/{netuid}/`,
anonymous tier (no key; 10 requests/minute). With `span=ALL` it returns up to 365 daily end-of-day rows per
subnet: emission share, buy/sell volume, transactions, registrations, supply, emission and TAO price.

Every fetch is saved untouched with a SHA-256 manifest, and the database refuses to load a raw file that has
changed since it was fetched.

## Pipeline

```
fetch.py  ──▶  data/raw/<run>/*.json + MANIFEST.json      (Python, standard library only)
build_db.py ─▶ data/subnets.db  (SQLite: runs, subnet_daily, views latest + daily)
report.py ──▶  output/*.csv     (one file per query in sql/analysis.sql)
                     │
                     ▼
              dashboard (Power BI / Tableau Public / Looker Studio) + one-page memo
```

## Run it

Requires Python 3.10+. No packages to install.

```sh
python3 fetch.py --netuids 1-5     # quick check (about 30 seconds)
python3 fetch.py                   # all subnets, about 15 minutes
python3 build_db.py
python3 report.py
python3 -m unittest -v             # tests on synthetic data, no network
```

## Outputs (`output/`)

| File | Answers |
| --- | --- |
| `concentration_by_day.csv` | Q1: top-10 share and Herfindahl index (HHI) per day, quality-checked days only |
| `concentration_quality.csv` | Data-quality flag per day for Q1 (`quality_ok`) |
| `concentration_by_month.csv` | Q1: monthly averages over quality-checked days |
| `activity_vs_reward_30d.csv` | Q2: 30-day volume, transactions and registrations per subnet next to its emission |
| `emission_trend_90d.csv` | Q3: change in emission share, last 30 days versus 61–90 days back |
| `latest_snapshot.csv` | Latest day per subnet |
| `network_daily.csv` | Network totals per day |
| `coverage.csv` | Days of data per subnet (data-quality check) |
| `subnet_daily_dashboard.csv` | Tidy daily table per subnet for the dashboard |
| `emission_share_check.csv` | Sum of emission percent per day (data-quality check) |

## Limitations

- One third-party source. Figures are not cross-checked against the chain itself yet.
- Amounts are converted from rao to TAO (1 TAO = 1e9 rao). `daily_emission` is network-wide, so a subnet's
  reward is estimated as `emission_percent / 100 × daily_emission`.
- `daily_emission` reads 7 200 TAO for the whole year, although a halving of network emission was reported for
  December 2025. Treat absolute TAO reward figures as unverified until checked against a second source.
- Emission percentages sum to less than 100 on most days (median 94.7, about 50 a year ago), because the root
  network (SN0) returns no data and subnets that were deregistered during the year are not in the source.
  The first day has 87 subnets, the last 128. Concentration measures are therefore re-normalised per day and
  describe the subnets present in the data, not the whole network.
- Two data-quality rules, fixed on 2026-10-30 after the first full fetch: a day is used for Q1 only if emission
  percent sums to at least 80 and at least 30 subnets have a share above zero. 40 of 366 days fail, mostly
  2025-10-30 to 2025-12-16 (sums of about 50 that look like a different recording) and three days in June 2026.
- History is limited to the last 365 days the API returns; subnets that were deregistered may be missing.
- Activity is not the same as usefulness: trading volume can be speculative.

## Status

- [x] Pipeline, SQL and tests
- [x] First full fetch and data-quality check (2026-10-30: 128 subnets, 39 342 daily rows)
- [ ] Dashboard (Tableau Public; build guide in `docs/TABLEAU_GUIDE.md`)
- [ ] One-page memo with three findings
