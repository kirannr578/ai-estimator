# 03 — Missing documents — TAMU Wehner 2025-06871

**Status as of 2026-05-27 PM.** Each row names the unblocking action and ownership.

---

## 1. The big rocks (blocking go/no-go)

| # | Doc | Why blocking | Who to contact | When |
|---:|---|---|---|---|
| 1 | **Eligibility confirmation post-missed-meeting** | Without confirmation that a non-attending firm can submit, we may be wasting 14 working days | **Cherise Toler (TAMU Procurement, primary), Matt Wiederstein (SSC PM, secondary)** | Thu 2026-05-28 AM |
| 2 | **Notice of Project PDF** (ESBD attachment) | Contains the link to the full CSP package | Download from ESBD posting for SSC-2025-06871 | Thu 2026-05-28 AM |
| 3 | **Full CSP package** — drawings, specs, proposal form, HSP form, UGSC, sample contract | Required for takeoff, pricing, narrative, form-fill | Download from Trimble Unity Construct / e-Builder link in NOP | Thu 2026-05-28 |
| 4 | **Pre-proposal meeting Q&A + sign-in sheet** | Captures clarifications and addenda issued at the 5/19 meeting; documents competitor pool | Matt Wiederstein (SSC PM) | Thu 2026-05-28 |

## 2. How to retrieve the CSP package (step-by-step for the user)

1. **Open ESBD** at `https://www.esbd.cpa.state.tx.us/`
2. Search by Solicitation ID: **SSC-2025-06871** OR by Agency 711 + Class/Item 90900
3. Open the posting for "Wehner Finance Seminar Rm 340E"
4. Click on the attachment named `ESBD_513163_1778104136552_2025-06871_Notice of Project-CS_26.05.05.pdf`
5. Download the NOP PDF to OneDrive: `Blueprint Constructs/Landmark/05072026/` or similar
6. **Open the NOP PDF** and locate the embedded URL or QR code for the Trimble Unity Construct / e-Builder bid package
7. Open that URL in a non-corporate-network browser (Zscaler may otherwise intercept large PDFs)
8. Download every file on the bid-package landing page
9. Save into `bids/tamu-wehner-fin-340E-2025-06871/local/` (gitignored)
10. Update `source-files-manifest.md` with actual file names

**Estimated time:** 15-30 minutes once at a non-corporate-network workstation.

## 3. Drawings (within the CSP package)

| Item | Why needed |
|---|---|
| A0 — Cover sheet + sheet index | Identify the full drawing scope |
| A1 — Demo plan(s) for Rms 340E, A, D, DA | Sizing demolition takeoff |
| A2 — Floor plan (combined seminar room) | Partition + finish takeoff |
| A3 — Reflected ceiling plan | Ceiling + lighting + diffuser takeoff |
| A4 — Wall sections / details | Construction detail clarity |
| A5 — Interior elevations | Finish + door/hardware locations |
| A6 — Schedules (door, finish, equipment) | Schedule-based quantity verification |
| **A7 — MARRS glass wall detail** | Specialty glazing scope clarity |
| S1-S2 — Structural (if walls are structural) | Structural-modification scope |
| M1 — Mechanical plan | HVAC re-balance + new equipment |
| E1-E2 — Electrical plan | Outlets, lighting, AV rough-in |
| P1 — Plumbing plan | Sink demolition + cap-in-place |
| T1 — Telecommunications plan | AV / data rough-in |

## 4. Specifications (within the CSP package)

| CSI Division | What to look for |
|---:|---|
| 00 | Procurement documents — Proposal Form (00 42 13), Technical Proposal (00 45 16), Safety/QC (00 45 17), HSP / VetHUB (00 45 17.1), Master Vendor Agreement (00 52 63), UGSC (00 72 00), SGC (00 73 00) |
| 01 | General Requirements — Summary of Work, Coordination, References, Project Meetings, Submittals, QC, Temporary Facilities, Closeout |
| 02 | Demolition (02 41 19 Selective Demolition) |
| 06 | Wood / Carpentry — typically minimal; may have lab/seminar trim |
| 07 | Thermal / Moisture — typically minimal in office reno |
| 08 | **Openings / Doors / Glazing** — MARRS architectural glass wall system; door schedule |
| 09 | Finishes — flooring (carpet tile / LVT), base, acoustic ceiling, gypsum board, paint |
| 10 | Specialties — signage, casework |
| 11-14 | Likely "NOT USED" — no equipment/conveying scope |
| 21-23 | Mechanical / HVAC modifications |
| 26 | Electrical — circuits, lighting, devices |
| 27 | Communications — AV, data rough-in |
| 28 | Electronic Safety + Security — typically NIC |

## 5. Firm-side documents (BPC must surface or refresh)

| # | Doc | Status | Owner |
|---:|---|---|---|
| 1 | Current COI (ACORD 25) | EXPIRED 2024-09-25 per firm-profile | Rocky — contact insurance broker (see `outreach/06-email-insurance-broker.md`) |
| 2 | Workers Comp carrier + limits | NOT FOUND in firm-profile | Rocky |
| 3 | Auto Liability carrier + limits | NOT FOUND in firm-profile | Rocky |
| 4 | Umbrella / Excess carrier + limits | NOT FOUND in firm-profile | Rocky |
| 5 | Bonding agent + capacity letter | Image-scan only in firm-profile | Rocky — contact bonding agent (see `outreach/05-email-bonding-agent.md`) |
| 6 | TX HUB Certificate renewal | ✅ Renewed 2026-05-30 per user (prior cycle expired 2024-08-31 per firm-profile); new expiration `[USER TO CONFIRM: new expiration date]` | Rocky — capture new expiration date; BPC can now self-perform HUB-credited scope |
| 7 | DFW MSDC MBE / SBE renewal | ✅ Renewed 2026-05-30 per user (prior cycle expired 2024-08-31 per firm-profile); new expiration `[USER TO CONFIRM: new expiration date]` | Rocky — capture new expiration date |
| 8 | EMR (3-year) | NOT FOUND in firm-profile | Rocky — pull from WC carrier |
| 9 | TRIR / LTIR (1-year) | NOT FOUND in firm-profile | Rocky — calculate from OSHA 300 logs |
| 10 | Past-perf reference contacts (3 references) | `[USER TO FILL]` per firm-profile | Rocky — surface real names + emails + phones |
| 11 | Annual revenue (FY-1, FY-2, FY-3) | NOT FOUND in firm-profile | Rocky — pull from accounting / tax returns |

## 6. Sub-side documents (for HSP + technical proposal)

| Sub trade | Status | Owner |
|---|---|---|
| Architectural glazing (MARRS) | UNKNOWN — no contacts in firm-profile | Rocky — identify via Patty Winkler HUB network OR direct outreach to MARRS-experienced glaziers (e.g., **Acme Architectural Glazing**, **South Texas Glass**, **Brazos Glass**) |
| Electrical | UNKNOWN | Rocky — reuse Harrington outreach contacts if any |
| Plumbing | UNKNOWN | Rocky |
| HVAC | UNKNOWN | Rocky |
| Flooring (carpet tile / LVT) | UNKNOWN | Rocky |
| Painting | BPC self-performs typically | — |
| Drywall / Gypsum | BPC self-performs typically | — |
| Acoustic ceiling | UNKNOWN | Rocky |
| Casework / millwork (demo + install) | UNKNOWN | Rocky |
| Demolition / hauling | UNKNOWN | Rocky — may self-perform or sub |

## 7. Documents NOT needed (avoid scope creep)

- ❌ Federal SF 1442 / SF 1449 — this is a Texas state CSP, not a federal solicitation
- ❌ Federal SAM.gov reps & certs — not federal; SAM not relevant
- ❌ Davis-Bacon WD — Texas state work uses TX Prevailing Wage Determination (Brazos County), not Davis-Bacon
- ❌ Buy American certification — federal-specific; not applicable
- ❌ AF IMT 3000 — Air Force-specific
- ❌ DD Form — DOD-specific
