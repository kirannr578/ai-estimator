# Bid-prep checklist — B1710 Office Refurbishment (48-hour sprint)

**Window:** Wed 2026-05-27 13:25 CDT → **Fri 2026-05-29 17:00 CDT** (~51.5 hours, ~3 working halves)
**Hard internal deadline:** Fri 2026-05-29 **15:00 CDT** (2-hour buffer for transmission)

Status legend: `[ ]` not started · `[~]` in progress · `[x]` done · `[!]` blocked / needs decision

---

## Gate 0 — Submission-eligibility prerequisites (TODAY, Wed 2026-05-27, by 17:00)

These are the items that, if any one fails, the bid is non-responsive regardless of how good the technical/price story is. Knock them out first.

- [ ] **G0.1** — Verify SAM.gov entity registration status (Rocky to log in at `https://sam.gov/` → Entity Management → Registration Status):
   - [ ] Registration is **Active** (not Inactive / Submitted / Work in Progress)
   - [ ] Expiration date is on or after **2026-05-29 17:00 CDT** (record exact expiration date in `firm/firm-profile.json → sam_expiration_date`)
   - [ ] Reps & Certs last refresh date is within the last 12 months (FAR 52.204-7 / 52.204-8). If not, refresh now — propagation takes 3-10 business days, so this is the longest-lead item in Gate 0.
   - [ ] EFT (banking) info in SAM is current
   - [ ] TIN-IRS match confirmed
   - **Owner:** Rocky N. **Deadline:** Wed 2026-05-27 17:00. **Blocker if fails:** all else.

- [ ] **G0.2** — Verify NAICS 236220 size representation matches RFQ:
   - [ ] BPC's SAM-posted NAICS list includes 236220 ✓ (already verified per `firm/firm-profile.json → naics_codes`)
   - [ ] Size representation at 236220 is **Small** under $45M (per SBE certificate + BPC's actual revenue). The DFW MSDC SBE cert (`DL09279`) attests this; user should double-check the revenue-based size representation in SAM is consistent.

- [ ] **G0.3** — Confirm bonding capacity for the **post-award** payment-bond requirement (FAR 52.228-13):
   - **Need:** Payment bond OR Irrevocable Letter of Credit (ILC), 100% of contract price, within 10 days of award.
   - **Estimated contract value:** $40K-$80K (based on the SF/LF scope at Davis-Bacon TX wages; see `09-price-references.md`).
   - **Action:** Email bonding agent (whoever issued the on-file bond letter) and ask for a payment-bond commitment letter for "up to $100K contract value, Air Force Reserve construction, NAS JRB Fort Worth, 100-day PoP." See `proposal/06-bondability-letter-template.md` for the draft.
   - **Note:** No *bid bond* is required (no FAR 52.228-1 in the package).
   - **Owner:** Rocky N. **Deadline:** Wed 2026-05-27 17:00. **Blocker if fails:** **PURSUIT REVERSAL** trigger.

- [ ] **G0.4** — Confirm current renewed Commercial GL COI is in hand:
   - **Need:** ACORD 25 listing the firm as named insured, $1M occurrence / $2M aggregate minimum (per typical AF small-construction requirement; verify against actual Section I clauses on insurance — the Sol package does not appear to specify FAR 52.228-5 insurance limits explicitly, default applies).
   - **Note:** Per `firm/firm-profile.json → insurance`, the last GL policy on file (SBCC-042443-00, American Builders Insurance / Appalachian Underwriters) expired 2024-09-25. **A current renewed COI must be surfaced before submission** — this is a year-over-year carry-forward item from prior bid prep.
   - **Owner:** Rocky N. + insurance broker. **Deadline:** Thu 2026-05-28 12:00. **Blocker if fails:** non-responsive offer.

---

## Gate 1 — Source-doc deep dive (today + Thu morning)

- [x] **G1.1** — Read full Solicitation PDF (25 pages, `Solicitation - FA667526Q0002.pdf`) — completed during scaffold creation; key facts extracted into `00-overview.md`.
- [x] **G1.2** — Read SOW DOCX in full — completed during scaffold creation; scope decomposed in `02-scope-of-work.md`.
- [x] **G1.3** — Skim Davis-Bacon WD TX20260270 — completed during scaffold creation; wages summarized in `10-prevailing-wages.md`.
- [ ] **G1.4** — Print + read the floor plan (Attachment 02) at 11×17 minimum so room-by-room measurements can be cross-checked against the SOW's stated 3,500 SF. **Owner:** Rocky N. or estimator. **Deadline:** Thu 2026-05-28 09:00.
- [ ] **G1.5** — Read AF IMT 3000 (Material Submission Form) — this is a **post-award** submittal template; ensure understanding so the project schedule can build in submittal time.
- [ ] **G1.6** — Read the RFI form (Attachment 05) — fill and submit at G3 below.

---

## Gate 2 — Technical scope + takeoff (Wed PM → Thu PM)

- [ ] **G2.1** — Cross-walk the floor plan's "C/B/P" (Carpet/Base/Paint) labels in Rooms 1002, 1006, 1008, 1009, 1013, 1020, 1022, 1023, 1025, 1026, 1028, 1029, 1030, hallway + canopy area against the SOW's "approximately 3,500 SF." Verify by scaling the plan. Record per-room SF in `11-takeoff-template.json`. **Owner:** Estimator. **Deadline:** Thu 2026-05-28 13:00.
- [ ] **G2.2** — Linear footage of 6" rubber base (perimeter of each carpeted room + hallway segments). Record in takeoff JSON. **Deadline:** Thu 2026-05-28 13:00.
- [ ] **G2.3** — Paint SF (walls only? walls + ceilings? — SOW §C says "paint all identified surfaces"; conservatively quote walls floor-to-ceiling for all C/B/P rooms + hallway as labeled "paint all hallway" on plan). **Deadline:** Thu 2026-05-28 13:00.
- [ ] **G2.4** — Drywall patch list: Rm 1030 doorway sheetrock-in (one wall opening, est. 36"×84" + framing); Rm 1008 wall repair + access panel install (size TBD from field; conservatively bid 4 SF patch + 12"×12" access panel). **Deadline:** Thu 2026-05-28 13:00.
- [ ] **G2.5** — Furniture-relocation labor estimate (multiple rooms with existing furniture per SOW §A and §E). Build into general conditions. **Deadline:** Thu 2026-05-28 13:00.
- [ ] **G2.6** — Disposal cost: certified construction-debris landfill per SOW §A. Plan for ~10 CY roll-off (carpet + furniture from Rm 1008 + wall debris). **Deadline:** Thu 2026-05-28 13:00.

---

## Gate 3 — RFI submission (Thu 2026-05-28 morning)

- [ ] **G3.1** — Send RFI to `lydia.carlton@us.af.mil` cc `todd.benner@us.af.mil` and `steven.munnell@us.af.mil`. Questions to include (draft in `proposal/11-rfi-cover-letter.md`):
   1. Is a coordinated site walk being offered before 29 May? If yes, when/POC for base-access sponsorship?
   2. Confirm primary submission email — is it `lydia.carlton@us.af.mil` or a different routing?
   3. Confirm whether the SOW's "Agreeable Gray" is **Sherwin-Williams SW 7029** specifically, or any-brand color-matched equivalent.
   4. Confirm whether the carpet tile must be Shaw *Constellat EW24* specifically (with dye-lot match H6958), or "or approved equal" — SOW §B says "Shaw or other accepted contractor submission" so equal is allowed; just confirm.
   5. Confirm acceptance period: 30 cal days minimum (FAR 52.212-1 default for commercial items) or longer?
   6. Confirm whether contractor must use AF IMT 3000 for *both* materials and substantial completion notices, or only for material submittals.
   - **Owner:** Rocky N. **Deadline:** Thu 2026-05-28 09:00.

---

## Gate 4 — Price proposal (Thu PM + Fri AM)

- [ ] **G4.1** — Pull rough rule-of-thumb pricing from `09-price-references.md` (carpet tile installed SF, rubber base LF, paint SF, drywall LF, access panel EA, debris disposal LS, furniture relocation LS, mobilization + general conditions LS).
- [ ] **G4.2** — Apply Davis-Bacon TX20260270 wage uplift (see `10-prevailing-wages.md` for hourly + fringe rates per trade).
- [ ] **G4.3** — Build the lump-sum line-item price → 1 number for Item 0001 (Lot). Show backup detail in `proposal/01-price-proposal.md` even though the offer cover form (SF 1449 Block 24) takes a single dollar figure for the lot.
- [ ] **G4.4** — Sanity-check against the 2 likely competitor bands (small construction shops servicing AFRC at NAS JRB).
- [ ] **G4.5** — Add 5% quantity contingency (justification: no site walk to verify 3,500 SF SOW figure).
- [ ] **G4.6** — Build CWICR / `config/cost_database.json` line-item benchmarks where the matcher returns confident hits (carpet tile install, base, paint per SF). Document in `09-price-references.md`. **Owner:** Estimator. **Deadline:** Fri 2026-05-29 11:00.

---

## Gate 5 — Past performance (Thu PM)

- [ ] **G5.1** — Per `firm/firm-profile.json → past_project_selection_rules` for federal AFRC small-construction, pull the 3 best-fit projects: **Hindu Temple of Southlake** (institutional finishes), **Holiday Inn Hall Park** (commercial hospitality interior), **Lavon RV Park** (federal-style coordination + scope discipline). Format per `proposal/03-past-performance.md`.
- [ ] **G5.2** — Surface owner-side reference contacts (currently `[USER TO FILL]` in firm-profile.json). At minimum, get a current email + phone for Hindu Temple + Holiday Inn + Lavon. **Owner:** Rocky N. **Deadline:** Thu 2026-05-28 16:00.

---

## Gate 6 — Schedule narrative (Fri AM)

- [ ] **G6.1** — Draft 90-cal-day construction schedule from NTP. Major activities: mobilization (3 days) → demo + furniture relocate (5 days, room-by-room) → Rm 1030 sheetrock-in + Rm 1008 wall repair + access panel (3 days, concurrent) → paint prep + paint (12 days, 2 painters, room-by-room) → flooring install (carpet + base) (12 days, 2-person crew) → punch-list + cleanup (5 days). Float: 50 days. Document why generous float (no site walk; Davis-Bacon scheduling overhead; AF inspection cadence). See `proposal/02-technical-acceptability.md`.

---

## Gate 7 — Submission package assembly (Fri AM)

- [ ] **G7.1** — Print SF 1449 from page 1 of the source PDF; fill blocks 12, 17, 23, 24, 30 (offeror data + signed offer). See `proposal/04-SF-1449-fill-guide.md`.
- [ ] **G7.2** — Compile the email packet:
   1. Cover letter (1 page) — see `proposal/11-rfi-cover-letter.md` for shape; adapt as offer cover.
   2. Signed SF 1449 (PDF).
   3. Price proposal narrative (`proposal/01-price-proposal.md` → PDF).
   4. Technical acceptability (`proposal/02-technical-acceptability.md` → PDF) — equipment/materials/labor list + 90-day schedule.
   5. Past performance 3-pack (`proposal/03-past-performance.md` → PDF).
   6. SAM.gov screenshot (current Active status + Reps & Certs date) — per `proposal/05-reps-and-certs-pull-guide.md`.
   7. Current COI (ACORD 25 PDF).
   8. Payment-bond commitment letter (from bonding agent, per Gate 0.3).
- [ ] **G7.3** — Final review pass: Rocky reads every document for legal-name consistency (`RK Residential Homes and Commercial Constructions LLC dba Blue Print Constructs`), UEI (`LM4YHVQ71QG7`), CAGE (`9LET0`).
- [ ] **G7.4** — Email send to `lydia.carlton@us.af.mil` cc `todd.benner@us.af.mil`, subject line: `Quote — FA667526Q0002 — Blue Print Constructs (UEI LM4YHVQ71QG7)` — Fri 2026-05-29 by **15:00 CDT** (2-hour buffer).

---

## Gate 8 — Confirmation + log (Fri 17:00-18:00)

- [ ] **G8.1** — Request read-receipt + delivery confirmation from Lydia Carlton's email.
- [ ] **G8.2** — Log submission in `firm/_scripts/` audit ledger.
- [ ] **G8.3** — Calendar the expected award/no-award response (typical AFRC SAP: 5-15 business days from offer close).
