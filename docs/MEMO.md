# Bittensor subnets: where do the rewards go, and is there activity behind them?

*One-page memo · data to 30 Oct 2026 · updated 1 Nov 2026 · [interactive dashboard](https://public.tableau.com/app/profile/anteneh.hailu/viz/Book1bittensorsubnet/Overview) · figures from `sql/analysis.sql`*

> Descriptive analysis only. Nothing here is investment advice or a recommendation to buy, stake in or mine any subnet or token.

## Summary

Among the subnets in the data, network emission has become more concentrated. The ten largest receive 60–68% of it in most months since March 2026, against about 48% in November 2025. Several of the subnets with the largest emission share have low trading volume relative to their estimated reward. Over the last 90 days, a few large subnets lost share and a group of small ones gained.

## 1. Concentration is rising among the subnets in the data

| | Nov 2025 | Mar 2026 | Aug 2026 | Oct 2026 |
| --- | --- | --- | --- | --- |
| Top-10 share of emission | 47.5% | 64.3% | 68.2% | 60.0% |
| Herfindahl index (HHI) | 0.035 | 0.087 | 0.060 | 0.054 |
| Valid days in the month | 11 of 30 | 31 of 31 | 31 of 31 | 30 of 30 (data ends 30 Oct) |

**How it is measured:** monthly averages of daily values. Each day's shares are re-normalised so they sum to 100% across the subnets in the data. The root network (SN0) and deregistered subnets are missing from the source, so this is a share of the subnets present, not of the whole network. Only days that pass both data-quality rules are used: emission percent sums to at least 80, and at least 30 subnets have a share above zero.

**Caveat:** November 2025 rests on 11 valid days, and December 2025 on 15 of 31. The starting point is therefore less certain than the later months.

The increase came between January and March 2026. Since then the top-10 share has stayed between 58% and 68%. HHI peaked in March and has eased since, so the emission is now spread across the top ten rather than going to one leader.

## 2. Several of the subnets with the largest emission share have low trading volume relative to estimated reward

**Measure:** average 24-hour trading volume divided by the estimated daily reward, both in TAO, over the last 30 days (1–30 Oct 2026). Estimated reward = emission share × network emission. This says nothing about profit.

**Network emission:** the API reports 7 200 TAO per day all year. The first halving cut issuance to 3 600 TAO per day around 14 December 2025 ([The Block](https://www.theblock.co/post/381638/bittensors-halving-tao-price), [Forklog](https://forklog.com/en/bittensor-token-drops-8-following-first-halving/)). The estimates below use 3 600, so they are half of what the API implies.

**Population:** the 55 subnets with an estimated reward of at least 1 TAO per day. Among them the **median** ratio is about 32, and half fall between 14 and 204.

Among the five largest by emission share, the ratio is between 6.9 and 14.9: SN51 14.9, SN64 6.9, SN4 13.9, SN120 11.2, SN107 12.1. Of the ten largest, only SN53 (57) and SN28 (64) are above the median. A low ratio does not mean low trading in total. SN51 has the fourth-highest absolute volume of the 55.

**What the correction changed:** with the API figure of 7 200 TAO per day, the same measure gave 62 subnets, a median of 19 and 3.5–7.4 for the five largest. Halving the reward doubles every ratio, so the ranking of a given subnet stays the same. But the 1 TAO cut-off now excludes seven more subnets, so the median does not simply double. The pattern in this finding holds under both figures.

**Still an estimate:** the halving date comes from press reports, not the chain, and each subnet's reward is derived from its share rather than read on-chain.

## 3. Momentum: average share, last 30 days versus 61–90 days back

**Measure:** each subnet's average daily emission percent over the last 30 days (1–30 Oct 2026) minus its average over days 61–90 back (2–31 Aug 2026), in percentage points. This compares two monthly averages, not two single dates. It uses raw emission percent as reported, without re-normalisation or the quality filter. All 60 days in the two windows pass the quality rules, but that does not mean coverage is complete: SN0 and deregistered subnets are still missing from the source, and emission percent sums to between 98.2 and 100.5 on those days rather than exactly 100.

- **Largest gains:** SN51 (+3.3, 10.7% → 14.0%), SN80 (+3.0, from almost zero), SN90 (+2.4, from zero) and SN28 (+2.0).
- **Largest losses:** SN107 (−4.2, 8.8% → 4.5%), SN64 (−2.6), SN97 (−2.0), SN120 (−1.7), SN44 (−1.3) and SN15 (−1.1).

Two subnets went from almost no emission to 2–3% between the two windows. High concentration does not mean the same subnets stay at the top.

## Caveats

- One third-party source (TaoMarketCap public API), not yet cross-checked against the chain.
- Absolute TAO rewards use the published halving schedule (3 600 TAO per day since about 14 Dec 2025), not the API's 7 200. Shares and rankings are more reliable than absolute TAO amounts.
- History is limited to the 365 days the API returns. Deregistered subnets and SN0 are missing.
- Trading volume can be speculative. It is a rough proxy for demand, not for usefulness.

## Suggested next steps

1. Confirm the halving block and per-subnet emission on-chain, then recompute finding 2.
2. Add a usage measure beyond trading, such as validator queries or miner counts.
3. Re-run monthly and watch whether the 58–68% range holds.
