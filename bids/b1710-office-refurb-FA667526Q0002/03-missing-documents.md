# Missing documents — B1710 Office Refurbishment

This is the **exhaustive list of inputs we still need** before the Friday 17:00 submission. Each entry names exactly what would unblock the dependent section, so the 48-hour sprint doesn't lose time to "what doc do I need?" guesswork.

Status legend: `[have]` in hand · `[need]` blocking · `[soft]` nice-to-have but not blocking · `[na]` confirmed not applicable

---

## A. Solicitation package (Attachment 01-05) — **ALL HAVE**

- [have] **`Solicitation - FA667526Q0002.pdf`** — RFQ cover SF 1449 + Sections E/F/G/I/L/M (25 pp). Unblocks: `00-overview.md` ✓, `04-evaluation-strategy.md` ✓, `proposal/04-SF-1449-fill-guide.md` ✓.
- [have] **`SOW for B1710 Office Refurbish.docx`** — Statement of Work. Unblocks: `02-scope-of-work.md` ✓, `11-takeoff-template.json` ✓.
- [have] **`B1710 Floorplan for Refresh Project.pdf`** — Floor plan with C/B/P room labels. Unblocks: takeoff per-room SF.
- [have] **`Construction WD Building TX20260270 02Jan2026.pdf`** — Davis-Bacon WD. Unblocks: `10-prevailing-wages.md` ✓.
- [have] **`AF3000 Material Submission Form.pdf`** — Post-award submittal form. Unblocks: `proposal/02-technical-acceptability.md` (submittal-cycle reference).
- [have] **`Request For Information Form.pdf`** — RFI template. Unblocks: `proposal/11-rfi-cover-letter.md`.

All 6 files are in `C:\Users\rnuduru1\OneDrive\Blueprint Constructs\Landmark\05072026\B1710+Office+Refurbish.zip` (957 KB ZIP, downloaded 2026-05-27 13:22 CDT). See `source-files-manifest.md`.

---

## B. Firm-side documents needed for submission

### B.1 SAM.gov status verification — **`[need]` Wed 2026-05-27 PM**

- [need] **Screenshot of SAM.gov Entity Management page** showing:
   - Registration status: Active (green)
   - Registration expiration date (must be ≥ 2026-05-29)
   - Last Reps & Certs refresh date (must be within last 12 months)
   - NAICS 236220 included in the entity's NAICS list
   - Size representation at 236220: Small under $45M
   - EFT (banking) info current
   - TIN-IRS match confirmed
- **What unblocks if it lands:** `proposal/05-reps-and-certs-pull-guide.md` and the SAM-status PDF that goes into the email packet.
- **What to do:** Rocky logs into `https://sam.gov/`, prints the entity page to PDF, drops into `proposal/exports/` (gitignored) or attaches to email packet directly.
- **Why blocking:** non-current SAM = non-responsive offer per FAR 52.204-7 / 52.204-13.

### B.2 Current Commercial General Liability COI — **`[need]` Thu 2026-05-28 12:00**

- [need] **ACORD 25 PDF** showing current GL coverage:
   - Named insured: `RK Residential Homes and Commercial Constructions LLC dba Blue Print Constructs`
   - Limits: $1M each occurrence / $2M general aggregate (minimum)
   - Policy period covering 2026-05-29 through at least 2026-09-30 (covers all 100 cal days of PoP)
   - Description should include the project: "Office Refurbishment B1710, NAS JRB Fort Worth"
   - Optionally with **U.S. Government / Department of the Air Force** listed as additional insured (typical AF construction COI requirement; verify against Section I clauses on insurance — see note below)
- **What unblocks if it lands:** insurance attachment in the email packet.
- **What to do:** Rocky contacts insurance broker (see `firm/firm-profile.json → insurance.insurance_broker` — currently **not surfaced** in firm profile; this is the #1 stale data item from the 2026-05-23 firm-profile audit, Block 1).
- **Why blocking:** AF construction RFQs require COI submission either with the offer or within 10 days of award; absent COI, offer is technically non-responsive on insurance.

> Section I clauses on insurance in this RFQ package: I scanned the 25-page solicitation for FAR 52.228-5 (Insurance — Work on a Government Installation) and did **not** find it as a separately cited full-text clause. The clause is, however, default-applicable to AF construction work at $25K+. Insurance limits default to FAR 28.307-2 minimums unless agency-specific (which would be $1M/$2M GL for AF small construction, typical). **Action:** if the broker can issue an ACORD with both *Air Force* and *USA* as additional-insureds and a "U.S. Government" certificate-holder line, that satisfies the typical AF requirement. If unclear, send the RFI question to the CO.

### B.3 Payment-bond commitment letter — **`[need]` Wed 2026-05-27 PM or Thu 2026-05-28 AM**

- [need] **Letter from bonding agent** stating the surety is willing to issue a payment bond for **100% of contract price** (or, alternatively, an ILC) up to $100K, post-award, valid for PoP + 1 year (per FAR 52.228-13). The letter goes into the offer packet to signal capacity.
- **What unblocks if it lands:** `proposal/06-bondability-letter-template.md` (currently a template; replace with the real letter).
- **What to do:** Rocky contacts bonding agent. Per `firm/firm-profile.json → bonding`, the surety + agent details are NOT in the firm profile (bond letter on file is image-only PDF, not text-extracted). The Lavon RV Park contract proves at least $1M single-project capacity; a $100K payment bond is well within capacity. The bonding agent identity needs to be surfaced from the on-file letter (`BPC/Bond Letter_RK Residential Homes and Commercial Constructions, LLC dba Blue Print Constructs.pdf` on OneDrive). This is Block 2 of the 2026-05-23 firm-profile audit.
- **Why blocking:** FAR 52.228-13 makes the payment-bond requirement a contract clause; absent capacity, the bonder must be willing to issue. Showing a commitment letter in the offer packet is what differentiates a responsive offeror from one who can't perform.

### B.4 Past-performance reference contacts — **`[need]` Thu 2026-05-28 16:00**

Per `firm/firm-profile.json → past_projects`, the 3 best-fit past-perf picks for this AFRC small-construction bid are:

1. **Hindu Temple of Southlake** — owner: North Texas Hindu Heritage Society. Reference contact in firm profile: `[USER TO FILL — North Texas Hindu Heritage Society project POC]`. **Action:** Rocky surfaces a current name, title, email, and phone for the temple's project POC (likely the project coordinator on the 2024-024 owner-side project number).
2. **Holiday Inn Hall Park** — owner: Holiday Inn franchisee at Hall Park, Frisco. Reference contact: `[USER TO FILL — Holiday Inn Hall Park property POC]`. **Action:** Rocky surfaces a current name, title, email, phone for the property GM or facilities manager.
3. **Lavon RV Park** — owner: Lavon Leisure 78 RV Park LLC, 614 Forest Hill Dr, Murphy, TX 75094. Reference contact: `[USER TO FILL — Lavon Leisure 78 RV Park LLC owner POC]`. **Action:** Rocky surfaces owner contact (named on contract).

- **What unblocks if it lands:** `proposal/03-past-performance.md` per-reference contact rows.
- **Why blocking-ish:** AFRC CO will use **CPARS + SPRS + personal knowledge** plus may call references. A reference list with `[USER TO FILL]` annotations is a red flag for the evaluator. If contacts can't be sourced in time, the alternative is a one-line note: "Reference contacts available upon request to protect privacy" — this is a defensive but acceptable posture.

### B.5 Key-personnel resumes — **`[soft]` Thu 2026-05-28**

- [soft] **Rocky Nudurupati's bio** — already in `firm/firm-profile.json → key_personnel[0]`. Reformat as a 1-page resume for the proposal's project-team section.
- [soft] **Designated PM / Superintendent / Safety Officer for THIS project**. Per the firm-profile audit Block 3, named PM-of-record / Super / Safety Lead are NOT in the firm profile. For a 90-day, ~$50K project, **Rocky serves all three roles** is defensible (small firm, owner-operator pattern). Document this in `proposal/02-technical-acceptability.md`.
- **Why soft:** SAP RFQs are not always evaluated on key-personnel resumes (the Section M here doesn't call for them explicitly). But comparative evaluation lets the CO consider any factor; a credible team-of-three story strengthens the offer.

---

## C. Site-specific information — **`[need]` to ask CO via RFI**

### C.1 Site walk coordination — **see RFI**

- [need] Whether a site walk is offered, when, and POC for base-access sponsorship. RFI question #1 (see `proposal/11-rfi-cover-letter.md`).
- **Decision rule:** if CO replies by Thu 12:00 with a site-walk date that falls before Fri 14:00, attend; otherwise field-verify post-award.

### C.2 Carpet color + dye-lot — **defer to post-award submittal**

- [need] Whether dye lot **H6958** is firm (matching existing stock) or whether any current Shaw production dye lot is acceptable.
- **Why:** dye-lot H6958 from a 2-year-old spec may no longer be in production; carpet manufacturers commonly cycle dye lots. If the CO requires the exact H6958, contractor needs to source from carryover stock OR negotiate a substitution. Get clarity in RFI question #4.

### C.3 Paint brand — **defer to post-award submittal**

- [need] Whether "Agreeable Gray" must be **Sherwin-Williams SW 7029** specifically or any brand color-matched. RFI question #3.

---

## D. Internal documents (workspace-side; user authors)

- [need] **Signed offer cover** — SF 1449 page 1, blocks 12 (discount terms), 17 (offeror name/address), 23 (unit price), 24 (amount), 30 (signature/date). See `proposal/04-SF-1449-fill-guide.md`.
- [need] **Cover letter** for the email packet. Draft in `proposal/00-readme.md` and `proposal/11-rfi-cover-letter.md` (the latter doubles as an offer-cover template).

---

## E. Documents NOT NEEDED (negative confirmations)

To save the user from chasing items that aren't in scope:

- [na] **No bid bond** — FAR 52.228-1 is NOT in the package. No SF 24 required.
- [na] **No SF 1442** — this RFQ uses SF 1449 (commercial items).
- [na] **No HSP / HUB Subcontracting Plan** — this is a federal bid, not a TX state bid. (The HUB plan is for TAMU / ASU / other TX state bids — see `bids/tamu-wehner-fin-340E-2025-06871/` for that pattern.)
- [na] **No SBA 8(a) / SDVOSB / HUBZone certification** — set-aside is generic Small Business; BPC's small-business assertion is sufficient.
- [na] **No security clearance** — work is in an AFRC office building, not a SCIF/secure space. Base-access vetting only (escort or temp pass).
- [na] **No SCA / Service Contract Act compliance** — this is construction (Davis-Bacon Construction Wage Rate Requirements applies, FAR 52.222-6), not service work.
- [na] **No DBE / WBE / MBE plan** — federal bid, no state-style minority-participation plan needed.
- [na] **No drawings beyond the floor plan** — single sheet A-1 partial floor plan at Attachment 02; no specs book.
