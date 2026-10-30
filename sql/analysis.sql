-- Analysis queries for the newest loaded run. report.py runs each block and writes output/<name>.csv.
-- All queries read the `daily` view: one row per subnet per day, amounts converted from rao to TAO.
-- Checked on the first real fetch (2026-10-30, SN1-5): amounts are in rao; daily_emission is the same for
-- every subnet (network-wide, 7 200 TAO); emission_percent is a percentage (SN4 = 7.2). It should sum to
-- about 100 per day across all subnets: see `emission_share_check`. On the full fetch it sums to a median of
-- 94.7 (SN0 and deregistered subnets are missing), so Q1 re-normalises per day. Days summing to 0 are excluded.

-- name: emission_share_check
-- Data quality: does emission_percent sum to ~100 across subnets each day? Rows far from 100 need a look.
SELECT date, COUNT(*) AS subnets, ROUND(SUM(emission_percent), 4) AS percent_sum,
       MAX(network_emission_tao) AS network_emission_tao, MIN(network_emission_tao) AS min_network_emission_tao
FROM daily GROUP BY date ORDER BY date;

-- name: coverage
SELECT netuid, MIN(date) AS first_day, MAX(date) AS last_day, COUNT(*) AS days
FROM daily GROUP BY netuid ORDER BY netuid;

-- name: latest_snapshot
WITH last AS (SELECT netuid, MAX(date) AS d FROM daily GROUP BY netuid)
SELECT d.netuid, d.date, ROUND(d.emission_percent, 4) AS emission_pct,
       ROUND(d.subnet_emission_tao, 2) AS subnet_emission_tao, ROUND(d.volume_tao_24h, 2) AS volume_tao_24h,
       d.tx_count_24h, d.neuron_registrations_24h, ROUND(d.subnet_tao_pool, 2) AS subnet_tao_pool, d.tao_price_usd
FROM daily d JOIN last ON d.netuid = last.netuid AND d.date = last.d
ORDER BY d.emission_percent DESC;

-- name: network_daily
SELECT date, COUNT(*) AS subnets, ROUND(SUM(volume_tao_24h), 2) AS total_volume_tao_24h,
       SUM(tx_count_24h) AS total_tx_24h, SUM(neuron_registrations_24h) AS registrations_24h,
       MAX(network_emission_tao) AS network_emission_tao, AVG(tao_price_usd) AS tao_price_usd
FROM daily GROUP BY date ORDER BY date;

-- name: concentration_by_day
-- Q1: How concentrated is the reward? Share of the top 10 subnets and the Herfindahl index (HHI),
-- re-normalised per day so it does not depend on the percentages summing exactly to 100.
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
-- Q2: Market activity relative to the estimated reward a subnet receives (last 30 days, in TAO).
WITH m AS (SELECT MAX(date) AS d FROM daily),
win AS (SELECT daily.* FROM daily, m WHERE date > date(m.d, '-30 day'))
SELECT netuid, 'SN' || netuid AS subnet, COUNT(*) AS days,
       ROUND(AVG(emission_percent), 4) AS avg_emission_pct,
       ROUND(AVG(subnet_emission_tao), 2) AS avg_subnet_emission_tao,
       ROUND(AVG(volume_tao_24h), 2) AS avg_volume_tao_24h,
       ROUND(AVG(tx_count_24h), 1) AS avg_tx_count_24h,
       SUM(neuron_registrations_24h) AS registrations_30d,
       -- ratio only where the reward is at least 1 TAO/day; below that it is dominated by noise
       CASE WHEN AVG(subnet_emission_tao) >= 1
            THEN ROUND(AVG(volume_tao_24h) / AVG(subnet_emission_tao), 3) END AS volume_to_emission
FROM win GROUP BY netuid ORDER BY avg_emission_pct DESC;

-- name: emission_trend_90d
-- Q3: Who is gaining or losing share? Average of the last 30 days vs days 61-90 back, in percentage points.
WITH m AS (SELECT MAX(date) AS d FROM daily),
recent AS (SELECT netuid, AVG(emission_percent) AS v FROM daily, m WHERE date > date(m.d, '-30 day') GROUP BY netuid),
earlier AS (SELECT netuid, AVG(emission_percent) AS v FROM daily, m
            WHERE date <= date(m.d, '-60 day') AND date > date(m.d, '-90 day') GROUP BY netuid)
SELECT recent.netuid, 'SN' || recent.netuid AS subnet, ROUND(earlier.v, 3) AS earlier_pct, ROUND(recent.v, 3) AS recent_pct,
       ROUND(recent.v - earlier.v, 3) AS change_pp
FROM recent JOIN earlier USING (netuid) ORDER BY change_pp DESC;

-- name: subnet_daily_dashboard
-- Tidy table for the dashboard: one row per subnet per day, with a label and the share re-normalised
-- over the subnets present that day (see the coverage note at the top of this file).
SELECT date, netuid, 'SN' || netuid AS subnet,
       ROUND(emission_percent, 4) AS emission_pct,
       ROUND(100 * emission_percent / SUM(emission_percent) OVER (PARTITION BY date), 4) AS emission_share_pct,
       ROUND(subnet_emission_tao, 3) AS subnet_emission_tao,
       ROUND(volume_tao_24h, 3) AS volume_tao_24h,
       tx_count_24h, neuron_registrations_24h, ROUND(subnet_tao_pool, 3) AS subnet_tao_pool, tao_price_usd
FROM daily ORDER BY date, netuid;
