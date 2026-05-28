# PAIS — Backcountry Cabin Roof Repairs — Scope Outline

> **Use:** Internal estimating-side scope outline that maps each line of the SOW to a CLIN, a sub trade, and a quantity. The companion to `01-scope.md` (SOW-side view) and `05-bid-form-prep.md` (CLIN-pricing side).
> **Scope template:** No exact-fit template in [`firm/scope-templates/`](../../firm/scope-templates/README.md) — closest archetypes are *small-structure roofing repair* + *coastal carpentry*. Build out PAIS-specific scope inline; paste back to template library after pricing is finalized.

## 1. Scope-template applied

Selected: **none — bespoke for PAIS**. Closest archetypes: small-structure-roofing-repair + small-structure-carpentry-coastal. After bid is priced, recommend extracting a `firm/scope-templates/coastal-cabin-repair-and-protection.md` into the firm scope-template library so the next coastal / backcountry / small-structure RFQ has a starting point.

## 2. SOW → CLIN → Sub mapping

| SOW reference | Description | CLIN | Sub trade | Quantity | Self / Sub | Notes |
|---|---|---|---|---|---|---|
| Att 1 §4 CLIN 001 | Door adjustment, SS hardware, deadbolt + jamb reinforcement | 001 | Carpentry | 3 doors | **Self** | BPC self-performs interior carpentry per firm-profile trade_capabilities |
| Att 1 §4 CLIN 002 | Roof leak inspection + water test + marine-grade shingle replacement + sealant + SS fasteners + post-repair water test | 002 | Roofing | LS (estimate ≈ 50–200 SF damaged area; verify at site visit) | **Self** | BPC self-performs roofing per firm-profile (composition, metal, repairs and replacement) |
| Att 1 §4 CLIN 003 | TDI CAT5 Bahama shutters — 10 units; SS / powder-coated AL; manual; lockable; engineer-stamped | 003 | Specialty (TDI hurricane shutter sub) | 10 units | **Sub** | TDI-listed manufacturer + installer; engineer stamp required |
| Att 1 §5 Opt 001 | Ramp extension — 2 landings + 2 ramp runs + GFE aluminum ramp integration | OPT 001 | Carpentry (PT lumber) | LS (per Att 2 drawing — verify dims at site) | **Self** | BPC self-performs carpentry; GFE aluminum ramp owner-furnished |
| Att 1 §5 Opt 002 | Breakaway sand control — 2x10 PT lumber 2 boards high on 3 sides | OPT 002 | Carpentry (PT lumber) | LS (3-side perimeter — verify dims at site) | **Self** | BPC self-performs carpentry; breakaway design per FEMA TB-9 (RFI #8) |
| Mob + temp protection + transport | All | Self | LS | **Self** | 4WD truck rental; lodging in CCI; per-diem; haul-out from HQ to backcountry |
| GC supervision (60-cal-day POP) | All | Self | 60 cal-days × super | **Self** | Super on site for active construction days (estimate 25–35 actual work days within the 60-cal-day window) |
| Punch + final clean + as-builts + operation manual | All | Self | LS | **Self** | Per SOW §Deliverables |
| Closeout | All | Self | LS | **Self** | DI-137 Release of Claims; final IPP invoice |

## 3. Trade-by-trade rollup

| Trade | CLINs covered | BPC self / sub | Estimated direct cost | % of contract |
|---|---|---|---|---|
| Mobilization + temp protection + transport | All | Self | `${{COST}}` | `{{PCT}}%` |
| Door repair + SS hardware (CLIN 001) | 001 | Self | `${{COST}}` | `{{PCT}}%` |
| Roof leak repair (CLIN 002) | 002 | Self | `${{COST}}` | `{{PCT}}%` |
| TDI CAT5 Bahama shutters (CLIN 003) | 003 | **Sub** | `${{COST}}` | `{{PCT}}%` |
| Ramp extension carpentry (Opt 001) | OPT 001 | Self | `${{COST}}` | `{{PCT}}%` |
| Breakaway sand-control carpentry (Opt 002) | OPT 002 | Self | `${{COST}}` | `{{PCT}}%` |
| GC supervision + 4WD vehicle + per-diem + lodging | All | Self | `${{COST}}` | `{{PCT}}%` |
| Punch + final clean + closeout + as-builts + manuals | All | Self | `${{COST}}` | `{{PCT}}%` |
| **Direct cost subtotal** | | | `${{DIRECT_TOTAL}}` | 100% |

## 4. Self-perform verification (FAR 52.236-1)

| Self-perform scope | Direct cost | % of total direct |
|---|---|---|
| GC + supervision + 4WD vehicle + per-diem + lodging | `${{COST}}` | `{{PCT}}%` |
| Door repair (CLIN 001) | `${{COST}}` | `{{PCT}}%` |
| Roof leak repair (CLIN 002) | `${{COST}}` | `{{PCT}}%` |
| Ramp extension carpentry (Opt 001) | `${{COST}}` | `{{PCT}}%` |
| Breakaway sand-control carpentry (Opt 002) | `${{COST}}` | `{{PCT}}%` |
| Punch + final clean + closeout | `${{COST}}` | `{{PCT}}%` |
| **Total self-perform** | `${{SELF_TOTAL}}` | **`{{SELF_PCT}}%`** (target ≥ 30%; well above the 15% FAR 52.236-1 floor) |

## 5. Sub-only trades (CLIN 003)

| CLIN | Sub trade | Sub-solicitation count target | Lead time concern |
|---|---|---|---|
| CLIN 003 | TDI-listed CAT5 Bahama shutter manufacturer / installer | ≥ 3 quotes (per BPC standard) | Engineer-stamped drawings + 10-unit fabrication; possible 4–6 wk lead time → schedule Dec at NTP for 60-day window. Alternative: pre-engineered standard sizes if window dims are stock; site-visit measurement critical. |

## 6. Materials sourcing

| Material | Source | Buy American note |
|---|---|---|
| Marine-grade shingles + sealant (CLIN 002) | Domestic roofing manufacturer | COTS construction material; domestic preference applies but COTS waiver on domestic-content test |
| SS fasteners + hardware (CLIN 001 + 002 + 003 + Opt 001 + Opt 002) | Domestic SS hardware vendor (e.g. McMaster-Carr / Fastenal domestic stock) | Iron + steel content > 5% — must verify domestic mill or accept Buy American non-compliance risk |
| TDI CAT5 Bahama shutters (CLIN 003) | TDI-listed manufacturer | If powder-coated AL — verify AL mill origin (some TDI manufacturers source AL from foreign mills); SS — verify domestic |
| PT lumber (Opt 001 + Opt 002) | Domestic PT lumber yard | Wood is exempt from iron+steel rule; standard COTS construction material |
| GRK structural screws (Opt 001 alternate fastener) | Domestic distributor | Iron + steel — verify origin |

## 7. Schedule (60 cal-days from NTP — illustrative)

| Day range | Activity |
|---|---|
| NTP+1 to NTP+5 | Mobilization, IPP enrollment, site re-inspection, materials ordering (CLIN 003 shutters long-lead — order Day 1) |
| NTP+5 to NTP+10 | CLIN 002 roof leak inspection + water test; CLIN 001 door measurements; sub solicitations finalized; deliveries staged at HQ |
| NTP+10 to NTP+25 | CLIN 002 roof repair execution (weather-dependent — coastal); haul-out cycles HQ → cabin |
| NTP+15 to NTP+35 | CLIN 001 door repair + SS hardware install; Option 002 sand-control fabrication on site |
| NTP+25 to NTP+50 | Option 001 ramp extension construction (drawings, materials, sub-sequencing); Option 002 install if Option 001 schedule allows in parallel |
| NTP+35 to NTP+55 | CLIN 003 shutter fabrication delivery + install (pending sub lead time); concurrent with ramp completion |
| NTP+50 to NTP+58 | Punch list; final clean; as-built drawings + operation manual + final inspection scheduling |
| NTP+58 to NTP+60 | Final inspection signed by Park rep; closeout package; release of claims (DI-137); final IPP invoice |
| Buffer | 5–10 day buffer within the 60-day window for: weather (coastal storms), wildlife buffers (sea-turtle nesting if in window), tide / sand-road closure of Park Road 22 |

## 8. Risk-driven contingency points

Cross-reference `07-risk-register.md` items E1–E12 + B-side risks. Specific to this scope:

- **Hidden conditions on demo (E1)** → CLIN 002 roof + CLIN 001 doors may reveal rotted sheathing / framing under shingles / behind frames; build modest contingency into self-perform labor
- **Long-lead CLIN 003 shutters (E2)** → Order Day 1 of NTP; identify a backup TDI-listed manufacturer if primary slips
- **Site access lag (E5)** → Park Road 22 sand/tide closure; build 5-day weather/access buffer
- **Wildlife nesting (E5 variant)** → If 60-day window crosses Apr–Aug Kemp's ridley nesting, may need night-work or vehicle restrictions; contingency for slower productivity
- **Buy American audit risk (E4)** → SS fasteners + shutter AL — verify domestic before delivery
