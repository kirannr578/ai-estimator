# Scope outline — MCC Cosmetology Phase 4 Renovation

> **Source:** This outline is keyed to the digest's scope list verbatim:
>
> > *"The Project consists of interior renovations to the existing classrooms on the first floor of the MCC CSC Module B Cosmetology Lab. Casework, Door Hardware, Glazing, Drywall, Paint, Flooring, HVAC, Plumbing, Electrical"*
>
> The detailed scope-of-work, drawings, and Owner's Proposal Form are in the HCS Box folder. Treat every line below as an **estimator's working hypothesis** until plans + the Owner's Proposal Form are in hand.

## Scope categories — BPC self-perform vs. sub

| Trade (digest order) | Typical Phase-4 cosmetology classroom scope | BPC self-perform vs. sub | Notes |
|---|---|---|---|
| **Casework** | Cosmetology stations (mirrored counter w/ shampoo-bowl rough-in), instructor desks, supply cabinets, possibly reception desk | Sub (millwork shop) | High-touch lab casework typically OFCI for the stations; BPC installs. Confirm OFCI vs. CFCI in plans. |
| **Door Hardware** | Classroom passage sets, lever-style ADA-compliant, possibly access control on lab doors | Self (BPC installs hardware on owner-furnished doors and frames) | Confirm hardware schedule — is HCS providing doors/frames, or does BPC's sub package include doors? |
| **Glazing** | Vision lites in classroom doors; possibly storefront glazing if Phase 4 includes any exterior wall modification | Sub (glazing) | Cosmetology lab interior glazing is typically minimal — vision lites only. Storefront usually a separate phase. |
| **Drywall** | Demo + reframe of existing classroom partitions; new GWB on metal-stud framing; tape, bed, texture | Self (BPC self-performs drywall + tape, bed, texture per `firm/firm-profile.json → trade_capabilities.self_perform`) | Strong BPC fit. |
| **Paint** | Interior paint (walls, doors, frames, trim) — likely epoxy or scrubbable enamel for cosmetology lab durability | Self (BPC core trade) | Strong BPC fit. Confirm paint system from spec book — cosmetology labs often spec a chemical-resistant finish. |
| **Flooring** | Likely vinyl tile / LVT / sheet vinyl for the lab floor (chemical resistance + cleanability) plus carpet/LVT for instructor / lecture areas | Self (BPC self-performs LVT, vinyl, sheet vinyl per profile) | Strong BPC fit. |
| **HVAC** | Air-handler / VAV box modification for new classroom layouts; possibly dedicated exhaust over color/chemistry stations (cosmetology requires elevated ventilation per IBC + cosmetology curriculum norms) | Sub (mechanical) | Specialty — engage HVAC sub with classroom-lab experience. |
| **Plumbing** | Shampoo-bowl rough-in (drain + supply); possibly station-mounted handwash sinks; tempering valve / mixing valve | Sub (plumbing) | Cosmetology shampoo bowls are a recurring cost driver — confirm count from plans. |
| **Electrical** | Station outlets (each cosmetology station typically requires 1–2 dedicated 20A circuits for blow dryers, curling tools, station lighting); LED lighting; possibly emergency / egress lighting modification | Sub (electrical) | High circuit density per station — flag for spec-book confirmation. |

## What's likely NOT in scope

- Vertical building expansion (project is "interior renovations to the existing classrooms")
- Major roof or envelope work
- Major structural modifications
- Hazardous materials abatement (no asbestos / lead trigger language in the digest, but Phase 4 of an older campus building could surprise — confirm in spec book)
- Sitework / hardscape / parking
- Fire suppression sprinkler modifications (confirm in plans — typical when partition layouts change)

## Quoting strategy options

BPC has three viable approaches; choose at the Gate-0 decision:

### Option A — Self-perform single trade (lowest-effort quote)

Quote one of: drywall, paint, or flooring. Lowest BPC overhead, most competitive pricing on a single trade. Risk: HCS may not be looking for narrow-scope subs at this stage.

### Option B — Multi-trade self-perform package (medium effort)

Quote drywall + paint + flooring as a bundled package. BPC's natural lane and a credible MBE-sub story for HCS to roll up to MCC. Captures the bulk of the visible interior-finish trades.

### Option C — Multi-trade rolled-up sub-GC package (highest effort, highest upside)

Quote everything in the digest scope list (including managed-via-subs trades). Effectively positions BPC as a sub-GC handling the full interior reno scope, with HCS delivering pad-ready conditions. **Highest mobilization-premium exposure** given Waco distance; only viable if HCS is open to fewer, more-comprehensive subs.

**Recommend Option B** at scaffold time pending HCS scope clarification.

## Critical questions for HCS / spec book

1. Total project magnitude (HCS may not disclose; helpful for sub-bid sizing)
2. Phase-4 boundary: which classrooms specifically? How many shampoo / cosmetology stations?
3. OFCI vs. CFCI casework decision
4. Paint system spec (standard latex vs. chemical-resistant)
5. Flooring system spec (sheet vinyl vs. LVT vs. tile in wet zones)
6. HVAC-exhaust spec (general classroom vs. cosmetology-specific exhaust hoods)
7. Schedule: NTP date, completion date, summer-class blackout dates (MCC summer term may overlap construction)
8. Liquidated damages / completion-date premium
9. Whether HCS requires sub bond at this tier
10. Whether MBE / HUB participation is a positive signal in HCS's roll-up to MCC

## Reusable scope templates

The closest scope templates in `firm/scope-templates/` (when populated):

- **`office-tenant-refurb.md`** — most analogous to a multi-trade interior classroom reno
- **`restroom-renovation-historic.md`** — has the wet-trade pattern (plumbing + tile + finishes) but historic-preservation overlay does not apply

If neither is fit, **recommend** seeding `firm/scope-templates/cosmetology-classroom-reno.md` from this opportunity's actual scope once plans are in hand. Capture: shampoo-station count + plumbing rough-in pattern, station-electrical circuit density, cosmetology-specific HVAC exhaust, durable-finish system specs.
