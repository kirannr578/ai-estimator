# Bid-prep checklist — USACE Fort Hood Staging W9126G26RA015

> **PLACEHOLDER** — full checklist only completes after the go/no-go decision in [`go-no-go-decision.md`](./go-no-go-decision.md) returns **GO**.
>
> If the decision is **NO-GO**, this checklist is abandoned and the workspace converts to a `bids/_NO_GO/` memo per the no-go template.

## Pre-decision (mandatory regardless of outcome)

These steps run **before** the go/no-go decision so the decision rests on facts:

- [ ] Locate the offer-due date — SF 1442 Item 13c (typically a few pages into the SF 1442 form near the SOLICITATION block). Pull from the 1,835-page compiled RFP at `C:\Users\rnuduru1\OneDrive\Blueprint Constructs\Landmark\05272026\W9126G26RA015_Compiled.pdf` page 6+ (SF 1442 appears around there per extraction). Also confirm against SAM.gov posting W9126G26RA015.
- [ ] Identify the Contracting Officer (CO) name + email — typically Block 9 of SF 1442 ("For Information Call") and/or the Section L Block 17 Contract Specialist contact.
- [ ] Confirm the SBA Case Number 347768 against SBA.gov small-business sub-net listing.
- [ ] Pull the Davis-Bacon WD for Bell + Coryell Counties from SAM.gov (likely attached to the W9126G26RA015 posting).
- [ ] Confirm bonding capacity with BPC's surety broker — specifically: can BPC post a $1M bid bond and $5M-$10M P&P bonds within the bid window?
- [ ] Inventory BPC's federal-construction past performance ≥$3M in the last 5 years. If zero priors at this magnitude, document the gap explicitly for the no-go memo.

## Post-go (if go/no-go = GO)

If the decision returns GO, the full checklist below activates. Each item is a placeholder until the decision is made.

### Gate G-1 — SAM.gov + federal compliance refresh

- [ ] Confirm SAM active through anticipated NTP + 12 months
- [ ] UEI + CAGE current
- [ ] Reps & Certs ≤ 12 months old
- [ ] FAR 52.219-1 small-business size assertion at NAICS 236220
- [ ] FAR 52.204-21 Basic Safeguarding readiness
- [ ] FAR 52.204-29 FASCSA rep
- [ ] FAR 52.204-24 / 52.204-25 / 52.204-26 Section 889 reps
- [ ] Buy American reps
- [ ] DBA / certified-payroll (WH-347) readiness

### Gate G-2 — Bonding

- [ ] Bid bond at FAR 52.228-1 (20% of bid OR $1M, whichever less)
- [ ] P&P bond letters at FAR 52.228-15 (100% / 100% of contract price)

### Gate G-3 — Pre-bid

- [ ] Attend pre-proposal conference (if any — pull from Section L)
- [ ] Attend site visit (if any — base access via USACE-FWD pre-clearance)
- [ ] Submit substantive RFI questions by deadline (Section L)

### Gate G-4 — Spec-book takeoff

- [ ] Divisions 00 (procurement + contracting) — proposal volumes structure
- [ ] Divisions 01 (general requirements) — schedule, submittals, QC, safety, AT/OPSEC
- [ ] Divisions 02-12 (existing conditions through furnishings) — building scope
- [ ] Divisions 22-27 (plumbing, HVAC, integrated automation, electrical, comms) — MEP scope
- [ ] Divisions 31-33 (earthwork, exterior improvements, utilities) — civil scope
- [ ] Appendix A — Justification & Approval

### Gate G-5 — Sub outreach

- [ ] Concrete (Division 03)
- [ ] Structural steel + cold-formed framing (Division 05)
- [ ] Carpentry + cabinets (Division 06)
- [ ] Insulation + air-barrier + roofing + sealants (Division 07)
- [ ] Doors + windows + hardware + glazing (Division 08)
- [ ] Finishes (Division 09)
- [ ] Toilet accessories + fire ext + signage (Division 10)
- [ ] Facility fall protection (Section 11 18 29)
- [ ] Roller shades (Section 12 24 13)
- [ ] Plumbing (Division 22)
- [ ] HVAC with BACnet DDC (Division 23)
- [ ] Cybersecurity for FRCS / HVAC / lighting (Section 25 05 11.01 / 25 05 11.02) — **specialty**
- [ ] Electrical interior distribution + lightning + lighting (Division 26)
- [ ] Telecom OSP + interior cabling (Division 27 + 33 82 00)
- [ ] Earthwork + clearing + grubbing (Division 31)
- [ ] Asphalt + roller-compacted concrete paving + chain-link fencing + landscape (Division 32)
- [ ] Stormwater + underground electrical + comms OSP (Division 33)

### Gate G-6 — Volumes I–IV

Per [`firm/proposal-library/federal-volumes/`](../../firm/proposal-library/federal-volumes/):

- [ ] Volume I — Technical Approach
- [ ] Volume II — Management Approach
- [ ] Volume III — Past Performance (the binding constraint per `go-no-go-decision.md` Gate 2)
- [ ] Volume IV — Price Proposal (CLIN schedule + base + 5 options)

### Gate G-7 — Submission

- [ ] Per Section L instructions (electronic SAM.gov upload typical for USACE)
- [ ] Submit ≥ 24 hr before deadline (federal-RFP latency margin)
- [ ] Acknowledge any amendments via SF 30 in Block 19 of SF 1442

## Watch items

- **AT/OPSEC** (Section 01 01 10.00 44) — likely requires NACI/NACLC screening for any personnel needing base access for installation work. Lead time 4-8 weeks.
- **DPAS rating** — if blocks in Section L provision near FAR 52.214-34 show a DO or DX rating, accept the rated-order priority obligations in writing.
- **Section 889** — confirm BPC's subs don't use covered telecom (Huawei, ZTE, Hytera, Hikvision, Dahua) per FAR 52.204-25.
