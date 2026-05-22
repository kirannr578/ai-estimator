# 04 — Scope of work (draft, pre-drawings)

> Source: RFCSP narrative (in `inbox/opportunities/attachments/2026-05-21/ESBD_516718_..._RFCSP.pdf`; v3 summary in `exports/calibration_v3/estimate.json` `bid_packages[4]`) + the user's task-brief project-facts block (which is the literal scope text from the RFCSP) + typical TTUS member-institution dressing-room renovation patterns.
>
> Every quantity placeholder is `[TBD per drawings]` and ties back to a row in `takeoff-template.json`. The CSI section column references the seed cost DB at `config/cost_database.json` where a match exists; rows tagged "**no cost-DB hit**" will need either the F1 (CWICR cost-DB) land OR a manual price entry to deliver a unit price.

---

## A. Contractor-vs-owner scope boundary — read this FIRST

**This is unusual.** ASU is providing more owner-furnished scope than is typical on a TTUS reno. We must price coordination, protection, and rough-ins for these items but NOT the items themselves. Getting this wrong is the single largest pricing error risk on this bid.

| Item | Who | What we do | What we do NOT do |
|---|---|---|---|
| Technology systems (AV, classroom AV, performer comm) | **Owner** | Provide power + pathway (conduit, J-boxes, ring & string). Coordinate cutover with ASU IT. | Do NOT supply or install AV equipment, screens, projectors, headends, ceiling speakers |
| Network / data cabling | **Owner** | Provide pathway (conduit, J-boxes, plenum-rated ring & string from device to closest accessible plenum) | Do NOT pull, terminate, label, or test data cable. ASU's cabling vendor (likely a TTUS standing-contract vendor) does this. |
| Equipment install (post-construction equipment that goes INTO the dressing rooms) | **Owner** | Provide finished spaces ready for owner-furnished equipment install. Coordinate sequence so owner install can follow our punch list closure. | Do NOT receive, store, install, or commission owner equipment |
| Furniture / FF&E (makeup chairs, costume racks, lockers if applicable) | **Owner** | Provide blocking in walls where owner needs to mount any heavy items; coordinate floor / wall finishes around any owner-installed millwork | Do NOT supply furniture, lockers, costume storage, makeup chairs |
| Fire suppression system | **Owner** | **Provide ACCESS only** for owner's fire suppression contractor. Do NOT relocate sprinkler heads — owner is doing the whole FP system. This is unusual; reconfirm in writing with Samuel. | Do NOT price sprinkler-head relocation, FP main modifications, FP shutdown coordination |
| CBORD access-control devices (readers, controllers, electric strikes) | **Owner** (devices) | Provide door hardware preparation (electric-strike-ready frames, electric hinges where required, low-voltage wiring pathway to the door), 120V at the reader if PoE not used | Do NOT supply CBORD readers, controllers, head-end equipment, or pull / terminate access-control cabling |
| Sargent cylindrical locks (mechanical door hardware) | **Contractor** (us) | Supply, install, key per the CBORD coordination | (this IS in our scope — Sargent is named) |
| Door hardware preparation for CBORD | **Contractor** (us) | Frame prep, electric strike or electric hinge mortise, low-voltage conduit from frame to plenum, ring & string | (this IS in our scope) |

> When in doubt: if a system "lives" in the dressing room after we leave (a screen, a chair, a costume rack, a sprinkler head), it's likely owner. If it's the substrate / power / pathway that makes the system possible, it's us. **Get this in writing from Samuel — see `02-bid-prep-checklist.md` § D action item 2.**

---

## B. Assumptions baked in (until drawings prove otherwise)

1. **Multi-room dressing-room suite scope** — RFCSP says "Dressing Room Renovation" (plural in context). Working assumption: 2–4 dressing rooms + adjacent circulation / vestibule, total **2,500 SF**. Range 2,000–3,000 SF.
2. **Existing wall structure stays** — perimeter demising walls remain; only the interior finish layer and any non-structural partitions get touched. Confirm against demo drawings.
3. **No structural mods** — slab and ceiling structure are not affected; demo + reno is interior-only.
4. **Active performing-arts building** — Carr EFA is the home of theater, dance, music. Expect: no daytime noisy work during rehearsals / classes / productions; after-hours premium labor for any noisy / odor-generating tasks; dust containment with negative-air; restricted dumpster placement; coordination with theater faculty calendar.
5. **Possible shower / wet area** in dressing rooms — confirm against drawings. If present, this drives waterproof flooring, ceramic tile, accessible shower stall (ADA), additional plumbing fixtures.
6. **ADA full compliance triggered** by the alterations standard (28 CFR 35.151) — door clear width 32" min, hardware reach 48" max, accessible route, mirror height at 40" AFF max to reflective surface bottom, ADA lavatory rim/knee, signage with raised characters + Braille.
7. **No hazmat budgeted** — pending ASU EHS survey. If Carr EFA was built pre-1980, asbestos VCT, mastic, pipe insulation, and fireproofing are realistic concerns. Carry an allowance only after survey returns OR negotiate as a Div 02 allowance line.
8. **Brick wall finish is existing exposed brick** (clean, repoint, seal) rather than new brick veneer. New brick veneer in a dressing-room reno would be unusual; confirm against drawings.

---

## C. Trade-by-trade scope draft

### Division 01 — General requirements

| Item | RFCSP says | Reasonable assumption | Quantity placeholder | CSI section (cost-DB) |
|---|---|---|---|---|
| General conditions / project supervision | Yes — "CPM scheduling, submittals, change requests, inspections" | Full-time PM + super for the 124-day construction window | `[TBD: ~4 months]` | `01 00 00` ($12,000/mo seed) |
| Temporary facilities, controls, dumpsters, PPE | Yes — implied | Dust containment with negative-air; performer-area protection; ASU-designated dumpster; portable toilet at lay-down | 1 LS | `01 50 00` ($6,500 LS seed; bump to $10K–$15K for active-building constraints) |
| Project closeout — O&M manuals, attic stock, training, as-builts, record drawings | Yes — explicit | Standard TTUS UGSC requirement | included in GCs | — |
| Material testing / independent inspection | Yes — explicit | Concrete (if any new slabs / topping), welds (if any structural mods), air balance — typically owner-paid for material testing on a renovation this size; confirm | `[TBD: allowance only]` | no cost-DB hit |
| Coordination with ASU IT / EHS / Facilities | Yes — implied by owner-furnished scope | Heavy coordination load due to CBORD + AV/data + FP all being owner | included in GCs (bump PM hours) | — |
| Construction CPM schedule + updates | Yes — explicit | Baseline + monthly updates per UGSC | included in GCs | — |
| Submittals (per UGSC Art. 7) | Yes — implied | Major submittals: doors/hardware, finishes, lighting, plumbing fixtures, HVAC equipment, paint | included in GCs | — |

### Division 02 — Existing conditions / selective demolition

| Item | RFCSP says | Reasonable assumption | Quantity placeholder | CSI section |
|---|---|---|---|---|
| Selective interior demo of existing finishes (flooring, base, walls / wall finishes, casework, ceiling, MEP) | Yes — **"complete demolition"** of all interior finishes & MEP | Strip dressing rooms to demising walls & structure | `[TBD: ~2,500 SF]` | `02 41 16` ($4.50/SF seed; for complete MEP-included strip, real cost ~$8–$14/SF) |
| Demo of existing partition walls if floor plan changes | Maybe | Confirm against demo drawings; assume some | `[TBD: LF of demo partition]` | `02 41 16` |
| Demo of existing HVAC ductwork, plumbing rough-ins, electrical rough-ins | Yes — RFCSP says "demo of HVAC, lighting, infrastructure" | Carry separately from finish demo (different sub) | `[TBD: SF of MEP demo]` | `02 41 16` |
| Demo of existing fire-alarm devices in scope area | Likely (incidental to ceiling demo) | Coordinate with EHS for shutdown | `[TBD]` | no cost-DB hit |
| Hazmat abatement allowance | Not stated | **Pending ASU EHS survey.** If Carr EFA is pre-1980 construction, asbestos VCT + mastic + pipe insulation possible. | `[TBD: $0 or $5K–$15K allowance]` | no cost-DB hit |
| Protection of adjacent active spaces (theater, classrooms, offices) | Yes — implied | Temporary partitions, plastic sheeting, walk-off mats at egress, sound mitigation | included in Div 01 temp facilities | — |

### Division 04 — Masonry (existing brick)

| Item | RFCSP says | Reasonable assumption | Quantity placeholder | CSI section |
|---|---|---|---|---|
| Existing brick wall — clean, repoint, seal | Yes — "brick" listed as wall finish | Likely interior exposed-brick accent wall(s); clean to remove paint/coatings if applicable, tuckpoint failed joints, apply clear sealer | `[TBD: SF of exposed brick]` | `04 22 00` is for new CMU — **no cost-DB hit** for brick restoration. Carry $18–$35/SF allowance for clean + repoint + seal |
| New brick veneer (if applicable) | Maybe — unlikely for dressing room | Confirm against drawings; carry zero unless drawings show new brick | `[TBD: likely 0]` | no cost-DB hit |

### Division 06 — Carpentry / casework / finish carpentry / millwork

| Item | RFCSP says | Reasonable assumption | Quantity placeholder | CSI section |
|---|---|---|---|---|
| Finish carpentry (door + window trim, base trim, wall trim) | Yes — explicit "finish carpentry" | Painted MDF or wood at door openings, wall accents | `[TBD: LF]` | `06 10 00` ($8.75/SF seed for rough framing — **wrong category for finish trim**; carry $12–$22/LF for paint-grade trim) |
| Millwork — makeup vanities, counters, mirror surrounds, costume storage shelving | Yes — explicit "millwork" | Plastic-laminate base cabs + countertops, with LED-lit mirror surrounds at makeup stations (theater-grade) | `[TBD: LF + EA]` | `06 41 00` ($425/LF seed for general millwork — **realistic for paint-grade PLAM; theater dressing rooms run $400–$700/LF including mirrors + LED lighting**) |
| Wall blocking for owner-furnished items (mirror mounts, costume rack mounts, hook strips, accessibility grab bars) | Yes — implied by ADA + owner-furnished | 2x or 3/4" PT plywood blocking behind GWB at known mount locations | `[TBD: SF of blocking — small allowance]` | `06 10 00` |
| Wall-mounted accessory backing for owner-furnished CBORD readers | Yes — implied | Reinforced GWB or blocking at door-side reader location | `[TBD: EA per door]` | `06 10 00` |

### Division 08 — Openings (doors, frames, hardware)

| Item | RFCSP says | Reasonable assumption | Quantity placeholder | CSI section |
|---|---|---|---|---|
| New door + frame at each dressing room entry | Yes — implied by full demo | Solid-core wood door + HM frame; some doors may stay if existing condition permits | `[TBD: 4–8 EA]` | `08 14 16` ($575/EA seed) + `08 11 13` ($950/EA seed for HM frame) |
| Sargent cylindrical lockset at each door | Yes — **Sargent specified by name** | Sargent 7- or 10-Line cylindrical lockset, US26D finish typical; classroom function or storeroom function depending on door | `[TBD: 4–8 EA]` | `08 71 00` ($425/EA seed — **light for Sargent at institutional spec; carry $500–$700/EA**) |
| Door hardware accessories — closers, kick plates, silencers, weatherstrip (if exterior), thresholds, stops | Yes — implied by hardware schedule | Per ADA + TTUS standard hardware set | `[TBD: EA sets]` | `08 71 00` |
| Door prep for CBORD electric strike or electric hinge | Yes — implied by access control | Mortise prep in frame; low-voltage conduit & ring & string from frame to plenum | `[TBD: EA prep — owner furnishes the electric strike itself]` | no cost-DB hit (labor only) |
| Vision lite kit if required | Maybe | Confirm against door schedule | `[TBD]` | no cost-DB hit |

### Division 09 — Finishes

| Item | RFCSP says | Reasonable assumption | Quantity placeholder | CSI section |
|---|---|---|---|---|
| Metal-stud framing for any new partitions / furring | Maybe | Confirm against drawings | `[TBD: SF of new partition]` | `09 22 16` ($6.40/SF seed) |
| Gypsum board on framing (5/8" Type X, moisture-resistant in wet areas) | Yes — implied by finish replacement | Both faces of new partitions; furring at existing brick where applicable | `[TBD: SF, both faces]` | `09 29 00` ($2.85/SF seed) |
| Acoustical ceiling — replace existing | Yes — RFCSP says "ceilings" | 2x4 or 2x2 lay-in grid + tile in dressing-room areas | `[TBD: ~2,000 SF of ACT]` | `09 51 13` ($5.10/SF seed) |
| GWB ceiling in wet areas (if showers present) | Maybe | Moisture-resistant GWB on resilient channel | `[TBD]` | `09 29 00` |
| Flooring — sheet vinyl or LVT in dry dressing rooms | Yes — RFCSP says "flooring" | Slip-resistant sheet vinyl with heat-welded seams (theater-friendly: easy clean, costume-snag resistant); LVT in adjacent circulation | `[TBD: ~2,000 SF dry zone]` | `09 65 19` ($6.40/SF seed for LVT; sheet vinyl heat-welded ~$8–$12/SF — **no cost-DB hit for sheet vinyl, carry allowance**) |
| Ceramic tile in wet zones (shower stalls, shower walls) | Maybe | If showers present, ceramic floor + porcelain wall tile to ceiling | `[TBD: SF of tile]` | no cost-DB hit. Carry $18–$30/SF for floor tile + $14–$22/SF for wall tile installed |
| Waterproofing membrane under wet-zone tile | Maybe | Schluter Kerdi or similar membrane | `[TBD: SF]` | no cost-DB hit |
| Resilient base — 4" rubber, integral or cove | Yes — typical | Standard 4" rubber base | `[TBD: LF of perimeter]` | `09 65 13` ($3.25/LF seed) |
| Painting — walls + ceilings (where GWB) + door frames | Yes — explicit | 2-coat institutional latex, low-VOC; theater dressing rooms sometimes specify a specific color/sheen | `[TBD: SF of paint surface]` | `09 91 23` ($1.65/SF seed) |

### Division 10 — Specialties

| Item | RFCSP says | Reasonable assumption | Quantity placeholder | CSI section |
|---|---|---|---|---|
| Room signage (ADA-compliant, raised characters + Braille) | Yes — implied by ADA | Per ASU/TTUS wayfinding standard | `[TBD: 4–8 EA]` | `10 14 00` ($95/EA seed) |
| Toilet accessories (if dressing rooms include private toilets) | Maybe | Grab bars, paper holders, soap dispensers, ADA mirrors | `[TBD: 0–4 sets]` | `10 28 00` ($850/EA seed) |
| Theater dressing-room mirrors (large makeup mirrors with LED lighting) | Yes — implied by performer dressing rooms | Often part of the millwork package (see Div 06) | `[TBD: see Div 06]` | — |
| Costume hooks, hat hooks, hanging rods | Maybe | If not owner-furnished | `[TBD]` | no cost-DB hit |
| Lockers (if dressing-room scope includes lockers) | **OWNER-FURNISHED** per RFCSP if listed under "furniture" | Carry zero | 0 | n/a |
| Fire extinguishers + cabinets (1 per 75 ft of travel distance per code) | Yes — code-required | 2–3 EA | `[TBD]` | no cost-DB hit |

### Division 21 — Fire suppression

| Item | RFCSP says | Owner / contractor | Quantity placeholder | CSI section |
|---|---|---|---|---|
| Sprinkler-head relocation per new ceiling layout | **OWNER-FURNISHED per RFCSP narrative** | Do NOT price. Coordinate access only. | 0 | n/a |
| FP main / branch modifications | **OWNER-FURNISHED** | Do NOT price. | 0 | n/a |
| FP shutdown coordination | Yes — coordination only | Schedule access windows with owner's FP contractor | included in GCs | — |

### Division 22 — Plumbing

| Item | RFCSP says | Reasonable assumption | Quantity placeholder | CSI section |
|---|---|---|---|---|
| Plumbing fixture replacement — lavatories | Yes — explicit "plumbing" | ADA-compliant wall-hung lavatories with sensor or lever faucets | `[TBD: 2–4 EA]` | `22 40 00` ($1,850/EA seed) |
| Plumbing fixture replacement — water closets (if private toilets in scope) | Maybe | Floor-mounted or wall-hung, ADA | `[TBD: 0–4 EA]` | `22 40 00` |
| Plumbing fixture replacement — shower stalls (if dressing rooms include showers) | Maybe | ADA-compliant shower stall (60"x36" transfer shower or roll-in shower with seat), thermostatic mixing valve, slip-resistant base | `[TBD: 0–4 EA]` | no cost-DB hit. Carry $4,500–$7,500/EA installed |
| Supply, waste, vent rough-in modifications | Yes — implied by fixture replacement | Coordinate with existing risers | `[TBD: per fixture allowance]` | `22 11 00` ($525/EA seed for domestic water) |
| Water heater (if scope) | Maybe | If existing dressing-room HW is dedicated and at end of life | `[TBD]` | no cost-DB hit |
| Plumbing rough-in for owner-furnished equipment | Yes — implied | Coordinate with owner equipment schedule | `[TBD]` | no cost-DB hit |

### Division 23 — HVAC

| Item | RFCSP says | Reasonable assumption | Quantity placeholder | CSI section |
|---|---|---|---|---|
| HVAC system replacement — air handler or VAV box + new ductwork + diffusers/grilles | Yes — **"complete replacement"** of HVAC system | Major scope item; carry ~$25–$45/SF on the served area | `[TBD: ~2,500 SF served]` | `23 00 00` ($22.50/SF seed for light-commercial RTU+duct — **light for full system replacement; bump to $30–$45/SF**) |
| Dressing-room exhaust (hair/makeup chemical vapors) | Likely | Higher exhaust rate than standard ACH for back-of-house spaces | `[TBD: EA exhaust fans / LF of exhaust duct]` | no cost-DB hit |
| HVAC controls — DDC, integration with ASU BMS | Likely | TTUS standardizes on Siemens or Automated Logic typically; confirm | `[TBD]` | no cost-DB hit |
| Test, adjust, balance (TAB) report | Yes — typical TTUS UGSC requirement | 1 LS independent agency | `[TBD: 1 LS]` | no cost-DB hit ($3,500–$8,500 range for this size of system) |

### Division 26 — Electrical

| Item | RFCSP says | Reasonable assumption | Quantity placeholder | CSI section |
|---|---|---|---|---|
| Branch wiring + devices — receptacles, switches, GFCI in wet zones | Yes — explicit "electrical" full replacement | Dedicated 20A circuits at makeup stations; GFCI within 6' of any sink or shower | `[TBD: ~2,500 SF]` | `26 05 00` ($8.40/SF seed) |
| Lighting — LED fixture replacement + controls | Yes — implied by demo of "lighting" | Theater-grade dimming for performer prep; makeup-mirror lighting (see Div 06); general ambient lighting; egress lighting; emergency lighting | `[TBD: ~25 fixtures + 4 mirror surrounds]` | `26 51 00` ($285/EA seed — light for theater-grade; carry $350–$650/EA for dimmable LED) |
| Emergency egress + exit signage | Yes — code-required | Per IBC | `[TBD: 2–4 EA]` | no cost-DB hit |
| Sub-panel for dressing-room loads (if existing panel is full / wrong location) | Maybe | Carry 1 EA allowance | `[TBD: 0–1 EA]` | `26 24 16` ($2,400/EA seed — residential-spec; carry $5,500–$8,500/EA for institutional 200A sub-panel) |
| Power for owner-furnished CBORD readers (120V or PoE) | Yes — implied | Dedicated low-voltage circuit per door | `[TBD: EA per door]` | included in `26 05 00` allowance |
| Power for owner-furnished AV equipment | Yes — implied | Receptacle + dedicated circuit at each AV equipment location | `[TBD: EA per AV device]` | included in `26 05 00` allowance |
| Lighting controls — occupancy + manual override + dimming | Yes — Title 24-ish (TTUS sustainability standard) | Per ASU standard | `[TBD: per room]` | no cost-DB hit |

### Division 27 — Communications / low-voltage

| Item | RFCSP says | Reasonable assumption | Quantity placeholder | CSI section |
|---|---|---|---|---|
| Data drops + AV pathway / J-box / conduit | Yes — **OWNER cabling, contractor pathway** | GC furnishes pathway only (conduit + J-box + ring & string + faceplate-ready opening) | `[TBD: # outlets]` | no cost-DB hit. Carry $125–$250/EA for pathway only |
| AV/sound system | **OWNER-FURNISHED** | Do NOT price equipment | 0 | n/a |
| Performer call / cue system | Maybe owner | Confirm with Samuel — theaters sometimes have a performer-cue intercom system; if owner has one in scope, exclude | `[TBD]` | no cost-DB hit |

### Division 28 — Electronic safety / security / fire alarm

| Item | RFCSP says | Reasonable assumption | Quantity placeholder | CSI section |
|---|---|---|---|---|
| Fire-alarm device relocation per new ceiling layout | Likely (incidental to ceiling demo) | Strobe + smoke detector relocation; coordinate with EHS for shutdown windows | `[TBD: 4–10 EA]` | no cost-DB hit. Carry $350–$650/EA for relocation |
| CBORD access-control device install | **OWNER-FURNISHED** | Do NOT supply or install readers; provide pathway + power + door prep | 0 (devices) + included in Div 08 & 26 (prep) | n/a |
| CCTV (if scope) | Likely owner | Confirm | 0 | n/a |

---

## D. Coordination notes (the pain-points worth pricing for)

1. **Owner-furnished scope is unusually broad.** Tech, cabling, equipment install, furniture, AND fire suppression are all owner-furnished. The single most likely pricing error is to inadvertently price one of these items. The contractor-vs-owner table in § A is the canonical demarcation; reconfirm in writing with Samuel.
2. **CBORD coordination is high-stakes.** ASU's CBORD-managed access control means the door hardware schedule, low-voltage pathway, and door prep all hinge on a coordination call with the CBORD admin. Schedule that call in week 1 of construction (or earlier).
3. **Active performing-arts building.** Carr EFA hosts theater, dance, music productions and rehearsals. Carry: (a) after-hours premium labor for noisy work, (b) negative-air dust containment, (c) walk-off mats at every transition to occupied space, (d) sound mitigation during rehearsals/productions, (e) explicit access-window calendar coordinated with the College of Arts and Humanities.
4. **EHS shutdown windows.** Fire alarm (during relocation), HVAC (during cutover), electrical (during panel work), water (during plumbing cutover) all require coordinated shutdowns with ASU EHS / Facilities. Typically 2-week advance notice + 2–4 hour shutdown windows.
5. **Existing-conditions risk in a 1960s/1970s-era building.** Carr EFA is older; expect: asbestos in floor tile / mastic / pipe insulation (carry hazmat allowance), galvanized water supply (consider replacement scope), cast-iron DWV (may need transitions to new PVC), undersized electrical service to the dressing room area, existing ductwork that's hard to demo without disturbing adjacent spaces. Site walk is critical; press hard for it via Samuel.
6. **ADA "alterations" compliance.** Trigger: any alteration that touches a primary function area (and a performer dressing room is a primary function area for a performing-arts venue) triggers the 28 CFR 35.151 alterations standard. We must bring at least the renovated areas to current ADA, including any accessible route, restroom, lavatory, and (if showers) shower stall to the dressing rooms.
7. **Submittal turnaround time.** TTUS UGSC Art. 7 sets the submittal review cycle. Major submittals: doors/hardware (with CBORD coordination), plumbing fixtures, lighting (theater-grade requires extra sample/spec review), finish samples (especially paint colors and floor product). Lead times on dressing-room mirrors with LED lighting can be 8–12 weeks — order early.
8. **The $25,000 cash/contingency allowance** in Attachment A is a separate line item — do NOT roll it into the base proposal price; do NOT mark it up; it gets drawn against during construction via PCO process per the CSA.
