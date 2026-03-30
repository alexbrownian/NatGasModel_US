# Industry Learnings — US Natural Gas & Energy Markets

> Key concepts, delivery points, benchmarks, and market mechanics.
> Built up progressively as the project develops.

---

## Price Benchmarks & Delivery Points

### Henry Hub — `DHHNGSP`
- The primary US natural gas price benchmark
- Physical delivery point in **Erath, Louisiana**, on the Sabine Pipe Line
- Where 13 interstate and 9 intrastate pipelines interconnect — makes it the most liquid physical gas trading location in the US
- Price quoted in **USD/MMBtu** (million British thermal units)
- NYMEX Natural Gas futures are settled against Henry Hub — so when traders say "gas is at $2.50", they mean Henry Hub
- Being a physical point (not a balancing area), prices at other locations trade at a **basis differential** to Henry Hub (e.g. "Algonquin citygate basis" = premium paid in the Northeast in winter)

### WTI Crude — `DCOILWTICO`
- **West Texas Intermediate** — the US crude oil benchmark
- Physical delivery point: **Cushing, Oklahoma** — a major pipeline hub and storage facility
- Quoted in **USD/barrel**
- The "CO" in the FRED series ID stands for Cushing, Oklahoma
- WTI typically trades at a slight discount to Brent (the global benchmark) due to landlocked delivery location — though this spread fluctuates
- Relevant to gas modelling because:
  - **Associated gas:** oil drilling produces gas as a byproduct — high oil prices → more drilling → more gas supply
  - **Fuel switching:** some industrial users can switch between oil and gas
  - **LNG contracts:** many long-term LNG export deals are oil-indexed

### Brent Crude
- Global benchmark, priced at **Sullom Voe terminal, North Sea**
- More relevant for international LNG pricing than domestic US gas
- WTI is the right cross-commodity input for a US Henry Hub model

---

## Storage — The Central Market Driver

### EIA Weekly Storage Report
- Published every **Thursday at 10:30am ET**
- Reports working gas in underground storage for the prior week (ending Friday)
- The single most market-moving data release in US gas — Henry Hub can move 3–5%+ in minutes after the print
- Key number is the **storage surprise**: actual change vs analyst consensus
  - Bigger-than-expected withdrawal (or smaller injection) = **bullish** (less supply in ground)
  - Smaller-than-expected withdrawal (or bigger injection) = **bearish**
- Storage measured in **Bcf** (billion cubic feet)

### Working Gas vs Base Gas
- **Working gas** — the volume that can actually be withdrawn and sold. This is the number the market watches (`SWO` in EIA facets)
- **Base gas** (cushion gas) — permanently held in the reservoir to maintain pressure. Not tradeable
- The EIA report headline is always working gas

### Storage Regions (EIA duoarea codes)
| Code | Region |
|---|---|
| `R48` | Lower 48 states (national total — the headline number) |
| `R31` | East |
| `R32` | Midwest |
| `R33` | Mountain |
| `R34` | Pacific |
| `R35` | South Central |

- South Central matters most because it holds the largest share of US storage capacity, including salt cavern storage (fastest cycling — can inject/withdraw in days vs weeks for depleted fields)

### Injection vs Withdrawal Season
- **Injection season:** April–October — producers refill storage ahead of winter
- **Withdrawal season:** November–March — storage drawn down to meet heating demand
- The **November 1st storage level** is a major seasonal benchmark — the market watches whether storage enters winter above or below the 5-year average

---

## The Shale Revolution

### What It Was
The shale revolution was a structural transformation of US natural gas supply between roughly **2005–2015**, driven by two technologies used together at scale for the first time:

- **Horizontal drilling** — instead of drilling straight down, rigs drill horizontally through shale rock formations for thousands of feet, exposing far more rock surface to the wellbore
- **Hydraulic fracturing ("fracking")** — high-pressure fluid is pumped into the rock to crack it open, releasing gas (or oil) trapped in the shale

Before this, shale rock was known to contain gas but was considered uneconomic — the rock was too tight (low permeability) to flow gas at commercial rates. Horizontal drilling + fracking solved both problems simultaneously.

### The Key Shale Basins for Gas
| Basin | Location | Notes |
|---|---|---|
| **Marcellus** | Pennsylvania / West Virginia | Largest gas basin in the US; transformed Appalachia into a major producing region |
| **Haynesville** | Louisiana / East Texas | High-quality dry gas; one of the lowest-cost basins in the country |
| **Permian** | West Texas | Primarily an oil play — but produces enormous volumes of **associated gas** as a byproduct |
| **Utica** | Ohio / Pennsylvania | Extends the Appalachian fairway; wet gas and dry gas windows |
| **Eagle Ford** | South Texas | Oil + condensate + associated gas |

### What It Did to the Market
- **Before shale (~2000–2008):** US gas was scarce. Production peaked in the 1970s and had been declining. The US was building LNG *import* terminals (to bring gas *in* from Qatar, etc.)
- **After shale (~2009–present):** The US became the world's largest gas producer. Import terminals were converted to *export* terminals. Henry Hub prices collapsed from ~$8 to ~$2–4 — a structural repricing of the entire commodity
- **Consequence for prices:** The shale cost curve created a soft ceiling around $3–4/MMBtu. When prices rise above that level, producers drill more wells; supply increases and prices fall back. This is why 2022 was unusual — the external LNG demand shock overwhelmed the supply response

### Why It Matters for This Model
- A model trained on 2000–2008 data would embed a high-price prior — completely wrong post-2009
- The regime shift is not gradual: there is a visible **structural break** in the price series around 2009 when Marcellus production began ramping at scale
- The shale cost curve (~$2–3/MMBtu for the lowest-cost basins) is the effective downside floor for Henry Hub under normal conditions

---

## Demand Structure

### Two-Season US Gas Market
Unlike most European markets which are heating-dominated, US gas demand has two distinct peaks:
1. **Winter (Nov–Mar):** Residential and commercial heating — driven by HDD
2. **Summer (Jun–Sep):** Power burn — gas-fired generation to meet air conditioning load — driven by CDD

This is why a single temperature feature is insufficient for the US — you need both HDD and CDD separately.

### HDD and CDD — Degree Days
- **Base temperature: 65°F** (US industry standard, ~18°C)
- **HDD (Heating Degree Days)** = `max(0, 65°F − daily mean temp)` — each degree below 65°F = 1 HDD
- **CDD (Cooling Degree Days)** = `max(0, daily mean temp − 65°F)` — each degree above 65°F = 1 CDD
- A day at 45°F = 20 HDD, 0 CDD (heating day)
- A day at 85°F = 0 HDD, 20 CDD (cooling day)
- A day at 65°F = 0 HDD, 0 CDD (no demand from temperature)

### Power Burn
- Gas consumed by power plants to generate electricity
- Has grown significantly as coal plants retired — gas is now the marginal fuel for electricity in most US regions
- Creates a **gas-power price relationship**: when electricity demand spikes (heatwave), gas demand for generation spikes with it
- EIA sector code: electric power consumption (`VCS` process in `natural-gas/cons/sum`)

### LNG Exports — Structural Demand Floor
- Before 2016 the US exported essentially zero LNG
- **Sabine Pass LNG** (Louisiana) started exports in February 2016 — first major US LNG export terminal
- Now ~14 Bcf/day of export capacity — a significant and relatively **inelastic demand floor** (LNG contracts are long-term, terminals run near capacity regardless of Henry Hub price)
- Key event: **Freeport LNG outage (June–December 2022)** — fire knocked out ~2 Bcf/day of export capacity for 6 months, materially bearish for Henry Hub

---

## Pipeline & Flow Concepts

### Associated Gas
- Natural gas produced as a byproduct of oil drilling — not the primary target
- Permian Basin (West Texas) is the largest source of associated gas in the US
- Problem: sometimes more gas comes out than pipelines can handle → **gas flaring** or **negative basis prices** at the wellhead
- When WTI is high → more oil drilling → more associated gas → more supply pressure on Henry Hub

### Basis Differentials
- Henry Hub is the benchmark but gas physically trades at hundreds of other points across the pipeline grid
- **Basis = local price − Henry Hub price**
- Positive basis = local price premium (e.g. Algonquin citygate in winter — pipeline constrained into New England)
- Negative basis = local price discount (e.g. Waha hub in West Texas when Permian gas is stranded)
- Not modelled in this project (Henry Hub only) but important context

### MMBtu vs Mcf vs Bcf vs Tcf
| Unit | Meaning | Scale |
|---|---|---|
| MMBtu | Million British thermal units | Single trade / price unit |
| Mcf | Thousand cubic feet | Small volume |
| MMcf | Million cubic feet | EIA consumption reports |
| Bcf | Billion cubic feet | EIA storage reports |
| Tcf | Trillion cubic feet | Annual production / reserves |
- At ~1,020 BTU/cubic foot: **1 Mcf ≈ 1 MMBtu** (close enough for most purposes)

---

*Updated as new concepts are introduced in the project.*
