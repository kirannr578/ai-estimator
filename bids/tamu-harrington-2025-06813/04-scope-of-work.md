# 04 — Scope of work (refined from portal-pulled CSP package, 2026-05-23)

> **Source:** the actual CSP package pulled from the e-Builder portal on 2026-05-23 — `inbox/opportunities/attachments/2026-05-21/tamu-csp/Harrington_Lab303_Drawings.pdf` (10 sheets, dated 5/7/2026 IFC) and `Harrington_Lab303_Specifications.pdf` (308 pp project manual). Patterson Architects PA Project No. 2605; MEP by River MEP, LLC.
> Site address: **540 Ross Street, Bldg #0435 (Harrington Tower), College Station, TX 77843.**
>
> Spec divisions explicitly **"NOT USED"**: 03 Concrete, 04 Masonry, 05 Metals, 08 Doors & Windows, 11 Equipment, 12 Furnishings, 13 Special Construction, 14 Conveying. **No casework spec in the project manual** — note the H2I casework Sub-06 file in the portal (pending re-download); casework appears to be design-deferred or sub-driven.
>
> Spec divisions **explicitly included**: 01 (Full set), 02 (02 26 23 Asbestos Assessment + 02 40 00 Demolition), 06 (06 10 00 Rough Carpentry only), 07 (07 90 00 Sealants), 09 (09 22 00 GWB, 09 51 00 Acoustical Ceilings, 09 65 00 Resilient Flooring, 09 91 00 Painting), 10 (10 14 00 Identifying Devices & Graphics), MEP divs 22 / 23 / 26 "see drawings" (no separate spec sections).
>
> Every quantity placeholder is `[TBD from drawings — user to measure in Bluebeam]` and ties back to a row in `takeoff-template.json`. The CSI section column references the seed cost DB at `config/cost_database.json` where a match exists.

---

## A. Assumptions confirmed / revised from portal pull

1. ~~**Single-room scope** — Lab 303 only.~~ ✅ **CONFIRMED.** Drawings cover only Lab 303 in Harrington Tower Bldg 0435 at 540 Ross Street.
2. ~~**Room area assumption — 1,200 SF.**~~ 🟡 **TO BE CONFIRMED from A2.1 Floor Plans.** User to measure room area in Bluebeam. Initial 1,200 SF working assumption holds until measured.
3. ~~**Existing wall structure stays.**~~ ✅ **CONFIRMED.** Drawing index shows no structural sheets; spec Div 03–05 marked NOT USED.
4. ~~**No structural mods.**~~ ✅ **CONFIRMED.** Same evidence as #3.
5. ~~**Occupied building.**~~ ✅ **CONFIRMED.** Section 01 41 00 "General Requirements for Renovation Work" (5 pp) governs renovation procedures; Section 01 50 00 Temporary Facilities (9 pp) governs site logistics. Section 01 31 00 Project Management & Coordination (6 pp) is the SSC-side coordination spec.
6. **Lab type — "Science Education Classroom/Lab"** — drawings package confirms a single Lab 303 reno with M1.1 mechanical, E1.1+E1.2 electrical (incl. demo plans), P1.1 plumbing. **NO fume hood spec in project manual** (Div 11 NOT USED — no lab equipment spec). **NO casework spec** in Div 06 spec set (only 06 10 00 Rough Carpentry, which is wall blocking and similar — no 06 41 lab casework spec). The H2I casework Sub-06 file in the portal is most likely a bid-only sub-quote on casework; the *casework details* are likely on A2.1/A2.2 only. **Verify on the drawings + once H2I file is retrieved.**
7. **Asbestos handling is in scope.** Section 02 26 23 "Asbestos Assessment" (15 pp) is in the project manual — establishes the procedure for handling any asbestos found during the renovation. Section 02 40 00 Demolition is the demo spec. **Carry an abatement allowance** in the takeoff per `03-missing-documents.md` item #14. The TAMU EHS survey is implicitly already done (otherwise the asbestos-assessment-procedure spec would not be in the project manual) — confirm with Joelle whether a clearance certificate exists.
8. **No fire-suppression spec in package — handle by deferred-submittal or T&M with the existing building sprinkler vendor.** Spec divisions list shows no Div 21 spec section (FP sheets are not in the 10-sheet drawing set). Sprinkler-head relocation triggered by ceiling rework will need to be either a deferred-submittal item (proposed in Technical Proposal) or carried as an allowance for the existing TAMU building sprinkler vendor to T&M.
9. **No new exterior or site work** — Divs 31, 32, 33 NOT USED; no civil sheets in the drawing set.

---

## B. Trade-by-trade scope draft

### Division 01 — General requirements

| Item | Notice says | Reasonable assumption | Quantity placeholder | CSI section (cost-DB) |
|---|---|---|---|---|
| General conditions / project supervision | (not enumerated) | PM + super for 60–90 days; reduced presence after substantial completion | `[TBD: duration in months × monthly rate]` | `01 00 00` ($12,000/mo seed) |
| Temporary facilities, controls, dumpsters, PPE | (not enumerated) | Dust containment, negative-air, walk-off mats, dumpster in TAMU-approved location, portable toilet at construction lay-down | 1 LS | `01 50 00` ($6,500 LS seed) |
| Project closeout — O&M manuals, attic stock, training, as-builts | (not enumerated) | Standard TAMU SGC requirement | included in GCs | — |
| Coordination with TAMU EHS, Tech Services, Facilities | Yes — implied | EHS pre-work meeting + during-work check-ins; Tech Services for low-volt; Facilities for shutdowns | included in GCs | — |

### Division 02 — Existing conditions / selective demolition

| Item | Spec section | Reasonable assumption | Quantity placeholder | CSI section / cost-DB |
|---|---|---|---|---|
| **Asbestos assessment + abatement procedure** | **02 26 23 (15 pp)** | Procedure spec in the project manual — establishes handling protocol for any asbestos encountered during the renovation. **Carry an abatement allowance** until a clearance certificate is shared by Joelle. | `[TBD: LS allowance]` | no cost-DB hit; carry $3K–$10K allowance for a single-room reno |
| Selective interior demo of existing finishes (flooring, base, ceiling tile, casework) | 02 40 00 Demolition (4 pp) | Strip room to perimeter walls & structure | `[TBD: measure from A2.1 demo plan]` | `02 41 16` ($4.50/SF seed) |
| Demo of existing non-structural partitions if floor plan changes | 02 40 00 | Confirm against drawings | `[TBD: LF of demo partition from A2.1]` | `02 41 16` |
| Demo of existing casework / countertops | 02 40 00 | Remove and dispose | `[TBD: LF from A2.1]` | `02 41 16` |

### Division 06 — Carpentry (no casework spec in project manual)

| Item | Spec section | Reasonable assumption | Quantity placeholder | CSI section / cost-DB |
|---|---|---|---|---|
| Wall blocking for shelving, monitors, ADA grab, AV mount | **06 10 00 Rough Carpentry (5 pp)** | Per the only Div 06 spec in the project manual | `[TBD: LS / SF]` | `06 10 00` |
| **Lab casework** (base + wall cabs, work tops) | **Not in spec.** See drawings A2.1 / A2.2 for any casework details, plus the H2I Sub-06 file (pending re-download). | If casework is shown on the drawings only, this is a design-light approach — most likely the casework scope is captured as a furniture / lab-equipment line that the GC carries as a lab-casework allowance OR awards to H2I per their Sub-06 pricing. **Carry an allowance until A2.1 + H2I file are reviewed.** | `[TBD: allowance or LF from drawings]` | no cost-DB hit; carry $20K–$60K allowance for a single lab room |

### Division 07 — Thermal and moisture protection

| Item | Spec section | Reasonable assumption | Quantity placeholder | CSI section |
|---|---|---|---|---|
| Sealants — at flooring transitions, fixture trims, and any opening sealing | **07 90 00 Sealants (5 pp)** | Small allowance | `[TBD: LF allowance]` | no cost-DB hit; carry as part of finishes labor |

### Division 08 — Openings (NOT USED per spec)

| Item | Status |
|---|---|
| Doors, frames, hardware | **Spec division NOT USED.** Existing door stays; no replacement scope. **Remove this row from `takeoff-template.json`**. |

### Division 09 — Finishes (refined — single-spec resilient flooring, no LVT/sheet-vinyl split)

| Item | Spec section | Reasonable assumption | Quantity placeholder | CSI section |
|---|---|---|---|---|
| Metal-stud framing + gypsum wallboard (for any new partitions or furring) | **09 22 00 Gypsum Wallboard (6 pp)** | Confirm partitions against A2.1; 5/8" Type X both sides where called out | `[TBD: SF from A2.1]` | `09 22 16` / `09 29 00` (combined per spec) |
| Acoustical ceiling — replace existing | **09 51 00 Acoustical Ceilings (4 pp)** | 2x4 lay-in grid + tile, full room replacement | `[TBD: measure from A2.2]` | `09 51 13` ($5.10/SF seed) |
| **Resilient flooring** (single spec — type TBD from finish plan on A2.1) | **09 65 00 Resilient Flooring (5 pp)** | **Single resilient-flooring spec section** — no split between classroom-LVT and wet-lab-sheet-vinyl in the project manual; the finish plan on A2.1 will identify which resilient product. **Treat as a single resilient-flooring line in the takeoff.** | `[TBD: room area from A2.1]` | `09 65 19` ($6.40/SF seed if LVT). |
| Resilient base | Same spec (09 65 00) | 4" rubber base | `[TBD: LF of room perimeter + casework toe-kick]` | `09 65 13` ($3.25/LF seed) |
| Painting — walls + soffits + door frames | **09 91 00 Painting (10 pp)** | 2-coat institutional latex, low-VOC | `[TBD: SF of paint surface]` | `09 91 23` ($1.65/SF seed) |

### Division 10 — Specialties (signage only per project manual)

| Item | Spec section | Reasonable assumption | Quantity placeholder | CSI section |
|---|---|---|---|---|
| Room signage (ADA-compliant — see A0.2/A0.3 TAS sheets) | **10 14 00 Identifying Devices & Graphics (3 pp)** | "Lab 303" room sign + ADA tactile sign per TAMU wayfinding standard | 1–2 EA | `10 14 00` ($95/EA seed) |
| Tackable wall panels / marker board / AV mounting board | **Not in spec.** Confirm against A2.1 plans. If shown, carry as deferred-submittal in technical proposal. | (likely owner-furnished or out of GC scope) | — | — |
| Fire extinguishers | Not in spec | Confirm via TAMU EHS / fire-life-safety review | — | — |

### Division 11 — Lab Equipment (NOT USED per spec)

| Item | Status |
|---|---|
| Fume hood, lab equipment | **Spec division NOT USED.** No GC scope for lab equipment — TAMU furnishes any lab equipment separately. **Remove these rows from `takeoff-template.json`.** |

### Division 21 — Fire Suppression (NOT in spec — handle via deferred-submittal or T&M)

| Item | Spec section | Reasonable assumption | Quantity placeholder | CSI section |
|---|---|---|---|---|
| Sprinkler head relocation per new ceiling layout | **No Div 21 spec section in the project manual; no FP sheets in the drawing set.** | Ceiling rework triggers some sprinkler-head adjustment; handle via (a) deferred submittal proposed in Technical Proposal, or (b) carry an allowance for the existing TAMU building sprinkler vendor to perform on T&M with EHS-coordinated shutdowns. | `[TBD: 4–10 EA allowance]` | no cost-DB hit; carry $250–$450/EA per-head allowance |

### Division 22 — Plumbing (per P1.1 + MEP1.0)

| Item | Drawing | Reasonable assumption | Quantity placeholder | CSI section |
|---|---|---|---|---|
| Lab sink(s), faucets, gooseneck spouts | **P1.1 Plumbing Plans** | Count from P1.1 fixture schedule | `[TBD: 1–4 EA from P1.1]` | `22 40 00` ($1,850/EA seed for fixture incl. rough; lab fixture trims at ~$2,500–$3,500/EA) |
| Eye-wash / safety-shower combo (plumbed) — if shown | P1.1 | Confirm against P1.1 — typical lab requirement | `[TBD: 0–1 EA]` | no cost-DB hit (carry ~$3,500–$5,500/EA installed) |
| DI water / lab gas / acid waste — if shown | MEP1.0 + P1.1 | Confirm against P1.1 — if not shown, not in scope | `[TBD: from P1.1]` | no cost-DB hit |

### Division 23 — HVAC (per M1.1 + MEP1.0)

| Item | Drawing | Reasonable assumption | Quantity placeholder | CSI section |
|---|---|---|---|---|
| HVAC modifications — diffuser/grille relocation, VAV box retrim | **M1.1 Mechanical Plan** | Light reconfiguration to match new ceiling layout from A2.2 | `[TBD: count diffusers / grilles on M1.1]` | `23 00 00` ($22.50/SF seed — too high for a single-room retrim; real cost ~$8–$15/SF) |
| Lab exhaust modifications | M1.1 | Confirm against M1.1 — likely none since Div 11 NOT USED | `[TBD: from M1.1]` | no cost-DB hit |
| Air balance + test report (TAB) | MEP1.0 spec | Required per MEP1.0 spec | `[TBD: 1 LS]` | $2,500–$5,000 range |

### Division 26 — Electrical (per E1.1 + E1.2 + MEP1.0)

| Item | Drawing | Reasonable assumption | Quantity placeholder | CSI section |
|---|---|---|---|---|
| Demolition of existing electrical | **E1.1 Electrical Demo Plans** | Remove + cap circuits per E1.1 | `[TBD: SF served]` | `02 40 00` / `26 05 00` |
| Lighting — LED fixtures + classroom controls | **E1.2 Electrical Plans** | Replace all fixtures; new controls per E1.2 fixture schedule | `[TBD: count from E1.2]` | `26 51 00` ($285/EA seed for typical fixture) |
| Branch wiring + devices — receptacles, switches, GFCI within 6' of sinks | E1.2 | Per E1.2 device plan | `[TBD: SF / device count from E1.2]` | `26 05 00` ($8.40/SF seed) |
| Emergency egress lighting | E1.2 | Per code; verify from E1.2 | `[TBD: EA]` | no cost-DB hit |
| Sub-panel for lab loads — if shown | E1.2 | Confirm against E1.2 panel schedule | `[TBD: 0–1 EA]` | $4,500–$7,000/EA |

### Division 27 — Communications / low-voltage (NOT in spec — pathway only by GC, per typical TAMU pattern)

| Item | Assumption | Quantity placeholder | CSI section |
|---|---|---|---|
| Data + AV pathway (conduit, J-box, ring & string) | TAMU Tech Services furnishes cable + termination; GC furnishes pathway only. Coordinate. | `[TBD: count outlets from E1.2 or A2.1]` | no cost-DB hit |

### Division 28 — Electronic safety / security / fire alarm (NOT in spec — handle as needed via existing TAMU vendors)

| Item | Assumption | Quantity placeholder |
|---|---|---|
| Fire-alarm device relocation per new ceiling layout | Coordinate with TAMU EHS / existing FA vendor on T&M | `[TBD: EA]` |
| Card-access door reader if scope changes — likely none since Div 08 NOT USED | — | — |

---

## C. Coordination notes (refined post-portal-pull)

1. **Occupied building.** Harrington Tower (Bldg 0435, 540 Ross St.) is an active academic tower. Section 01 41 00 "General Requirements for Renovation Work" governs. Carry **after-hours premium labor** for at least demo and any HVAC / sprinkler shutdown work.
2. **EHS shutdown windows for fire alarm + sprinkler.** Since Div 21 / Div 28 are not in the project manual, fire-alarm and sprinkler shutdowns will be coordinated through SSC + the existing TAMU building FA / sprinkler vendor on T&M; reflect in the schedule.
3. **TAMU Tech Services owns the cabling.** GC scope ends at the pathway; the cable, jack, and termination are TAMU. Don't accidentally bid the cable.
4. **Asbestos handling is procedurally scoped in 02 26 23.** The 15-page asbestos-assessment spec section implies TAMU EHS has a known protocol for any asbestos discovered during demo — most likely a Texas-licensed abatement sub is on-call. **Confirm with Joelle whether a clearance certificate exists for Lab 303 prior to demo, OR carry an asbestos-abatement allowance + 5–10-day schedule float.**
5. **Adjacent-lab impact.** Confirm against M1.1 / P1.1 whether Lab 303 shares any plenum / riser / main with adjacent labs; coordinate cutovers with the adjacent-room user.
6. **Patterson Architects + River MEP both look like small Texas A/E shops.** Carry ~5–10% RFI churn in the schedule; price extra PM hours in GCs.
7. **Substantial Completion is bidder-chosen and 10% of the evaluation score** (per CSP §00 21 00 ¶11.2). **Final Completion is fixed at 30 calendar days after Substantial Completion.** The shorter the proposed duration, the higher the score — but the harder it is to deliver. Pricing-vs-time trade-off: do not propose <45 calendar days for this scope without a defensible CPM schedule in the Technical Proposal.
8. **Proposal valid for 90 calendar days.** Hold the price commitment for 90 days post-submittal (per CSP §00 42 13 ¶3).
9. **CSI-division line-item pricing is the proposal format.** The Section 00 42 13 form requires a $ amount for each CSI division actually in scope (blank for not-in-scope), or the bid is disqualified for being incomplete. Roll the takeoff into CSI-division subtotals: **01, 02, 06, 07, 09, 10, 22, 23, 26** are the divisions that will likely carry non-zero amounts on the pricing form.
10. **Sample contract is the SSC/Compass Master Vendor Agreement (Section 00 52 63).** Before bidding, the firm should flag MVA §6 (2-year non-solicit), §7 (1-year non-compete with the Client), §5 (Net-75-day payment terms), and §13 (sub flow-down insurance limits including $10M CGL aggregate + $10M Umbrella) to leadership. **These are not blocking on bid submission but may inform the price (high insurance limits + slow payment terms increase carry cost).**
