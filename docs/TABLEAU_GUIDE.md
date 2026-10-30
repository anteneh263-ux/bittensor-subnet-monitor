# Byggeguide: dashbord i Tableau Public

Mål: ett dashbord med tre visninger som svarer på de tre spørsmålene i README, pluss en tekstboks med funnene.
Regn med 1–2 timer første gang. Tallene i titlene under er fra datahentingen 2026-10-30.

## 0. Forberedelser

1. Last ned **Tableau Public** (gratis) fra public.tableau.com og opprett en gratis konto.
2. Kjør `python3 report.py` slik at `output/` er oppdatert.
3. Merk: alt du lagrer i Tableau Public blir **offentlig**. Det er greit her, fordi dataene allerede er offentlige.

## 1. Koble til dataene

Åpne Tableau Public → **Connect → To a File → Text file** → velg `output/concentration_by_day.csv`.
Legg til de andre som egne datakilder via **Data → New Data Source**:

- `concentration_by_day.csv` (visning 1)
- `activity_vs_reward_30d.csv` (visning 2)
- `emission_trend_90d.csv` (visning 3)

Tips: hvis `netuid` havner under *Measures*, høyreklikk → **Convert to Dimension**. Bruk helst kolonnen `subnet` (SN51 osv.).

## 2. Visning 1 – «Belønningen sprer seg»

Datakilde: `concentration_by_day`

1. Dra `date` til **Columns**. Høyreklikk → velg **Day** (den nederste, kontinuerlige varianten).
2. Dra `top10_share` til **Rows**. Høyreklikk på aksen → **Format** → tall som prosent.
3. Tittel: *De ti største subnetene fikk 71 % av belønningen for et år siden, nå 61 %*.
4. Valgfritt: legg `hhi` på en egen akse (Dual Axis) for å vise samme utvikling med et annet mål.

## 3. Visning 2 – «Aktivitet mot belønning»

Datakilde: `activity_vs_reward_30d`

1. Dra `volume_to_emission` til **Filters** → velg *Special → Non-null values*.
   (Forholdstallet finnes bare for subnets med minst 1 TAO belønning per dag: 62 stykker.)
2. Dra `avg_subnet_emission_tao` til **Columns** og `avg_volume_tao_24h` til **Rows**.
3. Høyreklikk på begge aksene → **Edit Axis → Logarithmic**.
4. Dra `subnet` til **Label** og `volume_to_emission` til **Color**.
5. Tittel: *Median-subnetet omsetter rundt 19 ganger sin daglige belønning (siste 30 dager)*.

## 4. Visning 3 – «Vinnere og tapere»

Datakilde: `emission_trend_90d`. Lag to like ark.

1. Dra `subnet` til **Rows** og `change_pp` til **Columns**.
2. Dra `change_pp` også til **Color**.
3. Ark A: høyreklikk `subnet` → **Filter → Top → By field: Top 10 by change_pp**. Sorter synkende.
4. Ark B: samme, men **Bottom 10**.
5. Titler: *Størst økning i belønningsandel, siste 30 mot 61–90 dager siden* og *Størst nedgang*.
   (Fra hentingen: SN51 +3,3 prosentpoeng, SN107 −4,2.)

## 5. Sett sammen dashbordet

1. **Dashboard → New Dashboard**. Størrelse: *Automatic* eller fast 1200 × 900.
2. Dra inn de fire arkene: visning 1 øverst i full bredde, visning 2 under til venstre, visning 3 A og B til høyre.
3. Legg til en **Text**-boks øverst med:
   - Spørsmålet: *Hvilke Bittensor-subnets har reell aktivitet, og hvilke lever mest på belønninger?*
   - De tre funnene i hver sin setning.
   - Kilde og forbehold: *Data: TaoMarketCap public API, 2025-10-30 til 2026-10-30. Beskrivende analyse, ikke investeringsråd.*
   - Lenke til GitHub-repoet når det er publisert.

## 6. Publiser

**File → Save to Tableau Public**. Gi dashbordet en tydelig tittel, for eksempel
*Bittensor Subnet Monitor – who earns and who is active*. Kopier lenken; den skal i README, CV og søknader.
