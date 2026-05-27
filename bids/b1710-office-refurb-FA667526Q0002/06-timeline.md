# Timeline — B1710 Office Refurbishment (48-hour sprint)

**Now:** Wed 2026-05-27 13:25 CDT
**Hard deadline:** Fri 2026-05-29 17:00 CDT (Offer Due Date/Local Time per SF 1449 Block 8)
**Internal deadline:** Fri 2026-05-29 **15:00 CDT** (2-hour buffer for email transmission, attachment size issues, last-minute corrections)
**Total working window:** ~51.5 hours wall-clock, ~25 working hours net (Wed PM + Thu full + Fri morning)

---

## Day-by-day plan

### Wed 2026-05-27 — afternoon (3-4 working hours)

| Time | Task | Owner | Output |
|---|---|---|---|
| 13:25-14:00 | Scaffold review — Rocky reads through `00-overview.md` + `01-bid-prep-checklist.md` + `02-scope-of-work.md` to validate the read of the RFQ | Rocky | Decision: PURSUE confirmed (or change scope) |
| 14:00-15:00 | **Gate 0.1** — SAM.gov verification at sam.gov. Print entity page. Record expiration date. | Rocky | SAM screenshot PDF saved; firm-profile.json `sam_expiration_date` updated |
| 14:00-15:00 (parallel) | **Gate 0.3** — Email bonding agent for payment-bond commitment letter | Rocky | Email sent; commitment letter ETA from agent |
| 15:00-16:00 | **Gate 0.4** — Email/call insurance broker for current GL COI | Rocky | Broker confirms COI delivery ETA |
| 15:00-17:00 (parallel) | **Gate 2.1-2.6** — Floor plan study + per-room SF measurements + LF base + paint SF + drywall patch + furniture relocation + disposal | Estimator (or Rocky) | `11-takeoff-template.json` populated with real numbers |
| 17:00 | **Status check** — confirm Gate 0 items in motion; commit Wed PM work. | Rocky | EOD checkpoint |

### Thu 2026-05-28 — full working day (8-10 hours)

| Time | Task | Owner | Output |
|---|---|---|---|
| 08:00-09:00 | **Gate 3.1** — Send RFI to CO (Lydia Carlton) on the 6 questions in `proposal/11-rfi-cover-letter.md` | Rocky | RFI sent; logged |
| 09:00-12:00 | **Gate 1.4-1.6** — Floor plan + AF IMT 3000 + RFI form read; cross-check takeoff against plan SF labels | Estimator | Plan reviewed; AF 3000 understood for the post-award submittal schedule narrative |
| 12:00-13:00 | Buffer / lunch / status sync | Both | Confirm Gate 0 items resolved or escalate |
| 13:00-16:00 | **Gate 4.1-4.6** — Price proposal build: rule-of-thumb pricing × Davis-Bacon uplift × CWICR cross-check × 5% contingency → lump-sum Item 0001 price. Document backup detail. | Estimator | `proposal/01-price-proposal.md` complete |
| 16:00-17:00 | **Gate 5.1-5.2** — Past-perf 3-pack finalization: surface owner-side reference contacts for Hindu Temple, Holiday Inn, Lavon | Rocky | `proposal/03-past-performance.md` complete |
| 17:00-19:00 | **Gate 6.1** — 90-day schedule narrative + Gantt table | Estimator + Rocky | `proposal/02-technical-acceptability.md` complete (schedule section) |
| 19:00 | EOD checkpoint — Thu commits | Rocky | All proposal sections drafted; Fri AM is review + assembly + send |

### Fri 2026-05-29 — final assembly + send (4-5 working hours)

| Time | Task | Owner | Output |
|---|---|---|---|
| 07:00-08:00 | **Gate 7.1** — SF 1449 fill: blocks 12, 17, 23, 24, 30 (signed offer) | Rocky | Signed SF 1449 PDF |
| 08:00-10:00 | **Gate 7.2** — Email packet assembly: cover letter + signed SF 1449 + price + technical + past-perf + SAM screenshot + COI + payment-bond letter | Rocky + assistant | Email packet draft (all attachments labeled) |
| 10:00-11:00 | **Gate 4.6** — Final pricing sanity check; competitor band review; confirm lump-sum number | Estimator + Rocky | Final number locked |
| 11:00-12:00 | Buffer for any final RFI responses from CO; address if any | Rocky | RFI responses incorporated |
| 12:00-14:00 | **Gate 7.3** — Final review pass: Rocky reads every doc for legal-name / UEI / CAGE consistency, no `[USER TO FILL]` leftovers, all dates/dollar values correct, signed | Rocky | Packet final |
| 14:00-15:00 | **Buffer hour** — fix any last issues found in review | Both | Packet ready to send |
| **15:00** | **Gate 7.4 — EMAIL SEND** to `lydia.carlton@us.af.mil` cc `todd.benner@us.af.mil` — subject `Quote — FA667526Q0002 — Blue Print Constructs (UEI LM4YHVQ71QG7)` | Rocky | Email confirmation; read-receipt requested |
| 15:00-17:00 | **Buffer** for transmission issues (file-size limit, mailbox rejection, attachment corruption, etc.). Re-send if needed. | Rocky | Confirmed delivery |
| **17:00** | **HARD DEADLINE** — offer due per Block 8 | — | Submission complete |
| 17:00-18:00 | **Gate 8** — Log submission in `firm/_scripts/` ledger; calendar award/no-award expected response (5-15 business days) | Rocky | EOW |

---

## Federal holidays / blackout periods

- Mon 2026-05-26 — **Memorial Day** (past; only relevant for context — it explains why this scaffold lands on Wed not Tue, and why the user couldn't act on the 2026-05-07 email until this week)
- No federal holidays in the Wed-Fri submission window

## Award window forecast (post-submission)

Typical AFRC SAP construction award cycle:
- **5-15 business days** from offer close to award announcement (no formal best-and-final / negotiation cycle on FFP commercial RFQs at SAP scale)
- Most likely award window: **2026-06-09 to 2026-06-19**
- NTP issued: typically 5-7 business days after award → **2026-06-16 to 2026-06-30**
- PoP starts: **NTP + 10 cal days** per Section F = ~2026-06-26 to 2026-07-10
- PoP ends: **NTP + 90 cal days** from NTP = ~2026-09-14 to 2026-09-28

This means the actual on-base construction window is **mid-July through mid-September 2026** — squarely in summer holiday + Independence Day + Labor Day federal-holiday season. Schedule narrative should account for Juneteenth (Fri 2026-06-19), Independence Day observed (Fri 2026-07-03), Labor Day (Mon 2026-09-07), and the 0700-1600 M-F base hour window.

## Status reporting cadence

- **Wed EOD** — Rocky confirms Gate 0 items in motion (SAM, bonding, insurance).
- **Thu noon** — Mid-day sync: takeoff complete, RFI sent, pricing in build phase.
- **Thu EOD** — All proposal narrative sections drafted.
- **Fri 12:00** — All review issues identified; buffer hour starts.
- **Fri 15:00** — SEND.
- **Fri 17:30** — Confirmed delivered; debrief next steps.
