# 04 — Scope of work (draft, pre-drawings)

> Source: Notice of Project ("303 Science Education Classroom/Lab Renovation") plus the user's expanded scope brief, cross-referenced against typical TAMU System single-room educational lab renovations.
>
> Every quantity placeholder is `[TBD from drawings]` and ties back to a row in `takeoff-template.json`. The CSI section column references the seed cost DB at `config/cost_database.json` where a match exists; rows tagged "**no cost-DB hit**" will need the F1 (CWICR) cost-DB land to deliver a unit price.

---

## A. Assumptions baked in (until drawings prove otherwise)

1. **Single-room scope** — Lab 303 only. The Notice ties scope to "303 Science Education Classroom/Lab," not the whole building.
2. **Room area assumption** — 800–1,500 SF typical for a single college science classroom/lab room in a TAMU office tower. Carry **1,200 SF** as the working assumption.
3. **Existing wall structure stays** — perimeter demising walls remain; only the interior finish layer and any non-structural partitions get touched.
4. **No structural mods** — slab and ceiling structure are not affected; demo + reno is interior-only.
5. **Occupied building** — adjacent labs and classrooms continue operating; dust containment, after-hours noisy work, and EHS shutdown windows for fire-alarm and sprinkler work are required.
6. **Lab type is "science classroom/lab"** — implies general chemistry / biology bench layout, eyewash + safety shower, possible fume hood, possible lab gas, possible DI water. Confirm against the drawings; a heavy-chemistry lab vs a "STEM teaching classroom with sinks" doubles the MEP cost.
7. **No abatement budgeted** — pending TAMU EHS survey. If the existing flooring is mid-century VCT or the existing ceiling has any asbestos pipe insulation in the plenum, this assumption flips and a Div 02 abatement line gets added.

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

| Item | Notice says | Reasonable assumption | Quantity placeholder | CSI section |
|---|---|---|---|---|
| Selective interior demo of existing finishes (flooring, base, ceiling tile, casework) | Yes — "interior demo" | Strip room to perimeter walls & structure | `[TBD: ~1,200 SF]` | `02 41 16` ($4.50/SF seed) |
| Demo of existing non-structural partitions if floor plan changes | Maybe | Confirm against drawings | `[TBD: LF of demo partition]` | `02 41 16` |
| Demo of existing casework / countertops | Yes — implied by "casework/cabinetry" | Remove and dispose | `[TBD: LF of casework]` | `02 41 16` |
| Hazmat abatement | Not stated | **Pending TAMU EHS survey**. Carry allowance only after survey returns. | `[TBD: 0 or allowance]` | no cost-DB hit |

### Division 06 — Carpentry / casework

| Item | Notice says | Reasonable assumption | Quantity placeholder | CSI section |
|---|---|---|---|---|
| Lab-grade casework — base cabs, wall cabs | Yes — "casework/cabinetry" | Plastic-laminate base + wall cabs with phenolic resin or epoxy work tops; lab-grade hinges & pulls | `[TBD: LF of base, LF of wall]` | `06 41 00` ($425/LF seed for general millwork — **lab-grade premium runs $600–$900/LF; the seed entry is light**) |
| Lab work tops — phenolic resin or epoxy resin | Yes — implied | Chemical-resistant horizontal surface | `[TBD: SF of work top]` | no cost-DB hit (specialty material) |
| Wall blocking for shelving, monitors, ADA grab | Likely | Carry as small allowance | `[TBD: LS]` | `06 10 00` |

### Division 08 — Openings (doors, frames, hardware)

| Item | Notice says | Reasonable assumption | Quantity placeholder | CSI section |
|---|---|---|---|---|
| Replace existing door, frame, hardware (if scope) | Not stated — confirm against drawings | Single classroom door; existing may stay if condition is good | `[TBD: 0–2 EA]` | `08 14 16` ($575/EA seed wood door) |
| New door hardware | Maybe | Institutional grade, ANSI Grade 1, ADA lever | `[TBD: 0–2 sets]` | `08 71 00` ($425/EA seed) |
| Vision lite kit in classroom door (per TAMU code) | Maybe | Code requires line-of-sight into classroom; existing may already have | `[TBD]` | no cost-DB hit |

### Division 09 — Finishes

| Item | Notice says | Reasonable assumption | Quantity placeholder | CSI section |
|---|---|---|---|---|
| Metal-stud framing for any new partitions or furring | Maybe | Confirm against drawings | `[TBD: SF of new partition]` | `09 22 16` ($6.40/SF seed) |
| Gypsum board on framing | Same as above | 5/8" Type X both sides | `[TBD: SF, both faces]` | `09 29 00` ($2.85/SF seed) |
| Acoustical ceiling — replace existing | Likely | 2x4 lay-in grid + tile | `[TBD: ~1,200 SF]` | `09 51 13` ($5.10/SF seed) |
| Flooring — VCT or LVT in classroom zone | Yes — implied | LVT is the current TAMU classroom standard; chemical-resistant sheet vinyl with heat-welded seams in any "wet" lab zone | `[TBD: ~1,200 SF; split classroom vs lab]` | `09 65 19` ($6.40/SF seed for LVT). Sheet vinyl in lab zone is a **no cost-DB hit**; carry ~$10–$14/SF allowance |
| Resilient base | Yes — implied | 4" rubber base, integral or cove | `[TBD: LF of perimeter]` | `09 65 13` ($3.25/LF seed) |
| Painting — walls + soffits + door frames | Yes — explicit | 2-coat institutional latex, low-VOC | `[TBD: SF of paint surface]` | `09 91 23` ($1.65/SF seed) |
| Epoxy paint in wet lab zone | Maybe | If lab area requires washdown | `[TBD]` | no cost-DB hit |

### Division 10 — Specialties

| Item | Notice says | Reasonable assumption | Quantity placeholder | CSI section |
|---|---|---|---|---|
| Room signage (ADA-compliant) | Likely | "Lab 303" room sign per ADA + TAMU wayfinding standard | 1–2 EA | `10 14 00` ($95/EA seed) |
| Tackable wall panels / marker board / AV mounting board | Maybe | Educational classroom standard | `[TBD]` | no cost-DB hit |
| Eye-wash / safety-shower (if not in Div 22) | Yes — lab implies | Combination eye-wash + drench shower at lab sink | 1 EA | no cost-DB hit |
| Fire extinguishers | Yes | Per code review | 1–2 EA | no cost-DB hit |

### Division 11 — Lab equipment

| Item | Notice says | Reasonable assumption | Quantity placeholder | CSI section |
|---|---|---|---|---|
| Existing lab equipment to remain / be relocated | Yes — implied by "lab utility coordination" | TAMU likely owner-furnishes major lab equipment; GC roughs in utilities | `[TBD: EA fixtures / equipment]` | no cost-DB hit |
| Fume hood — install, modify, or remove | Maybe | If room has a fume hood, this is a major MEP coordination point | `[TBD]` | no cost-DB hit |

### Division 21 — Fire suppression

| Item | Notice says | Reasonable assumption | Quantity placeholder | CSI section |
|---|---|---|---|---|
| Sprinkler head relocation per new ceiling layout | Likely (any ceiling rework triggers) | 4–10 heads typical for a single room | `[TBD: EA heads]` | `21 13 00` ($4.85/SF seed; per-head pricing not in seed DB — carry $250–$450 per head allowance) |

### Division 22 — Plumbing

| Item | Notice says | Reasonable assumption | Quantity placeholder | CSI section |
|---|---|---|---|---|
| Lab sink, faucet, gooseneck spout | Yes — "plumbing modifications" | 1–4 sinks typical | `[TBD: 1–4 EA]` | `22 40 00` ($1,850/EA seed for fixture incl. rough; lab fixture trims at ~$2,500–$3,500/EA) |
| Eye-wash / safety-shower combo (plumbed) | Yes — lab implies | 1 unit at lab sink area | 1 EA | no cost-DB hit (carry ~$3,500–$5,500/EA installed) |
| DI water tap (if program requires) | Maybe | Polishing loop tap | `[TBD]` | no cost-DB hit |
| Acid-waste piping / neutralization tank | Maybe | Only if "wet chemistry" use | `[TBD]` | no cost-DB hit |
| Lab gas (natural gas / compressed air / vacuum) | Maybe | Only if program requires | `[TBD: LF + outlets]` | no cost-DB hit |

### Division 23 — HVAC

| Item | Notice says | Reasonable assumption | Quantity placeholder | CSI section |
|---|---|---|---|---|
| HVAC modifications — diffuser/grille relocation, VAV box retrim | Yes — "HVAC modifications" | Light reconfiguration to match new layout | `[TBD: SF served]` | `23 00 00` ($22.50/SF seed) — note this is light-commercial RTU+duct; for an existing-system retrim, real cost is typically ~$8–$15/SF |
| Lab exhaust modifications (if fume hood / canopy hood) | Maybe | Major scope if present | `[TBD]` | no cost-DB hit |
| Air balance + test report (TAB) | Yes — typical SGC requirement | 1 LS | `[TBD]` | no cost-DB hit |

### Division 26 — Electrical

| Item | Notice says | Reasonable assumption | Quantity placeholder | CSI section |
|---|---|---|---|---|
| Lighting — LED retrofit + classroom controls (occupancy + daylight + dimming) | Yes — explicit | Replace all fixtures; new controls | `[TBD: EA fixtures, ~1,200 SF]` | `26 51 00` ($285/EA seed for typical fixture) |
| Branch wiring + devices — receptacles for lab benches, AV outlets | Yes — implied by "electrical" | Dedicated 20A circuits at lab benches; GFCI within 6' of any sink | `[TBD: ~1,200 SF]` | `26 05 00` ($8.40/SF seed) |
| Emergency egress lighting | Likely | Per IBC | `[TBD: EA]` | no cost-DB hit |
| Possible sub-panel for lab loads | Maybe | Only if heavy-equipment loads | `[TBD]` | `26 24 16` (residential-spec seed — under-spec for institutional; carry $4,500–$7,000/EA for a real lab panel) |

### Division 27 — Communications / low-voltage

| Item | Notice says | Reasonable assumption | Quantity placeholder | CSI section |
|---|---|---|---|---|
| Data drops + AV pathway / J-box / conduit | Yes — "technology infrastructure coord" | Coordinate with TAMU Tech Services; GC typically furnishes pathway (conduit, J-boxes, ring + string); TAMU furnishes the cable and termination | `[TBD: # outlets]` | no cost-DB hit |
| Classroom AV — projector / display, ceiling speakers, mic array | Yes — implied by "technology" | Typically owner-furnished, owner-installed; GC provides power + pathway | `[TBD]` | no cost-DB hit |

### Division 28 — Electronic safety / security / fire alarm

| Item | Notice says | Reasonable assumption | Quantity placeholder | CSI section |
|---|---|---|---|---|
| Fire-alarm device relocation per new ceiling layout | Likely | Strobe + smoke detector relocation | `[TBD: EA]` | no cost-DB hit |
| Building access / door reader if classroom is card-access | Maybe | TAMU often standardizes on Lenel; coordinate | `[TBD]` | no cost-DB hit |

---

## C. Coordination notes (the pain-points worth pricing for)

1. **Occupied building.** Harrington Education Center is an active office / academic tower. Expect: no daytime jackhammering, dust containment with negative-air, restricted dumpster placement, mandatory after-hours work for any noisy / odor-generating tasks. Carry **after-hours premium labor** for at least demo and any HVAC / sprinkler shutdown work.
2. **EHS shutdown windows.** Fire alarm, sprinkler, and any plenum work require coordinated shutdowns with TAMU EHS. Typically 2-week advance notice + 2–4 hour shutdown windows. Doesn't kill the schedule but means your sub can't decide last-minute.
3. **TAMU Tech Services owns the cabling.** GC scope ends at the pathway; the cable, jack, and termination are TAMU. Don't accidentally bid the cable.
4. **TAMU EHS owns hazmat clearance.** Don't accept "no asbestos / no lead" without the TAMU EHS survey in hand. Older campus buildings can have surprises.
5. **Adjacent-lab impact.** If Lab 303 shares a return-air plenum, exhaust stack, lab-gas main, or DI water riser with an adjacent active lab, coordinate the cutover window with the adjacent-lab PI. This is where lab renos most commonly slip.
6. **Patterson Architects is a small firm.** Small A/E shops can produce thin drawing packages. Carry ~5–10% RFI churn in the schedule; price extra PM hours in GCs.
7. **Project start = TBD.** Bid your schedule against a generic "60 calendar days from NTP" or "90 calendar days from NTP" unless the CSP package specifies. The summer-fall academic-calendar window matters — if TAMU wants the room ready for spring semester, the substantial completion window narrows.
8. **TAMU prefers a single point of accountability.** Even though there are many subs, the proposal narrative should emphasize one PM-of-record and a clean RACI.
