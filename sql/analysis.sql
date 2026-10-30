-- Analysis queries for the newest loaded run. report.py runs each block and writes output/<name>.csv.
-- All queries read the `daily` view: one row per subnet per day.
-- Units: emission_percent is treated as each subnet's share of network emission and is re-normalised
-- per day. Other units (daily_emission, volume_24h) must be checked against the first real run
-- before any ratio between them is interpreted.

-- name: coverage
SELECT netuid, MIN(date) AS first_day, MAX(date) AS last_day, COUNT(*) AS days
FROM daily GROUP BY netuid ORDER BY netuid;

-- name: latest_snapshot
WITH last AS (SELECT netuid, MAX(date) AS d FROM daily GROUP BY netuid)
SELECT d.netuid, d.date, d.emission_percent, d.volume_24h, d.tx_count_24h,
       d.neuron_registrations_24h, d.daily_emission, d.subnet_tao, d.tao_price_usd
FROM daily d JOIN last ON d.netuid = last.netuid AND d.date = last.d
ORDER BY d.emission_percent DESC;

-- name: network_daily
SELECT date, COUNT(*) AS subnets, SUM(volume_24h) AS total_volume_24h, SUM(tx_count_24h) AS total_tx_24h,
       SUM(neuron_registrations_24h) AS registrations_24h, AVG(tao_price_usd) AS tao_price_usd
FROM daily GROUP BY date ORDER BY date;

-- name: concentration_by_day
-- Q1: How concentrated is the reward? Share of the top 10 subnets and the Herfindahl index (HHI).
WITH t AS (
    SELECT date, emission_percent AS e,
           SUM(emission_percent) OVER (PARTITION BY date) AS tot,
           ROW_NUMBER() OVER (PARTITION BY date ORDER BY emission_percent DESC) AS rk
    FROM daily WHERE emission_percent IS NOT NULL
)
SELECT date, COUNT(*) AS subnets,
       ROUND(SUM(CASE WHEN rk <= 10 THEN e ELSE 0 END) / MAX(tot), 4) AS top10_share,
       ROUND(SUM((e / tot) * (e / tot)), 4) AS hhi
FROM t WHERE tot > 0 GROUP BY date ORDER BY date;

-- name: activity_vs_reward_30d
-- Q2: Which subnets show market activity relative to the reward they receive (last 30 days)?
WITH m AS (SELECT MAX(date) AS d FROM daily),
win AS (SELECT daily.* FROM daily, m WHERE date > date(m.d, '-30 day'))
SELECT netuid, COUNT(*) AS days,
       ROUND(AVG(emission_percent), 4) AS avg_emission_pct,
       AVG(volume_24h) AS avg_volume_24h,
       AVG(tx_count_24h) AS avg_tx_count_24h,
       SUM(neuron_registrations_24h) AS registrations_30d,
       CASE WHEN AVG(daily_emission) > 0 THEN AVG(volume_24h) / AVG(daily_emission) END AS volume_to_emission
FROM win GROUP BY netuid ORDER BY avg_emission_pct DESC;

-- name: emission_trend_90d
-- Q3: Who is gaining or losing share? Average of the last 30 days vs days 61-90 back, in percentage points.
WITH m AS (SELECT MAX(date) AS d FROM daily),
recent AS (SELECT netuid, AVG(emission_percent) AS v FROM daily, m WHERE date > date(m.d, '-30 day') GROUP BY netuid),
earlier AS (SELECT netuid, AVG(emission_percent) AS v FROM daily, m
            WHERE date <= date(m.d, '-60 day') AND date > date(m.d, '-90 day') GROUP BY netuid)
SELECT recent.netuid, ROUND(earlier.v, 4) AS earlier_avg, ROUND(recent.v, 4) AS recent_avg,
       ROUND(recent.v - earlier.v, 4) AS change_pp
FROM recent JOIN earlier USING (netuid) ORDER BY change_pp DESC;
