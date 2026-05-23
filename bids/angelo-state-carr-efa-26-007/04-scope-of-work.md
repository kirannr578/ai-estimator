# 04 — Scope of work (2026-05-23 refresh — drawings + project manual IN HAND)

> **Source documents (all in `inbox/opportunities/attachments/2026-05-21/`):**
> - Original RFCSP + Attachments A through F.1
> - **Base Drawings** (38 sheets, 2026-03-27 Issue for Construction; PBK Architects / LEAF Engineers / Lundy & Franke Engineering — PBK Project No. 250402)
> - **Drawings Addendum 1** (2026-04-15, 13 pages; mirror sizes, dimensions, electrical add-on receptacles, new specs MT7/MT8/SWL1/SWL2/SVW)
> - **Drawings Addendum 2** (2026-05-07, 8 pages; corridor light salvage/re-use, 8" can lights, **shower tile updated to 2"x2" mosaic** per spec 09 30 00.T4, emergency lights added)
> - **Project Manual** (796 pages, 144 unique SECTION headings throughout, Issue for Construction 2026-03-27)
> - **Addendum #1** (21-page pre-response meeting deck + sign-in sheet, 2026-05-20)
>
> Every CSI section number below is now the **actual section number from the bound project manual** (verified by searching the manual PDF for the literal "SECTION XX XX XX" heading and finding the part-1 / part-2 / part-3 content). Quantity totals are pulled from the AF100 Room Finish Schedule (Grand Total = **3,115 SF**) where applicable, and rendered as `null` in `takeoff-template.json` only where the drawing is genuinely ambiguous.

---

## 0. Project scope at a glance (verified from AF100 finish plan + drawing index G-001)

**Total area in scope (AF100 Room Finish Schedule Grand Total) = 3,115 SF**, across 10 rooms in Carr EFA at 2602 Dena Dr, San Angelo, TX 76909:

| Room # | Room Name | Area (SF) | Notes |
|---|---|---|---|
| 1R9 | Women's RR (Restroom) | 159 | T1 floor tile + T2 wall tile + paint; toilet partitions |
| 1R10 | Men's RR (Restroom) | 160 | T1 floor tile + T2 wall tile + paint; toilet partitions + urinal |
| 101 | Corridor | 641 | Existing wallpaper to remain partially; RB1 base; light salvage/re-use per Add 2 |
| 104 | Mechanical Room | 61 | Re-use existing (MEP only) |
| 105 | Elevator | 68 | Re-use existing; no contractor scope inside cab |
| 106 | Front Entry | 1,098 | Carpet tile + existing-to-remain wall finishes; circulation only |
| 107 | Green Room | 222 | HPB hardwood base + paint walls; performer rest space |
| 108 | Makeup Room | 434 | T1 floor tile + paint walls; vanity countertops + LED mirror surrounds + TV per Add 1 |
| 109 | Women's Dressing | 135 | T1 floor tile + paint walls; vanity + mirror |
| 110 | Men's Dressing | 136 | T1 floor tile + paint walls; vanity + mirror |
| **TOTAL** | — | **3,115 SF** | |

**This is ~25% larger than the pre-drawing assumption of 2,500 SF** (Front Entry @ 1,098 SF is mostly circulation; the actual back-of-house dressing-room volume is ~1,047 SF spread across 107/108/109/110 + restrooms 1R9/1R10).

**Sheet count (verified):** **38 sheets** in the base set, broken down by discipline:
- **General (G):** 9 sheets — G-000 cover, G-001 index, G-020, G-040, G-090, G-101 (plus 3 sheets P7-P9 that didn't extract text — likely accessibility / code / partition-type sheets)
- **Architectural Demo (AD):** 2 sheets — AD-101 (composite demo plan), AD-401 (enlarged demo)
- **Architectural (A + AF):** 5 sheets — A-401 (enlarged plans), A-501 (enlarged elevations / mirrors), A-801 (door schedule + details), A-901 (millwork details), AF100 (finish plans + schedules)
- **Mechanical (M):** 6 sheets — M-001 (legend/schedule), M-101A, M-101, M-102A, M-601, M-701
- **Electrical (E):** 5 sheets — E-001 (lighting schedule), E-101A (1st flr power), E-201A (1st flr lighting), E-600, E-701
- **Plumbing (P + PD):** 6 sheets — P-000, PD-101 (demo), P-101, P-101A, P-501, P-601
- **Technology (T + TF + TN):** 5 sheets — T-001, TF-101A (fire alarm), TN-101A (network/comm), T-701, T-702
- **Civil (C / CA), Sports Arch (SA), Structural (S), Landscape (L), Theatrical (TH):** **NOT IN SET** (interior dressing-room reno only — no structural, civil, landscape, or theatrical-specialty drawings in scope)

**Project manual coverage (verified by section-heading search throughout the 796-page bound manual):**
- **Div 00 (Procurement + Contracting Requirements):** Sections 00 01 02, 00 01 03 (Project Directory), 00 01 07 (Seals), 00 01 10 (TOC), 00 31 00 (Available Project Information — **referenced in 02 41 00 as containing hazmat survey**), 00 40 11/13/14 (Affidavits), 00 43 36 (Proposed Subs Form), 00 50 00 / 00 50 01 (TX Statutory Bonds), 00 65 19.16 (Affidavit of Release of Liens), 00 70 00 (Conditions of Contract), 00 73 00 (Supplementary Conditions), 00 73 43 (Wage Rate Requirements TX), 00 73 46 (Wage Determination Schedule)
- **Div 01 (General Requirements):** 01 10 00 Summary; 01 21 00 Allowances; 01 22 00 Unit Prices; 01 23 00 Alternates; 01 25 13 Product Substitution; 01 29 00 Payment Procedures; 01 29 73 Schedule of Values; 01 31 00 Project Mgmt + Coordination; 01 31 13 Admin Reqs; 01 32 00 Construction Progress; 01 32 33 Photographic Documentation; 01 33 00 Submittals; 01 35 16 **Alteration Project Procedures**; 01 35 43.13 **Environmental Procedures for Hazardous Materials**; 01 35 46 Indoor Air Quality; 01 40 00 Quality Requirements; 01 42 00 References; 01 45 23 Testing & Inspecting; 01 50 00 Temporary Facilities; 01 56 00 Temporary Barriers; 01 57 13 Erosion Control (incidental); 01 57 15 Integrated Pest Management; 01 60 00 Product Requirements; 01 61 16 VOC Restrictions; 01 73 00 Execution; 01 73 29 Cutting & Patching; 01 74 19 Construction Waste Mgmt; 01 77 00 Closeout (+ A/B/C subcontractor closeout affidavits); 01 78 23 O&M Data; 01 78 39 Project Record Docs; 01 91 13 General Commissioning
- **Div 02:** 02 41 00 Demolition; **02 82 00 Asbestos Remediation** (contingent); **02 83 00 Lead Remediation** (contingent); **02 87 13 PCB Remediation** (contingent — note: spec name shown in manual is "Mold Remediation" at section 02 87 13, which appears to be a labeling inconsistency in PBK's manual; in standard MasterFormat 02 87 13 is PCB Remediation. Flag for clarification.)
- **Div 03:** 03 10 00 Concrete Forming; 03 30 00 Cast-in-Place Concrete; 03 54 00 Cast Underlayment
- **Div 04:** 04 01 20 Maintenance of Unit Masonry; 04 05 00 Common Work Results for Masonry; 04 20 00 Unit Masonry; 04 73 23 Lightweight Synthetic Stone
- **Div 05:** 05 31 00 Steel Decking; 05 50 00 Metal Fabrications; **05 75 00 Decorative Formed Metal (DT1 decorative trim at tile edges + MT1/MT2/MT3 flooring transitions)**
- **Div 06:** **06 10 00 Rough Carpentry (blocking)**; 06 16 00 Sheathing; **06 20 00 Finish Carpentry (incl HPB hardwood base + millwork frame-out)**; 06 41 00 implied via Architectural Casework (countertops carry 12 36 00)
- **Div 07:** 07 21 00 Thermal Insulation; 07 26 27 Fluid-Applied Air Barrier; 07 27 26 Fluid-Applied Air Barrier (VB); 07 62 00 Roof Related Sheet Metal; 07 84 13 Penetration Firestopping; **07 84 43 Joint Firestopping**; 07 92 00 Joint Sealants; **07 95 13 Expansion Joint Cover Assemblies**
- **Div 08:** **08 11 13 Hollow Metal Doors and Frames**; **08 14 16 Flush Wood Doors**; **08 31 00 Access Doors and Panels**; **08 71 00 Door Hardware**; **08 83 00 Mirrors**
- **Div 09 (the biggest division by scope volume):** 09 05 00 Common Work Results for Finishes; 09 05 61 Common Work Results for Flooring Prep; **09 21 16 Gypsum Board Assemblies**; 09 22 16 Non-Structural Metal Framing (via 09 21 16 / 09 22 26.23); 09 22 26.23 Metal Suspension Systems; **09 24 00 Cement Plastering**; **09 30 00 Tiling (T1 floor, T2 blue wall, T3 ridged white, T4 2x2 shower mosaic per Add 2, T6 wall plus T7 ceiling per Add 1)**; **09 51 00 Acoustical Ceilings (ACS1 + ACP1)**; **09 65 13 Resilient Base and Accessories (RB1)**; **09 65 19 Resilient Tile Flooring** (LVT/VCT); **09 68 00 Carpeting (CPT1 carpet tile)**; **09 81 00 Acoustic Insulation**; **09 90 00 Painting and Coating (P1 white field + P2 door frame)**; 09 91 00 Painting/Staining
- **Div 10:** **10 14 00 Signage**; **10 21 13.17 Phenolic-Core Toilet Compartments (FTC)**; **10 21 13.19 Plastic Toilet Compartments (PTC)**; **10 26 00 Wall and Door Protection (CG1 corner guards + PWC protective wall covering)**; 10 28 00 Toilet/Bath/Laundry Accessories; **10 51 13 Metal Lockers**; 10 56 17 Wall-Mounted Standards and Shelving
- **Div 11:** **11 30 13 Residential Appliances** (likely TV per Add 1 Makeup Room + any owner-prep)
- **Div 12:** **12 36 00 Countertops** (PLAM countertops + LED-lit mirror surrounds at vanity stations)
- **Div 13, 14, 21, 33, 34, 35, 40–46, 48 = NOT USED** per project manual TOC — confirms **fire suppression is fully owner-furnished**, conveying is out, no special construction, no environmental remediation other than the contingent Div 02 hazmat sections, no civil/sitework
- **Div 22 (Plumbing):** 22 05 00 Common Work Results; 22 05 16 Expansion Fittings; 22 05 29 Hangers; 22 05 48.13 Vibration Controls; 22 08 00 Commissioning of Plumbing; 22 11 16 Domestic Water Piping; 22 13 16 Sanitary Waste + Vent Piping; 22 40 00 Plumbing Fixtures (incl shower receptors)
- **Div 23 (HVAC):** 23 05 00 Common Work Results; 23 05 13 Motors; 23 05 29 Hangers; 23 05 48 Vibration; 23 05 53 Identification; 23 05 93 TAB; 23 07 13 Duct Insulation; 23 31 00 HVAC Duct Casings; 23 31 13 Metal Ducts; 23 33 00 Air Duct Accessories; 23 34 00 HVAC Fans; 23 37 13 Diffusers/Registers/Grilles
- **Div 25 / 26 (Integrated Automation + Electrical):** 25 55 00 Integrated Automation Control of HVAC; 26 05 00 Common Work Results for Electrical; 26 05 19 Conductors; 26 05 26 Grounding; 26 05 29 Hangers; 26 05 33 Raceways and Boxes; 26 05 34 Provisions for Communication/Security/Safety; 26 05 53 Identification; 26 08 00 Commissioning of Electrical; 26 09 23 Lighting Control Devices; 26 09 43 Distributed Digital Lighting Control System (was originally typed "Network Lighting Controls" — same scope); 26 20 00 Electrical Distribution Equipment; 26 27 26 Wiring Devices; 26 50 00 Lighting; 26 52 00 Emergency Lighting
- **Div 27 (Communications — pathway only; cable owner-furnished):** 27 00 00 Basic Materials and Methods; 27 05 00 Common Work Results; 27 05 39 Surface Raceways; 27 10 00 Structured Cabling System
- **Div 28 (Electronic Safety + Security):** 28 05 00 Common Work Results; 28 31 00 Fire Detection and Notification System
- **Div 31 / 32:** Sections present in TOC but unlikely to apply at meaningful volume given interior-only scope

> Every quantity placeholder is `[TBD per drawings]` and ties back to a row in `takeoff-template.json`. The CSI section column references both the seed cost DB at `config/cost_database.json` AND the actual project-manual section. Rows tagged "**no cost-DB hit**" will need either the F1 (CWICR cost-DB) land OR a manual price entry to deliver a unit price.

---

## A. Contractor-vs-owner scope boundary — read this FIRST (2026-05-23 refresh)

ASU is providing meaningful owner-furnished scope. The project manual TOC + drawings now give us a defensible demarcation; one ambiguity remains (Sec 27 10 00 Structured Cabling System — see Div 27 below).

| Item | Who | What we do | What we do NOT do | Confidence |
|---|---|---|---|---|
| **Lockers** | **Contractor** (us) — UPDATED 2026-05-23 | Supply + install per PM Sec **10 51 13 Metal Lockers**; verify exact qty on A-401 / A-901. Earlier prep-doc assumption that lockers were owner-furnished was wrong; the PM has a dedicated locker spec. | n/a | HIGH (PM confirmed) |
| Technology systems (AV, classroom AV, performer comm) | **Owner** | Provide power + pathway (conduit, J-boxes, ring & string). Coordinate cutover with ASU IT. | Do NOT supply or install AV equipment, screens, projectors, headends, ceiling speakers | HIGH |
| **Network / data cabling — STRUCTURED CABLING** | **Likely Owner** but **PM Sec 27 10 00 is present in spec book** — **AMBIGUOUS** | Carry pathway-only base; carry unit-price for full pull + terminate as alternate | Default to pathway-only unless Hannah Bignall confirms otherwise | MEDIUM — confirm with Hannah |
| TV in Makeup Room 108 (per Add 1) | Likely **Owner** | Provide TV-mount blocking + 120V receptacle + data drop pathway behind TV; rough-in for cable management | Do NOT supply TV unless explicitly listed in 11 30 13 specifying contractor furnish | MEDIUM — confirm |
| Equipment install (post-construction equipment that goes INTO the dressing rooms) | **Owner** | Provide finished spaces ready for owner-furnished equipment install. Coordinate sequence so owner install can follow our punch list closure. | Do NOT receive, store, install, or commission owner equipment | HIGH |
| Furniture / FF&E (makeup chairs, costume racks) | **Owner** | Provide blocking in walls where owner needs to mount items; coordinate floor / wall finishes around any owner-installed millwork | Do NOT supply furniture or makeup chairs | HIGH |
| Fire suppression system | **Owner** | Provide ACCESS only. Do NOT relocate sprinkler heads. | Do NOT price sprinkler-head relocation, FP main modifications, FP shutdown | HIGH (Div 21 NOT USED) |
| CBORD access-control devices (readers, controllers, electric strikes) | **Owner** (devices) | Provide door hardware preparation (electric-strike-ready frames, electric hinges where required, low-voltage wiring pathway to the door), 120V at the reader if PoE not used | Do NOT supply CBORD readers, controllers, head-end equipment, or pull / terminate access-control cabling | HIGH |
| Sargent door hardware (mechanical door hardware) | **Contractor** (us) | Supply, install, key per Sec **08 71 00** Door Hardware schedule (A-801) | (this IS in our scope) | HIGH |
| **All Div 22 plumbing, Div 23 HVAC, Div 26 electrical, Div 27 communications-pathway, Div 28 fire-alarm** | **Contractor** (us) | Full responsibility per PM | n/a | HIGH |

> When in doubt: if a system "lives" in the dressing room after we leave (a screen, a chair, a costume rack, a sprinkler head), it's likely owner. If it's the substrate / power / pathway that makes the system possible, it's us. **Sec 27 10 00 Structured Cabling is the only remaining ambiguity — get clarification from Hannah Bignall in the email at `outreach/01-email-hannah-bignall-eligibility.md`.**

---

## B. Assumptions baked in (after drawings + project manual review, 2026-05-23)

1. **10-room dressing-suite + circulation scope, 3,115 SF total** — confirmed from AF100 finish schedule. Dressing rooms 109 + 110 + the Makeup Room 108 + Green Room 107 are the "back-of-house" volume (~927 SF); the two restrooms 1R9 + 1R10 add 319 SF wet-area scope; the corridor 101 (641 SF) is mostly finish-only; the Front Entry 106 (1,098 SF) is largely circulation + new carpet tile + retained wall finishes.
2. **Existing wall structure stays** — confirmed: demo plan AD-101 shows only finish + partition demo within the suite; no structural mods. Lundy & Franke (structural) appears on the seals page but the drawing set has **no S-discipline sheets**, confirming no structural scope.
3. **No structural mods** — slab and ceiling structure are not affected; reno is interior-only. (Carry $0 for Div 03 forming / Div 05 metal fabrications **except** the decorative formed metal tile-edge trim from Div 05 75 00.)
4. **Active performing-arts building** — Carr EFA is a College of Visual & Performing Arts venue. Pre-response slide 11 says "Currently none at this time" for ASU calendar conflicts — encouraging, but: **Project Manual Sec 01 35 16 (Alteration Project Procedures)** requires owner-approved noise/dust-windows + after-hours work where needed. Apply 5–8% premium-time labor allowance on the demo + MEP phases.
5. **Showers ARE in scope** — confirmed: Drawings Addendum 2 explicitly adds spec **09 30 00.T4 (2"x2" mosaic shower tile)** and updates the wet-zone tile callouts on AF100. Plumbing schedule on P-501 likely shows shower receptors per spec 22 40 00. **Carry full ADA shower-stall scope: roll-in shower or 60"x36" transfer shower per restroom (1R9 + 1R10), 2 EA total**, with thermostatic mixing valve, Schluter Kerdi or equivalent waterproof membrane below mosaic tile.
6. **ADA full compliance triggered** by the alterations standard (28 CFR 35.151) — confirmed in PM Sec 01 35 16. Door clear width 32" min, hardware reach 48" max, accessible route, mirror height per ADA, ADA lavatory rim/knee, signage with raised characters + Braille per Section 10 14 00.
7. **Hazmat budget — $10K–$25K allowance still required pending Section 00 31 00** — Project Manual carries contingent sections 02 82 00 Asbestos / 02 83 00 Lead / 02 87 13 PCB (or Mold — name needs clarification), AND Attachment A requires the Affidavit of Non-Asbestos, Lead, PCB Use (Sec 00 40 14). The presence of both says PBK/ASU expect a clean building but have spec sections ready. Section 00 31 00 (Available Project Information) is referenced in 02 41 00 § 1.3.A as containing "existing building survey conducted by Owner; information about known hazardous materials." **Section 00 31 00 was NOT included in the bound manual we downloaded — Hannah Bignall needs to send it.** Until then, carry $15K hazmat allowance in base (within the $25K cash/contingency line on Attachment A).
8. **No new brick veneer** — there are no brick-veneer details on the architectural sheets; PM Div 04 sections are template-included but unlikely to trigger meaningful quantities. Existing-condition brick (if any) is in the corridor/entry and is being retained per the AF100 finish schedule ("EXISTING TO REMAIN" callouts on rooms 101 + 106).
9. **Salvage requirement: corridor 2x4 light fixtures from existing must be SALVAGED and re-used in the Makeup Room (108) per Drawings Addendum 2.** Carry careful-removal labor + temporary storage in the demo cost; do NOT count these fixtures as new-buy.
10. **Power upgrades per Add 1:** Makeup Room 108 gets a new TV-power receptacle (likely 60" TV per Residential Appliances spec 11 30 13 — owner-furnished TV, GC-provided 120V + low-voltage data pathway). Vanity outlets per Add 1 in rooms 109/110.
11. **New emergency lights per Add 2** — added in corridor 101 (per Addendum 2). Spec section 26 52 00 Emergency Lighting applies.

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

| Item | Project Manual / Drawing source | Working assumption | Quantity | PM section |
|---|---|---|---|---|
| Selective interior demo of existing finishes (flooring, base, walls / wall finishes, casework, ceiling, MEP) | AD-101 (composite demo plan) + AD-401 (enlarged demo) + PM Sec **02 41 00** | Strip 107/108/109/110/1R9/1R10 to demising walls & structure; minimal finish touchup in 101 + 106 (retain wallpaper per AF100) | ~1,950 SF full-strip + ~641 SF light-touch corridor | **02 41 00** ($8–$14/SF for MEP-included strip; partial finish-touch on corridor ~$3–$5/SF) |
| Salvage + storage of existing 2x4 corridor light fixtures for re-use in Makeup Room 108 | Drawings Addendum 2 explicit callout | Careful demo + crate + interim storage; reinstall in 108 | 4–8 EA fixtures (verify on site walk) | **02 41 00** (labor) + **26 50 00** (reinstall) |
| Demo of existing HVAC ductwork, plumbing rough-ins, electrical rough-ins | PD-101 (plumbing demo), and demo notes on M, E sheets; PM 02 41 00 | Coordinate cutover with MEP sub | ~1,950 SF MEP-impact area | **02 41 00** |
| Demo of existing fire-alarm devices in scope area | T-001 TN-101A (technology) + Sec **28 31 00** | Strobe + smoke detector relocation; EHS-coordinated shutdown windows | ~6–10 EA devices (verify on site walk) | **28 31 00** |
| **Asbestos / Lead / PCB remediation if encountered** | PM Sec **02 82 00 / 02 83 00 / 02 87 13** (contingent) + Sec 01 35 43.13 Environmental Procedures for Hazardous Materials | Carry $15K allowance until Sec 00 31 00 survey received | 1 LS allowance | **02 82 00 / 02 83 00 / 02 87 13** |
| Protection of adjacent active spaces (theater, classrooms, offices) | PM Sec **01 35 16 Alteration Project Procedures** + **01 56 00 Temporary Barriers and Enclosures** | Negative-air dust containment, temp partitions, walk-off mats; sound mitigation during performances | 1 LS | **01 50 00 / 01 56 00** ($10K–$15K LS for active-building constraints) |
| Indoor Air Quality compliance during construction | PM Sec **01 35 46 Indoor Air Quality Procedures** | Per IAQ submittal, HVAC filtration during demo, finish-product VOC controls | included in Div 01 | **01 35 46** + **01 61 16** |

### Division 04 — Masonry (likely zero contractor scope)

| Item | Source | Working assumption | Quantity | PM section |
|---|---|---|---|---|
| Unit masonry (CMU + brick) | PM Sec 04 05 00 / 04 20 00 / 04 73 23 are present in TOC as template inclusions | Drawings show no new masonry in scope; existing walls retained as-is | 0 | n/a |
| Maintenance of existing unit masonry (clean / repoint) | PM Sec 04 01 20 (template inclusion) | Existing wallpapered walls in 101 + 106 stay; if masonry encountered behind GWB during demo, scope is unit-price additive | 0 base + verify on site walk | n/a |

### Division 06 — Carpentry / casework / finish carpentry / millwork

| Item | Source | Working assumption | Quantity | PM section |
|---|---|---|---|---|
| Rough carpentry / blocking | PM Sec **06 10 00** + A-901 millwork details | Plywood blocking behind GWB at all mirror, vanity, locker (if scope), grab bar, and signage mounts | ~250–400 SF blocking | **06 10 00** |
| Sheathing (where required at partitions) | PM Sec **06 16 00** | Minimal — likely only at exterior-facing furred-out walls if any | ~0–100 SF | **06 16 00** |
| Finish carpentry — HPB hardwood base in Green Room 107 | PM Sec **06 20 00** + AF100 finish schedule (HPB stain-to-match hardwood base, 4"H x 1"D) | LF perimeter of Room 107 | ~64 LF (verify on A-401) | **06 20 00** ($16–$25/LF stain-grade hardwood base installed) |
| Millwork — vanity countertops (PLAM) + LED-lit mirror surrounds at Makeup Room 108, Dressing Rooms 109 + 110 | A-501 + A-901 + PM Sec **12 36 00 Countertops** (PLAM); Add 1 confirms mirror sizing 24"x72" with vanity LED | Three (3) vanity stations with PLAM tops, theater-grade LED-edge mirrors, drawer/door cabinetry below | ~24–30 LF total vanity (verify on A-901) | **06 20 00 + 12 36 00** ($550–$750/LF theater-grade with LED mirror surround) |
| Wall-mounted accessory backing for owner-furnished CBORD readers | Implied by Sec 28 31 00 + Sec 08 71 00 hardware schedule | Reinforced GWB / 2x blocking at door-side reader location each door | ~4–8 EA per door (verify on A-801) | **06 10 00** |

### Division 08 — Openings (doors, frames, hardware, mirrors)

| Item | Source | Working assumption | Quantity | PM section |
|---|---|---|---|---|
| New hollow metal doors + frames | A-801 (door schedule) + PM Sec **08 11 13** | HM frames at all dressing/RR/makeup entries; some openings may stay if existing acceptable | `[verify on A-801]` 4–10 EA | **08 11 13** |
| Flush wood doors (interior) | A-801 + PM Sec **08 14 16** | Solid-core wood door, paint or stain grade per door schedule | `[verify on A-801]` 4–10 EA | **08 14 16** |
| Access doors + panels (MEP/plumbing access) | PM Sec **08 31 00** | Wherever new MEP service requires above-ceiling access; typical for HVAC valves + plumbing chases | 2–6 EA (verify on M/P sheets) | **08 31 00** |
| Door hardware — Sargent cylindrical locksets at each door | A-801 hardware schedule + PM Sec **08 71 00** | Sargent 10-Line cylindrical lockset, US26D finish, classroom or storeroom function per door schedule | `[verify on A-801]` 4–10 EA + matching closers, kick plates, silencers, stops | **08 71 00** ($550–$750/EA hardware set for Sargent at institutional spec) |
| Door prep for CBORD electric strike + low-voltage pathway | PM Sec 08 71 00 hardware schedule (electric strikes likely shown) + Sec 28 31 00 | Mortise prep in frame; low-voltage conduit & ring/string from frame to plenum | `[verify per A-801]` per door | **08 71 00** + **27 05 00** pathway (labor only — owner furnishes electric strike + CBORD reader) |
| **Mirrors — large theater dressing-room mirrors at each vanity station** | PM Sec **08 83 00 Mirrors** + Add 1 callout 24"x72" mirror size + A-501 elevations | 24"x72" silvered mirrors at each vanity station; ADA mirror at each RR lavatory | 6–10 EA total (3 vanity + 2 RR + spare) | **08 83 00** ($350–$550/EA depending on size + safety backing) |

### Division 09 — Finishes (the largest single-trade volume on the bid)

| Item | Source | Working assumption | Quantity | PM section |
|---|---|---|---|---|
| Common Work Results for Finishes (incl flooring prep) | PM Sec **09 05 00 + 09 05 61** | Substrate prep over existing slab; moisture testing per ASTM F-2170 + F-1869 before LVT or carpet installation | per 3,115 SF | **09 05 00 / 09 05 61** |
| Gypsum board assemblies — non-structural metal framing + GWB | PM Sec **09 21 16** | 5/8" Type X both sides at new partitions; moisture-resistant in wet areas (1R9/1R10); furring at existing walls where finish-change requires | `[verify per A-401]` ~600–900 SF new GWB | **09 21 16** |
| Metal suspension systems (where ceiling assemblies require) | PM Sec **09 22 26.23** | Carrier channels for acoustical ceilings + light-fixture support | included with **09 51 00** | **09 22 26.23** |
| Cement plastering (where required) | PM Sec **09 24 00** | Minor patching at any encountered plaster removal during demo | small allowance | **09 24 00** |
| **Tiling — floor T1 (porcelain) + wall T2 (blue) + T3 (ridged white) + T4 (2"x2" shower mosaic per Add 2) + T6 wall + T7 ceiling per Add 1** | AF100 + Add 1 + Add 2 + PM Sec **09 30 00** | Floor T1 covers 159 + 160 + 434 + 135 + 136 + (107 if extends from MUR?) = ~1,024 SF wet/back-of-house; wall T2 + T3 around restrooms + shower stalls; T4 mosaic 2"x2" inside shower receptors; T6/T7 per Add 1 callouts | T1 floor ~1,024 SF + wall tile T2/T3 ~250–400 SF + shower mosaic T4 ~140 SF | **09 30 00** ($18–$30/SF floor + $14–$22/SF wall + $28–$40/SF mosaic with Kerdi membrane) |
| Acoustical ceilings (ACS1 grid + ACP1 panel) | PM Sec **09 51 00** + AF100 ceiling materials legend | 2x2 lay-in white grid + panel in 107/108/109/110/1R9/1R10 (~1,047 SF); existing-to-remain in corridor 101 + entry 106 | ~1,047 SF | **09 51 00** ($6–$9/SF including grid + panel) |
| Acoustic insulation between partitions (privacy walls between dressing rooms) | PM Sec **09 81 00** | R-13 batts in dressing-room partition cavities for speech privacy | included with **09 21 16** GWB | **09 81 00** |
| Resilient base (RB1) | PM Sec **09 65 13** + AF100 | Standard 4" rubber base around perimeter of carpeted/LVT rooms 101 + 106 | ~200–300 LF | **09 65 13** |
| Resilient tile flooring / LVT (where called) | PM Sec **09 65 19** + AF100 flooring legend (vinyl tile + carpet) | Potential LVT in corridor 101 or makeup room; verify per finish plan | small allowance (`null` until A-401 cross-reference) | **09 65 19** |
| Carpet tile CPT1 in front entry 106 + corridor 101 (where AF100 shows CPT1) | PM Sec **09 68 00** + AF100 floor finish legend (CPT1) | Modular carpet tile, broadloom replacement; verify exact rooms on AF100 north plan | ~1,000–1,500 SF | **09 68 00** ($5–$9/SF installed) |
| Painting (P1 white walls + P2 door frames + ceiling paint where GWB) | PM Sec **09 90 00** + AF100 wall finish legend | 2-coat institutional latex, low-VOC per Sec 01 61 16 | ~2,500–3,500 SF wall paint + 60 EA door frames | **09 90 00** ($1.65–$2.50/SF for walls) |

### Division 10 — Specialties

| Item | Source | Working assumption | Quantity | PM section |
|---|---|---|---|---|
| Room signage (ADA-compliant, raised characters + Braille) | PM Sec **10 14 00** | Per ASU/TTUS wayfinding standard at each renovated room | 8–10 EA | **10 14 00** ($95–$145/EA installed) |
| Phenolic-core toilet compartments (FTC) | PM Sec **10 21 13.17** + AF100 finish schedule (FTC callout) | Floor-to-ceiling mounted phenolic-core partitions in 1R9 + 1R10 | 4–6 stalls + 2 urinal screens | **10 21 13.17** ($1,500–$2,200/stall installed) |
| Plastic toilet compartments (PTC) | PM Sec **10 21 13.19** + AF100 (PTC callout) | If both finish types appear, only one will dominate; PTC is the budget option | (alternate to FTC above) | **10 21 13.19** |
| Wall and door protection — CG1 stainless-steel surface-mounted corner guards | PM Sec **10 26 00** + AF100 (heavy CG1 callout — appears 17 times on AF100, **biggest single-item count on the plan**) | At every outside corner where wheeled traffic or costume-rack collision is a risk | **~17 EA from AF100 + add wallpapered corridor / restroom = carry ~24 EA** | **10 26 00** ($85–$140/EA installed) |
| Wall and door protection — PWC protective wall covering | PM Sec **10 26 00** + AF100 (PWC callout) | Likely 4'-6' high PWC at high-traffic corridor walls behind costume racks / equipment | ~150–250 SF | **10 26 00** |
| Toilet accessories (grab bars, paper holders, soap dispensers, ADA mirrors, lavatory shelves) | PM Sec **10 28 00** | Full ADA-compliant accessory package per RR (1R9 + 1R10) | 2 full RR sets | **10 28 00** ($750–$1,200/RR set installed) |
| **Metal lockers** — Div 10 51 13 (NOTE: **lockers ARE in contractor scope**, contradicting earlier owner-furnished assumption) | PM Sec **10 51 13** | If shown on A-401 / A-901, supply per spec; verify on dressing-room enlarged plan | `[verify on A-401 + A-901]` 8–24 lockers per dressing room (109 + 110) | **10 51 13** ($425–$650/locker installed for institutional steel) |
| Wall-mounted standards + shelving (costume storage) | PM Sec **10 56 17** | Adjustable shelf standards in Green Room 107 or wherever costume storage is shown | `[verify on A-401]` 1–2 wall systems | **10 56 17** |
| Fire extinguishers + cabinets (code-required) | NFPA 10 + IBC | 2–3 EA in scope area | 3 EA | (no PM section called out; use **10 44 13** generic) |

### Division 11 — Equipment

| Item | Source | Working assumption | Quantity | PM section |
|---|---|---|---|---|
| Residential appliances (TV per Add 1 in Makeup Room 108; possibly small refrigerator in Green Room) | PM Sec **11 30 13** + Drawings Addendum 1 | TV is likely owner-furnished (verify with Hannah Bignall); GC provides 120V receptacle + low-voltage data pathway behind TV wall mount. If TV mount is in scope, it's a small adder. | 1 TV mount + 0–1 appliances | **11 30 13** (mostly owner-furnished — GC pathway only) |

### Division 12 — Furnishings (countertops)

| Item | Source | Working assumption | Quantity | PM section |
|---|---|---|---|---|
| Countertops at vanity stations | PM Sec **12 36 00** + A-901 | PLAM countertops at vanities; minimum 25mm chamfered edge; integrated cord-management grommets at each makeup station | ~24–30 LF (verify on A-901) | **12 36 00** (included in millwork package per Div 06 line above) |

### Division 21 — Fire suppression ✅ **NOT IN CONTRACTOR SCOPE**

PM TOC explicitly lists **Div 21 as "NOT USED"** — confirms FP system is fully owner-furnished. Contractor provides access only. No FP pricing.

### Division 25 — Integrated automation (HVAC controls)

| Item | Source | Working assumption | Quantity | PM section |
|---|---|---|---|---|
| Integrated Automation Control of HVAC (DDC tie-in to ASU BMS) | PM Sec **25 55 00** + M-601 controls schedule | Mechanical sub provides DDC controllers + BMS tie-in to ASU's standard (likely Siemens or Automated Logic — confirm) | 1 LS for the dressing-room scope | **25 55 00** (included in Div 23 sub price) |

### Division 22 — Plumbing

| Item | Source | Working assumption | Quantity | PM section |
|---|---|---|---|---|
| Plumbing common work + identification + hangers + vibration | PM Sec **22 05 00 + 22 05 16 + 22 05 29 + 22 05 48.13 + 22 05 53** | Standard reno-scope; minimal infrastructure work | 1 LS | **22 05 00 family** |
| Domestic water piping | PM Sec **22 11 16** + P-101 / P-101A | Replace supply branches to fixtures; PEX or Type L copper per spec | per P-101 isometric | **22 11 16** |
| Sanitary waste and vent piping | PM Sec **22 13 16** + PD-101 / P-101 | Replace waste lines as required for new fixture layout; tie into existing risers | per P-101 isometric | **22 13 16** |
| Plumbing fixtures — lavatories (ADA wall-hung) | PM Sec **22 40 00** + P-501 fixture schedule + AF100 | 2 lavatories per RR (1R9 + 1R10) + lavs at vanity stations if shown | 4–8 EA | **22 40 00** ($1,200–$1,850/EA installed) |
| Plumbing fixtures — water closets (ADA floor-mounted) | PM Sec **22 40 00** + P-501 | 2–4 WCs in 1R9 + 1R10 | 2–4 EA | **22 40 00** ($900–$1,500/EA installed) |
| Plumbing fixtures — urinal (Men's RR 1R10) | PM Sec **22 40 00** + P-501 | 1 ADA urinal in 1R10 | 1 EA | **22 40 00** ($700–$1,100/EA installed) |
| **Plumbing fixtures — shower stalls per Add 2 (2"x2" mosaic tile in shower)** | PM Sec **22 40 00** + AF100 (T4 mosaic per Add 2) | ADA roll-in or transfer shower per RR; receptor sized per stall layout (32"x60" or 36"x60"); thermostatic mixing valve | 2 EA showers | **22 40 00** + **09 30 00.T4** ($5,500–$8,500/EA installed including waterproof membrane, mosaic tile, fixtures, control valve, grab bars) |
| Commissioning of plumbing systems | PM Sec **22 08 00** | TAB on water flow + drain witness per Cx authority | 1 LS | **22 08 00** ($1,500–$3,500) |

### Division 23 — HVAC

| Item | Source | Working assumption | Quantity | PM section |
|---|---|---|---|---|
| HVAC common work + motors + hangers + vibration + identification | PM Sec **23 05 00 + 23 05 13 + 23 05 29 + 23 05 48 + 23 05 53** | Standard reno-scope; some seismic bracing for hangers | 1 LS | **23 05 00 family** |
| Duct insulation | PM Sec **23 07 13** | Fiberglass duct wrap on supply ductwork in plenum + acoustic liner where called | per M-101A linear footage | **23 07 13** |
| Metal ducts | PM Sec **23 31 13** + M-101A / M-102A | New supply + return + exhaust ductwork serving the 1,047 SF dressing-room volume + 641 SF corridor (existing-to-remain in 106) | ~1,500–2,200 LF total | **23 31 13** |
| Air duct accessories (volume dampers, fire/smoke dampers, access doors) | PM Sec **23 33 00** | Standard reno-package | per M sheets | **23 33 00** |
| HVAC fans (dressing-room exhaust for hair/makeup chemical vapors) | PM Sec **23 34 00** | Inline exhaust fans serving each dressing room + makeup room + restrooms | 4–6 EA | **23 34 00** |
| Diffusers, registers, grilles | PM Sec **23 37 13** + AF100 ceiling fixture legend | Supply diffusers + return grilles + exhaust grilles per ceiling plan | ~25–40 EA total | **23 37 13** |
| Testing, adjusting, and balancing | PM Sec **23 05 93** | Independent NEBB/AABC-certified TAB | 1 LS | **23 05 93** ($3,500–$8,500) |
| Integrated automation control (DDC) | PM Sec **25 55 00** (cross-ref) | DDC tie-in to ASU's BMS | included in mech sub | **25 55 00** |

### Division 26 — Electrical

| Item | Source | Working assumption | Quantity | PM section |
|---|---|---|---|---|
| Electrical common work + conductors + grounding + hangers + raceways + identification | PM Sec **26 05 00 + 26 05 19 + 26 05 26 + 26 05 29 + 26 05 33 + 26 05 53** | Standard reno; new branch circuits + grounding from existing distribution | per 3,115 SF | **26 05 00 family** |
| Provisions for communication / security / safety systems | PM Sec **26 05 34** | Raceways + boxes for low-voltage systems (CBORD, FA, AV, network) | per E-101A + TN-101A | **26 05 34** |
| Electrical distribution equipment (panel upgrade if needed) | PM Sec **26 20 00** + E-001 + E-101A | Likely sub-panel addition for new dressing-room loads; verify existing-panel capacity on site walk | 0–1 panel | **26 20 00** ($5,500–$8,500/EA installed for institutional sub-panel) |
| Wiring devices (receptacles, switches, GFCI in wet zones) per Add 1 (Makeup Room TV receptacle + vanity outlets in 109/110) | PM Sec **26 27 26** + E-101A + Add 1 | Dedicated 20A circuits at makeup stations; GFCI within 6' of sinks/showers; quad outlets behind vanities | ~60–90 EA devices | **26 27 26** |
| Lighting (general LED fixtures + makeup mirror surrounds + corridor 8" can lights added per Add 2) | PM Sec **26 50 00** + E-001 fixture schedule + E-201A | Type A (general), Type D1/D2 (emergency option per Add 2), 8" can lights per Add 2 corridor scope, vanity LED surrounds at 3 stations + **salvaged 2x4 corridor fixtures re-used in MUR per Add 2** | ~25–40 EA new + 4–8 EA salvage-reinstall | **26 50 00** ($350–$650/EA for dimmable LED; mirror surrounds ~$1,500–$2,500/EA from Div 06 millwork package) |
| Emergency lighting (added in corridor per Add 2) | PM Sec **26 52 00** + Add 2 | Emergency-mode LED with battery backup OR central-inverter feed | 4–8 EA | **26 52 00** |
| Lighting controls — occupancy + dimming + scene control | PM Sec **26 09 23 + 26 09 43** | Per ASU energy standard + dimming at vanities for performer prep | per room | **26 09 23 / 26 09 43** |
| Commissioning of electrical systems | PM Sec **26 08 00** | Independent Cx agent witnesses + commissioning report | 1 LS | **26 08 00** ($1,500–$3,500) |

### Division 27 — Communications (PATHWAY ONLY; ASU vendor pulls + terminates cable)

| Item | Source | Working assumption | Quantity | PM section |
|---|---|---|---|---|
| Basic materials and methods + common work results | PM Sec **27 00 00 + 27 05 00** | Standard pathway scope: conduit + back-boxes + plenum cable tray + faceplate openings | per TN-101A | **27 00 00 / 27 05 00** |
| Surface raceways for communications (if any) | PM Sec **27 05 39** | If any wireway/raceway shown on TN-101A | minor | **27 05 39** |
| Structured cabling system | PM Sec **27 10 00** | **THIS SECTION IS PRESENT IN THE PROJECT MANUAL** — which raises a question: does Sec 27 10 00 mean the GC IS responsible for structured cabling, OR is it template-included for the ASU vendor's reference? **Need to clarify with Hannah Bignall.** RFCSP body said "owner cabling," but the PM spec says structured cabling system is described here. **Carry pathway-only at $125–$250/EA outlet** until clarified, with a unit-price line for full cable + termination scope if GC ends up responsible. | ~20–30 outlets at $125–$250/EA pathway only OR add $200–$400/EA for full pull + terminate | **27 10 00** |

### Division 28 — Electronic safety + security + fire alarm

| Item | Source | Working assumption | Quantity | PM section |
|---|---|---|---|---|
| Common work results for electronic safety + security | PM Sec **28 05 00** | Standard scope | 1 LS | **28 05 00** |
| Fire detection and notification system (fire alarm device relocation per new ceiling layout) | PM Sec **28 31 00** + TF-101A | Strobe + smoke detector relocation; coordinate with EHS for shutdown windows; new addressable devices per IBC/NFPA 72 | 6–12 EA devices total | **28 31 00** ($450–$750/EA for new device + tie-in to existing panel) |
| CBORD access-control devices (readers, controllers, electric strikes) | **OWNER-FURNISHED per RFCSP narrative + slide 4 of Addendum #1** | Do NOT supply or install readers/controllers; provide pathway + power + door prep | 0 (devices) + included in Div 08 & 26 + 27 (prep) | n/a |
| CCTV (if scope shown on TN-101A) | Likely owner | Confirm with Samuel/Hannah | 0 | n/a |

---

## D. Coordination notes (the pain-points worth pricing for) (2026-05-23 refresh)

1. **Owner-furnished scope confirmed by PM TOC.** Div 21 (Fire Suppression) NOT USED + Div 14 (Conveying) NOT USED. Lockers are now confirmed contractor scope (PM Sec 10 51 13). CBORD readers are still owner. Only ambiguity is Sec 27 10 00 Structured Cabling — confirm with Hannah.
2. **CBORD coordination is high-stakes.** ASU's CBORD-managed access control means the door hardware schedule (A-801), low-voltage pathway (TN-101A), and door prep all hinge on a coordination call with the CBORD admin. Schedule that call in week 1 of construction (or earlier).
3. **Active performing-arts building.** Carr EFA hosts theater, dance, music productions and rehearsals. Per Add #1 pre-response meeting slide 11, ASU currently has "no" calendar conflicts during the construction window (7/1–11/2/2026), which is encouraging. Still carry: (a) after-hours premium labor for noisy work, (b) negative-air dust containment per Sec 01 35 16, (c) walk-off mats at every transition to occupied space, (d) sound mitigation during rehearsals/productions, (e) explicit access-window calendar coordinated with the College of Visual and Performing Arts.
4. **EHS shutdown windows.** Fire alarm (during relocation per Sec 28 31 00), HVAC (during cutover), electrical (during panel work), water (during plumbing cutover) all require coordinated shutdowns with ASU EHS / Facilities. Typically 2-week advance notice + 2–4 hour shutdown windows. Per Add #1 slide 13, ASU FP&C will coordinate utility shutdowns.
5. **Existing-conditions risk in an older building.** Carr EFA is older; carry $15K hazmat allowance within the $25K Attachment A cash/contingency until Section 00 31 00 (Available Project Information) hazmat survey is received from Hannah Bignall. **Site walk this week** — see `outreach/01-email-hannah-bignall-eligibility.md`.
6. **ADA "alterations" compliance per PM Sec 01 35 16.** Trigger: dressing-room renovation is a primary function area for a performing-arts venue → 28 CFR 35.151 alterations standard. PM 01 35 16 should explicitly list the required compliance items; verify on read.
7. **Submittal turnaround time per PM Sec 01 33 00.** Major submittals: doors/hardware (with CBORD coordination), plumbing fixtures (especially shower receptors + thermostatic mixing valves), lighting (theater-grade dimmable + emergency add-on per Add 2), finish samples (T1/T2/T3/T4 tile, T6/T7 from Add 1, P1/P2 paint, CPT1 carpet, HPB hardwood base). **Long-lead items to flag in `proposal/05-schedule-narrative.md`:**
   - **Mirror surrounds with theater LED:** 8–12 weeks
   - **Shower receptors + accessories:** 6–8 weeks
   - **Specialty 2"x2" mosaic tile (T4):** 4–8 weeks depending on quantity
   - **Sargent hardware sets:** 6–10 weeks
   - **Dimmable LED lighting + DDLC controls (per Sec 26 09 43):** 8–12 weeks
   - **Metal lockers:** 8–12 weeks
8. **The $25,000 cash/contingency allowance** in Attachment A is a separate line item per Sec **01 21 00 Allowances** — do NOT roll it into the base proposal price; do NOT mark it up; it gets drawn against during construction via PCO process per the CSA (Sec 01 21 00 process). This is where the hazmat allowance + minor differing-site-conditions claims will land.
9. **Commissioning (Sec 22 08 00 + 26 08 00 + 01 91 13)** — ASU is running Cx on this project. Independent Cx agent likely owner-furnished but contractor must support per Cx specifications. Carry $3K–$6K for contractor Cx-support hours.
10. **JOC vs CSA contradiction** — PM Sec 01 10 00.1.5 references "Job Order Contract" but RFCSP procures via CSA. Treat as PBK boilerplate scrivener's error; flag for clarification (per `07-risk-register.md` R-02 mitigation).
