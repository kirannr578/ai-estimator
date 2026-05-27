# Price references — TAMU Wehner 2025-06871

> Rule-of-thumb $/SF and $/LF benchmarks for office / seminar / faculty-area renovation in TAMU System work (Brazos County, TX). Refined estimates require drawing-based takeoff (see `takeoff-template.json`). These benchmarks are sourced from public construction-cost databases (RSMeans 2026, USCensusRS), regional TAMU System cost reports, and BPC's CWICR matcher (where applicable). All numbers in 2026 USD.

---

## 1. Total project envelope (lump-sum)

For a multi-room (4-room combined) seminar expansion of approximately **1,200-2,000 SF** with MARRS glazing, MEP modifications, and finishes:

| Estimate basis | Low | Mid | High |
|---|---:|---:|---:|
| Per-SF (TAMU System office/seminar reno benchmark) | $50/SF | $90/SF | $150/SF |
| For 1,500 SF (estimated combined room area) | $75,000 | $135,000 | $225,000 |
| With MARRS glazing premium (~$25K-$50K) | $100,000 | $160,000 | $275,000 |

**BPC target range:** $100,000–$200,000 lump-sum (mid-pack pricing aimed at competitive positioning).

## 2. Per-trade benchmarks

### Demolition (Division 02)

| Item | Unit | $/Unit (range) | Notes |
|---|---|---:|---|
| Partition demo | LF | $20-$45 | Includes haul-off |
| Casework removal | LF | $25-$60 | Includes haul-off |
| Carpet tile demo | SF | $1.50-$3.00 | |
| Ceiling demo | SF | $2.00-$4.00 | |
| Disposal at landfill | LS | $1,500-$3,500 | For multi-room project |

### Carpentry / Wood (Division 06)

| Item | Unit | $/Unit | Notes |
|---|---|---:|---|
| Rough carpentry / blocking | LF | $8-$15 | Per-LF installed |
| Trim / casing | LF | $10-$20 | |

### Doors + Glazing (Division 08)

| Item | Unit | $/Unit | Notes |
|---|---|---:|---|
| **MARRS architectural glass wall (installed)** | LF | $300-$600 | Glass-pane + frame + hardware + installation labor. Premium per LF compared to standard glazing (~$100/LF) |
| **MARRS glass-wall door** | EA | $4,000-$8,000 | Includes hardware |
| Standard hollow-metal door + frame | EA | $1,200-$2,500 | If scope |
| Door hardware (locks, closer, hinges, ADA) | EA | $400-$1,200 | |

### Finishes (Division 09)

| Item | Unit | $/Unit | Notes |
|---|---|---:|---|
| Carpet tile (Shaw or comparable) | SF | $5-$12 | Includes material + installation |
| LVT (Mannington / Tarkett or comparable) | SF | $8-$18 | Includes material + installation |
| 6" rubber base | LF | $4-$8 | Includes material + installation |
| Acoustic ceiling tile (2×2) | SF | $4-$7 | Includes grid + tile + installation |
| Gypsum board (5/8" type X) | SF | $3-$6 | Material + installation |
| Tape, bed, texture | SF | $1.50-$3.00 | |
| Paint (primer + 2 coats) | SF | $1.20-$2.50 | |

### Mechanical / HVAC (Division 21-23)

| Item | Unit | $/Unit | Notes |
|---|---|---:|---|
| HVAC re-balance (single room) | LS | $2,500-$6,000 | |
| New supply diffuser (incl. ductwork tap) | EA | $400-$900 | |
| Plumbing cap-in-place (sink) | EA | $400-$800 | Includes shut-off + cap |

### Electrical (Division 26)

| Item | Unit | $/Unit | Notes |
|---|---|---:|---|
| New circuit (20A) including conduit + wire | EA | $300-$650 | Per home-run |
| LED 2x2 troffer fixture (installed) | EA | $350-$650 | Includes wiring |
| Duplex outlet (new circuit) | EA | $90-$200 | Per outlet |
| Switch (new install) | EA | $90-$200 | |

### Communications (Division 27)

| Item | Unit | $/Unit | Notes |
|---|---|---:|---|
| Data drop (cat6 home-run) | EA | $250-$500 | |
| AV rough-in coordination | LS | $1,500-$3,500 | Coordinates with TAMU IT |

---

## 3. Davis-Bacon vs. Brazos County prevailing wage

This is **TAMU System state work**, not federal. Brazos County prevailing wage rates apply per Tex. Gov't Code Ch. 2258.

- Brazos County rates are moderate; uplift on labor costs is **~15-20% over open-shop rates** (much less than the 50-75% uplift typical of Davis-Bacon in major metros)
- Confirm exact rates from CSP package (typically Brazos County WD attached)
- Specialty subs (electrical, plumbing, HVAC) typically self-administer wage compliance and reflect prevailing-wage labor in their quoted rates

## 4. Build-up summary (placeholder lump-sum target)

| Cost element | Estimated $ | Notes |
|---|---:|---|
| Direct labor (BPC self-perform: paint, drywall, demo) | $15,000-$25,000 | At Brazos prevailing wage |
| Sub costs (MARRS glazing, electrical, plumbing, HVAC, flooring, ceiling) | $50,000-$110,000 | Awaiting sub quotes |
| Materials (drywall, paint, flooring buys, ceiling) | $8,000-$20,000 | |
| Equipment (drywall, lift, etc.) | $1,500-$3,500 | |
| Mobilization + site setup | $2,500-$5,000 | |
| Subtotal direct costs | $77,000-$163,500 | |
| 8% GC overhead | $6,160-$13,080 | |
| 7% GC profit | $5,800-$12,360 | |
| 10% contingency (multi-trade reno + missed-pre-proposal uncertainty) | $9,000-$19,000 | |
| Performance + Payment Bond | $1,500-$3,500 | 0.75-1.5% of contract value |
| Insurance (project-specific GL surcharge) | $1,000-$2,500 | |
| **TOTAL LUMP-SUM TARGET** | **$100,460-$213,940** | **Recommended target: $145,000-$175,000** |

> **Pricing strategy:** Aim for lump-sum in the **$145K-$175K range** for competitive mid-pack positioning. If pricing comes in below $130K, double-check sub quote completeness (likely missing something). If above $200K, identify cost overruns and trim.

## 5. CWICR matcher placeholder

For each line item above, the CWICR matcher (`scripts/cwicr_match.py` if available) can be run against TAMU-area cost data to refine $/unit:

```
python scripts/cwicr_match.py --bid bids/tamu-wehner-fin-340E-2025-06871 --region "Brazos County, TX" --year 2026
```

(Output will be a JSON file with refined $/unit estimates that can be reconciled with sub quotes.)

## 6. Sub-quote tracking

When sub quotes come in (target Fri 2026-06-05 EOD), populate this table:

| Trade | Sub | HUB | Quote $ | Quote received |
|---|---|---|---:|---|
| MARRS glazing | TBD | TBD | TBD | TBD |
| Electrical | TBD | TBD | TBD | TBD |
| Plumbing | TBD | TBD | TBD | TBD |
| HVAC | TBD | TBD | TBD | TBD |
| Flooring | TBD | TBD | TBD | TBD |
| Acoustic ceiling | TBD | TBD | TBD | TBD |
| Casework demo | TBD | TBD | TBD | TBD |
