# Scope outline — HHSC Bldg 500 Mechanical Room Renovation

> **Source:** Transcribed from §1 and §7.1 of `ESBD_520042_..._HHS0017366_PCS_137_Building 500 Mechanical Room Renovation.pdf` (pages 4 + 11–12). The IFB extends to page 41 and additional scope detail may exist in §7.2+ — see [`03-missing-documents.md`](./03-missing-documents.md).

## High-level scope (verbatim from §1)

> "Complete demolition, structural reinforcement, industrial generator removal, and installation of a new commercial overhead door."

## Detailed scope (transcribed from §7.1)

### §7.1.1 — Demolition & Structural Prep

| § | Activity | Self/Sub |
|---|---|---|
| 7.1.1.1 | **Roofing demo** — Remove existing metal roof sheets and dispose of all debris at an authorized facility | Sub (roofing) |
| 7.1.1.2 | **Structural inspection** — Inspect all exposed metal beams for damage or corrosion | BPC PM + structural eng. sub if needed |
| 7.1.1.3 | **Structural reinforcement** — Install replacement steel beams as required to ensure structural integrity | Sub (structural steel) |

### §7.1.2 — Industrial Generator Removal (Hazardous Material Handling)

| § | Activity | Self/Sub |
|---|---|---|
| 7.1.2.1 | **Decommissioning** — Disconnect all electrical, exhaust, and fuel systems | Sub (electrical + mechanical) |
| 7.1.2.2 | **Fluid management** — Drain and safely remove all coolant, oil, and fuel from the non-working industrial generator prior to rigging | **Sub (hazmat, specialty)** |
| 7.1.2.3 | **Rigging & extraction** — Use a crane and rigging gear to lift, load, and move generator to the back of SH maintenance shop | **Sub (rigging, specialty)** |

### §7.1.3 — Overhead Door Installation

| § | Activity | Self/Sub |
|---|---|---|
| 7.1.3.1 | **System setup** — Install a commercial-grade overhead door, including the full track system, springs, and heavy-duty hardware | Sub (door specialty) |
| 7.1.3.2 | **Alignment** — Ensure the door is plumb and square, with a recommended tolerance of 5mm to 10mm for proper operation | Sub |
| 7.1.3.3 | **Testing** — Perform multiple operation cycles to verify balance and alignment | Sub |

### §7.1.4 — Interior Prep & Finishing

| § | Activity | Self/Sub |
|---|---|---|
| 7.1.4.1 | **Surface preparation** — Clean all walls to remove dust and residue; scrape any peeling paint | BPC self (small qty) |
| 7.1.4.2 | **Painting** — Prime and paint all interior walls (approx. **198 sq ft floor area**) using industrial-grade materials | BPC self |

> Note: §7.1.4.2 says "198 sq ft floor area" but paint is applied to *walls*. This likely means the room footprint is ~198 sf and wall surface area is approximately (perimeter × height). For a square ~14×14 ft room at 12 ft ceiling, walls = 4 × 14 × 12 = ~672 sf. Confirm at site visit or via clarification question.

### §7.1.5 — Final Cleaning & Site Restoration

| § | Activity | Self/Sub |
|---|---|---|
| 7.1.5.1 | **Debris removal** — Load and haul away all leftover materials, trash, and heavy equipment | BPC self + dumpster |
| 7.1.5.2 | **Site condition** — Restore the mechanical room to a clean, workable condition | BPC self |

## Critical estimating assumptions to validate

1. **Existing beam condition.** §7.1.1.3 says "Install replacement steel beams **as required**" — this is open-ended. The bid must include some allowance for beam replacement, but the actual scope depends on field inspection results. Ask at Q&A: is HHSC providing a structural inspection report? If not, propose a unit price for beam replacement (LF of W-shape).
2. **Generator size / specifications.** §7.1.2 says "industrial generator" but does not specify kW, fuel type, dimensions, or weight. Crane size and rigging plan depend on this. Ask at Q&A.
3. **Roof structure type.** §7.1.1.1 says "metal roof sheets" — likely a metal building system. Need to know span, slope, and how reinforcement integrates with existing structure.
4. **Overhead door specifications.** Manufacturer / size / R-value / operator type not stated. Ask at Q&A.
5. **"198 sq ft floor area" interpretation.** Confirm whether this is the room size or the wall paint area.
6. **Hazmat disposal.** TX-licensed hazardous-waste handler required for generator fluids. Ask whether HHSC has a preferred vendor.
7. **Work hours.** Mechanical room is in an active HHS facility — confirm whether work is normal business hours, after-hours, weekend.

## Reusable scope templates

Closest match in `firm/scope-templates/`:

- None of the existing templates cover **mechanical-room renovation** or **industrial equipment removal**. The closest is `office-tenant-refurb.md` for the paint + cleaning portion, but the structural + generator + overhead-door work is novel for the BPC scope-template library.

**Recommend** seeding `firm/scope-templates/mechanical-room-renovation.md` once this scope is finalized. Capture: typical equipment-removal-by-crane sub categories, hazmat disposal documentation chain, structural reinforcement labor classes, commercial overhead door cycle-testing acceptance criteria.
