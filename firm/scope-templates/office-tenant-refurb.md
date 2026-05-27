# Scope Template — Office / Lab / Classroom Interior Refurbish

> **Source bids mined:** TAMU Harrington Lab 303 (single educational lab, ~1,200 SF), B1710 Refurbish (USAF office space, multi-room), TAMU Wehner Finance Suite (multi-room office reno; partial — in-flight).
>
> **Typical CSI divisions touched:** 01, 02, 06, 08, 09, 10, 11 (lab only), 21 (sprinkler mods), 22, 23, 26, 27, 28.

## 1. Scope outline (standard sequencing)

| # | Phase | Trade(s) | Typical duration (1-room ~1,200 SF) | Typical duration (multi-room ~5,000 SF) |
|---|---|---|---|---|
| 1 | Mobilization + temp protection | GC | 3 days | 5 days |
| 2 | Selective demolition | Demo sub | 3–5 days | 1–2 weeks |
| 3 | Abatement (if triggered by pre-1981 building) | Licensed abatement sub | Plus 1–2 weeks if triggered | Plus 2–4 weeks |
| 4 | Rough MEP (plumbing rough-in, electrical rough, HVAC rough, fire-sprinkler mods) | Plumber, electrician, HVAC, fire-sprinkler subs | 1–2 weeks (parallel) | 2–4 weeks (parallel) |
| 5 | Framing + drywall (one side) | Drywall sub | 3–5 days | 1–2 weeks |
| 6 | In-wall inspections (electrical, plumbing, framing) | AHJ | 1–2 days | 1 week |
| 7 | Drywall close + tape + texture + prime | Drywall sub | 3–5 days | 1–2 weeks |
| 8 | Casework / millwork install (lab base + wall cabinets, ed-grade casework) | Casework sub | 3–5 days | 1–2 weeks |
| 9 | Door / frame / hardware install | Carpenter | 1–2 days | 3–5 days |
| 10 | Acoustic ceiling grid + tile | ACT sub | 2–3 days | 1 week |
| 11 | Flooring (LVT, sheet vinyl, base) | Flooring sub | 2–3 days | 1 week |
| 12 | Paint (1 coat primer + 2 finish) | Paint sub | 3–5 days | 1–2 weeks |
| 13 | MEP trim (devices, fixtures, registers, sprinkler heads, plumbing trim) | Each MEP sub | 3–5 days (parallel) | 1 week (parallel) |
| 14 | Specialty (lab gas + utility hookups, AV, lab equipment connection) | Lab specialty sub | 3–5 days | 1–2 weeks |
| 15 | Punch list + final clean | GC | 3–5 days | 1 week |
| 16 | Closeout (O&M manuals, as-builts, warranties, training) | GC | 1 week | 2 weeks |
| **Total** | | | **6–8 weeks** | **12–16 weeks** |

## 2. Standard takeoff-item list

Use this as the seed for the takeoff-template JSON and for the room-by-room takeoff sheet.

### 2.1 Per-room items (repeat per room)

```
ROOM <NAME / NUMBER>
  Demolition
    □ Demo existing flooring (LF perimeter + SF)
    □ Demo existing base (LF)
    □ Demo existing ceiling tile + grid (SF)
    □ Demo existing casework (LF base + LF wall)
    □ Demo existing doors + frames (each)
    □ Demo existing partition walls (LF)
    □ Demo existing plumbing fixtures (each)
    □ Demo existing electrical devices (each)
    □ Patch + match existing finishes outside scope footprint (SF wall, SF floor)
    □ Haul + disposal (LF + tonnage estimate)
  Framing + drywall
    □ New 3-5/8" metal-stud partition (LF + height)
    □ 5/8" Type X drywall, one side (SF)
    □ 5/8" Type X drywall, both sides (SF, where rated)
    □ Tape + texture + prime (SF)
    □ In-wall blocking for casework + grab bars (LF)
  Casework / millwork
    □ Plastic-laminate base cabinets (LF)
    □ Plastic-laminate wall cabinets (LF)
    □ Plastic-laminate countertop (LF) — verify epoxy / phenolic if lab
    □ Sink + faucet (each) — verify lab / ADA
  Doors / frames / hardware
    □ HM frames (each)
    □ Solid-core wood door (each) — verify rating
    □ Door hardware sets per spec (each)
    □ Cardreader / electric strike preps (each)
  Ceilings
    □ ACT grid + 2x2 or 2x4 lay-in tile (SF)
    □ GWB hard-lid ceiling (SF)
    □ Ceiling hatch (each)
  Flooring
    □ LVT (SF) — verify spec brand + thickness
    □ Sheet vinyl with welded seams (SF) — lab / wet rooms
    □ Sealed concrete (SF) — service rooms
    □ Rubber base (LF) — height per spec (typ 4" or 6")
    □ Walk-off mat at entry (SF)
  Paint
    □ Egg-shell latex on walls (SF) — 1 coat primer + 2 finish
    □ Semi-gloss on door + frame (each)
    □ Flat or eggshell on ceiling (SF) — verify GWB ceilings
  Electrical
    □ Receptacles 20A — standard (each)
    □ Receptacles 20A — quad / surge (each)
    □ Switch (each)
    □ Data jack box + conduit (each)
    □ LED 2x2 or 2x4 troffer (each)
    □ Occupancy sensor (each)
    □ Whip + connection to existing panel
  HVAC
    □ Modify supply diffusers (each)
    □ Modify return grilles (each)
    □ Add VAV box (each, if zoning change)
    □ Reroute branch ductwork (LF)
    □ T-stat (each)
  Plumbing
    □ Sink rough-in (each)
    □ Sink final trim (each)
    □ Eyewash (each, if lab)
    □ Floor drain (each, if wet)
  Fire sprinkler
    □ Modify sprinkler heads to match new layout (each)
    □ Hydrostatic test
  Low-voltage
    □ Cat 6A pull to data closet (per drop, LF)
    □ Telecom backbone if any
  Lab specialty (lab rooms only)
    □ Lab gas drop (each) — verify gas type
    □ Specialty utility (DI water, vacuum, compressed air) connection (each)
    □ Fume hood connection (each, if existing relocated; new hood likely OFOI)
```

### 2.2 Project-wide items (count once)

```
PROJECT-WIDE
  General conditions
    □ Site supervision (super + asst super hours)
    □ PM hours
    □ Temp barricades + dust protection
    □ Temp power + lighting (if existing inadequate)
    □ Temp HVAC (if existing must be shut down)
    □ Daily clean + final clean
    □ Dumpster + waste haul
    □ Building access coordination (key card, escort hours)
  Submittals
    □ Submittal log + binders
    □ Shop drawings (casework, doors / frames / hardware, mechanical, electrical fixture cuts)
    □ Mockups (paint, flooring) if required
  Testing / commissioning
    □ Sprinkler hydrostatic test
    □ HVAC air-balance report
    □ Electrical megger / continuity test
    □ Cx hours (if Cx is required by spec)
  Closeout
    □ As-built drawings (red-line + final)
    □ O&M manuals
    □ Warranty letters
    □ Owner training (typ 1–4 hours per system)
    □ Final cleaning
    □ Punch list resolution + AHJ + owner walk-throughs
```

## 3. Default unit rates + waste factors

> **Source:** seeded from `config/cost_database.json`. **Refresh per project against current sub quotes + last-3 actuals.**

| Item | Unit | Base unit rate (TX, 2025) | Waste factor | CSI ref |
|---|---|---|---|---|
| Selective interior demo | SF | $4 – $7 | n/a | 02 41 19 |
| Asbestos abatement (if triggered) | SF | $8 – $15 | n/a | 02 82 13 |
| 3-5/8" metal-stud partition, full height | LF | $14 – $18 | 5% | 09 22 16 |
| 5/8" Type X drywall, one side | SF | $1.80 – $2.50 | 10% | 09 29 00 |
| Tape + texture + prime | SF | $1.60 – $2.20 | 5% | 09 29 00 |
| Acoustic ceiling tile + grid (2x4 standard) | SF | $4.50 – $6.50 | 8% | 09 51 23 |
| Hard-lid GWB ceiling | SF | $9 – $14 | 8% | 09 22 16 + 09 29 00 |
| LVT, mid-grade | SF | $5 – $8 | 8% | 09 65 19 |
| Sheet vinyl with welded seams | SF | $9 – $14 | 8% | 09 65 16 |
| Rubber base, 4" coved | LF | $3.50 – $5 | 5% | 09 65 13 |
| Solid-core wood door + HM frame + hardware (passage) | each | $1,200 – $1,800 | n/a | 08 14 16 + 08 11 13 + 08 71 00 |
| Plastic-laminate base cabinet | LF | $250 – $450 | n/a | 06 41 00 |
| Plastic-laminate wall cabinet | LF | $180 – $320 | n/a | 06 41 00 |
| Plastic-laminate countertop | LF | $80 – $140 | n/a | 06 61 00 |
| Egg-shell latex paint, walls (1 prime + 2 finish) | SF | $1.60 – $2.40 | 10% | 09 91 23 |
| 20A duplex receptacle, MC drop | each | $180 – $260 | n/a | 26 27 26 |
| LED 2x4 troffer, install + control wiring | each | $280 – $420 | n/a | 26 51 19 |
| Data jack box + 1" EMT to ceiling | each | $90 – $140 | n/a | 27 11 00 |
| Sprinkler-head modification | each | $280 – $450 | n/a | 21 13 13 |
| Diffuser modification | each | $180 – $320 | n/a | 23 37 13 |
| Sink rough-in (waste + supply + vent) | each | $1,400 – $2,200 | n/a | 22 41 00 |

**Apply 8–12% GC + 5–7% contingency + 8–10% OH + 5–7% profit on top** for state-CSP institutional work; tighten to **3–5% contingency + 7–9% OH + 5–7% profit** for federal LPTA where past performance + bonding capacity is the moat.

## 4. Typical sub trades

| Trade | Typical share of contract | Typical sub vetting bar |
|---|---|---|
| Demolition | 5–8% | TX HUB pool deep; pick local |
| Drywall + framing | 5–8% | Often combined with paint |
| Casework / millwork | 7–12% | Specialty; vet for lab-grade (epoxy / phenolic countertops) if applicable |
| Doors / frames / hardware | 3–5% | Material-only often via distributor; install by carpenter |
| Acoustic ceilings | 2–4% | Quick sub; often combined with drywall sub |
| Flooring | 4–7% | LVT + base + sheet vinyl; verify lab-grade welded-seam capability if lab |
| Paint | 3–5% | TX HUB pool deep; pick crew with institutional experience |
| Electrical | 10–15% | Lab / classroom familiarity required if lab |
| HVAC | 6–10% | VAV / DDC controls familiarity required |
| Plumbing | 3–8% | Lab fixtures + eyewash if lab |
| Fire sprinkler | 1–3% | NICET-certified designer if zoning changes |
| Low-voltage / Cat 6A | 1–2% | Often institution-preferred vendor (single-pull discipline) |
| Lab specialty (gas, DI, vacuum) | 2–4% if lab | Few qualified subs; lock early |
| Abatement (if triggered) | 4–8% if triggered | TDSHS-licensed; non-negotiable |

## 5. Common alternates / VE opportunities

- **Alt flooring:** LVT (base spec) → Sheet vinyl (cheaper but worse-looking on long runs) → Polished sealed concrete (cheapest but loses look in offices)
- **Alt ceiling tile:** ARM AC2x4 lay-in (base) → vinyl-faced gypsum tile (cheaper, plain look) → leave-existing-grid (if grid is sound; demo just tile and replace)
- **Alt paint:** SW ProMar 200 (base) → SW SuperPaint (slight premium but better scrub) → PPG SpeedHide (lower-cost but contractor-grade look)
- **Alt casework:** PLAM on particle-board core (base) → PLAM on MDF core (cheaper, less moisture resilience) → solid-surface countertops (premium upgrade alt)
- **Alt lighting:** OFCI tenant-supplied LED → contractor-supplied institutional-grade troffer with 0–10V dimming (premium)
- **VE — eliminate ceiling work in rooms with existing sound grid + tile:** replace tile only, leave grid (saves 30–40% of ACT line)
- **VE — combine paint + drywall into one sub:** saves 1–2 weeks of crew handoff
- **VE — eliminate sprinkler mods if existing pattern is acceptable per AHJ:** save 1–3% of contract

## 6. Schedule duration guidance

| Project size | Substantial completion | Final completion | Notes |
|---|---|---|---|
| 1 room, ~1,200 SF (TAMU Harrington Lab 303 archetype) | 60–80 cal days | + 30 cal days fixed | Lab specialty + long-lead lighting / casework can push to 90 SC |
| Small suite, 3–6 rooms, ~3,000 SF | 90–120 cal days | + 30 cal days fixed | Multi-room means parallel crews can compress |
| Floor, 8–15 rooms, ~5,000–10,000 SF (B1710, Wehner archetype) | 120–180 cal days | + 30–45 cal days fixed | Long-lead casework / doors is critical path |

**Long-lead items to flag early (week 1 of project):**

- Casework (~8–12 weeks lead)
- Hollow-metal frames + doors + hardware (~6–10 weeks lead)
- LED troffers if owner-spec (~6–8 weeks lead)
- Specialty lab equipment (~8–16 weeks lead; usually OFOI but verify)
- VFD / VAV boxes (~10–14 weeks lead if non-stock)

## 7. Lab-specific overlay (TAMU Harrington pattern)

When the renovation is an educational / research lab, layer these on top of the base template:

- **Casework spec:** epoxy or phenolic countertops in chemistry labs; PLAM acceptable in non-chemistry teaching labs
- **Eyewash / safety shower:** mandatory in chemistry labs; coordinate with plumbing rough + tempering valve (some jurisdictions require thermostatic mixing)
- **Lab gas drops:** verify gas type (vacuum, compressed air, natural gas, specialty) and whether owner-furnished gas line stub-out is in place
- **Fume hoods:** typically OFOI but pre-tested; verify hood face-velocity test post-install
- **Floor finish:** sheet vinyl with welded seams + integral cove base preferred for spill containment
- **Wall finish:** epoxy paint in chemistry; eggshell latex acceptable in dry teaching labs
- **Specialty waste:** acid-neutralization trap (if chemistry) — usually OFOI but coordinate plumbing
- **Backup power:** verify whether outlets need to be tied to building emergency / standby power
- **Building automation:** verify whether new diffusers + VAVs need to integrate with existing building DDC system (significant integration cost if yes)

## 8. Federal-RFQ overlay (B1710 USAF archetype)

When the renovation is on a federal installation (USAF base, USACE, USFWS), layer these on:

- **Davis-Bacon labor:** apply WD rates from the RFP attachment; weekly WH-347 administration burden = +1–2% on GC line
- **Base-access lead time:** 5–15 business days per worker; size crew with extras to cover absences
- **Building-shutdown coordination:** can't always work during business hours; expect after-hours / weekend premium
- **15% on-site self-perform** (FAR 52.236-1): pre-allocate self-perform scope (typically GC + supervision + selective demo) > 15% of direct cost
- **Buy American on iron + steel:** doors, frames, MEP rough; verify domestic-content rep on every PO
- **Bonding:** P&P at 100% over $150K — add 1.5–2.5%
