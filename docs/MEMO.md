# Bittensor subnets: who earns the rewards, and is there activity behind them?

*One-page memo · data to 30 Oct 2026 · [interactive dashboard](https://public.tableau.com/app/profile/anteneh.hailu/viz/Book1bittensorsubnet/Overview)*

> Descriptive analysis only. Nothing here is investment advice or a recommendation to buy, stake in or mine any subnet or token.

## Summary

Network rewards (emission) are flowing to fewer subnets. The ten largest now receive 60–68% of emission, up from about 48% a year ago. The subnets that earn the most also trade the least relative to their reward. Over the last 90 days, the top of the table has been reshuffling: a few large subnets lost share and a group of small ones gained.

## 1. Concentration is rising

| | Nov 2025 | Mar 2026 | Aug 2026 | Oct 2026 |
| --- | --- | --- | --- | --- |
| Top-10 share of emission | 47.5% | 64.3% | 68.2% | 60.0% |
| Herfindahl index (HHI) | 0.035 | 0.087 | 0.060 | 0.054 |

The jump happened between January and March 2026. Since then the top-10 share has moved in a 58–68% band. HHI peaked in March, when a single subnet dominated, and has eased since. The rewards are now spread across the top ten rather than going to a single leader, but they still sit within that small group.

## 2. The biggest earners trade the least relative to their reward

Among the 62 subnets that earned at least 1 TAO per day over the last 30 days, the median subnet trades about **19×** its daily reward. Half of them fall between 7× and 111×.

The largest earners sit at the bottom of that range. SN51 (14% of emission) trades 7.4× its reward, SN64 3.5×, SN4 7.0×, SN120 5.6× and SN107 6.0×. Of the ten largest earners, only SN53 (28×) and SN28 (32×) are above the median.

The large earners may depend more on rewards than on outside demand. But trading volume is a rough proxy: it says nothing about whether the service a subnet produces is used.

## 3. Momentum: the top of the table is shifting

Comparing the last 30 days with 61–90 days ago:

- **Gainers:** SN51 (+3.3 points, 10.7% → 14.0%), SN80 (+3.0, from almost zero), SN90 (+2.4, from zero) and SN28 (+2.0).
- **Losers:** SN107 (−4.2, 8.8% → 4.5%), SN64 (−2.6), SN97 (−2.0), SN120 (−1.7), SN44 (−1.3) and SN15 (−1.1).

Two subnets went from almost no emission to 2–3% within three months. The share at the top is not locked in, even though concentration is high.

## Caveats

- One third-party source (TaoMarketCap public API), not yet cross-checked against the chain.
- Absolute TAO rewards rest on a network emission figure that did not change through a reported halving. Shares and ratios are more reliable than TAO amounts.
- 40 of 366 days fail the data-quality rules and are left out of the concentration figures. Deregistered subnets and the root network (SN0) are missing from the source.
- Trading volume can be speculative. High activity does not mean a subnet is useful.

## Suggested next steps

1. Cross-check emission and the halving against an on-chain source.
2. Add a usage measure beyond trading, such as validator queries or miner counts.
3. Re-run monthly and watch whether the 58–68% band holds.
